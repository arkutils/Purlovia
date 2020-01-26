import math
import operator
import struct
import sys
import uuid
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from logging import NullHandler, getLogger
from numbers import Real
from typing import *

from .base import UEBase
from .context import INCLUDE_METADATA, get_ctx
from .coretypes import *
from .number import *
from .stream import MemoryStream
from .utils import clean_float

if INCLUDE_METADATA:
    try:
        from IPython.lib.pretty import PrettyPrinter  # type: ignore
        support_pretty = True
    except ImportError:
        support_pretty = False
else:
    support_pretty = False

#pylint: disable=unused-argument,arguments-differ

dbg_structs = 0

logger = getLogger(__name__)
logger.addHandler(NullHandler())

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

    if INCLUDE_METADATA and support_pretty:

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
            if self.header.type.value.value not in SKIPPABLE_STRUCTS:
                warnings.warn(f'Skipping unknown property type {self.header.type.value.value}')

        if propertyType:
            self._newField('value', propertyType(self), self.header.size)
            self.value.link()  # safe to link as all imports/exports are completed
        else:
            self._newField('value', f'<unsupported type {str(self.header.type)}>')
            self.stream.offset += self.header.size

    if INCLUDE_METADATA and support_pretty:

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


class DummyAsset(UEBase):
    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        for k, v in kwargs.items():
            vars(self).setdefault(k, v)
        self.fake_names = dict()
        self.index = 0
        self.none_index = 9999
        self.asset = self

    def _deserialise(self, *args, **kwargs):
        return super()._deserialise(*args, **kwargs)

    def _link(self):
        return super()._link()

    def addFakeName(self, name: str) -> int:
        index = self.index = self.index + 1
        self.fake_names[index] = name
        return index

    def getName(self, index):
        fake_name = self.fake_names.get(index, None)
        if fake_name is not None:
            return StringProperty.create(fake_name)
        if index == self.none_index:
            return StringProperty.create('None')
        raise ValueError("Attempt to lookup a name in a dummy asset")


class ValueProperty(UEBase, Real, ABC):
    value: Real

    @abstractmethod
    def _deserialise(self, size=None):
        pass

    def format_for_json(self):
        return self.value

    # Not sure why we have to specifically override these, but we do
    __eq__ = UEBase.__eq__
    __hash__ = UEBase.__hash__

    def __bool__(self):
        assert self.is_serialised
        return bool(self.value)

    __nonzero__ = __bool__

    def __float__(self):
        assert self.is_serialised
        return float(self.value)

    def __int__(self):
        assert self.is_serialised
        return int(self.value)

    __nonzero__ = __bool__

    def __pos__(self):
        assert self.is_serialised
        return self.value

    def __neg__(self):
        assert self.is_serialised
        return -self.value

    __pow__, __rpow__ = make_binary_operators(pow)
    __mod__, __rmod__ = make_binary_operators(operator.mod)
    __add__, __radd__ = make_binary_operators(operator.add)
    __sub__, __rsub__ = make_binary_operators(operator.sub)
    __mul__, __rmul__ = make_binary_operators(operator.mul)
    __truediv__, __rtruediv__ = make_binary_operators(operator.truediv)
    __floordiv__, __rfloordiv__ = make_binary_operators(operator.floordiv)

    __eq__ = make_binary_operator(operator.eq)
    __ne__ = make_binary_operator(operator.ne)
    __gt__ = make_binary_operator(operator.gt)
    __lt__ = make_binary_operator(operator.lt)
    __ge__ = make_binary_operator(operator.ge)
    __le__ = make_binary_operator(operator.le)

    __round__ = make_operator(round)
    __ceil__ = make_operator(math.ceil)
    __abs__ = make_operator(operator.abs)
    __floor__ = make_operator(math.floor)
    __trunc__ = make_operator(math.trunc)


