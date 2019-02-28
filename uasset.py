import os
import struct
from copy import deepcopy
from collections import defaultdict
from types import SimpleNamespace as Bag

from dict_utils import merge

import ue_format
import hexutils

MAX_STRING_LEN = 2048


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
    asset.summary = ue_format.HeaderTop(mem, 0x00)
    asset.tables = ue_format.HeaderTables(mem, 0x25)
    asset.misc = ue_format.HeaderBottom(mem, 0x45)

    asset.names = parse_names_chunk(asset.tables.names_chunk, mem)
    asset.imports = parse_array(mem, asset.tables.imports_chunk.offset, asset.tables.imports_chunk.count,
                                ue_format.ImportTableItem)
    asset.exports = parse_array(mem, asset.tables.exports_chunk.offset, asset.tables.exports_chunk.count,
                                ue_format.ExportTableItem)

    prop_export = find_default_property_export(asset)
    if prop_export:
        asset.raw_props = list(parse_blueprint_export(mem, prop_export, asset))
        asset.props = get_clean_properties(asset)

    return asset


def parse_blueprint_export(mem, export, asset):
    o = export.serial_offset
    end = o + export.serial_size
    while o < end:
        field = ue_format.BlueprintField(mem, o)
        value_offset = o + len(field)
        name = fetch_name(asset, field.name)
        type_name = fetch_name(asset, field.field_type)
        if name == 'None':
            return

        # print(field)

        value, new_offset = parse_typed_field(mem, value_offset, type_name, field.size, asset)

        # print(f'@[0x{o:08X}:0x{new_offset-1:08X}] ({type_name}) {name} = [{field.index}:{value}]')
        yield Bag(name=name, index=field.index, value=value, type_name=type_name, offset=o, end=new_offset - 1)
        o = new_offset


def fetch_name(asset, index):
    if not type(index) == int:
        return None

    extra = index >> 32
    flags = (index >> 24) & 0xFF  # we don't use these yet
    index = index & 0xFFFFFF
    if index >= len(asset.names):
        return f'invalid_name_0x{index:X}'
        raise ValueError(f"Invalid name index 0x{index:08X} ({index})")

    name = asset.names[index]
    if extra:
        name = name + '_' + str(extra - 1)

    return name


def fetch_object_name(asset, index):
    obj = fetch_object(asset, index)
    if obj:
        return fetch_name(asset, obj.name)
    else:
        return None


def fetch_object(asset, index):
    if not type(index) == int:
        return None

    try:
        if index < 0:
            return asset.imports[-index - 1]
        elif index > 0:
            return asset.exports[index - 1]
    except IndexError:
        return None

    return None


def explain_obj_id(index):
    if index == 0:
        return '0'
    elif index < 0:
        return f'import {-index - 1}'
    else:
        return f'export {index - 1}'


def parse_typed_field(mem, offset, type_name, size, asset):
    if type_name == 'IntProperty':
        return struct.unpack_from('<i', mem, offset)[0], offset + 4

    elif type_name == 'BoolProperty':
        return (struct.unpack_from('<B', mem, offset)[0] != 0), offset + 1

    elif type_name == 'FloatProperty':
        return struct.unpack_from('<f', mem, offset)[0], offset + 4

    elif type_name == 'ByteProperty' or type_name == 'EnumProperty':
        if size == 1:
            enum_name_index, value = struct.unpack_from('<QB', mem, offset)
            enum_name = fetch_name(asset, enum_name_index)
            if enum_name == 'None':
                return value, offset + size + 8
            else:
                return (value, enum_name), offset + size + 8
        elif size == 8:
            enum_name_index, value_name_index = struct.unpack_from('<QQ', mem, offset)
            enum_name = fetch_name(asset, enum_name_index)
            value_name = fetch_name(asset, value_name_index)
            return value_name, offset + size + 8
        else:
            print(f"Unsupported ByteProperty size of {size}")
            return '<unsupported>', offset + size + 8  # a guess

    elif type_name == 'StructProperty':
        # print(f'Struct contents @ 0x{offset:08x}, count=0x{size:X}')

        # for m in range(offset, offset+size, 16):
        #     display_mem(mem[m:m+16], as_hex_bytes, as_int32s)

        # for o in range(offset, offset+size*8, 4):
        #     v, = struct.unpack_from('<i', mem, o)
        #     if v:
        #         print(f'0x{o:08X}: {v}, name={fetch_name(asset, v)}, object={fetch_name(asset, fetch_object_name(asset, v))}, float={reinterpret_as_float(v)}')
        #     else:
        #         print(f'0x{o:08X}: {v}')

        item = parse_struct_field(mem, offset, size, asset)
        return item, offset + size + 8
        
    # Probably should loop but don't have enough cases yet
    elif type_name == 'ArrayProperty':
        inner_type = fetch_name(asset, struct.unpack_from('Q', mem, offset)[0])
        size, value = struct.unpack_from('<Ii', mem, offset + 8)
        rtn_val = [inner_type, fetch_object_name(asset, value)]
        return rtn_val, offset + 16

    elif type_name == 'StrProperty':
        string, used = parse_string(mem[offset:])
        return string, offset + used

    elif type_name == 'ObjectProperty':
        obj_index, = struct.unpack_from('<I', mem, offset)
        return fetch_object_name(asset, obj_index), offset + size

    return hexutils.bytes_to_hex(mem[offset:offset + size]), 999999999
    raise ValueError(f"Unsupported type '{type_name}''")


def parse_struct_field(mem, offset, size, asset):
    item = ue_format.StructProperty(mem, offset)
    #print(f'{fetch_name(asset, item.owner_name_i)}({fetch_name(asset, item.item_name_i)}=({fetch_name(asset, item.type2_name_i)}) {item.value1}, ...)')
    return item


def find_default_property_export(asset):
    interesting_part = 'Default_'
    for export in asset.exports:
        name = fetch_name(asset, export.name)
        if name.startswith('Default_') and name.endswith('_C'):
            # print('Using export: ' + name)
            asset.default_export = export
            return export


def get_clean_properties(asset):
    tree = defaultdict(dict)
    for prop in asset.raw_props:
        if type(prop.value) in (float, int, str):
            value = prop.value
            if type(prop.value) == float:
                value = round(value, 6)
            tree[prop.name][prop.index] = value

    return dict(tree)


def merge_properties(base, extra):
    base_props = deepcopy(base.props)
    result = merge(base_props, extra.props)
    return result


def find_external_source_of_export(asset, export):
    imp = find_import_for_export(asset, export)
    return fetch_name(asset, imp.package)


def find_import_for_export(asset, obj):
    print('-----')
    print('object name =', fetch_name(asset, obj.name))
    if hasattr(obj, 'super'): print('object super =', fetch_object_name(asset, obj.super))
    if hasattr(obj, 'package'): print('object package =', fetch_name(asset, obj.package))

    if type(obj) == ue_format.ImportTableItem:
        print('object klass =', fetch_name(asset, obj.klass))
        return obj

    print('object klass =', fetch_object_name(asset, obj.klass))
    klass_name = fetch_object_name(asset, obj.klass)

    if klass_name and klass_name.startswith('Blueprint'):
        parent = fetch_object(asset, obj.super)
    else:
        parent = fetch_object(asset, obj.klass)

    print('parent =', parent)
    # if fetch_name(asset, parent.name).startswith('Blueprint'):
    #     print('...switched to super')
    #     parent = fetch_object(asset, obj.super)
    #     print('super name =',fetch_name(asset, parent.name))

    return find_import_for_export(asset, parent)
