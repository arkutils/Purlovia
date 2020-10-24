from typing import Any, Dict, List, Optional, cast

from ark.types import PrimalColorSet
from automate.hierarchy_exporter import ExportFileModel, ExportModel, JsonHierarchyExportStage
from ue.hierarchy import inherits_from
from ue.proxy import UEProxyStructure
from utils.log import get_logger

__all__ = [
    'EventColorsStage',
]

logger = get_logger(__name__)

TESTGAMEMODE_ASSET = '/Game/PrimalEarth/CoreBlueprints/TestGameMode'
SCRIPT_COLORSET = '/Script/ShooterGame.PrimalColorSet'


class EventColorsModel(ExportModel):
    name: str
    regions: List[Optional[List[str]]]


class EventColorsExportModel(ExportFileModel):
    events: List[EventColorsModel]

    class Config:
        title = "Event-specific color sets"


class EventColorsStage(JsonHierarchyExportStage):
    def get_format_version(self) -> str:
        return "1"

    def get_name(self) -> str:
        return "event_colors"

    def get_field(self) -> str:
        return "events"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return PrimalColorSet.get_ue_type()

    def get_schema_model(self):
        return EventColorsExportModel

    def get_pre_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        # Fetch TestGameMode and find see which DinoColorSets it references
        asset = self.manager.loader[TESTGAMEMODE_ASSET]
        color_set_imports = [imp for imp in asset.imports if inherits_from(imp.fullname, SCRIPT_COLORSET, safe=True)]
        self.event_color_sets = [imp.fullname for imp in color_set_imports]
        return None

    def pre_load_filter(self, cls_name: str) -> bool:
        # We're only interested if the color set is ref'd from TestGameMode
        if cls_name not in self.event_color_sets:
            return False

        return True

    def extract(self, proxy: UEProxyStructure) -> Any:
        color_set: PrimalColorSet = cast(PrimalColorSet, proxy)

        assert self.event_color_sets is not None

        try:
            name = collect_name(color_set)
            regions = collect_regions(color_set.ColorSetDefinitions)
            v = EventColorsModel(name=name, regions=regions)
        except Exception:  # pylint: disable=broad-except
            logger.warning(f'Export conversion failed for {proxy.get_source().fullname}', exc_info=True)
            return None

        return v


def collect_name(proxy) -> str:
    name: str = str(proxy.get_source().name)

    if name.startswith('Default__'):
        name = name[9:]

    if name.startswith('DinoColorSet_'):
        name = name[13:]

    if name.endswith('_C'):
        name = name[:-2]

    return name


def collect_names(region) -> Optional[List[str]]:
    if not region:
        return None
    names = [str(name) for name in region.values]
    return names


def collect_regions(color_set) -> List[Optional[List[str]]]:
    regions = [collect_names(region.get_property('ColorEntryNames', fallback=None)) for i, region in color_set.items()]
    return regions
