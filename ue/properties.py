import sys
import math
import uuid
import struct
import logging
from typing import Type, Dict, List, Optional, Union
from collections import defaultdict

try:
    from IPython.lib.pretty import PrettyPrinter, pprint, pretty  # type: ignore
    support_pretty = True
except ImportError:
    support_pretty = False

from .stream import MemoryStream
from .base import UEBase
from .coretypes import *

dbg_structs = 0

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

PropDict = Dict[str, Dict[int, UEBase]]

NO_FALLBACK = object()


class PropertyTable(UEBase):
    string_format = '{count} entries'
    display_fields = ['values']
    skip_level_field = 'values'
    _as_dict: Optional[PropDict] = None

    values: List["Property"]

    def as_dict(self) -> PropDict:
        return self._as_dict or self._convert_to_dict()

    def get_property(self, name: str, index: int = 0, fallback=NO_FALLBACK) -> UEBase:
        value = self.as_dict()[name][index]

        if value is not None:
            return value

        if fallback is not NO_FALLBACK:
            return fallback

        raise KeyError(f"Property {name}[{index}] not found")

    def _convert_to_dict(self):
        result: PropDict = defaultdict(lambda: defaultdict(lambda: None))

        for prop in self.values:
            name = str(prop.header.name)
            idx = prop.header.index
            value = prop.value

            result[name][idx] = value

        self._as_dict = result
        return result

    def _deserialise(self):
        values = []
        self._newField('values', values)

        while self.stream.offset < (self.stream.end - 8):
            start_offset = self.stream.offset
            value = self._parseField()
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

    name: NameIndex
    type: NameIndex
    size: int
    index: int

    def _deserialise(self):
        self._newField('name', NameIndex(self))
        self._newField('type', NameIndex(self))
        self._newField('size', self.stream.readUInt32())
        self._newField('index', self.stream.readUInt32())


class Property(UEBase):
    string_format = '{header.name}[{header.index}] = {value}'

    header: PropertyHeader
    value: UEBase

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
    main_field = 'textual'
    display_fields = ['textual']

    value: float
    textual: str
    bytes: bytes
    rounded: str
    rounded_value: float

    def _deserialise(self, size=None):
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
        self._newField('rounded', text)
        self._newField('rounded_value', rounded)
        if inexact:
            text += ' (inexact)'
        self._newField('textual', text)


class DoubleProperty(UEBase):
    main_field = 'textual'
    display_fields = ['textual']

    value: float
    textual: str
    bytes: bytes
    rounded: str
    rounded_value: float

    def _deserialise(self, size=None):
        # Read once as a float
        saved_offset = self.stream.offset
        self._newField('value', self.stream.readDouble())

        # Read again as plain bytes for exact exporting
        self.stream.offset = saved_offset
        self._newField('bytes', self.stream.readBytes(8))

        # Make a rounded textual version with (inexact) if required
        value = self.value
        rounded = round(value, 8)
        inexact = abs(value - rounded) >= sys.float_info.epsilon
        text = str(rounded)
        self._newField('rounded', text)
        self._newField('rounded_value', rounded)
        if inexact:
            text += ' (inexact)'
        self._newField('textual', text)


class IntProperty(UEBase):
    string_format = '(int) {value}'
    main_field = 'value'

    value: int

    def _deserialise(self, size=None):
        self._newField('value', self.stream.readInt32())


class BoolProperty(UEBase):
    main_field = 'value'

    value: bool

    def _deserialise(self, size=None):
        self._newField('value', self.stream.readBool8())


class ByteProperty(UEBase):  # With optional enum type
    enum: NameIndex
    value: Union[NameIndex, int]

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
    main_field = 'value'
    skip_level_field = 'value'

    value: ObjectIndex

    def _deserialise(self, size=None):
        self._newField('value', ObjectIndex(self))


class NameProperty(UEBase):
    main_field = 'value'
    display_fields = ['value']

    value: NameIndex

    def _deserialise(self, size=None):
        self._newField('value', NameIndex(self))


class StringProperty(UEBase):
    main_field = 'value'

    size: int
    value: str

    def _deserialise(self, *args):
        self._newField('size', self.stream.readInt32())
        if self.size >= 0:
            self._newField('value', self.stream.readTerminatedString(self.size))
        else:
            self.size = -self.size
            self._newField('value', self.stream.readTerminatedWideString(self.size))

        # References to this item
        self.users = set()

    def register_user(self, user):
        self.users.add(user)


class Guid(UEBase):
    main_field = 'value'

    value: uuid.UUID

    def _deserialise(self, *args):
        raw_bytes = self.stream.readBytes(16)
        # Here we need to reverse the endian of each 4-byte word
        # to match C# UUID decoder. Python's bytes_le only corrects
        # some of the fields as the rest are single bytes.
        value = uuid.UUID(bytes=struct.pack('>4I', *struct.unpack('<4I', raw_bytes)))
        self._newField('value', value)


