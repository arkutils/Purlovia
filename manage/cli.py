import argparse
import logging
import subprocess
import sys

from yaml import safe_load

from utils.log import get_logger

from .run import generate_run_command
from .status import load_status_cache, save_status_cache
from .trigger import collect_trigger_values, should_run, update_cache
from .types import ConfigFile

__all__ = ('main', )

logger = get_logger(__name__)

EPILOG = '''example: python -m manage [--dry-run] --pass=--live --pass=--skip-push'''

DESCRIPTION = '''Run any pending scheduled Purlovia tasks.'''


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("manage", description=DESCRIPTION, epilog=EPILOG)

    parser.add_argument('--pass', help='Add an argument to pass to automate', action='append', dest='args')
    parser.add_argument('--dry-run', help='Only print what would be executed - do not run anything', action='store_true')
    parser.add_argument('--fake-buildids', help='Provide random fake buildids for app repos', action='store_true')
    parser.add_argument('--list', help='List all available runs', action='store_true')
    parser.add_argument('--config-file', help='Path to the config file', default='config/runs.yaml')
    parser.add_argument('--pause', help=argparse.SUPPRESS, action='store_true')

    return parser


def parse_config(path: str):
    with open(path, 'rt') as f:
        raw_data = safe_load(f)

    config: ConfigFile = ConfigFile.parse_obj(raw_data)
    return config.__root__


def setup_logging():
    logging.basicConfig(force=True, level=logging.DEBUG)
    logger.info('Starting run manager...')
    logger.info('Python version: %s', sys.version)
    logger.info('Python executable: %s', sys.executable)
    logger.info('Command line: %s', ' '.join(sys.argv))


def main():
    parser = create_parser()
    args = parser.parse_args()

    run_config = parse_config(args.config_file)

    if args.list:
        print('Available runs:')
        for name in run_config:
            print(f'  {name}')
        return

    setup_logging()

    if args.pause:
        print('Pausing before running anything...')
        input('Press enter to continue...')

    cache = load_status_cache()
    collect_trigger_values(run_config, fake_buildids=args.fake_buildids)

    for name, run in run_config.items():
        logger.info(f'Testing if `{name}` is triggered...')

        if not should_run(name, run, cache.get(name)):
            continue

        cmd = generate_run_command(run, args.args)
        if args.dry_run:
            logger.info('Would run: %s', ' '.join(cmd))
        else:
            logger.info('Running: %s', cmd)
            result = subprocess.run(cmd)
            print(result.returncode)

            if result.returncode != 0:
                logger.error('Run failed - aborting')
                sys.exit(1)

            update_cache(name, run, cache)
            save_status_cache(cache)
