import uuid
from typing import Type

try:
    from IPython.lib.pretty import PrettyPrinter
    support_pretty = True
except ImportError:
    support_pretty = False

from .base import UEBase

__all__ = (
    'Table',
    'String',
    'ChunkPtr',
    'Guid',
    'NameIndex',
    'ObjectIndex',
)


class Table(UEBase):
    display_fields = ['itemType', 'count', 'values']

    def _deserialise(self, itemType: Type[UEBase], count: int):
        assert count is not None
        assert issubclass(itemType, UEBase), f'Table item type must be UEBase'

        values = []
        for i in range(count):
            value = itemType(self).deserialise()
            values.append(value)

        self._newField('itemType', itemType)
        self._newField('count', count)
        self._newField('values', values)
        return self

    def link(self):
        '''Override link to link all table entries.'''
        super().link()
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

    if support_pretty:

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


class String(UEBase):
    display_fields = ('value', )

    def _deserialise(self):
        self._newField('size', self.stream.readUInt32())
        self._newField('value', self.stream.readTerminatedString(self.size))

    def __str__(self):
        return f'{self.value}'

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            if cycle:
                p.text(f'String(<cyclic>)')
                return

            p.text(self.value)


class ChunkPtr(UEBase):
    def _deserialise(self):
        self._newField('count', self.stream.readUInt32())
        self._newField('offset', self.stream.readUInt32())


class Guid(UEBase):
    def _deserialise(self):
        raw_bytes = self.stream.readBytes(16)
        self._newField('value', uuid.UUID(bytes_le=raw_bytes))


class NameIndex(UEBase):
    def _deserialise(self):
        # Get the index but don't look up the actual value until the link phase
        self._newField('index', self.stream.readUInt64())

    def link(self):
        self._newField('value', self.asset.getName(self.index))

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
    def _deserialise(self):
        # Calculate the indexes but don't look up the actual import/export until the link phase
        self._newField('index', self.stream.readInt32())
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

    def link(self):
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

        self._newField('value', value)

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            if cycle:
                p.text(f'ObjectIndex(index={self.index})')
                return

            with p.group(4, self.__class__.__name__ + '(', ')'):
                p.text(str(self.index) + ",")
                p.breakable()
                p.pretty(self.value)
