from pathlib import Path
import logging

from config import get_global_config

from .git import GitManager
from .ark import ArkSteamManager
from .export import export_values
from .logging import setup_logging


def main(logdir: str = 'logs'):
    # Ensure log directory exists before starting the logging system
    Path(logdir).mkdir(parents=True, exist_ok=True)
    setup_logging(path='config/logging.yaml', level=logging.INFO)

    # Run update then export
    try:
        # Get mod list
        mods = get_global_config().mods

        git = GitManager(config=get_global_config())

        # Update game ad mods
        arkman = ArkSteamManager()
        arkman.ensureSteamCmd()
        arkman.ensureGameUpdated()
        arkman.ensureModsUpdated(mods, uninstallOthers=get_global_config().settings.UninstallUnusedMods)

        # Ensure Git is setup and ready
        git.before_exports()

        # Export vanilla and/or requested mods
        export_values(arkman, set(mods))

        # Commit any changes
        git.after_exports()

    except:  # pylint: disable=bare-except
        logging.exception('Caught exception during automation run. Aborting.')

