import json
import re
import shutil
from os import walk
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Set, Union

import requests

from config import ConfigFile, get_global_config
from ue.loader import AssetLoader, ModNotFound, ModResolver
from utils.log import get_logger
from utils.name_convert import uelike_prettify

from .modutils import readACFFile, readModInfo, readModMetaInfo, unpackModFile
from .steamapi import SteamApi
from .steamcmd import Steamcmd

__all__ = ('ArkSteamManager', )

ARK_SERVER_APP_ID = 376030
ARK_MAIN_APP_ID = 346110

MODDATA_FILENAME = '_moddata.json'

logger = get_logger(__name__)


class DownloadError(Exception):
    ...


class ArkSteamManager:
    def __init__(self, config: ConfigFile = get_global_config()):
        self.config = config
        self.basepath: Path = Path(config.settings.DataDir).absolute()

        self.steamcmd_path: Path = self.basepath / 'Steam'
        self.gamedata_path: Path = self.basepath / 'game'
        self.asset_path: Path = self.gamedata_path / 'ShooterGame'
        self.mods_path: Path = self.asset_path / 'Content' / 'Mods'

        self.steamcmd = Steamcmd(self.steamcmd_path)

        self.steam_mod_details: Optional[Dict[str, Dict]] = None  # from steam
        self.mod_data_cache: Optional[Dict[str, Dict]] = None  # internal data
        self.game_version: Optional[str] = None
        self.game_buildid: Optional[str] = None

        self.loader: Optional[AssetLoader] = None

        self._sanityCheck()

    def getLoader(self) -> AssetLoader:
        if not self.loader:
            self.loader = self.createLoader()

        return self.loader

    def createLoader(self) -> AssetLoader:
        '''Create an asset loader pointing at the managed game install.'''
        modresolver = ManagedModResolver(self)
        loader = AssetLoader(modresolver, self.asset_path)
        return loader

    def getInstalledMods(self) -> Optional[Dict[str, Dict]]:
        '''
        Scan installed modules and return their information in a Dict[id->data].
        Returns None if mods have not been evaluated yet.
        '''
        return self.mod_data_cache

    def getModData(self, modid: str) -> Optional[Dict[str, Any]]:
        modid = str(modid)

        # Official "mods" get a custom moddata using the game's version
        if modid in self.config.official_mods.ids():
            data = dict(id=modid)
            data['version'] = self.getGameBuildId() or '0'
            data['name'] = self.config.official_mods.tag_from_id(modid)
            data['title'] = data['name']
            return data

        if self.mod_data_cache:
            return self.mod_data_cache.get(modid, None)

        moddata = readModData(self.asset_path, modid)
        return moddata

    def getGameVersion(self) -> Optional[str]:
        '''
        Return the installed game version.
        Returns None if not installed is not yet evaluated.
        '''
        return self.game_version

    def getGameBuildId(self) -> Optional[str]:
        '''
        Return the installed game's build ID (a simply incrementing version number of the Steam depot).
        Returns None if not installed is not yet evaluated.
        '''
        return self.game_buildid

    def getContentPath(self) -> Path:
        '''Return the Content directory of the game.'''
        return self.asset_path

    def ensureSteamCmd(self):
        logger.info('Ensuring SteamCMD is installed')
        self.steamcmd_path.mkdir(parents=True, exist_ok=True)
        self.steamcmd.install()

    def ensureGameUpdated(self):
        """Install/update the game and return its version string."""
        logger.info('Ensuring Ark is installed and up to date')

        self.gamedata_path.mkdir(parents=True, exist_ok=True)

        if not self.config.settings.SkipInstall:
            self.steamcmd.install_gamefiles(ARK_SERVER_APP_ID, self.gamedata_path)
        else:
            logger.info('(skipped)')

        self.game_version = fetchGameVersion(self.gamedata_path)
        self.game_buildid = getGameBuildId(self.gamedata_path)

    def ensureModsUpdated(self, modids: Union[Sequence[str], Sequence[int]]):
        '''
        Ensure the listed mods are installed and updated to their latest versions.
        '''
        logger.info('Ensuring mods are installed and up to date')

        modids_requested: Set[str] = set(str(modid) for modid in modids)
        uninstallOthers = self.config.steamcmd.UninstallUnusedMods
        dryRun = self.config.settings.SkipInstall

        # Remove any request to manage official mods
        official_modids = set(self.config.official_mods.ids())
        modids_requested -= official_modids

        # Find currently installed mods (file search for our _moddata.json)
        self.mod_data_cache = findInstalledMods(self.asset_path)
        modids_installed = set(self.mod_data_cache.keys())

        # Compare lists to calculate mods to 'add/keep/remove'
        # modids_keep = modids_installed & modids_requested
        modids_add = modids_requested - modids_installed
        modids_remove = modids_installed - modids_requested

        # Request details for the requested mods from steam api (specifically want update times and titles)
        mod_details_list = SteamApi.GetPublishedFileDetails(modids_requested) if modids_requested else []

        # Check all returned okay
        for details in mod_details_list:
            result = details.get('result', None)
            if result != 1:
                raise DownloadError(f'Steam API returned result {result} for mod {details.get("publishedfileid", "<unknown>")}')

        # Cache the details by modid
        self.steam_mod_details = dict((details['publishedfileid'], details) for details in mod_details_list)

        # Calculate mods that need fetching (adds + outdated keeps)
        def isOutdated(existing_data, workshop_details):
            if existing_data is None or workshop_details is None:
                return True
            return int(workshop_details['time_updated']) > int(existing_data['version'])

        modids_update = set(modid for modid in modids_requested
                            if isOutdated(self.mod_data_cache.get(modid, None), self.steam_mod_details.get(modid, None)))
        modids_update = modids_update | modids_add

        # Fetch updated mods, then unpack
        if modids_update:
            logger.info(f'Updating mods: {", ".join(sorted(modids_update))}')
            if not dryRun:
                self._installMods(modids_update)
            else:
                logger.info('(skipped)')
        else:
            logger.info('No mods to update')

        # Delete unwanted installed mods
        if uninstallOthers:
            if modids_remove:
                logger.info(f'Removing mods: {modids_remove}')
                if not dryRun:
                    self._removeMods(modids_remove)
                else:
                    logger.info('(skipped)')
            else:
                logger.info('No mods to remove')

        # Delete all downloaded steamapps mods
        logger.info('Removing steam workshop cache')
        if not dryRun:
            self._cleanSteamModCache()
        else:
            logger.info('(skipped)')

        # Remove mod data for mods that are no longer present
        for modid in modids_remove:
            self.mod_data_cache.pop(modid, None)

        # Verify there are no overlapping mod tags
        tag_list = [data['name'].lower() for data in self.mod_data_cache.values()]
        if len(set(tag_list)) != len(tag_list):
            raise ValueError('There are mods with duplicate tag names present. Aborting.')

    def _installMods(self, modids):
        # TODO: Consider doing the extractions in parallel with the installations (offset) to speed this up

        for modid in modids:
            # Get Steam to download the mod, compressed
            logger.debug(f'Installing/updating mod {modid}')
            self.steamcmd.install_workshopfiles(str(ARK_MAIN_APP_ID), modid, self.gamedata_path)
            if not verifyModDownloaded(self.gamedata_path, modid):
                raise FileNotFoundError("Mod was not downloaded despite successful retcode - is it still available?")

            # Unpack the mod into the game directory proper
            logger.debug(f'Unpacking mod {modid}')
            unpackMod(self.gamedata_path, modid)

            # Collection mod version number from workshop data file
            newVersions = getSteamModVersions(self.gamedata_path, [modid])

            # Save data on the installed mod
            moddata = gatherModInfo(self.asset_path, modid)
            moddata['version'] = str(newVersions[modid])

            # See if we got a title for this mod from either the mod's PGD or the SteamAPI earlier
            moddata['title'] = self._fetch_mod_title(moddata)

            moddata_path = self.mods_path / modid / MODDATA_FILENAME
            with open(moddata_path, 'w') as f:
                json.dump(moddata, f, indent='\t')

            # Save the data so we can refer to it later
            self.mod_data_cache[modid] = moddata

    def _fetch_mod_title_from_pgd(self, moddata):
        resolver = FixedModResolver({moddata['name']: moddata['id']})
        loader = AssetLoader(resolver, self.asset_path)
        pkg = moddata['package']

        if pkg:
            pgd_asset = loader[moddata['package']]
            title = pgd_asset.default_export.properties.get_property('ModName', fallback=None)
            if title:
                return str(title)

        return None

    def _fetch_mod_title(self, moddata):
        modid = moddata['id']
        title = self._fetch_mod_title_from_pgd(moddata)

        # Fallback to a name provided by SteamAPI (if any)
        if not title and modid in self.steam_mod_details and 'title' in self.steam_mod_details[modid]:
            title = self.steam_mod_details[modid]['title']  # ^ inefficient

        # Fallback to mod tag prettified with UE-like rules
        if not title:
            title = uelike_prettify(moddata['name'])

        return title

    def _removeMods(self, modids):
        # Remove the installed mods
        for modid in modids:
            modpath: Path = self.gamedata_path / 'ShooterGame' / 'Content' / 'Mods' / str(modid)
            if modpath.is_dir():
                shutil.rmtree(modpath, ignore_errors=True)

    def _cleanSteamModCache(self):
        workshop_path: Path = self.gamedata_path / 'steamapps' / 'workshop'
        if workshop_path.is_dir():
            shutil.rmtree(workshop_path)

    def _sanityCheck(self):
        # Check if we have an old steamcmd directory instead of a new Steam directory
        if Path(self.basepath / 'steamcmd').is_dir() and not self.steamcmd_path.is_dir():
            logger.warning("Renaming old-style 'steamcmd' folder to 'Steam'")
            shutil.move(str(self.basepath / 'steamcmd'), str(self.steamcmd_path))

        invalid = not self.steamcmd_path.is_dir() or not self.asset_path.is_dir()

        if invalid:
            logger.warning('Sanity check detected no game install present')


