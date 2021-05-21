from typing import Iterable, Set

from config import get_global_config

__all__ = [
    'get_core_mods',
    'get_managed_mods',
    'get_official_mods',
    'get_separate_mods',
    'get_aliases_for_mod',
]


def _mod_sorter(modid: str):
    try:
        return f'{int(modid):014d}'
    except ValueError:
        return modid


def get_official_mods() -> Iterable[str]:
    '''A list of mods that are installed as part of the base game.'''
    config = get_global_config()
    official_mods = sorted(set(config.official_mods.ids()), key=_mod_sorter)
    return official_mods


def get_managed_mods() -> Iterable[str]:
    '''A list of mods that should be installed and managed.'''
    config = get_global_config()
    official_mods = set(config.official_mods.ids())
    separate_mods = set(config.settings.SeparateOfficialMods)
    extract_mods = set(config.mods)
    managed_mods = sorted(extract_mods - separate_mods - official_mods, key=_mod_sorter)
    return managed_mods


def get_core_mods() -> Iterable[str]:
    '''A list of mods that should be included in 'core' extraction data.'''
    config = get_global_config()
    official_mods = set(config.official_mods.ids())
    separate_mods = set(config.settings.SeparateOfficialMods)
    extract_mods = set(config.extract_mods if config.extract_mods is not None else config.mods)
    core_mods = sorted(official_mods - separate_mods - extract_mods, key=_mod_sorter)
    return core_mods


def get_separate_mods() -> Iterable[str]:
    '''A list of mods that should be extracted into separate files.'''
    config = get_global_config()
    extract_mods = sorted(set(config.extract_mods if config.extract_mods is not None else config.mods), key=_mod_sorter)
    return extract_mods


def get_aliases_for_mod(modid: str) -> Set[str]:
    config = get_global_config()
    return config.combine_mods.src_to_aliases.get(modid, set())
