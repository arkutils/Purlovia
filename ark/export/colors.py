import warnings
from typing import *

import ark.mod
from ark.properties import PriorityPropDict, gather_properties, stat_value
from ue.asset import UAsset
from ue.loader import AssetLoader
from ue.properties import LinearColor, UEBase

__all__ = [
    'gather_pgd_colors',
    'gather_color_data',
]

cached_color_defs: List[Tuple[str, Tuple[float, float, float, float]]] = []

NUM_REGIONS = 6

ColorEntry = Tuple[str, Tuple[float, float, float, float]]


def gather_pgd_colors(props: PriorityPropDict, loader: AssetLoader,
                      require_override=True) -> Tuple[Optional[Sequence[ColorEntry]], Optional[Sequence[ColorEntry]]]:
    '''Gather color and dye definitions from a PrimalGameData asset.'''
    colors: Optional[List[ColorEntry]] = list()
    dyes: Optional[List[ColorEntry]] = list()

    # Collect the color definitions
    color_def_overrides = props['ColorDefinitions'][0]
    if require_override and len(color_def_overrides) == 1:
        colors = None
    else:
        color_defs = color_def_overrides[-1].values
        colors = list()
        for definition in ((entry.as_dict() for entry in color_defs)):
            name = definition.get('ColorName', None) or '~~unset~~'
            value = definition.get('ColorValue', None)
            color = value.values[0].as_tuple() if value else None
            colors.append((str(name), color))

    # Collect the dye definitions
    dye_def_overrides = props['MasterDyeList'][0]
    if require_override and len(dye_def_overrides) == 1:
        dyes = None
    else:
        dye_defs = props['MasterDyeList'][0][-1].values
        dyes = list()
        for dye_asset in (loader.load_related(entry) for entry in dye_defs):
            dye_props = gather_properties(dye_asset)
            name = stat_value(dye_props, 'DescriptiveNameBase', 0, None) or '~~unset~~'
            value = dye_props['DyeColor'][0][-1]
            color = value.values[0].as_tuple() if value else None
            dyes.append((str(name), color))

    return (colors, dyes)


def gather_color_data(props: PriorityPropDict, loader: AssetLoader):
    '''Gather color region definitions for a species.'''
    colors: List[Any] = list()
    male_colorset = props['RandomColorSetsMale'][0][-1]
    female_colorset = props['RandomColorSetsFemale'][0][-1]

    male_colorset_props: Optional[PriorityPropDict] = None
    female_colorset_props: Optional[PriorityPropDict] = None

    # Choose which color set to use
    if male_colorset and male_colorset.value and male_colorset.value.value:
        male_colorset_props = ark.mod.gather_properties(loader.load_related(male_colorset))
    if female_colorset and female_colorset.value and female_colorset.value.value:
        female_colorset_props = ark.mod.gather_properties(loader.load_related(female_colorset))

    # TODO: Incorporate both male and female colorsets, as well as if multiple colorsets are listed
    colorset_props = male_colorset_props or female_colorset_props
    if not colorset_props:
        return None

    # Export a list of color names for each region
    for i in range(NUM_REGIONS):
        prevent_region = stat_value(props, 'PreventColorizationRegions', i, 0)
        color: Dict[str, Any] = dict()
        color_names: Set[str] = set()

        if prevent_region:
            color['name'] = None
        elif i not in colorset_props['ColorSetDefinitions']:
            color['name'] = None
        else:
            color_set_defs: Dict[str, UEBase] = colorset_props['ColorSetDefinitions'][i][-1].as_dict()
            color['name'] = str(color_set_defs.get('RegionName', 'Unknown Region Name'))
            if 'ColorEntryNames' in color_set_defs:
                for color_name in color_set_defs['ColorEntryNames'].values:
                    color_names.add(str(color_name))

        if not color_names:
            color['name'] = None

        color['colors'] = sorted(color_names)
        colors.append(color)

    return colors
