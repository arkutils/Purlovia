from __future__ import annotations

import atexit
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from time import sleep

import psutil

from utils.log import get_logger

__all__ = (
    'set_lock_path',
    'ensure_process_lock',
)

LOCK_FILE: Path = None  # type: ignore # we verify this is set before use

logger = get_logger(__name__)

# sys.exit triggers atexit handlers
# os._exit does not trigger atexit handlers
# os.kill does not trigger atexit handlers
# os.abort does not trigger atexit handlers
# some signals do not trigger atexit handlers
#
# So we register atexit and various signal handlers to make sure we cover all possible cases
we_claimed_lock = False
'''True if this process claimed its process lock'''
already_released = False
'''True if we have already released the lock'''

_lock_file_handle = None
_our_details: tuple[int, int] | None = None


def set_lock_path(path: str) -> None:
    global LOCK_FILE
    if LOCK_FILE is not None:
        raise RuntimeError("Lock path already set")
    LOCK_FILE = Path(path)


def ensure_process_lock():
    '''
    Ensure only one instance of this process is running at a time.
    '''
    if not LOCK_FILE:
        raise ValueError("Lock file path not set")

    global we_claimed_lock
    if we_claimed_lock:
        return

    if not _create_lock():
        locked_pid, locked_create_time = _read_lock_file()
        logger.error("Lock %s already exists for PID %s @ %d (%s)", LOCK_FILE, locked_pid, locked_create_time,
                     datetime.fromtimestamp(locked_create_time))
        raise RuntimeError("Failed to claim process lock")

    we_claimed_lock = True

    our_pid, our_create_time = _our_details
    logger.info("Claimed %s for PID %s @ %d (%s)", LOCK_FILE, our_pid, our_create_time, datetime.fromtimestamp(our_create_time))

    atexit.register(_release_lock)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGSEGV, signal_handler)
    if sys.platform == 'win32':
        signal.signal(signal.SIGBREAK, signal_handler)
    elif sys.platform == 'linux':
        signal.signal(signal.SIGILL, signal_handler)
        signal.signal(signal.SIGBUS, signal_handler)
        signal.signal(signal.SIGQUIT, signal_handler)


def _create_lock() -> bool:
    global _lock_file_handle, _our_details
    assert _lock_file_handle is None

    logger.debug("Attempting to create lock file")
    try:
        f = LOCK_FILE.open('xt')
        _our_details = (os.getpid(), int(psutil.Process(os.getpid()).create_time()))
        f.writelines([f'{line}\n' for line in _our_details])
        f.flush()
        os.fsync(f.fileno())
        logger.debug("Process lock claimed")
    except FileExistsError:
        logger.debug("Process lock already exists")
        return False

    _lock_file_handle = f

    return True


def _read_lock_file() -> tuple[int, int]:
    logger.debug("Reading lock file")
    lines = LOCK_FILE.read_text().strip().splitlines()
    if len(lines) != 2:
        raise ValueError("Lock file is invalid")
    values = map(int, lines)
    pid, create_time = values
    return pid, create_time


def _release_lock():
    '''
    Release the lock file if we claimed it, first checking we still own it.
    It is safe to call this method multiple times.
    '''
    global already_released, we_claimed_lock, _lock_file_handle

    # Silently bail if we never claimed the lock or have already released it
    if already_released or not we_claimed_lock:
        return

    assert _lock_file_handle is not None

    # Verify we still own the lock
    try:
        our_pid, our_create_time = _our_details
        locked_pid, locked_create_time = _read_lock_file()
        if locked_pid != our_pid:
            logger.debug("Lock is for another process (pid=%s, create_time=%s)", locked_pid, locked_create_time)
            raise RuntimeError("Our process lock was stolen while we ran (PID mismatch)")
        if locked_create_time != our_create_time:
            logger.debug("Lock is for our process but create time does not match (pid=%s, create_time=%s)", locked_pid,
                         locked_create_time)
            raise RuntimeError("Our process lock was stolen while we ran (create time mismatch)")
    except FileNotFoundError:
        logger.error("Lock file does not exist, not releasing")
        return

    # Close the lock file handle and remove the file
    _lock_file_handle.close()
    _lock_file_handle = None
    LOCK_FILE.unlink()
    logger.info("Lock %s verified and released", LOCK_FILE)
    already_released = True


def signal_handler(signum: int, frame):
    sig = signal.Signals(signum)
    logger.warning("Signal handler called with signal %s", sig.name)
    try:
        _release_lock()
    except:  # noqa: E722 bare except is good here as we're in a signal handler
        logger.error("Failed to release lock, aborting anyway")

    signal.default_int_handler(signum, frame)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    ensure_process_lock()
    print("Sleeping")
    sleep(5)  # to test Ctrl-C, etc
    print('Clean exit')
