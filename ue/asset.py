import weakref
from typing import *

from .base import UEBase
from .coretypes import *
from .properties import Guid, PropertyTable, StringProperty
from .stream import MemoryStream
from .utils import get_clean_name, get_clean_namespaced_name

dbg_getName = 0


class UAsset(UEBase):
    display_fields = ('tag', 'legacy_ver', 'ue_ver', 'file_ver', 'licensee_ver', 'custom_versions', 'header_size', 'package_group',
                      'package_flags', 'names_chunk', 'exports_chunk', 'imports_chunk', 'depends_offset', 'string_assets',
                      'thumbnail_offset', 'guid')

    def __init__(self, stream):
        # Bit of a hack because we are the root of the tree
        self.asset = self
        self.loader: Optional['AssetLoader'] = None
        self.assetname: Optional[str] = None
        self.name: Optional[str] = None
        self.default_export: Optional['ExportTableItem'] = None
        self.default_class: Optional['ExportTableItem'] = None
        super().__init__(self, stream)

    def _deserialise(self):
        # Header top
        self._newField('tag', self.stream.readUInt32())
        self._newField('legacy_ver', self.stream.readInt32())
        self._newField('ue_ver', self.stream.readInt32())
        self._newField('file_ver', self.stream.readUInt32())
        self._newField('licensee_ver', self.stream.readUInt32())
        self._newField('custom_versions', self.stream.readUInt32())
        self._newField('header_size', self.stream.readUInt32())
        self._newField('package_group', StringProperty(self))
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
        self._newField('names', self._parseTable(self.names_chunk, StringProperty))
        self._newField('imports', self._parseTable(self.imports_chunk, ImportTableItem))
        self._newField('exports', self._parseTable(self.exports_chunk, ExportTableItem))

    def _link(self):
        '''Override linking phase to support hidden table fields.'''
        super()._link()
        self.names.link()
        self._findNoneName()
        self.imports.link()
        self.exports.link()

        for export in self.exports:
            export.deserialise_properties()

    def getName(self, index):
        '''Get a name for the given index.'''
        names = self.names
        assert index is not None
        assert type(index) == int
        assert names is not None

        extraIndex = index >> 32
        flags = index & 0xFFF00000
        clean_index = index & 0xFFFFF

        try:
            name = names[clean_index]
        except IndexError as err:
            raise IndexError(f'Invalid name index 0x{index:08X} ({index})') from err

        if (flags or extraIndex) and dbg_getName:
            print(f'getName for "{name}" ignoring flags 0x{flags:08X} and extraIndex 0x{extraIndex:08X}')

        # TODO: Do something with extraIndex?
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
        target = self.package_group.value
        for i, name in enumerate(self.names):
            if name.value == target:
                self.none_index = i
                return

        raise RuntimeError("Could not find None string entry")

    # def __eq__(self, other):
    #     return super().__eq__(other)

    # def __hash__(self):
    #     if 'guid' in self.field_values:
    #         return hash(self.field_values['guid'])

    #     if hashattr(self, 'assetname'):
    #         return hash(tuple(self.assetname, self.start_offset, self.end_offset))

    #     return super().__hash__()


class ImportTableItem(UEBase):
    package: NameIndex
    klass: NameIndex
    namespace: ObjectIndex
    name: NameIndex

    def _deserialise(self):
        self._newField('package', NameIndex(self))  # item type/class namespace
        self._newField('klass', NameIndex(self))  # item type/class
        self._newField('namespace', ObjectIndex(self))  # item namespace
        self._newField('name', NameIndex(self))  # item name

        # References to this item
        self.users = set()

    def register_user(self, user):
        self.users.add(user)

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text('Import(<cyclic>)')
        else:
            parent = get_clean_name(self.klass, 'class')
            pkg = get_clean_name(self.namespace)
            if pkg:
                p.text(f'Import({self.name} ({parent}) from {pkg})')
            else:
                p.text(f'Import({self.name} ({parent})')

    def __str__(self):
        parent = get_clean_name(self.klass, 'class')
        pkg = get_clean_name(self.namespace)
        if pkg:
            return f'{self.name} ({parent}) from {pkg}'
        else:
            return f'{self.name} ({parent})'


class ExportTableItem(UEBase):
    string_format = '{name} ({klass}) [{super}]'
    display_fields = ('name', 'namespace', 'klass', 'super')
    fullname: Optional[str] = None

    klass: ObjectIndex
    super: ObjectIndex
    namespace: ObjectIndex
    name: NameIndex
    properties: PropertyTable

    def _deserialise(self):
        self._newField('klass', ObjectIndex(self))  # item type/class
        self._newField('super', ObjectIndex(self))  # item type/class namespace
        self._newField('namespace', ObjectIndex(self))  # item namespace
        self._newField('name', NameIndex(self))  # item name
        self._newField('object_flags', self.stream.readUInt32())
        self._newField('serial_size', self.stream.readUInt32())
        self._newField('serial_offset', self.stream.readUInt32())
        self._newField('force_export', self.stream.readBool32())
        self._newField('not_for_client', self.stream.readBool32())
        self._newField('not_for_server', self.stream.readBool32())
        self._newField('guid', Guid(self))
        self._newField('package_flags', self.stream.readUInt32())
        self._newField('not_for_editor_game', self.stream.readBool32())

        # References to this item
        self.users = set()

    def _link(self):
        super()._link()
        if hasattr(self, 'asset') and hasattr(self.asset, 'assetname'):
            self.fullname = self.asset.assetname + '.' + str(self.name)

    def register_user(self, user):
        self.users.add(user)

    def deserialise_properties(self):
        if 'properties' in self.field_values:
            raise RuntimeError('Attempt to deserialise properties more than once')

        # We deferred deserialising the properties until all imports/exports were defined
        stream = MemoryStream(self.stream, self.serial_offset, self.serial_size)
        self._newField('properties', PropertyTable(self, weakref.proxy(stream)))
        self.properties.link()

    def __str__(self):
        parent = get_clean_name(self.super)
        cls = get_clean_name(self.klass, 'class')
        pkg = get_clean_name(self.namespace)

        result = str(self.name)
        if cls:
            result += f' [{cls}]'
        if parent:
            result += f' ({parent})'
        if pkg:
            result += ' from ' + pkg

        return result
