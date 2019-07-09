from config import ConfigFile, get_global_config

__all__ = [
    'GitManager',
]


class GitManager:
    def __init__(self, config: ConfigFile = None):
        self.config = config or get_global_config()

    def before_exports(self):
        # Validate clone is valid
        # Check branch is correct (maybe checkout if not?)
        # Pull and ensure it was clean
        pass

    def after_exports(self):
        # If no files changed, return
        # Add all changed files
        # Construct commit message using a simple message plus names and versions of all changed files.
        # Commit
        # Push
        pass
