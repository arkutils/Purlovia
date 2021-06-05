'''
Helpers for regionMaps.py
'''

from urllib.parse import quote

from ..common import remove_unicode_control_chars

LINK_SAFE_CHARS = '~()*!.\'/'


def make_biome_link(map_name: str, biome_name: str, is_mod: bool) -> str:
    map_name = remove_unicode_control_chars(map_name)
    biome_name = remove_unicode_control_chars(biome_name)
    if is_mod:
        map_name = quote(map_name, safe=LINK_SAFE_CHARS)
        biome_name = quote(biome_name, safe=LINK_SAFE_CHARS)
        return f'/wiki/Mod:{map_name}/{biome_name}'
    return quote(f'/wiki/{biome_name}_({map_name})', safe=LINK_SAFE_CHARS).replace(' ', '_')


def translate_coord(x, shift, multiplier):
    return x/multiplier + shift


def map_translate_coord(x, border_l_or_t, wh, map_size):
    return (x-border_l_or_t) * map_size / wh
