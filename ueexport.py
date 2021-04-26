import argparse
import sys
from contextlib import contextmanager
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, Optional, Tuple, cast

from ark.discovery import initialise_hierarchy
from ark.types import PrimalItem
from automate.ark import ArkSteamManager
from automate.jsonutils import _format_json
from browseasset import find_asset
from config import get_global_config
from export.wiki.stage_items import get_item_name
from ue.asset import ExportTableItem, UAsset
from ue.gathering import gather_properties
from ue.hierarchy import inherits_from
from ue.proxy import UEProxyStructure
from ue.utils import sanitise_output

EPILOG = '''example: python ueexport.py /Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP'''

DESCRIPTION = '''Convert assets as JSON.'''

args: argparse.Namespace


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("uegrep", description=DESCRIPTION, epilog=EPILOG)

    parser.add_argument('--dir', nargs=1, help='output to a directory')
    parser.add_argument('--output', '-o', nargs=1, help='output to a specific file')
    parser.add_argument('--all', '-a', action='store_true', help='include all exports')
    parser.add_argument('--default', '-d', action='store_true', help='include only the default export')
    parser.add_argument('--ovi', action='store_true', help='create a 2D item icon render template for Oviraptor')
    parser.add_argument('assetname', metavar='ASSETNAME', type=str, help="asset to convert")
    parser.add_argument('export',
                        metavar='EXPORT',
                        type=str,
                        nargs='?',
                        help="select single export by name or index (all if not specified)")

    return parser


def collect_asset(assetname: str) -> UAsset:
    config = get_global_config()
    config.settings.SkipInstall = True
    arkman = ArkSteamManager(config=config)

    if args.ovi:
        # Hierarchy is needed for proxies in the Oviraptor target.
        arkman.ensureSteamCmd()
        arkman.ensureGameUpdated()
        arkman.ensureModsUpdated(config.mods)
        initialise_hierarchy(arkman, config)

    loader = arkman.getLoader()
    # config = get_global_config()

    assetname = find_asset(args.assetname, loader)
    if not assetname:
        print("Asset not found")
        sys.exit(1)

    return loader[assetname]


def create_filename(name: str) -> str:
    name = name.strip('/')

    if not name.endswith('.json'):
        name = name + '.json'

    name = name.replace('/', '+')
    return name


def find_export(asset: UAsset) -> Optional[ExportTableItem]:
    if args.default:
        # Produce default export only
        if not hasattr(asset, 'default_export'):
            print("Asset does not have a default export", file=sys.stderr)
            sys.exit(1)

        assert asset.default_export and asset.default_export.fullname
        return asset.default_export

    elif args.export:
        # Single export
        as_int: Optional[int] = None
        try:
            as_int = int(args.export)
        except ValueError:
            pass

        if as_int is not None:
            # Integer-based export lookup
            if as_int < 0 or as_int >= len(asset.exports.values):
                print(f"Maximum export index for this asset is {len(asset.exports.values)-1}", file=sys.stderr)
                sys.exit(1)

            return asset.exports[as_int]
        else:
            # Name-based export lookup
            found_indexes = []
            search_name = args.export.lower()

            for i in range(len(asset.exports.values)):
                export = asset.exports.values[i]

                if str(export.name).lower() == search_name:
                    found_indexes.append(i)

            if found_indexes:
                print("Export with this name not found", file=sys.stderr)
                sys.exit(1)
            elif len(found_indexes) > 1:
                print("This name was found at multiple indexes:", file=sys.stderr)
                pprint(found_indexes, stream=sys.stderr)
                sys.exit(1)

            return asset.exports.values[found_indexes[0]]

    return None


def collect_data(asset: UAsset) -> Tuple[str, Any]:
    if args.default and args.export is not None:
        print("Cannot specify an export with --default", file=sys.stderr)
        sys.exit(1)

    if args.ovi:
        if not args.export and not args.default:
            # Grab the default export since we need a starting point for the proxy.
            args.default = True
        export = find_export(asset)
        assert export
        assert export.fullname

        if not inherits_from(export, PrimalItem.get_ue_type()):
            print(f"Export {export.name} is not a subclass of PrimalItem.", file=sys.stderr)
            sys.exit(1)

        proxy: UEProxyStructure = gather_properties(export)
        item = cast(PrimalItem, proxy)

        if 'ItemIconMaterialParent' not in item:
            print("Item does not use an icon shader", file=sys.stderr)
            sys.exit(1)

        name = get_item_name(item) or export.name
        data: Dict[str, Any] = dict(
            Format='2.0',
            Name=name,
            BlueprintPath=export.fullname,
        )

        assert asset.loader
        mat_instance = asset.loader.load_related(item.ItemIconMaterialParent[0]).default_export
        assert mat_instance
        mat_properties = mat_instance.properties.as_dict()

        # Convert all parameters from the material instance.
        parameters = dict()
        if 'ScalarParameterValues' in mat_properties:
            for param in mat_properties['ScalarParameterValues'][0].values:
                param_info = param.as_dict()
                param_name = sanitise_output(param_info['ParameterName'])
                parameters[param_name] = param_info['ParameterValue']
        if 'VectorParameterValues' in mat_properties:
            for param in mat_properties['VectorParameterValues'][0].values:
                param_info = param.as_dict()
                param_name = sanitise_output(param_info['ParameterName'])
                parameters[param_name] = param_info['ParameterValue'].values[0]
        if 'TextureParameterValues' in mat_properties:
            for param in mat_properties['TextureParameterValues'][0].values:
                param_info = param.as_dict()
                param_name = sanitise_output(param_info['ParameterName'])
                parameters[param_name] = param_info['ParameterValue']

        if parameters:
            data['2DMaterial'] = dict(Parent=mat_properties['Parent'][0], **parameters)
        else:
            # Export only the parent material as the instance has no parameters.
            data['2DMaterial'] = mat_properties['Parent'][0]

        data = sanitise_output(data)
        filename = create_filename(export.fullname)

    elif args.default or args.export:
        export = find_export(asset)
        assert export
        assert export.fullname
        data = sanitise_output(export.properties)
        filename = create_filename(export.fullname)

    else:
        # Full asset extraction
        data = sanitise_output(asset)
        assert asset.assetname
        filename = create_filename(asset.assetname)

    return (filename, data)


@contextmanager
def manage_output_file(filename: str):
    # Work out where to save it
    if args.output:
        path = Path(args.output[0])
    elif args.dir:
        path = Path(args.dir[0], filename)
    else:
        path = Path('-')

    if path == Path('-'):
        yield sys.stdout
        return

    with open(path, 'wt', newline='\n', encoding='utf8') as handle:
        yield handle

    print("Output saved as: " + str(path))

    return


def main():
    global args  # pylint: disable=global-statement, invalid-name
    args = create_parser().parse_args()

    if args.dir and args.output:
        print("Cannot specify both --dir and --output:", file=sys.stderr)
        sys.exit(1)

    asset = collect_asset(args.assetname)
    filename, data = collect_data(asset)
    json = _format_json(data, pretty=True)
    with manage_output_file(filename) as handle:
        handle.write(json)


if __name__ == '__main__':
    main()
