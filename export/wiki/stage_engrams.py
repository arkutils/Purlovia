from typing import Any, Dict, Iterable, List, Optional, cast

from automate.hierarchy_exporter import ExportFileModel, ExportModel, Field, JsonHierarchyExportStage
from export.wiki.types import PrimalEngramEntry
from ue.asset import UAsset
from ue.properties import IntProperty, StringProperty
from ue.proxy import UEProxyStructure
from ue.utils import sanitise_output
from utils.log import get_logger

__all__ = [
    'EngramsStage',
]

logger = get_logger(__name__)


class EngramRequirements(ExportModel):
    characterLevel: Optional[IntProperty] = Field(None, title="Required character level")
    engramPoints: Optional[IntProperty] = Field(None, title="Required number of points")
    otherEngrams: Optional[List[Optional[str]]] = Field(None, title="Required engrams")


class Engram(ExportModel):
    description: Optional[StringProperty]
    blueprintPath: str = Field(
        ...,
        title="Full blueprint path of the engram",
    )
    itemBlueprintPath: Optional[str] = Field(
        ...,
        title="Full blueprint path of the item",
    )
    group: Optional[str] = Field(
        ...,
        title="DLC group",
    )
    requirements: EngramRequirements
    manualUnlock: bool = Field(
        ...,
        title="Unlockable in UI",
        description="Whether the engram can be unlocked by the player in UI",
    )
    givesBP: bool = Field(
        ...,
        title="Craftable in inventory",
        description="Whether the player can craft the item in their inventory",
    )


class EngramsExportModel(ExportFileModel):
    species: List[Engram]

    class Config:
        title = "Engram data for the Wiki"


class EngramsStage(JsonHierarchyExportStage):

    def get_format_version(self) -> str:
        return "2"

    def get_name(self) -> str:
        return "engrams"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return PrimalEngramEntry.get_ue_type()

    def get_schema_model(self):
        return EngramsExportModel

    def get_pre_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            title = mod_data['title'] or mod_data['name']
            return dict(mod=dict(id=modid, tag=mod_data['name'], title=title))

        return None

    def extract(self, proxy: UEProxyStructure) -> Engram | None:
        if self.manager.config.export_wiki.RestrictPath:
            # Check this asset is within the path restriction
            goodpath = self.manager.config.export_wiki.RestrictPath
            assetname = proxy.get_source().asset.assetname
            if not assetname.startswith(goodpath):
                return None

        engram: PrimalEngramEntry = cast(PrimalEngramEntry, proxy)

        out = Engram(
            description=engram.ExtraEngramDescription[0] if engram.has_override('ExtraEngramDescription') else None,
            blueprintPath=engram.get_source().fullname,
            itemBlueprintPath=sanitise_output(engram.get('BluePrintEntry', 0, None)),
            group=convert_engram_group(engram),
            requirements=EngramRequirements(
                characterLevel=engram.RequiredCharacterLevel[0],
                engramPoints=engram.RequiredEngramPoints[0],
            ),
            manualUnlock=bool(engram.bCanBeManuallyUnlocked[0]),
            givesBP=bool(engram.bGiveBlueprintToPlayerInventory[0]),
        )

        if 'EngramRequirementSets' in engram:
            out.requirements.otherEngrams = list(convert_requirement_sets(engram))

        return out

    def get_post_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if not self.gathered_results:
            return None

        if not modid:
            # Add indexes from the base PGD
            pgd_asset = self.manager.loader['/Game/PrimalEarth/CoreBlueprints/BASE_PrimalGameData_BP']
            return self._add_pgd_indices(pgd_asset, None)
        else:
            # Mod indexes are dependent on load order, and thus
            # unstable. It's up to the user to concat indexes in mods.
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            package = mod_data.get('package', None)
            if package:
                pgd_asset = self.manager.loader[package]
                return self._add_pgd_indices(pgd_asset, mod_data)

        return None

    def _add_pgd_indices(self, pgd_asset: UAsset, mod_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not self.gathered_results or not pgd_asset.default_export:
            return None

        properties = pgd_asset.default_export.properties
        if not mod_data:
            d = properties.get_property('EngramBlueprintClasses', fallback=None)
        else:
            d = properties.get_property('AdditionalEngramBlueprintClasses', fallback=None)
        if not d:
            return None

        master_list = [ref.value.value and ref.value.value.fullname for ref in d.values]
        return dict(indices=master_list)


_ENGRAM_GROUP_MAP = {
    'ARK_PRIME': 'Base Game',
    'ARK_SCORCHEDEARTH': 'Scorched Earth',
    'ARK_TEK': 'TEK',
    'ARK_UNLEARNED': 'Unavailable',
    'ARK_ABERRATION': 'Aberration',
    'ARK_EXTINCTION': 'Extinction',
    'ARK_GENESIS': 'Genesis',
}


def convert_engram_group(engram: PrimalEngramEntry) -> str:
    if 'EngramGroup' not in engram:
        return 'BaseGame'

    group = engram.EngramGroup[0].get_enum_value_name()
    return _ENGRAM_GROUP_MAP.get(group, group)


def convert_requirement_sets(engram: PrimalEngramEntry) -> Iterable[Optional[str]]:
    for struct in engram.EngramRequirementSets[0].values:
        for entry in struct.get_property('EngramEntries').values:
            yield sanitise_output(entry)
