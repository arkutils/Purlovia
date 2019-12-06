from logging import NullHandler, getLogger
from typing import Iterable

from automate.discovery import AssetTester, Discoverer
from ue.asset import UAsset
from ue.consts import SCRIPT_ENGINE_PKG
from ue.hierarchy import MissingParent, inherits_from
from ue.loader import AssetLoader, AssetLoadException

from .consts import LEVEL_SCRIPT_ACTOR_CLS, WORLD_CLS

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class CompositionSublevelTester(AssetTester):
    @classmethod
    def get_category_name(cls) -> str:
        return 'worldcomposition'

    @classmethod
    def get_file_extensions(cls) -> Iterable[str]:
        return ('.umap', )

    @classmethod
    def get_requires_properties(cls) -> bool:
        return False

    def is_a_fast_match(self, mem: bytes) -> bool:
        return b'World' in mem

    def is_a_full_match(self, asset: UAsset) -> bool:
        if 'tile_info' not in asset.field_values:
            return False

        if not asset.default_export:
            return False

        try:
            return inherits_from(asset.default_export, LEVEL_SCRIPT_ACTOR_CLS) or inherits_from(asset.default_export, WORLD_CLS)
        except AssetLoadException:
            # This asset is more broken than it ever should be.
            return False
