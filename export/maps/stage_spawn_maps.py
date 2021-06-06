from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.log import get_logger

from .common import SVGBoundaries, get_svg_bounds_for_map, order_growing, remove_unicode_control_chars
from .spawns_consts import SVG_SIZE
from .stage_base import JsonProcessingStage, ModType

logger = get_logger(__name__)

__all__ = [
    'ProcessSpawnMapsStage',
]

SVG_CSS = '''
    <style>
        .spawningMap-very-common { fill: #0F0; }
        .spawningMap-common { fill: #B2FF00; }
        .spawningMap-uncommon { fill: #FF0; }
        .spawningMap-very-uncommon { fill: #FC0; }
        .spawningMap-rare { fill: #F60; }
        .spawningMap-very-rare { fill: #F00; }
        .spawning-map-point { stroke:black; stroke-width:1; }
    </style>'''
SVG_FILTER_UNTAMEABLE = '''
    <pattern id="pattern-untameable" width="10" height="10" patternTransform="rotate(135)" patternUnits="userSpaceOnUse">
        <rect width="4" height="10" fill="black"></rect>
    </pattern>'''
SVG_FILTER_CAVE = '''
    <filter id="groupStroke">
        <feFlood result="outsideColor" flood-color="black"/>
        <feMorphology in="SourceAlpha" operator="dilate" radius="2"/>
        <feComposite result="strokeoutline1" in="outsideColor" operator="in"/>
        <feComposite result="strokeoutline2" in="strokeoutline1" in2="SourceAlpha" operator="out"/>
        <feGaussianBlur in="strokeoutline2" result="strokeblur" stdDeviation="1"/>
    </filter>'''

# These CSS class names are also defined on the ARK Wiki (https://ark.fandom.com/wiki/MediaWiki:Common.css)
# and thus shouldn't be renamed here.
CSS_RARITY_CLASSES = [
    'spawningMap-very-rare', 'spawningMap-rare', 'spawningMap-very-uncommon', 'spawningMap-uncommon', 'spawningMap-common',
    'spawningMap-very-common'
]
POINT_RADIUS = max(SVG_SIZE / 150, 2) * 2


