import argparse
import logging
import logging.config
import os
from pathlib import Path
from typing import *

import yaml

from config import ConfigFile, get_global_config

from .ark import ArkSteamManager
from .export import export_values
from .git import GitManager
from .manifest import update_manifest

# pylint: enable=invalid-name

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


def setup_logging(path='config/logging.yaml', level=logging.INFO):
    '''Setup logging configuration.'''
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f)
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


EPILOG = '''example: python -m automate --dev --skip-install'''

DESCRIPTION = '''Perform an automated run of Purlovia, optionally overriding config or individual parts of the process.'''


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("automate", description=DESCRIPTION, epilog=EPILOG)

    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument('--live', action='store_true', help='enable live mode [requires git identity]')
    exclusive.add_argument('--dev', action='store_true', help='enable dev mode [skips commit and push]')

    parser.add_argument('--skip-pull', action='store_true', help='skip git pull or reset of the output repo')
    parser.add_argument('--skip-install', action='store_true', help='skip install/update of game and mods')
    parser.add_argument('--skip-extract', action='store_true', help='skip extracting all species completely')
    parser.add_argument('--skip-vanilla', action='store_true', help='skip extracting vanilla species')
    parser.add_argument('--skip-commit', action='store_true', help='skip git commit of the output repo (use dry-run mode)')
    parser.add_argument('--skip-push', action='store_true', help='skip git push of the output repo')

    parser.add_argument('--stats', action='store', choices=('8', '12'), help='specify the stat format to export')

    return parser


def handle_args(args: Any) -> ConfigFile:
    setup_logging(path='config/logging.yaml')

    config = get_global_config()

    if args.dev:
        logger.info('DEV mode enabled')
        config.settings.GitUseIdentity = False
        config.settings.GitUseReset = False
        config.settings.SkipCommit = True
        config.settings.SkipPush = True
        config.settings.SkipPull = True
    elif args.live:
        logger.info('LIVE mode enabled')
        config.settings.EnableGit = True
        config.settings.GitUseReset = True
        config.settings.GitUseIdentity = True

    if args.stats:
        if int(args.stats) == 12:
            config.settings.Export8Stats = False
        else:
            config.settings.Export8Stats = True

    if args.skip_pull:
        config.settings.SkipPull = True

    if args.skip_install:
        config.settings.SkipInstall = True

    if args.skip_extract:
        config.settings.SkipExtract = True

    if args.skip_vanilla:
        config.settings.ExportVanillaSpecies = False

    if args.skip_commit:
        config.settings.SkipCommit = True

    if args.skip_push:
        config.settings.SkipPush = True

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

        # Export vanilla and/or requested mods
        export_values(arkman, set(mods), config)

        # Update the manifest file
        update_manifest(config=config)

        # Commit any changes
        git.after_exports()

        logger.info('Automation completed')

    except:  # pylint: disable=bare-except
        logger.exception('Caught exception during automation run. Aborting.')


def main():
    parser = create_parser()
    args = parser.parse_args()
    config = handle_args(args)
    run(config)
