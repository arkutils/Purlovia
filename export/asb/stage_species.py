from pathlib import PurePosixPath
from typing import Any, Dict, Optional, cast

from ark.overrides import get_overrides_for_mod
from ark.types import COREMEDIA_PGD_PKG, PrimalDinoCharacter
from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.loader import AssetLoadException
from ue.proxy import UEProxyStructure
from utils.log import get_logger

from .export_asb_values import values_for_species, values_from_pgd

__all__ = [
    'SpeciesStage',
]

logger = get_logger(__name__)


class SpeciesStage(JsonHierarchyExportStage):
    def get_name(self):
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
        return "1.13"

    def get_ue_type(self):
        return PrimalDinoCharacter.get_ue_type()

    def get_post_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        output = dict()

        if modid:
            # Find any colour overrides in the mod's PGD
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            package = mod_data.get('package', None)
            if package:
                pgd_asset = self.manager.loader[package]
                pgd_output = values_from_pgd(pgd_asset, require_override=True)
                output.update(pgd_output)
        else:
            # Return the colours from the main PGD
            pgd_asset = self.manager.loader[COREMEDIA_PGD_PKG]
            pgd_output = values_from_pgd(pgd_asset, require_override=False)
            output.update(pgd_output)
            modid = ''

        # Add species override data, if any
        mod_overrides = get_overrides_for_mod(modid)
        if mod_overrides.species_remaps:
            output['remaps'] = mod_overrides.species_remaps

        return output

    def extract(self, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        char = cast(PrimalDinoCharacter, proxy)
        asset = proxy.get_source().asset
        asset_name = asset.assetname

        # Extract the species!
        try:
            species_data = values_for_species(asset, char)
        except AssetLoadException as ex:
            logger.warning(f'Gathering properties failed for {asset_name}: %s', str(ex))
            return None
        except Exception:  # pylint: disable=broad-except
            logger.warning(f'Export conversion failed for {asset_name}', exc_info=True)
            return None

        return species_data
