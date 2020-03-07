# Helper for creatureSpawningMaps.py

import math
from typing import Optional

from .intermediate_types import SpawnFrequency
from .swaps import apply_ideal_swaps_to_entry

# TODO: Move this to overrides, or find a better way
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
    ],
    # Titanomyrma
    [
        '/Game/PrimalEarth/Dinos/Ant/Ant_Character_BP.Ant_Character_BP',
        '/Game/PrimalEarth/Dinos/Ant/FlyingAnt_Character_BP.FlyingAnt_Character_BP',
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


def calculate_blueprint_freqs(spawngroups, class_swap_rulesets, dino_classes):
    # The rarity is arbitrarily divided in 6 groups from "very rare" (0) to "very common" (5)
    frequencies = []
    dino_class_set = set(dino_classes)

    # Calculate how frequently spawning groups are chosen
    for group in spawngroups:
        if 'entries' not in group:
            continue
        entry_frequency_sum = 0
        frequency = group['maxNPCNumberMultiplier']
        total_group_weights = sum(entry['weight'] for entry in group['entries']) or 1

        for entry in group['entries']:
            # Apply class swaps
            classes, weights = entry['classes'], entry['classWeights']
            for swap_ruleset in class_swap_rulesets:
                classes, weights = apply_ideal_swaps_to_entry(dict(
                    classes=classes,
                    classWeights=weights,
                ), swap_ruleset)

            if not bool(dino_class_set & set(classes)):
                continue

            # Calculate total weight of classes in the spawning group
            total_entry_class_weights = sum(weights) or 1
            chances = [weight / total_entry_class_weights for weight in weights]

            # Calculate a combined chance of all entries for current blueprint
            entry_class_chance = sum(chances[index] for index, klass in enumerate(classes) if klass in dino_classes)
            entry_class_chance *= (entry['weight'] / total_group_weights)
            entry_frequency_sum += entry_class_chance

        frequency *= entry_frequency_sum
        if frequency > 0:
            frequencies.append(SpawnFrequency(group['blueprintPath'], frequency))

    return frequencies


def get_rarity_for_spawn(spawn_data, frequency: float):
    creature_number = frequency * spawn_data['minDesiredNumberOfNPC']
    # Calculate density from number of creatures and area
    area_density = ((spawn_data['locations'][0]['end']['long'] - spawn_data['locations'][0]['start']['long']) *
                    (spawn_data['locations'][0]['end']['lat'] - spawn_data['locations'][0]['start']['lat']))
    creature_density = creature_number / area_density
    # This formula is arbitrarily constructed to create 5 naturally feeling groups of rarity 0..5 (very rare to very common)
    return min(5, round(1.5 * (math.log(1 + 50*creature_density))))
