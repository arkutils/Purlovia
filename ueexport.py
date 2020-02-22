import os
import sys
from pprint import pprint

from automate.ark import ArkSteamManager
from automate.jsonutils import save_as_json
from browseasset import find_asset
from config import get_global_config
from ue.loader import AssetLoader, AssetLoadException
from ue.utils import sanitise_output


def main():
    arkman = ArkSteamManager()
    loader = arkman.getLoader()
    config = get_global_config()

    assetname = sys.argv[1] if len(sys.argv) > 1 else None
    if not assetname:
        print('Usage: python ueexport.py <assetname>')
        sys.exit(1)

    assetname = find_asset(assetname, loader)
    if not assetname:
        print("Not found")
        sys.exit(1)

    asset = loader[assetname]
    assert asset.default_export
    if not asset.default_export:
        print("Asset has no default export")
        sys.exit(2)

    export = asset.default_export
    data = sanitise_output(export.properties)

    pprint(data)

    save_as_json(data, f'output/{asset.name}.{export.name}.json', pretty=True)


if __name__ == '__main__':
    main()
