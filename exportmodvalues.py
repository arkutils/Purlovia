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
    return mod_name


def parse(mod_name: str, loader: AssetLoader):
    mod_number = loader.mods_names_to_numbers[mod_name]
    log(f'Exporting {mod_number} ({mod_name})...')

    mod_assetnames = loader.find_assetnames(INCLUDE_REGEX, f'/Game/Mods/{mod_name}', exclude=EXCLUDE_REGEX)

    species_data = []
    for assetname in mod_assetnames:
        asset = loader[assetname]
        props = ark.mod.gather_properties(asset)
        species_data.append((asset, props))

    return species_data


def convert(species_data: list):
    values = dict()
    values['ver'] = datetime.utcnow().isoformat()
    values['species'] = list()

    for asset, props in species_data:
        species_values = values_for_species(asset, props, all=True)
        values['species'].append(species_values)

    return values


def output(mod_name: str, values: dict):
    filename = os.path.join(args.outdir, f'{mod_name.lower()}.json')
    log(f' -> {filename}')
    with open(filename, 'w') as f:
        json.dump(values, fp=f)


def create_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Export mod data for ASB in values.json format")
    parser.add_argument('mods', metavar='MODID', type=str, nargs='+', help='ID of a mod to export (can appear multiple times)')
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

    for modid in args.mods:
        mod_name = lookup(modid, loader) or error(f"Unable to find details for mod {modid}")
        mod_names[modid] = mod_name

    for (modid, mod_name) in mod_names.items():
        species_data = parse(mod_name, loader)
        values = convert(species_data)
        output(mod_name, values)


if __name__ == '__main__':
    main()
