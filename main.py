from pprint import pprint

from uasset import *

# No content

if __name__ == '__main__':
    set_asset_path(r'.')
    assetname = r'Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP_Aberrant'
    # assetname = r'Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP'

    mem = load_asset(assetname)
    if mem[0] != 0xC1:  # This happens if you view the binary file in the editor!
        raise ValueError(f"File corrupt again :( Got 0x{mem[0]:02X} not 0xC1")

    asset = decode_asset(mem)

    # UAsset Summary
    if True:
        print(asset.summary)
        print(asset.tables)
        pprint("")

    # UAsset Names
    if False:
        pprint(asset.names)

    # UAsset Imports
    if False:
        # Each Import Entry is 28 bytes long
        o = asset.tables.imports_chunk.offset
        print(f'\nImports: offset=0x{o:08X}, count={asset.tables.imports_chunk.count}')
        for i in range(asset.tables.imports_chunk.count):
            item = ImportTableItem(mem, o)
            print(f'{i:2}: {item}')
            print(asset.names[item.package], end=',')
            print(asset.names[item.klass], end=',')
            print(asset.names[item.name])
            # display_mem(mem[o:o+28], as_hex_bytes, as_int32s)
            o += 28
        print(f'Chunk ends at offset: 0x{o:X}')

    # UAsset Exports
    if False:
        # Each Export Entry might be 68 bytes (comparing like words)
        o = asset.tables.exports_chunk.offset
        print(f'\nExports: offset=0x{o:08X}, count={asset.tables.exports_chunk.count}')
        for i in range(asset.tables.exports_chunk.count):
            item = ExportTableItem(mem, o)
            print(f'{i:2}: {item}')
            print(f'name={asset.names[item.name & 0xFFFF]}')  # Note: clearing flags
            # display_mem(mem[o:o+24], as_hex_bytes, as_int32s)
            # display_mem(mem[o+24:o+48], as_hex_bytes, as_int32s)
            # display_mem(mem[o+48:o+68], as_hex_bytes, as_int32s)
            o += 17 * 4
        print(f'Chunk ends at offset: 0x{o:X}')

    if False:
        # Take a look at the Depends chunk contents
        o = asset.depends_offset
        size = asset.header_size - o
        print(f'\nDepends: offset=0x{o:08X}, size={size}? (up to header_size)')
        # display_mem(mem[o:o+28], as_hex_bytes, as_int32s)
        # display_mem(mem[o+28:o+28*2], as_hex_bytes, as_int32s)
