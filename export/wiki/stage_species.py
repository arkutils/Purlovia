from typing import Any, Dict, List, Optional, Set, Tuple, cast

from ark.gathering import gather_dcsc_properties
from ark.overrides import OverrideSettings, TamingMethod, get_overrides_for_species
from ark.taming_food.datatypes import SpeciesItemOverride
from ark.taming_food.species import collect_species_data_by_proxy
from ark.types import PrimalDinoCharacter
from ark.variants import get_variants_from_assetname, get_variants_from_species
from automate.hierarchy_exporter import ExportFileModel, ExportModel, Field, JsonHierarchyExportStage
from ue.asset import UAsset
from ue.loader import AssetLoadException
from ue.properties import FloatProperty, StringLikeProperty
from ue.proxy import UEProxyStructure
from utils.log import get_logger

from .flags import gather_flags
from .species.attacks import AttackData, gather_attack_data
from .species.cloning import CloningData, gather_cloning_data
from .species.death import DeathData, gather_death_data
from .species.movement import MovementModes, StaminaRates, gather_movement_data
from .species.xp import LevelData, convert_level_data

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
    'bDieIfLeftWater',

    # Other related stuff not included:
    # bCanRun/Jump/Walk/Crouch/etc - covered with the movement speed section
    # bUseColorization - in future color data will cover this
    # bCanHaveBaby/bUseBabyGestation - add breeding section
)


class FallingData(ExportModel):
    dmgMult: FloatProperty = Field(..., title="Damage multiplier")
    maxSpeed: FloatProperty = Field(..., title="Max speed")


class TamingOverride(ExportModel):
    class_name: str = Field(alias="cls")
    untamed_priority: float = 1.0
    overrides: Dict[str, float] = Field(
        {},
        description="Overrides that replace the food's base value (only values != 0)",
    )
    mults: Dict[str, float] = Field(
        {},
        description="Multipliers that apply on top of the food's normal affects, per stat (only values != 1)",
    )


class Species(ExportModel):
    name: Optional[str] = Field(
        None,
        description="Descriptive name",
    )
    bp: str = Field(
        ...,
        title="Full blueprint path",
    )

    dinoNameTag: Optional[StringLikeProperty] = Field(
        None,
        title="Dino name tag",
        description="Only known use is saddle compatibility and server configuration",
    )
    customTag: Optional[StringLikeProperty] = Field(
        None,
        title="Custom tag",
        description="",
    )
    targetingTeamName: Optional[StringLikeProperty] = Field(
        None,
        title="Targeting team name",
        description="Prevent friendly fire with creatures in the same team",
    )

    mass: Optional[FloatProperty] = Field(
        None,
        description="Physics mass, used as a limit in some immobilisation systems",
    )
    dragWeight: Optional[FloatProperty] = Field(
        None,
        title="Drag weight",
        description="Apparent weight for many game systems including carrying and boss arena entry limits",
    )

    variants: Optional[Tuple[str, ...]] = Field(
        tuple(),
        description="List of relevant variant names",
    )
    flags: Optional[List[str]] = Field(
        list(),
        description="Relevant boolean flags that are True for this species",
    )

    leveling: LevelData = LevelData()
    cloning: Optional[CloningData] = Field(
        None,
        description="Full cost is determined by Ceil(costBase + costLevel x CharacterLevel). " +
        "Cloning time is determined by (timeBase + timeLevel x CharacterLevel) / BabyMatureSpeedMulti.",
    )

    falling: Optional[FallingData]
    movementW: Optional[MovementModes] = Field(None, title="Movement (wild)")
    movementD: Optional[MovementModes] = Field(None, title="Movement (domesticated)")
    movementR: Optional[MovementModes] = Field(None, title="Movement (ridden)")
    staminaRates: Optional[StaminaRates]
    attack: Optional[AttackData]
    death: DeathData = DeathData()

    food: List[TamingOverride] = Field(
        [],
        title="Taming food",
        description="A list of food overrides that apply when feeding this species",
    )


class SpeciesExportModel(ExportFileModel):
    species: List[Species]

    class Config:
        title = "Species data for the Wiki"


def should_skip_from_variants(variants: Set[str], overrides: OverrideSettings) -> bool:
    skip_variants = set(name for name, use in overrides.variants_to_skip_export.items() if use)
    return bool(variants & skip_variants)


