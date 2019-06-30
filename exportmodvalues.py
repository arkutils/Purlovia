import re
import sys
import os.path
import json
import string
from datetime import datetime
from collections import defaultdict
from argparse import ArgumentParser, Namespace
from typing import *

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
loggingHandler = logging.StreamHandler()
logger.addHandler(loggingHandler)

import ark.mod
from automate.ark import readModData, ArkSteamManager
from ark.export_asb_values import values_for_species
from ue.loader import AssetLoader

INCLUDE_REGEX = r'.*(_Character|Character_).*BP.*'
EXCLUDE_REGEX = r'.*(_Base|Base_).*'


def log(*args):
    print(*args)


def error(*args):
    logger.error(string.format(args))
    print('Error:', *args, file=sys.stderr)
    sys.exit(1)


# def lookup(modid, loader: AssetLoader):
#     mod_name = loader.mods_numbers_to_names.get(modid)
#     long_name = loader.mods_numbers_to_descriptions.get(modid, mod_name)
#     return mod_name, long_name


def parse(mod_name: str, modid: int, loader: AssetLoader):
    log(f'Exporting {modid} ({mod_name})...')

    mod_assetnames = loader.find_assetnames(INCLUDE_REGEX, f'/Game/Mods/{mod_name}', exclude=EXCLUDE_REGEX)

    species_data = []
    for assetname in mod_assetnames:
        asset = loader[assetname]
        props = ark.mod.gather_properties(asset)
        species_data.append((asset, props))

    return species_data


def convert(species_data: list, modid: str, version: str):
    values: Dict[str, Any] = dict()
    values['formatVersion'] = 2
    # values['mod'] = dict(id=modid, tag=tag, title=title) # TODO: Complete
    values['ver'] = version
    values['generatedAt'] = datetime.utcnow().isoformat()
    values['species'] = list()

    for asset, props in species_data:
        species_values = values_for_species(asset, props, allFields=True, fullStats=True)
        values['species'].append(species_values)

    return values


def output(name: str, values: dict):
    filename = os.path.join(args.outdir, f'{name.lower()}.json')
    log(f' -> {filename} [version {values["ver"]}]')
    with open(filename, 'w') as f:
        json.dump(values, fp=f)


def parse_mod_args():
    requests = [[modid.strip() for modid in field.split('+')] for field in args.mods]
    mod_list = set(item for sublist in requests for item in sublist)
    return requests, mod_list


def grab_mod_info(mod_list, loader: AssetLoader):
    mod_info = dict()
    for modid in mod_list:
        mod_data = readModData(loader.asset_path, modid)
        assert mod_data
        asset = loader[mod_data['package']]
        props = ark.mod.gather_properties(asset)
        long_name = str(props['ModName'][0][-1])
        long_name = clean_name(long_name)
        mod_data['descriptive_name'] = long_name
        mod_info[modid] = mod_data
    return mod_info


def clean_name(name):
    name = name.strip()
    name = re.sub(r'\s+', '_', name)
    return name


def do_convertions(requests, mod_info, loader: AssetLoader):
    for request in requests:
        infos = dict((modid, mod_info[modid]) for modid in request)
        modids_string = '+'.join(str(modid) for modid in request)
        longname_string = '+'.join(infos[modid].get('descriptive_name', infos[modid]['name']) for modid in request)
        version_string = str(max(infos[modid]['version'] for modid in request)) + '.0'
        species_data = sum((parse(infos[modid]['name'], modid, loader) for modid in request), [])
        values = convert(species_data, modids_string, version_string)
        output(longname_string, values)


def create_parser():
    parser = ArgumentParser(description="Export mod data for ASB in values.json format.")
    parser.add_argument('mods', metavar='MODID', nargs='+', help='ID of a mod to export (can be repeated)')
    parser.add_argument('-o', dest='outdir', default='output', help='directory to save the output(s) into (default: output)')
    parser.add_argument('-b', dest='basedir', default='livedata', help='base directory of the live data (default: livedata)')
    parser.add_argument('-q', dest='quiet', action='store_const', const=True, help='disable non-essential output')
    parser.add_argument('-v', dest='verbosity', action='count', default=0, help='increase log level (can be repeated)')
    parser.add_argument('-c', dest='createdir', action='store_const', const=True, help="create 'outdir' if it doesn't exist")
    return parser


args: Namespace = Namespace()


def main():
    global args, log

    parser = create_parser()
    args = parser.parse_args()

    print(args)
    sys.exit(0)

    if args.quiet:
        log = lambda *args: None
        logger.setLevel(logging.ERROR)

    if not args.quiet:
        if args.verbosity:
            logger.setLevel(logging.INFO)
        elif args.verbosity > 1:
            logger.setLevel(logging.DEBUG)

    if not os.path.isdir(args.outdir):
        if args.createdir and not os.path.exists(args.outdir):
            try:
                os.makedirs(args.outdir)
            except Exception as ex:
                error('Unable to create outdir: ' + ex)
        else:
            error('Outdir does not exist or is not a directory')

    mod_names = dict()

    arkman = ArkSteamManager(args.basedir)
    loader = arkman.createLoader()

    requests, mod_list = parse_mod_args()
    mod_info = grab_mod_info(mod_list, loader)
    do_convertions(requests, mod_info, loader)


if __name__ == '__main__':
    main()
