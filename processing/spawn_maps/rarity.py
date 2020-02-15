import math

from .intermediate_types import SpawnFrequency


def calculate_group_frequencies(spawngroups, class_modifiers):
    # The rarity is arbitrarily divided in 6 groups from "very rare" (0) to "very common" (5)
    frequencies = []

    # Calculate how frequently spawning groups are chosen
    for group in spawngroups:
        if 'entries' not in group:
            continue
        frequency = group['maxNPCNumberMultiplier']
        entry_frequency_sum = 0

        total_group_weights = sum(entry['weight'] for entry in group['entries']) or 1

        for entry in group['entries']:
            if 'classes' not in entry or len(entry['classes']) == 0:
                continue

            # Check all entries for the current blueprint
            # Some groups have multiple entries for the same blueprint
            spawn_indices = []
            for index, npc_spawn in enumerate(entry['classes']):
                if npc_spawn in class_modifiers.keys():
                    spawn_indices.append((index, class_modifiers[npc_spawn]))

            # Calculate total weight of classes in the spawning group
            if entry['classWeights']:
                total_entry_class_weights = sum(entry['classWeights']) or 1
            else:
                total_entry_class_weights = len(entry['classes']) or 1
            entry_class_chances_data = [weight / total_entry_class_weights for weight in entry['classWeights']]

            entry_class_chance = 0  # The combined chance of all entries for current blueprint
            for index, modifier in spawn_indices:
                if len(entry['classWeights']) > index:
                    entry_class_chance += entry_class_chances_data[index] * modifier
                # assume default weight of 1 if there is no specific value
                else:
                    entry_class_chance += 1
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
