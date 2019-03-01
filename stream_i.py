#%% Setup
from stream import *
import uasset
import loader

assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Dodo'
filename = loader.convert_asset_name_to_path(assetname)


#%% Load and decode
mem = loader.load_raw_asset_from_file(filename)
stream = MemoryStream(mem, 0, len(mem))
asset = UAsset(stream)
asset.deserialise()

#%%
hex(asset.package_flags)


#%%
