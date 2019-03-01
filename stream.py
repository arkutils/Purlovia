import struct
import uuid


class MemoryStream(object):
    def __init__(self, mem, offset, size):
        self.mem = mem
        self.offset = offset
        self.end = offset + size

    def readUInt32(self):
        return self._read('I')

    def readInt32(self):
        return self._read('i')

    def readUInt64(self):
        return self._read('Q')

    def readInt64(self):
        return self._read('q')

    def readBytes(self, count):
        if self.offset + count > self.end:
            raise EOFError("End of stream")
        raw_bytes = bytes(self.mem[self.offset:self.offset + count])
        self.offset += count
        return raw_bytes

    def readTerminatedString(self, size, encoding='utf8'):
        raw_bytes = self.readBytes(size)
        value = bytes(raw_bytes[:-1]).decode(encoding)
        return value

    def _read(self, fmt, count=None):
        size = struct.calcsize(fmt)
        if self.offset + size > self.end:
            raise EOFError("End of stream")

        if count == None or count == 1:
            value, = struct.unpack_from('<' + fmt, self.mem, self.offset)
            self.offset += size
            return value

        values = struct.unpack_from('<' + str(count) + fmt, self.mem, self.offset)
        self.offset += size
        return values


class UEThing(object):
    def __init__(self, ownerOrStream, asset=None):
        if isinstance(ownerOrStream, UEThing):
            self.stream = ownerOrStream.stream
            self.asset = ownerOrStream.asset
        else:
            self.stream = ownerOrStream
            self.asset = asset


class UAsset(UEThing):
    def deserialise(self):
        # Header top
        self.tag = self.stream.readUInt32()
        self.legacy_ver = self.stream.readInt32()
        self.ue_ver = self.stream.readInt32()
        self.file_ver = self.stream.readUInt32()
        self.licensee_ver = self.stream.readUInt32()
        self.engine = self.stream.readUInt32()
        self.header_size = self.stream.readUInt32()
        self.none_string = String(self).deserialise()
        self.package_flags = self.stream.readUInt32()

        # Offsets
        self.names_chunk = ChunkPtr(self).deserialise()
        self.exports_chunk = ChunkPtr(self).deserialise()
        self.imports_chunk = ChunkPtr(self).deserialise()
        self.depends_offset = self.stream.readUInt32()
        self.string_assets = ChunkPtr(self).deserialise()
        self.thumbnail_offset = self.stream.readUInt32()

        # Remaining header
        self.guid = Guid(self).deserialise()

        # Read the various tables
        #...

        return self

    def get_name(self, index):
        assert self.names_table
        return self.names_table[index]

    def get_object(self, index):
        if index < 0:
            assert self.imports_table
            return self.imports_table[-index - 1]
        elif index > 0:
            assert self.exports_table
            return self.exports_table[index - 1]

        return None


class String(UEThing):
    def deserialise(self):
        self.size = self.stream.readUInt32()
        self.value = self.stream.readTerminatedString(self.size)
        return self

    def __str__(self):
        return f'String(size={self.size}, value=\'{self.value}\')'


class ChunkPtr(UEThing):
    def deserialise(self):
        self.count = self.stream.readUInt32()
        self.offset = self.stream.readUInt32()
        return self

    def __str__(self):
        return f'{self.__class__.__name__}(count={self.count}, offset={self.offset})'


class Guid(UEThing):
    def deserialise(self):
        raw_bytes = self.stream.readBytes(16)
        self.value = uuid.UUID(bytes_le=raw_bytes)
        return self

    def __str__(self):
        return f'{self.__class__.__name__}(value={self.value})'


class ImportTableItem(UEThing):
    def deserialise(self):
        self.package = NameIndex(self).deserialise()
        self.klass = NameIndex(self).deserialise()
        self.outer_index = self.stream.readInt32()
        self.name = NameIndex(self).deserialise()
        return self

    def __str__(self):
        return f'{self.__class__.__name__}({self.package}::{self.name} ({self.klass})'


class NameIndex(UEThing):
    def deserialise(self):
        self.index = self.stream.readUInt64()
        self.value = self.asset.get_name(self.index)
        return self

    def __str__(self):
        return f'{self.__class__.__name__}(\'{self.value}\')'


class ObjectIndex(UEThing):
    def deserialise(self):
        self.index = self.stream.readUInt64()
        if self.index < 0:
            self.used_index = -self.index - 1
            self.value = self.asset.imports_table[self.used_index]
            self.kind = 'import'
        elif self.index > 0:
            self.used_index = self.index - 1
            self.value = self.asset.exports_table[self.used_index]
            self.kind = 'export'
        else:
            self.value = None
            self.kind = 'zero'
        return self

    def __str__(self):
        return f'{self.__class__.__name__}(\'{self.value.name}\' [{self.kind} {self.used_index}])'
