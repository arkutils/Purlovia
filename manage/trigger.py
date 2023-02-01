from datetime import datetime
from pathlib import Path
from random import randint
from typing import Iterable

from automate.ark import getGameBuildId
from automate.steamcmd import Steamcmd
from utils.log import get_logger

from .types import Run, RunStatus

__all__ = ('collect_trigger_values', 'add_manual_trigger', 'should_run', 'update_cache')

logger = get_logger(__name__)

trigger_time: datetime = datetime.utcnow()
last_buildid_by_appid: dict[int, int] = {}
manual_triggers: set[str] = set()


def collect_trigger_values(config: dict[str, Run], fake_buildids: bool = False):
    global trigger_time, last_buildid_by_appid

    trigger_time = datetime.utcnow()
    last_buildid_by_appid.clear()

    used_appids = {run.appid for run in config.values() if run.triggers.buildid}

    if fake_buildids:
        for appid in used_appids:
            last_buildid_by_appid[appid] = randint(900_000, 999_999)
    else:
        for appid, buildid in _get_live_buildids_for_appids(used_appids).items():
            last_buildid_by_appid[appid] = buildid


def add_manual_trigger(name: str):
    manual_triggers.add(name.lower())


def should_run(name: str, run: Run, status: None | RunStatus) -> bool:
    # Check the buildid trigger
    if run.triggers.buildid is not None:
        if not status:
            logger.info('Triggered by BuildId and never run before')
            return True

        # If the buildid has changed, we should run
        if status.last_buildid != last_buildid_by_appid[run.appid]:
            logger.info('BuildId has changed from %s to %s', status.last_buildid, last_buildid_by_appid[run.appid])
            return True

    # Check the frequency trigger
    if run.triggers.frequency is not None:
        if not status:
            logger.info('Triggered by frequency and never run before')
            return True

        if status.last_run_time is None:
            logger.info('Triggered by frequency and never run before')
            return True

        # If the last run time is too long ago, we should run
        if trigger_time - status.last_run_time >= run.triggers.frequency:
            logger.info('Triggered by frequency and past due')
            return True

    # Check manual triggers
    if name.lower() in manual_triggers:
        logger.info('Triggered manually')
        return True

    logger.info('No trigger found')
    return False


def update_cache(name: str, run: Run, cache: dict[str, RunStatus]):
    cache_entry = cache.setdefault(name, RunStatus())
    cache_entry.last_run_time = trigger_time
    logger.debug('Updated last run time for %s to %s', name, trigger_time)

    if run.triggers.buildid is not None:
        # Read the used buildid from the appmanifest file
        used_buildid = _get_used_buildid_for_appid(run.appid)
        cache_entry.last_buildid = used_buildid
        logger.debug('Updated build id for %s to %d', name, used_buildid)


def _get_live_buildids_for_appids(appids: Iterable[int]) -> dict[int, int]:
    logger.info('Fetching live buildids from Steam')
    steamcmd = Steamcmd('livedata/Steam')
    data = steamcmd.get_app_info(appids)
    return {int(appid): int(data[str(appid)]['depots']['branches']['public']['buildid']) for appid in appids}


def _get_used_buildid_for_appid(appid: int) -> int:
    # Read the buildid from the appmanifest file
    game_path = Path(f'livedata/app-{appid}')
    buildid = getGameBuildId(game_path, appid)
    return int(buildid)
