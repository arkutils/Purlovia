from typing import Any, Dict, GeneratorType, List, Optional

from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.utils import sanitise_output
from utils.log import get_logger

from .file_models import EXPORTS

logger = get_logger(__name__)

# TODO: rename file to exporter


class World:
    files: Dict[str, List[Any]]
    # Persistent level data
    persistent_level: Optional[str] = None
    settings: Dict[str, Any]

    def __init__(self):
        self.data = []

    def ingest_level(self, level: UAsset):
        assetname = level.assetname
        loader = level.loader

        # Check if asset is a persistent level and mark it as such in map info object
        if not getattr(level, 'tile_info', None) and self.persistent_level != assetname:
            if self.persistent_level:
                logger.warning(
                    f'Found a persistent level ({assetname}), but {self.persistent_level} was located earlier: skipping.')
                return
            self.persistent_level = assetname

        # Go through each export and, if valuable, gather data from it.
        for export in level.exports:
            helper = find_gatherer_for_export(export)
            if helper:
                category_name = helper.get_export_name()

                # Extract data using helper class.
                try:
                    data = helper.extract(proxy=gather_properties(export))
                except Exception:
                    logger.warning(f'Gathering properties failed for export "{export.name}" in {assetname}', exc_info=True)
                    continue
                if not data:
                    continue

                # Make sure the data list is initialized.
                if category_name not in self.data:
                    self.data[category_name] = list()

                if isinstance(data, GeneratorType):
                    data_fragments: list = sanitise_output(list(data))
                    for fragment in data_fragments:
                        if fragment:
                            self.data[category_name].append(fragment)
                else:
                    fragment = sanitise_output(data)
                    self.data[category_name].append(fragment)

        # Preemptively remove the level from linker cache.
        loader.cache.remove(assetname)


def find_gatherer_for_export(export: ExportTableItem) -> Optional[Type[MapGathererBase]]:
    try:
        parents = set(find_parent_classes(export, include_self=True))
    except (AssetLoadException, MissingParent):
        return None

    for _, helpers in EXPORTS.items():
        for helper in helpers:
            if parents & helper.get_ue_types():
                if helper.do_early_checks(export):
                    return helper

    return None


def find_gatherer_by_category_name(category: str) -> Optional[Type[MapGathererBase]]:
    for _, helpers in EXPORTS.items():
        for helper in helpers:
            if helper.get_export_name() == category:
                return helper

    return None
