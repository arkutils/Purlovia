from pathlib import Path
from typing import Optional, Tuple

from pydantic import BaseModel, Extra, UrlStr

from utils.name_convert import snake_to_kebab

from .util_types import IniStringList, ModIdAccess


class SettingsSection(BaseModel):
    DataDir: Path = Path('livedata')
    OutputPath: Path = Path('output')

    SeparateOfficialMods: IniStringList = IniStringList()

    SkipGit: bool = False
    SkipExtract: bool = False
    SkipInstall: bool = False

    class Config:
        extra = Extra.forbid


class DevSection(BaseModel):
    DevMode: bool = True
    ClearHierarchyCache: bool = False

    class Config:
        extra = Extra.forbid


class SteamCmdSection(BaseModel):
    RetryCount: int = 5
    UninstallUnusedMods: bool = True

    class Config:
        extra = Extra.forbid


class GitSection(BaseModel):
    Branch: str = 'master'
    UseReset: bool = False
    UseIdentity: bool = False

    SkipCommit: bool = False
    SkipPull: bool = False
    SkipPush: bool = False

    class Config:
        extra = Extra.forbid


class ErrorsSection(BaseModel):
    SendNotifications: bool = False
    MessageHeader: str = 'Purlovia ran into an error:'

    class Config:
        extra = Extra.forbid


class ExportDefaultsSection(BaseModel):
    PrettyJson: bool = True


class ExportSection(ExportDefaultsSection):
    Skip: bool = False
    PrettyJson: Optional[bool] = None  # type: ignore  # pydantic allows this so shush
    PublishSubDir: Path
    CommitHeader: str


class ExportASBSection(ExportSection):
    class Config:
        extra = Extra.forbid


class ExportWikiSection(ExportSection):
    ExportVanillaMaps: bool = True
    ExportSpawnData: bool = True
    ExportBiomeData: bool = True
    ExportSupplyCrateData: bool = True
    ExportVeinLocations: bool = True
    ExportNestLocations: bool = True

    class Config:
        extra = Extra.forbid


class OptimisationSection(BaseModel):
    SearchIgnore: IniStringList = IniStringList()

    class Config:
        extra = Extra.forbid


# ...and one class to rule them all
class ConfigFile(BaseModel):
    settings: SettingsSection
    dev: DevSection
    steamcmd: SteamCmdSection
    git: GitSection
    errors: ErrorsSection
    optimisation: OptimisationSection

    export_asb: ExportASBSection
    export_wiki: ExportWikiSection

    maps: Tuple[str, ...] = tuple()
    official_mods: ModIdAccess = ModIdAccess(dict())
    mods: Tuple[str, ...] = tuple()

    class Config:
        alias_generator = snake_to_kebab
