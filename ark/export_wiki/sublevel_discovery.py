from logging import NullHandler, getLogger
from typing import Iterable

from automate.discovery import AssetTester, Discoverer
from ue.asset import UAsset
from ue.loader import AssetLoader, AssetLoadException

from ..asset import findSubComponentParentPackages
from ..common import CHR_PKG, DCSC_PKG
from ..tree import inherits_from, walk_parents
from .common import KNOWN_KLASS_NAMES

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class SublevelTester(AssetTester):
    @classmethod
    def get_category_name(cls) -> str:
        return 'sublevels'

    @classmethod
    def get_file_extensions(cls) -> Iterable[str]:
        return ('.umap', )

    @classmethod
    def get_requires_properties(cls) -> bool:
        return False

    def is_a_fast_match(self, mem: bytes) -> bool:
        if b'World' in mem:
            # TODO: Fast check might over- or even underselect.
            for klass_name in KNOWN_KLASS_NAMES:
                if klass_name.encode() in mem:
                    return True

        return False

    def is_a_full_match(self, asset: UAsset) -> bool:
        # TODO: Implement full check for sublevels using cached inheritance chains (pending).
        if 'tile_info' in asset.field_values:
            return True

        return False
