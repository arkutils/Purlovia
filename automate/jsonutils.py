import hashlib
import json
import re
from logging import NullHandler, getLogger
from pathlib import Path
from typing import *

from ue.utils import property_serialiser

__all__ = [
    'save_json_if_changed',
    'save_as_json',
    'should_save_json',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


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
    except:  # pylint: disable=bare-except
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

    # Calculate the digest of the minified output, using SHA512
    as_bytes = _format_json(values, pretty=False).encode('utf8')
    digest = hashlib.sha512(as_bytes).hexdigest()

    return (version, digest)


JOIN_LINES_REGEX = re.compile(r"(?:\n\t+)?(?<=\t)([\d.-]+,?)(?:\n\t+)?")
JOIN_COLORS_REGEX = re.compile(r"\[\n\s+([\w\" ]+),\n\s+(.{,90})\n\s+\]")
SHRINK_EMPTY_COLOR_REGEX = re.compile(r"\{\n\s+(\"\w+\": \w+)\n\s+\}")
JOIN_XYZ_REGEX = re.compile(r"\s+(\"x\": [-.0-9]+,)\s+(\"y\": [-.0-9]+,)\s+(\"z\": [-.0-9]+)\s+")
JOIN_LON_LAT_REGEX = re.compile(r"(\"lon\": [-.0-9]+,)\s+(\"lat\": [-.0-9]+)")


def _format_json(data, pretty=False):
    if pretty:
        json_string = json.dumps(data, default=property_serialiser, indent='\t')
        json_string = re.sub(JOIN_LINES_REGEX, r" \1", json_string)
        json_string = re.sub(JOIN_XYZ_REGEX, r" \1 \2 \3 ", json_string)
        json_string = re.sub(JOIN_LON_LAT_REGEX, r"\1 \2", json_string)
        json_string = re.sub(JOIN_COLORS_REGEX, r"[ \1, \2 ]", json_string)
        json_string = re.sub(SHRINK_EMPTY_COLOR_REGEX, r"{ \1 }", json_string)
        json_string = re.sub(r'(\d)\]', r'\1 ]', json_string)
    else:
        json_string = json.dumps(data, default=property_serialiser, indent=None, separators=(',', ':'))
    return json_string


def save_as_json(data, filename, pretty=False):
    path = Path(filename).parent
    path.mkdir(parents=True, exist_ok=True)
    json_string = _format_json(data, pretty)
    with open(filename, 'w', newline='\n') as f:
        f.write(json_string)
