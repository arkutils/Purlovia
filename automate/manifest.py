import json
import re
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

    data: Dict[str, dict] = dict()

    # Collect info from each json file
    for filename in directory.glob('*.json'):
        if not filename.is_file:
            continue

        if any(ignore == filename.name.lower() for ignore in ignores):
            continue

        info = _collect_info(filename)
        if info:
            key = str(filename.relative_to(directory))
            data[key] = info

    # Try to make directory the file lives in
    if not output_file.parent.is_dir:
        output_file.parent.mkdirs(parents=True, exists_ok=True)

    # Sort by filename to ensure diff consistency
    sorted_data = dict((k, v) for k, v in sorted(data.items(), key=itemgetter(0)))

    # Save
    with open(output_file, 'w') as f:
        json.dump(sorted_data, f, indent='\t')


def _collect_info(filename: Path) -> Dict:
    with open(filename) as f:
        data = json.load(f)

    info = dict()

    ver = data.get('version', None)
    if ver:
        info['version'] = ver

    fmt = data.get('formatVersion', None)
    if fmt:
        info['format'] = fmt

    mod = data.get('mod', None)
    if mod:
        info['mod'] = mod

    return info
