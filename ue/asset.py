from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, Optional, Set

from utils.log import get_logger

from .base import UEBase
from .context import INCLUDE_METADATA, get_ctx
from .coretypes import ChunkPtr, CompressedChunk, GenerationInfo, NameIndex, ObjectIndex, Table
from .properties import Box, CustomVersion, EngineVersion, Guid, PropertyTable, StringProperty, AFTER_PROPERTY_TABLE_TYPES
from .stream import MemoryStream
from .utils import get_clean_name

if TYPE_CHECKING:
    from .loader import AssetLoader

if INCLUDE_METADATA:
    try:
        from IPython.lib.pretty import PrettyPrinter  # type: ignore  # noqa: F401
        support_pretty = True
    except ImportError:
        support_pretty = False
else:
    support_pretty = False

dbg_getName = 0

__all__ = [
    'UAsset',
    'ImportTableItem',
    'ExportTableItem',
]

logger = get_logger(__name__)


class UAsset(UEBase):
    display_fields = ('tag', 'legacy_ver', 'ue_ver', 'file_ver', 'licensee_ver', 'custom_versions', 'header_size',
                      'package_group', 'package_flags', 'names_chunk', 'exports_chunk', 'imports_chunk', 'depends_offset',
                      'string_assets', 'thumbnail_offset', 'guid')

    none_index: int

    def __init__(self, stream):
        # Bit of a hack because we are the root of the tree
        self.asset = self
        self.loader: Optional[AssetLoader] = None
        self.assetname: Optional[str] = None
        self.name: Optional[str] = None
        self.file_ext: Optional[str] = None
        self.default_export: Optional['ExportTableItem'] = None
        self.default_class: Optional['ExportTableItem'] = None
        self.has_properties = False
        self.has_bulk_data = False
        super().__init__(self, stream)

    def _deserialise(self):  # pylint: disable=arguments-differ
        # ctx = get_ctx()  # not yet required

        # Header top
        self._newField('tag', self.stream.readUInt32())
        self._newField('legacy_ver', self.stream.readInt32())
        self._newField('ue_ver', self.stream.readInt32())
        self._newField('file_ver', self.stream.readUInt32())
        self._newField('licensee_ver', self.stream.readUInt32())
        self._newField('custom_versions', Table(self).deserialise(CustomVersion, self.stream.readUInt32()))
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
        self._newField('generations', Table(self).deserialise(GenerationInfo, self.stream.readUInt32()))
        self._newField('engine_version_saved', EngineVersion(self))
        self._newField('compression_flags', self.stream.readUInt32())
        self._newField('compressed_chunks', Table(self).deserialise(CompressedChunk, self.stream.readUInt32()))
        self._newField('package_source', self.stream.readUInt32())
        if self.licensee_ver >= 10:
            # This field isn't present in some older ARK mods
            self._newField('unknown_field', self.stream.readUInt64())
        self._newField('packages_to_cook', Table(self).deserialise(StringProperty, self.stream.readUInt32()))
        if self.legacy_ver > -7:
            # Legacy field that is not used anymore
            self._newField('texture_allocations', self.stream.readInt32())
        self._newField('asset_registry_data_offset', self.stream.readUInt32())
        self._newField('bulk_data_start_offset', self.stream.readUInt64())
        self._newField('world_tile_info_data_offset', self.stream.readUInt64())

        # Read the various chunk table contents
        # These tables are not included in the field list so they're not included in pretty printing
        # TODO: Include chunk ends by using other chunk start locations
        self._newField('names', self._parseTable(self.names_chunk, StringProperty))
        self._newField('imports', self._parseTable(self.imports_chunk, ImportTableItem))
        self._newField('exports', self._parseTable(self.exports_chunk, ExportTableItem))

        if self.world_tile_info_data_offset != 0:
            tile_info_stream = MemoryStream(self.stream, self.world_tile_info_data_offset)
            self._newField('tile_info', WorldTileInfo(self, tile_info_stream))

    def _link(self):
        '''Override linking phase to support hidden table fields.'''
        super()._link()
        self.names.link()
        self._findNoneName()
        self.imports.link()
        self.exports.link()

        ctx = get_ctx()

        if ctx.bulk_data:
            # bulk_chunk = namedtuple('FakeChunkPtr', ['offset', 'count'])(self.bulk_data_start_offset, self.bulk_length)
            # self._newField('bulk', self._parseTable(bulk_chunk, PropertyTable))
            self.has_bulk_data = True

        if ctx.properties:
            for export in self.exports:
                export.deserialise_properties()
            self.has_properties = True

    def is_context_satisfied(self, ctx):
        # Check that each of the context parameters is satisfied
        if not self.is_linked and ctx.link:
            return False
        if not self.has_properties and ctx.properties:
            return False
        if not self.has_bulk_data and ctx.bulk_data:
            return False

        return True

    def getName(self, index):
        '''Get a name for the given index.'''
        names = self.names
        assert index is not None
        assert isinstance(index, int)
        assert names is not None

        extraIndex = index >> 32
        flags = index & 0xFFF00000
        clean_index = index & 0xFFFFF

        try:
            name = names[clean_index]
        except IndexError as err:
            raise IndexError(f'Invalid name index 0x{index:08X} ({index})') from err

        if (flags or extraIndex) and dbg_getName:
            logger.warning('getName for "%s" ignoring flags 0x%08X and extraIndex 0x%08X', name, flags, extraIndex)

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

    def format_for_json(self):
        return dict(
            file=self.assetname + self.file_ext,
            legacy_ver=self.legacy_ver,
            ue_ver=self.ue_ver,
            file_ver=self.file_ver,
            licensee_ver=self.licensee_ver,
            custom_versions=self.custom_versions,
            package_group=self.package_group,
            package_flags=self.package_flags,
            engine_version_saved=self.engine_version_saved,
            names=self.names,
            exports=self.exports,
            imports=self.imports,
        )

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
    users: Set[UEBase]

    def _deserialise(self):  # pylint: disable=arguments-differ
        self._newField('package', NameIndex(self))  # item type/class namespace
        self._newField('klass', NameIndex(self))  # item type/class
        self._newField('namespace', ObjectIndex(self))  # item namespace
        self._newField('name', NameIndex(self))  # item name

        if INCLUDE_METADATA:
            # References to this item
            self.users = set()

    def register_user(self, user):
        if INCLUDE_METADATA:
            self.users.add(user)

    if support_pretty and INCLUDE_METADATA:

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

    @property
    def fullname(self) -> str:
        if self.namespace:
            return str(self.namespace.value.name) + '.' + str(self.name)
        return str(self.name)

    def format_for_json(self):
        return self.fullname

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
    users: Set[UEBase]

    def _deserialise(self):  # pylint: disable=arguments-differ
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

        if INCLUDE_METADATA:
            # References to this item
            self.users = set()

    def _link(self):
        super()._link()
        if hasattr(self, 'asset') and hasattr(self.asset, 'assetname'):
            self.fullname = self.asset.assetname + '.' + str(self.name)

    def register_user(self, user):
        if INCLUDE_METADATA:
            self.users.add(user)

    def deserialise_properties(self):
        if 'properties' in self.field_values:
            raise RuntimeError('Attempt to deserialise properties more than once')

        # We deferred deserialising the properties until all imports/exports were defined
        stream = MemoryStream(self.stream, self.serial_offset, self.serial_size)
        self._newField('properties', PropertyTable(self, weakref.proxy(stream)))
        self.properties.link()

        # Read data that some types have, located after the property table
        if self.klass.value:
            stream.offset += 4  # skip the remaining bytes of the PropertyTable marker

            type_cls = AFTER_PROPERTY_TABLE_TYPES.get(str(self.klass.value.name), None)
            if type_cls:
                extended_object = type_cls(self, weakref.proxy(stream))
                self._newField('extended_data', extended_object.deserialise(self.properties))

    def format_for_json(self):
        return dict(
            klass=self.klass,
            super=self.super,
            namespace=self.namespace,
            name=self.name,
            object_flags=self.object_flags,
            package_flags=self.package_flags,
            force_export=self.force_export,
            not_for_client=self.not_for_client,
            not_for_server=self.not_for_server,
            not_for_editor_game=self.not_for_editor_game,
            properties=self.properties,
        )

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


class WorldTileInfo(UEBase):
    display_fields = ('layer_name', 'bounds')
    fullname: Optional[str] = None

    unknown_field1: int
    bounds: Box
    layer_name: StringProperty
    unknown_field2: int
    unknown_field3: int
    unknown_field4: int
    streaming_distance: int
    distance_streaming_enabled: bool

    def _deserialise(self):  # pylint: disable=arguments-differ
        self._newField('unknown_field1', self.stream.readUInt64())
        self._newField('bounds', Box(self))
        self._newField('layer_name', StringProperty(self))
        self._newField('unknown_field2', self.stream.readUInt32())
        self._newField('unknown_field3', self.stream.readUInt32())
        self._newField('unknown_field4', self.stream.readUInt32())
        self._newField('streaming_distance', self.stream.readInt32())
        self._newField('distance_streaming_enabled', self.stream.readBool8())

    def __str__(self):
        return f'{self.layer_name} ({self.bounds})'
