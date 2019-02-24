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
    asset.summary = HeaderPart1(mem, 0x00)
    asset.tables = HeaderTables(mem, 0x25)

    asset.names = parse_names_chunk(asset.tables.names_chunk, mem)
    asset.imports = parse_array(mem, asset.tables.imports_chunk.offset, asset.tables.imports_chunk.count, ImportTableItem)
    asset.exports = parse_array(mem, asset.tables.exports_chunk.offset, asset.tables.exports_chunk.count, ExportTableItem)

    return asset
