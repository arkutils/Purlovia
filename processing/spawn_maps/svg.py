# Creates an svg-file with spawning regions of a species colored depending on the rarity

import json
import math
import os
import re

from .consts import POINT_RADIUS, SVG_SIZE
from .intermediate_types import *

# These CSS class names are also defined on the ARK Wiki (https://ark.gamepedia.com/MediaWiki:Common.css) and thus shouldn't be renamed here.
CSS_RARITY_CLASSES = [
    'spawningMap-very-rare', 'spawningMap-rare', 'spawningMap-very-uncommon', 'spawningMap-uncommon', 'spawningMap-common',
    'spawningMap-very-common'
]


def generate_svg_map(spawns, spawngroups, borderL, borderT, coordsW, coordsH, species_name, spawning_modifiers):
    blueprints = spawning_modifiers.keys()

    always_untameable = 'Alpha' in species_name
    svgOutput = ('<svg xmlns="http://www.w3.org/2000/svg"'
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
    rarity_regions = [[] for _ in range(6)]
    rarity_points = [[] for _ in range(6)]
    spawn_entries_frequencies = []

    # spawngroups
    for g in spawngroups['spawngroups']:
        if 'entries' not in g:
            continue
        frequency = g['maxNPCNumberMultiplier']
        entry_frequency_sum = 0

        total_group_weights = sum(entry['weight'] for entry in g['entries']) or 1

        for entry in g['entries']:
            if 'classes' not in entry or len(entry['classes']) == 0:
                continue

            # Check all entries for the current blueprint
            # Some groups have multiple entries for the same blueprint
            spawn_indices = []
            for index, npc_spawn in enumerate(entry['classes']):
                # TODO: Review later. npc_spawn is an str. Object path format differs between ASB and wiki. Perhaps this is already solved in make_species_mapping_from_asb?
                if npc_spawn in blueprints:
                    spawn_indices.append((index, spawning_modifiers[npc_spawn]))

            # Calculate total weight of classes in the spawning group
            if entry['classWeights']:
                total_entry_class_weights = sum(entry['classWeights']) or 1
            else:
                total_entry_class_weights = len(entry['classes']) or 1
            entry_class_chances_data = [weight / total_entry_class_weights for weight in entry['classWeights']]

            entry_class_chance = 0  # The combined chance of all entries for current blueprint
            for index, modifier in spawn_indices:
                if len(entry['classWeights']) > index:
                    entry_class_chance += entry_class_chances_data[index] * modifier
                # assume default weight of 1 if there is no specific value
                else:
                    entry_class_chance += 1
            entry_class_chance *= (entry['weight'] / total_group_weights)
            entry_frequency_sum += entry_class_chance

        frequency *= entry_frequency_sum
        if frequency > 0:
            spawn_entries_frequencies.append(SpawnFrequency(g['blueprintPath'], frequency))

    # spawns
    regionSpawnsExist = False
    pointSpawnsExist = False
    for s in spawns['spawns']:
        # Check if spawngroup exists for current species
        if not s.get('locations', None) or s.get('disabled', False) or 'minDesiredNumberOfNPC' not in s:
            continue

        frequency = 0
        for sef in spawn_entries_frequencies:
            if sef.path == s['spawnGroup']:
                frequency = sef.frequency
                break

        if frequency == 0:
            continue

        number = frequency * s['minDesiredNumberOfNPC']
        # Calculate density from number of creatures and area
        creatureDensity = number / ((s['locations'][0]['end']['long'] - s['locations'][0]['start']['long']) *
                                    (s['locations'][0]['end']['lat'] - s['locations'][0]['start']['lat']))
        # This formula is arbitrarily constructed to create 5 naturally feeling groups of rarity 0..5 (very rare to very common)
        rarity = round(1.5 * (math.log(1 + 50*creatureDensity)))
        if rarity > 5:
            rarity = 5

        # TODO: Check for locations going out of the map region (lat/long over 100)
        if 'spawnLocations' in s:
            for region in s['spawnLocations']:
                # add small border to avoid gaps
                xStart = round((region['start']['long'] - borderL) * SVG_SIZE / coordsW) - 3
                xEnd = round((region['end']['long'] - borderL) * SVG_SIZE / coordsW) + 3
                yStart = round((region['start']['lat'] - borderT) * SVG_SIZE / coordsH) - 3
                yEnd = round((region['end']['lat'] - borderT) * SVG_SIZE / coordsH) + 3

                rarity_regions[rarity].append(
                    SpawnRectangle(xStart, yStart, xEnd - xStart, yEnd - yStart,
                                   ('Cave' in s['spawnGroup'] or 'UnderwaterGround' in s['spawnGroup']),
                                   (always_untameable or s['forceUntameable'])))
                regionSpawnsExist = True

        if 'spawnPoints' in s:
            for point in s['spawnPoints']:
                # add small border to avoid gaps
                x = round((point['long'] - borderL) * SVG_SIZE / coordsW)
                y = round((point['lat'] - borderT) * SVG_SIZE / coordsW)
                if x < 0:
                    x = 0
                if x > SVG_SIZE:
                    x = SVG_SIZE
                if y < 0:
                    y = 0
                if y > SVG_SIZE:
                    y = SVG_SIZE

                rarity_points[rarity].append(
                    SpawnPoint(x, y, ('Cave' in s['spawnGroup'] or 'UnderwaterGround' in s['spawnGroup']),
                               (always_untameable or s['forceUntameable'])))
                pointSpawnsExist = True

    untameableRegionsExist = False
    caveRegionsExist = False

    # spawnRegions
    if regionSpawnsExist:
        svgOutput += '<g filter="url(#blur)" opacity="0.7">'
        cssRarity = -1
        for rarityRegions in rarity_regions:
            cssRarity += 1
            if len(rarityRegions) == 0:
                continue
            svgOutput += '<g class="' + CSS_RARITY_CLASSES[cssRarity] + '">'
            for region in rarityRegions:
                svgOutput += '<rect x="' + str(region.x) + '" y="' + str(region.y) + '" width="' + str(
                    region.w) + '" height="' + str(region.h) + '" />'
                if region.untameable:
                    untameableRegionsExist = True
                if region.cave:
                    caveRegionsExist = True

            svgOutput += '</g>'
        svgOutput += '</g>\n'

    # spawnPoints
    if pointSpawnsExist:
        svgOutput += '<g class="spawning-map-point" opacity="0.8">'
        cssRarity = -1
        for rarityPoints in rarity_points:
            cssRarity += 1
            if len(rarityPoints) == 0:
                continue
            svgOutput += f'<g class="{CSS_RARITY_CLASSES[cssRarity]}">'
            for point in rarityPoints:
                svgOutput += f'<circle cx="{point.x}" cy="{point.y}" r="{2 * POINT_RADIUS}" />'
                if point.untameable:
                    untameableRegionsExist = True
                if point.cave:
                    caveRegionsExist = True

            svgOutput += '</g>'
        svgOutput += '</g>\n'

    # untameable stripes (without blurfilter)
    if untameableRegionsExist:
        svgOutput += '\n<g fill="url(#pattern-untameable)" opacity="0.3">'
        for rarityRegions in rarity_regions:
            for region in rarityRegions:
                if region.untameable:
                    svgOutput += '<rect x="' + str(region.x) + '" y="' + str(region.y) + '" width="' + str(
                        region.w) + '" height="' + str(region.h) + '"/>'
        svgOutput += '</g>'

    # cave outlines
    if caveRegionsExist:
        caveOutlineRegions = ''
        for rarityRegions in rarity_regions:
            for region in rarityRegions:
                if region.cave:
                    caveOutlineRegions += '<rect x="' + str(region.x) + '" y="' + str(region.y) + '" width="' + str(
                        region.w) + '" height="' + str(region.h) + '"/>'
        if len(caveOutlineRegions) > 0:
            svgOutput += '\n<g filter="url(#groupStroke)" opacity="0.8">' + caveOutlineRegions + '</g>'

    # end of svg
    svgOutput += '</svg>'
    if not regionSpawnsExist and not pointSpawnsExist:
        return None
    return svgOutput