class FloatProperty(ValueProperty):
    main_field = 'textual'
    display_fields = ['textual']

    # value: float
    textual: str
    raw_data: bytes
    rounded: str
    rounded_value: float

    @classmethod
    def create(cls, inp: Union[float, str, Tuple[float, str]], asset: UEBase = None):
        '''Create a new FloatProperty directly.

        Specify as either:

        * Simple float value
        * Hex string representing the raw data
        * Byte string representing the raw data
        * A tuple of (float, hex/bytes)

        If both raw data and a value is supplied the raw data will be used but only after a check that the
        two arguments are equal (to 5 significant figures).'''

        value: Optional[float] = None
        data: Optional[Union[str, bytes]] = None

        if isinstance(inp, tuple):
            value, data = inp
        elif isinstance(inp, float):
            value = inp
        elif isinstance(inp, Real):
            value = float(inp)
        elif isinstance(inp, (str, bytes)):
            data = inp
        else:
            raise ValueError(f"Invalid inputs for FloatProperty.create: {inp!r}")

        if isinstance(data, str):
            assert len(data) == 8, "Hex value must be 8 digits"
            data = bytes.fromhex(data)

        if value is not None and data is not None:
            # Check the two match, roughly
            from_data = struct.unpack('f', data)[0]
            assert f"{value:.5e}" == f"{from_data:.5e}", "Float value and raw data do not match"

        if data is None:
            data = struct.pack('f', value)

        asset = asset or DummyAsset(asset=None)
        obj = cls(asset, MemoryStream(data))
        obj.deserialise()
        return obj

    def _deserialise(self, size=None):
        # Read once as a float
        saved_offset = self.stream.offset
        self._newField('value', self.stream.readFloat())

        # Read again as plain bytes for exact exporting
        self.stream.offset = saved_offset
        self._newField('raw_data', self.stream.readBytes(4))

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

    def __bytes__(self):
        assert self.is_serialised
        return self.raw_data

    def format_for_json(self):
        '''Restrict single-precision float output to 7 significant figures.'''
        return clean_float(self.value)


class DoubleProperty(ValueProperty):
    main_field = 'textual'
    display_fields = ['textual']

    value: float  # type: ignore
    textual: str
    bytes: ByteString
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


class IntProperty(ValueProperty):
    string_format = '(int) {value}'
    main_field = 'value'

    value: int  # type: ignore

    @classmethod
    def create(cls, value: int, asset: UEBase = None):
        '''Create a new IntProperty directly.'''
        if not isinstance(value, int):
            raise ValueError("IntProperty requires an int value")

        data = struct.pack('i', value)
        asset = asset or DummyAsset(asset=None)
        obj = cls(asset, MemoryStream(data))
        obj.deserialise()
        return obj

    def _deserialise(self, size=None):
        self._newField('value', self.stream.readInt32())


class UInt32Property(IntProperty):
    string_format = '(uint) {value}'

    def _deserialise(self, size=None):
        self._newField('value', self.stream.readUInt32())


class BoolProperty(ValueProperty):
    main_field = 'value'

    value: bool  # type: ignore

    @classmethod
    def create(cls, value: bool, asset: UEBase = None):
        '''Create a new BoolProperty directly.'''
        if not isinstance(value, bool):
            raise ValueError("BoolProperty requires a boolean value")

        data = struct.pack('b', 1 if value else 0)
        asset = asset or DummyAsset(asset=None)
        obj = cls(asset, MemoryStream(data))
        obj.deserialise()
        return obj

    def _deserialise(self, size=None):
        self._newField('value', self.stream.readBool8())


