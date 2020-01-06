from collections.abc import Iterable
from typing import Any, Dict

from ue.base import UEBase


def _get_formatted_value(data: Any) -> Any:
    if hasattr(data, 'format_for_json'):
        return data.format_for_json()
    elif isinstance(data, UEBase):
        return str(data)
    
    return data

def format_data_fragment_for_export(data: Any) -> Any:
    if isinstance(data, dict):
        for key in data.keys():
            data[key] = format_data_fragment_for_export(data[key])

        return data
    elif isinstance(data, list) or isinstance(data, tuple):
        return [format_data_fragment_for_export(value) for value in data]
    else:
        return _get_formatted_value(data)
