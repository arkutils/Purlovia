import os
import struct
from types import SimpleNamespace as Bag

from structex import Format, Type, Struct
from hexutils import *


MAX_STRING_LEN = 2048
ENDIAN = '<'

asset_basepath = None


class ImportTableItem(Struct):
  _format = ENDIAN
  package = Type.int64
  klass = Type.int64
  outer_index = Type.int32
  name = Type.int64

class Guid(Struct):
  _format = ENDIAN
  a = Type.uint32
  b = Type.uint32
  c = Type.uint32
  d = Type.uint32

class ExportTableItem(Struct):
  _format = ENDIAN
  klass = Type.int32
  super = Type.int32
  outer_index = Type.int32
  name = Type.int64
  object_flags = Type.uint32
  serial_size = Type.uint32
  serial_offset = Type.uint32
  force_export = Type.bool32
  not_for_client = Type.bool32
  not_for_server = Type.bool32
  guid = Type.Struct(Guid)
  package_flags = Type.uint32
  not_for_editor_game = Type.bool32
  
class HeaderPart1(Struct):
  _format = ENDIAN
  tag = Type.uint32
  legacy_ver = Type.int32
  ue_ver = Type.int32
  file_ver = Type.uint32
  licensee_ver = Type.uint32
  engine = Type.uint32
  header_size = Type.uint32

class ChunkPtr(Struct):
  _format = ENDIAN
  count = Type.uint32
  offset = Type.uint32

class HeaderTables(Struct):
  _format = ENDIAN
  package_flags = Type.uint32
  names_chunk = Type.Struct(ChunkPtr)
  exports_chunk = Type.Struct(ChunkPtr)
  imports_chunk = Type.Struct(ChunkPtr)
  depends_offset = Type.uint32
  

def set_asset_path(basepath):
  global asset_basepath
  asset_basepath = basepath

def convert_asset_name_to_path(name):
  parts = name.split('\\')
  if parts[0].lower() == 'game': parts[0] = 'Content'
  return os.path.join(asset_basepath, *parts) + '.uasset'

def load_asset(name):
  filename = convert_asset_name_to_path(name)
  print("Loading:",filename)
  mem = load_file_into_memory(filename)
  return mem

def load_file_into_memory(filename):
  with open(filename, 'rb') as f:
    data = f.read()
    mem = memoryview(data)
    return mem

def parse_string(mem):
  size, = struct.unpack('<I', mem[:4])
  if size > MAX_STRING_LEN:
    raise ValueError("String length invalid")

  data = bytes(mem[4:4+size-1])
  string = data.decode('utf8')
  used = 4 + size
  return string, used

def get_chunk_count_and_offset(mem):
  count, offset = struct.unpack_from('<II', mem[:8])
  return Bag(count=count, offset=offset)

def decode_header(mem):
  asset = Bag()
  asset.tag, = struct.unpack_from('<I', mem, 0x00)
  asset.legacy_ver, = struct.unpack_from('<i', mem, 0x04)
  asset.file_ver, = struct.unpack_from('<I', mem, 0x0C)
  asset.licensee_ver, = struct.unpack_from('<I', mem, 0x10)
  asset.engine, = struct.unpack_from('<I', mem, 0x14)
  asset.header_size, = struct.unpack_from('<I', mem, 0x18)
  asset.package_flags, = struct.unpack_from('<I', mem, 0x25)
  asset.chunks = Bag()
  asset.chunks.names = get_chunk_count_and_offset(mem[0x29:])
  asset.chunks.exports = get_chunk_count_and_offset(mem[0x31:])
  asset.chunks.imports = get_chunk_count_and_offset(mem[0x39:])
  asset.depends_offset, = struct.unpack_from('<I', mem, 0x41)
  asset.guid = Bag()
  asset.guid.a, = struct.unpack_from('<I', mem, 0x51)
  asset.guid.b, = struct.unpack_from('<I', mem, 0x55)
  asset.guid.c, = struct.unpack_from('<I', mem, 0x59)
  asset.guid.d, = struct.unpack_from('<I', mem, 0x5D)
  asset.bulk_data, = struct.unpack_from('<I', mem, 0x9B)
  return asset
 
def parse_names_chunk(name_chunk, mem):
  namesArr = []
  offset = name_chunk.offset
  for i in range(name_chunk.count):
    string, used = parse_string(mem[offset:])
    offset += used
    namesArr.append(string)
    
  return namesArr

def decode_asset(mem):
  asset = decode_header(mem)
  asset.names = parse_names_chunk(asset.chunks.names, mem)

  return asset

def display_summary(asset):
  print(f'Tag - {asset.tag}')
  print(f'Legacy Ver. - {asset.legacy_ver}')
  print(f'File Ver. - {asset.file_ver}')
  print(f'Licensee Ver. - {asset.licensee_ver}')
  print(f'Engine - {asset.engine}')
  print()
  print(f'Header Size - {asset.header_size}')
  print(f'Package Flags - {asset.package_flags}')
  print()
  print(f'Name Count - {asset.chunks.names.count}')
  print(f'Name Offset - 0x{asset.chunks.names.offset:08X}')
  print(f'Import Count - {asset.chunks.imports.count}')
  print(f'Import Offset - 0x{asset.chunks.imports.offset:08X}')
  print(f'Export Count - {asset.chunks.exports.count}')
  print(f'Export Offset - 0x{asset.chunks.exports.offset:08X}')
  print(f'Depends Offset - 0x{asset.depends_offset:08X}')
  print()
  print(f'GUID A - {asset.guid.a}')
  print(f'GUID B - {asset.guid.b}')
  print(f'GUID C - {asset.guid.c}')
  print(f'GUID D - {asset.guid.d}')
  print()
  print(f'Bulk Data Offset - 0x{asset.bulk_data:08X}')

