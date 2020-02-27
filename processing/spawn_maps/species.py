# Helper for creatureSpawningMaps.py

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

_MERGED_DINOS = [
    # Coelacanths
    [
        '/Game/PrimalEarth/Dinos/Coelacanth/Coel_Character_BP.Coel_Character_BP_C',
        '/Game/PrimalEarth/Dinos/Coelacanth/Coel_Character_BP_Ocean.Coel_Character_BP_Ocean_C',
    ],
]


def _get_front_dino_merge_group(blueprint_path: str) -> Optional[str]:
    for group in _MERGED_DINOS:
        if blueprint_path in group:
            return group[0]
    return None


def generate_dino_mappings(asb):
    '''
    Collects a list of dino blueprints and does optional merging.
    '''
    v = dict()

    for species in asb['species']:
        blueprint_path = species['blueprintPath']

        if not blueprint_path.endswith('_C'):
            blueprint_path += '_C'

        higher_class = _get_front_dino_merge_group(blueprint_path)
        if not higher_class:
            higher_class = blueprint_path
        if higher_class not in v:
            v[higher_class] = list()

        v[higher_class].append(blueprint_path)

    return v


def determine_tamability(asb, blueprint_path) -> bool:
    blueprint_path_compat = blueprint_path.rstrip('_C')
    for species in asb['species']:
        if species['blueprintPath'] == blueprint_path_compat:
            return (species['taming']['violent'] or species['taming']['nonViolent']) if 'taming' in species else False
    return False
