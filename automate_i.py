#%% Setup
from interactive_utils import *

from automate.ark import ArkSteamManager

data_path = os.path.abspath(os.path.join('.', 'livedata'))
arkman = ArkSteamManager(data_path)

#%% Init
arkman.ensureSteamCmd()

#%% Update game
gamever = arkman.ensureGameUpdated()
print(f'\nGame:\n')
print(f'Version: {gamever}')
print(f'Content path: {arkman.getContentPath()}')

#%% Update mods
modvers = arkman.ensureModsUpdated([839162288, 1356703358, 895711211])
print(f'\nMods:\n')
pprint(modvers)
