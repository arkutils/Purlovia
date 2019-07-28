import json
import os
import tempfile
from logging import NullHandler, getLogger
from pathlib import Path

from config import ConfigFile, get_global_config
from utils.brigit import Git, GitException

__all__ = [
    'GitManager',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())

MESSAGE_HEADER = "Raptor Claus just dropped some files off"


class GitManager:
    def __init__(self, config: ConfigFile = None):
        self.config = config or get_global_config()
        self.git = Git(str(self.config.settings.GitDirectory))

        # Just the parts of PublishDir that live "inside" GitDirectory (e.g. output/data/asb -> data/asb)
        self.relative_publish_path = str(self.config.settings.PublishDir.relative_to(self.config.settings.GitDirectory))

    def before_exports(self):
        if not self.config.settings.EnableGit:
            logger.info('Git interaction disabled')
            return

        logger.info('Verifying Git repo integrity')

        # Validate clone is valid
        self._validate_setup()

        # Check branch is correct
        self._set_branch()

        # Perform reset, if configured
        self._do_reset()

        logger.info('Git repo is setup and ready to go')

    def after_exports(self):
        if not self.config.settings.EnableGit:
            return

        # Perform pull, if configured
        self._do_pull()

        # If no files changed, return
        if not self._any_local_changes():
            logger.info('No local changes, aborting')
            return

        # Add changed files
        self._do_add()

        # Construct commit message using a simple message plus names and versions of changed files
        message = self._create_commit_msg()

        # Commit
        self._do_commit(message)

        # Push
        self._do_push()

        logger.info('Git automation complete')

    def _any_local_changes(self):
        output = self.git.status('-s', '--', self.relative_publish_path).strip()
        return bool(output)

    def _do_reset(self):
        if self.config.settings.GitUseReset:
            logger.info('Performing hard reset to remote HEAD')
            if not self.config.settings.SkipPull:
                self.git.fetch()
                self.git.reset('--hard', 'origin/' + self.config.settings.GitBranch)
            else:
                logger.info('(skipped)')

    def _do_pull(self):
        if not self.config.settings.GitUseReset:
            logger.info('Performing pull')
            if not self.config.settings.SkipPull:
                self.git.pull('--no-rebase', '--ff-only')
            else:
                logger.info('(skipped)')

    def _do_add(self):
        if self.config.settings.SkipCommit:
            logger.info('(skipped by request)')
        else:
            self.git.add('--', self.relative_publish_path)

    def _do_push(self):
        if self.config.settings.SkipPush:
            logger.info('(push skipped by request)')
        elif not self.config.settings.GitUseIdentity:
            logger.warning('Push skipped due to lack of git identity')
        else:
            logger.info('Pushing changes')
            self.git.push()

    def _do_commit(self, message):
        if self.config.settings.SkipCommit:
            logger.info('(commit skipped by request)')
        elif not self.config.settings.GitUseIdentity:
            logger.warning('Commit skipped due to lack of git identity')
        else:
            logger.info('Performing commit')

            try:
                # Put the message in a temp file to avoid stupidly long command-line arguments
                tmpfilename: str
                with tempfile.NamedTemporaryFile('w', delete=False) as f:
                    tmpfilename = f.name
                    f.write(message)

                # Run the commit
                self.git.commit('-F', f.name, '--', self.relative_publish_path)
            finally:
                if tmpfilename:
                    os.unlink(tmpfilename)

    def _validate_setup(self):
        # This will throw if there's no git repo here
        self.git.status()

        if self.config.settings.GitUseIdentity:
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
        else:
            logger.info(f'Git ready, without user identity')

    def _set_branch(self):
        branch = self.git.revParse('--abbrev-ref', 'HEAD').strip()

        if branch != self.config.settings.GitBranch:
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
            if path.name.lower() == '_manifest.json':
                return None

            with open(path) as f:
                data = json.load(f)

            version = data.get('version', None)
            title = data.get('mod', dict()).get('title', None)
            if title:
                return f'"{title}" updated to version {version}'
            return f'{path.name} updated to version {version}'

        return None
