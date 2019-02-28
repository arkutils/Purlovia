#%% Setup
from pprint import pprint
import hexutils, uasset, loader

# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP'
# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Argent'
# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Dodo'
# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Rex'
# assetname = r'Game\Extinction\CoreBlueprints\DinoCharacterStatusComponent_BP_Gacha'
# assetname = r'Game\Extinction\CoreBlueprints\DinoCharacterStatusComponent_BP_Owl'

# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_FlyerRide'

# assetname = r'Game\PrimalEarth\Dinos\Argentavis\Argent_Character_BP'
# assetname = r'Game\PrimalEarth\Dinos\Argentavis\Argentavis'
# assetname = r'Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP'
assetname = r'Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP_Aberrant'
# assetname = r'Game\PrimalEarth\Dinos\Rex\Rex_Character_BP'
# assetname = r'Game\Extinction\Dinos\Gacha\Gacha_Character_BP'
# assetname = r'Game\Extinction\Dinos\Owl\Owl_Character_BP'
# assetname = r'Game\\ScorchedEarth\Dinos\Wyvern\DinoCharacterStatusComponent_BP_Wyvern'
# assetname = r'Game\\ScorchedEarth\Dinos\Wyvern\Wyvern_Character_BP_Base'
# assetname = r'Game\\ScorchedEarth\Dinos\Wyvern\Wyvern_Character_BP_Fire'

# assetname = "Game\ScorchedEarth\Dinos\Wyvern\DinoCharacterStatusComponent_BP_MegaWyvern"

#%% Load and decode
mem = loader.load_raw_asset(assetname)
asset = uasset.decode_asset(mem)
print("Decode complete")

#%% UAsset Summary
print(asset.summary)
print(asset.tables)
print(asset.misc)

#%% Show names
print('\nNames:')
for i, name in enumerate(asset.names):
    print(f'{i:>4}(0x{i:02X}): {name}')

#%% Show imports
print(f'\nImports: offset=0x{asset.tables.imports_chunk.offset:08X}, count={asset.tables.imports_chunk.count}')
for i, item in enumerate(asset.imports):
    print(f'{i:2}(0x{i:02X}): {item}')
    # print(f'{i:2}(0x{i:02X}):')
    print(f'    name={uasset.fetch_name(asset, item.name)}')
    print(f'    class={uasset.fetch_name(asset, item.klass)}')
    print(f'    package={uasset.fetch_name(asset, item.package)}')

#%% Show exports
print(f'\nExports: offset=0x{asset.tables.exports_chunk.offset:08X}, count={asset.tables.exports_chunk.count}')
for i, item in enumerate(asset.exports):
    print(f'{i:2}(0x{i:02X}): {item}')
    # print(f'{i:2}(0x{i:02X}):')
    print(f'    name={uasset.fetch_name(asset, item.name)}')
    print(f'    class={uasset.fetch_object_name(asset, item.klass)} ({uasset.explain_obj_id(item.klass)})')
    print(f'    super={uasset.fetch_object_name(asset, item.super)} ({uasset.explain_obj_id(item.super)})')
    props = uasset.parse_blueprint_export(mem, item, asset)
    # props = asset.raw_props
    for entry in props:
        # print(f'{entry.name}[{entry.index}] = ({entry.type_name}) {entry.value}')
        print(f'@[0x{entry.offset:08X}:0x{entry.end:08X}] ({entry.type_name}) {entry.name}[{entry.index}] = {entry.value}')
        # print(f'  {entry.type_name:<15} | {entry.name}[{entry.index}] = {entry.value}')

#%% Explore depends section - content unknown
# o = asset.tables.depends_offset
# size = asset.summary.header_size - o
# print(f'\nDepends: offset=0x{o:08X}, size={size}? (up to header_size)')
# display_mem(mem[o:o+28], as_hex_bytes, as_int32s)
# display_mem(mem[o+28:o+28*2], as_hex_bytes, as_int32s)

#%% Peek into the values pointed to by exports
# e = asset.exports[3]
# print(e)
# print(f'name={fetch_name(asset, e.name)}')
# for o in range(e.serial_offset, e.serial_offset+e.serial_size, 28):
#     display_mem(mem[o:o+28], as_hex_bytes, as_floats)

#%% Attempt to parse the blueprint export
# e = asset.exports[1]
# # e = uasset.find_default_property_export(asset)
# print(f'\nExport properties: offset=0x{e.serial_offset:08X}, size=0x{e.serial_size:X} ({e.serial_size})')
# print('\n  ' + str(e) + '\n')
# print(f'  name  = {uasset.fetch_name(asset, e.name)}')
# print(f'  class = {uasset.fetch_object_name(asset, e.klass)}')
# print(f'  super = {uasset.fetch_object_name(asset, e.super)}')
# print()
# props = uasset.parse_blueprint_export(mem, e, asset)
# # props = asset.raw_props
# for entry in props:
#     # print(f'{entry.name}[{entry.index}] = ({entry.type_name}) {entry.value}')
#     print(f'@[0x{entry.offset:08X}:0x{entry.end:08X}] ({entry.type_name}) {entry.name}[{entry.index}] = {entry.value}')
#     # print(f'  {entry.type_name:<15} | {entry.name}[{entry.index}] = {entry.value}')

#%% Show the clean properties only
print(f'Clean properties:')
pprint(asset.props, width=250)
# for prop in asset.props:
#     print(f'{prop.name}[{prop.index}] = {prop.value}')

#%% Work out dependencies
parent_name = uasset.find_external_source_of_export(asset, asset.default_export)
print('\nParent asset: ' + parent_name)

#%% See if dependency loading works
# loader.ensure_dependencies(asset)

##%% Pretty Import/Export w/ Class name
# Example Printout:
# -----------------
# {asset_path}\{package_name}
#
# Imports:
#    ({import.class_name}) {import.package_name} || {import.name}
#
# Exports:
#    ({import.class_name}) {import.super_name} || {import.name}
#       ({prop.type_name}) {prop.name}[{prop.index}] = {prop.value}
#
# print(loader.clean_asset_name(assetname))
#
# #%% Pretty Print [Names]
# print("\nNames:")
# for name in asset.names:
#     print(f'   {name}')
#
# #%% Pretty Print [Imports]
# print("\nImports:")
# for entry in asset.imports:
#     # if uasset.fetch_object_name(asset, entry.klass) == "BlueprintGeneratedClass":
#     print(f'  ({uasset.fetch_name(asset, entry.klass)})', end = " ")
#     print(f'{uasset.fetch_name(asset, entry.package)} ||', end = " ")
#     print(f'{uasset.fetch_name(asset, entry.name)}')
#
# #%% Pretty Print [Exports (Properties)]
# print("\nExports:")
# for entry in asset.exports:
#     # if uasset.fetch_object_name(asset, entry.klass) == "BlueprintGeneratedClass":
#     print(f'  ({uasset.fetch_object_name(asset, entry.klass)})', end = " ")
#     if entry.super_index:
#         print(f'{uasset.fetch_name(asset, entry.name)} || ', end = " ")
#     print(f'{uasset.fetch_name(asset, entry.name)}')
#     # for prop in entry.prop:
#     #     print(f'      ({prop.type_name})', end = " ")
#     #     print(f'{prop.name}[{prop.index}]', end = " ")
#     #     if prop.value.count > 1:
#     #         for i, value in enumerate(prop.value):
#     #             print(f'                    [{i}] {value})
#     #     else:
#     #         print(f'{prop.value}')
