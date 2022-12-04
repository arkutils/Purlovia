from datetime import datetime, timedelta

from pydantic import BaseModel


class Run(BaseModel):
    appid: int
    output_path: str = 'output'
    stages: list[str] = []
    include_official_mods: bool = False
    mods: list[str] = []
    maps: list[str] = []
    trigger_buildid: None | bool = None
    trigger_frequency: None | timedelta = None

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
