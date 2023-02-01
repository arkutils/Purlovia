from pathlib import Path

from .types import RunStatus, StatusFile

__all__ = ('load_status_cache', 'save_status_cache')

STATUS_FILE = Path('livedata/manage-status.json')
STATUS_FILE_TMP = STATUS_FILE.with_suffix('.json.tmp')


def load_status_cache() -> dict[str, RunStatus]:
    if not STATUS_FILE.exists():
        return dict()

    return StatusFile.parse_file(STATUS_FILE).__root__


def save_status_cache(status: dict[str, RunStatus]):
    data = StatusFile.parse_obj(status)
    STATUS_FILE_TMP.write_text(data.json(indent=2, exclude_unset=True, exclude_none=True))
    STATUS_FILE_TMP.replace(STATUS_FILE)
