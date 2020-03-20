from ue.hierarchy import find_sub_classes


def fix_up_groups(spawngroups):
    '''Adds missing weights to classes without copying the data.'''
    for container in spawngroups:
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

        swap_rule = class_swaps.get(dino_class, None)
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
    for container in spawngroups:
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
    for container in spawngroups:
        for entry in container['entries']:
            entry['classes'], entry['classWeights'] = apply_ideal_swaps_to_entry(entry, class_swaps)


def copy_spawn_groups(spawngroups):
    copies = list()

    for container in spawngroups:
        copy = dict()
        copy['blueprintPath'] = container['blueprintPath']
        copy['maxNPCNumberMultiplier'] = container['maxNPCNumberMultiplier']
        copy['entries'] = [
            dict(
                weight=source['weight'],
                classes=[*source['classes']],
                classWeights=[*source['classWeights']],
            ) for source in container['entries']
        ]
        copies.append(copy)

    return copies
