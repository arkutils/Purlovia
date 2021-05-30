'''
Creates an svg-file with regions that contain links to the according region-page
(used on the ARK: Survival Evolved Wiki)
'''

import html
import re

from ..common import SVGBoundaries
from .func import make_biome_link, map_translate_coord, translate_coord

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


def _generate_biome_rects(bounds: SVGBoundaries, world_settings, biome):
    svg_output = ''
    for box in biome['boxes']:
        # rectangle-coords
        x1 = translate_coord(box['start']['x'], world_settings['longShift'], world_settings['longMulti'])
        x2 = translate_coord(box['end']['x'], world_settings['longShift'], world_settings['longMulti'])
        y1 = translate_coord(box['start']['y'], world_settings['latShift'], world_settings['latMulti'])
        y2 = translate_coord(box['end']['y'], world_settings['latShift'], world_settings['latMulti'])

        x1 = round(map_translate_coord(x1, bounds.border_left, bounds.coord_width, bounds.size))
        x2 = round(map_translate_coord(x2, bounds.border_left, bounds.coord_width, bounds.size))
        y1 = round(map_translate_coord(y1, bounds.border_top, bounds.coord_height, bounds.size))
        y2 = round(map_translate_coord(y2, bounds.border_top, bounds.coord_height, bounds.size))

        # Clamp the coords
        x1 = min(max(0, x1), bounds.size)
        x2 = min(max(0, x2), bounds.size)
        y1 = min(max(0, y1), bounds.size)
        y2 = min(max(0, y2), bounds.size)

        # Make sure the order is right
        if x1 > x2:
            x2, x1 = x1, x2
        if y1 > y2:
            y2, y1 = y1, y2

        w = x2 - x1
        h = y2 - y1

        # Skip if the volume's area is zero, or if out of bounds
        if w == 0 or h == 0:
            continue

        svg_output += f'\n<rect x="{x1}" y="{y1}" width="{w}" height="{h}" />'
    return svg_output


def generate_svg_map(bounds: SVGBoundaries, map_name, world_settings, biomes, follow_mod_convention):
    svg_output = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{bounds.size}" height="{bounds.size}" '
                  f'viewBox="0 0 {bounds.size} {bounds.size}" style="position: absolute; width:100%; height:100%;">\n'
                  '<defs>\n'
                  '<filter id="blur" x="-30%" y="-30%" width="160%" height="160%">'
                  '<feColorMatrix type="matrix" values="1 0 0 1 0, 0 1 0 0 0, 0 0 1 0 0, 0 0 0 0.7 0" />'
                  '<feGaussianBlur stdDeviation="10" />'
                  '</filter>\n'
                  '</defs>\n')

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

    textX = bounds.size / 2
    textY = 60

    # Create svg
    for biome in valid_biomes:
        biome_link = make_biome_link(world_settings["name"], biome["name"], follow_mod_convention)
        svg_output += f'<a href="/{biome_link}" class="svgRegion">'
        svg_output += '<g filter="url(#blur)">\n'
        svg_output += _generate_biome_rects(bounds, world_settings, biome)
        svg_output += '</g>\n'
        svg_output += f'<text x="{round(textX)}" y="{round(textY)}">{html.escape(biome["name"], quote=True)}</text>'
        svg_output += '</a>\n'

    # End of svg
    svg_output += '</svg>'
    return svg_output
