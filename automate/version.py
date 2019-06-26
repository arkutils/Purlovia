__all__ = [
    'createVersion',
]


def createVersion(gameVersion, timestamp):
    if gameVersion.count('.') < 1:
        gameVersion = gameVersion + '.0'
    gameVersion = gameVersion.replace('-', '')
    version = f'{gameVersion}.{timestamp}'
    return version
