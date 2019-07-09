import logging
from config import ConfigFile, get_global_config
from utils.brigit import Git

__all__ = [
    'GitManager',
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class GitManager:
    def __init__(self, config: ConfigFile = None):
        self.config = config or get_global_config()
        self.git = Git(str(self.config.settings.GitDirectory))

    def before_exports(self):
        if not self.config.settings.EnableGit:
            return

        # Validate clone is valid
        self.git.status()

        # Check branch is correct (maybe checkout if not?)
        self._set_branch()

    def after_exports(self):
        if not self.config.settings.EnableGit:
            return

        # Pull and ensure it was clean
        self.git.pull()

        # If no files changed, return
        if not self.git.status('-s').strip():
            return

        # Add all changed files
        self.git.add('--all')
        # Construct commit message using a simple message plus names and versions of all changed files.
        message = 'Raptor Claus just dropped some files off'
        # Commit
        # self.git.commit('-a', message=message)
        # Push
        # self.git.push()

    def _set_branch(self):
        branch = self.git.revParse('--abbrev-ref', 'HEAD').strip()

        if branch != self.config.settings.GitBranch:
            branch = self.config.settings.GitBranch
            self.git.checkout(self.config.settings.GitBranch)
