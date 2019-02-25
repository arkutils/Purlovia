__test__ = False

#%% Setup
from pprint import pprint
from uasset import *
set_asset_path(r'.')
# assetname = r'Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP_Aberrant'
# assetname = r'Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP'
# assetname = r'Game\PrimalEarth\CoreBlueprints/DinoCharacterStatusComponent_BP_Dodo'
assetname = r'Game\PrimalEarth\CoreBlueprints/DinoCharacterStatusComponent_BP'

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
    print(f'{i:>4}: {name}')

#%% Show imports
print(f'\nImports: offset=0x{asset.tables.imports_chunk.offset:08X}, count={asset.tables.imports_chunk.count}')
for i, item in enumerate(asset.imports):
    print(f'{i:2}: {item}')
    print(asset.names[item.package], end=',')
    print(asset.names[item.klass], end=',')
    print(asset.names[item.name])

#%% Show exports
print(f'\nExports: offset=0x{asset.tables.exports_chunk.offset:08X}, count={asset.tables.exports_chunk.count}')
for i, item in enumerate(asset.exports):
    print(f'{i:2}: {item}')
    klass_index = item.klass
    if klass_index < 0:
        klass_index = -klass_index - 1
        klass_index = asset.imports[klass_index].name

    print(f'    name={asset.names[item.name & 0xFFFF]} ({asset.names[klass_index]})')

#%% Explore depends section - content unknown
o = asset.tables.depends_offset
size = asset.summary.header_size - o
print(f'\nDepends: offset=0x{o:08X}, size={size}? (up to header_size)')
display_mem(mem[o:o+28], as_hex_bytes, as_int32s)
display_mem(mem[o+28:o+28*2], as_hex_bytes, as_int32s)


#%% Peek into the values pointed to by exports
e = asset.exports[3]
print(e)
print(f'name={asset.names[e.name & 0xFFFF]}')
for o in range(e.serial_offset, e.serial_offset+e.serial_size, 28):
    display_mem(mem[o:o+28], as_hex_bytes, as_floats)


#%% Attempt to parse the blueprint export
e = asset.exports[3]
bp = parse_blueprint_export(mem, e, asset)
for entry in bp:
    pprint(f'@[0x{entry["offset"]:08X}:0x{entry["end"]:08X}] ({entry["type_name"]}) {entry["name"]} = [{entry["index"]}:{entry["value"]}]', width=150)
