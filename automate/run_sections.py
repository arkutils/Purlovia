import re
from typing import Dict, Iterator, Tuple

__all__ = [
    'parse_parse_runlist',
    'should_run_section',
]


def _section_parent(value: str) -> str:
    '''
    >>> _section_parent('root.stage')
    'root'
    >>> _section_parent('root')
    ''
    >>> _section_parent('')
    ''
    '''
    idx = value.rfind('.')
    if idx >= 0:
        return value[:idx]

    return ''


def _section_parents(value: str, include_self=False) -> Iterator[str]:
    '''
    >>> list(_section_parents('root.stage')) == ['root', '']
    True
    >>> list(_section_parents('root.stage', True)) == ['root.stage', 'root', '']
    True
    >>> list(_section_parents('')) == []
    True
    '''
    if include_self:
        yield value

    while value:
        value = _section_parent(value)
        yield value


def _parse_section(value: str) -> Tuple[str, bool]:
    '''
    >>> _parse_section('all') == ('', True)
    True
    >>> _parse_section('-all') == ('', False)
    True
    >>> _parse_section('root.stage') == ('root.stage', True)
    True
    >>> _parse_section('-root.stage') == ('root.stage', False)
    True
    '''
    sense = True
    if value.startswith('-'):
        sense = False
        value = value[1:]

    if not value:
        raise ValueError("Empty run section")

    if value.count('.') > 1:
        raise ValueError("Sections must be for the format 'root[.stage]'")

    if value == 'all':
        value = ''

    return (value, sense)


def parse_runlist(value: str) -> Dict[str, bool]:
    '''
    Simply parse the input string and turn it into dict entries. Key is the target and value is True for add, False for remove.

    >>> parse_runlist('') == {}
    True
    >>> parse_runlist('all') == {'': True}
    True
    >>> parse_runlist('-all') == {'': False}
    True
    >>> parse_runlist('all -wiki') == {'': True, 'wiki': False}
    True
    >>> parse_runlist('all,-wiki') == {'': True, 'wiki': False}
    True
    >>> parse_runlist('all-wiki') == {'': True, 'wiki': False}
    True
    >>> parse_runlist('root1+root2') == {'root1': True, 'root2': True}
    True
    >>> parse_runlist('root-root.stage') == {'root': True, 'root.stage': False}
    True
    >>> parse_runlist('root.stage') == {'root.stage': True}
    True
    >>> parse_runlist('root,-root.stage') == {'root': True, 'root.stage': False}
    True
    '''
    value = value.replace('-', ',-')
    value = re.sub(r'[\s,+]+', ' ', value, 0)
    parts = value.split(' ')
    part_states = dict(_parse_section(part) for part in parts if part)
    return part_states


def should_run_section(name: str, states: Dict[str, bool]) -> bool:
    '''
    Given a set of state configs, and a name, work out if it should be run.

    >>> should_run_section('root.stage', {'root.stage': True})
    True
    >>> should_run_section('root.stage', {'root': True})
    True
    >>> should_run_section('root.stage', {'': True})
    True
    >>> should_run_section('root.stage', {})
    False
    >>> should_run_section('root.stage', {'root': True, 'root.stage': True})
    True
    >>> should_run_section('root.stage', {'root': False, 'root.stage': True})
    True
    >>> should_run_section('root.stage2', {'root.stage': True})
    False
    >>> should_run_section('root.stage2', {'root': True})
    True
    >>> should_run_section('root.stage2', {'': True})
    True
    >>> should_run_section('root.stage2', {})
    False
    >>> should_run_section('root.stage2', {'root': True, 'root.stage': True})
    True
    >>> should_run_section('root.stage2', {'root': False, 'root.stage': True})
    False
    '''
    for parent in _section_parents(name, include_self=True):
        state = states.get(parent, None)
        if state is not None:
            return state

    return False
