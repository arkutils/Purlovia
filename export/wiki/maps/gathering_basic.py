from typing import Any, Dict, Set, cast

from export.wiki.types import *
from ue.asset import ExportTableItem
from ue.gathering import gather_properties

from . import models
from .common import convert_location_for_export, get_actor_location_vector, get_actor_location_vector_m
from .data_container import World
from .gathering_base import GatheredData, GatheringResult, MapGathererBase


class GenericActorExport(MapGathererBase[models.Actor]):
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


class GenericActorListExport(MapGathererBase):
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


class HLNAGlitchExport(GenericActorListExport):
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


class PlayerSpawnPointExport(GenericActorExport):
    CLASSES = {PlayerStart.get_ue_type()}
    CATEGORY = 'playerSpawns'

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


class OilVeinExport(GenericActorExport):
    CLASSES = {OilVein.get_ue_type()}
    CATEGORY = 'oilVeins'


class WaterVeinExport(GenericActorExport):
    CLASSES = {WaterVein.get_ue_type()}
    CATEGORY = 'waterVeins'


class LunarOxygenVentExport(GenericActorExport):
    CLASSES = {LunarOxygenVentGen1.get_ue_type()}
    CATEGORY = 'lunarOxygenVents'


class OilVentExport(GenericActorExport):
    CLASSES = {OilVentGen1.get_ue_type()}
    CATEGORY = 'oilVents'


class GasVeinExport(GenericActorExport):
    CLASSES = {GasVein.get_ue_type(), GasVeinGen1.get_ue_type()}
    CATEGORY = 'gasVeins'


class ChargeNodeExport(GenericActorExport):
    CLASSES = {PrimalStructurePowerNode.get_ue_type()}
    CATEGORY = 'chargeNodes'


class WildPlantSpeciesZExport(GenericActorExport):
    CLASSES = {WildPlantSpeciesZ.get_ue_type()}
    CATEGORY = 'plantZNodes'


class WyvernNests(GenericActorListExport):
    TAGS = {'DragonNestSpawns'}
    CATEGORY = 'wyvernNests'


class IceWyvernNests(GenericActorListExport):
    TAGS = {'IceNestSpawns'}
    CATEGORY = 'iceWyvernNests'


class RockDrakeNests(GenericActorListExport):
    TAGS = {'DrakeNestSpawns'}
    CATEGORY = 'drakeNests'


class DeinonychusNests(GenericActorListExport):
    TAGS = {'DeinonychusNestSpawns', 'AB_DeinonychusNestSpawns'}
    CATEGORY = 'deinonychusNests'


class MagmasaurNests(GenericActorListExport):
    TAGS = {'MagmasaurNestSpawns'}
    CATEGORY = 'magmasaurNests'


ALL_GATHERERS = [
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
    HLNAGlitchExport,
    OilVentExport,
    LunarOxygenVentExport,
    MagmasaurNests,
]
