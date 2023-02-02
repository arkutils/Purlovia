from datetime import datetime, timedelta

from pydantic import BaseModel


class Triggers(BaseModel):
    buildid: None | bool = None
    frequency: None | timedelta = None
    manual: bool = True

    class Config:
        extra = 'forbid'


class Run(BaseModel):
    appid: int
    config: str
    stages: list[str] = []
    include_official_mods: bool = False
    mods: list[str] | None = None
    maps: list[str] | None = None
    triggers: Triggers = Triggers()

    class Config:
        extra = 'forbid'


class ConfigFile(BaseModel):
    __root__: dict[str, Run] = {}

    class Config:
        extra = 'forbid'


class RunStatus(BaseModel):
    last_run_time: None | datetime = None
    last_buildid: int = 0

    class Config:
        extra = 'forbid'


class StatusFile(BaseModel):
    __root__: dict[str, RunStatus] = {}

    class Config:
        extra = 'forbid'
