from enum import Enum
from math import ceil
from typing import List, Optional

from ark.types import BASE_PGD_PKG, COREMEDIA_PGD_PKG, DinoCharacterStatusComponent, PrimalDinoCharacter
from automate.hierarchy_exporter import ExportModel, Field
from export.wiki.models import BoolLike, FloatLike, IntLike, MinMaxChanceRange
from ue.loader import AssetNotFound
from ue.properties import PropertyTable
from ue.utils import clean_float


class LevelExperienceRampType(Enum):
    '''
    Contains experience ramp types of dinos.
    Equivalent to ELevelExperienceRampType from ARK engine module.
    '''
    # DevKit Verified
    Player = 0
    DinoEasy = 1
    DinoMedium = 2
    DinoHard = 3
    MAX = 4


class LevelData(ExportModel):
    wildForcedLevel: Optional[IntLike] = Field(None, description="A value here means the spawns will not respect difficulty.")
    ignoresLevelModifiers: BoolLike = Field(
        False,
        description="Forced level will also not be influenced by spawner's level scaling or other settings on the species.",
    )
    wildLevelTable: List[MinMaxChanceRange] = [
        MinMaxChanceRange(chance=0.5405405, min=1.0, max=5.0),  # weight = 1.0
        MinMaxChanceRange(chance=0.2702703, min=6.0, max=12.0),  # weight = 0.5
        MinMaxChanceRange(chance=0.1351351, min=13.0, max=20.0),  # weight = 0.25
        MinMaxChanceRange(chance=0.05405405, min=21.0, max=30.0),  # weight = 0.1
    ]

    xpRamp: str = Field(
        'DinoEasy',
        description="Name of ramp that describes amount of experience needed to progress.",
    )
    maxExperience: FloatLike = 22213970
    maxTameLevels: int = Field(
        88,
        description="Max amount of level ups this species can have at default server settings.",
    )
    levelCapOffset: IntLike = Field(
        0,
        description=
        "Extra levels this species can have before getting destroyed on servers with the DestroyTamesOverLevelClamp setting "
        "enabled.",
    )
    mutagenCost: int = Field(0, description="Amount of Mutagen needed to use it on this dino.")


def convert_level_data(species: PrimalDinoCharacter, dcsc: DinoCharacterStatusComponent) -> LevelData:
    try:
        pgd_asset = species.get_source().asset.loader[COREMEDIA_PGD_PKG]
    except AssetNotFound:
        pgd_asset = species.get_source().asset.loader[BASE_PGD_PKG]
    assert pgd_asset.default_export
    pgd: PropertyTable = pgd_asset.default_export.properties

    result = LevelData()

    # Max experience points
    max_xp_override = species.OverrideDinoMaxExperiencePoints[0]
    if max_xp_override > 0:
        result.maxExperience = max_xp_override
    else:
        result.maxExperience = dcsc.MaxExperiencePoints[0]

    # Export ramp type and find one from PGD
    ramp_type = dcsc.LevelExperienceRampType[0].get_enum_value_name()
    if ramp_type != LevelExperienceRampType.DinoEasy.name:
        result.xpRamp = ramp_type

    # Calculate max levels out of max XP.
    ramp_id = LevelExperienceRampType[ramp_type].value
    ramp_prop = pgd.get_property('LevelExperienceRamps', index=ramp_id, fallback=None)
    if not ramp_prop:
        # No ramp (MAX). Tame level ups not possible.
        result.maxTameLevels = 0
    else:
        ramp = ramp_prop.values[0].value
        # Find highest level using a vanilla ramp
        for index, threshold in enumerate(ramp.values):
            if result.maxExperience >= threshold:
                result.maxTameLevels = index + 1
            else:
                break

    # Official servers' level cap
    if species.has_override('DestroyTamesOverLevelClampOffset'):
        result.levelCapOffset = species.DestroyTamesOverLevelClampOffset[0]

    # Wild spawn levels
    base_level_override = species.AbsoluteBaseLevel[0]
    fixed_level = species.bUseFixedSpawnLevel[0]
    if base_level_override != 0 or fixed_level:
        # Forced base level. Does not scale with difficulty.
        result.wildForcedLevel = base_level_override or 1
        result.ignoresLevelModifiers = fixed_level

        # If level modifiers are enabled, multiply the level by final level multiplier.
        if not fixed_level:
            result.wildForcedLevel *= species.FinalNPCLevelMultiplier[0]
    else:
        # Weighed level range table.
        level_weights = species.get('DinoBaseLevelWeightEntries', fallback=None)
        out_level_table = list()

        if level_weights and level_weights.values:
            weight_sum = 0
            entries = list()
            final_mult = species.FinalNPCLevelMultiplier[0]

            # Gather the data into a temporary list, with weight and range.
            for entry in level_weights:
                d = entry.as_dict()
                entries.append((d['EntryWeight'], d['BaseLevelMinRange'] * final_mult, d['BaseLevelMaxRange'] * final_mult))
                weight_sum += d['EntryWeight']

            # Pack gathered data into MinMaxChanceRanges with calculated chances. The properties cannot be modified through INI
            # configs.
            for weight, min_lvl, max_lvl in entries:
                out_level_table.append(
                    MinMaxChanceRange(chance=clean_float(weight / weight_sum),
                                      min=clean_float(min_lvl),
                                      max=clean_float(max_lvl)))

        result.wildLevelTable = out_level_table

    # Calculate required amount of Mutagen needed to use it.
    # Formula extracted from PrimalItemConsumable_Mutagen_C's scripts
    # Vultures cannot use Mutagen as it can't enter their inventories.
    # IsRobot and IsVehicle banned from Mutagen in v329.51.
    if species.DinoNameTag[0] != 'Vulture' and not species.bIsRobot[0] and not species.bIsVehicle[0]:
        mutagen_base = species.MutagenBaseCost[0]
        if mutagen_base <= 0:
            mutagen_base = species.CloneBaseElementCost[0]
        if mutagen_base > 0:
            cost = 1 + 99*mutagen_base

            # Round up 0.5 to conform with in-game calculations.
            if (cost % 1) >= 0.5:
                result.mutagenCost = ceil(cost)
            else:
                result.mutagenCost = round(cost)

    return result
