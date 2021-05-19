from itertools import zip_longest
from typing import List

from ark.types import PrimalDinoCharacter
from automate.hierarchy_exporter import ExportModel, Field
from export.wiki.inherited_structs import gather_inherited_struct_fields
from export.wiki.models import ItemChancePair
from export.wiki.stage_drops import decode_item_name
from ue.properties import FloatProperty, IntProperty


class DeathData(ExportModel):
    dossierId: IntProperty = Field(-1)
    lootBagChance: float = Field(0, description="Chance for a loot bag to appear on death")
    lootBags: List[ItemChancePair] = Field(
        [],
        description="Lists of possible loot bag drop sets (for cross-reference with drops.json files)",
    )
    engrams: List[str] = Field([], description="Engrams player receives when this creature is defeated")
    baseXP: FloatProperty = Field(
        0,
        description="XP awarded when level 1 creature is killed. Formula for specific level: baseXP * (1 + 0.1 * (level - 1))",
    )


LOOT_INVENTORY_TEMPLATES_DEFAULTS = {
    'Weights': None,
    'AssociatedObjects': None,
}


def gather_death_data(species: PrimalDinoCharacter) -> DeathData:
    out = DeathData(
        dossierId=species.DeathGivesDossierIndex[0],
        baseXP=species.KillXPBase[0],
    )

    engrams = species.get('DeathGiveEngramClasses', fallback=None)
    if engrams:
        # Output only valid engram references.
        for engram_ref in engrams:
            if engram_ref and engram_ref.value and engram_ref.value.value:
                out.engrams.append(decode_item_name(engram_ref))

    # Export possible loot bag drop components (for use with wiki.drops).
    loot_chance = species.DeathInventoryChanceToUse[0]
    if loot_chance > 0:
        loot_templates = gather_inherited_struct_fields(species.get_source(), 'DeathInventoryTemplates',
                                                        LOOT_INVENTORY_TEMPLATES_DEFAULTS)
        weights = loot_templates['Weights']
        drop_components = loot_templates['AssociatedObjects']

        if drop_components and drop_components.values:
            # Make sure there's no more weights than drop components
            if weights:
                weights = weights.values
            else:
                weights = []
            weights = weights[:len(drop_components.values)]

            # Go through each drop component and gather the possible choices.
            choices = list()
            for ref, weight in zip_longest(drop_components, weights, fillvalue=1):
                # Skip invalid drop component references.
                if not ref or not ref.value or not ref.value.value:
                    continue

                # Skip the component if its weight is lower than zero.
                if weight <= 0:
                    continue

                # Needed due to a bug in the UE module which will be fixed in another commit.
                choices.append((weight, ref.format_for_json().format_for_json()))

            # Convert the choices list into chance
            weight_sum = sum(t[0] for t in choices)
            for weight, ref in choices:
                out.lootBags.append(ItemChancePair(chance=weight / weight_sum, item=ref))

        # Clamp the primary chance for the bag between 0 and 1.
        # If there's no valid drop components, override it to zero.
        if out.lootBags:
            # Explicit float cast to avoid a type warning over missing overloads for int+object.
            out.lootBagChance = min(1, max(0, float(loot_chance)))
        else:
            out.lootBagChance = 0

    return out
