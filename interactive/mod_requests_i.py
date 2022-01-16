# flake8: noqa
# Asset interactive experiments

#%% Setup

from interactive_utils import *  # pylint: disable=wrong-import-order

import csv
from datetime import datetime, timedelta
from math import ceil
from operator import itemgetter
from typing import *

from automate.ark import ArkSteamManager
from automate.steamapi import SteamApi
from config import ConfigFile, get_global_config

OLD_DAYS = 9 * 30

config = get_global_config()
config.settings.SkipInstall = True

arkman = ArkSteamManager(config=config)
arkman.ensureSteamCmd()
arkman.ensureGameUpdated()
arkman.ensureModsUpdated(config.mods)
loader = arkman.getLoader()

#%% Mod list

modids = set([
    # Delayed decisions
    '916417001',  # MAP: Ebenus Astrum -                                        CHECK for dinos

    # No
    # '538986229',   # Annunaki Genesis - obsolete, replaced with Ark Creatures Rebalanced (AG REBORN)
    # '972887420',   # Jurassic Park Expansion - massive and discontinued
    # '2205699189',  # Alpha Everything - probably only buffs
    # '2016338122',  # Shiny! Dinos - uses buffs
    # '1278441218',  # GunSmoke - this is the map
    # '1112780816',  # Insects-Plus - discontinued

    # Unable to process currently
    # '632898827',  # Dino Colors Plus - adds copies of vanilla species with more colours
    # '833379388',  # Pugnacia Dinos

    # Candidates
    '843960973',  # Dragontail
    '1679826889',  # Caballus Custom Map - The Equestrian Lan
    '1754846792',  # Zytharian Critters
    '1880357240',  # Sanctuary Overhaul
    '1989252120',  # ARK: Reclamation
    '1558114752',  # Dino hybrids & more (Radioactive tag?)
    '1967035140',  # AramoorePlus
    '2212177129',  # Sid's Hybrids
    '1912090921',  # Scratchy Claws' Improved Flyers
    '1840936777',  # Prometheus
    '1511268523',  # Gunsmoke Animals
    '2251437896',  # TheBurningLoop Community Mod
    '908817184',  # Nightmare Pegasus
    '2337840412',  # RR StarFarmanimals
    '2360410335',  # RR StarExoticAnimals
    '1592652278',  # Random Egg Spawner 2.0
    '710880648',  # DinoOverhaul X
    '1416912482',  # Bunn3h's extras
    '2117433951',  # Galvanized Wolf
    '2472371628',  # MilicrocaWarriors CommunityMod
    '1534108504',  # VWSR - Dino Rebalance, Tameable Alphas, Sub Species and More
    '1852495701',  # Shad's Better Gigas Rebalance
    '1134797219',  # Breedable Griffins
    '1838617463',  # Fjordur
])

#%% Conversion function


def data_from_mod(data):
    try:
        return dict(
            id=data['publishedfileid'],
            file_size=data.get('file_size', 0),
            title=data['title'],
            time_created=datetime.fromtimestamp(int(data['time_created'])),
            time_updated=datetime.fromtimestamp(int(data['time_updated'])),
            visibility=data['visibility'],
            banned=data['banned'] and (data['ban_reason'] or '<unknown ban reason>'),
            sub_count_current=data['subscriptions'],
            sub_count_lifetime=data['lifetime_subscriptions'],
            fave_count_current=data['favorited'],
            fave_count_lifetime=data['lifetime_favorited'],
            page_views=data['views'],
        )
    except KeyError as ex:
        print(data)
        raise ex


#%% Check for mods already enabled
already_enabled = set(config.mods).intersection(modids)
if already_enabled:
    print('Already in config:')
    for modid in already_enabled:
        print(modid)
    print()

#%% Fetch data for them all
mod_data = SteamApi.GetPublishedFileDetails(list(modids))
output_data = [data_from_mod(d) for d in mod_data]

#%% Config addition

age_cutoff = datetime.utcnow() - timedelta(days=OLD_DAYS)
for mod in sorted(output_data, key=lambda v: int(v['id'])):
    size = f"{ceil(mod['file_size']/1024.0/1024.0):>4.0f}"
    comment = f"{size} Mb, {mod['sub_count_current']:>7} subs, {mod['fave_count_current']:>6} faves"
    updated = mod['time_updated']
    if updated < age_cutoff:
        comment += f" (old? {updated.date()})"
    title = mod['title'][:40].replace('"', '\\"').replace('\n', ' ')
    title = f'"{title}"'
    print(f"{mod['id']:<10} = {title:42} # {comment}")

#%% CSV export

csv_filename = 'livedata/mod_requests.csv'
with open(csv_filename, 'wt', newline='', encoding='utf-8') as f:
    csv_writer = csv.writer(f)
    csv_writer.writerow(output_data[0].keys())
    csv_writer.writerows(mod.values() for mod in output_data)
    print()
    print(f'CSV saved as: {csv_filename}')
