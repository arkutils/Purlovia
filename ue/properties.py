import sys
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
            except Exception as ex:
                print("!*!*!*!*!*! EXCEPTION DURING PARSING !*!*!*!*!*!")
                pprint(ex)
                values.append(f'<failed to read entry at 0x{start_offset:08X}>')
                break
            if value is None:
                break
            values.append(value)

        self._newField('count', len(values))

    def _link(self):
        '''Override link to link all table entries.'''
        super()._link()
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

        # Reset back to the saved offset and read the whole property
        self.stream.offset = saved_offset
        value = Property(self).deserialise()
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


class PropertyHeader(UEBase):
    display_fields = ['name', 'index']

    def _deserialise(self):
        self._newField('name', NameIndex(self))
        self._newField('type', NameIndex(self))
        self._newField('size', self.stream.readUInt32())
        self._newField('index', self.stream.readUInt32())


class Property(UEBase):
    def _deserialise(self):
        self._newField('header', PropertyHeader(self))
        self.header.link()  # safe to link as all imports/exports are completed
        propertyType = getPropertyType(self.header.type.value.value)
        self._newField('value', propertyType(self), self.header.size)
        self.value.link()  # safe to link as all imports/exports are completed

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Clean property format: Name[index] = (type) value'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            p.pretty(self.header.name)
            p.text('[')
            p.pretty(self.header.index)
            p.text('] = (')
            p.pretty(self.header.type)
            p.text(') ')
            # p.breakable()
            p.pretty(self.value)


class FloatProperty(UEBase):
    def _deserialise(self, size):
        # Read once as a float
        saved_offset = self.stream.offset
        self._newField('value', self.stream.readFloat())

        # Read again as plain bytes for exact exporting
        self.stream.offset = saved_offset
        self._newField('bytes', self.stream.readBytes(4))

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Rounded float with inexact notifier.'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            value = self.value
            rounded = round(value, 6)
            inexact = abs(value - rounded) >= sys.float_info.epsilon
            p.text(str(rounded))
            if inexact:
                p.text(' (inexact)')


class IntProperty(UEBase):
    def _deserialise(self, size):
        self._newField('value', self.stream.readInt32())

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Cleanly wrappable display in Jupyter.'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            p.pretty(self.value)


class BoolProperty(UEBase):
    def _deserialise(self, size):
        self._newField('value', self.stream.readBool8())

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Cleanly wrappable display in Jupyter.'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            p.pretty(self.value)


class ByteProperty(UEBase):  # With optional enum type
    def _deserialise(self, size):
        self._newField('enum', NameIndex(self))
        if size == 1:
            self._newField('value', self.stream.readUInt8())
        elif size == 8:
            self._newField('value', NameIndex(self))
        else:
            self._newField('value', '<skipped bytes>')
            self.stream.offset += size

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Cleanly wrappable display in Jupyter.'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            if self.enum.index == self.asset.none_index:
                p.pretty(self.value)
            else:
                p.text('(')
                p.pretty(self.enum)
                p.text(') ')
                p.pretty(self.value)


class ObjectProperty(UEBase):
    def _deserialise(self, size):
        self._newField('value', ObjectIndex(self))


class StructProperty(UEBase):
    def _deserialise(self, size):
        self._newField('field_type', NameIndex(self))
        self.stream.offset += size
        self._newField('value', '<skipped struct>')


class ArrayProperty(UEBase):
    def _deserialise(self, size):
        self._newField('field_type', NameIndex(self))
        self.stream.offset += size + 8
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
