from logging import NullHandler, getLogger
from typing import Iterable

from automate.discovery import AssetTester, Discoverer
from ue.asset import UAsset
from ue.loader import AssetLoader, AssetLoadException

from ..asset import findSubComponentParentPackages
from ..common import CHR_PKG, DCSC_PKG
from ..tree import inherits_from, walk_parents

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class SpeciesTester(AssetTester):
    @classmethod
    def get_category_name(cls) -> str:
        return 'species'

    @classmethod
    def get_file_extensions(cls) -> Iterable[str]:
        return ('.uasset', )

    @classmethod
    def get_requires_properties(cls) -> bool:
        return False

    def is_a_fast_match(self, mem: bytes) -> bool:
        return b'ShooterCharacterMovement' in mem

    def is_a_full_match(self, asset: UAsset) -> bool:
        '''
        Check that the asset inherits from Character and it or one of
        its parents has a component that inherits from DCSC.
        '''
        assert asset.assetname
        assert asset.loader

        if not asset.assetname.startswith('/Game'):
            return False

        loader: AssetLoader = asset.loader

        # Must inherit from Character somewhere down the line
        if not inherits_from(asset, CHR_PKG):
            return False

        # Check all parents - if any has a sub-component that inherits from DCSC, we're good
        def check_component(assetname: str) -> bool:
            if not assetname.startswith('/Game'):
                return False

            try:
                for cmp_assetname in findSubComponentParentPackages(loader[assetname]):
                    if not cmp_assetname.startswith('/Game'):
                        continue
                    cmp_asset = loader[cmp_assetname]
                    if inherits_from(cmp_asset, DCSC_PKG):
                        return True  # finish walk early
            except AssetLoadException as ex:
                logger.warning('Failed to check inheritance of potential species: %s', str(ex))
                return False  # abort early

            return False

        # Check this asset first
        if check_component(asset.assetname):
            return True

        # Then check all parents in the tree
        found_dcsc = walk_parents(asset, check_component)

        return found_dcsc or False
