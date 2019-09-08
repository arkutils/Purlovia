import hashlib
import json
import re
from datetime import datetime
from logging import NullHandler, getLogger
from operator import attrgetter
from pathlib import Path
from typing import *

import ark.discovery
import ark.properties
from ark.common import PGD_PKG
from ark.export_asb_values import values_for_species, values_from_pgd
from automate.ark import ArkSteamManager
from automate.version import createExportVersion
from config import ConfigFile, get_global_config
from ue.loader import AssetLoadException
from ue.utils import property_serialiser
from utils.strings import get_valid_filename

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'export_values',
]


def export_values(arkman: ArkSteamManager, modids: Set[str], config: ConfigFile):
    logger.info('Export beginning')
    if config.settings.SkipExtract or config.export_asb.Skip:
        logger.info('(skipped)')
        return

    # Ensure the output directory exists
    outdir = config.settings.OutputPath
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

        if self.config.export_asb.ExportVanillaSpecies:
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

        other: Dict[str, Any] = dict()
        other.update(self._gather_color_data(PGD_PKG, require_override=False))

        self._export_values(species_values, version=version, moddata=None, other=other)

    def _export_mod(self, modid: str):
        moddata = self.arkman.getModData(modid)
        if not moddata:
            raise ValueError("Mod not installed or ArkSteamManager not yet initialised")
        version = self._create_version(moddata['version'])
        species = list(self.discoverer.discover_mod_species(modid))
        species.sort()
        species_data = self._gather_species_data(species)
        species_values = self._convert_for_export(species_data, True)

        other: Dict[str, Any] = dict()
        mod_pgd = moddata.get('package', None)
        if mod_pgd:
            other.update(self._gather_color_data(mod_pgd, require_override=True))
        else:
            logger.warning(f'PrimalGameData information missing for mod {modid}')

        self._export_values(species_values, version=version, moddata=moddata, other=other)

    def _gather_color_data(self, pgd_assetname: str, require_override: bool = False) -> Dict[str, Any]:
        asset = self.loader[pgd_assetname]
        color_data = values_from_pgd(asset, require_override=require_override)
        return color_data

    def _gather_species_data(self, species):
        species_data = list()
        for assetname in species:
            asset = self.loader[assetname]

            props = None
            try:
                props = ark.properties.gather_properties(asset)
            except AssetLoadException as ex:
                logger.warning(f'Gathering properties failed for {assetname}: %s', str(ex))
            except:  # pylint: disable=bare-except
                logger.warning(f'Gathering properties failed for {assetname}', exc_info=True)

            if props:
                species_data.append((asset, props))

        return species_data

    def _convert_for_export(self, species_data, _ismod: bool):
        values = list()
        for asset, props in species_data:
            species_values = None
            try:
                species_values = values_for_species(asset,
                                                    props,
                                                    allFields=True,
                                                    fullStats=not self.config.export_asb.Export8Stats,
                                                    includeBreeding=True,
                                                    includeColor=True)
            except:  # pylint: disable=bare-except
                logger.warning(f'Export conversion failed for {asset.assetname}', exc_info=True)

            if species_values:
                values.append(species_values)

        return values

    def _export_values(self, species_values: List, version: str, other: Dict = None, moddata: Optional[Dict] = None):
        values: Dict[str, Any] = dict()
        values['format'] = "1.12"

        if moddata:
            filename = f"{moddata['id']}-{moddata['name']}"
            filename = get_valid_filename(filename)
            title = moddata['title'] or moddata['name']
            values['mod'] = dict(id=moddata['id'], tag=moddata['name'], title=title)
        else:
            filename = 'values'

        values['version'] = version
        values['species'] = species_values

        if other:
            values.update(other)

        fullpath = (self.config.settings.OutputPath / self.config.export_asb.PublishSubDir / filename).with_suffix('.json')
        self._save_json_if_changed(values, fullpath)

    def _save_json_if_changed(self, values: Dict[str, Any], fullpath: Path):
        changed, version = _should_save_json(values, fullpath)
        if changed:
            pretty = self.config.export_asb.PrettyJson
            logger.info(f'Saving export to {fullpath} with version {version}')
            values['version'] = version
            _save_as_json(values, fullpath, pretty=pretty)
        else:
            logger.info(f'No changes to {fullpath}')


