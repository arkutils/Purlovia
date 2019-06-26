import math
import json
import shutil
import logging
from typing import Dict, Any, Tuple, List, Sequence, Union
from pathlib import Path
from shutil import rmtree
from os import walk

from ue.loader import AssetLoader, ModResolver
from .modutils import unpackModFile, readACFFile, readModInfo, readModMetaInfo
from .steamcmd import Steamcmd
from .steamapi import SteamApi, SteamApiException
from .version import createVersion

__all__ = (
    'ArkSteamManager',
    'findInstalledMods',
    'getModVersions',
    'readModData',
    'unpackMod',
    'OFFICIAL_MODS',
)

ARK_SERVER_APP_ID = 376030
ARK_MAIN_APP_ID = 346110

MODDATA_FILENAME = '_moddata.json'

OFFICIAL_MODS = {
    'Ragnarok': 'Ragnarok',
    'TheCenter': 'TheCenter',
    '111111111': 'PrimitivePlus',
}
# Force IDs to be lowercase to help with lookup
OFFICIAL_MODS = dict((id.lower(), name) for id, name in OFFICIAL_MODS.items())

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ArkSteamManager:
    def __init__(self, basepath=Path('livedata'), skipInstall=False):
        self.basepath: Path = Path(basepath).absolute()
        self.skip_install = skipInstall
        self.steamcmd_path: Path = self.basepath / 'steamcmd'
        self.gamedata_path: Path = self.basepath / 'game'
        self.asset_path: Path = self.gamedata_path / 'ShooterGame'
        self.mods_path: Path = self.asset_path / 'Content' / 'Mods'

        self.steamcmd = Steamcmd(self.steamcmd_path)

        self._sanityCheck()

    def createLoader(self):
        '''Create an asset loader pointing at the managed game install.'''
        modresolver = ManagedModResolver(self)
        loader = AssetLoader(modresolver, self.asset_path)
        return loader

    def findInstalledMods(self):
        '''Scan installed modules and return their information in a Dict[id->data].'''
        mods = findInstalledMods(self.asset_path, exclude_official=True)
        return mods

    def ensureSteamCmd(self):
        logger.info(f'Ensuring SteamCMD is installed')
        self.steamcmd_path.mkdir(parents=True, exist_ok=True)
        self.steamcmd.install()

    def ensureGameUpdated(self, skipInstall=None) -> str:
        """Install/update the game and return its version string."""
        logger.info(f'Ensuring Ark is installed and up to date')

        if skipInstall is None: skipInstall = self.skip_install

        self.gamedata_path.mkdir(parents=True, exist_ok=True)
        if not skipInstall:
            self.steamcmd.install_gamefiles(ARK_SERVER_APP_ID, self.gamedata_path)

        gameVer = self.fetchGameVersion()
        return gameVer

    def newEnsureModsUpdated(self, modids: Union[List[str], Tuple[str]], dryRun=False, uninstallOthers=False):
        '''
        Ensure the listed mods are installed and updated to their latest versions.
        If uninstallOthers is True, also remove any previously installed mods that are not in the given list.
        If dryRun is True, make no changes - only report what would have been done.
        '''
        modids_requested = set(str(modid) for modid in modids)

        # Find currently installed mods (file search for our _moddata.json)
        mod_data_installed = findInstalledMods(self.asset_path, exclude_official=True)
        modids_installed = set(mod_data_installed.keys())

        # Compare lists to calculate mods to 'add/keep/remove'
        modids_keep = modids_installed & modids_requested
        modids_add = modids_requested - modids_installed
        modids_remove = modids_installed - modids_requested
        logger.debug(f'installed: {modids_installed}')
        logger.debug(f'requested: {modids_requested}')
        logger.debug(f'to keep: {modids_keep}')
        logger.debug(f'to add: {modids_add}')
        logger.debug(f'to remove: {modids_remove}')

        # Request update times for the 'keep' mods from steam api
        mod_details_keep_list = SteamApi.GetPublishedFileDetails(modids_keep) if modids_keep else []
        mod_details_keep = dict((details['publishedfileid'], details) for details in mod_details_keep_list)

        # Calculate mods that need fetching (adds + outdated keeps)
        def isOutdated(existing_data, workshop_details):
            return int(workshop_details['time_updated']) > int(existing_data['version'])

        modids_update = set(modid for modid in modids_keep if isOutdated(mod_data_installed[modid], mod_details_keep[modid]))
        modids_update = modids_update | modids_add

        # Fetch updated mods, then unpack (in thread?)
        if modids_update:
            logger.info(f'Updating mods: {modids_update}')
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

    def _installMods(self, modids):
        # TODO: Consider doing the extractions in parallel with the installations (offset) to speed this up

        # Get Steam to download the mods, compressed
        for modid in modids:
            logger.debug(f'Installing/updating mod {modid}')
            self.steamcmd.install_workshopfiles(str(ARK_MAIN_APP_ID), modid, self.gamedata_path)

        # Unpack the mods into the game directory proper
        for modid in modids:
            logger.info(f'Unpacking mod {modid}')
            unpackMod(self.gamedata_path, modid)

        # Collection mod version numbers from workshop data file
        newVersions = getSteamModVersions(self.gamedata_path, modids)

        # Also need the game version to make a full version number
        gameVersion = self.fetchGameVersion()

        # Save data on the installed mods
        for modid in modids:
            moddata = gatherModInfo(self.asset_path, modid)
            moddata['version'] = f'{gameVersion}.{newVersions[modid]}'
            moddata_path = self.mods_path / modid / MODDATA_FILENAME
            with open(moddata_path, 'w') as f:
                json.dump(moddata, f, indent='\t')

    def _removeMods(self, modids):
        # Remove the installed mods
        for modid in modids:
            modpath: Path = self.gamedata_path / 'ShooterGame' / 'Content' / 'Mods' / str(modid)
            if modpath.is_dir():
                rmtree(modpath, ignore_errors=True)

    def _cleanSteamModCache(self):
        workshop_path: Path = self.gamedata_path / 'steamapps' / 'workshop'
        if workshop_path.is_dir():
            logging.info('Removing steam workshop cache')
            rmtree(workshop_path)

    def ensureModsUpdated(self, modids, skipInstall=None) -> Dict[str, Dict]:
        """
        Install/update the listed mods and return a dict of their versions.

        :param modids: List of mod IDs to work on.
        :return: Dict of mod data for the given modids.
        """
        logger.info(f'Ensuring mods are installed and up to date')

        if skipInstall is None: skipInstall = self.skip_install
        modids = tuple(str(modid) for modid in modids)

        workshopFile: Path = self.gamedata_path / 'steamapps' / 'workshop' / f'appworkshop_{ARK_MAIN_APP_ID}.acf'
        workshopData = readACFFile(workshopFile) if workshopFile.is_file() else None

        # Gather existing moddata files
        old_moddata = dict()
        for modid in modids:
            moddata = readModData(self.asset_path, modid)
            if moddata:
                old_moddata[modid] = moddata

        # Update mods using steamcmd
        if not skipInstall:
            for modid in modids:
                logger.info(f'Installing/updating mod {modid}')
                self.steamcmd.install_workshopfiles(str(ARK_MAIN_APP_ID), modid, self.gamedata_path)

        # Collection version numbers from workshop data file
        newVersions = getSteamModVersions(self.gamedata_path, modids)

        # Unpack mods which have updated versions
        for modid in modids:
            oldVersion = int(old_moddata[modid]['version']) if modid in old_moddata else -math.inf
            newVersion = newVersions.get(modid, None)
            assert newVersion, LookupError(f"Unable to find version for installed mod {modid}")
            if newVersion > oldVersion:
                logger.info(f'Unpacking mod {modid}')
                unpackMod(self.gamedata_path, modid)
            else:
                logger.debug(f'Skipping unchanged mod {modid}')

        # Extract and save mod data
        all_moddata = dict()
        for modid in modids:
            moddata = gatherModInfo(self.asset_path, modid)
            moddata['version'] = str(newVersions[modid])
            moddata_path = self.mods_path / modid / MODDATA_FILENAME
            with open(moddata_path, 'w') as f:
                json.dump(moddata, f, indent='\t')

            all_moddata[modid] = moddata

        return all_moddata

    def fetchGameVersion(self) -> str:
        verFile = self.gamedata_path / 'version.txt'
        with open(verFile) as f:
            version = f.read().strip()
        return version

    def fetchModData(self, modid) -> Dict[str, Dict]:
        '''Fetch data for a previously installed mod. Returns None if not installed or invalid.'''
        moddata_path = self.mods_path / modid / MODDATA_FILENAME
        try:
            with open(moddata_path) as f:
                moddata = json.load(f, indent='\t')
                return moddata
        except FileNotFoundError:
            return None

    def getContentPath(self) -> str:
        '''Return the Content directory of the game.'''
        return self.asset_path

    def _sanityCheck(self):
        invalid = not self.steamcmd_path.is_dir() or not self.asset_path.is_dir()

        if invalid and self.skip_install:
            logger.error('Found no game install and was told to skipInstall, aborting')
            raise ValueError('Ark Steam Manager found no game install and was told to skipInstall, aborting')

        if invalid:
            logger.warning('Sanity check detected no game install present')

        if self.skip_install:
            logger.warning('Skipping installations due to skipInstall flag!')


