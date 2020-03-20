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
from export.wiki.root import WikiRoot

from .ark import ArkSteamManager
from .exporter import ExportManager
from .git import GitManager
from .notification import handle_exception
from .run_sections import parse_runlist, should_run_section

# pylint: enable=invalid-name

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())

ROOT_TYPES = [
    ASBRoot,
    WikiRoot,
]


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


def maplist(value: str) -> Tuple[str, ...]:
    value = value.strip()
    inputs = [v.strip() for v in value.split(',')]
    maps = tuple(v for v in inputs if v)
    return maps


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("automate", description=DESCRIPTION, epilog=EPILOG)

    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument('--live', action='store_true', help='enable live mode [requires git identity]')

    parser.add_argument('--remove-cache', action='store_true', help='remove the (dev only) asset tree cache')

    parser.add_argument('--skip-install', action='store_true', help='skip install/update of game and mods')
    parser.add_argument('--skip-extract', action='store_true', help='skip extracting all data completely')
    parser.add_argument('--skip-commit', action='store_true', help='skip git commit of the output repo (use dry-run mode)')
    parser.add_argument('--skip-pull', action='store_true', help='skip git pull or reset of the output repo')
    parser.add_argument('--skip-push', action='store_true', help='skip git push of the output repo')

    parser.add_argument('--notify', action='store_true', help='enable sending error notifications')

    parser.add_argument('--list-stages', action='store_true', help='display extraction stage options and exit')

    parser.add_argument('--mods', action='store', type=modlist, help='override which mods to export (comma-separated)')
    parser.add_argument('--maps', action='store', type=maplist, help='override which maps to export (comma-separated)')

    parser.add_argument('sections',
                        action='store',
                        default=parse_runlist('all'),
                        type=parse_runlist,
                        metavar='SECTIONS',
                        nargs='?',
                        help='override extraction sections to be run (format: `all,-root1,-root2.stage1`, default: `all`)')

    return parser


def handle_args(args: Any) -> ConfigFile:
    config = get_global_config()

    # Action selections
    config.run_sections = args.sections

    # If stage list requested, skip everything else
    if args.list_stages:
        config.display_sections = True
        return config

    # Logging can be setup now we know we're not aborting
    setup_logging(path='config/logging.yaml')

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

    if args.notify:  # to enable notifications in dev mode
        config.errors.SendNotifications = True

    if args.remove_cache:
        config.dev.ClearHierarchyCache = True

    if args.skip_install:
        config.settings.SkipInstall = True
    if args.skip_extract:
        config.settings.SkipExtract = True

    if args.mods is not None:
        config.extract_mods = args.mods
    if args.maps is not None:
        config.extract_maps = args.maps

    # Git actions
    if args.skip_pull:
        config.git.SkipPull = True
    if args.skip_commit:
        config.git.SkipCommit = True
    if args.skip_push:
        config.git.SkipPush = True

    return config


def display_sections(config: ConfigFile):
    print('Available stages:')
    for root_type in ROOT_TYPES:
        root = root_type()  # type: ignore
        root_name = root.get_name()
        print(f'  {root_name}')
        for stage in root.stages:
            stage_name = stage.get_name()
            fullname = f'{root_name}.{stage_name}'
            match = should_run_section(fullname, config.run_sections)
            print(f'    {fullname} {("[*]" if match else "")}')


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
        for root_type in ROOT_TYPES:
            exporter.add_root(root_type())  # type: ignore
        exporter.perform()

        # Push any changes
        git.finish()

        logger.info('Automation completed')

    except KeyboardInterrupt:
        logger.error("Aborting on Ctrl-C.")
    except:  # pylint: disable=bare-except
        handle_exception(logfile='logs/errors.log', config=config)
        logger.exception('Caught exception during automation run. Aborting.')


def main():
    parser = create_parser()
    args = parser.parse_args()
    config = handle_args(args)
    if config.display_sections:
        display_sections(config)
    else:
        run(config)
