import re
import unicodedata
from collections import namedtuple
from typing import Tuple

from ark.overrides import get_overrides_for_map

from .spawns_consts import SVG_SIZE

SVGBoundaries = namedtuple('SVGBoundaries', ('size', 'border_top', 'border_left', 'coord_width', 'coord_height'))


def remove_unicode_control_chars(s):
    return ''.join(c for c in re.sub(r'\s+', '_', s) if not unicodedata.category(c).startswith('C'))


def get_svg_bounds_for_map(persistent_level: str) -> SVGBoundaries:
    config = get_overrides_for_map(persistent_level, None).svgs
    bounds = SVGBoundaries(
        size=SVG_SIZE,
        border_top=config.border_top,
        border_left=config.border_left,
        coord_width=config.border_right - config.border_left,
        coord_height=config.border_bottom - config.border_top,
    )
    return bounds


def order_growing(a: float, b: float) -> Tuple[float, float]:
    return (min(a, b), max(a, b))
