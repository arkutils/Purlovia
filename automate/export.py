import re
import json
import logging
from operator import attrgetter
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


def export_values(arkman: ArkSteamManager, modids: Set[str], config: ConfigFile):
    logger.info('Export beginning')
    if config.settings.SkipExtract:
        logger.info('(skipped)')
        return

    # Ensure the output directory exists
    outdir = config.settings.PublishDir
    outdir.mkdir(parents=True, exist_ok=True)

    # Export based on current config
    exporter = Exporter(arkman, modids, config)
    exporter.perform()

    logger.info('Export complete')


class Exporter:
    def __init__(self, arkman: ArkSteamManager, modids: Set[str], config: ConfigFile):
        self.config = config
        self.arkman = arkman
        self.modids = modids
        self.loader = arkman.createLoader()
        self.discoverer = ark.discovery.SpeciesDiscoverer(self.loader)
        self.game_version = self.arkman.getGameVersion()

    def perform(self):
        self._prepare_versions()

        if self.config.settings.ExportVanillaSpecies:
            logger.info('Beginning export of vanilla species')
            self._export_vanilla()

        for modid in self.modids:
            logger.info(f'Beginning mod {modid} export')
            self._export_mod(modid)

            # Remove assets with this mod's prefix from the cache
            prefix = '/Game/Mods/' + self.loader.get_mod_name('/Game/Mods/' + modid)
            self.loader.wipe_cache_with_prefix(prefix)

    def _prepare_versions(self):
        if not self.game_version:
            raise ValueError("Game not installed or ArkSteamManager not yet initialised")

    def _create_version(self, timestamp: str) -> str:
        return createExportVersion(self.game_version, timestamp)  # type: ignore

    def _export_vanilla(self):
        game_buildid = self.arkman.getGameBuildId()
        version = self._create_version(game_buildid)
        species = list(self.discoverer.discover_vanilla_species())
        species.sort()
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

            props = None
            try:
                props = ark.properties.gather_properties(asset)
            except:  # pylint: disable=bare-except
                logger.warning(f'Gathering properties failed for {assetname}', exc_info=True)

            if props:
                species_data.append((asset, props))

        return species_data

    def _convert_for_export(self, species_data, ismod: bool):
        values = list()
        for asset, props in species_data:
            species_values = None
            try:
                species_values = values_for_species(asset,
                                                    props,
                                                    allFields=True,
                                                    fullStats=not self.config.settings.Export8Stats,
                                                    includeBreeding=True,
                                                    includeColor=not ismod)
            except:  # pylint: disable=bare-except
                logger.warning(f'Export conversion failed for {asset.assetname}', exc_info=True)

            if species_values:
                values.append(species_values)

        return values

    def _export_values(self, species_values: List, version: str, moddata: Optional[Dict] = None):
        values: Dict[str, Any] = dict()
        values['formatVersion'] = "1.12"

        if moddata:
            filename = moddata['name']
            title = moddata['title'] or moddata['name']
            values['mod'] = dict(id=moddata['id'], tag=moddata['name'], title=title)
        else:
            filename = 'values'

        values['version'] = version
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
