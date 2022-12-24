import argparse
import re
from logging import WARNING, basicConfig
from typing import Iterator, Tuple

from ark.discovery import initialise_hierarchy
from ark.mod import get_official_mods
from automate.ark import ArkSteamManager
from config import get_global_config, switch_config
from ue.hierarchy import find_parent_classes, iterate_all, tree
from utils.log import get_logger
from utils.tree import Node

# pylint: enable=invalid-name

logger = get_logger(__name__)

EPILOG = '''example: python uegrep.py Dodo_Character_C'''

DESCRIPTION = '''Perform searches in the game asset hierarchy.'''

args: argparse.Namespace = argparse.Namespace()


def modlist(value: str) -> Tuple[str, ...]:
    value = value.strip()
    inputs = [v.strip() for v in value.split(',')]
    mods = tuple(v for v in inputs if v)
    for modid in mods:
        as_int = int(modid)  # pylint: disable=unused-variable  # noqa: F841  # For type-checking only
    return mods


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("uegrep", description=DESCRIPTION, epilog=EPILOG)

    parser.add_argument('--config', type=str, default='config/config.ini', help='config file to use')
    parser.add_argument('--regex', '-r', action='store_true', help='allow regex matching')
    parser.add_argument('--ignore-case', '-i', action='store_true', help='ignore case')
    parser.add_argument('--vanilla', '-v', action='store_true', help='only search core game assets')
    parser.add_argument('--output-paths', action='store_true', help='output full paths instead of just assets')

    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument('--asset-only', '-a', action='store_true', help='search only asset names (ignore class name)')
    exclusive.add_argument('--class-only', '-c', action='store_true', help='search only class names (ignore asset name)')

    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument('--subs', '-s', action='store_true', help='show sub-classes of those found')
    exclusive.add_argument('--parents', '-p', action='store_true', help='show parents classes of those found')

    parser.add_argument('--no-script', '-n', action='store_true', help='restrict parents output to assets only')

    parser.add_argument('searches', metavar='SEARCHES', type=str, nargs='+', help='strings to search for')

    return parser


def run():
    config = get_global_config()
    if args.config:
        config = switch_config(args.config)
    config.settings.SkipInstall = True

    arkman = ArkSteamManager(config=config)
    arkman.ensureSteamCmd()
    arkman.ensureGameUpdated()
    arkman.ensureModsUpdated(config.mods)

    initialise_hierarchy(arkman)

    args.mods = ['', *set(get_official_mods()) - {'111111111'}] if args.vanilla else None

    for result in sorted(find_matches()):
        output_result(result)


def find_matches() -> Iterator[str]:
    if args.ignore_case:
        searches = list(search.lower() for search in args.searches)
    else:
        searches = list(args.searches)

    if args.regex:
        regexes = [re.compile(search, flags=re.I if args.ignore_case else 0) for search in searches]

    for cls_name in iterate_all():
        if args.mods is not None:
            modid = get_modid_from_class_name(cls_name)
            if modid not in args.mods:
                continue

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
            if do_simple_searches_match(searches, name):
                yield cls_name


def output_result(result: str):
    print(format_result(result))
    if args.subs:
        node = tree[result]
        display_subs(node, 1)
    if args.parents:
        for i, parent_cls_name in enumerate(find_parent_classes(result)):
            if args.no_script and not parent_cls_name.startswith('/Game'):
                break
            print(f'{"  "*(i+1)}{format_result(parent_cls_name)}')


def display_subs(node: Node[str], level: int):
    indent = '    ' * level
    for child in sorted(node.nodes, key=lambda n: n.data):
        if get_modid_from_class_name(child.data) not in args.mods:
            continue
        print(f'{indent}{format_result(child.data)}')
        display_subs(child, level + 1)


def main():
    basicConfig(level=WARNING)
    global args  # pylint: disable=global-statement, invalid-name
    args = create_parser().parse_args()
    try:
        run()
    except Exception:  # pylint: disable=bare-except
        logger.exception('Caught exception. Aborting.')


def get_modid_from_class_name(cls_name):
    parts = cls_name.strip('/').split('/')
    if len(parts) < 3 or parts[0] != 'Game' or parts[1] != 'Mods':
        return ''
    return parts[2]


def do_simple_searches_match(searches: list[str], input: str) -> bool:
    if args.ignore_case:
        input = input.lower()  # searches are already lowercase

    if args.asset_only:
        input = input.split('.')[0]
    elif args.class_only:
        input = input.split('.')[-1]

    for search in searches:
        # Bail if any negative match matches
        if search.startswith('-'):
            if search[1:] in input:
                return False

        # Bail if any positive match doesn't match
        elif search not in input:
            return False

    return bool(searches)


def format_result(result: str) -> str:
    if args.output_paths or not result.startswith('/Game'):
        return result
    return result.split('.')[0]


if __name__ == '__main__':
    main()
