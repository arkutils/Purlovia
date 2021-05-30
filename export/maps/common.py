import re
import unicodedata
from collections import namedtuple
from typing import Tuple

SVGBoundaries = namedtuple('SVGBoundaries', ('size', 'border_top', 'border_left', 'coord_width', 'coord_height'))


def remove_unicode_control_chars(s):
    return ''.join(c for c in re.sub(r'\s+', '_', s) if not unicodedata.category(c).startswith('C'))

def order_growing(a: float, b: float) -> Tuple[float, float]:
    return (min(a, b), max(a, b))
