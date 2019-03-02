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

        while self.stream.offset < (self.stream.end - 8):
            value = self._parseField()
            if value is None:
                break
            values.append(value)

        self._newField('count', len(values))
        self._newField('values', values)

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
        name.link()
        if name.value.value == self.asset.none_string.value:
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
                p.text(self.__class__.__name__ + '(...)')
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


class ObjectProperty(Property):
    def _deserialise(self):
        super()._deserialise()
        self._newField('value', ObjectIndex(self))


class StructProperty(Property):
    display_fields = ['name', 'index', 'value', 'field_type']

    def _deserialise(self):
        super()._deserialise()
        self._newField('field_type', NameIndex(self))
        self.stream.offset += self.size + 8
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
