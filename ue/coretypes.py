from typing import List, Type, Union, Optional

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
)


class Table(UEBase):
    __slots__ = ('count', 'values', 'itemType')
    string_format = '{count} x {itemType.__name__}'
    skip_level_field = 'values'
    display_fields = ['itemType', 'count', 'values']

    count: int
    values: List[UEBase]
    itemType: Type[UEBase]

    def _deserialise(self, itemType: Type[UEBase], count: int):  # type: ignore
        assert count is not None
        assert issubclass(itemType, UEBase), f'Table item type must be UEBase'

        values = []
        for i in range(count):
            value = itemType(self).deserialise()
            value.table_index = i
            values.append(value)

        self._newField('itemType', itemType)
        self._newField('count', count)
        self._newField('values', values)

        return self

    def _link(self):
        '''Override link to link all table entries.'''
        super()._link()
        for value in self.values:
            if isinstance(value, UEBase):
                value.link()

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
    __slots__ = ('count', 'offset')
    count: int
    offset: int

    def _deserialise(self):
        self._newField('count', self.stream.readUInt32())
        self._newField('offset', self.stream.readUInt32())


class GenerationInfo(UEBase):
    __slots__ = ('export_count', 'name_count')
    export_count: int
    name_count: int

    def _deserialise(self):
        self._newField('export_count', self.stream.readUInt32())
        self._newField('name_count', self.stream.readUInt32())


class CompressedChunk(UEBase):
    __slots__ = ('uncompressed_offset', 'uncompressed_size', 'compressed_offset', 'compressed_offset')
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
    __slots__ = ('index', 'instance', 'value')
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
            self.value = f'{self.value}_{self.instance}'

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            cls = self.__class__.__name__
            if cycle:
                p.text(f'{cls}(<cyclic>)')
                return

            if 'value' in self.field_list:
                p.pretty(self.value)
            else:
                p.text(f'{cls}(index={self.index})')


class ObjectIndex(UEBase):
    __slots__ = ('index', 'used_index', 'kind', 'value')

    main_field = 'value'
    display_fields = ['index', 'value']
    skip_level_field = 'value'

    index: int
    used_index: int
    kind: str
    value: Optional[UEBase]

    def _deserialise(self):
        # Calculate the indexes but don't look up the actual import/export until the link phase
        self._newField('index', self.stream.readInt32())  # object indexes are 32-bit and signed
        if self.index < 0:
            used_index = -self.index - 1
            self.kind = 'import'
        elif self.index > 0:
            used_index = self.index - 1
            self.kind = 'export'
        else:
            used_index = 0
            self.kind = 'none'

        self._newField('used_index', used_index)

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
        if not self.value:
            return None

        return f'{self.value.namespace.value.name}.{str(self.value.name).rstrip("_C")}'

    # if support_pretty:

    #     def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
    #         if cycle:
    #             p.text(f'ObjectIndex(index={self.index})')
    #             return

    #         with p.group(4, self.__class__.__name__ + '(', ')'):
    #             p.text(str(self.index) + ", ")
    #             p.pretty(self.value)
