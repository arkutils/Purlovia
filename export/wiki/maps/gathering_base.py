from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Optional, Set, Type, Union

from automate.hierarchy_exporter import ExportModel
from ue.asset import ExportTableItem
from ue.proxy import UEProxyStructure

__all__ = [
    'GatheringResult',
    'MapGathererBase',
]

GatheringResult = Optional[Union[ExportModel, Iterable[ExportModel]]]


class PersistentLevel(ABC):
    persistent_level: Optional[str] = None
    settings: Dict[str, Any]


class MapGathererBase(ABC):

    @classmethod
    @abstractmethod
    def get_ue_types(cls) -> Set[str]:
        ...

    @classmethod
    @abstractmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
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
        '''
        ...

    @classmethod
    def before_saving(cls, _world: PersistentLevel, _data: Dict[str, Any]):
        '''
        Modify the sanitised data before saving.
        '''
        ...
