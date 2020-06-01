import json
import re
from collections import Counter
from operator import itemgetter
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Optional, Sequence

from utils.log import get_logger

MANIFEST_FILENAME = '_manifest.json'
SHRINK_MOD_REGEX = r"{\n\s+(.+: .*),\n\s+(.+: .*),\n\s+(.+: .*)\n\s+}"

__all__ = [
    'update_manifest',
    'MANIFEST_FILENAME',
]

logger = get_logger(__name__)


def update_manifest(path: Path) -> Optional[Dict[str, Any]]:
    '''Update manifest file in the output directory.'''
    manifest_file = Path(path / MANIFEST_FILENAME)

    logger.info('Updating manifest file')
    json_data = _generate_manifest(path, ignores=[MANIFEST_FILENAME])

    if json_data:
        _write_manifest(manifest_file, json_data)
    else:
        logger.info('No files present - removing existing manifest')
        if manifest_file.is_file():
            manifest_file.unlink()  # missing_ok=True is 3.8+

    return json_data


def _write_manifest(filename: Path, data: Dict[str, Any]):
    filename.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, 'w', newline='\n') as f:
        content = json.dumps(data, indent='\t')
        content = re.sub(SHRINK_MOD_REGEX, r'{ \1, \2, \3 }', content)
        f.write(content)


def _generate_manifest(directory: Path, ignores: Sequence[str] = ()) -> Optional[Dict[str, Any]]:
    '''Generate the manifest data that represents the files in a directory. Returns None if there no files.'''
    if not directory.is_dir:
        raise ValueError("Must supply a valid directory")

    # Ignored will be case insensitive to support all platforms
    ignores = [ignore.lower() for ignore in ignores]

    files: Dict[str, dict] = dict()

    # Collect info from each json file
    for filename in directory.glob('**/*.json'):
        if not filename.is_file:
            continue

        if any(ignore == filename.name.lower() for ignore in ignores):
            continue

        info = _collect_info(filename)
        if info:
            # File paths use Unix style for consistency
            key = str(PurePosixPath(filename.relative_to(directory)))
            files[key] = info

    if not files:
        return None

    # Sort by filename to ensure diff consistency
    sorted_files = dict((k, v) for k, v in sorted(files.items(), key=lambda p: p[0].lower()))

    # Pull common formats out to the top-level
    counts = Counter(mod.get('format', None) for mod in files.values())
    most_common_format = sorted(counts.items(), key=itemgetter(1), reverse=True)[0][0]
    for _, mod in files.items():
        if 'format' in mod and mod['format'] == most_common_format:
            del mod['format']

    output: Dict[str, Any] = dict()
    output['format'] = most_common_format
    output['files'] = sorted_files

    return output


def _collect_info(filename: Path) -> Dict:
    '''Collect any available manifest data about a file (version, format, metadata).'''
    with open(filename) as f:
        data = json.load(f)

    info = dict()

    ver = data.get('version', None)
    if ver:
        info['version'] = ver

    fmt = data.get('format', None)
    if fmt:
        info['format'] = fmt

    mod = data.get('mod', None)
    if mod:
        info['mod'] = mod

    metadata = data.get('metadata', None)
    if metadata:
        info['metadata'] = metadata

    return info
