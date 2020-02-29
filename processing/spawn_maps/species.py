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
    # Tusoteuthis
    [
        '/Game/PrimalEarth/Dinos/Tusoteuthis/Tusoteuthis_Character_BP.Tusoteuthis_Character_BP_C',
        '/Game/PrimalEarth/Dinos/Tusoteuthis/Tusoteuthis_Character_BP_Caves.Tusoteuthis_Character_BP_Caves_C',
    ],
    # Megalosaurus
    [
        '/Game/PrimalEarth/Dinos/Megalosaurus/Megalosaurus_Character_BP.Megalosaurus_Character_BP_C',
        '/Game/PrimalEarth/Dinos/Megalosaurus/Megalosaurus_Character_BP_TekCave.Megalosaurus_Character_BP_TekCave_C',
    ],
    # Giganotosaurus,
    [
        '/Game/PrimalEarth/Dinos/Giganotosaurus/Gigant_Character_BP.Gigant_Character_BP_C',
        '/Game/PrimalEarth/Dinos/Giganotosaurus/Gigant_Character_BP_TekCave.Gigant_Character_BP_TekCave_C',
    ],
    # Seeker
    [
        '/Game/Aberration/Dinos/Pteroteuthis/Pteroteuthis_Char_BP.Pteroteuthis_Char_BP_C',
        '/Game/Aberration/Dinos/Pteroteuthis/Pteroteuthis_Char_BP_Surface.Pteroteuthis_Char_BP_Surface_C',
    ],
    # Nameless
    [
        '/Game/Aberration/Dinos/ChupaCabra/ChupaCabra_Character_BP.ChupaCabra_Character_BP_C',
        '/Game/Aberration/Dinos/ChupaCabra/ChupaCabra_Character_BP_Surface.ChupaCabra_Character_BP_Surface_C',
    ],
    # Lunar Sabertooth Salmon
    [
        '/Game/Genesis/Dinos/BiomeVariants/Lunar_Salmon/Lunar_Salmon_Character_BP.Lunar_Salmon_Character_BP_C',
        '/Game/Genesis/Dinos/BiomeVariants/Lunar_Salmon/Rare_Lunar_Salmon_Character_BP.Rare_Lunar_Salmon_Character_BP_C',
    ]
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
