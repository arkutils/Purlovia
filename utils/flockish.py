from __future__ import annotations

import atexit
import os
import signal
import sys
from pathlib import Path
from time import sleep

import psutil

from utils.log import get_logger

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

    logger.info('Trying to claim lock file %s for PID %s', LOCK_FILE, os.getpid())
    if not _create_lock():
        logger.debug("Lock already exists - checking if it's stale")
        if _should_retry_lock():
            logger.debug("Lock is stale, retrying")
            if not _create_lock():
                raise RuntimeError("Failed to claim process lock")
        else:
            raise RuntimeError("Failed to claim process lock")

    we_claimed_lock = True

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
    logger.debug("Attempting to create lock file")
    try:
        with LOCK_FILE.open('xt') as f:
            f.writelines([
                f'{os.getpid()}\n',
                f'{int(psutil.Process(os.getpid()).create_time())}\n',
            ])
            f.write('\n')
        logger.info("Process lock claimed")
    except FileExistsError:
        logger.warning("Process lock already exists")
        return False

    return True


def _read_lock_file() -> tuple[int, int]:
    logger.debug("Reading lock file")
    lines = LOCK_FILE.read_text().strip().splitlines()
    if len(lines) != 2:
        raise ValueError("Lock file is invalid")
    values = map(int, lines)
    pid, create_time = values
    return pid, create_time


def _should_retry_lock() -> bool:
    '''
    Returns True if a lock either does not exist or is stale.
    '''
    try:
        locked_pid, create_time = _read_lock_file()
        logger.info(f"Existing lock is for PID {locked_pid} @ {create_time}")

        # Lock is stale if the process with this PID does not exist or match the create_time
        proc = psutil.Process(locked_pid)
        if int(proc.create_time()) != create_time:
            logger.info("Locked PID does not match recorded create_time - it is stale")
            LOCK_FILE.unlink()
            return True
        logger.info("Locked PID matches create_time - it is valid")
        return False
    except FileNotFoundError:
        logger.debug("Lock file does not exist")
        return True
    except ValueError:
        logger.info("Lock file is empty or invalid, removing")
        LOCK_FILE.unlink()
        return True
    except psutil.NoSuchProcess:
        logger.info("Process does not exist, removing lock")
        LOCK_FILE.unlink()
        return True
    except Exception as ex:
        logger.info("Unknown exception during lock check", exc_info=ex)
        return False


def _release_lock():
    '''
    Release the lock file if we claimed it, first checking we still own it.
    It is safe to call this method multiple times.
    '''
    global already_released, we_claimed_lock

    # Siletly bail if we never claimed the lock or have already released it
    if already_released or not we_claimed_lock:
        return

    # Verify we still own the lock
    try:
        locked_pid, _ = _read_lock_file()
        if locked_pid != os.getpid():
            logger.debug("Lock is for another process")
            raise RuntimeError("Our process lock was stolen while we ran")
    except FileNotFoundError:
        logger.debug("Lock file does not exist, not releasing")
        return

    LOCK_FILE.unlink()
    logger.info("Process lock released")
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
