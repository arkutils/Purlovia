from interactive_utils import *  # pylint: disable=wrong-import-order

from logging import INFO, basicConfig
from pathlib import Path
from typing import *

from ark.discovery import initialise_hierarchy
from ark.types import *
from automate.ark import ArkSteamManager
from config import ConfigFile, get_global_config
from ue.asset import ExportTableItem, ImportTableItem, UAsset
from ue.gathering import gather_properties
from ue.hierarchy import find_parent_classes, find_sub_classes, inherits_from
from ue.loader import AssetLoader, AssetNotFound
from utils.log import get_logger

is_interactive = bool(getattr(sys, 'ps1', sys.flags.interactive))

if is_interactive:
    basicConfig(level=INFO)

logger = get_logger(__name__)

config = get_global_config()
config.settings.SkipInstall = True
# config.mods = tuple('111111111,895711211,839162288'.split(','))

arkman = ArkSteamManager(config=config)
arkman.ensureSteamCmd()
arkman.ensureGameUpdated()
arkman.ensureModsUpdated(config.mods)
loader = arkman.getLoader()
initialise_hierarchy(arkman)

if is_interactive:
    print()
    print('Interactive session ready:')
    print('  arkman   : ArkSteamManager initialised in dry-run mode')
    print('  loader   : Asset loader')
    print('  config   : A safe default config')
    print()
