'''
Helpers for regionMaps.py
'''

import re
from urllib.parse import quote


def make_biome_article_name(map_name: str, biome_name: str, is_mod: bool) -> str:
    if is_mod:
        name = f'Mod:{map_name}/{biome_name}'
    else:
        name = f'{biome_name} ({map_name})'
    return quote(name, safe='()')


def coordTrans(x, Shift, Mult):
    return x/Mult + Shift


def map_translate_coord(x, borderLT, wh, mapSize):
    return (x-borderLT) * mapSize / wh
