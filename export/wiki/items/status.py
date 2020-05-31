def convert_status_effect(entry):
    d = entry.as_dict()
    stat_name = d['StatusValueType'].get_enum_value_name().lower()
    result = dict(
        value=d['BaseAmountToAdd'],
        useItemQuality=d['bUseItemQuality'],
        descriptionIndex=d['StatusValueModifierDescriptionIndex'],

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
        result['pctOf'] = 'max' if pctOfMax else 'current'
        result['pctAbsRange'] = (d['PercentAbsoluteMinValue'], d['PercentAbsoluteMaxValue'])

    if d['bSetValue']:
        result['setValue'] = True
    if d['bSetAdditionalValue']:
        result['setAddValue'] = True
    if d['bForceUseStatOnDinos']:
        result['forceUseOnDino'] = True
    if not d['bDontRequireLessThanMaxToUse']:
        result['allowWhenFull'] = False

    qlyMult = d['ItemQualityAddValueMultiplier']
    if qlyMult != 1.0:
        result['qualityMult'] = d['ItemQualityAddValueMultiplier']

    if d['bAddOverTimeSpeedInSeconds']:
        result['duration'] = d['AddOverTimeSpeed']
    else:
        if d['AddOverTimeSpeed'] == 0:
            # Assume instant
            result['duration'] = 0
        else:
            # Duration = amount / speed
            duration = abs(d['BaseAmountToAdd']) / d['AddOverTimeSpeed']
            duration = float(format(duration, '.7g'))
            result['duration'] = duration

    return (stat_name, result)
