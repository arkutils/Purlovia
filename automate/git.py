import json
import logging
from pathlib import Path
import requests

from config import ConfigFile, get_global_config
from utils.brigit import Git

__all__ = [
    'GitManager',
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

MESSAGE_HEADER = "Raptor Claus just dropped some files off"
GITHUB_API = 'https://api.github.com/graphql'


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
        status = self.git.status().split('\n')
        branch = status[0].split(' ')[-1]
        if self._check_branch(branch):
            if status[-1].strip() == 'nothing to commit, working tree clean':
                logger.info('Git is setup and ready to commit to the correct branch')
            else:
                logger.warning('Git is on the correct branch but the working tree is not clean.')
                self._stash_changes()
        else:
            if status[-1].strip() == 'nothing to commit, working tree clean':
                logger.info('Git is on the wrong branch but the working tree is clean.')
                self.git.checkout(self.config.settings.GitBranch)
                logger.info('Checkout complete. Git is ready.')
            else:
                logger.warning('Git is on the wrong branch and some files have been modified')
                self._stash_changes()
                self.git.checkout(self.config.settings.GitBranch)
                logger.info('Checkout complete. Git is ready.')

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

    def _check_branch(self, branch):
        return branch == self.config.settings.GitBranch

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

    @staticmethod
    def _create_issue(title: str, body: str):
        try:
            with open('token.json') as fp:
                token = json.load(fp)['token']
        except FileNotFoundError:
            logging.error("Cannot create issue because GitHub token file is not found.")
        else:
            header = {"Authorization": f'bearer {token}'}
            payload = {'query': f'mutation {{ createIssue(input: {{ repositoryId:"MDEwOlJlcG9zaXRvcnkxNzIzMzM4MjA=", '  # TODO move repositoryId to config
                                f'title:"{title}", body:"{body}" }}) {{ issue {{ id }} }} }}'}
            r = requests.post(GITHUB_API, headers=header, data=json.dumps(payload))
            try:
                id = json.loads(r.text)['data']['createIssue']['issue']['id']
            except KeyError:
                error_string = '\n'.join([error['message'] for error in r.json()['errors']])
                logger.warning(f"Failed to create issue on GitHub:\n{error_string}")
            else:
                logger.info(f"GitHub Issue created: {id}")

    def _stash_changes(self):
        stash = self.git.stash()
        logger.info(stash)
        stash_msg = self._get_stashed_changes()
        issue_body = f'The working tree was not clean when the export was run. The modifications were stashed.\n\n' \
                     f'`{stash}`\n```\n{stash_msg}\n```'
        self._create_issue('Purlovia: Stashed Modifications', issue_body)

    def _get_stashed_changes(self) -> str:
        stash_list = self.git.stash('list').split('\n')
        stash_message = ''

        for stash in stash_list:
            stash_id = stash.split(':')[0]
            stash_message += stash
            stash_message += '\n    '.join(self.git.stash('show', stash_id).split('\n'))
            stash_message += '\n'

        return stash_message
