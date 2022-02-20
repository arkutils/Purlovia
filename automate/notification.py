import os.path
from traceback import format_exc
from typing import List

import requests

from config import ConfigFile, get_global_config
from utils.log import get_logger

logger = get_logger(__name__)

__all__ = [
    'handle_exception',
]


def get_log_tail(filename: str, lines: int = 3) -> List[str]:
    buffer: List[str] = []
    with open(filename, 'rt', encoding='utf-8', buffering=4096) as f:
        for line in f.readlines():
            buffer = buffer[:lines - 1]
            buffer.append(line)

    return buffer


def send_to_discord(log: List[str], exception: List[str] = None, header: str = ''):
    header = header or 'Purlovia ran into an error:'
    if not header.endswith('\n'):
        header = header + '\n'

    hook_url = os.environ.get('PURLOVIA_DISCORD_HOOK', None)
    if not hook_url:
        logger.warning("Discord notification aborted due to missing PURLOVIA_DISCORD_HOOK")
        return

    role_id = os.environ.get('PURLOVIA_DISCORD_ROLE', None)
    if role_id:
        header = f'<@&{role_id}> {header}'

    base_path = os.path.abspath('.') + os.path.sep

    if not exception:
        content = ''.join([header, '```log\n', *log, '```\n'])
    else:
        for n in range(len(exception) - 1):
            lines = [header, '```log\n', *log, '```\n'
                     '```py\n', *exception[n:], '```\n']
            content = ''.join(lines)
            content = content.replace(base_path, '')
            if len(content) < 1990:
                break
        else:
            content = header + '\n...which could not fit into a Discord message :('

    try:
        requests.post(url=hook_url, data=dict(content=content))
    except IOError:
        logger.exception("Failed to send Discord error notification")


def handle_exception(logfile: str, loglines=3, config: ConfigFile = get_global_config()):
    if not config.errors.SendNotifications:
        return

    # Ensure all existing logs are flushed
    for handler in logger.root.handlers:
        handler.flush()

    # Grab the last few lines of the log
    log: List[str] = get_log_tail(logfile, loglines)
    exception: List[str] = format_exc()  # type: ignore

    send_to_discord(log, exception, config.errors.MessageHeader)
