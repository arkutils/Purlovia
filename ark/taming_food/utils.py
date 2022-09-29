def bp_to_clean_class(bp: str):
    bp = bp[bp.rfind('.') + 1:]
    bp = bp.removeprefix('PrimalItemConsumable_')
    bp = bp.removesuffix('_C')
    return bp


def match_searches(term: str, searches: tuple[str] | None):
    '''
    >>> match_searches('PrimalItemConsumable_Egg_C', None)
    False
    >>> match_searches('PrimalItemConsumable_Egg_C', ('Egg',))
    True
    >>> match_searches('PrimalItemConsumable_Egg_C', ('Egg', 'Consum'))
    True
    >>> match_searches('PrimalItemConsumable_Egg_C', ('Egg', 'Consum', '-Meat'))
    True
    >>> match_searches('PrimalItemConsumable_Egg_C', ('Egg', 'Consum', 'Meat'))
    False
    >>> match_searches('PrimalItemConsumable_EggMeat_C', ('Egg', 'Consum', '-Meat'))
    False
    '''
    if not searches:
        return False

    term = term.lower()

    for search in searches:
        search = search.lower()
        if search.startswith('-'):
            if search[1:] in term:
                return False
        elif search not in term:
            return False

    return True
