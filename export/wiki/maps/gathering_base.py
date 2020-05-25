from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Iterable, Optional, Set, TypeVar, Union

from automate.hierarchy_exporter import ExportModel
from ue.asset import ExportTableItem
from ue.base import UEBase
from ue.proxy import UEProxyStructure

from .data_container import WorldInfo

__all__ = [
    'GatheredData',
    'GatheringResult',
    'MapGathererBase',
]

GatheredData = Union[UEBase, ExportModel]
GatheringResult = Optional[Union[GatheredData, Iterable[GatheredData]]]

T = TypeVar('T', bound=ExportModel)


class MapGathererBase(Generic[T], ABC):
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
    def extract(cls, proxy: UEProxyStructure) -> Optional[Union[T, Iterable[T]]]:
        '''
        Collect data from a proxy object and return it as a dict.
        '''
        ...

    @classmethod
    def before_saving(cls, _world: WorldInfo, _data: Dict[str, Any]):
        '''
        Modify the sanitised data before saving.
        '''
        ...
