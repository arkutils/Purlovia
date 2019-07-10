import os
import json
import logging
import tempfile
from pathlib import Path

from config import ConfigFile, get_global_config
from utils.brigit import Git, GitException

__all__ = [
    'GitManager',
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

MESSAGE_HEADER = "Raptor Claus just dropped some files off"


class GitManager:
    def __init__(self, config: ConfigFile = None):
        self.config = config or get_global_config()
        self.git = Git(str(self.config.settings.GitDirectory))

        # Just the parts of PublishDir that live "inside" GitDirectory (e.g. output/data/asb -> data/asb)
        self.relative_publish_path = str(self.config.settings.PublishDir.relative_to(self.config.settings.GitDirectory))

    def before_exports(self):
        if not self.config.settings.EnableGit:
            logger.info('Git interaction disabled, aborting')
            return

        logger.info('Verifying Git repo integrity')

        # Validate clone is valid
        self._validate_setup()

        # Check branch is correct (maybe checkout if not?)
        self._set_branch()

        logger.info('Git repo is setup and ready to go')

    def after_exports(self):
        if not self.config.settings.EnableGit:
            return

        # Pull and ensure it was clean
        logger.info('Pulling remote changes')
        self.git.pull('--no-rebase', '--ff-only')

        # If no files changed, return
        if not self.git.status('-s', '--', self.relative_publish_path).strip():
            logger.info('There are no local changes')
            return

        # Construct commit message using a simple message plus names and versions of all changed files
        message = self._create_commit_msg()

        # Commit
        self._do_commit(message)

        # Push
        # self.git.push()

        logger.info('Git automation complete')

    def _do_commit(self, message):
        logger.info('Performing commit')

        # Put the message in a temp file to avoid stupidly long command-line arguments
        tmpfilename: str
        with tempfile.NamedTemporaryFile('w', delete=False) as f:
            tmpfilename = f.name
            f.write(message)

        self.git.commit('-F', f.name, '--', self.relative_publish_path)
        os.unlink(tmpfilename)

    def _validate_setup(self):
        # This will throw if there's no git repo here
        self.git.status()

        # Check a custom user has been configured and is using a custom ssh identity
        username: str = '<unset>'
        try:
            # Each of these will throw a GitException if not present
            username = self.git.config('--local', 'user.name').strip()
            self.git.config('--local', 'user.email')
            self.git.config('--local', 'core.sshCommand')
        except GitException:
            logger.error("Git output repo does not have custom identity configuration. Aborting!")
            raise

        logger.info(f'Git configured as user: {username}')

    def _set_branch(self):
        branch = self.git.revParse('--abbrev-ref', 'HEAD').strip()

        if branch != self.config.settings.GitBranch:
            branch = self.config.settings.GitBranch
            self.git.checkout(self.config.settings.GitBranch)

    def _create_commit_msg(self):
        message = MESSAGE_HEADER

        lines = []
        status_output = self.git.status('-s', '--', self.relative_publish_path)
        filelist = [line[3:].strip() for line in status_output.split('\n')]
        for filename in filelist:
            line = self._generate_info_line_from_file(filename)
            if line:
                lines.append(f'* {line}')

        if lines:
            message += '\n\n'
            message += '\n'.join(lines)

        logger.info('Commit message:\n%s', message)

        return message

    def _generate_info_line_from_file(self, filename: str):
        path: Path = self.config.settings.GitDirectory / filename

        if not path.is_file:
            return f'{path.name} removed'

        if path.suffix.lower() == '.json':
            with open(path) as f:
                data = json.load(f)

            version = data.get('version', None)
            title = data.get('mod', dict()).get('title', None)
            if title:
                return f'"{title}" updated to version {version}'
            return f'{path.name} updated to version {version}'

        return None
