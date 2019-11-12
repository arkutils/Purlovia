from abc import ABC, abstractmethod
from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from typing import *

# import ark.properties
# from ark.common import PGD_PKG
# from ark.discovery import SpeciesDiscoverer
# from ark.export_asb_values import values_for_species, values_from_pgd
# from automate.exporter import ExportedFile, ExportManager, ExportRoot, ExportStage
# from automate.manifest import MANIFEST_FILENAME
# from automate.version import createExportVersion
# from config import ConfigFile
# from ue.loader import AssetLoadException
# from utils.strings import get_valid_filename
# from

# __all__ = [
#     'SpeciesStage',
# ]

# logger = getLogger(__name__)
# logger.addHandler(NullHandler())

# class NPCSpawnEntriesContainer(UEProxyStructure, uetype='/Script/ShooterGame.NPCSpawnEntriesContainer'):
#     # DevKit Unverified
#     MaxDesiredNumEnemiesMultiplier = uefloats(1.0)

#     NPCSpawnEntries: Mapping[int, ArrayProperty]  # = []
#     NPCSpawnLimits: Mapping[int, ArrayProperty]  # = []

# class WikiRoot(ExportRoot):
#     @staticmethod
#     def get_name():
#         return "Wiki"

#     @staticmethod
#     def get_skip(config: ConfigFile) -> bool:
#         return config.export_wiki.Skip

#     def get_name_for_path(self, path: PurePosixPath) -> Optional[str]:
#         '''Return a nice name for a file to appear in the commit message.'''
#         folder = path.parts[0]
#         if folder == 'maps':
#             return f"Map for {path.stem}"
#         if folder == 'items':
#             return f"Items for {path.stem}"

#         return None  # will use a generic phrase

# class SpawnGroupStage(ExportStage):
#     # @staticmethod
#     # def get_title() -> str:
#     #     return "Spawn Groups"

#     @staticmethod
#     def get_skip(config: ConfigFile) -> bool:
#         # ...no specific config entry for this stage yet
#         return False

#     def extract_core(self, root: Path) -> Iterator[ExportedFile]:
#         ...
