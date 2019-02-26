#%% Setup
from pprint import pprint
from hexutils import *
from uasset import *
set_asset_path(r'.')

# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP'
assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Argent'
# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Dodo'
# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Rex'
# assetname = r'Game\Extinction\CoreBlueprints\DinoCharacterStatusComponent_BP_Gacha'
# assetname = r'Game\Extinction\CoreBlueprints\DinoCharacterStatusComponent_BP_Owl'
# assetname = r'Game\PrimalEarth\Dinos\Argentavis\Argent_Character_BP'
# assetname = r'Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP'
# assetname = r'Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP_Aberrant'
# assetname = r'Game\PrimalEarth\Dinos\Rex\Rex_Character_BP'
# assetname = r'Game\Extinction\Dinos\Gacha\Gacha_Character_BP'
# assetname = r'Game\Extinction\Dinos\Owl\Owl_Character_BP'

#%% Load asset into memory
mem = load_asset(assetname)
if mem[0] != 0xC1:  # This happens if you view the binary file in the editor!
    raise ValueError(f"File corrupt again :( Got 0x{mem[0]:02X} not 0xC1")

#%% Decode
asset = decode_asset(mem)
print("Decode complete")

#%% UAsset Summary
print(asset.summary)
print(asset.tables)
print(asset.misc)

#%% Show names
print('\nNames:')
for i,name in enumerate(asset.names):
    print(f'{i:>4}(0x{i:02X}): {name}')

#%% Show imports
print(f'\nImports: offset=0x{asset.tables.imports_chunk.offset:08X}, count={asset.tables.imports_chunk.count}')
for i, item in enumerate(asset.imports):
    print(f'{i:2}(0x{i:02X}): {item}')
    print(fetch_name(asset, item.package), end=',')
    print(fetch_name(asset, item.klass), end=',')
    print(fetch_name(asset, item.name))

#%% Show exports
print(f'\nExports: offset=0x{asset.tables.exports_chunk.offset:08X}, count={asset.tables.exports_chunk.count}')
for i, item in enumerate(asset.exports):
    print(f'{i:2}(0x{i:02X}): {item}')
    klass_name = fetch_object_name(asset, item.klass)
    print(f'    name={fetch_name(asset, item.name)} ({fetch_name(asset, klass_name)})')

#%% Explore depends section - content unknown
o = asset.tables.depends_offset
size = asset.summary.header_size - o
print(f'\nDepends: offset=0x{o:08X}, size={size}? (up to header_size)')
display_mem(mem[o:o+28], as_hex_bytes, as_int32s)
display_mem(mem[o+28:o+28*2], as_hex_bytes, as_int32s)


#%% Peek into the values pointed to by exports
# e = asset.exports[3]
# print(e)
# print(f'name={fetch_name(asset, e.name)}')
# for o in range(e.serial_offset, e.serial_offset+e.serial_size, 28):
#     display_mem(mem[o:o+28], as_hex_bytes, as_floats)


#%% Attempt to parse the blueprint export
# e = asset.exports[3]
e = find_default_property_export(asset)
print(f'\nExport properties: offset=0x{e.serial_offset:08X}, size=0x{e.serial_size:X} ({e.serial_size})')
print('\n  '+str(e)+'\n')
print(f'  name  = {fetch_name(asset, e.name)}')
print(f'  class = {fetch_name(asset, fetch_object_name(asset, e.klass))}')
print(f'  super = {fetch_name(asset, fetch_object_name(asset, e.super))}')
print()
# props = parse_blueprint_export(mem, e, asset)
props = asset.raw_props
for entry in props:
    # print(f'{entry.name}[{entry.index}] = ({entry.type_name}) {entry.value}')
    print(f'@[0x{entry.offset:08X}:0x{entry.end:08X}] ({entry.type_name}) {entry.name}[{entry.index}] = {entry.value}')
    # print(f'  {entry.type_name:<15} | {entry.name}[{entry.index}] = {entry.value}')


#%% Show the clean properties only
print(f'Clean properties:')
pprint(asset.props)
# for prop in asset.props:
#     print(f'{prop.name}[{prop.index}] = {prop.value}')

#%%
