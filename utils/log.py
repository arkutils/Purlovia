import os
import zlib
from logging.handlers import RotatingFileHandler

__all__ = [
    'CompressedRotatingFileHandler',
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
