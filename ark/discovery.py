from typing import *

from config import get_global_config
from ue.loader import AssetLoader

from .asset import findSubComponentParentPackages
from .tree import inherits_from, walk_parents

__all__ = [
    'SpeciesDiscoverer',
]


class ByRawData:
    '''Very fast/cheap method for bulk searching. Over-selects slightly.'''

    def __init__(self, loader: AssetLoader):
        self.loader = loader

    def is_species(self, assetname: str):
        '''Use binary string matching to check if an asset is a character.'''
        # Load asset as raw data
        mem = self.loader._load_raw_asset(assetname)

        # Check for the presence of required string
        result = b'ShooterCharacterMovement' in mem.obj

        return result

    def is_structure(self, assetname: str):
        '''Use binary string matching to check if an asset is a structure.'''
        # Load asset as raw data
        mem = self.loader._load_raw_asset(assetname)

        # Check for the presence of required string
        result = b'StructureMesh' in mem.obj

        return result


class ByInheritance:
    '''Totally accurate but expensive method, to be used to verify results from other discovery methods.'''

    def __init__(self, loader: AssetLoader):
        self.loader = loader

    CHARACTER_ASSET = '/Game/PrimalEarth/CoreBlueprints/Dino_Character_BP'
    DCSC_ASSET = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP'

    def is_species(self, assetname: str):
        '''
        Load the asset fully and check that it inherits from Character and it or one of
        its parents has a component that inheritcs from DCSC.
        '''
        if not assetname.startswith('/Game'):
            return False

        asset = self.loader[assetname]

        # Must inherit from Character somewhere down the line
        if not inherits_from(asset, ByInheritance.CHARACTER_ASSET):
            return False

        # Check all parents - if any has a sub-component that inherits from DCSC, we're good
        def check_component(assetname: str):
            if not assetname.startswith('/Game'):
                return False

            asset = self.loader[assetname]
            for cmpassetname in findSubComponentParentPackages(asset):
                if not cmpassetname.startswith('/Game'):
                    continue
                cmpasset = self.loader[cmpassetname]
                if inherits_from(cmpasset, ByInheritance.DCSC_ASSET):
                    return True  # finish walk early

        # Check this asset first
        if check_component(assetname):
            return True

        # Then check all parents in the tree
        found_dcsc = walk_parents(asset, check_component)

        return found_dcsc


class SpeciesDiscoverer:
    def __init__(self, loader: AssetLoader):
        self.loader = loader
        self.testByRawData = ByRawData(loader)
        self.testByInheriance = ByInheritance(loader)

        self.global_excludes = tuple(set(get_global_config().optimisation.SearchIgnore))

    def _filter_species(self, assetname: str) -> bool:
        return self.testByRawData.is_species(assetname) and self.testByInheriance.is_species(assetname)

    def discover_vanilla_species(self) -> Iterator[str]:
        # Scan /Game, excluding /Game/Mods and any excludes from config
        for species in self.loader.find_assetnames('.*', '/Game', exclude=('/Game/Mods/.*', *self.global_excludes)):
            if self._filter_species(species):
                yield species

        # Scan /Game/Mods/<modid> for each of the official mods, skipping ones in SeparateOfficialMods
        official_modids = set(get_global_config().official_mods.ids())
        official_modids -= set(get_global_config().settings.SeparateOfficialMods)
        for modid in official_modids:
            for species in self.loader.find_assetnames('.*', f'/Game/Mods/{modid}', exclude=self.global_excludes):
                if self._filter_species(species):
                    yield species

    def discover_mod_species(self, modid: str) -> Iterator[str]:
        # Scan /Game/Mods/<modid>
        for species in self.loader.find_assetnames('.*', f'/Game/Mods/{modid}', exclude=self.global_excludes):
            if self._filter_species(species):
                yield species
