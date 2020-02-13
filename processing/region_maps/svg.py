# Creates an svg-file with regions that contain links to the according region-page (used on the ARK: Survival evolved Wiki)

import html
import json
import math
import re

from .func import coordTrans, make_biome_article_name, map_translate_coord

REGEX_INVALID_BIOME = re.compile(r'^\?+$')


def generate_svg_map(map_name, world_settings, biomes, map_size, borderL, borderT, coordsW, coordsH, follow_mod_convention):
    svg_output = (
        '<svg xmlns="http://www.w3.org/2000/svg"'
        f''' width="{map_size}" height="{map_size}" viewBox="0 0 {map_size} {map_size}" style="position: absolute; width:100%; height:100%;">
<defs>
    <filter id="blur" x="-30%" y="-30%" width="160%" height="160%">'
        <feColorMatrix type="matrix" values="1 0 0 1 0, 0 1 0 0 0, 0 0 1 0 0, 0 0 0 0.7 0"/>
        <feGaussianBlur stdDeviation="10" />
    </filter>
</defs>\n''')

    # Remove regions without regions or if the name is only \?+, namefixes
    # TODO: Split into other function
    valid_biomes = []
    for biome in biomes['biomes']:
        if not biome['boxes'] or not biome['name'].strip() or REGEX_INVALID_BIOME.search(biome['name']):
            continue

        if biome['name'] == 'Underwater':
            biome['priority'] = -1
            # Remove underwater regions in the middle of the map
            valid_boxes = []
            for box in biome['boxes']:
                if not ((box['start']['x'] > -300000 and box['end']['x'] < 300000) and
                        (box['start']['y'] > -300000 and box['end']['y'] < 300000)):
                    valid_boxes.append(box)
            biome['boxes'] = valid_boxes
        elif biome['name'] == 'Deep Ocean':
            biome['priority'] = -2

        valid_biomes.append(biome)

    # Combine regions with the same name
    index = 0
    biome_count = len(valid_biomes)
    while index < biome_count:
        j = index + 1
        while j < biome_count:
            if valid_biomes[index]['name'] == valid_biomes[j]['name']:
                valid_biomes[index]['boxes'] = valid_biomes[index]['boxes'] + valid_biomes[j]['boxes']
                del valid_biomes[j]
                biome_count -= 1
            else:
                j += 1
        index += 1

    # Sort biomes by priority
    valid_biomes.sort(key=lambda biome: biome['priority'], reverse=False)

    textX = map_size / 2
    textY = 60

    # Create svg
    for biome in valid_biomes:
        svg_output += f'''<a href="{make_biome_article_name(map_name, biome['name'], follow_mod_convention)}" class="svgRegion">
    <g filter="url(#blur)">'''

        for box in biome['boxes']:
            # rectangle-coords
            xStart = round(
                map_translate_coord(coordTrans(box['start']['x'], world_settings['latShift'], world_settings['latMulti']),
                                    borderL, coordsW, map_size))
            xEnd = round(
                map_translate_coord(coordTrans(box['end']['x'], world_settings['latShift'], world_settings['latMulti']), borderL,
                                    coordsW, map_size))
            yStart = round(
                map_translate_coord(coordTrans(box['start']['y'], world_settings['longShift'], world_settings['longMulti']),
                                    borderT, coordsH, map_size))
            yEnd = round(
                map_translate_coord(coordTrans(box['end']['y'], world_settings['longShift'], world_settings['longMulti']),
                                    borderT, coordsH, map_size))
            if xStart < 0:
                xStart = 0
            if xEnd > map_size:
                xEnd = map_size
            if yStart < 0:
                yStart = 0
            if yEnd > map_size:
                yEnd = map_size

            svg_output += f'''
        <rect x="{xStart}" y="{yStart}" width="{xEnd - xStart}" height="{yEnd - yStart}" />'''

        svg_output += f'''
    </g>
    <text x="{round(textX)}" y="{round(textY)}">{html.escape(biome['name'], quote=True)}</text>
</a>
'''

    # End of svg
    svg_output += '</svg>'
    return svg_output
