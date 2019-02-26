# Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP
# Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Argent
# Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Dodo
# Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Rex
# Game\Extinction\CoreBlueprints\DinoCharacterStatusComponent_BP_Gacha
# Game\Extinction\CoreBlueprints\DinoCharacterStatusComponent_BP_Owl

# Game\PrimalEarth\Dinos\Argentavis\Argent_Character_BP
# Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP
# Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP_Aberrant
# Game\PrimalEarth\Dinos\Rex\Rex_Character_BP
# Game\Extinction\Dinos\Gacha\Gacha_Character_BP
# Game\Extinction\Dinos\Owl\Owl_Character_BP

#%% Imports
from pprint import pprint
import uasset
uasset.set_asset_path(r'.')


#%% Load base properties
base = uasset.load_and_parse('Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP')
print('\Base properties:')
pprint(base.props)

#%% Load species properties
species = uasset.load_and_parse('Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Dodo')
print('\Species properties:')
pprint(species.props)

#%% Try merge species properties into base ones
combined_props = uasset.merge_properties(base, species)
print('\nCombined properties:')
pprint(combined_props)
