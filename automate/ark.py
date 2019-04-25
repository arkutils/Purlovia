import math
import shutil
import os.path
import logging
from typing import Dict

from .steamcmd import Steamcmd
from .modutils import unpackModFile, readACFFile

ARK_SERVER_APP_ID = 376030
ARK_MAIN_APP_ID = 346110

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ArkSteamManager:
    def __init__(self, basepath):
        basepath = os.path.abspath(basepath)
        self.basepath = basepath
        self.steamcmd_path = os.path.join(basepath, 'steamcmd')
        self.gamedata_path = os.path.join(basepath, 'game')
        self.steamcmd = Steamcmd(self.steamcmd_path)

    def ensureSteamCmd(self):
        logger.info(f'Ensuring SteamCMD is installed')
        os.makedirs(self.steamcmd_path, exist_ok=True)
        self.steamcmd.install()

    def ensureGameUpdated(self) -> str:
        """Install/update the game and return its version string."""
        logger.info(f'Ensuring Ark is installed and up to date')
        os.makedirs(self.gamedata_path, exist_ok=True)
        self.steamcmd.install_gamefiles(ARK_SERVER_APP_ID, self.gamedata_path)
        verFile = os.path.join(self.gamedata_path, 'version.txt')
        with open(verFile) as f:
            version = f.read().strip()
        return version

    def ensureModsUpdated(self, modids, previousVersions: Dict[str, str] = None, skipInstall=False) -> Dict[str, str]:
        """
        Install/update the listed mods and return a dict of their versions.

        :param modids: List of mod IDs to work on.
        :param previousVersions: (Optional) Dict of previous versions, consisting of modid -> version pairs.
        :return: Dict of mod versions, consisting of modid -> version pairs.
        """
        logger.info(f'Ensuring mods are installed and up to date')

        modids = tuple(str(modid) for modid in modids)
        previousVersions = dict((modid, int(version)) for modid, version in (previousVersions or dict()).items())

        workshopFile = os.path.join(self.gamedata_path, 'steamapps', 'workshop', f'appworkshop_{ARK_MAIN_APP_ID}.acf')
        workshopData = readACFFile(workshopFile) if os.path.isfile(workshopFile) else None

        # TODO: Gather installed versions from a marker file in each installed mod's directory

        # Update mods using steamcmd
        if not skipInstall:
            for modid in modids:
                logger.info(f'Installing/updating mod {modid}')
                self.steamcmd.install_workshopfiles(str(ARK_MAIN_APP_ID), modid, self.gamedata_path)

        # Collection version numbers from workshop data file
        newVersions = getModVersions(self.gamedata_path, modids)

        # Unpack mods which have updated versions
        for modid in modids:
            oldVersion = previousVersions.get(modid, -math.inf)
            newVersion = newVersions.get(modid, None)
            assert newVersion is not None, LookupError(f"Unable to find version for installed mod {modid}")
            if newVersion > oldVersion:
                logger.info(f'Unpacking mod {modid}')
                unpackMod(self.gamedata_path, modid)
            else:
                logger.debug(f'Skipping unchanged mod {modid}')

        return newVersions

    def getContentPath(self) -> str:
        '''Return the Content directory of the game.'''
        content = os.path.join(self.gamedata_path, 'ShooterGame', 'Content')
        return content


def getModVersions(game_path, modids) -> Dict[str, int]:
    '''Collect version numbers for each of the specified mods.'''
    filename = os.path.join(game_path, 'steamapps', 'workshop', f'appworkshop_{ARK_MAIN_APP_ID}.acf')
    data = readACFFile(filename)
    details = data['AppWorkshop']['WorkshopItemDetails']
    newModVersions = dict((modid, int(details[modid]['timeupdated'])) for modid in modids)
    return newModVersions


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
]
