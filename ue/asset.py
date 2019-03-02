from stream import MemoryStream
from .base import UEBase
from .coretypes import *
from .properties import PropertyTable


class UAsset(UEBase):
    def __init__(self, stream):
        # Bit of a hack because we are the root of the tree
        self.asset = self
        super().__init__(self, stream)

    def _deserialise(self):
        # Header top
        self._newField('tag', self.stream.readUInt32())
        self._newField('legacy_ver', self.stream.readInt32())
        self._newField('ue_ver', self.stream.readInt32())
        self._newField('file_ver', self.stream.readUInt32())
        self._newField('licensee_ver', self.stream.readUInt32())
        self._newField('engine', self.stream.readUInt32())
        self._newField('header_size', self.stream.readUInt32())
        self._newField('none_string', String(self))
        self._newField('package_flags', self.stream.readUInt32())

        # Chunk offsets
        self._newField('names_chunk', ChunkPtr(self))
        self._newField('exports_chunk', ChunkPtr(self))
        self._newField('imports_chunk', ChunkPtr(self))
        self._newField('depends_offset', self.stream.readUInt32())
        self._newField('string_assets', ChunkPtr(self))
        self._newField('thumbnail_offset', self.stream.readUInt32())

        # Remaining header
        self._newField('guid', Guid(self))

        # Read the various chunk table contents
        # These tables are not included in the field list so they're not included in pretty printing
        # TODO: Include chunk ends by using other chunk start locations
        self.names = self._parseTable(self.names_chunk, String)
        self.imports = self._parseTable(self.imports_chunk, ImportTableItem)
        self.exports = self._parseTable(self.exports_chunk, ExportTableItem)

    def _link(self):
        '''Override linking phase to support hidden table fields.'''
        super()._link()
        self.names.link()
        self._findNoneName()
        self.imports.link()
        self.exports.link()

    def getName(self, index):
        '''Get a name for the given index.'''
        names = self.names
        assert index is not None
        assert names is not None
        extraIndex = index >> 32
        flags = index & 0xFF000000
        index = index & 0xFFFFFF
        name = names[index]
        # TODO: Do something with extraIndex
        return name

    def getObject(self, index):
        '''Get an object for the given index (either an import or an export).'''
        assert index is not None
        if index < 0:
            assert self.imports
            return self.imports[-index - 1]
        elif index > 0:
            assert self.exports
            return self.exports[index - 1]

        return None

    def _parseTable(self, chunk, itemType):
        stream = MemoryStream(self.stream, chunk.offset)
        table = Table(self, stream).deserialise(itemType, chunk.count)
        return table

    def _findNoneName(self):
        target = self.none_string.value
        for i, name in enumerate(self.names):
            if name.value == target:
                self.none_index = i
                return

        raise RuntimeError("Could not find None string entry")


class ImportTableItem(UEBase):
    def _deserialise(self):
        self._newField('package', NameIndex(self))
        self._newField('klass', NameIndex(self))
        self._newField('outer_index', self.stream.readInt32())
        self._newField('name', NameIndex(self))

    def __str__(self):
        return f'Import({self.package}::{self.name} ({self.klass})'

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text('Import(<cyclic>)')
        else:
            p.text(f'Import({self.package.value}::{self.name.value} ({self.klass.value}))')


class ExportTableItem(UEBase):
    display_fields = ('name', 'klass', 'super', 'outer_index', 'serial_offset')

    def _deserialise(self):
        self._newField('klass', ObjectIndex(self))
        self._newField('super', ObjectIndex(self))
        self._newField('outer_index', self.stream.readInt32())
        self._newField('name', NameIndex(self))
        self._newField('object_flags', self.stream.readUInt32())
        self._newField('serial_size', self.stream.readUInt32())
        self._newField('serial_offset', self.stream.readUInt32())
        self._newField('force_export', self.stream.readBool32())
        self._newField('not_for_client', self.stream.readBool32())
        self._newField('not_for_server', self.stream.readBool32())
        self._newField('guid', Guid(self))
        self._newField('package_flags', self.stream.readUInt32())
        self._newField('not_for_editor_game', self.stream.readBool32())

    def _link(self):
        # We defered deserialising the properties until all imports/exports were defined
        stream = MemoryStream(self.stream, self.serial_offset, self.serial_size)
        self._newField('properties', PropertyTable(self, stream))

        # This link will also link all properties within
        super()._link()
