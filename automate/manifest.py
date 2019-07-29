import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from logging import NullHandler, getLogger
from operator import itemgetter
from pathlib import Path
from typing import *

from config import get_global_config

__all__ = [
    'update_manifest',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())

DEFAULT_IGNORES = ('_manifest.json', )
SHRINK_MOD_REGEX = r"{\n\s+(.+: .*),\n\s+(.+: .*),\n\s+(.+: .*)\n\s+}"


def update_manifest(config=get_global_config()):
    '''Update manifest file in the exports directory.'''
    outdir = config.settings.PublishDir
    manifest = outdir / '_manifest.json'

    logger.info('Updating manifest file')
    generate_manifest(outdir, manifest, ignores=['_manifest.json'])


def generate_manifest(directory: Path, output_file: Path, ignores: Sequence[str] = DEFAULT_IGNORES):
    if not directory.is_dir:
        raise ValueError("Must supply a valid directory")
    if not output_file.suffix.endswith('.json'):
        raise ValueError("Output file must be json")

    files: Dict[str, dict] = dict()

    # Collect info from each json file
    for filename in directory.glob('*.json'):
        if not filename.is_file:
            continue

        if any(ignore == filename.name.lower() for ignore in ignores):
            continue

        info = _collect_info(filename)
        if info:
            key = str(filename.relative_to(directory))
            files[key] = info

    # Try to make directory the file lives in
    if not output_file.parent.is_dir:
        output_file.parent.mkdirs(parents=True, exists_ok=True)

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

    # Save
    with open(output_file, 'w', newline='\n') as f:
        content = json.dumps(output, indent='\t')
        content = re.sub(SHRINK_MOD_REGEX, r'{ \1, \2, \3 }', content)
        f.write(content)


def _collect_info(filename: Path) -> Dict:
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

    return info
