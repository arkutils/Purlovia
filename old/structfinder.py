import os
import sys
import mmap
import struct
from operator import xor
from itertools import cycle

from hexutils import *

# KEY = bytes.fromhex('00 00 12 34') # unknown endian
KEY = bytes.fromhex('34 12 00 00')  # opposite endian


def files_in(path, ending=None, recurse=False):
    path = os.path.abspath(path)

    for root, _, files in os.walk(path):
        for name in files:
            if not ending or name.endswith(ending):
                yield os.path.join(root, name)

        if not recurse:
            return


def find_values_in_binary(values, fmttype, data, endian='<'):
    '''
    Looks for the given string of values in the given format with the data supplied.
    This is a generator that yields a tuple for each result found, of the format:
        (offset, found_values, was_xored)

    Example:
    >>> list(find_values_in_binary([0x11, 0x22], 'B', bytes.fromhex('00 11 22 00')))
    [(1, (17, 34), False)]
    '''
    fmt = endian + fmttype * len(values)
    fmtlen = struct.calcsize(fmt)
    filelen = len(data)

    match_point = 0
    while match_point <= filelen - fmtlen:
        data_part = data[match_point:match_point + fmtlen]
        these_values = struct.unpack(fmt, data_part)
        if are_nearly_equal(these_values, values):
            yield match_point, these_values, False

        xor_data_part = xor_bytes(data_part, KEY)
        these_values = struct.unpack(fmt, xor_data_part)
        if are_nearly_equal(these_values, values):
            yield match_point, these_values, True

        match_point += 1


def search_files_for_values(path, values, fmttype):
    for filename in files_in(path, recurse=True):
        print(f"{os.path.basename(filename)}")

        with open(os.path.join(path, filename), 'rb') as f:
            data = f.read()
            for offset, values, was_xor in find_values_in_binary(values, fmttype, data):
                print(f'\t{offset} {was_xor}')


if __name__ == '__main__':
    path = r'K:\SteamLibrary\steamapps\common\ARK\ShooterGame\Content\PrimalEarth\Dinos\Dodo'
    # path = r'K:\SteamLibrary\steamapps\common\ARK\ShooterGame\Content\PrimalEarth\Dinos\BaseBPs'
    # path = r'K:\SteamLibrary\steamapps\common\ARK\ShooterGame\Content\PrimalEarth\Dinos'
    values = (40, 100, 30)

    print("\nSearching for floats:", values)
    search_files_for_values(path, values, 'f')

    print("\nSearching for ints:", values)
    search_files_for_values(path, values, 'i')
