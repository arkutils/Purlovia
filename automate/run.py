import argparse
import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import *

import yaml

import ark.discovery
from config import ConfigFile, get_global_config
from export.asb.root import ASBRoot
from export.example.root import ExampleRoot

from .ark import ArkSteamManager
from .exporter import ExportManager
from .git import GitManager
from .notification import handle_exception

# pylint: enable=invalid-name

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


def setup_logging(path='config/logging.yaml', level=logging.INFO):
    '''Setup logging configuration.'''
    if os.path.exists(path):
        with open(path, 'rt') as log_config_file:
            config = yaml.safe_load(log_config_file)
        Path('logs').mkdir(parents=True, exist_ok=True)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=level)

    logging.captureWarnings(True)

    root_logger = logging.getLogger()
    logging.addLevelName(100, 'STARTUP')
    root_logger.log(100, '')
    root_logger.log(100, '-' * 100)
    root_logger.log(100, '')


EPILOG = '''example: python -m automate --skip-install'''

DESCRIPTION = '''Perform an automated run of Purlovia, optionally overriding config or individual parts of the process.'''


def modlist(value: str) -> Tuple[str, ...]:
    value = value.strip()
    inputs = [v.strip() for v in value.split(',')]
    mods = tuple(v for v in inputs if v)
    for modid in mods:
        as_int = int(modid)  # pylint: disable=unused-variable  # For type-checking only
    return mods


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("automate", description=DESCRIPTION, epilog=EPILOG)

    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument('--live', action='store_true', help='enable live mode [requires git identity]')

    parser.add_argument('--remove-cache', action='store_true', help='remove the (dev only) asset tree cache')

    parser.add_argument('--skip-install', action='store_true', help='skip install/update of game and mods')
    parser.add_argument('--skip-extract', action='store_true', help='skip extracting all data completely')

    parser.add_argument('--skip-extract-asb', action='store_true', help='skip extracting all ASB data completely')
    parser.add_argument('--stats', action='store', choices=('8', '12'), help='specify the stat format for species')

    parser.add_argument('--skip-extract-wiki', action='store_true', help='skip extracting all wiki data completely')
    parser.add_argument('--skip-spawn-data', action='store_true', help='skip extracting spawn data from maps')
    parser.add_argument('--skip-biome-data', action='store_true', help='skip extracting biome data from maps')
    parser.add_argument('--skip-supply-drop-data', action='store_true', help='skip extracting supply drops from maps')

    parser.add_argument('--skip-commit', action='store_true', help='skip git commit of the output repo (use dry-run mode)')
    parser.add_argument('--skip-pull', action='store_true', help='skip git pull or reset of the output repo')
    parser.add_argument('--skip-push', action='store_true', help='skip git push of the output repo')

    parser.add_argument('--notify', action='store_true', help='enable sending error notifications')

    parser.add_argument('--mods', action='store', type=modlist, help='override which mods to export (comma-separated)')

    return parser


def handle_args(args: Any) -> ConfigFile:
    setup_logging(path='config/logging.yaml')

    config = get_global_config()

    if args.live:
        logger.info('LIVE mode enabled')
        config.settings.SkipGit = False
        config.git.UseReset = True
        config.git.UseIdentity = True
        config.errors.SendNotifications = True
    else:
        logger.info('DEV mode enabled')
        config.git.UseIdentity = False
        config.git.SkipCommit = True
        config.git.SkipPush = True
        config.errors.SendNotifications = False

    config.dev.DevMode = not args.live

    if args.stats:
        if int(args.stats) == 12:
            config.export_asb.Export8Stats = False
        else:
            config.export_asb.Export8Stats = True

    if args.notify:  # to enable notifications in dev mode
        config.errors.SendNotifications = True

    if args.remove_cache:
        config.dev.ClearHierarchyCache = True

    if args.skip_pull:
        config.git.SkipPull = True

    if args.skip_install:
        config.settings.SkipInstall = True

    if args.skip_extract:
        config.settings.SkipExtract = True

    if args.skip_extract_asb:
        config.export_asb.Skip = True

    if args.skip_extract_wiki:
        config.export_wiki.Skip = True

    if args.skip_spawn_data:
        config.export_wiki.ExportSpawnData = False

    if args.skip_biome_data:
        config.export_wiki.ExportBiomeData = False

    if args.skip_supply_drop_data:
        config.export_wiki.ExportSupplyCrateData = False

    if args.skip_commit:
        config.git.SkipCommit = True

    if args.skip_push:
        config.git.SkipPush = True

    if args.mods is not None:
        config.mods = args.mods

    return config


def run(config: ConfigFile):

    # Run update then export
    try:
        # Get mod list
        mods = config.mods

        # Update game ad mods
        arkman = ArkSteamManager(config=config)
        arkman.ensureSteamCmd()
        arkman.ensureGameUpdated()
        arkman.ensureModsUpdated(mods)

        # Ensure Git is setup and ready
        git = GitManager(config=config)
        git.before_exports()

        # Initialise the asset hierarchy, scanning everything
        ark.discovery.initialise_hierarchy(arkman, config)

        # Handle exporting
        exporter = ExportManager(arkman, git, config)
        # exporter.add_root(ExampleRoot())
        exporter.add_root(ASBRoot())
        # exporter.add_root(WikiRoot())
        exporter.perform()

        # Push any changes
        # git.finish()

        logger.info('Automation completed')

    except:  # pylint: disable=bare-except
        handle_exception(logfile='logs/errors.log', config=config)
        logger.exception('Caught exception during automation run. Aborting.')


def main():
    parser = create_parser()
    args = parser.parse_args()
    config = handle_args(args)
    run(config)