class ManagedModResolver(ModResolver):
    '''Mod resolution using managed mod data.'''
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.asset_path = manager.asset_path
        self.dataCache = dict()
        self.modNameToIds = dict()

    def initialise(self):
        self.dataCache = findInstalledMods(self.asset_path)
        self.modNameToIds = dict((data['name'].lower(), data['id']) for data in self.dataCache.values())
        for modid in get_global_config().official_mods.ids():
            name = get_global_config().official_mods.tag_from_id(modid)
            self.dataCache[modid] = dict(id=modid, name=name, official=True)
            self.modNameToIds[name.lower()] = modid
        return self

    def get_name_from_id(self, modid: str) -> str:
        data = self.dataCache.get(modid, None)
        if data is None:
            return modid
        return data['name']

    def get_id_from_name(self, name: str) -> str:
        modid = self.modNameToIds.get(name.lower(), None)
        if not modid:
            raise ModNotFound(name)
        return modid


class FixedModResolver(ModResolver):
    def __init__(self, namesToIds: Dict[str, str]):
        self.namesToIds = namesToIds
        self.idsToNames = dict((v, k) for k, v in namesToIds.items())
        super().__init__()

    def initialise(self):
        return super().initialise()

    def get_id_from_name(self, name):
        return self.namesToIds[name]

    def get_name_from_id(self, modid):
        return self.idsToNames[modid]


