import struct

__all__ = ('MemoryStream', )


class MemoryStream:
    mem: memoryview
    offset: int
    size: int
    end: int

    def __init__(self, memOrStream, offset=None, size=None):
        if isinstance(memOrStream, MemoryStream):
            self.mem = memOrStream.mem
            self.offset = memOrStream.offset if offset is None else offset
            self.size = memOrStream.size if size is None else size
            self.end = self.offset + self.size
        elif isinstance(memOrStream, (memoryview, bytes)):
            self.mem = memOrStream
            self.offset = 0 if offset is None else offset
            self.size = len(memOrStream) if size is None else size
            self.end = self.offset + self.size
        else:
            raise TypeError(f'Invalid item passed to MemoryStream constructor (a {type(memOrStream)})')

    def __len__(self):
        return self.size

    def readInt8(self) -> int:
        return self._read('b')

    def readUInt8(self) -> int:
        return self._read('B')

    def readBool8(self) -> bool:
        return bool(self._read('B'))

    def readBool32(self) -> bool:
        return bool(self._read('I'))

    def readUInt16(self) -> int:
        return self._read('H')

    def readInt16(self) -> int:
        return self._read('h')

    def readUInt32(self) -> int:
        return self._read('I')

    def readInt32(self) -> int:
        return self._read('i')

    def readUInt64(self) -> int:
        return self._read('Q')

    def readInt64(self) -> int:
        return self._read('q')

    def readFloat(self) -> float:
        return self._read('f')

    def readDouble(self) -> float:
        return self._read('d')

    def readBytes(self, count: int) -> bytes:
        if self.offset + count > self.end:
            raise EOFError("End of stream")
        raw_bytes = bytes(self.mem[self.offset:self.offset + count])
        self.offset += count
        return raw_bytes

    def readTerminatedString(self, size: int, encoding='utf8'):
        raw_bytes = self.readBytes(size)
        value = bytes(raw_bytes[:-1]).decode(encoding)
        return value

    def readTerminatedWideString(self, size: int):
        raw_bytes = self.readBytes(size * 2)
        value = bytes(raw_bytes[:-2]).decode('utf-16-le')
        return value

    def _read(self, fmt, count: int = None):
        size = struct.calcsize(fmt)
        if self.offset + size > self.end:
            raise EOFError("End of stream at offset " + str(self.offset))

        if count is None or count == 1:
            value, = struct.unpack_from('<' + fmt, self.mem, self.offset)
            self.offset += size
            return value

        values = struct.unpack_from('<' + str(count) + fmt, self.mem, self.offset)
        self.offset += size
        return values
