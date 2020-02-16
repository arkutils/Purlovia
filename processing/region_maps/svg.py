'''
Creates an svg-file with regions that contain links to the according region-page
(used on the ARK: Survival Evolved Wiki)
'''

import html
import json
import math
import re

from processing.common import SVGDimensions

from .func import coordTrans, make_biome_article_name, map_translate_coord

REGEX_INVALID_BIOME = re.compile(r'^\?+$')


def filter_biomes(biomes):
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

    return valid_biomes


def _generate_biome_rects(dimens: SVGDimensions, world_settings, biome):
    svg_output = ''
    for box in biome['boxes']:
        # rectangle-coords
        x1 = coordTrans(box['start']['x'], world_settings['longShift'], world_settings['longMulti'])
        x2 = coordTrans(box['end']['x'], world_settings['longShift'], world_settings['longMulti'])
        y1 = coordTrans(box['start']['y'], world_settings['latShift'], world_settings['latMulti'])
        y2 = coordTrans(box['end']['y'], world_settings['latShift'], world_settings['latMulti'])

        x1 = round(map_translate_coord(x1, dimens.border_left, dimens.coord_width, dimens.size))
        x2 = round(map_translate_coord(x2, dimens.border_left, dimens.coord_width, dimens.size))
        y1 = round(map_translate_coord(y1, dimens.border_top, dimens.coord_height, dimens.size))
        y2 = round(map_translate_coord(y2, dimens.border_top, dimens.coord_height, dimens.size))

        x1 = max(0, x1)
        x2 = min(x2, dimens.size)
        y1 = max(0, y1)
        y2 = min(y2, dimens.size)

        svg_output += f'\n<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" />'
    return svg_output


def generate_svg_map(dimens: SVGDimensions, map_name, world_settings, biomes, follow_mod_convention):
    svg_output = (
        '<svg xmlns="http://www.w3.org/2000/svg"'
        f''' width="{dimens.size}" height="{dimens.size}" viewBox="0 0 {dimens.size} {dimens.size}" style="position: absolute; width:100%; height:100%;">
<defs>
    <filter id="blur" x="-30%" y="-30%" width="160%" height="160%">'
        <feColorMatrix type="matrix" values="1 0 0 1 0, 0 1 0 0 0, 0 0 1 0 0, 0 0 0 0.7 0"/>
        <feGaussianBlur stdDeviation="10" />
    </filter>
</defs>\n''')

    # Remove invalid biome entries
    valid_biomes = filter_biomes(biomes)

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

    textX = dimens.size / 2
    textY = 60

    # Create svg
    for biome in valid_biomes:
        svg_output += f'''<a href="{make_biome_article_name(map_name, biome['name'], follow_mod_convention)}" class="svgRegion">
    <g filter="url(#blur)">'''

        svg_output += _generate_biome_rects(dimens, world_settings, biome)

        svg_output += f'''
    </g>
    <text x="{round(textX)}" y="{round(textY)}">{html.escape(biome['name'], quote=True)}</text>
</a>
'''

    # End of svg
    svg_output += '</svg>'
    return svg_output
