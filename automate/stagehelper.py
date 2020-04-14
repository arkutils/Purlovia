from abc import ABC
from pathlib import Path, PurePosixPath
from typing import *

from automate.exporter import ExportManager, ExportStage
from automate.jsonutils import save_as_json, should_save_json
from config import ConfigFile
from ue.loader import AssetLoader
from utils import throw
from utils.log import get_logger

# __all__ = [
#     'StageHelper',
# ]

# logger = get_logger(__name__)

# class StageHelper(ExportStage, ABC):
#     '''
#     To be used in conjunction with ExportStage.
#     Adds some common helper functions.
#     '''
#     official_mod_prefixes: Tuple[str, ...]
#     manager: ExportManager
#     game_version: str
#     game_buildid: str
#     loader: AssetLoader
#     config: ConfigFile

#     def initialise(self, manager: ExportManager):
#         self.manager = manager
#         self.loader = manager.loader
#         self.config = manager.config

#         self.game_version = manager.arkman.getGameVersion() or throw(ValueError("Game version missing"))
#         self.game_buildid = manager.arkman.getGameBuildId() or throw(ValueError("Build ID missing"))

#         official_modids = set(manager.config.official_mods.ids())
#         official_modids -= set(manager.config.settings.SeparateOfficialMods)
#         self.official_mod_prefixes = tuple(f'/Game/Mods/{modid}/' for modid in official_modids)

#     def is_core(self, assetname: str) -> bool:
#         '''Test if an asset should be considered 'core' as opposed to 'mod'.'''
#         if assetname.startswith('/Game/Mods') and not any(assetname.startswith(prefix) for prefix in self.official_mod_prefixes):
#             return False
#         return True

#     def is_mod(self, assetname: str, modid: str):
#         '''Test if an asset is from the specified mod.'''
#         clean_path = self.manager.loader.clean_asset_name(f'/Game/Mods/{modid}') + '/'
#         return assetname.startswith(clean_path)

#     def save_json_if_changed(self, data: Dict[str, Any], relative_path: PurePosixPath,
#                              metadata: Optional[Dict[str, Any]]) -> Optional[ExportedFile]:
#         '''
#         Pass in a data structure save only if content changed.
#         Data should have `version` and `format`.
#         Metadata should speciy anything to be included in the manifest file (e.g. mod title/ID).
#         '''
#         fullpath = Path(self.root.path / relative_path)
#         changed, version = should_save_json(data, fullpath)
#         if not changed:
#             logger.info(f'No changes to {fullpath}')
#             return None

#         pretty = self.config.export_asb.PrettyJson
#         logger.info(f'Saving export to {fullpath} with version {version}')
#         data['version'] = version
#         save_as_json(data, fullpath, pretty=pretty)

#         exported_file = ExportedFile(relative_path, version, format, metadata=metadata)
#         return exported_file
