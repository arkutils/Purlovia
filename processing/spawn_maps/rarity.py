import math

from ue.hierarchy import find_sub_classes, inherits_from

from .intermediate_types import SpawnFrequency


def fix_up_groups(spawngroups):
    '''Adds missing weights to classes without copying the data.'''
    for container in spawngroups['spawngroups']:
        for entry in container['entries']:
            class_num = len(entry['classes'])
            weight_num = len(entry['classWeights'])

            # Remove excess weights if present
            if weight_num > class_num:
                entry['classWeights'] = entry['classWeights'][:class_num]
            # Grow the weights to match number of classes
            elif weight_num < class_num:
                entry['classWeights'] += [1] * (class_num-weight_num)


def make_random_class_weights_dict(random_class_weights):
    '''
    Generates a look-up dict for random class weights.
    '''
    lookup = dict()
    for remap_entry in random_class_weights:
        if not remap_entry['to']:
            continue

        from_classes = remap_entry['from']

        for from_class in from_classes:
            if from_class and from_class not in lookup:
                lookup[from_class] = remap_entry
    return lookup


def fix_up_swap_rule_weights(rule):
    swap_weights = [*rule['weights']]
    class_num = len(rule['to'])
    weight_num = len(rule['weights'])
    # Remove excess weights if present
    if weight_num > class_num:
        swap_weights = rule['weights'][:class_num]
    # Grow the weights to match number of classes
    elif weight_num < class_num:
        swap_weights += [1] * (class_num-weight_num)
    return swap_weights


def inflate_swap_rules(random_class_weights):
    '''
    Mutates a rule set with pre-processed inheritance.
    
    Target's "from" field will turn into a list of classes.
    '''
    for rule in random_class_weights:
        from_class = rule['from']
        # Make sure number of weights is equal to the number of targets
        weights = fix_up_swap_rule_weights(rule)

        from_classes = [from_class]
        if not rule['exact']:
            # Pre-process non-exact match
            from_classes += find_sub_classes(from_class)
            rule['exact'] = True

        rule['from'] = from_classes
        rule['weights'] = weights


def _get_swap_for_dino(blueprint_path, rules):
    if not blueprint_path:
        return None

    return rules.get(blueprint_path, None)


def apply_ideal_swaps_to_entry(entry, class_swaps):
    '''
    Recalculates classes and their weights to include class swaps of specific entries.
    Returns new lists of classes and weights.
    '''
    old_weights = entry['classWeights']
    new_classes = list()
    new_weights = list()

    for index, dino_class in enumerate(entry['classes']):
        weight = old_weights[index]

        swap_rule = _get_swap_for_dino(dino_class, class_swaps)
        if swap_rule:
            # Make new entries. Swap occurs.
            # Fix up the swap
            swap_weights = swap_rule['weights']
            rule_weight_sum = sum(swap_weights)
            swap_weights = [weight / rule_weight_sum for weight in swap_weights]

            for swap_index, target in enumerate(swap_rule['to']):
                new_classes.append(target)
                new_weights.append(weight * swap_weights[swap_index])
        else:
            # Copy the values. No swap.
            new_classes.append(dino_class)
            new_weights.append(weight)

    return new_classes, new_weights


def apply_ideal_grouplevel_swaps(spawngroups):
    '''
    Recalculates classes and weights of all groups to include swaps
    at entry level.
    Does not copy the input.
    '''
    for container in spawngroups['spawngroups']:
        for entry in container['entries']:
            if 'classSwaps' in entry:
                inflate_swap_rules(entry['classSwaps'])
                class_swaps = make_random_class_weights_dict(entry['classSwaps'])

                entry['classes'], entry['classWeights'] = apply_ideal_swaps_to_entry(entry, class_swaps)


def apply_ideal_global_swaps(spawngroups, random_class_weights):
    '''
    Recalculates classes and weights of all groups to include global swaps.
    Does not copy the input.
    '''
    class_swaps = make_random_class_weights_dict(random_class_weights)
    for container in spawngroups['spawngroups']:
        for entry in container['entries']:
            new_classes, new_weights = apply_ideal_swaps_to_entry(entry, class_swaps)
            entry['classes'] = new_classes
            entry['classWeights'] = new_weights


def calculate_blueprint_freqs(spawngroups, class_swap_rulesets, dino_classes):
    # The rarity is arbitrarily divided in 6 groups from "very rare" (0) to "very common" (5)
    frequencies = []
    dino_class_set = set(dino_classes)

    # Calculate how frequently spawning groups are chosen
    for group in spawngroups['spawngroups']:
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
