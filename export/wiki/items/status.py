from typing import Optional, Tuple, Union

from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import FloatProperty


class StatEffectData(ExportModel):
    value: Optional[FloatProperty] = Field(..., title="")
    useItemQuality: bool = Field(False, title="")
    descriptionIndex: Optional[int] = Field(..., title="")
    pctOf: Optional[str] = Field(None, title="")
    pctAbsRange: Optional[Tuple[FloatProperty, FloatProperty]] = Field(None, title="")
    setValue: bool = Field(False, title="")
    setAddValue: bool = Field(False, title="")
    forceUseOnDino: bool = Field(False, title="")
    allowWhenFull: bool = Field(True, title="")
    qualityMult: float = Field(1.0, title="")
    duration: Optional[Union[float, FloatProperty]] = Field(0, title="")


def convert_status_effect(entry) -> Tuple[str, StatEffectData]:
    d = entry.as_dict()
    stat_name = d['StatusValueType'].get_enum_value_name().lower()
    result = StatEffectData(
        value=d['BaseAmountToAdd'],
        useItemQuality=bool(d['bUseItemQuality']),
        descriptionIndex=d['StatusValueModifierDescriptionIndex'],
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
        result.pctAbsRange = (d['PercentAbsoluteMinValue'], d['PercentAbsoluteMaxValue'])

    if d['bAddOverTimeSpeedInSeconds']:
        result.duration = d['AddOverTimeSpeed']
    else:
        if d['AddOverTimeSpeed'] == 0:
            # Assume instant
            result.duration = 0
        else:
            # Duration = amount / speed
            duration = abs(d['BaseAmountToAdd']) / d['AddOverTimeSpeed']
            duration = float(format(duration, '.7g'))
            result.duration = duration

    return (stat_name, result)
