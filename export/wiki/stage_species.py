from pathlib import PurePosixPath
from typing import *
from typing import cast

from ark.asset import find_dcsc
from ark.overrides import OverrideSettings, get_overrides_for_species
from ark.types import PrimalDinoCharacter
from ark.variants import adjust_name_from_variants, get_variants_from_assetname, get_variants_from_species
from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.proxy import UEProxyStructure
from ue.utils import clean_double as cd
from utils.log import get_logger

from .species.attacks import gather_attack_data
from .species.movement import gather_movement_data

__all__ = [
    'SpeciesStage',
]


logger = get_logger(__name__)

OUTPUT_FLAGS = (
    'bAllowCarryFlyerDinos',
    'bAllowFlyerLandedRider',
    'bAllowMountedWeaponry',
    'bAllowRiding',
    'bAllowRidingInWater',
    'bCanBeDragged',
    'bCanBeTorpid',
    'bCanDrag',
    'bCanMountOnHumans',
    'bDoStepDamage',
    'bFlyerAllowRidingInCaves',
    'bIsAmphibious',
    'bIsBigDino',
    'bIsBossDino',
    'bIsCarnivore',
    'bIsCorrupted',
    'bIsFlyerDino',
    'bIsNPC',
    'bIsRaidDino',
    'bIsRobot',
    'bIsWaterDino',
    'bPreventCharacterBasing',
    'bPreventEnteringWater',
    'bPreventNeuter',

    # Other related stuff not included:
    # bCanRun/Jump/Walk/Crouch/etc - covered with the movement speed section
    # bUseColorization - in future color data will cover this
    # bCanHaveBaby/bUseBabyGestation - add breeding section
)


def should_skip_from_variants(variants: Set[str], overrides: OverrideSettings) -> bool:
    skip_variants = set(name for name, use in overrides.variants_to_skip_export.items() if use)
    return bool(variants & skip_variants)


class SpeciesStage(JsonHierarchyExportStage):
    def get_name(self) -> str:
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

        name = str(species.DescriptiveName[0])

        variants = get_variants_from_assetname(asset.assetname, overrides) | get_variants_from_species(species)
        if variants:
            if should_skip_from_variants(variants, overrides):
                return None

            name = adjust_name_from_variants(name, variants, overrides)

        results: Dict[str, Any] = dict(
            name=name,
            blueprintPath=asset.default_class.fullname,
            dinoNameTag=species.DinoNameTag[0],
            customTag=species.CustomTag[0],
            targetingTeamName=species.TargetingTeamNameOverride[0],
            mass=species.CharacterMovement[0].Mass[0],
            dragWeight=species.DragWeight[0],
        )

        if variants:
            results['variants'] = tuple(sorted(variants))

        results['flags'] = _gather_flags(species)

        results['falling'] = dict(
            dmgMult=species.FallDamageMultiplier[0],
            maxSpeed=species.MaxFallSpeed[0],
        )

        results.update(gather_movement_data(species))
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
