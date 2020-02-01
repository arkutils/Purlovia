# Helper for regionMaps.py

import re

def fixRegionName(regionName):
    regionName = re.sub(r'^The ', '', regionName)
    nameFixes = {'Frigid Plains': 'The Frigid Plains (The Island)',
                'Redwood Forests': 'Redwood Forests (The Island)',
                'Lava Cave': 'Lava Cave (The Island)',
                'Maw': 'The Maw'
            }
    if regionName in nameFixes:
        return nameFixes[regionName]
    return regionName


def coordTrans(x, Shift, Mult):
    return x / Mult + Shift

def mapTrans(x, borderLT, wh, mapSize):
    return (x - borderLT) * mapSize / wh