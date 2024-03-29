from typing import Optional

from automate.config.reader import read_config
from automate.config.sections import ConfigFile

__all__ = [
    'get_global_config',
    'force_reload',
    'switch_config',
    'ConfigFile',
    'OVERRIDE_FILENAME',
    'LOGGING_FILENAME',
    'HIERARCHY_FILENAME',
    'ROOT_LOGGER',
]

CONFIG_FILENAME = 'config/config.ini'
OVERRIDE_FILENAME = 'config/overrides.yaml'
LOGGING_FILENAME = 'config/logging.yaml'
HIERARCHY_FILENAME = 'config/hierarchy.yaml'
ROOT_LOGGER = ''

config: Optional[ConfigFile] = None


def get_global_config() -> ConfigFile:
    _ensure_loaded()
    assert config is not None
    return config


def force_reload():
    global config  # pylint: disable=global-statement
    config = None
    _ensure_loaded()


def switch_config(filename: str):
    global config  # pylint: disable=global-statement
    config = read_config(filename)
    return config


def _ensure_loaded():
    global config  # pylint: disable=global-statement
    if not config:
        config = read_config(CONFIG_FILENAME)
