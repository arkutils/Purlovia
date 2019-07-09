import json
import logging
from pathlib import Path

from config import ConfigFile, get_global_config
from utils.brigit import Git

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
        self.git.status()

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
        if not self.git.status('-s').strip():
            logger.info('There are no local changes')
            return

        # Add all changed files in the PublishDir
        self.git.add('--all', self.relative_publish_path)

        # Construct commit message using a simple message plus names and versions of all changed files
        message = self._create_commit_msg()
        print(message)

        # Commit
        # self.git.commit('-a', message=message)
        # Push
        # self.git.push()

    def _set_branch(self):
        branch = self.git.revParse('--abbrev-ref', 'HEAD').strip()

        if branch != self.config.settings.GitBranch:
            branch = self.config.settings.GitBranch
            self.git.checkout(self.config.settings.GitBranch)

    def _create_commit_msg(self):
        message = MESSAGE_HEADER

        lines = []
        status_output = self.git.status('-s', self.relative_publish_path)
        filelist = [line[3:].strip() for line in status_output.split('\n')]
        for filename in filelist:
            line = self._generate_info_line_from_file(filename)
            if line:
                lines.append(f'* {line}')

        if lines:
            message += '\n\n'
            message += '\n'.join(lines)

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
                return f'{path.name} ({title}) updated to version {version}'
            return f'{path.name} updated to version {version}'

        return None
