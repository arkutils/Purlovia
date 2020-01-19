from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *

from ark.types import PrimalItem
from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.proxy import UEProxyStructure

__all__ = [
    'ItemsStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class ItemsStage(JsonHierarchyExportStage):
    def get_skip(self):
        return not self.manager.config.export_wiki.ExportItems

    def get_format_version(self) -> str:
        return "1"

    def get_field(self) -> str:
        return "items"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return PrimalItem.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        item: PrimalItem = cast(PrimalItem, proxy)

        v: Dict[str, Any] = dict()
        if not item.has_override('DescriptiveNameBase'):
            return None
        v['name'] = item.get('DescriptiveNameBase', 0, None)
        v['description'] = item.get('ItemDescription', 0, None)
        v['blueprintPath'] = item.get_source().fullname

        icon = item.get('ItemIcon', 0, None)
        if not icon:
            v['icon'] = None
            return  # this is used as an indicator that this is a non-spawnable base item

        if item.has_override('bPreventCheatGive'):
            v['preventCheatGive'] = item.bPreventCheatGive[0]

        if item.has_override('DefaultFolderPaths'):
            v['folders'] = [str(folder) for folder in item.DefaultFolderPaths[0].values]
        else:
            v['folders'] = []

        v['weight'] = item.BaseItemWeight[0]
        v['maxQuantity'] = item.MaxItemQuantity[0]

        if item.has_override('SpoilingTime'):
            v['spoilage'] = dict(time=item.SpoilingTime[0])
            if item.has_override('SpoilingItem'):
                v['spoilage']['productBP'] = item.SpoilingItem[0]

        if item.bUseItemDurability[0].value:
            v['durability'] = dict(min=item.MinItemDurability[0], ignoreInWater=item.bDurabilityRequirementIgnoredInWater[0])

        v['crafting'] = dict(
            xp=item.BaseCraftingXP[0],
            bpCraftTime=(item.MinBlueprintTimeToCraft[0], item.BlueprintTimeToCraft[0]),
            minLevelReq=item.CraftingMinLevelRequirement[0],
            productCount=item.CraftingGiveItemCount[0],
        )

        if item.bAllowRepair[0]:
            v['repair'] = dict(
                xp=item.BaseRepairingXP[0],
                time=item.TimeForFullRepair[0],
                resourceMult=item.RepairResourceRequirementMultiplier[0],
            )

        if 'StructureToBuild' in item and item.StructureToBuild[0].value.value:
            v['structureTemplate'] = item.StructureToBuild[0]

        if 'WeaponToBuild' in item and item.WeaponToBuild[0].value.value:
            v['weaponTemplate'] = item.WeaponToBuild[0]

        if item.has_override('BaseCraftingResourceRequirements'):
            recipe = item.BaseCraftingResourceRequirements[0]
            if recipe.values:
                v['crafting']['recipe'] = [convert_recipe_entry(entry.as_dict()) for entry in recipe.values]

        if 'OverrideRepairingRequirements' in item:
            recipe = item.OverrideRepairingRequirements[0]
            if recipe.values:
                v['repair'] = dict()
                v['repair']['recipe'] = [convert_recipe_entry(entry.as_dict()) for entry in recipe.values]

        if item.has_override('UseItemAddCharacterStatusValues'):
            status_effects = item.UseItemAddCharacterStatusValues[0]
            v['statEffects'] = dict(convert_status_effect(entry) for entry in status_effects.values)

        return v


def convert_recipe_entry(entry):
    result = dict(
        exact=entry['bCraftingRequireExactResourceType'],
        qty=entry['BaseResourceRequirement'],
        type=entry['ResourceItemType'].value.value.name,
    )
    return result


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

    if d['bSetValue']: result['setValue'] = True
    if d['bSetAdditionalValue']: result['setAddValue'] = True
    if d['bForceUseStatOnDinos']: result['forceUseOnDino'] = True
    if not d['bDontRequireLessThanMaxToUse']: result['allowWhenFull'] = False

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
