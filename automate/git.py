from config import ConfigFile, get_global_config

__all__ = [
    'GitManager',
]


class GitManager:
    def __init__(self, config: ConfigFile = None):
        self.config = config or get_global_config()

    def before_exports(self):
        pass

    def after_exports(self):
        pass
