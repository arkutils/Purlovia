import os
import struct
from types import SimpleNamespace as Bag

from hexutils import *
from ue_format import *

MAX_STRING_LEN = 2048
ENDIAN = '<'

asset_basepath = None


def set_asset_path(basepath):
    global asset_basepath
    asset_basepath = basepath


def convert_asset_name_to_path(name):
    parts = name.split('\\')
    if parts[0].lower() == 'game': parts[0] = 'Content'
    return os.path.join(asset_basepath, *parts) + '.uasset'


def load_asset(name):
    filename = convert_asset_name_to_path(name)
    print("Loading:", filename)
    mem = load_file_into_memory(filename)
    return mem


def parse_string(mem):
    size, = struct.unpack('<I', mem[:4])
    if size > MAX_STRING_LEN:
        raise ValueError("String length invalid")

    data = bytes(mem[4:4 + size - 1])
    string = data.decode('utf8')
    used = 4 + size
    return string, used


def get_chunk_count_and_offset(mem):
    count, offset = struct.unpack_from('<II', mem[:8])
    return Bag(count=count, offset=offset)


def parse_names_chunk(name_chunk, mem):
    namesArr = []
    offset = name_chunk.offset
    for i in range(name_chunk.count):
        string, used = parse_string(mem[offset:])
        offset += used
        namesArr.append(string)

    return namesArr


def parse_array(mem, offset, count, struct_type):
    result = []
    for i in range(count):
        item = struct_type(mem, offset)
        result.append(item)
        offset += len(item)

    return result


def decode_asset(mem):
    asset = Bag()
    asset.summary = HeaderTop(mem, 0x00)
    asset.tables = HeaderTables(mem, 0x25)
    asset.misc = HeaderBottom(mem, 0x45)

    asset.names = parse_names_chunk(asset.tables.names_chunk, mem)
    asset.imports = parse_array(mem, asset.tables.imports_chunk.offset, asset.tables.imports_chunk.count, ImportTableItem)
    asset.exports = parse_array(mem, asset.tables.exports_chunk.offset, asset.tables.exports_chunk.count, ExportTableItem)

    return asset


def parse_blueprint_export(mem, export, asset):
    o = export.serial_offset
    end = o + export.serial_size
    while o < end:
        field = BlueprintField(mem, o)
        value_offset = o + len(field)
        name = fetch_name(asset, field.name)
        type_name = fetch_name(asset, field.field_type)
        print(field)

        value, new_offset = parse_typed_field(mem, value_offset, type_name, field.size, asset)

        # print(f'@[0x{o:08X}:0x{new_offset-1:08X}] ({type_name}) {name} = [{field.index}:{value}]')
        yield Bag(name=name, index=field.index, value=value, type_name=type_name, offset=o, end=new_offset - 1)
        o = new_offset


def fetch_name(asset, index):
    if not type(index) == int:
        return None

    if index & 0xFFFF0000:
        print(f'Name ID with flags: 0x{index:08X} ({index})')
        index = index & 0xFFFF
    if index >= len(asset.names):
        return f'invalid_name_0x{index:X}'
        raise ValueError(f"Invalid name index 0x{index:08X} ({index})")

    return asset.names[index]


def fetch_object_name(asset, index):
    if not type(index) == int:
        return None

    try:
        if index < 0:
            index = -index - 1
            return asset.imports[index].name
        elif index > 0:
            index += 1
            return asset.exports[index].name
    except IndexError:
        return None

    return None


def parse_typed_field(mem, offset, type_name, size, asset):
    if type_name == 'IntProperty':
        return struct.unpack_from('<i', mem, offset)[0], offset + 4

    elif type_name == 'BoolProperty':
        return (struct.unpack_from('<I', mem, offset)[0] != 0), offset + 4

    elif type_name == 'FloatProperty':
        return struct.unpack_from('<f', mem, offset)[0], offset + 4

    elif type_name == 'ByteProperty' or type_name == 'EnumProperty':
        enum_name_index, value = struct.unpack_from('<QB', mem, offset)
        enum_name = fetch_name(asset, enum_name_index)
        if enum_name == 'None':
            return value, offset + 9
        else:
            return (value, enum_name), offset + 9

    elif type_name == 'StructProperty':
        print(f'Struct contents @ 0x{offset:08x}, count=0x{size:X}')

        # for m in range(offset, offset+size, 16):
        #     display_mem(mem[m:m+16], as_hex_bytes, as_int32s)

        # for o in range(offset, offset+size*8, 4):
        #     v, = struct.unpack_from('<i', mem, o)
        #     if v:
        #         print(f'0x{o:08X}: {v}, name={fetch_name(asset, v)}, object={fetch_name(asset, fetch_object_name(asset, v))}, float={reinterpret_as_float(v)}')
        #     else:
        #         print(f'0x{o:08X}: {v}')

        # parse_struct_field(mem, offset, size, asset)

        return '<struct>', offset + size
        # return bytes_to_hex(mem[offset:offset + size]), offset+size

    return bytes_to_hex(mem[offset:offset + size]), 999999999
    raise ValueError(f"Unsupported type '{type_name}''")


def parse_struct_field(mem, offset, size, asset):
    pass
