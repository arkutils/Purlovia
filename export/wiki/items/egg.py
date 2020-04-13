from typing import Any, Dict

from ark.types import PrimalItem
from ue.loader import AssetLoadException
from utils.log import get_logger

logger = get_logger(__name__)


def gather_mic_parameters(d):
    v = dict()

    for param in d.values:
        param = param.as_dict()
        v[str(param['ParameterName'])] = param['ParameterValue']

    return v


def gather_hud_color_data(mic):
    v = dict()
    props = mic.properties.as_dict()
    d = gather_mic_parameters(props['ScalarParameterValues'][0])
    d.update(gather_mic_parameters(props['VectorParameterValues'][0]))

    color0 = d.get('Color0', None)
    color4 = d.get('Color4', None)
    if color0:
        v['red'] = dict(
            intensity=d.get('Color0_RedIntensity', 1.0),
            color=color0.values[0],
        )
    if color4:
        v['cyan'] = dict(
            intensity=d.get('Color4_CyanIntensity', 1.0),
            color=color4.values[0],
        )

    return v


def convert_egg_values(item: PrimalItem) -> Dict[str, Any]:
    v = dict()

    dino_class = item.get('EggDinoClassToSpawn', 0, None)
    if dino_class:
        v['dinoClass'] = dino_class
        v['temperature'] = (item.EggMinTemperature[0], item.EggMaxTemperature[0])

    hud_mic_ref = item.get('ItemIconMaterialParent', 0, None)
    if hud_mic_ref and hud_mic_ref.value and hud_mic_ref.value.value:
        try:
            hud_mic = item.get_source().asset.loader.load_related(hud_mic_ref)
            hud_mic = hud_mic.default_export
            hud_colors = gather_hud_color_data(hud_mic)
            if hud_colors:
                v['hudColorisation'] = hud_colors
        except AssetLoadException:
            logger.warning(f'Failure while gathering color data from {hud_mic_ref.value.value.fullname}', exc_info=True)

    return v
