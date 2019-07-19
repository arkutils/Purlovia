from typing import Sequence, Set

from ark.asset import findComponentExports
from ue.asset import UAsset
from ue.loader import AssetLoader
from ue.utils import *

from .properties import gather_properties


def get_mod_remapped_spawners(asset: UAsset):
    for export in findComponentExports(asset):
        remap_spawners = get_property(export, 'GlobalNPCRandomSpawnClassWeights')
        if not remap_spawners: return
        for entry in remap_spawners.values:
            fromPkg = get_clean_name(entry.values[0].value.value.value.namespace)
            toPkgs = [get_clean_name(toPkg.value.value.namespace) for toPkg in entry.values[1].value.values]
            yield (fromPkg, toPkgs)


def get_mod_remapped_npcs(asset: UAsset):
    for export in findComponentExports(asset):
        remap_entries = get_property(export, 'Remap_NPC')
        if not remap_entries: return
        for entry in remap_entries.values:
            fromPkg = str(entry.values[0].value.value.value.namespace.value.name)
            toPkg = str(entry.values[1].value.value.value.namespace.value.name)
            yield (fromPkg, toPkg)


def get_species_from_mod(asset: UAsset, loader: AssetLoader = None) -> list:
    loader = loader or asset.loader
    assert loader and asset.assetname
    this_mod = loader.get_mod_name(asset.assetname)
    mod_species = set()

    # Gather species from the remapped NPCs list
    for _, toPkg in get_mod_remapped_npcs(asset):
        to_mod = loader.get_mod_name(toPkg)
        if to_mod == this_mod:
            mod_species.add(toPkg)

    # Gather species from the remapped spawn zones
    for _, toPkgs in get_mod_remapped_spawners(asset):
        for toPkg in toPkgs:
            to_mod = loader.get_mod_name(toPkg)
            if to_mod == this_mod:
                mod_species.add(toPkg)

    return sorted(list(mod_species))


def is_mod(asset: UAsset) -> bool:
    if not asset.default_export: return False
    if 'properties' not in asset.default_export.field_values: return False
    if not get_property(asset.default_export, 'ModName'): return False
    return True


def load_all_species(modasset: UAsset):
    assert modasset.loader
    species_data = []
    for pkgname in get_species_from_mod(modasset):
        pkg = modasset.loader[pkgname]
        props = gather_properties(pkg)
        species_data.append((pkg, props))

    return species_data
