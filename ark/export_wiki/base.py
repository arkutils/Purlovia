from abc import ABC, abstractclassmethod, abstractmethod, abstractproperty
from typing import Any, Dict, Optional

from ue.asset import ExportTableItem
from ue.proxy import UEProxyStructure

from .map import MapInfo


class MapGathererBase(ABC):
    @abstractclassmethod
    def get_category_name(cls) -> str:
        pass

    @abstractclassmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        '''
        Check whether an export may contain data covered by this gatherer.
        '''
        pass

    @abstractclassmethod
    def extract(cls, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        '''
        Collect data from a proxy object and return it as a dict.
        Caution: Data should be formatted for json to avoid leak any references.
        '''
        pass

    @abstractclassmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        pass

    @abstractclassmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        pass
