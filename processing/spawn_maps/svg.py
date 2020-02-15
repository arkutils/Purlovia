# Creates an svg-file with spawning regions of a species colored depending on the rarity

import json
import math
import os
import re

from .consts import POINT_RADIUS, SVG_SIZE
from .intermediate_types import *
from .rarity import calculate_group_frequencies, get_rarity_for_spawn

# These CSS class names are also defined on the ARK Wiki (https://ark.gamepedia.com/MediaWiki:Common.css) and thus shouldn't be renamed here.
CSS_RARITY_CLASSES = [
    'spawningMap-very-rare', 'spawningMap-rare', 'spawningMap-very-uncommon', 'spawningMap-uncommon', 'spawningMap-common',
    'spawningMap-very-common'
]


def generate_svg_map(spawns, spawngroups, borderL, borderT, coordsW, coordsH, species_name, spawning_modifiers):
    always_untameable = 'Alpha' in species_name
    svg_output = ('<svg xmlns="http://www.w3.org/2000/svg"'
                  f' width="{SVG_SIZE}" height="{SVG_SIZE}" viewBox="0 0 {SVG_SIZE} {SVG_SIZE}"'
                  f''' class="creatureMap" style="position:absolute;">
    <defs>
        <filter id="blur" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="{round(SVG_SIZE / 100)}" />
        </filter>
        <pattern id="pattern-untameable" width="10" height="10" patternTransform="rotate(135)" patternUnits="userSpaceOnUse">'
            <rect width="4" height="10" fill="black"></rect>
        </pattern>
        <filter id="groupStroke">
            <feFlood result="outsideColor" flood-color="black"/>
            <feMorphology in="SourceAlpha" operator="dilate" radius="2"/>
            <feComposite result="strokeoutline1" in="outsideColor" operator="in"/>
            <feComposite result="strokeoutline2" in="strokeoutline1" in2="SourceAlpha" operator="out"/>
            <feGaussianBlur in="strokeoutline2" result="strokeblur" stdDeviation="1"/>
        </filter>
        '''
                  '''<style>
            .spawningMap-very-common { fill: #0F0; }
            .spawningMap-common { fill: #B2FF00; }
            .spawningMap-uncommon { fill: #FF0; }
            .spawningMap-very-uncommon { fill: #FC0; }
            .spawningMap-rare { fill: #F60; }
            .spawningMap-very-rare { fill: #F00; }
            .spawning-map-point { stroke:black; stroke-width:1; }
        </style>
    </defs>\n''')

    # The rarity is arbitrarily divided in 6 groups from "very rare" (0) to "very common" (5)
    spawn_entries_frequencies = calculate_group_frequencies(spawngroups['spawngroups'], spawning_modifiers)

    # Generate intermediate shape objects out of spawning data
    regions_by_rarity = [[] for _ in range(6)]
    points_by_rarity = [[] for _ in range(6)]
    for s in spawns['spawns']:
        # Check if spawngroup exists for current species
        if not s['locations'] or s.get('disabled', False) or 'minDesiredNumberOfNPC' not in s:
            continue

        frequency = 0
        for sef in spawn_entries_frequencies:
            if sef.path == s['spawnGroup']:
                frequency = sef.frequency
                break

        if frequency == 0:
            continue

        rarity = get_rarity_for_spawn(s, frequency)

        if 'spawnLocations' in s:
            for region in s['spawnLocations']:
                # add small border to avoid gaps
                x1 = round((region['start']['long'] - borderL) * SVG_SIZE / coordsW) - 3
                x2 = round((region['end']['long'] - borderL) * SVG_SIZE / coordsW) + 3
                y1 = round((region['start']['lat'] - borderT) * SVG_SIZE / coordsH) - 3
                y2 = round((region['end']['lat'] - borderT) * SVG_SIZE / coordsH) + 3

                regions_by_rarity[rarity].append(
                    SpawnRectangle(
                        x1,
                        y1,
                        x2 - x1,
                        y2 - y1,
                        ('Cave' in s['spawnGroup'] or 'UnderwaterGround' in s['spawnGroup']),  # TODO: is_group_in_cave()
                        (always_untameable or s['forceUntameable'])))

        if 'spawnPoints' in s:
            for point in s['spawnPoints']:
                # add small border to avoid gaps
                x = round((point['long'] - borderL) * SVG_SIZE / coordsW)
                y = round((point['lat'] - borderT) * SVG_SIZE / coordsW)
                x = min(SVG_SIZE, max(0, x))
                y = min(SVG_SIZE, max(0, y))

                points_by_rarity[rarity].append(
                    SpawnPoint(
                        x,
                        y,
                        ('Cave' in s['spawnGroup'] or 'UnderwaterGround' in s['spawnGroup']),  # TODO: is_group_in_cave()
                        (always_untameable or s['forceUntameable'])))

    untameable_regions = [r for regions in regions_by_rarity for r in regions if r.untameable]
    cave_regions = [r for regions in regions_by_rarity for r in regions if r.cave]

    has_regions = sum(len(regions) for regions in regions_by_rarity) != 0
    has_points = sum(len(points) for points in points_by_rarity) != 0
    if not has_regions and not has_points:
        return None

    # spawnRegions
    if has_regions:
        svg_output += '''
    <g filter="url(#blur)" opacity="0.7">'''
        for rarity, regions in enumerate(regions_by_rarity):
            if not regions:
                continue

            svg_output += f'''
        <g class="{CSS_RARITY_CLASSES[rarity]}">'''
            for region in regions:
                svg_output += f'''
            <rect x="{region.x}" y="{region.y}" width="{region.w}" height="{region.h}" />'''
            svg_output += '''
        </g>'''
        svg_output += '''
    </g>'''

    # spawnPoints
    if has_points:
        svg_output += '''
    <g class="spawning-map-point" opacity="0.8">'''
        for rarity, points in enumerate(points_by_rarity):
            if not points:
                continue

            svg_output += f'''
        <g class="{CSS_RARITY_CLASSES[rarity]}">'''
            for point in points:
                svg_output += f'''
            <circle cx="{point.x}" cy="{point.y}" r="{2 * POINT_RADIUS}" />'''
            svg_output += '''
        </g>'''
        svg_output += '''
    </g>'''

    # Untameable stripes (without blur)
    if untameable_regions:
        svg_output += '''
    <g fill="url(#pattern-untameable)" opacity="0.3">'''
        for region in untameable_regions:
            if region:
                svg_output += f'''
        <rect x="{region.x}" y="{region.y}" width="{region.w}" height="{region.h}"/>'''
        svg_output += '''
    </g>'''

    # Cave outlines
    if cave_regions:
        svg_output += '''
    <g filter="url(#groupStroke)" opacity="0.8">'''
        for region in cave_regions:
            svg_output += f'''
        <rect x="{region.x}" y="{region.y}" width="{region.w}" height="{region.h}"/>'''
        svg_output += '''
    </g>'''

    # end of svg
    svg_output += '''
</svg>'''
    return svg_output
