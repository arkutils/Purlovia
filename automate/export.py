import re
import json
import logging
from typing import *
from datetime import datetime

import ark.discovery
import ark.properties
from ark.export_asb_values import values_for_species
from config import get_global_config, ConfigFile
from automate.ark import ArkSteamManager
from automate.version import createExportVersion

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = [
    'export_values',
]


def export_values(arkman: ArkSteamManager, modids: Set[str], include_vanilla=True):
    pretty = get_global_config().settings.PrettyJson
    exporter = Exporter(arkman, modids, include_vanilla=include_vanilla, prettyJson=pretty)
    exporter.perform()


class Exporter:
    def __init__(self, arkman: ArkSteamManager, modids: Set[str], include_vanilla=True, fullStats=False, prettyJson=False):
        self.arkman = arkman
        self.modids = modids
        self.include_vanilla = include_vanilla
        self.fullStats = fullStats
        self.prettyJson = prettyJson

        self.output_dir = get_global_config().settings.PublishDir
        self.loader = arkman.createLoader()

    def perform(self):
        self._prepare_versions()

        self.discoverer = ark.discovery.SpeciesDiscoverer(self.loader)

        if self.include_vanilla:
            logger.info('Beginning export of vanilla species')
            self._export_vanilla()

        for modid in self.modids:
            logger.info(f'Beginning mod {modid} export')
            self._export_mod(modid)

    def _prepare_versions(self):
        self.start_time = datetime.utcnow()
        self.start_time_stamp = str(int(self.start_time.timestamp()))
        self.start_time_text = self.start_time.isoformat()
        self.game_version = self.arkman.getGameVersion()
        if not self.game_version:
            raise ValueError("Game not installed or ArkSteamManager not yet initialised")

    def _create_version(self, timestamp: str) -> str:
        return createExportVersion(self.game_version, timestamp)

    def _export_vanilla(self):
        version = self._create_version(self.start_time_stamp)
        species = list(self.discoverer.discover_vanilla_species())
        species_data = self._gather_species_data(species)
        species_values = self._convert_for_export(species_data)
        self._export_values(species_values, version=version, moddata=None)

    def _export_mod(self, modid: str):
        moddata = self.arkman.getModData(modid)
        if not moddata:
            raise ValueError("Mod not installed or ArkSteamManager not yet initialised")
        version = self._create_version(moddata['version'])
        species = list(self.discoverer.discover_mod_species(modid))
        species.sort()
        species_data = self._gather_species_data(species)
        species_values = self._convert_for_export(species_data)
        self._export_values(species_values, version=version, moddata=moddata)

    def _gather_species_data(self, species):
        species_data = list()
        for assetname in species:
            asset = self.loader[assetname]
            props = ark.properties.gather_properties(asset)
            species_data.append((asset, props))
        return species_data

    def _convert_for_export(self, species_data):
        values = list()
        for asset, props in species_data:
            species_values = values_for_species(asset, props, allFields=True, fullStats=self.fullStats)
            values.append(species_values)
        return values

    def _export_values(self, species_values: List, version: str, moddata: Optional[Dict] = None):
        values: Dict[str, Any] = dict()
        values['formatVersion'] = 2

        if moddata:
            filename = moddata['id']
            values['mod'] = dict(id=moddata['id'], tag=moddata['name'], title=moddata['title'])
        else:
            filename = 'values'

        values['version'] = version
        values['generatedAt'] = self.start_time_text

        values['species'] = species_values

        fullpath = (get_global_config().settings.PublishDir / filename).with_suffix('.json')

        _save_as_json(values, fullpath, pretty=self.prettyJson)


JOIN_LINES_REGEX = re.compile(r"(?:\n\t+)?(?<=\t)([\d.-]+,?)(?:\n\t+)?")


def _format_json(data, pretty=False):
    if pretty:
        json_string = json.dumps(data, indent='\t')
        json_string = re.sub(JOIN_LINES_REGEX, r" \1", json_string)
        json_string = re.sub(r'(\d)\]', r'\1 ]', json_string)
    else:
        json_string = json.dumps(data, indent=None, separators=(',', ':'))
    return json_string


def _save_as_json(data, filename, pretty=False):
    json_string = _format_json(data, pretty)
    with open(filename, 'w') as f:
        f.write(json_string)


if __name__ == '__main__':
    mods = get_global_config().mods
    arkman = ArkSteamManager(skipInstall=True)
    arkman.ensureGameUpdated()
    arkman.ensureModsUpdated(mods, uninstallOthers=False)
    export_values(arkman, set(mods), include_vanilla=False)