class ByteProperty(ValueProperty):  # With optional enum type
    enum: NameIndex
    value: Union[NameIndex, int]  # type: ignore  # (we *want* to override the base type)

    @classmethod
    def create(cls, value: Union[int, Tuple[str, str]], asset: UEBase = None):
        '''Create a new ByteProperty directly.'''
        if isinstance(value, int):
            asset = asset or DummyAsset()
            data = struct.pack('iib', asset.none_index, 0, value)
            size = 1
        elif isinstance(value, tuple):  # (str, str)
            enum, name = value
            asset = asset or DummyAsset()
            enum_index = asset.addFakeName(enum)
            name_index = asset.addFakeName(f"{enum}::{name}")
            data = struct.pack('iiii', enum_index, 0, name_index, 0)
            size = 8
        else:
            raise ValueError("ByteProperty requires an int value or a tuple of (enum, value) strings")

        obj = cls(asset, MemoryStream(data))
        obj.deserialise(size=size)
        obj.link()
        return obj

    def get_enum_value_name(self):
        assert isinstance(self.value, NameIndex)
        return str(self.value).split('::')[-1]

    def _deserialise(self, size=None):
        assert size is not None

        self._newField('enum', NameIndex(self))
        if size == 1:
            self._newField('value', self.stream.readUInt8())
        elif size == 8:
            self._newField('value', NameIndex(self))
        else:
            self._newField('value', '<skipped bytes>')
            self.stream.offset += size

    if INCLUDE_METADATA and support_pretty:

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

    def format_for_json(self):
        return {"enum": str(self.enum), "value": self.value}


class ObjectProperty(UEBase):
    main_field = 'value'
    skip_level_field = 'value'

    value: ObjectIndex

    def _deserialise(self, size=None):
        self._newField('value', ObjectIndex(self))

    def format_for_json(self):
        return self.value.format_for_json()


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

    users: Set[UEBase]

    @classmethod
    def create(cls, value: str, asset: UEBase = None):
        '''Create a new StringProperty directly.'''
        if not isinstance(value, str):
            raise ValueError("StringProperty requires an str value")

        byte_string = value.encode('utf8') + bytes.fromhex('00')
        count = len(byte_string)
        data = struct.pack(f'i{count}s', count, byte_string)
        asset = asset or DummyAsset(asset=None)
        obj = cls(asset, MemoryStream(data))
        obj.deserialise()
        return obj

    def _deserialise(self, *args):
        self._newField('size', self.stream.readInt32())
        if self.size >= 0:
            self._newField('value', self.stream.readTerminatedString(self.size))
        else:
            self.size = -self.size
            self._newField('value', self.stream.readTerminatedWideString(self.size))

        if INCLUDE_METADATA:
            # References to this item
            self.users = set()

    def register_user(self, user):
        if INCLUDE_METADATA:
            self.users.add(user)

    def __str__(self):
        return self.value

    def __bool__(self):
        assert self.is_serialised
        return bool(self.value)

    __nonzero__ = __bool__


class TextProperty(UEBase):
    main_field = 'source_string'

    flags: int
    history_type: int
    namespace: StringProperty
    key: StringProperty
    source_string: StringProperty

    def _deserialise(self, *args):
        self._newField('flags', self.stream.readUInt32())
        self._newField('history_type', self.stream.readInt8())
        self._newField('namespace', StringProperty(self))
        self._newField('key', StringProperty(self))
        self._newField('source_string', StringProperty(self))

    def __str__(self):
        return f'{self.source_string}'


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


class CustomVersion(UEBase):
    guid: Guid
    version: int
    friendly_name: str

    def _deserialise(self):
        self._newField('guid', Guid(self))
        self._newField('version', self.stream.readUInt32())
        self._newField('friendly_name', StringProperty(self))


