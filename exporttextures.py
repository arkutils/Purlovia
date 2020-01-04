import argparse
import re
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

EPILOG = '''example: python exporttextures.py /Game/Genesis/Icons/Dinos/ArkG_DinoHeadIcons_ShaftShifterSmall'''

DESCRIPTION = '''Extracts every texture from an asset into a directory. Requires client build of the game or modded files.'''

args: argparse.Namespace


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("exporttextures", description=DESCRIPTION, epilog=EPILOG)

    parser.add_argument('assetname', metavar='ASSETNAME', type=str, nargs=1, help='asset to load')
    parser.add_argument('target', metavar='TARGET', type=str, nargs=1, help='output directory')

    return parser


def run():
    config = get_global_config()
    config.settings.SkipInstall = True

    arkman = ArkSteamManager(config=config)

    loader = arkman.getLoader()
    asset = loader[args.assetname[0]]

    for texture in find_textures(asset):
        decode_texture_and_save(texture)


def find_textures(asset: UAsset) -> Iterator[ExportTableItem]:
    for export in asset.exports:
        if str(export.klass.value.name) == 'Texture2D':
            yield export


def decode_texture_and_save(export: ExportTableItem):
    texture = export.extended_data
    filename = args.assetname[0].rsplit('/', 1)[1]
    data = texture.values[0]
    first_mipmap = data.mipmaps[0]

    if str(data.pixel_format) == 'PF_B8G8R8A8':
        image = Image.frombuffer('RGBA', (first_mipmap.size_x, first_mipmap.size_y), first_mipmap.raw_data, 'raw', 'BGRA', 0, 1)
    elif str(data.pixel_format) == 'PF_DXT5':
        image = Image.frombuffer('RGBA', (first_mipmap.size_x, first_mipmap.size_y), first_mipmap.raw_data, 'bcn', 3)
    else:
        raise NotImplementedError(f'{data.pixel_format} is not a supported pixel format.')
    image.save(f'{args.target[0]}/{filename}.{export.name}.png')


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
