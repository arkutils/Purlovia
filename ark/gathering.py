from collections import defaultdict
from typing import *
from typing import cast

import ark.asset
import ark.tree
from ark.types import DCSC_CLS, DINO_CHR_CLS, PDC_CLS, PDSC_CLS, DinoCharacterStatusComponent
from ue.asset import ExportTableItem, UAsset
from ue.base import UEBase
from ue.context import ue_parsing_context
from ue.hierarchy import find_parent_classes, inherits_from
from ue.loader import AssetLoader, AssetLoadException
from ue.proxy import UEProxyStructure, get_proxy_for_type
from ue.utils import get_clean_name, get_property


def extract_properties_from_export(export, props: Dict[str, Dict[int, UEBase]], skip_top=False, recurse=False, report=False):
    '''Restricted version of old gather_properties that only act on a single export (and optionally its parents).'''
    if recurse:
        parent = ark.tree.get_parent_of_export(export)
        if parent:
            extract_properties_from_export(parent, props, recurse=recurse)

    if skip_top:
        return

    if report: print(f'Props from {export.fullname}')
    for prop in export.properties.values:
        propname = str(prop.header.name)
        if propname:
            propindex = prop.header.index or 0
            props[propname][propindex] = cast(UEBase, prop.value)


def find_default_export_for_asset(species_cls: ExportTableItem):
    return species_cls.asset.default_export


def gather_dcsc_properties(species_cls: ExportTableItem, *, alt=False, report=False) -> DinoCharacterStatusComponent:
    '''
    Gather combined DCSC properties from a species, respecting CharacterStatusComponentPriority.
    '''
    assert species_cls.asset and species_cls.asset.loader
    if not inherits_from(species_cls, PDC_CLS):
        raise ValueError("Supplied export should be a species character class")

    loader: AssetLoader = species_cls.asset.loader
    dcscs: List[Tuple[float, ExportTableItem]] = list()

    proxy: DinoCharacterStatusComponent = get_proxy_for_type(DCSC_CLS, loader)

    chain = list(find_parent_classes(species_cls, include_self=True))

    with ue_parsing_context(properties=True):
        # Gather DCSCs as we traverse from UObject back towards this species class
        for cls_name in reversed(chain):
            if not cls_name.startswith('/Game'):
                continue

            asset: UAsset = loader[cls_name]
            for dcsc_export in _get_dcscs_for_species(asset):
                # Calculate the priority of this DCSC
                pri_prop = get_property(dcsc_export, "CharacterStatusComponentPriority")
                if pri_prop is None:
                    dcsc_cls = loader.load_related(dcsc_export.klass.value).default_export
                    pri_prop = get_property(dcsc_cls, "CharacterStatusComponentPriority")
                pri = 0 if pri_prop is None else float(pri_prop)
                if report: print(f'DCSC from {asset.assetname} = {dcsc_export.fullname} (pri {pri_prop} = {pri})')
                dcscs.append((pri, dcsc_export))

        # Order the DCSCs by CharacterStatusComponentPriority value, descending
        # Python's sort is stable, so it will maintain the gathered order of exports with identical priorities (e.g. Deinonychus)
        dcscs.sort(key=lambda p: p[0])

        # Collect properties from each DCSC in order
        props: Dict[str, Dict[int, UEBase]] = defaultdict(lambda: defaultdict(lambda: None))  # type: ignore
        for _, dcsc in dcscs:
            extract_properties_from_export(dcsc, props, skip_top=alt, recurse=True, report=False)
        proxy.update(props)

    return proxy


def _get_dcscs_for_species(asset: UAsset) -> Iterable[ExportTableItem]:
    for cmp_export in ark.asset.findSubComponentExports(asset):
        if inherits_from(cmp_export, DCSC_CLS, safe=True):
            yield cmp_export