class StructEntry(UEBase):
    string_format = '{name} = ({type}) {value}'

    name: NameIndex
    type: NameIndex
    length: int
    value: UEBase

    def _deserialise(self):
        self._newField('name', NameIndex(self))
        self._newField('type', '<not yet defined>')
        entryType = NameIndex(self).deserialise()
        self._newField('length', self.stream.readInt64())

        self.name.link()

        name, propertyType, skipLength = decode_type_or_name(entryType, skip_deserialise=True)
        self.field_values['type'] = entryType

        if dbg_structs > 1:
            print(f'    StructEntry @ {self.start_offset}: name={self.name}, type={entryType}, length={self.length}')

        # We may know the type of the data to go into this...
        subTypeName = TYPED_ARRAY_CONTENT.get(str(self.name), None)
        if propertyType == ArrayProperty and subTypeName is not None:
            self._newField('value', '<not yet defined>')
            subType = getPropertyType(subTypeName)
            self.field_values['value'] = ArrayProperty(self)
            self.field_values['value'].deserialise(self.length, with_type=subType)
            self.field_values['value'].link()
            if dbg_structs > 1:
                print(f'     = ', str(self.value))
        elif propertyType:
            self._newField('value', '<not yet defined>')
            self.field_values['value'] = propertyType(self)
            self.field_values['value'].deserialise(self.length)
            self.field_values['value'].link()
            if dbg_structs > 1:
                print(f'     = ', str(self.value))

            return

        if skipLength is not None:
            self.stream.offset += self.length
            if dbg_structs > 1: print(f'  Recognised as skippable: {self.length} bytes')
            self.field_values['value'] = f'<skipped {name} ({self.length} bytes)>'
            self.stream.offset += skipLength
            return

        if dbg_structs:
            print(f'Struct @ {self.start_offset}, size=?: ' +
                  f'name={name}, type={propertyType.__name__ if propertyType else ""}, len={skipLength}')


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
    'DelegateProperty': 12,
    'MulticastDelegateProperty': 12,  # TODO: Verify
    'LazyObjectProperty': 16,
    'Vector4': 16,
    # 'Transform': 4*4 + 3*4 + 3*4,
}

TYPED_ARRAY_CONTENT = {
    'VertexData': 'Vector',
    'NPCsSpawnOffsets': 'Vector',
}


def decode_type_or_name(type_or_name: NameIndex, skip_deserialise=False):
    '''Decode a name as either a supported type, a length of an unsupported but skippable type, or a simple name.'''
    if not skip_deserialise:
        type_or_name.deserialise()
    if type_or_name.index == type_or_name.asset.none_index:
        return None, None, None
    type_or_name.link()

    if dbg_structs > 1:
        print(f'  Entry "{type_or_name}"')

    name = str(type_or_name)

    # Is it a supported type?
    propertyType = getPropertyType(name, throw=False)
    if propertyType:
        if dbg_structs > 2:
            print(f'  ...is a supported type')
        return name, propertyType, None

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
    _as_dict: Optional[Dict[str, UEBase]] = None

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

    def as_dict(self) -> Dict[str, UEBase]:
        return self._as_dict or self._convert_to_dict()

    def get_property(self, name: str, fallback=NO_FALLBACK) -> UEBase:
        value = self.as_dict()[name]

        if value is not None:
            return value

        if fallback is not NO_FALLBACK:
            return fallback

        raise KeyError(f"Property {name} not found")

    def _convert_to_dict(self):
        result: Dict[str, Optional[UEBase]] = defaultdict(lambda: None)

        for entry in self.values:
            name = str(entry.name)
            value = entry.value

            result[name] = value

        self._as_dict = result
        return result

    def __str__(self):
        if self.values and len(self.values) == 1:
            return str(self.values[0])

        return f'{self.count} entries'

    if INCLUDE_METADATA and support_pretty:

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

    def _deserialise(self, size, with_type: Type = None):  # type: ignore
        assert size >= 4, "Array size is required"

        self._newField('field_type', NameIndex(self))
        self.field_type.link()

        saved_offset = self.stream.offset
        self._newField('count', self.stream.readUInt32())

        if self.count <= 0:
            self._newField('values', [])
            return

        propertyType = with_type
        if not propertyType:
            try:
                propertyType = getPropertyType(str(self.field_type))
            except TypeError:
                pass

        if propertyType is None:  # or str(self.field_type) == 'StructProperty':
            self.stream.offset = saved_offset + size
            self._newField('value', f'<unsupported field type {self.field_type}>')
            return

        values: List[Union[UEBase, str]] = []
        self._newField('values', values)

        field_size = (size-4) // self.count  # don't know if we can use this
        end = saved_offset + size
        if dbg_structs > 1:
            print(f'Array @ {self.start_offset}, size={size}, count={self.count}, '
                  f'calculated field size={field_size}, field type={self.field_type}')

        while self.stream.offset < end:
            # print("  Array entry @", self.stream.offset)
            value = propertyType(self)
            try:
                value.is_inside_array = True
                value.deserialise(field_size)
                value.link()
                values.append(value)
            except Exception as err:  # pylint: disable=broad-except
                values.append('<exception during decoding of array element>')
                # logger.warning('exception during decoding of array element', exc_info=True)
                assetname = '<unnamed asset>'
                if hasattr(self, 'asset') and hasattr(self.asset, 'assetname'):
                    assetname = self.asset.assetname
                logger.debug('Skippable exception parsing %s: %s', assetname, err)
                self.stream.offset = saved_offset + size
                return

        self.stream.offset = saved_offset + size

    def format_for_json(self):
        return [element.format_for_json() for element in self.values]

    if INCLUDE_METADATA and support_pretty:

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

    def format_for_json(self):
        return {'x': self.x.format_for_json(), 'y': self.y.format_for_json(), 'z': self.z.format_for_json()}


