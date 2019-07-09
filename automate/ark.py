import json
import shutil
import logging
import datetime
from typing import *
from pathlib import Path
from os import walk

from config import get_global_config
from ue.loader import AssetLoader, ModResolver
from .modutils import unpackModFile, readACFFile, readModInfo, readModMetaInfo
from .steamcmd import Steamcmd
from .steamapi import SteamApi
from .version import createExportVersion

__all__ = ('ArkSteamManager', )

ARK_SERVER_APP_ID = 376030
ARK_MAIN_APP_ID = 346110

MODDATA_FILENAME = '_moddata.json'

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ArkSteamManager:
    def __init__(self):
        self.basepath: Path = get_global_config().settings.DataDir.absolute()

        self.steamcmd_path: Path = self.basepath / 'steamcmd'
        self.gamedata_path: Path = self.basepath / 'game'
        self.asset_path: Path = self.gamedata_path / 'ShooterGame'
        self.mods_path: Path = self.asset_path / 'Content' / 'Mods'

        self.steamcmd = Steamcmd(self.steamcmd_path)

        self.steam_mod_details: Optional[Dict[str, Dict]] = None  # from steam
        self.mod_data_cache: Optional[Dict[str, Dict]] = None  # internal data
        self.game_version: Optional[str] = None

        self._sanityCheck()

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

        # Official "mods" need to be handled differently
        if modid in get_global_config().official_mods.ids():
            data = dict(id=modid)
            data['version'] = str(int(datetime.datetime.utcnow().timestamp()))
            data['name'] = get_global_config().official_mods.tag_from_id(modid)
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

    def getContentPath(self) -> Path:
        '''Return the Content directory of the game.'''
        return self.asset_path

    def ensureSteamCmd(self):
        logger.info('Ensuring SteamCMD is installed')
        self.steamcmd_path.mkdir(parents=True, exist_ok=True)
        self.steamcmd.install()

    def ensureGameUpdated(self) -> str:
        """Install/update the game and return its version string."""
        logger.info('Ensuring Ark is installed and up to date')

        self.gamedata_path.mkdir(parents=True, exist_ok=True)

        self.steamcmd.install_gamefiles(ARK_SERVER_APP_ID, self.gamedata_path)

        self.game_version = fetchGameVersion(self.gamedata_path)
        return self.game_version  # type: ignore

    def ensureModsUpdated(self, modids: Union[Sequence[str], Sequence[int]], dryRun=False, uninstallOthers=False):
        '''
        Ensure the listed mods are installed and updated to their latest versions.
        If uninstallOthers is True, also remove any previously installed mods that are not in the given list.
        If dryRun is True, make no changes - only report what would have been done.
        '''
        modids_requested: Set[str] = set(str(modid) for modid in modids)

        # Remove any request to manage official mods
        official_modids = set(get_global_config().official_mods.ids())
        modids_requested -= official_modids

        # Find currently installed mods (file search for our _moddata.json)
        self.mod_data_cache = findInstalledMods(self.asset_path)
        modids_installed = set(self.mod_data_cache.keys())

        # Compare lists to calculate mods to 'add/keep/remove'
        modids_keep = modids_installed & modids_requested
        modids_add = modids_requested - modids_installed
        modids_remove = modids_installed - modids_requested

        # Request details for the 'keep' and 'add' mods from steam api (specifically want update times and titles)
        mod_details_list = SteamApi.GetPublishedFileDetails(modids_keep | modids_add) if modids_keep | modids_add else []
        self.steam_mod_details = dict((details['publishedfileid'], details) for details in mod_details_list)

        # Calculate mods that need fetching (adds + outdated keeps)
        def isOutdated(existing_data, workshop_details):
            return int(workshop_details['time_updated']) > int(existing_data['version'])

        modids_update = set(modid for modid in modids_keep
                            if isOutdated(self.mod_data_cache[modid], self.steam_mod_details[modid]))
        modids_update = modids_update | modids_add

        # Fetch updated mods, then unpack
        if modids_update:
            logger.info(f'Updating mods: {", ".join(sorted(modids_update))}')
            if not dryRun:
                self._installMods(modids_update)

        # Delete unwanted installed mods
        if uninstallOthers and modids_remove:
            logger.info(f'Removing mods: {modids_remove}')
            if not dryRun:
                self._removeMods(modids_remove)

        # Delete all downloaded steamapps mods
        if not dryRun:
            self._cleanSteamModCache()

        # Remove mod data for mods that are no longer present
        for modid in modids_remove:
            self.mod_data_cache.pop(modid, None)

        # Verify there are no overlapping mod tags
        tag_list = [data['name'].lower() for data in self.mod_data_cache.values()]
        if len(set(tag_list)) != len(tag_list):
            raise ValueError(f'There are mods with duplicate tag names present. Aborting.')

    def _installMods(self, modids):
        # TODO: Consider doing the extractions in parallel with the installations (offset) to speed this up

        # Get Steam to download the mods, compressed
        for modid in modids:
            logger.debug(f'Installing/updating mod {modid}')
            self.steamcmd.install_workshopfiles(str(ARK_MAIN_APP_ID), modid, self.gamedata_path)
            if not verifyModDownloaded(self.gamedata_path, modid):
                raise FileNotFoundError("Mod was not downloaded despite successful retcode - is it still available?")

        # Unpack the mods into the game directory proper
        for modid in modids:
            logger.info(f'Unpacking mod {modid}')
            unpackMod(self.gamedata_path, modid)

        # Collection mod version numbers from workshop data file
        newVersions = getSteamModVersions(self.gamedata_path, modids)

        # Save data on the installed mods
        for modid in modids:
            moddata = gatherModInfo(self.asset_path, modid)
            moddata['version'] = str(newVersions[modid])

            # See if we got a title for this mod from the SteamAPI earlier
            if self.steam_mod_details and modid in self.steam_mod_details and 'title' in self.steam_mod_details[modid]:
                moddata['title'] = self.steam_mod_details[modid]['title']  # ^ inefficient

            moddata_path = self.mods_path / modid / MODDATA_FILENAME
            with open(moddata_path, 'w') as f:
                json.dump(moddata, f, indent='\t')

            # Save the data so we can refer to it later
            self.mod_data_cache[modid] = moddata

    def _removeMods(self, modids):
        # Remove the installed mods
        for modid in modids:
            modpath: Path = self.gamedata_path / 'ShooterGame' / 'Content' / 'Mods' / str(modid)
            if modpath.is_dir():
                shutil.rmtree(modpath, ignore_errors=True)

    def _cleanSteamModCache(self):
        workshop_path: Path = self.gamedata_path / 'steamapps' / 'workshop'
        if workshop_path.is_dir():
            logger.info('Removing steam workshop cache')
            shutil.rmtree(workshop_path)

    def _sanityCheck(self):
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
        if not modid: raise NameError(f"Mod name '{name}' not recognised or not installed")
        return modid


