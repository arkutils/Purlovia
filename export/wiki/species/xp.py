from ark.types import COREMEDIA_PGD_PKG, DinoCharacterStatusComponent, PrimalDinoCharacter
from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import FloatProperty, IntProperty, PropertyTable

RAMP_TYPE_TO_ID = {
    'Player': 0,
    'DinoEasy': 1,
    'MAX': 3,
}


class LevelData(ExportModel):
    ramp: str
    maxExperience: FloatProperty
    maxLevels: int
    capOffset: IntProperty


def convert_level_data(species: PrimalDinoCharacter, dcsc: DinoCharacterStatusComponent) -> LevelData:
    pgd_asset = species.get_source().asset.loader[COREMEDIA_PGD_PKG]
    assert pgd_asset.default_export
    pgd: PropertyTable = pgd_asset.default_export.properties

    max_xp_override = species.OverrideDinoMaxExperiencePoints[0]
    if max_xp_override > 0:
        max_xp = max_xp_override
    else:
        max_xp = dcsc.MaxExperiencePoints[0]

    ramp_type = dcsc.LevelExperienceRampType[0].get_enum_value_name()
    ramp = pgd.get_property('LevelExperienceRamps', index=RAMP_TYPE_TO_ID[ramp_type]).values[0].value

    highest_level = 0
    for index, threshold in enumerate(ramp.values):
        if max_xp >= threshold:
            highest_level = index
        else:
            break

    return LevelData(
        ramp=ramp_type,
        maxExperience=max_xp,
        maxLevels=highest_level,
        capOffset=species.DestroyTamesOverLevelClampOffset[0],
    )
