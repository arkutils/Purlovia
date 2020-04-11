from logging import NullHandler, getLogger
from typing import Any, Dict

import ue.gathering
from ark.types import PrimalDinoCharacter, PrimalItem
from ue.loader import AssetLoader
from ue.utils import clean_double as cd
from ue.utils import clean_float as cf

__all__ = [
    'gather_breeding_data',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def gather_breeding_data(char_props: PrimalDinoCharacter, loader: AssetLoader) -> Dict[str, Any]:
    data: Dict[str, Any] = dict(gestationTime=0, incubationTime=0)

    if not char_props.bPreventMating[0]:
        data['matingTime'] = cf(char_props.FemaleMatingTime[0])

    gestation_breeding = char_props.bUseBabyGestation[0]
    fert_eggs = char_props.get('FertilizedEggItemsToSpawn', 0, None)

    if gestation_breeding:
        gestation_speed = char_props.BabyGestationSpeed[0]
        extra_gestation_speed_m = char_props.ExtraBabyGestationSpeedMultiplier[0]
        try:
            # Gestation starts at 1% for mothers so the time remaining is 99% of this value
            data['gestationTime'] = cd(0.99 / gestation_speed / extra_gestation_speed_m)
        except ZeroDivisionError:
            logger.warning(f"Species {char_props.get_source().asset.assetname} tried dividing by zero for its gestationTime")

    elif fert_eggs and fert_eggs.values:
        eggs = [egg for egg in fert_eggs.values if str(egg) != 'None']

        if eggs:
            fert_egg_asset = loader.load_related(eggs[0])
            assert fert_egg_asset.default_export
            egg_props: PrimalItem = ue.gathering.gather_properties(fert_egg_asset.default_export)
            egg_decay = egg_props.EggLoseDurabilityPerSecond[0].rounded_value
            extra_egg_decay_m = egg_props.ExtraEggLoseDurabilityPerSecondMultiplier[0].rounded_value

            # 'incubationTime' = 100 / (Egg Lose Durability Per Second × Extra Egg Lose Durability Per Second Multiplier)
            try:
                data['incubationTime'] = cd(100 / egg_decay / extra_egg_decay_m)
            except ZeroDivisionError:
                logger.warning(
                    f"Species {char_props.get_source().asset.assetname} tried dividing by zero for its incubationTime")
            data['eggTempMin'] = egg_props.EggMinTemperature[0]
            data['eggTempMax'] = egg_props.EggMaxTemperature[0]

    # 'maturationTime' = 1 / (Baby Age Speed × Extra Baby Age Speed Multiplier)
    baby_age_speed = char_props.BabyAgeSpeed[0].rounded_value
    extra_baby_age_speed_m = char_props.ExtraBabyAgeSpeedMultiplier[0].rounded_value

    try:
        data['maturationTime'] = cd(1 / baby_age_speed / extra_baby_age_speed_m)
    except ZeroDivisionError:
        logger.warning(f"Species {char_props.get_source().asset.assetname} tried dividing by zero for its maturationTime")
    data['matingCooldownMin'] = char_props.NewFemaleMinTimeBetweenMating[0]
    data['matingCooldownMax'] = char_props.NewFemaleMaxTimeBetweenMating[0]

    return data