class ManagedModResolver(ModResolver):
    '''Mod resolution using managed mod data and mods.ini only for long names.'''

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.asset_path = manager.asset_path
        self.dataCache = dict()
        self.modNameToIds = dict()

    def initialise(self):
        self.dataCache = findInstalledMods(self.asset_path, exclude_official=False)
        self.modNameToIds = dict((data['name'].lower(), data['id']) for data in self.dataCache.values())
        return self

    def get_name_from_id(self, modid: str) -> str:
        data = self.dataCache.get(modid, None)
        if data is None:
            return modid
        return data['name']

    def get_id_from_name(self, name: str) -> str:
        if name.lower() in OFFICIAL_MODS: return name
        id = self.modNameToIds.get(name.lower(), None)
        if not id: raise NameError(f"Mod name '{name}' not recognised or not installed")
        return id


def findInstalledMods(asset_path: Path, exclude_official=True) -> Dict[str, Dict]:
    '''Scan installed modules and return their information in a Dict[id->data].'''
    mods_path: Path = asset_path / 'Content' / 'Mods'
    result = dict()
    for filename in mods_path.glob('*/' + MODDATA_FILENAME):
        modid = filename.parent.name
        if exclude_official and modid.lower() in OFFICIAL_MODS:
            result[modid] = dict(id=modid, name=modid)
        else:
            data = readModData(asset_path, modid)
            result[modid] = data

    return result


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


def readModData(asset_path: Path, modid) -> Dict[str, Any]:
    modid = str(modid)
    moddata_path: Path = asset_path / 'Content' / 'Mods' / modid / MODDATA_FILENAME
    logger.info(f'Loading mod {modid} metadata')
    if not moddata_path.is_file():
        logger.debug(f'Couldn\'t find mod data at "{moddata_path}"')
        return None

    with open(moddata_path, 'r') as f:
        moddata = json.load(f)

    return moddata


def unpackMod(game_path, modid) -> str:
    '''Unpack a compressed steam mod and return its version number.'''
    srcPath = game_path / 'steamapps' / 'workshop' / 'content' / str(ARK_MAIN_APP_ID) / str(modid) / 'WindowsNoEditor'
    dstPath = game_path / 'ShooterGame' / 'Content' / 'Mods' / str(modid)

    for curdir, dirs, files in walk(srcPath):
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
