from typing import Dict, List
from pathlib import Path
from configparser import ConfigParser

from pydantic import BaseModel, validator

__all__ = [
    'get_global_config',
    'ensure_loaded',
    'force_reload',
    'ConfigFile',
    'SettingsSection',
]

FILENAME = 'config.ini'


class SettingsSection(BaseModel):
    DataDir: Path = 'livedata'
    PublishDir: Path = 'output'
    UninstallUnusedMods: bool = True
    GitCommit: bool = False
    GitBranch: str = 'automated-values'


class ConfigFile(BaseModel):
    settings: SettingsSection
    mods: List[str] = tuple()
    official_mods: Dict[str, str] = dict()

    @validator('official_mods', whole=True)
    def reverse_official_mods(cls, value, values):
        # Intercept official mods and created dictionaries in both directions
        values['official_mods__name_to_id'] = {k.lower(): v for k, v in value.items()}
        values['official_mods__id_to_name'] = {v.lower(): k for k, v in value.items()}
        return value

    def is_official_mod(self, modid):
        return modid in self.official_mods__id_to_name

    def official_mod_name_from_id(self, modid):
        return self.official_mods__id_to_name.get(modid, None)

    def official_mod_name_from_id(self, name):
        return self.official_mods__name_to_id.get(name, None)


def get_global_config() -> ConfigFile:
    _ensure_loaded()
    return config


def force_reload():
    global config
    config = None
    _ensure_loaded()


def _ensure_loaded():
    if not config:
        _read_config(FILENAME)


def _read_config(filename):
    global parser
    parser = ConfigParser(inline_comment_prefixes='#;')
    parser.optionxform = lambda v: v  # keep exact case of mod names, please
    parser.read(filename)

    managed_mods = list(parser['mods'].keys())
    official_mods = {k: v for k, v in parser['official-mods'].items()}

    settings = SettingsSection(**parser['settings'])

    global config
    config = ConfigFile(settings=settings, mods=managed_mods, official_mods=official_mods)


config = None
parser = None
