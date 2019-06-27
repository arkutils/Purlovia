#%% Setup
from interactive_utils import *
import logging
logging.basicConfig(level=logging.INFO)

from automate.ark import ArkSteamManager

arkman = ArkSteamManager(skipInstall=False)

#%% Init
arkman.ensureSteamCmd()

#%% Update game
gamever = arkman.ensureGameUpdated()
print(f'\nGame:\n')
print(f'Version: {gamever}')
print(f'Content path: {arkman.getContentPath()}')
print()

#%% Update mods
arkman.ensureModsUpdated([
    # 829467257,  # SurvivalPlus
    # 839162288,  # Primal_Fear
    # 893735676,  # Ark Eternal
    895711211,  # ClassicFlyers
    # 919470289,  # SSFlyer
    # 1083349027,  # SpeedyFlyers
    # 1090809604,  # Pyria
    # 1125442531,  # Gaia
    # 1356703358,  # Primal_Fear_Noxious_Creatures
    # 1373744537,  # AC2
    # 1498206270,  # Small Dragon 2.0
    # 1522327484,  # Ark Additions: The Collection ?
    # 1675895024,  # NoUntameables
    # 1729386191,  # AC2Bonus
])
# print(f'\nMods:\n')
# pprint(modvers)
print()

#%% Check assets load properly
loader = arkman.createLoader()
print(f'\nChecking loader:\n')

assetnames = (
    'Game/Extinction/Dinos/Owl/Owl_Character_BP',
    '/Game/Mods/ClassicFlyers/Dinos/Ptero/Ptero_Character_BP',
)

for assetname in assetnames:
    asset = loader[assetname]
    assert asset, 'Asset failed to load: ' + assetname
    print(f'  {asset.assetname}')

print(f'\nDone.\n')
