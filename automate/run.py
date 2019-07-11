import logging
import argparse
from typing import *
from pathlib import Path

from config import get_global_config, ConfigFile

from .git import GitManager
from .ark import ArkSteamManager
from .export import export_values
from .logging import setup_logging

# pylint: enable=invalid-name

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


def get_level_names():
    for name in sorted(logging._levelToName.values()):  # pylint: disable=protected-access,no-member
        if isinstance(name, str) and 'NOTSET' not in name:
            yield name


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Perform an automated run of Purlovia")

    loglevels = list(get_level_names())

    parser.add_argument('--dev', action='store_true', help='Enable dev mode [skips install, commit and push]')

    parser.add_argument('--skip-install', action='store_true', help='Skip instllation of game and mods')
    parser.add_argument('--skip-extract', action='store_true', help='Skip extracting all species')
    parser.add_argument('--skip-vanilla', action='store_true', help='Skip extracting vanilla species')
    parser.add_argument('--skip-commit', action='store_true', help='Skip committing to Git (uses dry-run mode)')
    parser.add_argument('--skip-push', action='store_true', help='Skip pushing to Git')

    parser.add_argument('--stats', action='store', choices=('8','12'), help='Specify the stat format to export')

    parser.add_argument('-l', '--log-level', action='store', choices=loglevels, default='INFO', help="Set the logging level")
    parser.add_argument('--log-dir', action='store', type=Path, default=Path('logs'), help="Change the default logging level")

    return parser


def handle_args(args: Any) -> ConfigFile:
    # Ensure log directory exists before starting the logging system
    args.log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(path='config/logging.yaml', level=args.log_level)

    if args.dev:
        args.skip_commit = True
        args.skip_install = True
        logger.info('DEV mode enabled')

    config = get_global_config()

    if int(args.stats) == 8:
        config.settings.Export8Stats = True
    else:
        config.settings.Export8Stats = False

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


def go(config: ConfigFile):

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

        # Commit any changes
        git.after_exports()

    except:  # pylint: disable=bare-except
        logger.exception('Caught exception during automation run. Aborting.')


def main():
    parser = create_parser()
    args = parser.parse_args()
    config = handle_args(args)
    go(config)
