from typing import *

import ark.mod
from ark.defaults import *
from ark.properties import stat_value
from ue.loader import AssetLoader
from ue.utils import clean_double as cd
from ue.utils import clean_float as cf

__all__ = [
    'gather_breeding_data',
]


def gather_breeding_data(props, loader: AssetLoader) -> Dict[str, Any]:
    data: Dict[str, Any] = dict(gestationTime=0, incubationTime=0)

    gestation_breeding = stat_value(props, 'bUseBabyGestation', 0, False)
    has_eggs = False

    if props['FertilizedEggItemsToSpawn'][0] and props['FertilizedEggItemsToSpawn'][0][-1].values:
        # eggs = list(filter(lambda v: v and str(v) != 'None', props['FertilizedEggItemsToSpawn'][0][-1].values))
        eggs = [egg for egg in props['FertilizedEggItemsToSpawn'][0][-1].values if str(egg) != 'None']
        has_eggs = bool(eggs)

    if gestation_breeding:
        gestation_speed = stat_value(props, 'BabyGestationSpeed', 0, BABYGESTATIONSPEED_DEFAULT)
        extra_gestation_speed_m = stat_value(props, 'ExtraBabyGestationSpeedMultiplier', 0, 1.0)

        # TODO: Verify if these should really default to 1 - seems odd
        gestation_speed = gestation_speed or 1
        extra_gestation_speed_m = extra_gestation_speed_m or 1
        # 'gestationTime' = 1 / (Baby Gestation Speed × Extra Baby Gestation Speed Multiplier)
        data['gestationTime'] = cd((1 / gestation_speed /
                                    extra_gestation_speed_m) if gestation_speed and extra_gestation_speed_m else None)

    elif has_eggs:
        fert_egg_asset = loader.load_related(eggs[0])
        fert_egg_props = ark.mod.gather_properties(fert_egg_asset)
        egg_decay = stat_value(fert_egg_props, 'EggLoseDurabilityPerSecond', 0, 1)
        extra_egg_decay_m = stat_value(fert_egg_props, 'ExtraEggLoseDurabilityPerSecondMultiplier', 0, 1)

        # 'incubationTime' = 100 / (Egg Lose Durability Per Second × Extra Egg Lose Durability Per Second Multiplier)
        data['incubationTime'] = cd((100 / egg_decay / extra_egg_decay_m) if egg_decay and extra_egg_decay_m else None)
        data['eggTempMin'] = cf(stat_value(fert_egg_props, 'EggMinTemperature', 0))
        data['eggTempMax'] = cf(stat_value(fert_egg_props, 'EggMaxTemperature', 0))

    # 'maturationTime' = 1 / (Baby Age Speed × Extra Baby Age Speed Multiplier)
    baby_age_speed = stat_value(props, 'BabyAgeSpeed', 0, 1)
    extra_baby_age_speed_m = stat_value(props, 'ExtraBabyAgeSpeedMultiplier', 0, 1)

    data['maturationTime'] = cd((1 / baby_age_speed /
                                 extra_baby_age_speed_m) if baby_age_speed and extra_baby_age_speed_m else None)
    data['matingCooldownMin'] = cf(stat_value(props, 'NewFemaleMinTimeBetweenMating', 0, FEMALE_MINTIMEBETWEENMATING_DEFAULT))
    data['matingCooldownMax'] = cf(stat_value(props, 'NewFemaleMaxTimeBetweenMating', 0, FEMALE_MAXTIMEBETWEENMATING_DEFAULT))

    return data