def findInstalledMods(asset_path: Path) -> Dict[str, Dict]:
    '''Scan installed modules and return their information in a Dict[id->data].'''
    mods_path: Path = asset_path / 'Content' / 'Mods'
    result: Dict[str, Any] = dict()
    for filename in mods_path.glob('*/' + MODDATA_FILENAME):
        modid: str = filename.parent.name
        data = readModData(asset_path, modid)
        result[modid] = data

    return result


def _fetchGameVersionFromAPI() -> Optional[str]:
    rsp = requests.get('http://arkdedicated.com/version')
    rsp.raise_for_status()
    version = (rsp.text or '').strip()
    return version


def _fetchGameVersionFromFile(gamedata_path: Path) -> Optional[str]:
    verFile = Path(gamedata_path / 'version.txt')
    if not verFile.is_file():
        return None
    with open(verFile, 'rt') as f:
        version = f.read().strip()
    return version


def fetchGameVersion(gamedata_path: Path) -> str:
    # Try version.txt in depot... cross fingers
    version = _fetchGameVersionFromFile(gamedata_path)
    if version:
        if not re.fullmatch(r"\d+(\.\d+)*", version, re.I):
            logger.warning(f"Falling back to version API due to invalid version.txt!: {version}")
        else:
            logger.info(f"Game version from version.txt: {version}")
            return version

    # Fall back to possibly out-of-sync official server network version API
    logger.warning('Falling back to version API as version.txt is missing (again)!')
    version = _fetchGameVersionFromAPI()
    if not version or not re.fullmatch(r"\d+(\.\d+)*", version, re.I):
        raise ValueError(f"Fallback version API return unexpected data: {version}")

    logger.info(f"Game version from server API: {version}")
    return version


