from typing import Any, Dict, Generic, Set, TypeVar, cast

from export.wiki.types import *
from ue.asset import ExportTableItem
from ue.gathering import gather_properties

from . import models
from .common import convert_location_for_export, get_actor_location_vector, get_actor_location_vector_m
from .data_container import World
from .gathering_base import GatheredData, GatheringResult, MapGathererBase

## Bases

T = TypeVar('T', bound=models.Actor)


class GenericActorExport(Generic[T], MapGathererBase[T]):
    CLASSES: Set[str]
    CATEGORY: str

    @classmethod
    def get_export_name(cls) -> str:
        return cls.CATEGORY

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return cls.CLASSES

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> models.Actor:
        location = get_actor_location_vector(proxy)
        return models.Actor(hidden=not proxy.get('bIsVisible', fallback=True), x=location.x, y=location.y, z=location.z)

    @classmethod
    def before_saving(cls, world: World, data: Dict[str, Any]):
        convert_location_for_export(world, data)


class GenericActorListExport(Generic[T], MapGathererBase[T]):
    TAGS: Set[str]
    CATEGORY: str

    @classmethod
    def get_export_name(cls) -> str:
        return cls.CATEGORY

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {CustomActorList.get_ue_type()}

    @classmethod
    def do_early_checks(cls, export: ExportTableItem) -> bool:
        # Check the tag
        tag = export.properties.get_property('CustomTag', fallback='')
        return str(tag) in cls.TAGS

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        actors: CustomActorList = cast(CustomActorList, proxy)
        for entry in actors.ActorList[0].values:
            if not entry.value.value:
                continue

            yield cls.extract_single(entry.value.value)

    @classmethod
    def extract_single(cls, export: ExportTableItem) -> GatheredData:
        return get_actor_location_vector_m(export)

    @classmethod
    def before_saving(cls, world: World, data: Dict[str, Any]):
        convert_location_for_export(world, data)


## Actors


class GlitchExport(GenericActorListExport[models.Glitch]):
    @classmethod
    def get_export_name(cls) -> str:
        return 'glitches'

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {PointOfInterestListGen1.get_ue_type()}

    @classmethod
    def do_early_checks(cls, _: ExportTableItem) -> bool:
        return True

    @classmethod
    def extract_single(cls, export: ExportTableItem) -> GatheredData:
        poi: PointOfInterestBP = gather_properties(export)
        location = get_actor_location_vector(poi)

        result = models.Glitch(hexagons=poi.number_of_hexagons_to_reward_upon_fixing[0],
                               x=location.x,
                               y=location.y,
                               z=location.z)

        noteid = poi.get('Specific_Unlocked_Explorer_Note_Index', fallback=-1)
        if noteid != -1:
            result.noteId = noteid

        #poi_info = poi.get('MyPointOfInterestData', fallback=None)
        #if poi_info:
        #    tag = poi_info.as_dict().get('PointTag', None)
        #    d['poiTag'] = tag

        return result


class PlayerSpawnPointExport(GenericActorExport[models.PlayerSpawn]):
    CLASSES = {PlayerStart.get_ue_type()}

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        point: PlayerStart = cast(PlayerStart, proxy)
        location = get_actor_location_vector(point)

        return models.PlayerSpawn(
            regionId=point.SpawnPointRegion[0],
            x=location.x,
            y=location.y,
            z=location.z,
        )


class OilVeinExport(GenericActorExport[models.OilVein]):
    CLASSES = {OilVein.get_ue_type()}


class WaterVeinExport(GenericActorExport[models.WaterVein]):
    CLASSES = {WaterVein.get_ue_type()}


class LunarOxygenVentExport(GenericActorExport[models.LunarOxygenVent]):
    CLASSES = {LunarOxygenVentGen1.get_ue_type()}


class OilVentExport(GenericActorExport[models.OilVent]):
    CLASSES = {OilVentGen1.get_ue_type()}
    CATEGORY = 'oilVents'


class GasVeinExport(GenericActorExport[models.GasVein]):
    CLASSES = {GasVein.get_ue_type(), GasVeinGen1.get_ue_type()}
    CATEGORY = 'gasVeins'


class ChargeNodeExport(GenericActorExport[models.ChargeNode]):
    CLASSES = {PrimalStructurePowerNode.get_ue_type()}
    CATEGORY = 'chargeNodes'


class WildPlantSpeciesZExport(GenericActorExport[models.PlantSpeciesZWild]):
    CLASSES = {WildPlantSpeciesZ.get_ue_type()}
    CATEGORY = 'plantZNodes'


class WyvernNests(GenericActorListExport[models.WyvernNest]):
    TAGS = {'DragonNestSpawns'}
    CATEGORY = 'wyvernNests'


class IceWyvernNests(GenericActorListExport[models.IceWyvernNest]):
    TAGS = {'IceNestSpawns'}
    CATEGORY = 'iceWyvernNests'


class RockDrakeNests(GenericActorListExport[models.DrakeNest]):
    TAGS = {'DrakeNestSpawns'}
    CATEGORY = 'drakeNests'


class DeinonychusNests(GenericActorListExport[models.DeinonychusNest]):
    TAGS = {'DeinonychusNestSpawns', 'AB_DeinonychusNestSpawns'}
    CATEGORY = 'deinonychusNests'


class MagmasaurNests(GenericActorListExport[models.MagmasaurNest]):
    TAGS = {'MagmasaurNestSpawns'}
    CATEGORY = 'magmasaurNests'


GATHERERS = [
    # Core
    PlayerSpawnPointExport,
    # Scorched Earth
    OilVeinExport,
    WaterVeinExport,
    WyvernNests,
    # Aberration
    ChargeNodeExport,
    GasVeinExport,
    RockDrakeNests,
    WildPlantSpeciesZExport,
    # Ragnarok
    IceWyvernNests,
    # Valguero
    DeinonychusNests,
    # Genesis Part 1
    GlitchExport,
    OilVentExport,
    LunarOxygenVentExport,
    MagmasaurNests,
]
