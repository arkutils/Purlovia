from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *
from typing import cast

from ark.asset import find_dcsc
from ark.overrides import OverrideSettings, get_overrides_for_species
from ark.types import DCSC, PrimalDinoCharacter
from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.proxy import UEProxyStructure
from ue.utils import clean_double as cd

from .species.attacks import gather_attack_data

__all__ = [
    'SpeciesStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class SpeciesStage(JsonHierarchyExportStage):
    def get_skip(self) -> bool:
        return not self.manager.config.export_wiki.ExportSpecies

    def get_field(self):
        return 'species'

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_format_version(self):
        return "1"

    def get_ue_type(self):
        return PrimalDinoCharacter.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        species: PrimalDinoCharacter = cast(PrimalDinoCharacter, proxy)

        asset: UAsset = proxy.get_source().asset
        assert asset.assetname and asset.default_class
        modid: Optional[str] = self.manager.loader.get_mod_id(asset.assetname)
        overrides = get_overrides_for_species(asset.assetname, modid)

        if _should_skip_species(species, overrides):
            return None

        results: Dict[str, Any] = dict(
            name=species.DescriptiveName[0],
            blueprintPath=asset.default_class.fullname,
            dinoNameTag=species.DinoNameTag[0],
            customTag=species.CustomTag[0],
            targetingTeamName=species.TargetingTeamNameOverride[0],
            mass=species.Mass[0],
            dragWeight=species.DragWeight[0],
        )

        results['falling'] = dict(
            dmgMult=species.FallDamageMultiplier[0],
            maxSpeed=species.MaxFallSpeed[0],
        )

        results['speed'] = species.MaxWalkSpeed[0]
        if species.bCanRun[0]:
            results['speedSprint'] = cd(species.MaxWalkSpeed[0] * species.RunningSpeedModifier[0])
        else:
            results['speedSprint'] = None

        results.update(gather_attack_data(species))

        return results


def _should_skip_species(species: PrimalDinoCharacter, overrides: OverrideSettings):
    if overrides.skip_export:
        return True

    if not species.has_override('DescriptiveName'):
        return True

    # Check the local DCSC
    dcsc_export = find_dcsc(species.get_source().asset)
    if not dcsc_export:
        return None

    # Check if there no overrides of MaxStatusValues
    dcsc: DCSC = gather_properties(dcsc_export)  # does not respect prioritising DCSCs, but that's okay here
    if not any((not dcsc.has_override('MaxStatusValues', i)) for i in range(12)):
        return True

    return False
