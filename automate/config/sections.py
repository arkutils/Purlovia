from pathlib import Path
from typing import Dict, Optional, Tuple

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
    ExportSpecies: bool = True

    class Config:
        extra = Extra.forbid


class ExportWikiSection(ExportSection):
    ExportMaps: bool = True
    ExportVanillaMaps: bool = True
    ExportSpawningGroups: bool = True
    ExportEngrams: bool = True
    ExportItems: bool = True
    ExportDrops: bool = True
    ExportLootCrates: bool = True
    ExportSpecies: bool = True
    ExportTrades: bool = True
    ExportMissions: bool = True

    class Config:
        extra = Extra.forbid


class ProcessingSection(BaseModel):
    ProcessSpawns: bool = True
    ProcessBiomes: bool = True

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
    processing: ProcessingSection

    run_sections: Dict[str, bool] = {'': True}
    display_sections: bool = False

    official_mods: ModIdAccess = ModIdAccess(dict())
    mods: Tuple[str, ...] = tuple()
    extract_mods: Optional[Tuple[str, ...]] = None
    extract_maps: Optional[Tuple[str, ...]] = None

    class Config:
        alias_generator = snake_to_kebab
