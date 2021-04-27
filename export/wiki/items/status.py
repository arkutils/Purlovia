from typing import Dict, Optional, Tuple

from ark.types import PrimalItem
from automate.hierarchy_exporter import ExportModel, Field
from export.wiki.models import FloatLike, MinMaxRange
from ue.properties import FloatProperty
from ue.utils import clean_float


class StatEffectData(ExportModel):
    value: FloatProperty = Field(..., description="Stat value to set/add")
    useItemQuality: bool = Field(False, description="Whether item quality is used")
    pctOf: Optional[str] = Field(None, description="If set, this effect's value is a percentage of current/max stat value.")
    pctAbsRange: Optional[MinMaxRange] = None
    setValue: bool = Field(False, description="Whether the current stat value is overriden by this effect's value.")
    setAddValue: bool = Field(False, description="Whether this effect's is instantly added to current stat value.")
    forceUseOnDino: bool = Field(False, description="Whether can be used on dinos")
    allowWhenFull: bool = Field(True, description="Whether allowed when stat is full")
    qualityMult: float = Field(1.0, description="Item quality effect (addition)")
    duration: FloatLike = Field(0, description="Effect duration in seconds")


def convert_status_effect(entry) -> Tuple[str, StatEffectData]:
    d = entry.as_dict()
    stat_name = d['StatusValueType'].get_enum_value_name().lower()
    result = StatEffectData(
        value=d['BaseAmountToAdd'],
        useItemQuality=bool(d['bUseItemQuality']),
        setValue=bool(d['bSetValue']),
        setAddValue=bool(d['bSetAdditionalValue']),
        forceUseOnDino=bool(d['bForceUseStatOnDinos']),
        allowWhenFull=bool(d['bDontRequireLessThanMaxToUse']),
        qualityMult=float(d['ItemQualityAddValueMultiplier']),

        # 'bContinueOnUnchangedValue = (BoolProperty) False',
        # 'bResetExistingModifierDescriptionIndex = (BoolProperty) False',
        # 'LimitExistingModifierDescriptionToMaxAmount = (FloatProperty) 0.0',
        # 'ItemQualityAddValueMultiplier = (FloatProperty) 1.0',
        # 'StopAtValueNearMax = (ByteProperty) ByteProperty(EPrimalCharacterStatusValue, EPrimalCharacterStatusValue::MAX)',
        # 'ScaleValueByCharacterDamageType = (ObjectProperty) None'),
    )

    pctOfMax = d['bPercentOfMaxStatusValue']
    pctOfCur = d['bPercentOfCurrentStatusValue']
    if pctOfCur or pctOfMax:
        result.pctOf = 'max' if pctOfMax else 'current'
        result.pctAbsRange = MinMaxRange(min=d['PercentAbsoluteMinValue'], max=d['PercentAbsoluteMaxValue'])

    if d['bAddOverTimeSpeedInSeconds']:
        result.duration = d['AddOverTimeSpeed']
    else:
        if d['AddOverTimeSpeed'] == 0:
            # Assume instant
            result.duration = 0
        else:
            # Duration = amount / speed
            duration = abs(d['BaseAmountToAdd']) / d['AddOverTimeSpeed']
            duration = clean_float(duration)
            result.duration = duration

    return (stat_name, result)


def convert_status_effects(item: PrimalItem) -> Dict[str, StatEffectData]:
    # Behavior verified 26/04/2021.
    status_effects = item.UseItemAddCharacterStatusValues[0]
    out = dict()

    # Only first ever entry for a stat is used.
    for entry in status_effects.values:
        stat, effect = convert_status_effect(entry)
        if stat not in out:
            out[stat] = effect

    return out
