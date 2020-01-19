from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *

from automate.hierarchy_exporter import JsonHierarchyExportStage
from export.wiki.types import PrimalEngramEntry
from ue.proxy import UEProxyStructure

__all__ = [
    'EngramsStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class EngramsStage(JsonHierarchyExportStage):
    def get_skip(self):
        return not self.manager.config.export_wiki.ExportEngrams

    def get_format_version(self) -> str:
        return "1"

    def get_field(self) -> str:
        return "engrams"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return PrimalEngramEntry.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        engram: PrimalEngramEntry = cast(PrimalEngramEntry, proxy)

        v: Dict[str, Any] = dict()
        if engram.has_override('ExtraEngramDescription'):
            v['description'] = engram.ExtraEngramDescription[0]
        v['blueprintPath'] = engram.get_source().fullname
        v['itemBlueprintPath'] = engram.get('BluePrintEntry', 0, None)
        v['group'] = convert_engram_group(engram)
        v['requirements'] = dict(
            characterLevel=engram.RequiredCharacterLevel[0],
            engramPoints=engram.RequiredEngramPoints[0],
        )
        v['manualUnlock'] = engram.bCanBeManuallyUnlocked[0]
        v['givesBP'] = engram.bGiveBlueprintToPlayerInventory[0]

        if 'EngramRequirementSets' in engram:
            v['requirements']['otherEngrams'] = list(convert_requirement_sets(engram))

        return v


_ENGRAM_GROUP_MAP = {
    'ARK_PRIME': 'Base Game',
    'ARK_SCORCHEDEARTH': 'Scorched Earth',
    'ARK_TEK': 'TEK',
    'ARK_UNLEARNED': 'Unavailable',
    'ARK_ABERRATION': 'Aberration',
    'ARK_EXTINCTION': 'Extinction',
    'ARK_GENESIS': 'Genesis'
}


def convert_engram_group(engram: PrimalEngramEntry) -> str:
    if 'EngramGroup' not in engram:
        return 'BaseGame'

    group = engram.EngramGroup[0].get_enum_value_name()
    return _ENGRAM_GROUP_MAP.get(group, group)


def convert_requirement_sets(engram: PrimalEngramEntry) -> Iterable:
    for struct in engram.EngramRequirementSets[0].values:
        entries = struct.get_property('EngramEntries')
        yield from entries.values
