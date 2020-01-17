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
        exact=entry['bCraftingRequireExactResourceType'],
        qty=entry['BaseResourceRequirement'],
        type=entry['ResourceItemType'].value.value.name,
    )
    return result