class ProcessSpawnMapsStage(JsonProcessingStage):
    def get_name(self) -> str:
        return "spawn_maps"

    def get_files_to_load(self, modid: Optional[str]) -> List[str]:
        return ['species']

    def process(self, base_path: Path, modid: Optional[str], modtype: Optional[ModType], data: Dict[str, List[Any]]):
        # Ensure all bare minimum data is available
        assert data['species']

        # Discover maps
        if not modid or modtype == ModType.GameMod:
            map_names = list(self.find_maps(None, keyword='npc_spawns', include_official_mods=modtype == ModType.GameMod))
        elif modtype == ModType.CustomMap:
            map_names = list(self.find_maps(modid, keyword='npc_spawns'))
        else:
            return

        # Load map data
        mapdata: Dict[str, Dict[str, Any]] = dict()
        for name, _ in map_names:
            expath = base_path / name / 'stage1.json'
            mapdata[name] = self.load_json_file(expath)

        # Create a tamability lookup table.
        species_tamability: Dict[str, bool] = dict()
        for moddata in data['species']:
            for creature in moddata['species']:
                species_tamability[creature['bp']] = 'isTameable' in creature.get('flags', ())

        # Iterate over the maps and generate all SVGs.
        for name, _ in map_names:
            if not mapdata[name]:
                continue

            logger.info(f'Generating spawn maps for {name}')

            # Gather locations for each creature.
            zones_by_creature = self._gather_locations_of_species(mapdata[name])

            # Create output.
            for creature_bp, zones in zones_by_creature.items():
                # Skip creature if this is a game mod and the creature isn't coming from it.
                if modid and modtype == ModType.GameMod:
                    if self.manager.loader.get_mod_id(creature_bp) != modid:
                        continue

                # Check if creature is tameable according to wiki.species. Output a warning if it can't be found.
                is_tameable = species_tamability.get(creature_bp, None)
                if is_tameable is None:
                    is_tameable = True
                    logger.warning(f'Species encountered when generating maps but missing from wiki.species: {creature_bp}')

                # Generate the SVG.
                bounds = get_svg_bounds_for_map(mapdata[name]['level'])
                svg_contents = self._build_svg(bounds, creature_bp, zones, is_tameable)

                # Write to disk.
                if svg_contents:
                    filepath = base_path / name / self._get_filename_for_species(creature_bp)
                    self.save_raw_file(svg_contents, filepath)

    def _gather_locations_of_species(self, spawns: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        # Collect the zone controllers.
        zones: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for zone in spawns['zones']:
            for creature_bp in zone['creatures'].keys():
                zones[creature_bp].append(zone)

        return zones

    def _get_filename_for_species(self, bp: str) -> str:
        class_name = bp[bp.index('.') + 1:]
        class_name = remove_unicode_control_chars(class_name)

        modid = self.manager.loader.get_mod_id(bp)
        if modid:
            return f'{modid}/{class_name}.svg'
        return f'core/{class_name}.svg'

    def _build_svg(self, bounds: SVGBoundaries, creature: str, zones: List[Dict[str, Any]], is_tameable: bool) -> Optional[str]:
        boxes = defaultdict(list)
        points = defaultdict(list)
        needs_untameable_overlay_setup = False
        needs_cave_overlay_setup = False

        # Construct shapes
        for zone in zones:
            rarity = zone['creatures'][creature]

            spawn_points = zone['points']
            if spawn_points:
                # Build circles for each point
                for point in spawn_points:
                    x: float = round((point['long'] - bounds.border_left) * bounds.size / bounds.coord_width)
                    y: float = round((point['lat'] - bounds.border_top) * bounds.size / bounds.coord_height)

                    if x < 0 or y < 0 or x > bounds.size or y > bounds.size:
                        # Out of bounds, skip
                        continue

                    # Clamp the coords
                    x = min(bounds.size, max(0, x))
                    y = min(bounds.size, max(0, y))
                    points[rarity].append((x, y))

                continue

            spawn_locations = zone['locations']
            if spawn_locations:
                # Determine if overlays will have to be generated
                is_untameable = zone['untameable'] or not is_tameable
                is_cave = zone['cave']

                # Build a rectangular shape for each location
                for region in spawn_locations:
                    # Make sure the order is right
                    start_x, end_x = order_growing(region['start']['long'], region['end']['long'])
                    start_y, end_y = order_growing(region['start']['lat'], region['end']['lat'])

                    # Add a small border to avoid gaps
                    start_x = round((start_x - bounds.border_left) * bounds.size / bounds.coord_width) - 3
                    end_x = round((end_x - bounds.border_left) * bounds.size / bounds.coord_width) + 3
                    start_y = round((start_y - bounds.border_top) * bounds.size / bounds.coord_height) - 3
                    end_y = round((end_y - bounds.border_top) * bounds.size / bounds.coord_height) + 3

                    # Clamp the values
                    start_x = min(bounds.size, max(0, start_x))
                    end_x = min(bounds.size, max(0, end_x))
                    start_y = min(bounds.size, max(0, start_y))
                    end_y = min(bounds.size, max(0, end_y))

                    # Calculate box width and height
                    w = end_x - start_x
                    h = end_y - start_y

                    # Skip the box if height or width are zero
                    if w == 0 or h == 0:
                        continue

                    boxes[rarity].append((start_x, w, start_y, h, is_untameable, is_cave))

                    # Build untameability and cave overlays if needed
                    if is_untameable:
                        needs_untameable_overlay_setup = True
                    if is_cave:
                        needs_cave_overlay_setup = True

        # Skip if there's no shapes.
        if not boxes and not points:
            return None

        # Create a buffer and add the header.
        buffer = StringIO()
        buffer.write('<?xml version="1.0" encoding="utf-8"?>\n')
        buffer.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{bounds.size}" ')
        buffer.write(f'height="{bounds.size}" viewBox="0 0 {bounds.size} {bounds.size}" ')
        buffer.write('class="creatureMap" style="position:absolute;">\n<defs>')

        buffer.write(f'''
    <filter id="blur" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="{round(bounds.size / 100)}" />
    </filter>''')
        buffer.write(SVG_CSS)

        # Add required patterns/filters for overlays
        if needs_untameable_overlay_setup:
            buffer.write(SVG_FILTER_UNTAMEABLE)

        if needs_cave_overlay_setup:
            buffer.write(SVG_FILTER_CAVE)

        buffer.write('\n</defs>')

        # Output boxes and their overlays.
        if boxes:
            # Setup secondary buffers if overlays are to be written
            untameable_buffer = None
            cave_buffer = None
            if needs_untameable_overlay_setup:
                untameable_buffer = StringIO()
            if needs_cave_overlay_setup:
                cave_buffer = StringIO()

            # Write rarity rectangles.
            buffer.write('\n<g filter="url(#blur)" opacity="0.7">')
            for rarity, info in boxes.items():
                buffer.write(f'\n    <g class="{CSS_RARITY_CLASSES[rarity]}">')

                for x, w, y, h, is_untameable, is_cave in info:
                    # XYWH rect.
                    rect = f'''
        <rect x="{x}" y="{y}" width="{w}" height="{h}" />'''
                    buffer.write(rect)

                    # Write to relevant overlays.
                    if is_untameable and untameable_buffer:
                        untameable_buffer.write(rect)
                    if is_cave and cave_buffer:
                        cave_buffer.write(rect)

                buffer.write('\n    </g>')
            buffer.write('</g>')

            # Output overlays.
            if untameable_buffer:
                buffer.write('\n<g fill="url(#pattern-untameable)" opacity="0.3">')
                buffer.write(untameable_buffer.getvalue())
                buffer.write('\n</g>')
            if cave_buffer:
                buffer.write('\n<g filter="url(#groupStroke)" opacity="0.8">')
                buffer.write(cave_buffer.getvalue())
                buffer.write('\n</g>')

        # Output points.
        if points:
            buffer.write('\n<g class="spawning-map-point" opacity="0.8">')
            for rarity, coords in points.items():
                # Rarity group.
                buffer.write(f'\n    <g class="{CSS_RARITY_CLASSES[rarity]}">')

                for x, y in coords:
                    # XY circle.
                    buffer.write(f'''
        <circle cx="{x}" cy="{y}" r="{POINT_RADIUS}" />''')

                buffer.write('\n    </g>')
            buffer.write('</g>')

        # Return the contents.
        buffer.write('\n</svg>')
        return buffer.getvalue()
