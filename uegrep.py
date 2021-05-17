import argparse
import re
from logging import WARNING, basicConfig
from typing import Iterator, Tuple

from ark.discovery import initialise_hierarchy
from automate.ark import ArkSteamManager
from config import get_global_config
from ue.hierarchy import find_parent_classes, find_sub_classes, iterate_all
from utils.log import get_logger

# pylint: enable=invalid-name

logger = get_logger(__name__)

EPILOG = '''example: python uegrep.py Dodo_Character_C'''

DESCRIPTION = '''Perform searches in the game asset hierarchy.'''

args: argparse.Namespace


def modlist(value: str) -> Tuple[str, ...]:
    value = value.strip()
    inputs = [v.strip() for v in value.split(',')]
    mods = tuple(v for v in inputs if v)
    for modid in mods:
        as_int = int(modid)  # pylint: disable=unused-variable  # noqa: F841  # For type-checking only
    return mods


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("uegrep", description=DESCRIPTION, epilog=EPILOG)

    parser.add_argument('--regex', '-r', action='store_true', help='allow regex matching')
    parser.add_argument('--ignore-case', '-i', action='store_true', help='ignore case')

    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument('--asset-only', '-a', action='store_true', help='search only asset names (ignore class name)')
    exclusive.add_argument('--class-only', '-c', action='store_true', help='search only class names (ignore asset name)')

    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument('--subs', '-s', action='store_true', help='show sub-classes of those found')
    exclusive.add_argument('--parents', '-p', action='store_true', help='show parents classes of those found')

    parser.add_argument('--no-script', '-n', action='store_true', help='restrict parents output to assets only')

    # TODO: Implement me!
    # exclusive = parser.add_mutually_exclusive_group()
    # exclusive.add_argument('--mods', action='store', type=modlist, help='override which mods include (comma-separated)')
    # exclusive.add_argument('--no-mods', action='store_true', help='do not include any mods in the search')

    parser.add_argument('searches', metavar='SEARCHES', type=str, nargs='+', help='strings to search for')

    return parser


def run():
    config = get_global_config()
    config.settings.SkipInstall = True

    arkman = ArkSteamManager(config=config)
    arkman.ensureSteamCmd()
    arkman.ensureGameUpdated()
    arkman.ensureModsUpdated(config.mods)

    initialise_hierarchy(arkman)

    for result in find_matches():
        output_result(result)


def find_matches() -> Iterator[str]:
    if args.ignore_case:
        searches = list(search.lower() for search in args.searches)
    else:
        searches = list(args.searches)

    if args.regex:
        regexes = [re.compile(search, flags=re.I if args.ignore_case else 0) for search in searches]

    for cls_name in iterate_all():
        if args.class_only:
            name = cls_name[cls_name.rfind('.') + 1:]
        elif args.asset_only:
            name = cls_name[:cls_name.rfind('.')]
        else:
            name = cls_name

        if args.regex:
            for regex in regexes:
                if regex.search(name):
                    yield cls_name
                    break
        else:
            if args.ignore_case:
                name = name.lower()

            for search in searches:
                if search in name:
                    yield cls_name
                    break


def output_result(result: str):
    indent = '  '
    print(result)
    if args.subs:
        for sub_cls_name in find_sub_classes(result):
            print(f'{indent}{sub_cls_name}')
    if args.parents:
        for i, parent_cls_name in enumerate(find_parent_classes(result)):
            if args.no_script and not parent_cls_name.startswith('/Game'):
                break
            print(f'{indent*(i+1)}{parent_cls_name}')


def main():
    basicConfig(level=WARNING)
    global args  # pylint: disable=global-statement, invalid-name
    args = create_parser().parse_args()
    try:
        run()
    except Exception:  # pylint: disable=bare-except
        logger.exception('Caught exception. Aborting.')


if __name__ == '__main__':
    main()