class StructEntry(UEBase):
    string_format = '{name} = ({type}) {value}'

    name: NameIndex
    type: NameIndex
    length: int
    value: UEBase

    def _deserialise(self):
        self._newField('name', NameIndex(self))
        self._newField('type', NameIndex(self))
        self._newField('length', self.stream.readInt64())

        self.name.link()
        self.type.link()
        if dbg_structs > 1:
            print(f'    StructEntry @ {self.start_offset}: name={self.name}, type={self.type}, length={self.length}')

        propertyType = getPropertyType(str(self.type))
        self._newField('value', '<not yet defined>')
        self.field_values['value'] = propertyType(self)
        self.field_values['value'].deserialise(self.length)
        self.field_values['value'].link()
        if dbg_structs > 1:
            print(f'     = ', str(self.value))


# Still to investigate
# STRUCTS_TO_IGNORE = (
#     'Anchors',
#     'DinoSetup',
#     'RichCurve',
# )

STRUCT_TYPES_TO_ABORT_ON = (
    # name of struct to ignore
    'Transform',
    'DinoSetup',
)

SKIPPABLE_STRUCTS = {
    # 'name': byte length
    'Vector': 12,
    'Vector2D': 8,
    'Rotator': 12,
    'Quat': 16,
    'Color': 4,
    'LinearColor': 16,
    # 'Transform': 4*4 + 3*4 + 3*4,
}


def decode_type_or_name(type_or_name: NameIndex):
    '''Decode a name as either a supported type, a length of an unsupported but skippable type, or a simple name.'''
    type_or_name.deserialise()
    if type_or_name.index == type_or_name.asset.none_index:
        return None, None, None
    type_or_name.link()

    if dbg_structs > 1:
        print(f'  Entry "{type_or_name}"')

    name = str(type_or_name)

    # Is it a supported type?
    propertyType = getPropertyType(str(type_or_name), throw=False)
    if propertyType:
        if dbg_structs > 2:
            print(f'  ...is a supported type')
        return name, propertyType, None

    name = str(type_or_name)

    # Is it skippable?
    known_length = SKIPPABLE_STRUCTS.get(name, None)
    if known_length is not None:
        if dbg_structs > 2:
            print(f'  ...is skippable')
        return name, None, known_length

    # Is it known as a fixed length struct but without a length?
    if name in STRUCT_TYPES_TO_ABORT_ON:
        if dbg_structs > 2:
            print(f'  ...is an unsupported unskippable struct type')
        return name, None, float('NaN')

    # Then treat it as just a name
    if dbg_structs > 2:
        print(f'  ...is not a name we recognise')
    return name, None, None


class StructProperty(UEBase):
    skip_level_field = 'values'

    count: int
    values: List[UEBase]

    def _deserialise(self, size):
        values = []
        self._newField('values', values)
        self._newField('count', 0)

        # Only process the struct name / type if we're not inside an array
        if not self.is_inside_array:
            # The first field may be the name or type... work out how to deal with it
            type_or_name = NameIndex(self)
            name, propertyType, skipLength = decode_type_or_name(type_or_name)
            if dbg_structs:
                print(f'Struct @ {self.start_offset}, size={size}: ' +
                      f'name={name}, type={propertyType.__name__ if propertyType else ""}, len={skipLength}')

            # It is a type we have a class for
            if propertyType:
                if dbg_structs > 1: print(f'  Recognised type: {name}')
                value = propertyType(self)
                values.append(value)
                value.deserialise(None)  # we don't have any size information

                # This should be the end of the struct
                # TODO: Look for examples where this isn't the end
                return

            # It is a fixed-length type we have a length for
            if skipLength is not None:
                if math.isnan(skipLength):
                    if dbg_structs > 1: print(f'  Recognised as unskippable and unsupported!!! Struct parsing terminated...')
                    self.stream.offset = self.start_offset + size + 8
                    return
                else:
                    if dbg_structs > 1: print(f'  Recognised as skippable: {skipLength} bytes')
                    values.append(f'<skipped {name} ({skipLength} bytes)>')
                    self.stream.offset += skipLength
                    return

            # It is the terminator
            if name is None:
                return

            self._newField('name', name)
        else:
            self._newField('inArray', True)
            if dbg_structs:
                print(f'Struct @ {self.start_offset}, size={size}: No name (inside array)')

        # If we got here, this struct is a property-bag type
        # print(f'  Assuming list of StructEntries')
        while True:
            # Peek the name and terminate on None
            saved_offset = self.stream.offset
            type_or_name = NameIndex(self)
            type_or_name.deserialise()
            if type_or_name.index == self.asset.none_index:
                return
            self.stream.offset = saved_offset

            # Decode the entry
            value = StructEntry(self)
            value.deserialise()
            values.append(value)
            self.field_values['count'] += 1

    def __str__(self):
        if self.values and len(self.values) == 1:
            return pretty(self.values[0])

        return f'{self.count} entries'

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
                    p.pretty(value)


