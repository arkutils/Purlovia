from typing import Any, Dict, Iterable, List, Optional, Tuple

from automate.hierarchy_exporter import ExportModel, Field
from export.wiki.maps.models import WeighedClassSwap
from ue.asset import UAsset
from ue.properties import ArrayProperty
from ue.utils import sanitise_output

__all__ = [
    'NpcEntry',
    'NpcGroup',
    'NpcLimit',
    'convert_single_class_swap',
    'convert_class_swaps',
    'convert_group_entry',
    'convert_limit_entries',
]


def _zip_swap_outputs(d: Dict[str, Any]) -> Iterable[Tuple[float, Optional[str]]]:
    npcs: ArrayProperty = d['ToClasses']
    weights = d['Weights'].values

    for index, kls in enumerate(npcs.values):
        # Get weight of this class. Defaults to 1 if array is too short.
        weight = float(weights[index]) if index < len(weights) else 1.0
        yield (weight, sanitise_output(kls))


def convert_single_class_swap(d: Dict[str, Any]) -> Optional[WeighedClassSwap]:
    result = WeighedClassSwap(from_class=sanitise_output(d['FromClass']),
                              exact=bool(d.get('bExactMatch', True)),
                              to=list(_zip_swap_outputs(d)))

    if not result.from_class:
        return None

    if d['ActiveEvent'] and d['ActiveEvent'].value and d['ActiveEvent'].value.value:
        # Assigning "None" here is safe as it is the field default and therefore omitted
        result.during = str(d['ActiveEvent'])

    return result


def convert_class_swaps(pgd: UAsset) -> Optional[List[WeighedClassSwap]]:
    assert pgd.default_export
    export_data = pgd.default_export.properties
    d = export_data.get_property('GlobalNPCRandomSpawnClassWeights', fallback=None)
    if not d:
        return None

    out = []
    for entry in d.values:
        v = convert_single_class_swap(entry.as_dict())
        if v:
            out.append(v)

    return out


class Vector(ExportModel):
    x: float
    y: float
    z: float


class NpcEntry(ExportModel):
    chance: float
    bp: Optional[str]
    offset: Vector = Vector(x=0, y=0, z=0)


class NpcGroup(ExportModel):
    name: str
    weight: float
    species: List[NpcEntry]
    randomSwaps: List[WeighedClassSwap] = []


class NpcLimit(ExportModel):
    bp: str
    mult: float = Field(..., title="Max desired NPC number multiplier")


def convert_group_entry(struct) -> NpcGroup:
    d = struct.as_dict()
    out = NpcGroup(
        name=str(d['AnEntryName']),
        weight=d['EntryWeight'],
        species=list(),
        randomSwaps=[],
    )

    # Export zipped NPC entries
    chances = d['NPCsToSpawnPercentageChance'].values
    offsets = d['NPCsSpawnOffsets'].values
    for index, kls in enumerate(d['NPCsToSpawn'].values):
        npc = NpcEntry(
            chance=chances[index] if index < len(chances) else 1,
            bp=sanitise_output(kls),
            offset=sanitise_output(offsets[index] if index < len(offsets) else Vector(x=0, y=0, z=0)),
        )
        out.species.append(npc)

    # Export local random class swaps if any exist
    swaps = d['NPCRandomSpawnClassWeights'].values
    for entry in swaps:
        rule = convert_single_class_swap(entry.as_dict())
        if rule:
            out.randomSwaps.append(rule)

    return out


def convert_limit_entries(array) -> Iterable[NpcLimit]:
    already_found = set()

    for entry in array:
        d = entry.as_dict()
        npc_class = sanitise_output(d['NPCClass'])
        mult = d['MaxPercentageOfDesiredNumToAllow']

        # We've already seen this class so this rule does not matter in context of this container, skip it.
        if npc_class in already_found:
            continue

        # Only yield if the NPC class isn't a null and the max multiplier isn't 1.0.
        if npc_class and mult != 1.0:
            already_found.add(npc_class)
            yield NpcLimit(bp=npc_class, mult=mult)
