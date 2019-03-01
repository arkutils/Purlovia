from stream import MemoryStream
from .base import UEBase
from ue.coretypes import *


class UAsset(UEBase):
    def deserialise(self):
        self.asset = self

        # Header top
        self._newField('tag', self.stream.readUInt32())
        self._newField('legacy_ver', self.stream.readInt32())
        self._newField('ue_ver', self.stream.readInt32())
        self._newField('file_ver', self.stream.readUInt32())
        self._newField('licensee_ver', self.stream.readUInt32())
        self._newField('engine', self.stream.readUInt32())
        self._newField('header_size', self.stream.readUInt32())
        self._newField('none_string', String(self).deserialise())
        self._newField('package_flags', self.stream.readUInt32())

        # Chunk offsets
        self._newField('names_chunk', ChunkPtr(self).deserialise())
        self._newField('exports_chunk', ChunkPtr(self).deserialise())
        self._newField('imports_chunk', ChunkPtr(self).deserialise())
        self._newField('depends_offset', self.stream.readUInt32())
        self._newField('string_assets', ChunkPtr(self).deserialise())
        self._newField('thumbnail_offset', self.stream.readUInt32())

        # Remaining header
        self._newField('guid', Guid(self).deserialise())

        # Read the various chunk table contents
        # These tables are not included in the field list so they're not included in pretty printing
        # TODO: Include chunk ends by using other chunks start locations
        self.names = self._parseTable(self.names_chunk, String)
        self.imports = self._parseTable(self.imports_chunk, ImportTableItem)
        self.exports = self._parseTable(self.exports_chunk, ExportTableItem)

        return self

    def link(self):
        '''Override linking phase to support hidden table fields.'''
        super().link()
        self.names.link()
        self.imports.link()
        self.exports.link()

    def getName(self, index):
        assert self.names
        return self.names[index]

    def getObject(self, index):
        if index < 0:
            assert self.imports
            return self.imports[-index - 1]
        elif index > 0:
            assert self.exports
            return self.exports[index - 1]

        return None

    def _parseTable(self, chunk, itemType):
        stream = MemoryStream(self.stream, chunk.offset)
        table = Table(stream, self.asset).deserialise(itemType, chunk.count)
        return table


class ImportTableItem(UEBase):
    def deserialise(self):
        self._newField('package', NameIndex(self).deserialise())
        self._newField('klass', NameIndex(self).deserialise())
        self._newField('outer_index', self.stream.readInt32())
        self._newField('name', NameIndex(self).deserialise())
        return self

    def __str__(self):
        return f'Import({self.package}::{self.name} ({self.klass})'

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text('Import(...)')
        else:
            p.text(f'Import({self.package.value}::{self.name.value} ({self.klass.value})')


class ExportTableItem(UEBase):
    display_fields = ('name', 'klass', 'super', 'outer_index')

    def deserialise(self):
        self._newField('klass', ObjectIndex(self).deserialise())
        self._newField('super', ObjectIndex(self).deserialise())
        self._newField('outer_index', self.stream.readInt32())  # also an object index?
        self._newField('name', NameIndex(self).deserialise())
        self._newField('object_flags', self.stream.readUInt32())
        self._newField('serial_size', self.stream.readUInt32())
        self._newField('serial_offset', self.stream.readUInt32())
        self._newField('force_export', self.stream.readBool32())
        self._newField('not_for_clien', self.stream.readBool32())
        self._newField('not_for_server', self.stream.readBool32())
        self._newField('guid', Guid(self).deserialise())
        self._newField('package_flags', self.stream.readUInt32())
        self._newField('not_for_editor_game', self.stream.readBool32())
        return self

    def link(self):
        super().link()

    def __str__(self):
        return f'{self.__class__.__name__}({self.package}::{self.name} (a {self.klass})'
