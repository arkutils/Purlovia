import logging
import logging.config
import os
import sys
from pathlib import Path

import yaml

import ark.discovery
from config import LOGGING_FILENAME, ConfigFile
from export.asb.root import ASBRoot
from export.maps.root import WikiMapsRoot
from export.sanity.root import SanityRoot
from export.wiki.root import WikiRoot
from utils.log import get_logger

from .ark import ArkSteamManager
from .exporter import ExportManager
from .git import GitManager
from .notification import handle_exception

# pylint: enable=invalid-name

__all__ = (
    'ROOT_TYPES',
    'setup_logging',
    'run',
)

logger = get_logger(__name__)

ROOT_TYPES = (
    SanityRoot,
    ASBRoot,
    WikiRoot,
    WikiMapsRoot,
)


def setup_logging(path=LOGGING_FILENAME, level=logging.INFO):
    '''Setup logging configuration.'''
    if os.path.exists(path):
        with open(path, 'rt', encoding='utf-8') as log_config_file:
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


def log_versions():
    sha = os.environ.get('COMMIT_SHA', '')
    branch = os.environ.get('COMMIT_BRANCH', '<unknown branch>')

    if sha:
        logger.info("Version: %s (%s)", sha, branch)
    else:
        logger.info("Version: local development")


def run(config: ConfigFile):
    # Run update then export
    try:
        log_versions()

        # Get mod list
        mods = config.mods

        # Update game ad mods
        arkman = ArkSteamManager(config=config)
        arkman.ensureSteamCmd()
        arkman.ensureGameUpdated()
        arkman.ensureModsUpdated(mods)

        game_version = arkman.getGameVersion()
        if not game_version:
            raise ValueError("Game version not detected")

        # Ensure Git is setup and ready
        git = GitManager(config=config)
        git.before_exports()

        # Initialise the asset hierarchy, scanning everything
        ark.discovery.initialise_hierarchy(arkman)

        # Handle exporting
        exporter = ExportManager(arkman, git, config)
        for root_type in ROOT_TYPES:
            exporter.add_root(root_type())  # type: ignore
        exporter.perform()

        # Push any changes
        git.finish(game_version)

        logger.info('Automation completed')

    except KeyboardInterrupt:
        logger.error("Aborting on Ctrl-C.")
    except:  # pylint: disable=bare-except  # noqa: E722
        handle_exception(logfile='logs/debug.log', config=config)
        logger.exception('Caught exception during automation run. Aborting.')
        sys.exit(1)
