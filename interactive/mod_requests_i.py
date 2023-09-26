# flake8: noqa
# Asset interactive experiments

#%% Setup

from interactive_utils import *  # pylint: disable=wrong-import-order

import sys
import csv
import yaml
from pathlib import Path
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
    # '1967035140',  # AramoorePlus (locked to specific servers - probably don't support)
    # '2676028144',  # TaeniaStella (large map that also requires CrystalIsles - now replaced with TaeniaStella The RenewalAlpha)
    # '1558114752',  # Dino hybrids & more [Radioactive]
    # '1838617463',  # Fjordur (renamed Fjell to separate from Fjordur DLC, but tag still clashes)

    # Unable to process currently
    # '632898827',  # Dino Colors Plus - adds copies of vanilla species with more colours
    # '833379388',  # Pugnacia Dinos

    # Removed from Steam?
    # '1840936777',  # Prometheus
    # '2672233461',  # Ark Supreme

    # Candidates
    '843960973',  # Dragontail
    '1880357240',  # Sanctuary Overhaul
    '1912090921',  # Scratchy Claws' Improved Flyers
    '1511268523',  # Gunsmoke Animals
    '2251437896',  # TheBurningLoop Community Mod
    '908817184',  # Nightmare Pegasus
    '1592652278',  # Random Egg Spawner 2.0
    '2117433951',  # Galvanized Wolf
    '1534108504',  # VWSR - Dino Rebalance, Tameable Alphas, Sub Species and More
    '1134797219',  # Breedable Griffins
    '1230977449',  # Exiles of the ARK
    '1314441674',  # ARK: Parados
    '1788616268',  # Argentavis Darting Saddle
    '1989252120',  # ARK: Reclamation
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
runs = yaml.safe_load(Path('config/runs.yaml').read_text())
runs = {k: v for k, v in runs.items() if not k.startswith('_')}
mods_from_runs = {str(modid) for run in runs.values() for modid in run.get('mods', [])}
mods_from_config = set(config.mods)
all_existing_mods = mods_from_runs | mods_from_config
print(f'Pre-existing mods: {len(all_existing_mods)}')
already_enabled = all_existing_mods.intersection(modids)
if already_enabled:
    print('Already in config:')
    for modid in already_enabled:
        print(modid)
    sys.exit(0)

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
