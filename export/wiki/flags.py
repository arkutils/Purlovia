from typing import Iterable, List

from ue.proxy import UEProxyStructure


def gather_flags(proxy: UEProxyStructure, flags: Iterable[str]) -> List[str]:
    result = [_clean_flag_name(field) for field in flags if proxy.get(field, fallback=False)]
    return result


def _clean_flag_name(name: str):
    if len(name) >= 2 and name[0] == 'b' and name[1] == name[1].upper():
        return name[1].lower() + name[2:]

    if len(name) >= 1:
        return name[0].lower() + name[1:]

    raise ValueError("Invalid flag name found")
