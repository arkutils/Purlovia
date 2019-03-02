from typing import Type

from stream import MemoryStream
from .base import UEBase
from .coretypes import *

try:
    from IPython.lib.pretty import PrettyPrinter, pprint
    support_pretty = True
except ImportError:
    support_pretty = False

from .base import UEBase


class PropertyTable(UEBase):
    display_fields = ['values']

    def _deserialise(self):
        values = []
        self._newField('values', values)

        while self.stream.offset < (self.stream.end - 8):
            start_offset = self.stream.offset
            try:
                value = self._parseField()
            except:
                values.append(f'<failed to read entry at 0x{start_offset:08X}>')
                break
            if value is None:
                break
            values.append(value)

        self._newField('count', len(values))

    def link(self):
        '''Override link to link all table entries.'''
        super().link()
        for value in self.values:
            if isinstance(value, UEBase):
                value.link()

    def _parseField(self):
        # Records the current offset
        saved_offset = self.stream.offset

        # Check for a None name here - that's the terminator
        name = NameIndex(self).deserialise()
        if name.index == self.asset.none_index:
            return None

        # Reset back to the saved offset and read just the property header
        self.stream.offset = saved_offset
        tmp_value = Property(self).deserialise()
        tmp_value.link()

        # Get the actual property type
        propertyType = getPropertyType(tmp_value.type.value.value)

        # Decode from the saved offset again, this time using the correct property type
        self.stream.offset = saved_offset
        value = propertyType(self).deserialise()
        value.link()

        return value

    def __getitem__(self, index: int):
        '''Provide access using the index via the table[index] syntax.'''
        if self.values is None:
            raise RuntimeError('PropertyTable not deserialised before read')

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
                p.text(f'count={self.count}')
                for idx, value in enumerate(self.values):
                    p.text(',')
                    p.breakable()
                    p.text(f'0x{idx:04X} ({idx:<4}): ')
                    p.pretty(value)


class Property(UEBase):
    display_fields = ['name', 'index', 'value']

    def _deserialise(self):
        self._newField('name', NameIndex(self))
        self._newField('type', NameIndex(self))
        self._newField('size', self.stream.readUInt32())
        self._newField('index', self.stream.readUInt32())

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Cleanly wrappable display in Jupyter.'''
            cls = self.__class__.__name__
            if cycle:
                p.text(cls + '(<cyclic>)')
                return

            p.pretty(self.name)
            p.text(f'[{self.index}] = ({cls}) ')
            with p.group(4):
                p.pretty(self.value)


class FloatProperty(Property):
    def _deserialise(self):
        super()._deserialise()
        self._newField('value', self.stream.readFloat())


class IntProperty(Property):
    def _deserialise(self):
        super()._deserialise()
        self._newField('value', self.stream.readInt32())


class BoolProperty(Property):
    def _deserialise(self):
        super()._deserialise()
        self._newField('value', self.stream.readBool8())


class ByteProperty(Property):  # With optional enum type
    def _deserialise(self):
        super()._deserialise()
        self._newField('enum', NameIndex(self))
        if self.size == 1:
            self._newField('value', self.stream.readUInt8())
        elif self.size == 8:
            self._newField('value', NameIndex(self))
        else:
            self._newField('value', '<skipped bytes>')
            self.stream.offset += size

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Cleanly wrappable display in Jupyter.'''
            cls = self.__class__.__name__
            if cycle:
                p.text(cls + '(<cyclic>)')
                return

            p.pretty(self.name)
            if self.enum.index == self.asset.none_index:
                p.text(f'[{self.index}] = ({cls}) ')
                p.pretty(self.value)
            else:
                p.text(f'[{self.index}] = ({cls}) (')
                p.pretty(self.enum)
                p.text(') ')
                p.pretty(self.value)


class ObjectProperty(Property):
    def _deserialise(self):
        super()._deserialise()
        self._newField('value', ObjectIndex(self))


class StructProperty(Property):
    display_fields = ['name', 'index', 'value', 'field_type']

    def _deserialise(self):
        super()._deserialise()
        self._newField('field_type', NameIndex(self))
        self.stream.offset += self.size
        self._newField('value', '<skipped struct>')


class ArrayProperty(Property):
    display_fields = ['name', 'index', 'value', 'field_type']

    def _deserialise(self):
        super()._deserialise()
        self._newField('field_type', NameIndex(self))
        self.stream.offset += self.size + 8
        self._newField('value', '<skipped array>')


TYPE_MAP = {
    'FloatProperty': FloatProperty,
    'BoolProperty': BoolProperty,
    'ByteProperty': ByteProperty,
    'IntProperty': IntProperty,
    'ObjectProperty': ObjectProperty,
    'StructProperty': StructProperty,
    'ArrayProperty': ArrayProperty,
}


def getPropertyType(typeName: str):
    try:
        return TYPE_MAP[typeName]
    except KeyError as err:
        raise TypeError(f'Unsupported property type "{typeName}"')


# Types to export from this module
__all__ = tuple(TYPE_MAP.keys()) + (
    'getPropertyType',
    'PropertyTable',
)
