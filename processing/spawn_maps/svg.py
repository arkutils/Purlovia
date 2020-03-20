'''
Creates an svg-file with spawning regions of a species colored depending on the rarity.
'''

from typing import List

from processing.common import SVGBoundaries

from .consts import POINT_RADIUS
from .intermediate_types import SpawnPoint, SpawnRectangle
from .species import get_rarity_for_spawn

# These CSS class names are also defined on the ARK Wiki (https://ark.gamepedia.com/MediaWiki:Common.css) and thus shouldn't be renamed here.
CSS_RARITY_CLASSES = [
    'spawningMap-very-rare', 'spawningMap-rare', 'spawningMap-very-uncommon', 'spawningMap-uncommon', 'spawningMap-common',
    'spawningMap-very-common'
]


def is_group_in_cave(path):
    return 'Cave' in path or 'UnderwaterGround' in path


def find_frequency_for_group(frequency_set, group_path) -> float:
    for sef in frequency_set:
        if sef.path == group_path:
            return sef.frequency

    return 0


def build_shapes(bounds: SVGBoundaries, spawns, spawn_entries_frequencies, always_untameable):
    v_regions: List[List[SpawnRectangle]] = [[] for _ in range(6)]
    v_points: List[List[SpawnPoint]] = [[] for _ in range(6)]
    for s in spawns['spawns']:
        # Check if spawngroup exists for current species
        if not s['locations'] or s.get('disabled', False) or 'minDesiredNumberOfNPC' not in s:
            continue

        frequency = find_frequency_for_group(spawn_entries_frequencies, s['spawnGroup'])
        if frequency == 0:
            continue

        rarity = get_rarity_for_spawn(s, frequency)

        if 'spawnLocations' in s:
            for region in s['spawnLocations']:
                # Add small border to avoid gaps
                x1 = round((region['start']['long'] - bounds.border_left) * bounds.size / bounds.coord_width) - 3
                x2 = round((region['end']['long'] - bounds.border_left) * bounds.size / bounds.coord_width) + 3
                y1 = round((region['start']['lat'] - bounds.border_top) * bounds.size / bounds.coord_height) - 3
                y2 = round((region['end']['lat'] - bounds.border_top) * bounds.size / bounds.coord_height) + 3

                # Clamp the values
                x1 = min(bounds.size, max(0, x1))
                x2 = min(bounds.size, max(0, x2))
                y1 = min(bounds.size, max(0, y1))
                y2 = min(bounds.size, max(0, y2))

                # Make sure the order is right
                if x1 > x2:
                    x2, x1 = x1, x2
                if y1 > y2:
                    y2, y1 = y1, y2

                w = x2 - x1
                h = y2 - y1
                untameable = always_untameable or s['forceUntameable']

                # Skip if the volume does not cover a non-zero area
                if w == 0 or h == 0:
                    continue

                v_regions[rarity].append(SpawnRectangle(x1, y1, w, h, is_group_in_cave(s['spawnGroup']), untameable))

        if 'spawnPoints' in s:
            for point in s['spawnPoints']:
                # Add small border to avoid gaps
                x = round((point['long'] - bounds.border_left) * bounds.size / bounds.coord_width)
                y = round((point['lat'] - bounds.border_top) * bounds.size / bounds.coord_height)

                if x < 0 or y < 0 or x > bounds.size or y > bounds.size:
                    # Out of bounds, skip
                    continue

                x = min(bounds.size, max(0, x))
                y = min(bounds.size, max(0, y))
                untameable = always_untameable or s['forceUntameable']

                v_points[rarity].append(SpawnPoint(x, y, is_group_in_cave(s['spawnGroup']), untameable))

    return v_regions, v_points


def _generate_svg_spawn_regions(rarity_sets):
    svg_output = '\n<g filter="url(#blur)" opacity="0.7">'
    for rarity, regions in enumerate(rarity_sets):
        if not regions:
            continue

        svg_output += f'\n<g class="{CSS_RARITY_CLASSES[rarity]}">'
        for region in regions:
            svg_output += f'\n<rect x="{region.x}" y="{region.y}" width="{region.w}" height="{region.h}" />'
        svg_output += '\n</g>'
    svg_output += '\n</g>'
    return svg_output