class ArrayProperty(UEBase):
    field_type: NameIndex
    count: int
    values: List[UEBase]

    def _deserialise(self, size):
        assert size >= 4, "Array size is required"

        self._newField('field_type', NameIndex(self))
        self.field_type.link()
        saved_offset = self.stream.offset
        self._newField('count', self.stream.readUInt32())

        if self.count <= 0:
            self._newField('values', [])
            return

        propertyType = None
        try:
            propertyType = getPropertyType(str(self.field_type))
        except TypeError:
            pass

        if propertyType == None:  # or str(self.field_type) == 'StructProperty':
            self.stream.offset = saved_offset + size
            self._newField('value', f'<unsupported field type {self.field_type}>')
            return

        values = []
        self._newField('values', values)

        field_size = (size-4) // self.count  # don't know if we can use this
        end = saved_offset + size
        # print(f'Array @ {self.start_offset}, size={size}, count={self.count}, '
        #       f'calculated field size={field_size}, field type={self.field_type}')

        while self.stream.offset < end:
            # print("  Array entry @", self.stream.offset)
            value = propertyType(self)
            try:
                value.is_inside_array = True
                value.deserialise(field_size)
                value.link()
                values.append(value)
            except Exception as err:
                values.append('<exception during decoding of array element>')
                assetname = '<unnamed asset>'
                if hasattr(self, 'asset') and hasattr(self.asset, 'assetname'):
                    assetname = self.asset.assetname
                logger.info(f'Skippable exception parsing {assetname}: {err}')
                self.stream.offset = saved_offset + size
                return

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


class Vector(UEBase):
    x: FloatProperty
    y: FloatProperty
    z: FloatProperty

    def _deserialise(self, size=None):
        self._newField('x', FloatProperty(self))
        self._newField('y', FloatProperty(self))
        self._newField('z', FloatProperty(self))


class Vector2D(UEBase):
    x: FloatProperty
    y: FloatProperty

    def _deserialise(self, size=None):
        self._newField('x', FloatProperty(self))
        self._newField('y', FloatProperty(self))


class Rotator(UEBase):
    a: FloatProperty
    b: FloatProperty
    c: FloatProperty

    def _deserialise(self, size=None):
        self._newField('a', FloatProperty(self))
        self._newField('b', FloatProperty(self))
        self._newField('c', FloatProperty(self))


class Quat(UEBase):
    w: FloatProperty
    x: FloatProperty
    y: FloatProperty
    z: FloatProperty

    def _deserialise(self, size=None):
        self._newField('w', FloatProperty(self))
        self._newField('x', FloatProperty(self))
        self._newField('y', FloatProperty(self))
        self._newField('z', FloatProperty(self))


class Transform(UEBase):
    rotatio: Quat
    translation: Vector
    scale: Vector

    def _deserialise(self, size=None):
        self._newField('rotation', Quat(self))
        self._newField('translation', Vector(self))
        self._newField('scale', Vector(self))


class Color(UEBase):
    string_format = '#{rgba:08X}'

    rgba: int

    def _deserialise(self, size=None):
        self._newField('rgba', self.stream.readUInt32())


class LinearColor(UEBase):
    r: FloatProperty
    g: FloatProperty
    b: FloatProperty
    a: FloatProperty

    def _deserialise(self, size=None):
        self._newField('r', FloatProperty(self))
        self._newField('g', FloatProperty(self))
        self._newField('b', FloatProperty(self))
        self._newField('a', FloatProperty(self))


TYPE_MAP = {
    'FloatProperty': FloatProperty,
    'DoubleProperty': DoubleProperty,
    'BoolProperty': BoolProperty,
    'ByteProperty': ByteProperty,
    'IntProperty': IntProperty,
    'NameProperty': NameProperty,
    'StrProperty': StringProperty,
    'StringProperty': StringProperty,
    'ObjectProperty': ObjectProperty,
    'StructProperty': StructProperty,
    'ArrayProperty': ArrayProperty,
    'Guid': Guid,
    'Vector': Vector,
    'Vector2D': Vector2D,
    'Rotator': Rotator,
    'Quat': Quat,
    'Color': Color,
    'LinearColor': LinearColor,
    # 'Transform': Transform, # no worky
}


def getPropertyType(typeName: str, throw=True):
    result = TYPE_MAP.get(typeName, None)
    if throw and result is None:
        raise TypeError(f'Unsupported property type "{typeName}"')
    return result


# Types to export from this module
__all__ = tuple(set(cls.__name__ for cls in TYPE_MAP.values())) + ('getPropertyType', 'PropertyTable')
