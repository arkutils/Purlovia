#%% Run Me
import json
import os
from time import process_time, perf_counter
from automate.ark import ArkSteamManager, readModData

arkman = ArkSteamManager(skipInstall=True)
loader = arkman.createLoader()
output_file = 'partial.txt'

#%% Attempt to load assets and verify if they're a species asset or not
valid_assets = set()
num_assets = 0

start_time1 = process_time()
start_time2 = perf_counter()

for assetname in loader.find_assetnames('.*', '/Game'):
    num_assets += 1
    mem = loader._load_raw_asset(assetname)
    if b'ShooterCharacterMovement' in mem.obj and \
       not b'OnlyCollideWithStationary' in mem.obj and \
       not b'PawnMesh1P' in mem.obj:
        valid_assets.add(assetname)

end_time1 = process_time()
end_time2 = perf_counter()

print(f'process_time: {end_time1 - start_time1} seconds')
print(f'perf_counter: {end_time2 - start_time2} seconds')
print(len(valid_assets))
print(num_assets)

with open('output/text_files/' + output_file, 'w') as outfile:
    outfile.writelines(asset + '\n' for asset in sorted(valid_assets))

#%% Compare differences from the search
mainfile = 'output.txt'
compfile = output_file

with open('output/text_files/' + mainfile) as f1:
    with open('output/text_files/' + compfile) as f2:
        difference = sorted(set(f1.readlines()) - set(f2.readlines()))

print(difference)

#%% Check "undesired" assets against known good assets

desired_assets = [
    '/Game/Mods/Primal_Fear/Aberration/Dinos/ChupaCabra/ALPHA_ChupaCabra_Character_BP',
    '/Game/Aberration/Dinos/Nameless/Xenomorph_Character_BP_Female',
    '/Game/Aberration/Dinos/Nameless/Xenomorph_Character_BP',
    '/Game/Mods/ClassicFlyers/Dinos/Wyvern/Wyvern_Character_BP_Poison',
    '/Game/Mods/SpeedyFlyers/Dinos/Wyvern/Wyvern_Character_BP_Base',
    '/Game/PrimalEarth/Dinos/Microraptor/Microraptor_Character_BP',
]

undesired_assets = ['/Game/Mods/AE/Dinos/Dino_Character_BP_AE']
bad_assets = ['/Game/Mods/AE/Dinos/Dino_Character_BP_AE']

names_in_asset = set()
for asset in undesired_assets:
    names = set(str(name) for name in loader.partially_load_asset(asset).names)
    if not names_in_asset:
        names_in_asset = names  # if not names_in_asset else names_in_asset - names
    else:
        names_in_asset &= names

for asset in desired_assets:
    names_in_asset -= set(str(name) for name in loader.partially_load_asset(asset).names)

print(sorted(names_in_asset))

#%%
