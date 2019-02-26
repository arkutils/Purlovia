import os
import sys
import mmap
import math
import struct
from operator import xor
from itertools import cycle
from types import SimpleNamespace as Bag

ERROR_MARGIN = 1E-3


def bytes_to_hex(data):
    a = 3*2 + 1
    return ' '.join(f'{v:02X}' for v in data)


def bytes_from_floats(*floats):
    '''
	>>> assert bytes_from_floats(120) == bytes.fromhex('00 00 F0 42')
	>>> assert bytes_from_floats(1.1, 1.2) == bytes.fromhex('CD CC 8C 3F 9A 99 99 3F')
	'''
    return struct.pack('<' + 'f' * len(floats), *floats)


def xor_bytes(data, key):
    '''
	>>> xor_bytes(b'B', b'\x01')
	b'C'
	>>> xor_bytes(b'BC', b'\x01')
	b'CB'
	>>> xor_bytes(b'BB', b'\x01\x02')
	b'C@'
	>>> xor_bytes(b'BB', b'\x01\x02\x03')
	b'C@'
	'''
    return bytes(xor_bytes_gen(data, key))


def xor_bytes_gen(data, key):
    for a, b in zip(data, cycle(key)):
        yield xor(a, b)


def rotate_bytes(value):
    '''
	>>> list(rotate_bytes(b'A'))
	[b'A']
	>>> list(rotate_bytes(b'AB'))
	[b'AB', b'BA']
	>>> list(rotate_bytes(b'ABC'))
	[b'ABC', b'BCA', b'CAB']
	>>> list(rotate_bytes(b'ABCD'))
	[b'ABCD', b'BCDA', b'CDAB', b'DABC']
	'''
    l = len(value)
    for start in range(l):
        yield value[start:] + value[:start]


def are_nearly_equal(a, b):
    '''
	>>> are_nearly_equal([1], [])
	False
	>>> are_nearly_equal([], [1])
	False
	>>> are_nearly_equal([1], [1])
	True
	>>> are_nearly_equal([1.1], [1.1])
	True
	>>> are_nearly_equal([1.1], [1.10001])
	True
	>>> are_nearly_equal([1.1], [1.1001])
	True
	>>> are_nearly_equal([1.1], [1.101])
	True
	>>> are_nearly_equal([1.1], [1.11])
	False
	'''
    if len(a) != len(b): return False
    return all(abs(x - y) <= ERROR_MARGIN for x, y in zip(a, b))


def as_hex_bytes(mem, endian):
    values = (results[0] for results in struct.iter_unpack(endian + 'B', mem))
    return ('uint8', 1, (f'{v:02X}' for v in values))


def as_int8s(mem, endian):
    values = (results[0] for results in struct.iter_unpack(endian + 'b', mem))
    return ('uint8', 1, (f'{v:+g}' for v in values))


def as_ascii(mem, endian, fallback='.'):
    values = (results[0] for results in struct.iter_unpack(endian + 'B', mem))
    values = ('.' if v < 32 or v > 127 else chr(v) for v in values)
    return ('ascii', 1, values)


def as_hex_uint32s(mem, endian):
    values = (results[0] for results in struct.iter_unpack(endian + 'I', mem))
    return ('uint32', 4, (f'{v:08X}' for v in values))


def as_uint32s(mem, endian):
    values = (results[0] for results in struct.iter_unpack(endian + 'I', mem))
    return ('uint32', 4, (f'{v}' for v in values))


def as_int32s(mem, endian):
    values = (results[0] for results in struct.iter_unpack(endian + 'i', mem))
    return ('int32', 4, (f'{v:+g}' for v in values))


def as_hex_int32s(mem, endian):
    values = (results[0] for results in struct.iter_unpack(endian + 'i', mem))
    return ('int32', 4, (f'{v:+08X}' for v in values))


def as_floats(mem, endian):
    values = (results[0] for results in struct.iter_unpack(endian + 'f', mem))
    return ('float', 4, (f'{v:+g}' for v in values))


def accumulate_for_n(input, n):
    a = 0
    i = n
    for v in input:
        a += v
        i -= 1
        if i <= 0:
            yield a
            a = 0
            i = n


def display_mem(mem, *formats, endian='<'):
    results = [formatter(mem, endian) for formatter in formats]
    results = [(title, size, list(values)) for title, size, values in results]
    title_width = max(len(title) for title, size, values in results) + 1
    min_bytes = min(size for title, size, values in results)
    max_bytes = max(size for title, size, values in results)
    stride = max_bytes // min_bytes
    max_width = max(max(accumulate_for_n((len(v) + 1 for v in values), max_bytes // size)) for title, size, values in results)

    for title, size, values in results:
        print(f'{title:>{title_width}}: ', end='')
        pos = 0
        for i, v in enumerate(values):
            next_pos = (i+1) * math.ceil(max_width / stride) * size
            width = next_pos - pos
            print(f'{v:>{width}}', end='')
            pos = next_pos
        print()


def load_file_into_memory(filename):
    with open(filename, 'rb') as f:
        data = f.read()
        mem = memoryview(data)
        return mem


def first(seq, predicate):
    try:
        return next(x for x in seq if predicate(x))
    except StopIteration:
        return None

def reinterpret_as_float(v):
    return struct.unpack('<f', struct.pack('<I', v))[0]
