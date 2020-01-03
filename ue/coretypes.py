from typing import List, Type, Union

from .base import UEBase
from .context import INCLUDE_METADATA

try:
    from IPython.lib.pretty import PrettyPrinter  # type: ignore
    support_pretty = True
except ImportError:
    support_pretty = False

__all__ = (
    'Table',
    'ChunkPtr',
    'NameIndex',
    'ObjectIndex',
    'GenerationInfo',
    'CompressedChunk',
    'BulkDataHeader',
    'StripDataFlags',
)


class Table(UEBase):
    string_format = '{count} x {itemType.__name__}'
    skip_level_field = 'values'
    display_fields = ['itemType', 'count', 'values']

    count: int
    values: List[UEBase]
    itemType: Type[UEBase]

    def _deserialise(self, itemType: Type[UEBase], count: int):  # type: ignore # pylint: disable=arguments-differ
        assert count is not None
        assert issubclass(itemType, UEBase), 'Table item type must be UEBase'

        values = []
        for _ in range(count):
            value = itemType(self).deserialise()
            values.append(value)

        self._newField('itemType', itemType)
        self._newField('count', count)
        self._newField('values', values)

        return self

    def _link(self):
        '''Override link to link all table entries.'''
        for value in self.values:
            if isinstance(value, UEBase):
                value.link()

    def format_for_json(self):
        return self.values

    def __getitem__(self, index: int):
        '''Provide access using the index via the table[index] syntax.'''
        if self.values is None:
            raise RuntimeError('Table not deserialised before read')

        return self.values[index]

    def __len__(self):
        return len(self.values)

    if support_pretty and INCLUDE_METADATA:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Cleanly wrappable display in Jupyter.'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            with p.group(4, self.__class__.__name__ + '(', ')'):
                p.text(f'count={self.count}, itemType={self.itemType.__name__}')
                for idx, value in enumerate(self.values):
                    p.text(',')
                    p.breakable()
                    p.text(f'0x{idx:04X} ({idx:<4}): ')
                    p.pretty(value)


class ChunkPtr(UEBase):
    count: int
    offset: int

    def _deserialise(self):
        self._newField('count', self.stream.readUInt32())
        self._newField('offset', self.stream.readUInt32())


class GenerationInfo(UEBase):
    export_count: int
    name_count: int

    def _deserialise(self):
        self._newField('export_count', self.stream.readUInt32())
        self._newField('name_count', self.stream.readUInt32())


class CompressedChunk(UEBase):
    uncompressed_offset: int
    uncompressed_size: int
    compressed_offset: int
    compressed_size: int

    def _deserialise(self):
        self._newField('uncompressed_offset', self.stream.readUInt32())
        self._newField('uncompressed_size', self.stream.readUInt32())
        self._newField('compressed_offset', self.stream.readUInt32())
        self._newField('compressed_size', self.stream.readUInt32())


class NameIndex(UEBase):
    main_field = 'value'

    index: int
    instance: int
    value: Union[UEBase, str]  # can't specify StringProperty

    def _deserialise(self):
        # Get the index but don't look up the actual value until the link phase
        self._newField('index', self.stream.readUInt32())
        self._newField('instance', self.stream.readUInt32())

    def _link(self):
        self._newField('value', self.asset.getName(self.index))
        if INCLUDE_METADATA:
            self.value.register_user(self.parent or self)
        if self.instance:
            self.field_values['value'] = f'{self.value}_{self.instance - 1}'

    def format_for_json(self):
        return str(self)

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            cls = self.__class__.__name__
            if cycle:
                p.text(f'{cls}(<cyclic>)')
                return

            if 'value' in self.field_values:
                p.pretty(self.value)
            else:
                p.text(f'{cls}(index={self.index})')


class ObjectIndex(UEBase):
    main_field = 'value'
    display_fields = ['index', 'value']
    skip_level_field = 'value'

    index: int
    used_index: int
    kind: str

    def _deserialise(self):
        # Calculate the indexes but don't look up the actual import/export until the link phase
        self._newField('index', self.stream.readInt32())  # object indexes are 32-bit and signed
        if self.index < 0:
            self.used_index = -self.index - 1
            self.kind = 'import'
        elif self.index > 0:
            self.used_index = self.index - 1
            self.kind = 'export'
        else:
            self.used_index = 0
            self.kind = 'none'

        self._newField('used_index', self.used_index)

    def _link(self):
        # Look up the import/export in the asset tables now they're completed
        if self.kind == 'import':
            source = self.asset.imports
        elif self.kind == 'export':
            source = self.asset.exports
        else:
            source = None
            value = None

        if source:
            if self.used_index >= len(source):
                value = 'out_of_bounds_index_' + str(self.used_index)
            else:
                value = source[self.used_index]
                value.register_user(self)

        self._newField('value', value)

    def format_for_json(self):
        if self.kind == 'import':
            return self.value
        else:
            return self.value and self.value.fullname

    def __bool__(self):
        return self.index != 0

    # if support_pretty:

    #     def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
    #         if cycle:
    #             p.text(f'ObjectIndex(index={self.index})')
    #             return

    #         with p.group(4, self.__class__.__name__ + '(', ')'):
    #             p.text(str(self.index) + ", ")
    #             p.pretty(self.value)


class StripDataFlags(UEBase):
    display_fields = ('global_flags', 'class_flags')

    def _deserialise(self):
        self._newField('global_flags', self.stream.readInt8())
        self._newField('class_flags', self.stream.readInt8())

    def __str__(self):
        return f'StripDataFlags ({self.global_flags}, {self.class_flags})'


class BulkDataHeader(UEBase):
    display_fields = ()

    flags: int
    is_payload_at_the_end: bool  # 0x0001
    is_zlib_compressed: bool  # 0x0002
    is_unused: bool  # 0x0020
    is_payload_inline: bool  # 0x0040
    length: int
    size_on_disk: int
    offset_in_file: int

    def _deserialise(self):
        # Bulk Data Header
        self._newField('flags', self.stream.readInt32())
        self._newField('is_payload_at_the_end', self.flags & 0x0001 != 0)
        self._newField('is_zlib_compressed', self.flags & 0x0002 != 0)
        self._newField('is_unused', self.flags & 0x0020 != 0)
        self._newField('is_payload_inline', self.flags & 0x0040 != 0)
        self._newField('length', self.stream.readInt32())
        self._newField('size_on_disk', self.stream.readInt32())
        self._newField('offset_in_file', self.stream.readUInt64())

        if self.is_payload_at_the_end:
            self.offset_in_file += self.asset.bulk_data_start_offset

    def __str__(self):
        return f'{self.length} bytes @ {self.offset_in_file}'
