def merge_game_mod_groups(core_groups, changeset):
    # Create a dictionary for quicker look-ups of core groups
    groups = dict()
    for group in core_groups:
        groups[group['blueprintPath']] = group

    # Merge with the change-set
    for change in changeset:
        blueprint_path = change['blueprintPath']
        if blueprint_path not in groups:
            continue

        if 'entries' in change:
            groups[blueprint_path]['entries'] += change['entries']
        if 'limits' in change:
            groups[blueprint_path]['limits'] += change['limits']
