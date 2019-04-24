import os
import platform
import urllib.request
import zipfile
import tarfile
import subprocess


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
        self.install_path = install_path
        os.makedirs(self.install_path, exist_ok=True)

        self.platform = platform.system()
        if self.platform == 'Windows':
            self.steamcmd_url = 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip'
            self.steamcmd_zip = os.path.join(self.install_path, 'steamcmd.zip')
            self.steamcmd_exe = os.path.join(self.install_path, 'steamcmd.exe')

        elif self.platform == 'Linux':
            self.steamcmd_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"
            self.steamcmd_zip = os.path.join(self.install_path, 'steamcmd.tar.gz')
            self.steamcmd_exe = os.path.join(self.install_path, 'steamcmd.sh')

        else:
            raise SteamcmdException('The operating system is not supported.'
                                    'Expected Linux or Windows, received: {}'.format(self.platform))

    def _download_steamcmd(self):
        try:
            os.makedirs(os.path.dirname(self.steamcmd_zip), exist_ok=True)
            return urllib.request.urlretrieve(self.steamcmd_url, self.steamcmd_zip)
        except Exception as e:
            raise SteamcmdException('An unknown exception occurred! {}'.format(e))

    def _extract_steamcmd(self):
        if self.platform == 'Windows':
            with zipfile.ZipFile(self.steamcmd_zip, 'r') as f:
                return f.extractall(self.install_path)

        elif self.platform == 'Linux':
            with tarfile.open(self.steamcmd_zip, 'r:gz') as f:
                return f.extractall(self.install_path)

        else:
            # This should never happen, but let's just throw it just in case.
            raise SteamcmdException('The operating system is not supported.'
                                    'Expected Linux or Windows, received: {}'.format(self.platform))

    def install(self, force=False):
        """
        Installs steamcmd if it is not already installed to self.install_path.
        :param force: forces steamcmd install regardless of its presence
        :return:
        """
        if not os.path.isfile(self.steamcmd_exe) or force == True:
            # Steamcmd isn't installed. Go ahead and install it.
            try:
                self._download_steamcmd()
            except SteamcmdException as e:
                return e

            try:
                self._extract_steamcmd()
            except SteamcmdException as e:
                return e
        else:
            raise SteamcmdException('Steamcmd is already installed. Reinstall is not necessary.' 'Use force=True to override.')
        return

    def install_gamefiles(self, gameid, game_install_dir, user='anonymous', password=None, validate=False):
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
            validate = 'validate'
        else:
            validate = None

        steamcmd_params = (
            self.steamcmd_exe,
            '+login {} {}'.format(user, password),
            '+force_install_dir {}'.format(game_install_dir),
            '+app_update {}'.format(gameid),
            '{}'.format(validate),
            '+quit',
        )
        retcode = subprocess.call(steamcmd_params)
        if retcode not in (0, 6, 7):
            raise SteamcmdException("Steamcmd was unable to run. Did you install your 32-bit libraries?")

    def install_workshopfiles(self, gameid, workshop_id, game_install_dir, user='anonymous', password=None, validate=False):
        """
        Installs gamefiles for dedicated server. This can also be used to update the gameserver.
        :param gameid: steam game id for the files downloaded
        :param workshop_id: id of workshop item to download
        :param game_install_dir: installation directory for gameserver files
        :param user: steam username (defaults anonymous)
        :param password: steam password (defaults None)
        :param validate: should steamcmd validate the gameserver files (takes a while)
        :return: subprocess call to steamcmd
        """
        if validate:
            validate = 'validate'
        else:
            validate = None

        steamcmd_params = (
            self.steamcmd_exe,
            '+login {} {}'.format(user, password),
            '+force_install_dir {}'.format(game_install_dir),
            '+workshop_download_item {} {}'.format(gameid, workshop_id),
            '{}'.format(validate),
            '+quit',
        )
        retcode = subprocess.call(steamcmd_params)
        if retcode not in (0, 6, 7):
            raise SteamcmdException("Steamcmd was unable to run. Did you install your 32-bit libraries?")


if __name__ == '__main__':
    data_path = os.path.abspath(os.path.join('.', 'livedata'))
    steamcmd_path = os.path.join(data_path, 'steamcmd')
    game_path = os.path.join(data_path, 'game')

    os.makedirs(steamcmd_path, exist_ok=True)
    os.makedirs(game_path, exist_ok=True)

    steamcmd = Steamcmd(steamcmd_path)
    steamcmd.install_gamefiles(376030, game_path)
    steamcmd.install_workshopfiles(346110, 895711211, game_path)
