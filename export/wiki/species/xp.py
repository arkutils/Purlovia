from enum import Enum
from typing import Optional

from ark.types import COREMEDIA_PGD_PKG, DinoCharacterStatusComponent, PrimalDinoCharacter
from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import FloatProperty, IntProperty, PropertyTable


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
    ramp: str = Field(
        'DinoEasy',
        description="Name of ramp that describes amount of experience needed to progress.",
    )
    maxExperience: Optional[FloatProperty]
    maxLevels: Optional[int] = Field(
        None,
        title="Max Level Ups",
        description="Max amount of level ups this species can have at default server settings.",
    )
    capOffset: Optional[IntProperty] = Field(
        None,
        title="Tame Level Cap Offset",
        description=
        "Number of extra levels (above normal cap) this species can gain when tamed without getting destroyed by validation",
    )


def convert_level_data(species: PrimalDinoCharacter, dcsc: DinoCharacterStatusComponent) -> Optional[LevelData]:
    if bool(species.bIsBossDino[0]):
        return None

    pgd_asset = species.get_source().asset.loader[COREMEDIA_PGD_PKG]
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
        result.ramp = ramp_type

    ramp_id = LevelExperienceRampType[ramp_type].value
    ramp_prop = pgd.get_property('LevelExperienceRamps', index=ramp_id, fallback=None)
    if not ramp_prop:
        # No ramp (MAX).
        result.maxLevels = 0
    else:
        ramp = ramp_prop.values[0].value
        # Find highest level using a vanilla ramp
        for index, threshold in enumerate(ramp.values):
            if result.maxExperience >= threshold:
                result.maxLevels = index + 1
            else:
                break

    # Level cap offset
    if species.has_override('DestroyTamesOverLevelClampOffset'):
        result.capOffset = species.DestroyTamesOverLevelClampOffset[0]

    return result
