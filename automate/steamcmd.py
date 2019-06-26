import platform
import urllib.request
import logging
import subprocess
from pathlib import Path
'''
Adapted from the pysteamcmd library, which has an MIT license.
'''

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# TODO: DepotDownloadProgressTimeout 1200
# It's unlikely this will help, according to many sources


class SteamcmdException(Exception):
    """
    Base exception for the pysteamcmd package
    """

    def __init__(self, message=None, *args, **kwargs):
        self.message = message
        super(SteamcmdException, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return repr(self.message)

    def __str__(self):
        return repr(self.message)


class Steamcmd(object):
    def __init__(self, install_path):
        """
        :param install_path: installation path for steamcmd
        """
        self.install_path = Path(install_path)
        self.install_path.mkdir(parents=True, exist_ok=True)

        self.platform = platform.system()
        if self.platform == 'Windows':
            self.steamcmd_url = 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip'
            self.steamcmd_zip = self.install_path / 'steamcmd.zip'
            self.steamcmd_exe = self.install_path / 'steamcmd.exe'

        elif self.platform == 'Linux':
            self.steamcmd_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"
            self.steamcmd_zip = self.install_path / 'steamcmd.tar.gz'
            self.steamcmd_exe = self.install_path / 'steamcmd.sh'

        else:
            raise SteamcmdException('The operating system is not supported. '
                                    f'Expected Linux or Windows, received: {self.platform}')

    def _download_steamcmd(self):
        try:
            self.steamcmd_zip.parent.mkdir(parents=True, exist_ok=True)
            return urllib.request.urlretrieve(self.steamcmd_url, self.steamcmd_zip)
        except Exception as e:
            raise SteamcmdException(f'An unknown exception occurred! {e}')

    def _extract_steamcmd(self):
        if self.platform == 'Windows':
            import zipfile
            with zipfile.ZipFile(self.steamcmd_zip, 'r') as f:
                return f.extractall(self.install_path)

        elif self.platform == 'Linux':
            import tarfile
            with tarfile.open(self.steamcmd_zip, 'r:gz') as f:
                return f.extractall(self.install_path)

        else:
            # This should never happen, but let's just throw it just in case.
            raise SteamcmdException('The operating system is not supported. '
                                    f'Expected Linux or Windows, received: {self.platform}')

    def install(self, force=False):
        """
        Installs steamcmd if it is not already installed to self.install_path.
        :param force: forces steamcmd install regardless of its presence
        :return:
        """
        if not self.steamcmd_exe.is_file() or force == True:
            # Steamcmd isn't installed. Go ahead and install it.
            try:
                self._download_steamcmd()
            except SteamcmdException as e:
                return e

            try:
                self._extract_steamcmd()
            except SteamcmdException as e:
                return e

    def install_gamefiles(self, gameid, game_install_dir: Path, user='anonymous', password=None, validate=False):
        """
        Installs gamefiles for dedicated server. This can also be used to update the gameserver.
        :param gameid: steam game id for the files downloaded
        :param game_install_dir: installation directory for gameserver files
        :param user: steam username (defaults anonymous)
        :param password: steam password (defaults None)
        :param validate: should steamcmd validate the gameserver files (takes a while)
        :return: subprocess call to steamcmd
        """
        if validate:
            validate = '-validate'
        else:
            validate = ''

        game_dir = Path(game_install_dir).absolute()
        logger.info(f'Installing game {gameid} to {game_dir}{" with validate" if validate else ""}')

        steamcmd_params = (
            str(self.steamcmd_exe),
            f'+login {user} {password}',
            f'+force_install_dir {game_dir}',
            f'+app_update {gameid} {validate}',
            '+quit',
        )
        retcode = subprocess.call(steamcmd_params)
        logger.info(f'SteamCMD process exited with code {retcode}')
        if retcode not in (0, 6, 7):
            raise SteamcmdException("Steamcmd was unable to run. Did you install your 32-bit libraries?")

    def install_workshopfiles(self, gameid, workshop_id, game_install_dir, user='anonymous', password=None):
        """
        Installs gamefiles for dedicated server. This can also be used to update the gameserver.
        :param gameid: steam game id for the files downloaded
        :param workshop_id: id of workshop item to download
        :param game_install_dir: installation directory for gameserver files
        :param user: steam username (defaults anonymous)
        :param password: steam password (defaults None)
        :return: subprocess call to steamcmd
        """
        game_dir = Path(game_install_dir).absolute()
        logger.info(f'Installing mod {workshop_id} from game {gameid} to {game_dir}')

        steamcmd_params = (
            str(self.steamcmd_exe),
            f'+login {user} {password}',
            f'+force_install_dir {game_dir}',
            f'+workshop_download_item {gameid} {workshop_id}',
            '+quit',
        )
        retcode = subprocess.call(steamcmd_params)
        logger.info(f'SteamCMD process exited with code {retcode}')
        if retcode not in (0, 6, 7):
            raise SteamcmdException("Steamcmd was unable to run. Did you install your 32-bit libraries?")


__all__ = [
    'SteamcmdException',
    'Steamcmd',
]

if __name__ == '__main__':
    data_path = Path('livedata').absolute()
    steamcmd_path: Path = data_path / 'steamcmd'
    game_path: Path = data_path / 'game'
    print()

    steamcmd_path.mkdir(parents=True, exist_ok=True)
    game_path.mkdir(parents=True, exist_ok=True)

    steamcmd = Steamcmd(steamcmd_path)
    steamcmd.install_gamefiles(376030, game_path)
    steamcmd.install_workshopfiles(346110, 895711211, game_path)
