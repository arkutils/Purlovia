import argparse
from pathlib import Path
from typing import Any, Iterable, Tuple

from config import ConfigFile, get_global_config, switch_config
from utils.log import get_logger

from .run import ROOT_TYPES, run, setup_logging
from .run_sections import parse_runlist, should_run_section, verify_sections

# pylint: enable=invalid-name

__all__ = ('main', )

logger = get_logger(__name__)

EPILOG = '''example: python -m automate --skip-install'''

DESCRIPTION = '''Perform an automated run of Purlovia, optionally overriding config or individual parts of the process.'''


def commalist(value: str) -> Tuple[str, ...]:
    value = value.strip()
    inputs = [v.strip() for v in value.split(',')]
    mods = tuple(v for v in inputs if v)
    return mods


class VerifySectionsAction(argparse.Action):  # pylint: disable=too-few-public-methods

    def __init__(self, option_strings, dest, nargs=None, roots=None, **kwargs):
        if not roots:
            raise ValueError("roots must be set")
        self.roots = roots
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        sections = parse_runlist(values)

        try:
            verify_sections(sections, self.roots)
        except ValueError as err:
            raise argparse.ArgumentError(self, str(err))

        setattr(namespace, self.dest, sections)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("automate", description=DESCRIPTION, epilog=EPILOG)

    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument('--live', action='store_true', help='enable live mode [requires git identity]')

    parser.add_argument('--remove-cache', action='store_true', help='remove the (dev only) asset tree cache')
    parser.add_argument('--pause', help=argparse.SUPPRESS, action='store_true')

    parser.add_argument('--skip-install', action='store_true', help='skip install/update of game and mods')
    parser.add_argument('--skip-extract', action='store_true', help='skip extracting all data completely')
    parser.add_argument('--skip-version-extraction', action='store_true', help='skip running the game to extract its version')
    parser.add_argument('--skip-commit', action='store_true', help='skip git commit of the output repo (use dry-run mode)')
    parser.add_argument('--skip-pull', action='store_true', help='skip git pull or reset of the output repo')
    parser.add_argument('--skip-push', action='store_true', help='skip git push of the output repo')

    parser.add_argument('--notify', action='store_true', help='enable sending error notifications')

    parser.add_argument('--list-stages', action='store_true', help='display extraction stage options and exit')

    parser.add_argument('--maps', action='store', type=commalist, help='override which maps to export (comma-separated)')
    parser.add_argument('--mods', action='store', type=commalist, help='override which mods to export (comma-separated)')
    parser.add_argument('--include-official-mods', action='store_true', help='add official mods to the list of mods to export')

    parser.add_argument('--config-file', action='store', help='override the config file path')
    parser.add_argument('--output-path', action='store', help='override the output path')

    parser.add_argument('sections',
                        action=VerifySectionsAction,
                        default=parse_runlist('all'),
                        roots=ROOT_TYPES,
                        metavar='SECTIONS',
                        nargs='?',
                        help='override extraction sections to be run (format: `all,-root1,-root2.stage1`, default: `all`)')

    return parser


def handle_args(args: Any, parser: argparse.ArgumentParser) -> ConfigFile:
    try:
        if args.config_file is not None:
            config = switch_config(args.config_file)
        else:
            config = get_global_config()
    except Exception as err:
        parser.error(f'Failed to load config file: {err}')

    # Action selections
    config.run_sections = args.sections

    # If stage list requested, skip everything else
    if args.list_stages:
        config.display_sections = True
        return config

    if args.pause:
        print('Pausing before running anything...')
        input('Press enter to continue...\n')

    # Logging can be setup now we know we're not aborting
    setup_logging()

    if args.live:
        logger.info('LIVE mode enabled')
        config.settings.SkipGit = False
        config.git.UseReset = True
        config.git.UseIdentity = True
        config.errors.SendNotifications = True
    else:
        logger.info('DEV mode enabled')
        config.git.UseIdentity = False
        config.git.SkipCommit = True
        config.git.SkipPush = True
        config.errors.SendNotifications = False

    config.dev.DevMode = not args.live

    if args.notify:  # to enable notifications in dev mode
        config.errors.SendNotifications = True

    if args.remove_cache:
        config.dev.ClearHierarchyCache = True

    if args.skip_install:
        config.settings.SkipInstall = True
    if args.skip_extract:
        config.settings.SkipExtract = True
    if args.skip_version_extraction:
        config.settings.SkipRunGame = True

    # Parse the user's mod list
    mods: Tuple[str, ...] | None = None
    if args.mods is not None:
        try:
            mods = calculate_mods(args.mods, config.mods)
        except Exception as err:
            parser.error(str(err))

    if mods is not None:
        config.extract_mods = mods
    if args.include_official_mods:
        config.extract_mods = tuple(set(config.extract_mods or ()) | set(config.settings.SeparateOfficialMods))

    logger.info('Extracing mods: %s', ', '.join(config.extract_mods) if config.extract_mods else '(none)')

    if args.maps is not None:
        config.extract_maps = args.maps

    if args.output_path is not None:
        config.settings.OutputPath = Path(args.output_path)

    # Git actions
    if args.skip_pull:
        config.git.SkipPull = True
    if args.skip_commit:
        config.git.SkipCommit = True
    if args.skip_push:
        config.git.SkipPush = True

    return config


