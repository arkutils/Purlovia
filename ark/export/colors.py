import warnings
from typing import *

import ark.mod
from ark.properties import PriorityPropDict, stat_value
from ue.loader import AssetLoader
from ue.properties import LinearColor

cached_color_defs: List[Tuple[str, Tuple[float, float, float, float]]] = []

DEFAULT_COLOR_REGIONS = [0, 0, 0, 0, 0, 0]


# TODO: Move to somewhere more global, probably alongside gather_properties
def create_dict(prop):
    return dict((str(v.name), v.value) for v in prop.values)


# def convert_linear_color(lcolor: LinearColor):
#     # Uses rounded as it matches the export file values
#     return (lcolor.r.rounded, lcolor.g.rounded, lcolor.b.rounded, lcolor.a.rounded)

# TODO: Handle mod color definitions
# def read_colour_definitions(asset):
#     props = ark.mod.gather_properties(asset)

#     color_defs = []
#     for color_def in props['ColorDefinitions'][0][-1].values:
#         color_dict = create_dict(color_def)
#         color_defs.append((str(color_dict['ColorName']), convert_linear_color(color_dict['ColorValue'].values[0])))

#     return color_defs

# def ensure_color_data(loader: AssetLoader):
#     global cached_color_defs
#     if cached_color_defs: return
#     cached_color_defs = read_colour_definitions(loader['/Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP'])


def gather_color_data(props, loader: AssetLoader):
    colors: List[Any] = list()
    male_colorset = props['RandomColorSetsMale'][0][-1]
    female_colorset = props['RandomColorSetsFemale'][0][-1]

    male_colorset_props: Optional[PriorityPropDict] = None
    female_colorset_props: Optional[PriorityPropDict] = None

    # Verifies the listed colorsets aren't empty
    if male_colorset.value.value is not None:
        male_colorset_asset = loader.load_related(male_colorset)
        male_colorset_props = ark.mod.gather_properties(male_colorset_asset)
    elif female_colorset.value.value is not None:
        female_colorset_asset = loader.load_related(female_colorset)
        female_colorset_props = ark.mod.gather_properties(female_colorset_asset)
    else:
        return colors

    # TODO: Incorporate both male and female colorsets, as well as if multiple colorsets are listed
    colorset_props = male_colorset_props or female_colorset_props

    for i, region in enumerate(DEFAULT_COLOR_REGIONS):
        prevent_region = stat_value(props, 'PreventColorizationRegions', i, region)
        color: Dict[str, Any] = dict()
        color_names: Set[str] = set()

        if prevent_region:
            color['name'] = None
        elif i not in colorset_props['ColorSetDefinitions']:
            color['name'] = None
        else:
            color_set_defs = create_dict(colorset_props['ColorSetDefinitions'][i][-1])

            if 'RegionName' in color_set_defs:
                color['name'] = str(color_set_defs['RegionName'])
            else:
                color['name'] = 'Unknown Region Name'
            if 'ColorEntryNames' in color_set_defs:
                for color_name in color_set_defs['ColorEntryNames'].values:
                    color_names.add(str(color_name))

        if not color_names:
            color['name'] = None

        color['colors'] = sorted(color_names)
        colors.append(color)

    return colors
