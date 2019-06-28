import logging
from typing import *
from datetime import datetime

from config import get_global_config, ConfigFile
from automate.ark import ArkSteamManager

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = [
    'export_values',
]


def export_values(arkman: ArkSteamManager, modids: Set[str], include_vanilla=True):
    exporter = Exporter(arkman, modids, include_vanilla=include_vanilla)
    exporter.perform()


class Exporter:
    def __init__(self, arkman: ArkSteamManager, modids: Set[str], include_vanilla=True):
        self.arkman = arkman
        self.modids = modids
        self.include_vanilla = include_vanilla

        self.output_dir = get_global_config().settings.PublishDir
        self.loader = arkman.createLoader()

    def perform(self):
        self._prepare_versions()

        if self.include_vanilla:
            self._export_vanilla()

        for modid in self.modids:
            self._export_mod(modid)

    def _prepare_versions(self):
        self.start_time = datetime.utcnow()
        self.start_time_stamp = str(int(self.start_time.timestamp()))
        self.start_time_text = self.start_time.isoformat()
        self.game_version = _clean_game_version(self.arkman.fetchGameVersion())

    def _create_version(self, timestamp: str) -> str:
        return f'{self.game_version}.{timestamp}'

    def _export_vanilla(self):
        version = self._create_version(self.start_time_stamp)
        species = discover_vanilla_species()
        species_data = gather_species_data(species)
        export_values(species_data, version=version, moddata=None)

    def _export_mod(self, modid: str):
        moddata = self.arkman.getModInfo(modid)
        version = self._create_version(moddata.version)
        species = discover_vanilla_species()
        species_data = gather_species_data(species)
        export_values(species_data, version=version, moddata=None)


def _clean_game_version(version: str) -> str:
    version = version.strip().strip('.')
    if version.count('.') < 1:
        version += '.0'
    return version
