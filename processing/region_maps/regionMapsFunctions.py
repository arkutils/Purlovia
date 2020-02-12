# Helper for regionMaps.py

import re

NAME_FIXES = {
    'Frigid Plains': 'The Frigid Plains (The Island)',
    'Redwood Forests': 'Redwood Forests (The Island)',
    'Lava Cave': 'Lava Cave (The Island)',
    'Maw': 'The Maw'
}


def fix_region_name(region_name):
    # TODO: Rewrite into overrides (__SHOULD NOT__ AFFECT MAP DATA)
    region_name = re.sub(r'^The ', '', region_name)
    return NAME_FIXES.get(region_name, region_name)


def coordTrans(x, Shift, Mult):
    return x/Mult + Shift


def mapTrans(x, borderLT, wh, mapSize):
    return (x-borderLT) * mapSize / wh
