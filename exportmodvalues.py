import sys
import os.path
import json
from datetime import datetime
from collections import defaultdict

import ark.mod
from ark.export_asb_values import values_for_species
from ue.loader import AssetLoader

INCLUDE_REGEX = r'.*(_Character|Character_).*BP.*'
EXCLUDE_REGEX = r'.*(_Base|Base_).*'


def log(*args):
    print(*args)


def error(*args):
    print('Error:', *args, file=sys.stderr)
    sys.exit(1)


def lookup(modid, loader: AssetLoader):
    mod_name = loader.mods_numbers_to_names.get(modid)
    long_name = loader.mods_numbers_to_descriptions.get(modid, mod_name)
    return mod_name, long_name


def parse(mod_name: str, modid: int, loader: AssetLoader):
    log(f'Exporting {modid} ({mod_name})...')

    mod_assetnames = loader.find_assetnames(INCLUDE_REGEX, f'/Game/Mods/{mod_name}', exclude=EXCLUDE_REGEX)

    species_data = []
    for assetname in mod_assetnames:
        asset = loader[assetname]
        props = ark.mod.gather_properties(asset)
        species_data.append((asset, props))

    return species_data


def convert(species_data: list, modid: str):
    values = dict()
    values['ver'] = datetime.utcnow().isoformat()
    values['modid'] = modid
    values['species'] = list()

    for asset, props in species_data:
        species_values = values_for_species(asset, props, all=True)
        values['species'].append(species_values)

    return values


def output(name: str, values: dict):
    filename = os.path.join(args.outdir, f'{name.lower()}.json')
    log(f' -> {filename}')
    with open(filename, 'w') as f:
        json.dump(values, fp=f)


def parse_mod_args():
    requests = [[modid.strip() for modid in field.split('+')] for field in args.mods]
    mod_list = set(item for sublist in requests for item in sublist)
    return requests, mod_list


def grab_mod_info(mod_list, loader: AssetLoader):
    mod_names = dict()
    for modid in mod_list:
        mod_name = loader.mods_numbers_to_names.get(modid)
        long_name = loader.mods_numbers_to_descriptions.get(modid, mod_name)
        mod_names[modid] = (mod_name, long_name)
    return mod_names


def do_convertions(requests, mod_names, loader: AssetLoader):
    for request in requests:
        modids = '+'.join(str(modid) for modid in request)
        name = '+'.join(mod_names[modid][1] for modid in request)
        species_data = sum((parse(mod_names[modid][0], modid, loader) for modid in request), [])
        values = convert(species_data, modids)
        output(name, values)


def create_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Export mod data for ASB in values.json format.")
    parser.add_argument(
        'mods', metavar='MODID', type=str, nargs='+', help='ID of a mod to export (can appear multiple times, use + to combine)')
    parser.add_argument('-o', dest='outdir', default='mods', help='directory to save the output(s) into (default: mods)')
    parser.add_argument(
        '-c', dest='createdir', action='store_const', const=True, default=False, help='create \'outdir\' if it doesn\'t exist')
    parser.add_argument('-q', dest='quiet', action='store_const', const=True, default=False, help='quieten normal output')
    return parser


def main():
    global args, log

    parser = create_parser()
    args = parser.parse_args()

    if args.quiet:
        log = lambda *args: None

    if not os.path.isdir(args.outdir):
        if args.createdir and not os.path.exists(args.outdir):
            try:
                os.makedirs(args.outdir)
            except ex:
                error('Unable to create outdir: ' + ex)
        else:
            error('Outdir does not exist or is not a directory')

    mod_names = dict()

    loader = AssetLoader(quiet=args.quiet)

    requests, mod_list = parse_mod_args()
    mod_names = grab_mod_info(mod_list, loader)
    do_convertions(requests, mod_names, loader)


if __name__ == '__main__':
    main()
