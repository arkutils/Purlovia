import argparse
import logging
import sys
from pathlib import Path, PurePosixPath
from typing import Optional

from automate.git import GitManager
from automate.manifest import MANIFEST_FILENAME, update_manifest
from config import get_global_config
from utils.log import get_logger

__all__ = ('main', )

logger = get_logger(__name__)

EPILOG = '''example: python -m import <source file>:<output location> ... [--dry-run]'''

DESCRIPTION = '''Import extra output files.'''


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("manage", description=DESCRIPTION, epilog=EPILOG)

    parser.add_argument('--dry-run', help='Only print what would be executed - do not run anything', action='store_true')
    parser.add_argument('--skip-push', help='Do not push to Git', action='store_true')
    parser.add_argument('src', help='File to import')
    parser.add_argument('dst', help='Output path (should be within output)')

    return parser


def setup_logging():
    logging.basicConfig(force=True, level=logging.DEBUG)
    logger.info('Starting importer...')
    logger.info('Python version: %s', sys.version)
    logger.info('Python executable: %s', sys.executable)
    logger.info('Command line: %s', ' '.join(sys.argv))


def commit_line_for_file(filename: str) -> Optional[str]:
    '''Works out a reasonable single-line commit comment for the given file path.'''
    config = get_global_config()
    path = PurePosixPath(config.settings.OutputPath / filename)

    # Generic line for removals
    if not Path(path).is_file():
        return f'{path} removed'

    # Don't report manifest file updates
    if path.name.lower() == MANIFEST_FILENAME.lower():
        # Do not report this file
        return False  # type: ignore

    # Don't report files in dotted directories
    for dirname in PurePosixPath(filename).parent.parts:
        if dirname.startswith('.') and len(dirname) > 1:
            # Do not report this file
            return False  # type: ignore

    return f'Manual import of {filename}'


def main():
    parser = create_parser()
    args = parser.parse_args()

    operations: list[tuple[Path, Path]] = []

    source, output = args.src, args.dst

    source = Path(source)
    if not source.exists() or not source.is_file():
        logger.error('Source file not found: %s', source)
        sys.exit(1)

    output = Path(output)
    if not output.parent.exists() or not output.parent.is_dir():
        logger.error('Output location not found: %s', output.parent)
        sys.exit(1)

    operations.append((source, output))

    if not operations:
        logger.error('No operations specified')
        sys.exit(1)

    config = get_global_config()

    config.errors.SendNotifications = False
    config.dev.DevMode = args.dry_run

    if args.dry_run:
        logger.info('Dry run enabled, no changes will be made')
        config.git.UseIdentity = False
        config.git.UseReset = False
        config.git.SkipCommit = True
        config.git.SkipPush = True
        config.git.SkipPull = True
    else:
        config.git.UseIdentity = True
        config.git.UseReset = True
        config.git.SkipCommit = False
        config.git.SkipPush = False
        config.git.SkipPull = False

    if args.skip_push:
        config.git.SkipPush = True

    # print(config.git)
    # sys.exit(0)

    # Ensure Git is setup and ready
    git = GitManager(config=config)
    git.before_exports()

    # Perform the imports
    for source, output in operations:
        logger.info('Importing %s to %s', source, output)
        if not args.dry_run:
            output.write_bytes(source.read_bytes())
        else:
            logger.info('(skipped due to dry run)')

    # For each output folder, update the manifest and commit the changes
    for folder in {output.parent for _, output in operations}:
        logger.info('Updating manifest for %s', folder)
        if not args.dry_run:
            update_manifest(folder)

            # Commit the changes
            git.after_exports(
                folder.relative_to(config.settings.OutputPath),
                "Raptor Claus just dropped some files off for ASB",
                commit_line_for_file,
            )
        else:
            logger.info('(skipped due to dry run)')

    # Push any changes (no tagging)
    logger.info('Pushing changes to Git')
    if not args.dry_run:
        git.finish(None)
    else:
        logger.info('(skipped due to dry run)')

    logger.info('Import completed')
