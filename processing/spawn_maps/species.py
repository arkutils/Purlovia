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


def collect_npc_spawning_data(bp_mappings, jsonSpawngroups):
    blueprintSpecies = {}

    for sg in jsonSpawngroups['spawngroups']:
        if 'entries' not in sg:
            continue

        for e in sg['entries']:
            if 'classes' not in e:
                continue

            for bp in e['classes']:
                if bp not in blueprintSpecies and bp in bp_mappings:
                    blueprintSpecies[bp] = {bp_mappings[bp]: 1}

    # extra classes
    # TODO: not present in spawngroups.
    if 'npcRandomSpawnClassWeights' in jsonSpawngroups:
        for scw in jsonSpawngroups['npcRandomSpawnClassWeights']:
            if 'chances' not in scw or len(scw['chances']) == 0 or 'to' not in scw or 'from' not in scw or len(
                    scw['from']) == 0 or len(scw['to']) != len(scw['chances']):
                continue

            for num, bp in enumerate(scw['to']):
                if bp in bp_mappings:
                    if scw['from'] in blueprintSpecies:
                        blueprintSpecies[scw['from']][bp_mappings[bp]] = scw['chances'][num]
                    else:
                        blueprintSpecies[scw['from']] = {bp_mappings[bp]: scw['chances'][num]}

    return blueprintSpecies
