from configparser import ConfigParser
from pathlib import Path
from typing import *

from pydantic import BaseModel, validator

__all__ = [
    'get_global_config',
    'force_reload',
    'ConfigFile',
    'SettingsSection',
    'OptimisationSection',
    'ModIdAccess',
]

FILENAME = 'config/config.ini'


class IniStringList(list):
    '''A validated type that converts a newline-separated string list into a proper Python list.'''
    @classmethod
    def __get_validators__(cls):
        yield cls.convert

    @classmethod
    def convert(cls, v):
        if isinstance(v, (list, tuple)):
            return v
        if isinstance(v, str):
            v = v.strip().replace('\r\n', '\n').split('\n')
            return v
        raise ValueError('Expected string list')


class SettingsSection(BaseModel):
    UninstallUnusedMods: bool = True
    Export8Stats: bool = False
    ExportVanillaSpecies: bool = False
    PrettyJson: bool = False

    SeparateOfficialMods: IniStringList = IniStringList()

    DataDir: Path = Path('livedata')
    GitDirectory: Path = Path('output')
    PublishDir: Path = Path('output/data/asb')

    EnableGit: bool = False
    GitBranch: str = 'master'
    GitUseReset: bool = False
    GitUseIdentity: bool = False

    SkipInstall: bool = False
    SkipExtract: bool = False
    SkipCommit: bool = False
    SkipPull: bool = False
    SkipPush: bool = False


class SettingsWikiSection(BaseModel):
    SkipExtract: bool = False
    ExportVanillaMaps: bool = True
    ExportSpawnData: bool = False
    ExportBiomeData: bool = False
    ExportSupplyCrateData: bool = False

    PublishDir: Path = Path('output/data/wiki')


class OptimisationSection(BaseModel):
    SearchIgnore: IniStringList = IniStringList()


class ModIdAccess:
    '''Provide bi-directional access to a modid <-> tag dictionary.'''
    ids_to_tags: Dict[str, str]
    tags_to_ids: Dict[str, str]

    def __init__(self, source: Dict[str, str], keyed_by_id=False):
        if keyed_by_id:
            self.ids_to_tags = {k.lower(): v for k, v in source.items()}
            self.tags_to_ids = {v.lower(): k for k, v in source.items()}
        else:
            self.ids_to_tags = {v.lower(): k for k, v in source.items()}
            self.tags_to_ids = {k.lower(): v for k, v in source.items()}

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return value

    def ids(self) -> List[str]:
        return list(self.tags_to_ids.values())

    def tags(self) -> List[str]:
        return list(self.ids_to_tags.values())

    def id_from_tag(self, tag: str):
        return self.tags_to_ids.get(tag.lower(), None)

    def tag_from_id(self, modid: str):
        return self.ids_to_tags.get(modid.lower(), None)


class ConfigFile(BaseModel):
    settings: SettingsSection
    wiki_settings: SettingsWikiSection
    maps: Tuple[str, ...] = tuple()
    mods: Tuple[str, ...] = tuple()
    official_mods: ModIdAccess = ModIdAccess(dict())
    optimisation: OptimisationSection


config: Optional[ConfigFile] = None
parser: Optional[ConfigParser] = None


def get_global_config() -> ConfigFile:
    _ensure_loaded()
    assert config is not None
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
    official_mods = ModIdAccess(parser['official-mods'], keyed_by_id=False)
    maps = list(parser['maps'].values())

    settings = SettingsSection(**parser['settings'])
    wiki_settings = SettingsWikiSection(**parser['settings-wiki'])
    optimisation = OptimisationSection(**parser['optimisation'])

    global config
    config = ConfigFile(settings=settings,
                        wiki_settings=wiki_settings,
                        mods=managed_mods,
                        official_mods=official_mods,
                        maps=maps,
                        optimisation=optimisation)
