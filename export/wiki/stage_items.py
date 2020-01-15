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
        return self.manager.config.export_wiki.PrettyJson

    def get_ue_type(self) -> str:
        return PrimalItem.get_ue_type()

    def get_core_file_path(self) -> PurePosixPath:
        return PurePosixPath('items.json')

    def get_mod_file_path(self, modid) -> PurePosixPath:
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        return PurePosixPath(f'{modid}-{mod_data["name"]}/items.json')

    def extract(self, proxy: UEProxyStructure) -> Any:
        item: PrimalItem = cast(PrimalItem, proxy)

        v: Dict[str, Any] = dict()
        if not item.has_override('DescriptiveNameBase'):
            return None
        v['name'] = str(item.DescriptiveNameBase[0])
        v['description'] = str(item.ItemDescription[0])
        v['blueprintPath'] = item.get_source().fullname

        if getattr(item, 'ItemIcon', None):
            icon_obj = item.ItemIcon[0].value
            v['icon'] = icon_obj and icon_obj.value and icon_obj.value.fullname
            if not v['icon']:
                return None  # this is used as an indicator that this is a non-spawnable base item

        if item.has_override('DefaultFolderPaths'):
            v['folders'] = [str(folder) for folder in item.DefaultFolderPaths[0].values]
        else:
            v['folders'] = []

        if item.has_override('BaseCraftingResourceRequirements'):
            recipe = item.BaseCraftingResourceRequirements[0]
            if recipe.values:
                v['recipe'] = [convert_recipe_entry(entry.as_dict()) for entry in recipe.values]

        return v


def convert_recipe_entry(entry):
    result = dict(
        exact=bool(entry['bCraftingRequireExactResourceType']),
        qty=int(entry['BaseResourceRequirement']),
        type=str(entry['ResourceItemType'].value.value.name),
    )
    return result
