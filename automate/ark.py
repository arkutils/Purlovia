import math
import json
import shutil
import os.path
import logging
from typing import Dict

from .steamcmd import Steamcmd
from .modutils import unpackModFile, readACFFile, readModInfo, readModMetaInfo

ARK_SERVER_APP_ID = 376030
ARK_MAIN_APP_ID = 346110

MODDATA_FILENAME = '_moddata.json'

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ArkSteamManager:
    def __init__(self, basepath):
        basepath = os.path.abspath(basepath)
        self.basepath = basepath
        self.steamcmd_path = os.path.join(basepath, 'steamcmd')
        self.gamedata_path = os.path.join(basepath, 'game')
        self.asset_path = os.path.join(self.gamedata_path, 'ShooterGame', 'Content')
        self.steamcmd = Steamcmd(self.steamcmd_path)

    def ensureSteamCmd(self):
        logger.info(f'Ensuring SteamCMD is installed')
        os.makedirs(self.steamcmd_path, exist_ok=True)
        self.steamcmd.install()

    def ensureGameUpdated(self, skipInstall=False) -> str:
        """Install/update the game and return its version string."""
        logger.info(f'Ensuring Ark is installed and up to date')
        os.makedirs(self.gamedata_path, exist_ok=True)
        if not skipInstall:
            self.steamcmd.install_gamefiles(ARK_SERVER_APP_ID, self.gamedata_path)
        verFile = os.path.join(self.gamedata_path, 'version.txt')
        with open(verFile) as f:
            version = f.read().strip()
        return version

    def ensureModsUpdated(self, modids, skipInstall=False) -> Dict[str, Dict]:
        """
        Install/update the listed mods and return a dict of their versions.

        :param modids: List of mod IDs to work on.
        :return: Dict of mod data for the given modids.
        """
        logger.info(f'Ensuring mods are installed and up to date')

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
            moddata_path = os.path.join(self.asset_path, 'Mods', modid, MODDATA_FILENAME)
            with open(moddata_path, 'w') as f:
                json.dump(moddata, f, indent='\t')

            all_moddata[modid] = moddata

        return all_moddata

    def getContentPath(self) -> str:
        '''Return the Content directory of the game.'''
        return self.asset_path


def getSteamModVersions(game_path, modids) -> Dict[str, int]:
    '''Collect version numbers for each of the specified mods.'''
    filename = os.path.join(game_path, 'steamapps', 'workshop', f'appworkshop_{ARK_MAIN_APP_ID}.acf')
    data = readACFFile(filename)
    details = data['AppWorkshop']['WorkshopItemDetails']
    newModVersions = dict((modid, int(details[modid]['timeupdated'])) for modid in modids)
    return newModVersions


def gatherModInfo(asset_path, modid) -> Dict:
    '''Gather information from mod.info and modmeta.info and collate into an info structure.'''
    modpath = os.path.join(asset_path, 'Content', 'Mods', str(modid))

    modinfo = readModInfo(os.path.join(modpath, 'mod.info'))
    modmetainfo = readModMetaInfo(os.path.join(modpath, 'modmeta.info'))

    moddata = dict()
    moddata['id'] = str(modid)
    moddata['name'] = modinfo['modname']
    moddata['maps'] = modinfo['maps']
    return moddata


def readModData(asset_path, modid) -> Dict:
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


__all__ = [
    'ArkSteamManager',
    'getModVersions',
    'readModData',
]
