import re

__all__ = (
    'getModNameFromNumber',
    'getModNumberFromName',
)

mods = '''
    Primal_Fear                         839162288
    Primal_Fear_Noxious_Creatures       1356703358
'''

mods = [[field.strip() for field in re.sub('\s+', ' ', line).strip().split(' ')] for line in mods.strip().split('\n') if line]
mods_from_names = dict(mods)
mods_from_numbers = dict(reversed(fields) for fields in mods)


def getModNameFromNumber(number):
    return mod_from_numbers[number]


def getModNumberFromName(name):
    return mod_from_numbers[name]
