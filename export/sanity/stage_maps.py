from pathlib import Path
from typing import List

from ark.overrides import get_overrides
from automate.exporter import ExportManager, ExportRoot, ExportStage
from automate.notification import send_to_discord
from export.wiki.maps.discovery import LevelDiscoverer, group_levels_by_directory
from utils.log import get_logger

__all__ = [
    'MapsStage',
]

logger = get_logger(__name__)


class MapsStage(ExportStage):
    discoverer: LevelDiscoverer

    def initialise(self, manager: ExportManager, root: ExportRoot):
        super().initialise(manager, root)
        self.discoverer = LevelDiscoverer(self.manager.loader)

    def get_name(self):
        return 'maps'

    def extract_core(self, _: Path):
        '''Perform sanity tests on core maps.'''

        # Count species by prefix (/Game/<part> or /Game/Mods/<id>)
        maps = group_levels_by_directory(self.discoverer.discover_vanilla_levels())

        # Check counts against configured limits
        overrides = get_overrides()
        reports = list()
        for path, min_count in overrides.sanity_checks.min_maps.items():
            if path not in maps:
                # Map not found
                reports.append((path, 0, min_count))
                continue

            count = len(maps[path])
            logger.debug('%s = %d (need %d)', path, count, min_count)
            if count < min_count:
                reports.append((path, count, min_count))

        # If anything failed, report and turn off Git push
        if not reports:
            return None

        # Disable git push to hopefully avoid damaging commits
        self.manager.config.git.SkipPush = False

        # Put together a report message
        header = "Map count sanity check failed! (git push disabled):\n"
        lines: List[str] = []
        for path, count, min_count in reports:
            lines.append(f"    {path} expected {min_count}, found {count}\n")

        # Log it
        logger.error(''.join([header] + lines))

        # Send it to Discord
        send_to_discord(log=lines, header='Purlovia failed the maps sanity check:')

    def extract_mod(self, path: Path, modid: str):
        '''Perform extraction for the specified mod.'''
        ...
