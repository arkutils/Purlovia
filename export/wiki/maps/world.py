from collections import defaultdict
from types import GeneratorType
from typing import Any, Dict, List, Optional, Type, cast

from ue.asset import ExportTableItem, UAsset
from ue.gathering import gather_properties
from ue.hierarchy import MissingParent, find_parent_classes
from ue.loader import AssetLoader, AssetLoadException
from ue.utils import sanitise_output
from utils.log import get_logger

from .file_models import EXPORTS
from .gathering_base import MapGathererBase, PersistentLevel
from .gathering_basic import BASIC_GATHERERS
from .gathering_complex import COMPLEX_GATHERERS, WorldSettingsExport
from .models import WorldSettings
from .resources import ResourceNodesByType, collect_harvestable_resources

logger = get_logger(__name__)

__all__ = [
    'ALL_GATHERERS',
    'EXPORTS',
    'World',
]

ALL_GATHERERS = COMPLEX_GATHERERS + BASIC_GATHERERS


class World(PersistentLevel):
    data: Dict[Type[MapGathererBase], List[Dict[str, Any]]]
    resource_nodes: ResourceNodesByType

    def __init__(self, main_assetname: Optional[str]):
        self.persistent_level = main_assetname
        self.data = defaultdict(list)
        self.resource_nodes = defaultdict(list)

    def ingest_level(self, level: UAsset):
        assert level.assetname
        assert level.loader
        assetname = level.assetname
        loader = cast(AssetLoader, level.loader)

        # Check if asset is a persistent level and mark it as such in map info object
        if not getattr(level, 'tile_info', None) and self.persistent_level != assetname:
            if self.persistent_level:
                logger.warning(f'Found a persistent level ({assetname}), but {self.persistent_level} was located earlier')
            else:
                self.persistent_level = assetname

        # Go through each export and, if valuable, gather data from it.
        for export in level.exports:
            # Raw harvestable resources aren't exported to Obelisk nor as a JSON.
            # If this is a foliage actor, branch off to a dedicated unit.
            if str(export.klass.value.name) == 'HierarchicalInstancedStaticMeshComponent':
                try:
                    collect_harvestable_resources(export, self.resource_nodes)
                except Exception:
                    logger.warning(f'Gathering harvestables failed for export "{export.name}" in {assetname}', exc_info=True)
                continue

            # Find a gathering class for this export.
            gatherer = find_gatherer_for_export(export)
            if not gatherer:
                continue

            # Extract data using gatherer class.
            try:
                data = gatherer.extract(proxy=gather_properties(export))
            except Exception:
                logger.warning(f'Gathering properties failed for export "{export.name}" in {assetname}', exc_info=True)
                continue

            # Add fragment to data lists
            if data:
                if isinstance(data, GeneratorType):
                    # Helper class returned a generator - move each piece if not null.
                    data_fragments: list = sanitise_output(list(data))
                    for fragment in data_fragments:
                        if fragment:
                            self.data[gatherer].append(fragment)
                else:
                    # Single piece.
                    fragment = sanitise_output(data)
                    self.data[gatherer].append(fragment)

        # Preemptively remove the level from linker cache.
        loader.cache.remove(assetname)

    def bind_settings(self) -> bool:
        '''
        Finds persistent level's world settings and sets the 'settings' field to them.
        '''
        all_pws = self.data[WorldSettingsExport]
        if not all_pws:
            return False

        for candidate in all_pws:
            if candidate['source'] == self.persistent_level:
                self.settings = candidate
                del self.settings['source']
                return True

        return False

    def convert_for_export(self):
        '''
        Converts XYZ coords to long/lat keys, and sorts data by every category's criteria.
        '''
        # Run data-specific conversions
        for gatherer, fragments in self.data.items():
            # Add lat and long keys as world settings have been found.
            for fragment in fragments:
                gatherer.before_saving(self, fragment)

    def construct_export_files(self):
        # Create a look-up map of model type to data.
        by_model = dict()
        for gatherer, data in self.data.items():
            model_type = gatherer.get_model_type()
            if model_type:
                by_model[model_type] = data

        # Pack gathered data into file model-compatible dicts.
        for name, model_info in EXPORTS.items():
            file_model, format_version = model_info

            output = dict()
            for field_name, field_type in file_model.__annotations__.items():
                entry_model = field_type.__args__[0]
                if entry_model == WorldSettings:
                    output[field_name] = self.settings
                elif entry_model in by_model:
                    data = by_model[entry_model]
                    output[field_name] = data

            if output:
                # Add format and persistent level fields.
                wrapped = dict(
                    format=format_version,
                    persistentLevel=self.persistent_level,
                )
                wrapped.update(output)

                # Yield the dict for the export stage to save.
                yield (name, wrapped)
            else:
                # No data was gathered. Do not export anything.
                yield (name, None)


def find_gatherer_for_export(export: ExportTableItem) -> Optional[Type[MapGathererBase]]:
    '''
    Finds a data gathering helper for an export.
    '''
    # Retrieve parents if possible. Skip export otherwise.
    try:
        parents = set(find_parent_classes(export, include_self=True))
    except (AssetLoadException, MissingParent):
        return None

    # Find a helper that can accept the export.
    for helper in ALL_GATHERERS:
        if parents & helper.get_ue_types():
            if helper.do_early_checks(export):
                return helper

    return None
