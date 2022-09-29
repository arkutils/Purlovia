from enum import IntEnum

from ue.properties import ByteProperty


class Stat(IntEnum):
    Health = 0
    Stamina = 1
    Torpidity = 2
    Oxygen = 3
    Food = 4
    Water = 5
    Temperature = 6
    Weight = 7
    MeleeDamage = 8
    MovementSpeed = 9
    Fortitude = 10
    CraftingSkill = 11


def stat_enum_to_index(stat: ByteProperty) -> int:
    if str(stat.enum) != 'EPrimalCharacterStatusValue':
        raise ValueError(f'stat {stat.enum} is not an EPrimalCharacterStatusValue')

    try:
        return STAT_LOOKUP[str(stat.value)]
    except KeyError:
        raise ValueError(f'stat {stat.value} is not a valid EPrimalCharacterStatusValue')


def stat_enum_to_stat(stat: ByteProperty) -> Stat:
    return Stat(stat_enum_to_index(stat))


STAT_LOOKUP = {
    'EPrimalCharacterStatusValue::Health': 0,
    'EPrimalCharacterStatusValue::Stamina': 1,
    'EPrimalCharacterStatusValue::Torpidity': 2,
    'EPrimalCharacterStatusValue::Oxygen': 3,
    'EPrimalCharacterStatusValue::Food': 4,
    'EPrimalCharacterStatusValue::Water': 5,
    'EPrimalCharacterStatusValue::Temperature': 6,
    'EPrimalCharacterStatusValue::Weight': 7,
    'EPrimalCharacterStatusValue::MeleeDamageMultiplier': 8,
    'EPrimalCharacterStatusValue::SpeedMultiplier': 9,
    'EPrimalCharacterStatusValue::TemperatureFortitude': 10,
    'EPrimalCharacterStatusValue::CraftingSpeedMultiplier': 11,
}
