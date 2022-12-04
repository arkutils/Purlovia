from datetime import datetime
from random import randint

import requests

from utils.log import get_logger

from .types import Run, RunStatus

__all__ = ('collect_trigger_values', 'add_manual_trigger', 'should_run', 'update_cache')

logger = get_logger(__name__)

trigger_now: datetime = datetime.utcnow()
trigger_buildids: dict[int, int] = {}
trigger_manuals: set[str] = set()


def collect_trigger_values(config: dict[str, Run], fake_buildids: bool = False):
    global trigger_now, trigger_buildids

    trigger_now = datetime.utcnow()
    trigger_buildids.clear()

    used_appids = {run.appid for run in config.values() if run.trigger_buildid}

    for appid in used_appids:
        trigger_buildids[appid] = randint(900_000, 999_999) if fake_buildids else _get_buildid_for_appid(appid)


def add_manual_trigger(name: str):
    trigger_manuals.add(name.lower())


def should_run(name: str, run: Run, status: None | RunStatus) -> bool:
    # Check the buildid trigger
    if run.trigger_buildid is not None:
        if not status:
            logger.info('Triggered by BuildId and never run before')
            return True

        # If the buildid has changed, we should run
        if status.last_buildid != trigger_buildids[run.appid]:
            logger.info('BuildId has changed from %s to %s', status.last_buildid, trigger_buildids[run.appid])
            return True

    # Check the frequency trigger
    if run.trigger_frequency is not None:
        if not status:
            logger.info('Triggered by frequency and never run before')
            return True

        if status.last_run_time is None:
            logger.info('Triggered by frequency and never run before')
            return True

        # If the last run time is too long ago, we should run
        if trigger_now - status.last_run_time >= run.trigger_frequency:
            logger.info('Triggered by frequency and past due')
            return True

    # Check manual triggers
    if name.lower() in trigger_manuals:
        logger.info('Triggered manually')
        return True

    logger.info('No trigger found')
    return False


def update_cache(name: str, run: Run, cache: dict[str, RunStatus]):
    cache_entry = cache.setdefault(name, RunStatus())
    cache_entry.last_run_time = trigger_now
    logger.debug('Updated last run time for %s to %s', name, trigger_now)

    if run.trigger_buildid is not None:
        cache_entry.last_buildid = trigger_buildids[run.appid]
        logger.debug('Updated build id for %s to %d', name, cache_entry.last_buildid)


def _get_buildid_for_appid(appid: int) -> int:
    # Currently uses steamcmd.net, but could be changed to use our local steamcmd if necessary
    url = f'https://api.steamcmd.net/v1/info/{appid}'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    buildid = data['data'][str(appid)]['depots']['branches']['public']['buildid']
    return int(buildid)
