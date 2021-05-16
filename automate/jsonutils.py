import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from utils.log import get_logger

__all__ = [
    'save_json_if_changed',
    'save_as_json',
    'should_save_json',
]

logger = get_logger(__name__)


def save_json_if_changed(values: Dict[str, Any], fullpath: Path, pretty: bool) -> Optional[str]:
    '''
    Writes an object to the given file in JSON format.
    Avoids writing if the content has not changed (ignoring any 'version' field at the top-level).
    Returns the version number used if written, or None if not.
    '''
    changed, version = should_save_json(values, fullpath)
    if changed:
        logger.info(f'Saving export to {fullpath} with version {version}')
        values['version'] = version
        save_as_json(values, fullpath, pretty=pretty)
        return version
    else:
        logger.info(f'No changes to {fullpath}')
        return None


def should_save_json(values: Dict[str, Any], fullpath: Path) -> Tuple[bool, str]:
    '''
    Works out if a file needs to be saved and with which version number.

    This is calculated using the digest of its content, excluding the version field.
    Also handles cases where the content has changed but the version has not, by bumping the build number.

    Returns a tuple of (changed, version), where `changed` is a boolean saying whether the data needs to be
    saved and `version` is the version number to use.
    '''
    new_version: str = values.get('version', None)
    if not new_version:
        raise ValueError('Export data must contain a version field')

    # Load the existing file
    try:
        with open(fullpath) as f:
            existing_data = json.load(f)
    except Exception:  # pylint: disable=broad-except
        # Old file doesn't exist/isn't readable/is corrupt
        return (True, new_version)

    # Can only do this with dictionaries
    if not isinstance(existing_data, dict):
        return (True, new_version)

    # Get the old and new versions and digests
    _, new_digest = _calculate_digest(values)
    old_version, old_digest = _calculate_digest(existing_data)

    # If content hasn't changed, don't save regardless of any version changes
    if new_digest == old_digest:
        return (False, old_version or new_version)

    # Content has changed... if the version is changed also then we're done
    assert old_version
    old_parts = [int(v) for v in old_version.strip().split('.')]
    new_parts = [int(v) for v in new_version.strip().split('.')]
    if old_parts[:3] != new_parts[:3]:
        return (True, new_version)

    # Content has changed but version hasn't... bump build number
    parts = old_parts
    parts = parts + [0] * (4 - len(parts))
    parts[3] += 1
    bumped_version = '.'.join(str(v) for v in parts)

    return (True, bumped_version)


def _calculate_digest(values: Dict[str, Any]) -> Tuple[Optional[str], str]:
    '''Calculates the digest of the given data, returning a tuple of (version, digest).'''
    assert isinstance(values, dict)

    # Take a shallow copy of the data and remove the version field
    values = dict(values)
    version: Optional[str] = values.pop('version', None)

    # Also remove the format field
    # If it changes, but no content changes, we're content to use the old format
    values.pop('format', None)

    # Calculate the digest of the minified output, using SHA512
    as_bytes = _format_json(values, pretty=False).encode('utf8')
    digest = hashlib.sha512(as_bytes).hexdigest()

    return (version, digest)


NUMBER_RE = r'[+-]?\d+(\.\d+)?([eE][-+]?\d+)?|true|false'

# Join 2-line color (name, [r,g,b,e]) data onto one line
JOIN_COLORS_REGEX = re.compile(r"\[\n\s+([\w\" ]+),\n\s+(.{,90})\n\s+\]")

# Reduce 2-12 numbers in an array onto a single line
JOIN_MULTIPLE_NUMBERS_REGEX = re.compile(r'(\n\s+)(' + NUMBER_RE + r'),(?:\n\s+(?:' + NUMBER_RE + r'|null|"[^"\n\t]*"),?){1,12}')

# Reduce short arrays of strings onto a single line
JOIN_MULTIPLE_STRINGS_REGEX = re.compile(r'\[((?:\n\s+".{1,30}",?\s*$){1,4})\n\s+\]', re.MULTILINE)

# Reduces dict fields with only a single line of content (including previously joined multiple fields) to a single line
COLLAPSE_SINGLE_LINE_DICT_REGEX = re.compile(r"\{\n\s+(\"\w+\": [^}\n\]]{1,120})\n\s+\}")

# Reduce arrays with only a single line of content (including previously joined multiple fields) to a single line
COLLAPSE_SINGLE_LINE_ARRAY_REGEX = re.compile(r'\[\s+(.+)\s+\]')

# Sets of named fields that should be combined onto a single line
# Only applies if all fields are found
JOIN_LINE_FIELDS = (
    'x|y',
    'x|y|z',
    'a|b',
    'a|b|c',
    'lat|long?',
    'name|interval|dmg|radius|stamina',
    'base|sprint',
    'base|crouch|sprint',
    'min|max',
    'min|max|pow',
    'qty|type',
    'exact|qty|type',
    'stat|value|useItemQuality',
    'stat|value|useItemQuality|duration',
)


def _flattener(group=0, prefix='', postfix=None):
    '''Flatten spaces/newlines in the found string.'''
    if postfix is None:
        postfix = prefix

    def _fn(match):
        txt = match[group]
        txt = re.sub(r'\s*\n\s+', '', txt)
        txt = txt.replace(',', ', ')
        return f'{prefix}{txt}{postfix}'

    return _fn


def _flatten_re_result(match):
    txt = match[0]
    txt = re.sub(r'\s*\n\s+', '', txt)
    txt = txt.replace(',', ', ')
    return f'{match[1]}{txt}'


def _format_json(data, pretty=False):
    '''JSON with added beautification!'''
    if pretty:
        json_string = json.dumps(data, indent='\t')

        # Handle moving sets of terms onto single lines
        for term in JOIN_LINE_FIELDS:
            field_part = rf'(?:(\"(?:{term})\": [^,\n]+,?))'
            field_count = term.count('|') + 1
            full_re = r'\s+'.join([field_part] * field_count) + r'(\s+)'
            subs = ' '.join(f'\\{n+1}' for n in range(field_count)) + f'\\{field_count+1}'
            json_string = re.sub(full_re, subs, json_string)

        json_string = re.sub(JOIN_MULTIPLE_NUMBERS_REGEX, _flatten_re_result, json_string)
        json_string = re.sub(JOIN_MULTIPLE_STRINGS_REGEX, _flattener(1, '[ ', ' ]'), json_string)
        json_string = re.sub(COLLAPSE_SINGLE_LINE_DICT_REGEX, r"{ \1 }", json_string)
        json_string = re.sub(COLLAPSE_SINGLE_LINE_ARRAY_REGEX, r"[ \1 ]", json_string)
        json_string = re.sub(JOIN_COLORS_REGEX, r"[ \1, \2 ]", json_string)
    else:
        json_string = json.dumps(data, indent=None, separators=(',', ':'))
    return json_string


def save_as_json(data, filename, pretty=False):
    path = Path(filename).parent
    path.mkdir(parents=True, exist_ok=True)
    json_string = _format_json(data, pretty)
    with open(filename, 'w', newline='\n') as f:
        f.write(json_string)