def _should_save_json(values: Dict[str, Any], fullpath: Path) -> Tuple[bool, str]:
    '''
    Works out if a file needs to be saved and with which version number.

    This is calculated using the digest of its content, excluding the version field.
    Also handles cases where the content has changed but the version has not, by bumping the build number.

    Returns a tuple of (changed, version), where `changed` is a boolean saying whether the data needs to be
    saved and `version` is the version number to use.
    '''
    new_version: str = values.get('version', None)
    if not new_version:
        raise ValueError('Export data must contain a version field')

    # Load the existing file
    try:
        with open(fullpath) as f:
            existing_data = json.load(f)
    except:  # pylint: disable=bare-except
        # Old file doesn't exist/isn't readable/is corrupt
        return (True, new_version)

    # Can only do this with dictionaries
    if not isinstance(existing_data, dict):
        return (True, new_version)

    # Get the old and new versions and digests
    _, new_digest = _calculate_digest(values)
    old_version, old_digest = _calculate_digest(existing_data)

    # If content hasn't changed, don't save regardless of any version changes
    if new_digest == old_digest:
        return (False, old_version or new_version)

    # Content has changed... if the version is changed also then we're done
    assert old_version
    old_parts = [int(v) for v in old_version.strip().split('.')]
    new_parts = [int(v) for v in new_version.strip().split('.')]
    if old_parts[:3] != new_parts[:3]:
        return (True, new_version)

    # Content has changed but version hasn't... bump build number
    parts = old_parts
    parts = parts + [0] * (4 - len(parts))
    parts[3] += 1
    bumped_version = '.'.join(str(v) for v in parts)

    return (True, bumped_version)


def _calculate_digest(values: Dict[str, Any]) -> Tuple[Optional[str], str]:
    '''Calculates the digest of the given data, returning a tuple of (version, digest).'''
    assert isinstance(values, dict)

    # Take a shallow copy of the data and remove the version field
    values = dict(values)
    version: Optional[str] = values.pop('version', None)

    # Calculate the digest of the minified output, using SHA512
    as_bytes = _format_json(values, pretty=False).encode('utf8')
    digest = hashlib.sha512(as_bytes).hexdigest()

    return (version, digest)


JOIN_LINES_REGEX = re.compile(r"(?:\n\t+)?(?<=\t)([\d.-]+,?)(?:\n\t+)?")
JOIN_COLORS_REGEX = re.compile(r"\[\n\s+([\w\" ]+),\n\s+(.{,90})\n\s+\]")
SHRINK_EMPTY_COLOR_REGEX = re.compile(r"\{\n\s+(\"\w+\": \w+)\n\s+\}")


def _format_json(data, pretty=False):
    if pretty:
        json_string = json.dumps(data, default=property_serialiser, indent='\t')
        json_string = re.sub(JOIN_LINES_REGEX, r" \1", json_string)
        json_string = re.sub(JOIN_COLORS_REGEX, r"[ \1, \2 ]", json_string)
        json_string = re.sub(SHRINK_EMPTY_COLOR_REGEX, r"{ \1 }", json_string)
        json_string = re.sub(r'(\d)\]', r'\1 ]', json_string)
    else:
        json_string = json.dumps(data, default=property_serialiser, indent=None, separators=(',', ':'))
    return json_string


def _save_as_json(data, filename, pretty=False):
    json_string = _format_json(data, pretty)
    with open(filename, 'w', newline='\n') as f:
        f.write(json_string)
