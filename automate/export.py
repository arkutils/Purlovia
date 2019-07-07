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


def export_values(arkman: ArkSteamManager, modids: Set[str]):
    config = get_global_config()
    logger.info('Export beginning')

    # Ensure the output directory exists
    outdir = config.settings.PublishDir
    outdir.mkdir(parents=True, exist_ok=True)

    # Export based on current config
    exporter = Exporter(arkman, modids)
    exporter.perform()

    logger.info('Export complete')


class Exporter:
    def __init__(self, arkman: ArkSteamManager, modids: Set[str], config: ConfigFile=None):
        self.config = config = config or get_global_config()
        self.arkman = arkman
        self.modids = modids
        self.loader = arkman.createLoader()
        self.discoverer = ark.discovery.SpeciesDiscoverer(self.loader)
        self.game_version = self.arkman.getGameVersion()

        self.start_time_stamp = ''
        self.start_time_text = ''

    def perform(self):
        self._prepare_versions()

        if self.config.settings.ExportVanillaSpecies:
            logger.info('Beginning export of vanilla species')
            self._export_vanilla()

        for modid in self.modids:
            logger.info(f'Beginning mod {modid} export')
            self._export_mod(modid)

    def _prepare_versions(self):
        start_time = datetime.utcnow()
        self.start_time_stamp = str(int(start_time.timestamp()))
        self.start_time_text = start_time.isoformat()
        if not self.game_version:
            raise ValueError("Game not installed or ArkSteamManager not yet initialised")

    def _create_version(self, timestamp: str) -> str:
        return createExportVersion(self.game_version, timestamp) # type: ignore

    def _export_vanilla(self):
        version = self._create_version(self.start_time_stamp)
        species = list(self.discoverer.discover_vanilla_species())
        species_data = self._gather_species_data(species)
        species_values = self._convert_for_export(species_data, False)
        self._export_values(species_values, version=version, moddata=None)

    def _export_mod(self, modid: str):
        moddata = self.arkman.getModData(modid)
        if not moddata:
            raise ValueError("Mod not installed or ArkSteamManager not yet initialised")
        version = self._create_version(moddata['version'])
        species = list(self.discoverer.discover_mod_species(modid))
        species.sort()
        species_data = self._gather_species_data(species)
        species_values = self._convert_for_export(species_data, True)
        self._export_values(species_values, version=version, moddata=moddata)

    def _gather_species_data(self, species):
        species_data = list()
        for assetname in species:
            asset = self.loader[assetname]
            props = ark.properties.gather_properties(asset)
            species_data.append((asset, props))
        return species_data

    def _convert_for_export(self, species_data, ismod: bool):
        values = list()
        for asset, props in species_data:
            species_values = values_for_species(asset,
                                                props,
                                                allFields=True,
                                                fullStats=not self.config.settings.Export8Stats,
                                                includeBreeding=True,
                                                includeColor=not ismod)
            values.append(species_values)
        return values

    def _export_values(self, species_values: List, version: str, moddata: Optional[Dict] = None):
        values: Dict[str, Any] = dict()
        values['formatVersion'] = 2

        if moddata:
            filename = moddata['name']
            values['mod'] = dict(id=moddata['id'], tag=moddata['name'], title=moddata['title'])
        else:
            filename = 'values'

        values['version'] = version
        values['generatedAt'] = self.start_time_text

        values['species'] = species_values

        fullpath = (self.config.settings.PublishDir / filename).with_suffix('.json')

        pretty = self.config.settings.PrettyJson
        logger.info(f'Saving export to {fullpath}{(" (with pretty json)" if pretty else "")}')
        _save_as_json(values, fullpath, pretty=pretty)


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


def temporary_main(logdir:str='logs'):
    # All of this should not be here, but is it's temporary resting place

    # Ensure log directory exists before starting the logging system
    from pathlib import Path
    from .logging import setup_logging
    Path(logdir).mkdir(parents=True, exist_ok=True)
    setup_logging(path='config/logging.yaml', level=logging.INFO)

    # Run update then export
    try:
        mods = get_global_config().mods
        arkman = ArkSteamManager()
        arkman.ensureSteamCmd()
        arkman.ensureGameUpdated()
        arkman.ensureModsUpdated(mods, uninstallOthers=get_global_config().settings.UninstallUnusedMods)
        export_values(arkman, set(mods))
    except:  # pylint: disable=bare-except
        logging.exception('Caught exception during automation run. Aborting.')


if __name__ == '__main__':
    temporary_main()
