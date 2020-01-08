from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Tuple, Union

from ue.asset import ExportTableItem
from ue.base import UEBase
from ue.proxy import UEProxyStructure

from .map import MapInfo


class MapGathererBase(ABC):
    @classmethod
    @abstractmethod
    def get_category_name(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        '''
        Check whether an export may contain data covered by this gatherer.
        '''

    @classmethod
    @abstractmethod
    def extract(cls, proxy: UEProxyStructure) -> Iterable[Union[UEBase, Dict[str, Any]]]:
        '''
        Collect data from a proxy object and return it as a dict.
        Caution: Data should be formatted for json to avoid leak any references.
        '''

    @classmethod
    @abstractmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        pass

    @classmethod
    @abstractmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Tuple[Any, ...]:
        pass
