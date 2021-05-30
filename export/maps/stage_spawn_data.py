import math
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from automate.jsonutils import save_as_json
from ue.hierarchy import find_sub_classes
from utils.log import get_logger

from .common import order_growing
from .spawn_maps.consts import MERGED_DINOS
from .stage_base import JsonProcessingStage, ModType

logger = get_logger(__name__)

__all__ = [
    'GenerateSelfContainedSpawnDataStage',
]


class GenerateSelfContainedSpawnDataStage(JsonProcessingStage):
    def get_name(self) -> str:
        return "spawn_data"

    def get_files_to_load(self, modid: Optional[str]) -> List[str]:
        return ['species', 'spawn_groups']

    def process(self, base_path: Path, modid: Optional[str], modtype: Optional[ModType], data: Dict[str, List[Any]]):
        # Ensure all bare minimum data is available
        assert data['species'] and data['spawn_groups']

        # Discover maps
        if not modid or modtype == ModType.GameMod:
            map_names = list(self.find_maps(None, keyword='npc_spawns'))
            base_map_path = self.wiki_path
        elif modtype == ModType.CustomMap:
            map_names = list(self.find_maps(modid, keyword='npc_spawns'))
            base_map_path = self.wiki_path / self.get_mod_subroot_name(modid)
        else:
            return

        # Load map data
        mapdata: Dict[str, Dict[str, Any]] = defaultdict(dict)
        for name in map_names:
            wsfile = (base_map_path / name / 'world_settings').with_suffix('.json')
            npcfile = (base_map_path / name / 'npc_spawns').with_suffix('.json')
            mapdata[name]['world_settings'] = self.load_json_file(wsfile)
            mapdata[name]['npc_spawns'] = self.load_json_file(npcfile)

        # Expand spawning groups data
        fullbaked, halfbaked = self._expand_spawning_groups_data(data['spawn_groups'])

        # Generate a file per map.
        for name in map_names:
            logger.info(f'Expanding spawn data for {name}')

            # Scan NPC zones for used containers.
            required_groups = set()
            for zone in mapdata[name]['npc_spawns']['spawns']:
                if not zone.get('disabled', False):
                    required_groups.add(zone['spawnGroup'])

            # Filter containers to only operate on those used on map.
            ignores_global_random_swaps = mapdata[name]['world_settings']['worldSettings'].get('onlyEventGlobalSwaps', False)
            filter_source = halfbaked if ignores_global_random_swaps else fullbaked
            local_containers = list(filter(lambda x: x['bp'] in required_groups, filter_source))

            # Create a copy of the containers data.
            containers_copy = deepcopy(local_containers)

            # Check if map has its own custom global replacements.
            random_map_swaps = mapdata[name]['world_settings']['worldSettings'].get('randomNPCClassWeights', None)
            if random_map_swaps:
                # Evaluate.
                random_map_swaps = self._rebuild_random_swaps_with_hierarchy(random_map_swaps)
                random_map_swaps_lookup = self._build_class_lookup_from_random_swaps(random_map_swaps)
                self._evaluate_random_swaps_on_containers(containers_copy, random_map_swaps_lookup)

            # Make a lookup table from blueprint path to container.
            container_lookup = dict()
            for container in containers_copy:
                container_lookup[container['bp']] = container

            # Build creature probability table.
            containers_to_species = self._build_species_probability_table(container_lookup)

            # Scan NPC zones and retrieve info that might be needed for rarity calculations.
            zones = []
            required_groups = set()
            for zone in mapdata[name]['npc_spawns']['spawns']:
                # Skip if manager is disabled.
                if zone.get('disabled', False):
                    continue

                # Skip if NPC count is -1.
                npc_count = zone['minDesiredNumberOfNPC']
                if npc_count == -1:
                    continue

                # Skip if there's no counting locations.
                counters = zone.get('locations', None)
                if not counters:
                    continue

                # Retrieve species list.
                container_bp = zone['spawnGroup']
                species = containers_to_species.get(container_bp, None)
                if not species:
                    continue

                # Calculate total area of the counting locations
                area = 0.0
                for counter in counters:
                    start = counter['start']
                    end = counter['end']

                    # Order coordinates.
                    start_long, end_long = order_growing(start['long'], end['long'])
                    start_lat, end_lat = order_growing(start['lat'], end['lat'])

                    area += (end_long-start_long) * (end_lat-start_lat)

                # Calculate species rarities.
                npc_count = npc_count * container_lookup[container_bp]['maxNPCNumberMultiplier']
                rarities: Dict[str, float] = dict()
                for species_bp, probability in species.items():
                    creature_density = (probability*npc_count) / area
                    # This formula has been arbitrarily constructed by Cadaei to create 5 naturally feeling groups
                    # of rarity 0..5 (very rare to very common)
                    rarity = min(5, round(1.5 * (math.log(1 + 50*creature_density))))
                    rarities[species_bp] = rarity

                # Push processed info to the final list.
                zones.append(
                    dict(
                        container=container_bp,
                        npcCount=npc_count,
                        untameable=zone['forceUntameable'],
                        cave='Cave' in container_bp or 'UnderwaterGround' in container_bp,
                        creatures=rarities,
                        locations=zone.get('spawnLocations', None),
                        points=zone.get('spawnPoints', None),
                    ))

            # Remove consumed fields from container data.
            for _, container in container_lookup.items():
                del container['bp']
                del container['maxNPCNumberMultiplier']

            # Emit file.
            save_as_json(
                dict(
                    level=mapdata[name]['world_settings']['persistentLevel'],
                    zones=zones,
                    containers=container_lookup,
                ), base_path / name / 'stage1.json', True)

    def _expand_spawning_groups_data(self, data: List[Any]) -> Tuple[List[Any], List[Any]]:
        containers = []
        random_swaps = None
        extra_groups = []
        remaps = []

        # Grab all spawning group containers and first global random replacements rule set.
        for file in data:
            containers += file['containers']
            if 'randomSwaps' in file and not random_swaps:
                random_swaps = file['randomSwaps']
            if 'extraGroups' in file:
                extra_groups += file['extraGroups']
            if 'remaps' in file:
                remaps += file['remaps']

        # Splice extra groups with containers.
        self._splice_groups_and_containers(containers, extra_groups)
        del extra_groups

        # Normalize entries.
        self._normalize_group_members_in_containers(containers)

        # Remap creatures
        if remaps:
            remap_lookup = self._build_class_lookup_from_remaps(remaps)
            self._apply_remaps_to_containers(containers, remap_lookup)

        # Evaluate group-level random replacements.
        self._evaluate_group_random_swaps(containers)

        # Evaluate global random replacements. If there are any, copy the containers to preserve the original values for maps
        # like Genesis 1.
        halfbaked = containers
        if random_swaps:
            halfbaked = deepcopy(containers)
            random_swaps = self._rebuild_random_swaps_with_hierarchy(random_swaps)
            random_swaps_lookup = self._build_class_lookup_from_random_swaps(random_swaps)
            self._evaluate_random_swaps_on_containers(containers, random_swaps_lookup)

        # Merge creatures depending on our lists.
        merger_lookup = self._build_class_lookup_from_merged_dinos()
        self._apply_remaps_to_containers(containers, merger_lookup)

        return (containers, halfbaked)

    def _splice_groups_and_containers(self, containers: List[Any], extras: List[Any]):
        # Create a lookup table of containers.
        container_lookup = dict()
        for container in containers:
            container_lookup[container['bp']] = container

        # Do the splicing.
        for insertion in extras:
            # Make sure we do have a container for this.
            bp = insertion['bp']
            container = container_lookup.get(bp, None)
            if not container:
                continue

            # Make sure entries and limits are initialized on the container.
            if 'entries' not in container:
                container['entries'] = []
            if 'limits' not in container:
                container['limits'] = []

            # Append.
            container['entries'] += insertion.get('entries', [])
            container['limits'] += insertion.get('limits', [])

    def _normalize_group_members_in_containers(self, containers: List[Dict[str, Any]]):
        for container in containers:
            for group in container['entries']:
                new_members = []

                for member in group['species']:
                    member['chance'] = min(1, max(0, member['chance']))

                    if member['chance'] > 0 and member.get('bp', None):
                        new_members.append(member)

                group['species'] = new_members

    def _build_class_lookup_from_remaps(self, remaps: List[Dict[str, str]]) -> Dict[str, str]:
        out = dict()

        for rule in remaps:
            from_class = rule['from']
            if from_class and from_class not in out:
                out[from_class] = rule['to']

        return out

    def _apply_remaps_to_containers(self, containers: List[Dict[str, Any]], remap_lookup: Dict[str, str]):
        for container in containers:
            for group in container['entries']:
                for member in group['species']:
                    target = remap_lookup.get(member['bp'], None)
                    if target:
                        member['bp'] = target

    def _rebuild_random_swaps_with_hierarchy(self, random_swaps: List[Any]) -> List[Any]:
        results = []

        for rule in random_swaps:
            # Ignore event replacements and null matches.
            if 'during' in rule or rule['from'] is None or not rule['to']:
                continue

            # Copy the rule.
            rule_copy = dict(rule)

            # Make the "from" field a list of matched classes.
            class_to_match = rule['from']
            rule_copy['from'] = [class_to_match]
            results.append(rule_copy)

            # Extension: Add a pre-calculated weight sum.
            rule_copy['+sum'] = sum(x[0] for x in rule_copy['to'])

            # Append subclasses to the "from" list.
            if 'exact' not in rule:
                rule_copy['from'] += find_sub_classes(class_to_match)

        return results

    def _evaluate_group_random_swaps(self, containers: List[Dict[str, Any]]):
        for container in containers:
            for group in container['entries']:
                # Skip if the group has no random replacements.
                random_swaps = group.get('randomSwaps', None)
                if not random_swaps:
                    continue

                # Rebuild the random swaps with hierarchy.
                random_swaps = self._rebuild_random_swaps_with_hierarchy(random_swaps)

                # Evaluate.
                class_lookup = self._build_class_lookup_from_random_swaps(random_swaps)
                self._evaluate_random_swaps_on_group(group, class_lookup)

                del group['randomSwaps']

    def _build_class_lookup_from_random_swaps(self, random_swaps: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        out = dict()

        # Build a first-in lookup from dino class to random replacement rule.
        for rule in random_swaps:
            for class_to_match in rule['from']:
                if class_to_match not in out:
                    out[class_to_match] = rule

        return out

    def _evaluate_random_swaps_on_group(self, group: Dict[str, Any], class_lookup: Dict[str, Dict[str, Any]]):
        members = group['species']
        new_members = []

        for member in members:
            # Check if member is valid.
            bp = member.get('bp', None)
            if not bp:
                continue

            # Find a random replacement rule this member might be affected by.
            rule = class_lookup.get(bp, None)
            if rule:
                # Evaluate the random replacement.
                rule_sum = rule['+sum']
                for weight, target in rule['to']:
                    # Calculate new member's chance.
                    chance = (weight/rule_sum) * member['chance']

                    # Add a new member.
                    new_member = dict(chance=chance, bp=target)
                    new_members.append(new_member)

            else:
                # Push the member back onto the list.
                new_members.append(member)

        group['species'] = new_members

    def _evaluate_random_swaps_on_containers(self, containers: List[Dict[str, Any]], class_lookup: Dict[str, Dict[str, Any]]):
        for container in containers:
            for group in container['entries']:
                self._evaluate_random_swaps_on_group(group, class_lookup)

    def _build_class_lookup_from_merged_dinos(self) -> Dict[str, str]:
        out = dict()
        for group in MERGED_DINOS:
            assert len(group) >= 2
            target_bp = group[0]
            for bp in group[1:]:
                out[bp] = target_bp
        return out

    def _build_species_probability_table(self, containers: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        # Generate a containers to species table to gather all locations later in a single pass.
        containers_to_species: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(lambda: 0))

        for container_bp, container in containers.items():
            # Sum up group weights.
            weight_sum = sum(x['weight'] for x in container['entries'])

            for group in container['entries']:
                # Calculate this group's chance.
                group_chance = group['weight'] / weight_sum

                for member in group['species']:
                    # Increase probability of the species in the main table.
                    member_bp = member['bp']
                    member_chance = member['chance']
                    containers_to_species[container_bp][member_bp] += member_chance * group_chance

        return containers_to_species
