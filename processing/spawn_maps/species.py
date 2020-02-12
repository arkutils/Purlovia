# Helper for creatureSpawningMaps.py

import json
import re
from typing import Any, Dict


def make_species_mapping_from_asb(d: Dict[str, Any]) -> Dict[str, str]:
    v = dict()

    for species in d['species']:
        species_name = species['name']
        blueprint_path = species['blueprintPath']

        # TODO: Move to ASB overrides.
        if species_name == 'Rock Elemental':
            if re.search(r'IceGolem', blueprint_path):
                species_name = 'Ice Golem'
            elif re.search(r'ChalkGolem', blueprint_path):
                species_name = 'Chalk Golem'

        if not blueprint_path.endswith('_C'):
            blueprint_path += '_C'

        v[blueprint_path] = species_name

    return v


def collect_class_spawning_data(bp_mappings, world_settings, spawning_groups):
    '''
    Collects chances of a specific dino class appearing.
    '''
    v = {}

    for container in spawning_groups['spawngroups']:
        if 'entries' not in container:
            continue

        for entry in container['entries']:
            for blueprint_path in entry['classes']:
                if blueprint_path not in v and blueprint_path in bp_mappings:
                    v[blueprint_path] = {bp_mappings[blueprint_path]: 1}

    # Include random class swaps that might happen
    global_npc_weights = world_settings['worldSettings'].get('randomNPCClassWeights', [])
    for scw in global_npc_weights:
        if not scw['weights'] or not scw['from'] or len(scw['to']) != len(scw['weights']):
            continue

        total_weights = sum(scw['weights']) or 1
        chances = [weight / total_weights for weight in scw['weights']]

        for index, blueprint_path in enumerate(scw['to']):
            if blueprint_path in bp_mappings:
                if scw['from'] not in v:
                    v[scw['from']] = dict()

                v[scw['from']][bp_mappings[blueprint_path]] = chances[index]

    return v


def merge_class_spawning_data(species):
    '''
    Merges data of species with the same name and generates a new structure.
    '''
    copy = dict(**species)
    new = dict()
    for blueprint, blueprint_data in copy.items():
        for descriptive_name, modifier in blueprint_data.items():
            if descriptive_name not in new:
                new[descriptive_name] = {blueprint: modifier}
            else:
                new[descriptive_name][blueprint] = modifier

    return new
