from interactive.setup import arkman, loader

from pathlib import Path
from typing import Set

import ue.hierarchy
from automate.jsonutils import _format_json
from ue.context import ue_parsing_context
from ue.utils import sanitise_output

# Configs
root = '/Game/LostIsland/Dinos'
include_mods = True
output_dir = Path(r'livedata/assets')

# Requires amazon.ion package for Ion formats

# json/pretty_json/ion/table_ion
format = 'pretty_json'

if format == 'json':
    ext = '.json'

    def fmt(json, _):
        formatted = _format_json(json, pretty=False)
        return formatted.encode('utf8')
elif format == 'pretty_json':
    ext = '.json'

    def fmt(json, _):
        formatted = _format_json(json, pretty=True)
        return formatted.encode('utf8')
elif format == 'table_ion':
    import amazon.ion.simpleion as ion
    import amazon.ion.symbols as symbols
    ext = '.ion'

    def fmt(json, names):
        syms = symbols.shared_symbol_table(None, symbols=map(str, names))
        formatted = ion.dumps(json, binary=True, imports=[syms])
        return formatted
elif format == 'ion':
    import amazon.ion.simpleion as ion
    import amazon.ion.symbols as symbols
    ext = '.ion'

    def fmt(json, _):
        formatted = ion.dumps(json, binary=True)
        return formatted
else:
    raise Exception("Format not supported")


def create_filename(name: str, ext: str) -> str:
    name = name.strip('/')

    if not name.endswith(ext):
        name = name + ext

    return name


def setup():
    output_dir.mkdir(exist_ok=True, parents=True)


def calculate_excludes() -> Set[str]:
    mod_excludes = set(arkman.config.optimisation.SearchIgnore)
    core_excludes = set(['/Game/Mods/.*', *arkman.config.optimisation.SearchIgnore])
    excludes = mod_excludes if include_mods else core_excludes
    return excludes


def do_extract(root: str, excludes: Set[str]):
    base_dir = output_dir / format

    with ue_parsing_context(properties=True, bulk_data=False):
        asset_iterator = loader.find_assetnames(root,
                                                exclude=excludes,
                                                extension=ue.hierarchy.asset_extensions,
                                                return_extension=True)

        total_files = 0
        total_dirs = 0
        total_bytes = 0

        prev_path = ''
        for (assetname, _) in asset_iterator:
            # print(assetname)
            show_stats = False

            total_files += 1
            output_filename = create_filename(assetname, ext)
            output_path = base_dir / output_filename
            output_path.parent.mkdir(exist_ok=True, parents=True)
            print(f'► {output_path}')

            if str(output_path.parent) != prev_path:
                total_dirs += 1
                prev_path = str(output_path.parent)
                print(output_path.parent.relative_to(base_dir))

                if (total_dirs % 100) == 0:
                    show_stats = True

            try:
                # Skip existing files for
                if output_path.is_file():
                    continue

                try:
                    asset = loader[assetname]
                except Exception:
                    print(f'ERROR: Unable to parse: {assetname}')
                    continue
                loader.wipe_cache()  # No caching!

                data = sanitise_output(asset.exports)
                binary = fmt(data, asset.names.values)
                output_path.write_bytes(binary)

            finally:
                if output_path.is_file():
                    total_bytes += output_path.stat().st_size

                if show_stats:
                    print()
                    print(f'Total dirs:  {total_dirs:,}')
                    print(f'Total files: {total_files:,}')
                    print(f'Total bytes: {total_bytes/1024/1024:,.1f}Mo')
                    print()

        print()
        print('Grand total:')
        print()
        print(f'Total dirs:  {total_dirs:,}')
        print(f'Total files: {total_files:,}')
        print(f'Total bytes: {total_bytes/1024/1024:,.1f}Mo')


# Do it
setup()
excludes = calculate_excludes()
do_extract(root, excludes)
