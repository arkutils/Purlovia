from abc import ABC, abstractmethod
from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from typing import *

import ark.properties
from ark.common import PGD_PKG
from ark.discovery import SpeciesDiscoverer
from ark.export_asb_values import values_for_species, values_from_pgd
from automate.exporter import ExportManager, ExportRoot, ExportStage
from automate.manifest import MANIFEST_FILENAME
from automate.version import createExportVersion
from config import ConfigFile
from ue.loader import AssetLoadException
from utils.strings import get_valid_filename

# __all__ = [
#     'SpeciesStage',
# ]

# logger = getLogger(__name__)
# logger.addHandler(NullHandler())

# class SpeciesStage(StageHelper):
#     discoverer: SpeciesDiscoverer

#     def __init__(self):
#         self.stored_titles: Dict[PurePosixPath, str] = {}

#     @staticmethod
#     def get_title() -> str:
#         return "Species"

#     @staticmethod
#     def get_skip(config: ConfigFile) -> bool:
#         # Currently only gated by config.export_asb.Skip, which is tested before this point
#         return False

#     def initialise(self, manager: ExportManager):
#         super().initialise(manager)
#         self.discoverer = SpeciesDiscoverer(self.loader)

#     def generate_commit_name_for_file(self, path: PurePosixPath) -> str:
#         return f"{self.stored_titles[path]} updated"

#     def extract_core(self, base_path: Path) -> Iterator[ExportedFile]:
#         version = createExportVersion(self.game_version, self.game_buildid)
#         species = list(self.discoverer.discover_vanilla_species())
#         species.sort()
#         species_data = self._gather_species_data(species)
#         species_values = self._convert_for_export(species_data, False)
#         other: Dict[str, Any] = dict()
#         other.update(self._gather_color_data(PGD_PKG, require_override=False))
#         exported_file = self._export_values(species_values, version=version, moddata=None, other=other)
#         if exported_file:
#             yield exported_file

#     def extract_mod(self, base_path: Path, modid: str) -> Iterator[ExportedFile]:
#         ...

#     def _gather_color_data(self, pgd_assetname: str, require_override: bool = False) -> Dict[str, Any]:
#         asset = self.loader[pgd_assetname]
#         color_data = values_from_pgd(asset, require_override=require_override)
#         return color_data

#     def _gather_species_data(self, species):
#         species_data = list()
#         for assetname in species:
#             asset = self.loader[assetname]

#             props = None
#             try:
#                 props = ark.properties.gather_properties(asset)
#             except AssetLoadException as ex:
#                 logger.warning(f'Gathering properties failed for {assetname}: %s', str(ex))
#             except:  # pylint: disable=bare-except
#                 logger.warning(f'Gathering properties failed for {assetname}', exc_info=True)

#             if props:
#                 species_data.append((asset, props))

#         return species_data

#     def _convert_for_export(self, species_data, _ismod: bool):
#         values = list()
#         for asset, props in species_data:
#             species_values = None
#             try:
#                 species_values = values_for_species(asset,
#                                                     props,
#                                                     allFields=True,
#                                                     fullStats=not self.config.export_asb.Export8Stats,
#                                                     includeBreeding=True,
#                                                     includeColor=True)
#             except Exception:  # pylint: disable=broad-except  # We want to handle anything except system exit conditions
#                 logger.warning(f'Export conversion failed for {asset.assetname}', exc_info=True)

#             if species_values:
#                 values.append(species_values)

#         return values

#     def _export_values(self, species_values: List, version: str, other: Dict = None,
#                        moddata: Optional[Dict] = None) -> Optional[ExportedFile]:
#         values: Dict[str, Any] = dict()
#         values['format'] = "1.12"

#         if moddata:
#             filename = f"{moddata['id']}-{moddata['name']}"
#             filename = get_valid_filename(filename)
#             title = moddata['title'] or moddata['name']
#             values['mod'] = dict(id=moddata['id'], tag=moddata['name'], title=title)
#         else:
#             filename = 'values'

#         values['version'] = version
#         values['species'] = species_values

#         if other:
#             values.update(other)

#         fullpath = Path((self.config.settings.OutputPath / self.config.export_asb.PublishSubDir / filename).with_suffix('.json'))
#         exported_file = self._save_json_if_changed(values, fullpath)

#         return exported_file

#     def _save_json_if_changed(self, values: Dict[str, Any], fullpath: Path) -> Optional[ExportedFile]:
#         changed, version = should_save_json(values, fullpath)
#         if not changed:
#             logger.info(f'No changes to {fullpath}')
#             return None

#         pretty = self.config.export_asb.PrettyJson
#         logger.info(f'Saving export to {fullpath} with version {version}')
#         values['version'] = version
#         save_as_json(values, fullpath, pretty=pretty)

#         exported_file = ExportedFile(relative_path, version, format, metadata)
#         return exported_file
