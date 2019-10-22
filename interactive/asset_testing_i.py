#%% Run Me

import json
from time import perf_counter, process_time
from typing import *

import ark.discovery
from automate.ark import ArkSteamManager, readModData

arkman = ArkSteamManager()
loader = arkman.getLoader()
names_file = 'names.txt'
inherit_file = 'inherit.txt'

#%% Attempt to load assets and verify if they're a species asset or not
assets_from_name = set()
assets_from_inheritance = set()
num_assets = 0

start_time1 = process_time()
start_time2 = perf_counter()

inheritance_checker = ark.discovery.ByInheritance(loader)
name_checker = ark.discovery.ByRawData(loader)

for assetname in loader.find_assetnames('.*', toppath='/Game'):
    num_assets += 1
    if (num_assets % 100) == 0:
        print(num_assets)

    try:
        _ = loader[assetname]
        if inheritance_checker.is_species(assetname):
            assets_from_inheritance.add(assetname)

        if name_checker.is_species(assetname):
            assets_from_name.add(assetname)

    except:
        continue

    loader.wipe_cache_with_prefix(assetname)

end_time1 = process_time()
end_time2 = perf_counter()

print(f'process_time: {end_time1 - start_time1} seconds')
print(f'perf_counter: {end_time2 - start_time2} seconds')
print(len(assets_from_name))
print(len(assets_from_inheritance))
print(num_assets)

with open('__' + names_file, 'w') as outfile:
    outfile.writelines(asset + '\n' for asset in sorted(assets_from_name))
with open('__' + inherit_file, 'w') as outfile:
    outfile.writelines(asset + '\n' for asset in sorted(assets_from_inheritance))

#%% Compare differences from the search
mainfile = inherit_file
compfile = names_file

with open('__' + mainfile) as f1:
    with open('__' + compfile) as f2:
        difference = sorted(set(f1.readlines()) - set(f2.readlines()))

print(difference)

#%% Check "undesired" assets against known good assets

# desired_assets = [
#     '/Game/Mods/Primal_Fear/Aberration/Dinos/ChupaCabra/ALPHA_ChupaCabra_Character_BP',
#     '/Game/Aberration/Dinos/Nameless/Xenomorph_Character_BP_Female',
#     '/Game/Aberration/Dinos/Nameless/Xenomorph_Character_BP',
#     '/Game/Mods/ClassicFlyers/Dinos/Wyvern/Wyvern_Character_BP_Poison',
#     '/Game/Mods/SpeedyFlyers/Dinos/Wyvern/Wyvern_Character_BP_Base',
#     '/Game/PrimalEarth/Dinos/Microraptor/Microraptor_Character_BP',
# ]

# undesired_assets = ['/Game/Mods/AE/Dinos/Dino_Character_BP_AE']
# bad_assets = ['/Game/Mods/AE/Dinos/Dino_Character_BP_AE']

# names_in_asset: Set[str] = set()
# for asset in undesired_assets:
#     names = set(str(name) for name in loader.partially_load_asset(asset).names)
#     if not names_in_asset:
#         names_in_asset = names  # if not names_in_asset else names_in_asset - names
#     else:
#         names_in_asset &= names

# for asset in desired_assets:
#     names_in_asset -= set(str(name) for name in loader.partially_load_asset(asset).names)

# print(sorted(names_in_asset))

#%%
