#%% Run Me
import json
import os
from time import process_time, perf_counter
from automate.ark import ArkSteamManager, readModData

arkman = ArkSteamManager(skipInstall=True)
loader = arkman.createLoader()

#%% Gather all assets from all mods
assets_to_load = []
with open('asb_json/values.json') as json_file:
    data = json.load(json_file)
    for species in data['species']:
        assets_to_load.append(species['blueprintPath'].split('.')[0])
for r, d, f in os.walk('./output'):
    for file in f:
        with open(os.path.join(r, file)) as json_file:
            data = json.load(json_file)
            for species in data['species']:
                assets_to_load.append(species['blueprintPath'].split('.')[0])

print(len(assets_to_load))

#%% Extract Names from assets and compare them
real_names = {}
names = {}
first_run = True
skipped_count = 0
for asset in assets_to_load:
    names = set(str(name) for name in loader.partially_load_asset(asset).names)
    if first_run:
        first_run = False
        real_names = names
        print(real_names)
    else:
        initial_len = len(real_names)
        real_names = names & real_names
        if initial_len > len(real_names):
            print(f'Parsed {skipped_count} without removing any names')
            skipped_count = 0
            print(asset)
            print(f'Removed {initial_len - len(real_names)} names')
        else:
            skipped_count += 1

        # print(real_names)

print(f'Parsed {skipped_count} without removing any names')
print(real_names)

#%% Attempt to load assets and verify if they're a species asset or not
names = {}
valid_assets = set()
num_assets = 0

start_time1 = process_time()
start_time2 = perf_counter()
for assetname in loader.find_assetnames('.*', '/Game'):
    num_assets += 1
    names = set(str(name) for name in loader.partially_load_asset(assetname).names)
    if 'ShooterCharacterMovement' in names:
        valid_assets.add(assetname)
end_time1 = process_time()
end_time2 = perf_counter()

print(f'process_time: {end_time1 - start_time1} seconds')
print(f'perf_counter: {end_time2 - start_time2} seconds')
print(len(valid_assets))
print(num_assets)
