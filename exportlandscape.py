import argparse
import re
from dataclasses import dataclass
from logging import WARNING, NullHandler, basicConfig, getLogger
from pathlib import Path
from typing import *

from PIL import Image
from PIL.ImageFile import PyDecoder

from ark.discovery import initialise_hierarchy
from automate.ark import ArkSteamManager
from config import ConfigFile, get_global_config
from ue.asset import ExportTableItem, ImportTableItem, UAsset
from ue.loader import AssetLoader, AssetNotFound
from ue.properties import Texture2D

# pylint: enable=invalid-name

logger = getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(NullHandler())

EPILOG = '''example: python exportlandscape.py /Game/Maps/ScorchedEarth/SE_Landscape'''

DESCRIPTION = '''Extracts, splits up and stitches landscape splatmaps. Requires client build of the game or modded files.'''

args: argparse.Namespace


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("exportlandscape", description=DESCRIPTION, epilog=EPILOG)

    parser.add_argument('assetname', metavar='ASSETNAME', type=str, nargs=1, help='map to load')
    parser.add_argument('target', metavar='TARGET', type=str, nargs=1, help='output directory')

    return parser


def run():
    config = get_global_config()
    config.settings.SkipInstall = True

    arkman = ArkSteamManager(config=config)

    loader = arkman.getLoader()
    asset = loader[args.assetname[0]]
    base_filename = args.assetname[0].rsplit('/', 1)[1]

    for landscape in find_landscapes(asset):
        cache: Dict[str, Image] = dict()
        layers: Dict[str, List[TextureDescriptor]] = dict()

        # Extract textures into a dictionary from every component
        components = landscape.properties.get_property('LandscapeComponents')
        for component in components.values:
            for descriptor in grab_layers_from_component(cache, component.value.value):
                if descriptor.tag not in layers:
                    layers[descriptor.tag] = list()

                layers[descriptor.tag].append(descriptor)

        for layer_tag, descriptors in layers.items():
            print(layer_tag)
            layer = stitch(cache, descriptors)
            layer.save(f'{args.target[0]}/{base_filename}.{layer_tag}.png')


@dataclass
class TextureDescriptor(object):
    __slots__ = ('tag', 'position', 'key')
    tag: str
    position: Tuple[int, int]
    key: str


def decode_texture(export: ExportTableItem) -> Image:
    texture = export.extended_data
    data = texture.values[0]
    first_mipmap = data.mipmaps[0]

    if str(data.pixel_format) == 'PF_B8G8R8A8':
        image = Image.frombuffer('RGBA', (first_mipmap.size_x, first_mipmap.size_y), first_mipmap.raw_data, 'raw', 'BGRA', 0, 1)
    elif str(data.pixel_format) == 'PF_DXT5':
        image = Image.frombuffer('RGBA', (first_mipmap.size_x, first_mipmap.size_y), first_mipmap.raw_data, 'bcn', 3)
    else:
        raise NotImplementedError(f'{data.pixel_format} is not a supported pixel format.')
    return image


def stitch(cache: Dict[str, "Image"], descriptors: List[TextureDescriptor]) -> Image:
    #print(f'stitching {descriptors[0].tag} ({len(descriptors)} components)')
    # Find maximum values of X and Y offsets.
    texture_max_x = max(descriptors, key=lambda d: d.position[0] + cache[d.key].size[0])
    texture_max_y = max(descriptors, key=lambda d: d.position[1] + cache[d.key].size[1])
    # Calculate size of new texture.
    new_size_x = texture_max_x.position[0] + cache[texture_max_x.key].size[0]
    new_size_y = texture_max_y.position[1] + cache[texture_max_y.key].size[1]

    # Allocate a full size RGBA texture.
    mode = cache[descriptors[0].key].mode
    target_image = Image.new(mode, (new_size_x, new_size_y))

    # Go through each texture and copy it to the target.
    visited: List[str] = list()
    for info in descriptors:
        if info.key in visited:
            continue
        visited.append(info.key)

        #print(f'\t{info.key} @ {info.position}')
        target_image.paste(cache[info.key], info.position)

    return target_image


def find_landscapes(asset: UAsset) -> Iterator[ExportTableItem]:
    for export in asset.exports:
        if str(export.klass.value.name) == 'Landscape':
            yield export


def grab_layers_from_component(cache: Dict[str, "Image"], component: ExportTableItem) -> Iterator:
    properties = component.properties.as_dict()
    mic = properties['MaterialInstance'][0].value.value
    weight_allocs = properties['WeightmapLayerAllocations'][0].values
    weight_textures = properties['WeightmapTextures'][0].values
    heightmap = properties['HeightmapTexture'][0].value.value
    base_x = properties['SectionBaseX'][0]
    base_y = properties['SectionBaseY'][0]

    # Check that offsets are not null
    if base_x is None:
        base_x = 0
    else:
        base_x = base_x.value
    if base_y == None:
        base_y = 0
    else:
        base_y = base_y.value

    # Add heightmap texture to cache and yield a descriptor
    heightmap_key = str(heightmap.name)
    if heightmap_key not in cache:
        cache[heightmap_key] = decode_texture(heightmap)

    yield TextureDescriptor(tag='Heightmap', position=(base_x, base_y), key=heightmap_key)

    # Add weight textures to cache and yield descriptors
    texture_index = 0
    for weightmap in weight_textures:
        # Decode the weightmap itself
        weightmap = weightmap.value.value
        weightmap_key = str(weightmap)
        weightmap_image = decode_texture(weightmap)

        # Split color channels
        channels = weightmap_image.split()

        # Go through layer allocations and yield them
        for layer_alloc in weight_allocs:
            allocinfo = layer_alloc.as_dict()
            layer_tag = str(allocinfo['LayerInfo'].value.value.name)
            layer_key = f'{weightmap_key} {base_x}x{base_y} {layer_tag}'
            channel_id = allocinfo['WeightmapTextureChannel'].value

            # Check if texture index is right
            if allocinfo['WeightmapTextureIndex'].value != texture_index:
                continue

            # Yield channel
            if layer_key not in cache:
                cache[layer_key] = channels[channel_id]
            yield TextureDescriptor(tag=layer_tag, position=(base_x, base_y), key=layer_key)

        texture_index += 1


def main():
    basicConfig(level=WARNING)
    global args  # pylint: disable=global-statement, invalid-name
    args = create_parser().parse_args()
    try:
        run()
    except:  # pylint: disable=bare-except
        logger.exception('Caught exception. Aborting.')


if __name__ == '__main__':
    main()
