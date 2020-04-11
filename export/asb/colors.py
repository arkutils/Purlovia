from logging import NullHandler, getLogger
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import ue.gathering
from ark.overrides import OverrideSettings, any_regexes_match
from ark.types import PrimalColorSet, PrimalDinoCharacter, PrimalGameData, PrimalItem_Dye
from ue.asset import UAsset
from ue.loader import AssetLoader
from ue.properties import UEBase

__all__ = [
    'gather_pgd_colors',
    'gather_color_data',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())

NUM_REGIONS = 6
NULLABLE_REGION_COLORS = set(['Red'])

ColorEntry = Tuple[str, Tuple[float, float, float, float]]


def gather_pgd_colors(asset: UAsset, props: PrimalGameData, loader: AssetLoader,
                      require_override=True) -> Tuple[Optional[Sequence[ColorEntry]], Optional[Sequence[ColorEntry]]]:
    '''Gather color and dye definitions from a PrimalGameData asset.'''
    colors: Optional[List[ColorEntry]] = list()
    dyes: Optional[List[ColorEntry]] = list()

    # Collect the color definitions
    color_def_overrides = props.ColorDefinitions[0]
    if require_override and color_def_overrides.asset != asset:
        colors = None
    else:
        color_defs = color_def_overrides.values
        colors = list()
        for definition in ((entry.as_dict() for entry in color_defs)):
            name = definition.get('ColorName', None) or '~~unset~~'
            value = definition.get('ColorValue', None)
            color = value.values[0].as_tuple() if value else None
            colors.append((str(name), color))

    # Collect the dye definitions
    dye_def_overrides = props.MasterDyeList[0]
    if require_override and dye_def_overrides.asset != asset:
        dyes = None
    else:
        dye_defs = dye_def_overrides.values
        dyes = list()
        for dye_asset in (loader.load_related(entry) for entry in dye_defs):
            assert dye_asset and dye_asset.default_export
            dye_props: PrimalItem_Dye = ue.gathering.gather_properties(dye_asset.default_export)
            name = dye_props.DescriptiveNameBase[0] or '~~unset~~'
            value = dye_props.DyeColor[0]
            color = value.values[0].as_tuple() if value else None
            dyes.append((str(name), color))

    return (colors, dyes)


# TODO: Requires conversion to the Proxy system
def gather_color_data(char_props: PrimalDinoCharacter, overrides: OverrideSettings):
    '''Gather color region definitions for a species.'''
    settings = overrides.color_regions
    colors: List[Dict] = list()

    try:
        male_colorset_props: Optional[PrimalColorSet] = char_props.RandomColorSetsMale[0]
    except ValueError:
        male_colorset_props = None
    try:
        female_colorset_props: Optional[PrimalColorSet] = char_props.RandomColorSetsFemale[0]
    except ValueError:
        female_colorset_props = None

    # TODO: Incorporate both male and female colorsets, as well as if multiple colorsets are listed
    colorset_props = male_colorset_props or female_colorset_props
    if not colorset_props:
        return None

    if char_props.bIsCorrupted[0]:
        return colors

    # Export a list of color names for each region
    for i in range(NUM_REGIONS):
        prevent_region = char_props.PreventColorizationRegions[i]
        color: Dict[str, Any] = dict()
        color_names: Set[str] = set()

        if prevent_region:
            color['name'] = None
        elif i not in colorset_props.ColorSetDefinitions:
            color['name'] = None
        else:
            color_set_defs: Dict[str, UEBase] = colorset_props.ColorSetDefinitions[i].as_dict()

            if 'ColorEntryNames' in color_set_defs:
                for color_name in color_set_defs['ColorEntryNames'].values:
                    color_names.add(str(color_name))

            region_name: Optional[str] = str(color_set_defs.get('RegionName', settings.default_name)).strip()

            if region_name and any_regexes_match(settings.nullify_name_regexes, region_name):
                # Null-out this region if it matches NULLABLE_REGION_COLORS exactly
                if not color_names or color_names == NULLABLE_REGION_COLORS:
                    region_name = None
                    color_names.clear()

            if region_name and any_regexes_match(settings.useless_name_regexes, region_name):
                # Region name is useless, replace with the default_name
                region_name = settings.default_name

            if region_name and i in settings.region_names:
                # There's a specific override for this region
                region_name = settings.region_names[i]

            if region_name and settings.capitalize:
                region_name = region_name[0].upper() + region_name[1:]

            if not region_name:
                color['name'] = None
            else:
                color['name'] = region_name
                if region_name and color_names:
                    color['colors'] = sorted(color_names)

        if color['name'] is None:
            colors.append(None)  # type: ignore
        else:
            colors.append(color)

    return colors
