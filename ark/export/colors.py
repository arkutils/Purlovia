import warnings
from typing import *
from ue.loader import AssetLoader
from ue.properties import LinearColor
import ark.mod
from ark.properties import stat_value

cached_color_defs: List[Tuple[str, Tuple[float, float, float, float]]] = []

DEFAULT_COLOR_REGIONS = [0, 0, 0, 0, 0, 0]


# TODO: Move to somewhere more global, probably alongside gather_properties
def create_dict(prop):
    return dict((str(v.name), v.value) for v in prop.values)


def convert_linear_color(lcolor: LinearColor):
    # Uses rounded as it matches the export file values
    return (lcolor.r.rounded, lcolor.g.rounded, lcolor.b.rounded, lcolor.a.rounded)


def read_colour_definitions(asset):
    props = ark.mod.gather_properties(asset)

    color_defs = []
    for color_def in props['ColorDefinitions'][0][-1].values:
        color_dict = create_dict(color_def)
        color_defs.append((str(color_dict['ColorName']), convert_linear_color(color_dict['ColorValue'].values[0])))

    return color_defs


def ensure_color_data(loader: AssetLoader):
    global cached_color_defs
    if cached_color_defs: return
    cached_color_defs = read_colour_definitions(loader['/Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP'])


def gather_color_data(props, loader: AssetLoader):
    # TODO: Handle mod color definitions

    male_colorset_asset = loader.load_related(props['RandomColorSetsMale'][0][-1])
    male_colorset_props = ark.mod.gather_properties(male_colorset_asset)

    # Female Colorset
    # female_colorset_asset = loader.load_related(props['RandomColorSetsFemale'][0][-1])
    # female_colorset_props = ark.mod.gather_properties(female_colorset_asset)

    colors = list()
    for i, region in enumerate(DEFAULT_COLOR_REGIONS):
        prevent_region = stat_value(props, 'PreventColorizationRegions', i, region)
        color: Dict[str, Any] = dict()
        color_ids: List[int] = list()

        if prevent_region:
            color['name'] = None
        elif i not in male_colorset_props['ColorSetDefinitions']:
            color['name'] = None
        else:
            color_set_defs = create_dict(male_colorset_props['ColorSetDefinitions'][i][-1])

            try:
                color['name'] = str(color_set_defs['RegionName'])
            except:
                color['name'] = 'Unknown Region Name'

            if 'ColorEntryNames' in color_set_defs:
                # If one color doesn't exist, this entire region is nulled
                # Needs to be better implemented to support invalid color names
                try:
                    for color_name in color_set_defs['ColorEntryNames'].values:
                        color_id = [c_def[0] for c_def in cached_color_defs].index(str(color_name)) + 1
                        if color_id not in color_ids:
                            color_ids.append(color_id)
                except:
                    warnings.warn(f'{color_name} was not found in the Color definitions')

        if not color_ids:
            color['name'] = None

        color['colorIds'] = color_ids
        colors.append(color)

    return colors