def is_trappable_with_fish_basket(species: PrimalDinoCharacter) -> bool:
    # Returns True if the creature can be trapped with a Fish Basket when wild.
    # Explicit bool cast to avoid a BoolProperty|bool union in return type.
    return bool(species.bAllowTrapping[0] and not species.bPreventWildTrapping[0])


def is_creature_tameable(species: PrimalDinoCharacter, variants: Set[str], overrides: OverrideSettings) -> bool:
    if overrides.taming_method:
        return overrides.taming_method != TamingMethod.none

    # Properties that control Fish Baskets.
    if is_trappable_with_fish_basket(species) and species.bIsTrapTamed[0]:
        return True

    # Preemptive check for standard taming methods (like knockout or passive).
    if not species.bCanBeTamed[0]:
        return False

    # Taming is forcefully disabled on these dinos by the mission controller.
    if 'Mission' in variants or 'VR' in variants:
        return False

    violent = species.bCanBeTorpid[0] and not species.bPreventSleepingTame[0]
    nonviolent = species.bSupportWakingTame[0]
    return violent or bool(nonviolent)


class SpeciesStage(JsonHierarchyExportStage):

    def get_name(self) -> str:
        return 'species'

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_format_version(self):
        return "4"

    def get_ue_type(self):
        return PrimalDinoCharacter.get_ue_type()

    def get_schema_model(self):
        return SpeciesExportModel

    def extract(self, proxy: UEProxyStructure) -> Any:
        species: PrimalDinoCharacter = cast(PrimalDinoCharacter, proxy)

        asset: UAsset = proxy.get_source().asset
        assert asset.assetname and asset.default_class
        modid: Optional[str] = self.manager.loader.get_mod_id(asset.assetname)
        overrides = get_overrides_for_species(asset.assetname, modid)

        if _should_skip_species(species, overrides):
            return None

        try:
            dcsc = gather_dcsc_properties(species.get_source())
        except AssetLoadException as ex:
            logger.warning(f'Gathering properties failed for {asset.assetname}: %s', str(ex))
            return None

        name = str(species.DescriptiveName[0])

        variants = get_variants_from_assetname(asset.assetname, overrides) | get_variants_from_species(species, overrides)
        if variants:
            if should_skip_from_variants(variants, overrides):
                return None

        out = Species(bp=asset.default_class.fullname)
        out.name = name
        out.dinoNameTag = species.DinoNameTag[0]
        out.customTag = species.CustomTag[0]
        out.targetingTeamName = species.TargetingTeamNameOverride[0]
        out.mass = species.CharacterMovement[0].Mass[0]
        out.dragWeight = species.DragWeight[0]

        if variants:
            out.variants = tuple(sorted(variants))

        out.flags = gather_flags(species, OUTPUT_FLAGS)
        if is_creature_tameable(species, variants, overrides):
            out.flags.append('isTameable')
        if is_trappable_with_fish_basket(species):
            out.flags.append('canBeWildTrappedWithFishBasket')
        if species.bIsTrapTamed[0]:
            out.flags.append('canBeTamedWithFishBasket')

        if not species.bIsBossDino[0]:
            out.leveling = convert_level_data(species, dcsc)
        out.cloning = gather_cloning_data(species)

        out.falling = FallingData(
            dmgMult=species.FallDamageMultiplier[0],
            maxSpeed=species.MaxFallSpeed[0],
        )

        movement = gather_movement_data(species, dcsc)
        out.movementW = movement.movementW
        out.movementD = movement.movementD
        out.movementR = movement.movementR
        out.staminaRates = movement.staminaRates

        out.attack = gather_attack_data(species)
        out.death = gather_death_data(species)

        out.food = gather_food_data(species)

        return out


def _should_skip_species(species: PrimalDinoCharacter, overrides: OverrideSettings):
    if overrides.skip_export:
        return True

    if not species.has_override('DescriptiveName'):
        return True

    return False


def gather_food_data(species: PrimalDinoCharacter):
    foods = collect_species_data_by_proxy(species)

    def convert(effect: SpeciesItemOverride) -> TamingOverride:
        return TamingOverride(
            class_name=effect.bp[effect.bp.rfind('.') + 1:],
            untamed_priority=effect.untamed_priority,
            overrides=effect.overrides,
            mults=effect.mults,
        )

    return [convert(food) for food in foods]
