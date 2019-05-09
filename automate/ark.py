import math
import json
import glob
import shutil
import os.path
import logging
from typing import Dict, Any, Tuple

from ue.loader import AssetLoader, ModResolver
from .modutils import unpackModFile, readACFFile, readModInfo, readModMetaInfo
from .steamcmd import Steamcmd

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
    def __init__(self, basepath='livedata', skipInstall=False):
        basepath = os.path.abspath(basepath)
        self.basepath = basepath
        self.skip_install = skipInstall
        self.steamcmd_path = os.path.join(basepath, 'steamcmd')
        self.gamedata_path = os.path.join(basepath, 'game')
        self.asset_path = os.path.join(self.gamedata_path, 'ShooterGame')
        self.mods_path = os.path.join(self.asset_path, 'Content', 'Mods')

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
        os.makedirs(self.steamcmd_path, exist_ok=True)
        self.steamcmd.install()

    def ensureGameUpdated(self, skipInstall=None) -> str:
        """Install/update the game and return its version string."""
        logger.info(f'Ensuring Ark is installed and up to date')

        if skipInstall is None: skipInstall = self.skip_install

        os.makedirs(self.gamedata_path, exist_ok=True)
        if not skipInstall:
            self.steamcmd.install_gamefiles(ARK_SERVER_APP_ID, self.gamedata_path)
        verFile = os.path.join(self.gamedata_path, 'version.txt')
        with open(verFile) as f:
            version = f.read().strip()
        return version

    def ensureModsUpdated(self, modids, skipInstall=None) -> Dict[str, Dict]:
        """
        Install/update the listed mods and return a dict of their versions.

        :param modids: List of mod IDs to work on.
        :return: Dict of mod data for the given modids.
        """
        logger.info(f'Ensuring mods are installed and up to date')

        if skipInstall is None: skipInstall = self.skip_install
        modids = tuple(str(modid) for modid in modids)

        workshopFile = os.path.join(self.gamedata_path, 'steamapps', 'workshop', f'appworkshop_{ARK_MAIN_APP_ID}.acf')
        workshopData = readACFFile(workshopFile) if os.path.isfile(workshopFile) else None

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
            moddata_path = os.path.join(self.mods_path, modid, MODDATA_FILENAME)
            with open(moddata_path, 'w') as f:
                json.dump(moddata, f, indent='\t')

            all_moddata[modid] = moddata

        return all_moddata

    def getContentPath(self) -> str:
        '''Return the Content directory of the game.'''
        return self.asset_path

    def _sanityCheck(self):
        invalid = not os.path.isdir(self.steamcmd_path) or not os.path.isdir(self.asset_path)

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


def findInstalledMods(asset_path, exclude_official=True) -> Dict[str, Dict]:
    '''Scan installed modules and return their information in a Dict[id->data].'''
    mods_path = os.path.join(asset_path, 'Content', 'Mods')
    wildcard = os.path.join(mods_path, '*', MODDATA_FILENAME)
    result = dict()
    for filename in glob.iglob(wildcard):
        modid = os.path.split(os.path.dirname(filename))[-1]
        if exclude_official and modid.lower() in OFFICIAL_MODS:
            result[modid] = dict(id=modid, name=modid)
        else:
            data = readModData(asset_path, modid)
            result[modid] = data

    return result


def getSteamModVersions(game_path, modids) -> Dict[str, int]:
    '''Collect version numbers for each of the specified mods in for the form Dict[id->version].'''
    filename = os.path.join(game_path, 'steamapps', 'workshop', f'appworkshop_{ARK_MAIN_APP_ID}.acf')
    data = readACFFile(filename)
    details = data['AppWorkshop']['WorkshopItemDetails']
    newModVersions = dict((modid, int(details[modid]['timeupdated'])) for modid in modids if modid in details)
    return newModVersions


def gatherModInfo(asset_path, modid) -> Dict[str, Any]:
    '''Gather information from mod.info and modmeta.info and collate into an info structure.'''
    modpath = os.path.join(asset_path, 'Content', 'Mods', str(modid))

    modinfo = readModInfo(os.path.join(modpath, 'mod.info'))
    modmetainfo = readModMetaInfo(os.path.join(modpath, 'modmeta.info'))

    moddata = dict()
    moddata['id'] = str(modid)
    moddata['name'] = modinfo['modname']
    moddata['maps'] = modinfo['maps']
    moddata['package'] = modmetainfo['PrimalGameData']
    moddata['guid'] = modmetainfo['GUID']
    moddata['type'] = modmetainfo['ModType']
    moddata['MODMETA.INFO'] = modmetainfo
    moddata['MOD.INFO'] = modinfo
    return moddata


def readModData(asset_path, modid) -> Dict[str, Any]:
    moddata_path = os.path.join(asset_path, 'Content', 'Mods', modid, MODDATA_FILENAME)
    logger.info(f'Loading mod {modid} metadata')
    if not os.path.isfile(moddata_path):
        logger.debug(f'Couldn\'t find mod data at "{moddata_path}"')
        return None

    with open(moddata_path, 'r') as f:
        moddata = json.load(f)

    return moddata


def unpackMod(game_path, modid) -> str:
    '''Unpack a compressed steam mod and return its version number.'''
    srcPath = os.path.join(game_path, 'steamapps', 'workshop', 'content', str(ARK_MAIN_APP_ID), str(modid), 'WindowsNoEditor')
    dstPath = os.path.join(game_path, 'ShooterGame', 'Content', 'Mods', str(modid))

    for curdir, dirs, files in os.walk(srcPath):
        curdir = os.path.relpath(curdir, srcPath)
        for filename in files:
            name, ext = os.path.splitext(filename)
            if ext.lower().endswith('.z'):
                # decompress
                src = os.path.abspath(os.path.join(srcPath, curdir, filename))
                dst = os.path.abspath(os.path.join(dstPath, curdir, name))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                logger.debug(f'Decompressing {src} -> {dst}')
                unpackModFile(src, dst)
            elif ext.lower().endswith('.uncompressed_size'):
                # ignore
                pass
            else:
                # just copy
                src = os.path.abspath(os.path.join(srcPath, curdir, filename))
                dst = os.path.abspath(os.path.join(dstPath, curdir, filename))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                logger.debug(f'Copying {src} -> {dst}')
                shutil.copyfile(src, dst)
