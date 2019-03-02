#%% Setup
from interactive_utils import *
from stream import MemoryStream
from ue.asset import UAsset
import uasset
import loader

assetname = r'Game\PrimalEarth\CoreBlueprints\Dino_Character_BP'
filename = loader.convert_asset_name_to_path(assetname)

#%% Load and decode
mem = loader.load_raw_asset_from_file(filename)
stream = MemoryStream(mem, 0, len(mem))
asset = UAsset(stream)
print('Deserialising...')
asset.deserialise()
print('Linking...')
asset.link()
print('Decoding complete.')

#%% More display demos
# print('\nNames:')
# pprint(asset.names)
# print('\nImports:')
# pprint(asset.imports)
# print('\nExports:')
# pprint(asset.exports)

#%%
for i,export in enumerate(asset.exports):
    print(f'\nExport {i}:')
    pprint(export)
    pprint(export.properties)

#%% Try to discover inheritnce
# Find a Default__ export
# for export in asset.exports:
#     if not str(export.name).startswith('Default__'):
#         continue

#     pprint(export.name)