def display_sections(config: ConfigFile):
    print('Available stages:')
    for root_type in ROOT_TYPES:
        root = root_type()  # type: ignore
        root_name = root.get_name()
        print(f'  {root_name}')
        for stage in root.stages:
            stage_name = stage.get_name()
            fullname = f'{root_name}.{stage_name}'
            match = should_run_section(fullname, config.run_sections)
            print(f'    {fullname} {("[*]" if match else "")}')


def calculate_mods(user: Iterable[str], existing: Iterable[str]) -> Tuple[str, ...]:
    '''
    >>> calculate_mods(('123',), ('123', '456')) == ('123',)
    True
    >>> calculate_mods(('-123',), ('123', '456')) == ('456',)
    True
    >>> calculate_mods(('+789',), ('123', '456')) == ('789',)
    True

    >>> calculate_mods(('+123',), ('123', '456'))
    Traceback (most recent call last):
    ...
    ValueError: Added mods are already present in config: 123

    >>> calculate_mods(('123',), ('456',))
    Traceback (most recent call last):
    ...
    ValueError: Selected mods must be present in config: 123

    >>> calculate_mods(('-123', '456'), ())
    Traceback (most recent call last):
    ...
    ValueError: Cannot mix selected and deselected mods

    >>> calculate_mods(('-123', '+456'), ())
    Traceback (most recent call last):
    ...
    ValueError: Cannot mix selected and deselected mods

    >>> calculate_mods(('-123',), ('456',))
    Traceback (most recent call last):
    ...
    ValueError: Deselected mods are not present: 123

    >>> calculate_mods(('+',), ('123',))
    Traceback (most recent call last):
    ...
    ValueError: Empty mod id

    >>> calculate_mods(('-',), ('123',))
    Traceback (most recent call last):
    ...
    ValueError: Empty mod id
    '''
    user_set = set(user)
    existing_set = set(existing)
    has_negatives = any(modid.startswith('-') for modid in user)
    all_negatives = not any(not modid.startswith('-') for modid in user)

    # No negatives?
    if not has_negatives:
        user_set = {modid for modid in user_set if not modid.startswith('+')}

        # Handle mods that should be processed when not in config
        additions = set(modid.lstrip('+') for modid in user if modid.startswith('+'))
        if any(True for entry in additions if not entry):
            raise ValueError("Empty mod id")
        present_additions = additions.intersection(existing_set)
        if present_additions:
            raise ValueError("Added mods are already present in config: " + ','.join(present_additions))

        not_present = user_set - (existing_set | additions)
        if not_present:
            raise ValueError("Selected mods must be present in config: " + ','.join(not_present))

        return tuple(sorted(user_set | additions))

    # If any are negative, all entries must be negative
    if not all_negatives:
        raise ValueError("Cannot mix selected and deselected mods")

    # Work out which mods to include
    cleaned = set(modid.lstrip('-') for modid in user)
    if any(True for entry in cleaned if not entry):
        raise ValueError("Empty mod id")

    # Check none were mis-typed
    excess = cleaned - existing_set
    if excess:
        raise ValueError("Deselected mods are not present: " + ','.join(excess))

    result = tuple(existing_set - cleaned)
    return result


def main():
    parser = create_parser()
    args = parser.parse_args()
    config = handle_args(args, parser)
    if config.display_sections:
        display_sections(config)
    else:
        run(config)
