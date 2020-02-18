# Helper for creatureSpawningMaps.py

import json
import re
from typing import Any, Dict


def generate_dino_mappings(asb):
    '''
    Collects a map of blueprints sharing names.
    '''
    v = dict()

    for species in asb['species']:
        descriptive_name = species['name']
        blueprint_path = species['blueprintPath']

        if not blueprint_path.endswith('_C'):
            blueprint_path += '_C'

        if descriptive_name not in v:
            v[descriptive_name] = []
        v[descriptive_name].append(blueprint_path)

    return v