def _generate_svg_spawn_points(rarity_sets):
    svg_output = '\n<g class="spawning-map-point" opacity="0.8">'
    for rarity, points in enumerate(rarity_sets):
        if not points:
            continue

        svg_output += f'\n<g class="{CSS_RARITY_CLASSES[rarity]}">'
        for point in points:
            svg_output += f'\n<circle cx="{point.x}" cy="{point.y}" r="{2 * POINT_RADIUS}" />'
        svg_output += '\n</g>'
    svg_output += '\n</g>'
    return svg_output


def _generate_svg_untameables(rarity_sets):
    untameable_regions = [r for regions in rarity_sets for r in regions if r.untameable]
    if untameable_regions:
        svg_output = '\n<g fill="url(#pattern-untameable)" opacity="0.3">'
        for region in untameable_regions:
            svg_output += f'\n<rect x="{region.x}" y="{region.y}" width="{region.w}" height="{region.h}"/>'
        svg_output += '\n</g>'
        return svg_output
    return ''


def _generate_svg_caves(rarity_sets):
    cave_regions = [r for regions in rarity_sets for r in regions if r.cave]
    if cave_regions:
        svg_output = '\n<g filter="url(#groupStroke)" opacity="0.8">'
        for region in cave_regions:
            svg_output += f'\n<rect x="{region.x}" y="{region.y}" width="{region.w}" height="{region.h}"/>'
        svg_output += '\n</g>'
        return svg_output
    return ''


def generate_svg_map(bounds: SVGBoundaries, spawn_freqs, spawns, force_untameable):
    svg_output = \
f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{bounds.size}" height="{bounds.size}"
        viewBox="0 0 {bounds.size} {bounds.size}" class="creatureMap" style="position:absolute;">
    <defs>
        <filter id="blur" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="{round(bounds.size / 100)}" />
        </filter>
        <pattern id="pattern-untameable" width="10" height="10" patternTransform="rotate(135)" patternUnits="userSpaceOnUse">
            <rect width="4" height="10" fill="black"></rect>
        </pattern>
        <filter id="groupStroke">
            <feFlood result="outsideColor" flood-color="black"/>
            <feMorphology in="SourceAlpha" operator="dilate" radius="2"/>
            <feComposite result="strokeoutline1" in="outsideColor" operator="in"/>
            <feComposite result="strokeoutline2" in="strokeoutline1" in2="SourceAlpha" operator="out"/>
            <feGaussianBlur in="strokeoutline2" result="strokeblur" stdDeviation="1"/>
        </filter>
        <style>
            .spawningMap-very-common {{ fill: #0F0; }}
            .spawningMap-common {{ fill: #B2FF00; }}
            .spawningMap-uncommon {{ fill: #FF0; }}
            .spawningMap-very-uncommon {{ fill: #FC0; }}
            .spawningMap-rare {{ fill: #F60; }}
            .spawningMap-very-rare {{ fill: #F00; }}
            .spawning-map-point {{ stroke:black; stroke-width:1; }}
        </style>
    </defs>
'''

    # Generate intermediate shape objects out of spawning data
    regions_by_rarity, points_by_rarity = build_shapes(bounds, spawns, spawn_freqs, force_untameable)

    has_regions = sum(len(regions) for regions in regions_by_rarity) != 0
    has_points = sum(len(points) for points in points_by_rarity) != 0
    if not has_regions and not has_points:
        return None

    # Generate SVG rects and circles from the shapes
    if has_regions:
        svg_output += _generate_svg_spawn_regions(regions_by_rarity)
    if has_points:
        svg_output += _generate_svg_spawn_points(points_by_rarity)

    # Untameable stripes (without blur)
    svg_output += _generate_svg_untameables(regions_by_rarity)

    # Cave outlines
    svg_output += _generate_svg_caves(regions_by_rarity)

    # end of svg
    svg_output += '\n</svg>'
    return svg_output
