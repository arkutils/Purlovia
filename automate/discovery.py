'''
Provides methods for scanning and categorising assets.
'''

from abc import ABC, abstractclassmethod, abstractmethod, abstractproperty
from typing import *

from config import ConfigFile, get_global_config
from ue.asset import UAsset
from ue.loader import AssetLoader

# pylint: disable=unnecessary-pass # present for readability and to help the formatter

__all__ = [
    'AssetTester',
    'Discoverer',
]


class AssetTester(ABC):
    '''A class implementing a way to test assets for a single 'category'.'''
    @abstractclassmethod
    def get_category_name(cls) -> str:
        '''Return a category name for this tester, e.g. "species".'''
        pass

    @abstractclassmethod
    def get_file_extensions(cls) -> Iterable[str]:
        '''Return a list of asset file extensions used for this tester, e.g. [".uasset"].'''
        pass

    @abstractclassmethod
    def get_requires_properties(cls) -> bool:
        '''Return True if `is_a_full_match` requires access to export properties.'''
        pass

    @abstractmethod
    def is_a_fast_match(self, mem: bytes) -> bool:
        '''
        Return True if this asset is a possible match, using the fastest methods possible to guess.
        This method can over-select but it *must not* under-select.
        '''
        pass

    @abstractmethod
    def is_a_full_match(self, asset: UAsset) -> bool:
        '''
        Return True if this asset is a match, using the most correct method possible.
        This will generally include checking the inheritance tree for an expected parent class.
        '''
        pass


class Discoverer:
    def __init__(self, loader: AssetLoader, config: ConfigFile = get_global_config()):
        self.testers: Set[AssetTester] = set()
        self.loader = loader
        self.global_excludes: Set[str] = set(config.optimisation.SearchIgnore)
        self.testers_by_ext: Dict[str, Set[AssetTester]] = dict()

    def register_asset_tester(self, tester: AssetTester):
        self.testers.add(tester)

        # Maintain a fast lookup of testers by extension
        for ext in tester.get_file_extensions():
            ext = ext.lower()
            ext_testers = self.testers_by_ext.setdefault(ext, set())
            ext_testers.add(tester)

    def run(self, path: str, extra_excludes: Iterable[str] = ()) -> Dict[str, List[str]]:
        '''
        Run discovery on the given asset path, testing each asset with each registered tester.
        Exclusions come from extra_excludes plus configured ignored paths.
        Result is a dict entry per tester category name containing a list of matching assetnames.
        '''
        assert self.testers

        results = self._create_empty_results()
        extensions: Set[str] = set().union(*(tester.get_file_extensions() for tester in self.testers))  # type: ignore
        excludes = (*extra_excludes, *self.global_excludes)

        # Step through all assets with any requested file extension
        asset_iterator = self.loader.find_assetnames('.*', path, exclude=excludes, extension=extensions, return_extension=True)
        for (assetname, ext) in asset_iterator:
            assetnames = self._test_asset(assetname, ext)
            for category in assetnames:
                results[category].append(assetname)

        return results

    def _create_empty_results(self) -> Dict[str, List[str]]:
        '''Initialise outputs for each tester type.'''
        return {tester.get_category_name(): list() for tester in self.testers}

    def _test_asset(self, assetname: str, ext: str) -> Iterable[str]:
        '''Check the given asset against the registered testers, yielding the names of ones that match.'''
        # Load and test against the raw memory first, to be as fast as possible
        mem_view = self.loader.load_raw_asset(assetname)
        mem: bytes = mem_view.obj

        ext_testers = self.testers_by_ext[ext.lower()]
        fast_matches: List[AssetTester] = [tester for tester in ext_testers if tester.is_a_fast_match(mem)]

        del mem

        # Bail early if no fast matches
        if not fast_matches:
            return []

        # Load and parse the asset
        # TODO: Don't parse properties if we don't need them
        # need_props = any(tester.get_requires_properties() for tester in fast_matches)
        try:
            asset: UAsset = self.loader[assetname]
        except Exception:  # pylint: disable=broad-except
            print("Failed to load asset: " + assetname)
            return []

        # Test fully only for the ones that matched quickly
        full_matches = [tester for tester in fast_matches if tester.is_a_full_match(asset)]

        # Return the matching category names
        return [tester.get_category_name() for tester in full_matches]