def getSteamModVersions(game_path: Path, modids) -> Dict[str, int]:
    '''Collect version numbers for each of the specified mods in for the form Dict[id->version].'''
    filename: Path = game_path / 'steamapps' / 'workshop' / f'appworkshop_{ARK_MAIN_APP_ID}.acf'
    data = readACFFile(filename)
    details = data['AppWorkshop']['WorkshopItemDetails']
    newModVersions = dict((modid, int(details[modid]['timeupdated'])) for modid in modids if modid in details)
    return newModVersions


def getGameBuildId(game_path: Path) -> str:
    '''
    Collect the buildid of the game from Steam's metadata files.
    This will be updated even if the version number doesn't change.
    '''
    filename: Path = game_path / 'steamapps' / f'appmanifest_{ARK_SERVER_APP_ID}.acf'
    data = readACFFile(filename)
    buildid = data['AppState']['buildid']
    return buildid


def gatherModInfo(asset_path: Path, modid) -> Dict[str, Any]:
    '''Gather information from mod.info and modmeta.info and collate into an info structure.'''
    modid = str(modid)
    modpath: Path = asset_path / 'Content' / 'Mods' / modid

    modinfo = readModInfo(modpath / 'mod.info')
    modmetainfo = readModMetaInfo(modpath / 'modmeta.info')

    moddata = dict()
    moddata['id'] = modid
    moddata['name'] = modinfo['modname']
    moddata['maps'] = modinfo['maps']
    moddata['package'] = modmetainfo['PrimalGameData']
    moddata['guid'] = modmetainfo['GUID']
    moddata['type'] = modmetainfo['ModType']
    moddata['MODMETA.INFO'] = modmetainfo
    moddata['MOD.INFO'] = modinfo
    return moddata


def readModData(asset_path: Path, modid) -> Optional[Dict[str, Any]]:
    modid = str(modid)
    moddata_path: Path = asset_path / 'Content' / 'Mods' / modid / MODDATA_FILENAME
    logger.debug(f'Loading mod {modid} metadata')
    if not moddata_path.is_file():
        logger.debug(f'Couldn\'t find mod data at "{moddata_path}"')
        return None

    with open(moddata_path, 'r') as f:
        moddata = json.load(f)

    return moddata


def verifyModDownloaded(game_path, modid):
    srcPath = game_path / 'steamapps' / 'workshop' / 'content' / str(ARK_MAIN_APP_ID) / str(modid) / 'WindowsNoEditor'
    return srcPath.is_dir()


def unpackMod(game_path, modid):
    '''Unpack a compressed steam mod.'''
    srcPath: Path = game_path / 'steamapps' / 'workshop' / 'content' / str(ARK_MAIN_APP_ID) / str(modid) / 'WindowsNoEditor'
    dstPath: Path = game_path / 'ShooterGame' / 'Content' / 'Mods' / str(modid)

    if dstPath.is_dir():
        shutil.rmtree(dstPath)

    for curdir, _, files in walk(srcPath):
        curdir = Path(curdir).relative_to(srcPath)
        for filename in files:
            filename = Path(filename)
            if filename.suffix.lower() == '.z':
                # decompress
                src = srcPath / curdir / filename
                dst = dstPath / curdir / filename.stem
                dst.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f'Decompressing {src} -> {dst}')
                unpackModFile(src, dst)
            elif filename.suffix.lower() == '.uncompressed_size':
                # ignore
                pass
            else:
                # just copy
                src = srcPath / curdir / filename
                dst = dstPath / curdir / filename
                dst.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f'Copying {src} -> {dst}')
                shutil.copyfile(src, dst)
