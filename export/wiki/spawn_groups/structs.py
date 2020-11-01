from typing import Iterable, List, Optional

from automate.hierarchy_exporter import ExportModel, Field
from export.wiki.maps.models import WeighedClassSwap
from ue.asset import UAsset
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


def convert_single_class_swap(d) -> WeighedClassSwap:
    result = WeighedClassSwap(from_class=sanitise_output(d['FromClass']),
                              exact=bool(d.get('bExactMatch', True)),
                              to=sanitise_output(d['ToClasses']),
                              weights=d['Weights'].values)

    if d['ActiveEvent'] and d['ActiveEvent'].value and d['ActiveEvent'].value.value:
        # Assigning "None" here is safe as it is the field default and therefore omitted
        result.during = str(d['ActiveEvent'])

    return result


def convert_class_swaps(pgd: UAsset) -> Iterable[WeighedClassSwap]:
    assert pgd.default_export
    export_data = pgd.default_export.properties
    d = export_data.get_property('GlobalNPCRandomSpawnClassWeights', fallback=None)
    if not d:
        return None

    for entry in d.values:
        yield convert_single_class_swap(entry.as_dict())


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
    classSwaps: Optional[List[WeighedClassSwap]]


class NpcLimit(ExportModel):
    bp: str
    mult: float = Field(..., title="Max desired NPC number multiplier")


def convert_group_entry(struct) -> NpcGroup:
    d = struct.as_dict()
    out = NpcGroup(
        name=str(d['AnEntryName']),
        weight=d['EntryWeight'],
        species=list(),
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
    if swaps:
        out.classSwaps = [convert_single_class_swap(entry.as_dict()) for entry in swaps]

    return out


def convert_limit_entries(array) -> Iterable[NpcLimit]:
    for entry in array:
        d = entry.as_dict()
        npc_class = sanitise_output(d['NPCClass'])

        if npc_class:
            yield NpcLimit(bp=npc_class, mult=d['MaxPercentageOfDesiredNumToAllow'])
