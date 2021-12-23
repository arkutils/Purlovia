import json
import os
import tempfile
from pathlib import Path
from typing import Callable

from config import ConfigFile, get_global_config
from utils.brigit import Git, GitException
from utils.log import get_logger

__all__ = [
    'GitManager',
]

logger = get_logger(__name__)

MESSAGE_HEADER = "Raptor Claus just dropped some files off"


class GitManager:
    def __init__(self, config: ConfigFile = None):
        self.config = config or get_global_config()

        brigit_logger = get_logger('brigit')
        self.git = Git(str(self.config.settings.OutputPath), logger=brigit_logger)

    def before_exports(self):
        if self.config.settings.SkipGit:
            logger.info('Git interaction disabled')
            return

        logger.info('Verifying Git repo integrity')

        # Validate clone is valid
        self._validate_setup()

        # Check branch is correct
        self._set_branch()

        # Perform reset or pull, if configured
        self._do_reset_or_pull()

        logger.info('Git repo is setup and ready to go')

    def after_exports(self, relative_path: Path, commit_header: str, msg_fn: Callable[[Path], str]):
        if self.config.settings.SkipGit:
            return

        # If no files changed, return
        if not self._any_local_changes(relative_path):
            logger.info('No local changes, aborting')
            return

        # Add changed files in this path, recursively
        self._do_add(relative_path, all=True)

        # Construct commit message using the supplied message function
        message = self._create_commit_msg(relative_path, commit_header, msg_fn)

        # Commit
        self._do_commit(message, relative_path)

    def finish(self, game_version: str):
        if self.config.settings.SkipGit:
            return

        # If no changes to push, return
        if not self._any_changes_to_push():
            return

        # Tag
        self._do_tag(game_version)

        # Push
        self._do_push()

        logger.info('Git automation complete')

    def _any_local_changes(self, relative_path: Path):
        output = self.git.status('-s', '--', str(relative_path)).strip()
        return bool(output)

    def _any_changes_to_push(self):
        output = self.git.diff('--shortstat', 'HEAD', 'origin/' + self.config.git.Branch).strip()
        return bool(output)

    def _do_reset_or_pull(self):
        if self.config.git.SkipPull:
            logger.info('(pull/reset skipped by reset)')
        elif self.config.git.UseReset:
            logger.info('Performing hard reset to remote HEAD')
            self.git.fetch('--tags', '--force')
            self.git.reset('--hard', 'origin/' + self.config.git.Branch)
            self.git.clean('-dfq')
        else:
            logger.info('Performing pull')
            self.git.pull('--no-rebase', '--ff-only')

    def _do_add(self, relative_path: Path, all=False):
        if self.config.git.SkipCommit:
            logger.info('(add skipped by request)')
        else:
            if all:
                self.git.add('--all', '--', str(relative_path))
            else:
                self.git.add('--', str(relative_path))

    def _do_tag(self, game_version: str):
        '''Create a tag based on the game version, if it does not already exist.'''
        if self.config.git.SkipCommit:
            logger.info('(tag skipped by request)')
        elif not self.config.git.UseIdentity:
            logger.warning('Tagging skipped due to lack of git identity')
        else:
            version_tag = 'v' + game_version
            existing_tags = (self.git.tag('--list') or '').splitlines()
            existing_tags = [t for t in (tag.strip() for tag in existing_tags) if t]
            if version_tag in existing_tags:
                logger.info('Game version tag already exists')
                return

            self.git.tag(version_tag)
            logger.info(f'Created tag: {version_tag}')

    def _do_push(self):
        if self.config.git.SkipPush:
            logger.info('(push skipped by request)')
        elif not self.config.git.UseIdentity:
            logger.warning('Push skipped due to lack of git identity')
        else:
            logger.info('Pushing changes')
            self.git.push()
            logger.info('Pushing tags')
            self.git.push('--tags')

    def _do_commit(self, message: str, relative_path: Path):
        if self.config.git.SkipCommit:
            logger.info('(commit skipped by request)')
        elif not self.config.git.UseIdentity:
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
                self.git.commit('-F', f.name, '--', str(relative_path))
            finally:
                if tmpfilename:
                    os.unlink(tmpfilename)

    def _validate_setup(self):
        # This will throw if there's no git repo here
        self.git.status()

        if self.config.git.UseIdentity:
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
            logger.info('Git ready, without user identity')

    def _set_branch(self):
        branch = self.git.revParse('--abbrev-ref', 'HEAD').strip()

        if branch != self.config.git.Branch:
            self.git.checkout(self.config.git.Branch)

    def _create_commit_msg(self, relative_path: Path, commit_header: str, msg_fn: Callable[[Path], str]):
        message = commit_header

        lines = []
        status_output = self.git('-c', 'core.quotePath=false', 'status', '-s', '--', str(relative_path))
        filelist = [line[3:].strip() for line in status_output.split('\n')]
        for filename in filelist:
            if ' -> ' in filename:
                filename = filename.split(' -> ')[-1].strip()
            line = msg_fn(filename)
            if line is None:
                line = self._generate_info_line_from_file(filename)
            if line:
                lines.append(f'* {line}')

        if lines:
            message += '\n\n'
            message += '\n'.join(lines)

        logger.info('Commit message:\n%s', message)

        return message

    def _generate_info_line_from_file(self, filename: str):
        if not filename:
            return None

        path: Path = self.config.settings.OutputPath / filename

        if path.suffix.lower() == '.json':
            if path.name.lower() == '_manifest.json':
                return None
            if not path.is_file():
                return f'{filename} removed'

            with open(path, 'rt', encoding='utf-8') as f:
                data = json.load(f)

            version = data.get('version', None)

            title = data.get('mod', dict()).get('title', None)
            if title:
                return f'"{title}" updated to version {version}'

            mapname = data.get('map', None)
            if mapname:
                return f'"{mapname}" map updated to version {version}'

            return f'{filename} updated to version {version}'

        return None
