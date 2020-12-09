from typing import Any, Dict, Optional, Set, Type, cast

from automate.hierarchy_exporter import ExportModel
from export.wiki.types import CustomActorList, GasVein, GasVeinGen1, LunarOxygenVentGen1, OilVein, OilVentGen1, PlayerStart, \
    PointOfInterestBP, PointOfInterestListGen1, PoisonTree, PrimalStructurePowerNode, WaterVein, WildPlantSpeciesZ
from ue.asset import ExportTableItem
from ue.gathering import gather_properties
from ue.proxy import UEProxyStructure

from . import models
from .common import convert_location_for_export, get_actor_location_vector
from .gathering_base import GatheringResult, MapGathererBase, PersistentLevel

__all__ = ['BASIC_GATHERERS']

# Bases


class BaseActorExport(MapGathererBase):
    CLASSES: Set[str]
    MODEL: Type[ExportModel]

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return cls.CLASSES

    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return cls.MODEL

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        location = get_actor_location_vector(proxy)
        return models.Actor(
            hidden=not proxy.get('bIsVisible', fallback=True),
            x=location.x,
            y=location.y,
            z=location.z,
        )

    @classmethod
    def before_saving(cls, world: PersistentLevel, data: Dict[str, Any]):
        convert_location_for_export(world, data)


class BaseActorListExport(MapGathererBase):
    TAGS: Set[str]
    MODEL: Type[ExportModel]

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {CustomActorList.get_ue_type()}

    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return cls.MODEL

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
    def extract_single(cls, export: ExportTableItem) -> ExportModel:
        props = export.properties
        location = get_actor_location_vector(export)

        return models.Actor(
            hidden=not props.get_property('bIsVisible', fallback=True),
            x=location.x,
            y=location.y,
            z=location.z,
        )

    @classmethod
    def before_saving(cls, world: PersistentLevel, data: Dict[str, Any]):
        convert_location_for_export(world, data)


# Actors


class GlitchExport(BaseActorListExport):
    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return models.Glitch

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {PointOfInterestListGen1.get_ue_type()}

    @classmethod
    def do_early_checks(cls, _: ExportTableItem) -> bool:
        return True

    @classmethod
    def extract_single(cls, export: ExportTableItem) -> models.Glitch:
        poi: PointOfInterestBP = gather_properties(export)
        location = get_actor_location_vector(poi)

        result = models.Glitch(hexagons=poi.number_of_hexagons_to_reward_upon_fixing[0],
                               x=location.x,
                               y=location.y,
                               z=location.z)

        noteid = poi.get('Specific_Unlocked_Explorer_Note_Index', fallback=-1)
        if noteid != -1:
            result.noteId = noteid

        # TODO: remove?
        # poi_info = poi.get('MyPointOfInterestData', fallback=None)
        # if poi_info:
        #     tag = poi_info.as_dict().get('PointTag', None)
        #     d['poiTag'] = tag

        return result


class PlayerSpawnPointExport(BaseActorExport):
    CLASSES = {PlayerStart.get_ue_type()}
    MODEL = models.PlayerSpawn

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


class OilVeinExport(BaseActorExport):
    CLASSES = {OilVein.get_ue_type()}
    MODEL = models.OilVein


class WaterVeinExport(BaseActorExport):
    CLASSES = {WaterVein.get_ue_type()}
    MODEL = models.WaterVein


class LunarOxygenVentExport(BaseActorExport):
    CLASSES = {LunarOxygenVentGen1.get_ue_type()}
    MODEL = models.LunarOxygenVent


class OilVentExport(BaseActorExport):
    CLASSES = {OilVentGen1.get_ue_type()}
    MODEL = models.OilVent


class GasVeinExport(BaseActorExport):
    CLASSES = {GasVein.get_ue_type(), GasVeinGen1.get_ue_type()}
    MODEL = models.GasVein


class ChargeNodeExport(BaseActorExport):
    CLASSES = {PrimalStructurePowerNode.get_ue_type()}
    MODEL = models.ChargeNode


class WildPlantSpeciesZExport(BaseActorExport):
    CLASSES = {WildPlantSpeciesZ.get_ue_type()}
    MODEL = models.PlantSpeciesZWild


class PoisonTreeExport(BaseActorExport):
    CLASSES = {PoisonTree.get_ue_type()}
    MODEL = models.PoisonTree


class WyvernNests(BaseActorListExport):
    TAGS = {'DragonNestSpawns'}
    MODEL = models.WyvernNest


class IceWyvernNests(BaseActorListExport):
    TAGS = {
        'IceNestSpawns',
        # 1679826889 Caballus
        'DragonIceNestSpawns'
    }
    MODEL = models.IceWyvernNest


class RockDrakeNests(BaseActorListExport):
    TAGS = {'DrakeNestSpawns'}
    MODEL = models.DrakeNest


class DeinonychusNests(BaseActorListExport):
    TAGS = {'DeinonychusNestSpawns', 'AB_DeinonychusNestSpawns'}
    MODEL = models.DeinonychusNest


class MagmasaurNests(BaseActorListExport):
    TAGS = {'MagmasaurNestSpawns'}
    MODEL = models.MagmasaurNest


BASIC_GATHERERS = [
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
    PoisonTreeExport,
]
