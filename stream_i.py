#%% Setup
from interactive_utils import *
from stream import MemoryStream
from ue.asset import UAsset
import uasset
import loader


assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Dodo'
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

#%% Demo display system
print('\nImport chunk offset/count:')
pprint(asset.imports_chunk)
print('\nExport chunk offset/count:')
pprint(asset.exports_chunk)

#%% More display demos
print('\nName 0:')
pprint(asset.getName(0))
print('\nImport 0:')
pprint(asset.imports[0])
print('\nExport 0:')
pprint(asset.exports[0])

#%%
print('\nExport 3 properties:')
e = asset.exports[3]
# e.deserialise_properties()
pprint(e.properties)

#%%
print('\nExport 4 properties:')
e = asset.exports[4]
# e.deserialise_properties()
pprint(e.properties)
