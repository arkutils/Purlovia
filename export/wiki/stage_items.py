from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *

from ark.types import PrimalItem
from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.proxy import UEProxyStructure

from .items.cooking import convert_cooking_values
from .items.crafting import convert_crafting_values, convert_repair_values
from .items.status import convert_status_effect

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

    def get_pre_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            title = mod_data['title'] or mod_data['name']
            return dict(mod=dict(id=modid, tag=mod_data['name'], title=title))

        return None

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
            return None # this is used as an indicator that this is a non-spawnable base item
        v['icon'] = icon

        itemType = item.get('MyItemType', 0, None)
        v['type'] = itemType.get_enum_value_name()
        
        if v['type'] == 'MiscConsumable':
            consumableType = item.get('MyConsumableType', 0, None)
            v['type'] += '/' + consumableType.get_enum_value_name()
        elif v['type'] == 'Equipment':
            equipmentType = item.get('MyEquipmentType', 0, None)
            v['type'] += '/' + equipmentType.get_enum_value_name()

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
            v['durability'] = dict(
                min=item.MinItemDurability[0],
                ignoreInWater=item.bDurabilityRequirementIgnoredInWater[0]
            )

        v['crafting'] = convert_crafting_values(item)
        if item.bAllowRepair[0]:
            v['repair'] = convert_repair_values(item)

        if 'StructureToBuild' in item and item.StructureToBuild[0].value.value:
            v['structureTemplate'] = item.StructureToBuild[0]

        if 'WeaponToBuild' in item and item.WeaponToBuild[0].value.value:
            v['weaponTemplate'] = item.WeaponToBuild[0]

        if item.has_override('UseItemAddCharacterStatusValues'):
            status_effects = item.UseItemAddCharacterStatusValues[0]
            v['statEffects'] = dict(convert_status_effect(entry) for entry in status_effects.values)

        eggDinoClass = item.get('EggDinoClassToSpawn', 0, None)
        if item.bIsEgg[0] and eggDinoClass:
            v['egg'] = dict(
                dinoClass=eggDinoClass,
                temperature=(item.EggMinTemperature[0], item.EggMaxTemperature[0])
            )

        if item.bIsCookingIngredient[0]:
            v['cookingStats'] = convert_cooking_values(item)

        return v
