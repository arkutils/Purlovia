import sys
import uuid
from typing import Type

try:
    from IPython.lib.pretty import PrettyPrinter, pprint, pretty
    support_pretty = True
except ImportError:
    support_pretty = False

from .stream import MemoryStream
from .base import UEBase
from .coretypes import *


class PropertyTable(UEBase):
    string_format = '{count} entries'
    display_fields = ['values']
    skip_level_field = 'values'

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

    def _deserialise(self):
        self._newField('name', NameIndex(self))
        self._newField('type', NameIndex(self))
        self._newField('size', self.stream.readUInt32())
        self._newField('index', self.stream.readUInt32())


class Property(UEBase):
    string_format = '{header.name}[{header.index}] = {value}'

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
        self._newField('rounded', text)
        self._newField('rounded_value', rounded)
        if inexact:
            text += ' (inexact)'
        self._newField('textual', text)


class DoubleProperty(UEBase):
    main_field = 'textual'
    display_fields = ['textual']

    def _deserialise(self, size):
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

    def _deserialise(self, size):
        self._newField('value', self.stream.readInt32())


class BoolProperty(UEBase):
    main_field = 'value'

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
    main_field = 'value'
    skip_level_field = 'value'

    def _deserialise(self, size):
        self._newField('value', ObjectIndex(self))


class NameProperty(UEBase):
    main_field = 'value'
    display_fields = ['value']

    def _deserialise(self, size):
        self._newField('value', NameIndex(self))


class StringProperty(UEBase):
    main_field = 'value'

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

    def _deserialise(self, *args):
        raw_bytes = self.stream.readBytes(16)
        self._newField('value', str(uuid.UUID(bytes_le=raw_bytes)))


class StructEntry(UEBase):
    string_format = '{name} = ({type}) {value}'

    def _deserialise(self):
        self._newField('name', NameIndex(self))
        self._newField('type', NameIndex(self))
        self._newField('length', self.stream.readInt64())

        self.name.link()
        self.type.link()
        # print(f'    StructEntry @ {self.start_offset}: name={self.name}, type={self.type}, length={self.length}')

        propertyType = getPropertyType(str(self.type))
        self._newField('value', '<not yet defined>')
        self.field_values['value'] = propertyType(self)
        self.field_values['value'].deserialise(self.length)
        self.field_values['value'].link()
        # print(f'      ', str(self.value))


ARK_DEFINED_STRUCTS = (
    'AttenuationSettings',
    'BodyInstance',
    'CollisionResponse',
    'ColorSetDefinition',
    'DecalData',
    'HUDElement',
    'InputChord',
    'KAggregateGeom',
    'LevelExperienceRamp',
    'MultiUseEntry',
    'NavAgentProperties',
    'PlayerCharacterGenderDefinition',
    'PrimalCharacterStatusStateDefinition',
    'PrimalCharacterStatusStateThresholds',
    'PrimalCharacterStatusValueDefinition',
    'PrimalEquipmentDefinition',
    'PrimalItemDefinition',
    'PrimalItemStatDefinition',
    'ProjectileArc',
    'SingleAnimationPlayData',
    'StatusValueModifierDescription',
    'StringAssetReference',
    'WalkableSlopeOverride',
    'WeightedObjectList',
)

STRUCTS_TO_IGNORE = (
    'Anchors',
    'Color',
    'DinoSetup',
    'LinearColor',
    'RichCurve',
    'Rotator',
    'Transform',
    'Vector',
    'Vector2D',
)


class StructProperty(UEBase):
    skip_level_field = 'values'

    def _deserialise(self, size):
        values = []
        self._newField('values', values)
        self._newField('count', 0)
        # print(f'Struct @ {self.start_offset}, size={size}')

        while True:
            type_or_name = NameIndex(self)
            type_or_name.deserialise()
            if type_or_name.index == self.asset.none_index:
                break

            self.count += 1

            type_or_name.link()

            if str(type_or_name) in STRUCTS_TO_IGNORE:
                self.stream.offset = self.start_offset + 8 + size
                return

            if str(type_or_name) in ARK_DEFINED_STRUCTS:
                self.stream.offset += 8

            propertyType = None
            try:
                propertyType = getPropertyType(str(type_or_name))
            except TypeError:
                pass

            if propertyType:
                # This struct has a recognisable struct type and its data should be immediiately following
                # print(f'  Assuming a type')
                value = propertyType(self)
                values.append(value)
                value.deserialise(None)  # we don't have any size information
            else:
                # Then type_of_name was (hopefully) a name and we get the real property type next
                # print(f'  Struct entry @ {self.stream.offset-8}, type={type_or_name}')
                # print(f'  Name assumed')

                # Rewind and read a StructEntry
                self.stream.offset -= 8
                try:
                    value = StructEntry(self)
                    value.deserialise()
                    values.append(value)
                except Exception as err:
                    values.append(f'<exception during decoding of struct entry for type_or_name "{type_or_name}">')
                    print(f'Failed to decode struct entry @ {self.start_offset} with type: {type_or_name}')
                    if support_pretty: pprint(err)
                    self.stream.offset = self.start_offset + 8 + size
                    return

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
                value.deserialise(field_size)
                value.link()
                values.append(value)
            except Exception as err:
                values.append('<exception during decoding of array element>')
                if support_pretty: pprint(err)
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


TYPE_MAP = {
    'FloatProperty': FloatProperty,
    'DoubleProperty': DoubleProperty,
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
__all__ = tuple(set(cls.__name__ for cls in TYPE_MAP.values())) + ('getPropertyType', 'PropertyTable')
