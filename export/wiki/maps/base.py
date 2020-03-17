from abc import ABC, abstractmethod
from typing import *

from ue.asset import ExportTableItem
from ue.base import UEBase
from ue.proxy import UEProxyStructure

from .data_container import MapInfo

GatheredData = Union[UEBase, Dict[str, Any]]
GatheringResult = Optional[Union[GatheredData, Iterable[GatheredData]]]


class MapGathererBase(ABC):
    @classmethod
    @abstractmethod
    def get_export_name(cls) -> str:
        ...

    @classmethod
    @abstractmethod
    def get_ue_types(cls) -> Set[str]:
        ...

    @classmethod
    def do_early_checks(cls, _export: ExportTableItem) -> bool:
        '''
        Check whether an export meets any extra requirements
        set by the gatherer.
        '''
        return True

    @classmethod
    @abstractmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        '''
        Collect data from a proxy object and return it as a dict.
        Caution: Data should be formatted for json to avoid leak any references.
        '''
        ...

    @classmethod
    @abstractmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        ...
