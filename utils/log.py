import os
import zlib
from logging import NullHandler, getLogger
from logging.handlers import RotatingFileHandler

from config import ROOT_LOGGER

__all__ = [
    'CompressedRotatingFileHandler',
    'get_logger',
]


class CompressedRotatingFileHandler(RotatingFileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namer = namer_gz
        self.rotator = rotator_gz


def namer_gz(filename: str):
    return filename + '.gz'


def rotator_gz(source: str, dest: str):
    with open(source, "rb") as sf:
        with open(dest, "wb") as df:
            zf = zlib.compressobj(level=8, wbits=28)  # wbits important to get a file header

            while True:
                data = sf.read(64 * 1024 * 1024)
                if not data:
                    break

                data = zf.compress(data)
                df.write(data)

            data = zf.flush(zlib.Z_FINISH)
            df.write(data)

    os.remove(source)


def get_logger(name):
    logger = getLogger(ROOT_LOGGER + name)  # pylint: disable=invalid-name
    logger.addHandler(NullHandler())

    return logger
