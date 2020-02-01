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
from .species.movement import gather_movement_data

__all__ = [
    'SpeciesStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())

OUTPUT_FLAGS = (
    'bAllowCarryFlyerDinos',
    'bAllowFlyerLandedRider',
    'bAllowMountedWeaponry',
    'bAllowRiding',
    'bCanBeDragged',
    'bCanBeTorpid',
    'bCanDrag',
    'bDoStepDamage',
    'bFlyerAllowRidingInCaves',
    'bIsBossDino',
    'bIsCorrupted',
    'bIsFlyerDino',
    'bIsWaterDino',
    'bPreventCharacterBasing',
    'bPreventEnteringWater',
    'bPreventNeuter',

    # Other related stuff not included:
    # bCanRun - covered with the walk/running speed fields
    # bUseColorization - in future color data will cover this
    # bCanHaveBaby/bUseBabyGestation - add breeding section
)


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

        results['flags'] = _gather_flags(species)

        results['falling'] = dict(
            dmgMult=species.FallDamageMultiplier[0],
            maxSpeed=species.MaxFallSpeed[0],
        )

        results['movementW'] = gather_movement_data(species, float(species.UntamedRunningSpeedModifier[0]))
        results['movementD'] = gather_movement_data(species, float(species.TamedRunningSpeedModifier[0]))

        results.update(gather_attack_data(species))

        return results


def _gather_flags(species: PrimalDinoCharacter) -> List[str]:
    result = [_clean_flag_name(field) for field in OUTPUT_FLAGS if species.get(field, fallback=False)]
    return result


def _clean_flag_name(name: str):
    if len(name) >= 2 and name[0] == 'b' and name[1] == name[1].upper():
        return name[1].lower() + name[2:]

    if len(name) >= 1:
        return name[0].lower() + name[1:]

    raise ValueError("Invalid flag name found")


def _should_skip_species(species: PrimalDinoCharacter, overrides: OverrideSettings):
    if overrides.skip_export:
        return True

    if not species.has_override('DescriptiveName'):
        return True

    return False
