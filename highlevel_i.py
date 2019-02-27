#%% Setup
import os, glob
from pprint import pprint
import loader
loader.wipe_assets()

species_list = (
    ('PrimalEarth', (
        'Argent',
        'Dodo',
        'Rex',
        'Baryonyx',
        'Tuso',
    )),
    ('Extinction', (
        'Owl',
        'Gacha',
    )),
)

#%% Load base properties
for mod, species_names in species_list:
    for species in species_names:
        asset_name = f'Game\{mod}\CoreBlueprints\DinoCharacterStatusComponent_BP_{species}'
        asset = loader.get_asset(asset_name)
        loader.ensure_dependencies(asset)  # should load all parents recursively, stopping at CoreUObject

#%% Get Argent properties
species_asset = loader.get_asset('Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Argent')
print('\nArgent properties:')
pprint(species_asset.props)

#%% Get species properties
flyer_asset = loader.get_asset('Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_FlyerRide')
print('\nFlyerRide properties:')
pprint(flyer_asset.props)

#%% Try merge species properties merged into all baseclasses
combined_props = loader.merged_properties(species_asset)
print('\nFully combined properties (including base):')
pprint(combined_props, width=250)