def findInstalledMods(asset_path: Path) -> Dict[str, Dict]:
    '''Scan installed modules and return their information in a Dict[id->data].'''
    mods_path: Path = asset_path / 'Content' / 'Mods'
    result: Dict[str, Any] = dict()
    for filename in mods_path.glob('*/' + MODDATA_FILENAME):
        modid: str = filename.parent.name
        data = readModData(asset_path, modid)
        result[modid] = data

    return result


def fetchGameVersion(gamedata_path: Path) -> str:
    verFile = gamedata_path / 'version.txt'
    with open(verFile) as f:
        version = f.read().strip()
    return version


def getSteamModVersions(game_path: Path, modids) -> Dict[str, int]:
    '''Collect version numbers for each of the specified mods in for the form Dict[id->version].'''
    filename: Path = game_path / 'steamapps' / 'workshop' / f'appworkshop_{ARK_MAIN_APP_ID}.acf'
    data = readACFFile(filename)
    details = data['AppWorkshop']['WorkshopItemDetails']
    newModVersions = dict((modid, int(details[modid]['timeupdated'])) for modid in modids if modid in details)
    return newModVersions


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
    logger.info(f'Loading mod {modid} metadata')
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
    srcPath = game_path / 'steamapps' / 'workshop' / 'content' / str(ARK_MAIN_APP_ID) / str(modid) / 'WindowsNoEditor'
    dstPath = game_path / 'ShooterGame' / 'Content' / 'Mods' / str(modid)

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
