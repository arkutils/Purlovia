import sys
import uuid
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
            # try:
            value = self._parseField()
            # except Exception as ex:
            #     print("!*!*!*!*!*! EXCEPTION DURING PARSING !*!*!*!*!*!")
            #     pprint(ex)
            #     values.append(f'<failed to read entry at 0x{start_offset:08X}>')
            #     break
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
        propertyType = None
        try:
            propertyType = getPropertyType(self.header.type.value.value)
        except TypeError:
            print(f'Encountered unknown property type {self.header.type.value.value}... attempting to skip')

        if propertyType:
            self._newField('value', propertyType(self), self.header.size)
            self.value.link()  # safe to link as all imports/exports are completed
        else:
            self._newField('value', f'<unsupported type {str(self.header.type)}>')
            self.stream.offset += self.header.size

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Clean property format: Name[index] = (type) value'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            p.text(str(self.header.name) + '[')
            p.pretty(self.header.index)
            p.text(f'] = ')
            # p.text(f'{str(self.header.type)}) ')
            p.pretty(self.value)


class FloatProperty(UEBase):
    display_fields = ['textual']

    def _deserialise(self, size):
        # Read once as a float
        saved_offset = self.stream.offset
        self._newField('value', self.stream.readFloat())

        # Read again as plain bytes for exact exporting
        self.stream.offset = saved_offset
        self._newField('bytes', self.stream.readBytes(4))

        # Make a rounded textual version with (inexact) if required
        value = self.value
        rounded = round(value, 6)
        inexact = abs(value - rounded) >= sys.float_info.epsilon
        text = str(rounded)
        if inexact:
            text += ' (inexact)'
        self._newField('textual', text)


class IntProperty(UEBase):
    def _deserialise(self, size):
        self._newField('value', self.stream.readInt32())


class BoolProperty(UEBase):
    display_fields = ['value']

    def _deserialise(self, size):
        self._newField('value', self.stream.readBool8())


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

            p.text(self.__class__.__name__ + '(')
            if self.enum.index == self.asset.none_index:
                p.pretty(self.value)
            else:
                p.pretty(self.enum)
                p.text(', ')
                p.pretty(self.value)
            p.text(')')


class ObjectProperty(UEBase):
    def _deserialise(self, size):
        self._newField('value', ObjectIndex(self))


class NameProperty(UEBase):
    display_fields = ['value']

    def _deserialise(self, size):
        self._newField('value', NameIndex(self))

    def __str__(self):
        return str(self.value)


class StringProperty(UEBase):
    display_fields = ['value']

    def _deserialise(self, *args):
        self._newField('size', self.stream.readInt32())
        if self.size >= 0:
            self._newField('value', self.stream.readTerminatedString(self.size))
        else:
            self.size = -self.size
            self._newField('value', self.stream.readTerminatedWideString(self.size))

    def __str__(self):
        return str(self.value)

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            if cycle:
                p.text(f'{self.__class__.__name__}(<cyclic>)')
                return

            p.text(self.value)


class Guid(UEBase):
    display_fields = ['value']

    def _deserialise(self, *args):
        raw_bytes = self.stream.readBytes(16)
        self._newField('value', str(uuid.UUID(bytes_le=raw_bytes)))


class StructProperty(UEBase):
    def _deserialise(self, size):
        values = []
        self._newField('values', values)

        end = self.stream.offset + size
        while self.stream.offset < end - 4:
            type_name = NameIndex(self)
            type_name.deserialise()
            if type_name == self.asset.none_index:
                break

            type_name.link()
            try:
                propertyType = getPropertyType(str(type_name))
            except TypeError:
                # Abort unhandled types
                self.values.append(f'<unhandled type {type_name}>')
                break

            value = propertyType(self)
            value.deserialise()
            values.append(value)

        # Safely skip to the end of the struct regardless of whether we could decode it
        self.stream.offset = self.start_offset + 8 + size

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Cleanly wrappable display in Jupyter.'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            with p.group(4, self.__class__.__name__ + '(', ')'):
                for idx, value in enumerate(self.values):
                    if idx:
                        p.text(',')
                        p.breakable()
                    # p.text(f'0x{idx:04X} ({idx:<4}): ')
                    p.pretty(value)


class ArrayProperty(UEBase):
    def _deserialise(self, size):
        assert size > 4, "Array size is required"

        self._newField('field_type', NameIndex(self))
        self.field_type.link()
        saved_offset = self.stream.offset
        self._newField('count', self.stream.readUInt32())

        propertyType = None
        try:
            propertyType = getPropertyType(str(self.field_type))
        except TypeError:
            pass

        if propertyType == None or str(self.field_type) == 'StructProperty':
            self.stream.offset = saved_offset + size
            self._newField('value', f'<unsupported field type {self.field_type}')
            return

        values = []
        self._newField('values', values)

        field_size = (size-4) // self.count
        end = saved_offset + size
        # print("First field:", self.stream.offset)
        # print("Field size:", field_size, self.field_type)
        # print("End:", end)
        while self.stream.offset < end:
            # print("Field:", self.stream.offset)
            value = propertyType(self)
            value.deserialise(field_size)
            value.link()
            values.append(value)

        self.stream.offset = saved_offset + size

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Cleanly wrappable display in Jupyter.'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            with p.group(4, self.__class__.__name__ + '(', ')'):
                p.text(f'count={self.count}')
                if 'values' in self.field_values:
                    for idx, value in enumerate(self.values):
                        p.text(',')
                        p.breakable()
                        p.text(f'0x{idx:04X} ({idx:<4}): ')
                        p.pretty(value)
                else:
                    p.text(', ' + str(self.value))


TYPE_MAP = {
    'FloatProperty': FloatProperty,
    'BoolProperty': BoolProperty,
    'ByteProperty': ByteProperty,
    'IntProperty': IntProperty,
    'Guid': Guid,
    'NameProperty': NameProperty,
    'StrProperty': StringProperty,
    'StringProperty': StringProperty,
    'ObjectProperty': ObjectProperty,
    'StructProperty': StructProperty,
    'ArrayProperty': ArrayProperty,
}


def getPropertyType(typeName: str):
    try:
        return TYPE_MAP[typeName]
    except KeyError as err:
        raise TypeError(f'Unsupported property type "{typeName}"') from err


# Types to export from this module
__all__ = tuple(TYPE_MAP.keys()) + (
    'getPropertyType',
    'PropertyTable',
)
