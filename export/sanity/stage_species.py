from collections import Counter
from pathlib import Path
from typing import List

from ark.overrides import get_overrides
from ark.types import PrimalDinoCharacter
from automate.exporter import ExportStage
from automate.notification import send_to_discord
from ue.hierarchy import find_sub_classes
from utils.log import get_logger

__all__ = [
    'SpeciesStage',
]

logger = get_logger(__name__)


class SpeciesStage(ExportStage):
    def get_name(self):
        return 'species'

    def extract_core(self, _: Path):
        '''Perform sanity tests on core species.'''

        # Count species by prefix (/Game/<part> or /Game/Mods/<id>)
        counter: Counter = Counter()
        for clsname in find_sub_classes(PrimalDinoCharacter.get_ue_type()):
            if not clsname.startswith('/Game'):
                continue

            parts = clsname.split('/')
            if clsname.startswith('/Game/Mods/'):
                modid = self.manager.loader.get_mod_id(clsname)
                assert modid
                parts[3] = modid
                parts = parts[:4]
            else:
                parts = parts[:3]

            counter.update(['/'.join(parts)])

        # Check counts against configured limits
        overrides = get_overrides()
        reports = list()
        for path, min_count in overrides.sanity_checks.min_species.items():
            count = counter.get(path, 0)
            logger.debug('%s = %d (need %d)', path, count, min_count)
            if count < min_count:
                reports.append((path, count, min_count))

        # If anything failed, report and turn off Git push
        if not reports:
            return None

        # Disable git push to hopefully avoid damaging commits
        self.manager.config.git.SkipPush = False

        # Put together a report message
        header = "Species count sanity check failed! (git push disabled):\n"
        lines: List[str] = []
        for path, count, min_count in reports:
            lines.append(f"    {path} expected {min_count}, found {count}\n")

        # Log it
        logger.error(''.join([header] + lines))

        # Send it to Discord
        send_to_discord(log=lines, header='Purlovia failed the species sanity check:')

    def extract_mod(self, path: Path, modid: str):
        '''Perform extraction for the specified mod.'''
        ...
