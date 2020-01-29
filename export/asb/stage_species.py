from abc import ABCMeta, abstractmethod
from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from typing import *
from typing import cast

from ark.common import PGD_PKG
from ark.properties import PriorityPropDict, gather_properties, stat_value
from ark.types import PrimalDinoCharacter
from automate.hierarchy_exporter import JsonHierarchyExportStage
from config import ConfigFile
from ue.asset import ExportTableItem, UAsset
from ue.hierarchy import find_sub_classes
from ue.loader import AssetLoadException
from ue.proxy import UEProxyStructure

from .colors import gather_pgd_colors
from .export_asb_values import values_for_species, values_from_pgd

__all__ = [
    'SpeciesStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class SpeciesStage(JsonHierarchyExportStage):
    def get_skip(self) -> bool:
        return not self.manager.config.export_asb.ExportSpecies

    def get_field(self):
        return 'species'

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_asb.PrettyJson)

    def get_core_file_path(self):
        # Override the default naming to match what ASB expects
        return PurePosixPath('values.json')

    def get_mod_file_path(self, modid: str):
        # Override the default naming to match what ASB expects
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        return PurePosixPath(f'{modid}-{mod_data["name"]}.json')

    def get_format_version(self):
        return "1.12"

    def get_ue_type(self):
        return PrimalDinoCharacter.get_ue_type()

    def get_pre_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            title = mod_data['title'] or mod_data['name']
            return dict(mod=dict(id=modid, tag=mod_data['name'], title=title))

        return None

    def get_post_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if modid:
            # Find any colour overrides in the mod's PGD
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            package = mod_data.get('package', None)
            if package:
                pgd_asset = self.manager.loader[package]
                return values_from_pgd(pgd_asset, require_override=True)
        else:
            # Return the colours from the main PGD
            pgd_asset = self.manager.loader[PGD_PKG]
            return values_from_pgd(pgd_asset, require_override=False)

        return None

    def extract(self, proxy: UEProxyStructure) -> Any:
        # TODO: Use this lovely proxy - we're currently using the old gather_properties system
        asset = proxy.get_source().asset
        asset_name = asset.assetname

        # Extract the species!
        # ...gather...
        try:
            props = gather_properties(asset)
        except AssetLoadException as ex:
            logger.warning(f'Gathering properties failed for {asset_name}: %s', str(ex))
            return None
        except Exception:  # pylint: disable=broad-except
            logger.warning(f'Gathering properties failed for {asset_name}', exc_info=True)
            return None

        try:
            species_data = values_for_species(asset, props, allFields=True, includeBreeding=True, includeColor=True)
        except Exception:  # pylint: disable=broad-except
            logger.warning(f'Export conversion failed for {asset_name}', exc_info=True)
            return None

        return species_data
