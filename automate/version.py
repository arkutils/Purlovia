from typing import Union

__all__ = [
    'createExportVersion',
]


def createExportVersion(gameVersion: str, timestamp: Union[str, int]) -> str:
    '''
    Create a version number of the agreed format for ASB export files.

    >>> createExportVersion('1', '987')
    '1.0.987'
    >>> createExportVersion('1', 987)
    '1.0.987'
    >>> createExportVersion('1.2', 987)
    '1.2.987'
    >>> createExportVersion('1.2.3', 987)
    '1.2.987'
    '''
    gameVersion = gameVersion.replace('-', '.')
    parts = gameVersion.split('.')
    while len(parts) < 2:
        parts.append('0')
    gameVersion = '.'.join(parts[:2])
    version = f'{gameVersion}.{timestamp}'
    return version