class Box(UEBase):
    min: Vector
    max: Vector
    is_valid: bool

    def _deserialise(self, size=None):
        self._newField('min', Vector(self))
        self._newField('max', Vector(self))
        self._newField('is_valid', BoolProperty(self))


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
    rotation: Quat
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

    def as_tuple(self):
        return tuple(v for v in self.field_values.values())


class IntPoint(UEBase):
    x: int
    y: int

    def _deserialise(self, size=None):
        self._newField('x', self.stream.readInt32())
        self._newField('y', self.stream.readInt32())


class EngineVersion(UEBase):
    major: int
    minor: int
    patch: int
    changelist: int
    branch: str

    def _deserialise(self):
        self._newField('major', self.stream.readUInt16())
        self._newField('minor', self.stream.readUInt16())
        self._newField('patch', self.stream.readUInt16())
        self._newField('changelist', self.stream.readUInt32())
        self._newField('branch', StringProperty(self))


TYPE_MAP = {
    'FloatProperty': FloatProperty,
    'DoubleProperty': DoubleProperty,
    'BoolProperty': BoolProperty,
    'ByteProperty': ByteProperty,
    'IntProperty': IntProperty,
    'UInt32Property': UInt32Property,
    'NameProperty': NameProperty,
    'StrProperty': StringProperty,
    'StringProperty': StringProperty,
    'TextProperty': TextProperty,
    'ObjectProperty': ObjectProperty,
    'StringAssetReference': StringProperty,
    'AssetObjectProperty': StringProperty,
    'StructProperty': StructProperty,
    'ArrayProperty': ArrayProperty,
    'Guid': Guid,
    'Vector': Vector,
    'Vector2D': Vector2D,
    'Rotator': Rotator,
    'Quat': Quat,
    'Color': Color,
    'LinearColor': LinearColor,
    'Box': Box,
    'IntPoint': IntPoint,
    # 'Transform': Transform, # no worky
}


def getPropertyType(typeName: str, throw=True):
    result = TYPE_MAP.get(typeName, None)
    if throw and result is None:
        raise TypeError(f'Unsupported property type "{typeName}"')
    return result


# Types to export from this module
__all__ = tuple(set(cls.__name__
                    for cls in TYPE_MAP.values())) + ('getPropertyType', 'PropertyTable', 'CustomVersion', 'EngineVersion')
