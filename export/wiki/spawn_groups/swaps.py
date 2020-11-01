from ue.asset import UAsset

from .structs import convert_single_class_swap

__all__ = ['convert_class_swaps']


def convert_class_swaps(pgd: UAsset):
    assert pgd.default_export
    all_values = []
    export_data = pgd.default_export.properties
    d = export_data.get_property('GlobalNPCRandomSpawnClassWeights', fallback=None)
    if not d:
        return None

    for entry in d.values:
        all_values.append(convert_single_class_swap(entry.as_dict()))

    return all_values
