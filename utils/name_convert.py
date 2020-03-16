import re


def snake_to_camel(string: str) -> str:
    '''
    >>> snake_to_camel('snake_case')
    'SnakeCase'
    '''
    return ''.join(word.capitalize() for word in string.split('_'))


def camel_to_snake(name: str) -> str:
    '''
    Based on https://stackoverflow.com/a/12867228/8466643.

    >>> camel_to_snake('CamelCase')
    'camel_case'
    >>> camel_to_snake('camelCase')
    'camel_case'
    >>> camel_to_snake('get2HTTPResponse123Code')
    'get2_http_response123_code'
    >>> camel_to_snake('exportASB')
    'export_asb'
    '''
    return re.sub('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))', r'_\1', name).lower()


def kebab_to_snake(name: str) -> str:
    '''
    >>> kebab_to_snake('export-asb')
    'export_asb'
    '''
    return name.replace('-', '_')


def snake_to_kebab(name: str) -> str:
    '''
    >>> snake_to_kebab('export_asb')
    'export-asb'
    '''
    return name.replace('_', '-')


REGEX_UE_PRETTY = re.compile(r'((?<=[^\W[A-Z])[A-Z]|(?<=\S)[A-Z](?=[a-z]))')


def uelike_prettify(name: str) -> str:
    '''
    >>> uelike_prettify('ARK')
    'ARK'
    >>> uelike_prettify('ARK:SurvivalEvolved')
    'ARK: Survival Evolved'
    >>> uelike_prettify('ARKAdditions')
    'ARK Additions'
    >>> uelike_prettify('PrimalFear')
    'Primal Fear'
    >>> uelike_prettify('AAAABBBc')
    'AAAABB Bc'
    '''
    # Insert spaces before capital letters
    name = REGEX_UE_PRETTY.sub(r' \1', name)
    return name
