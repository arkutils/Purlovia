# Asset interactive experiments

#%% Setup
from interactive_utils import *
from ue.base import UEBase
from ue.asset import UAsset, ExportTableItem, ImportTableItem
from ue.loader import AssetLoader
from ue.stream import MemoryStream
from ue.utils import *
from ue.coretypes import *
from ue.properties import *
from automate.ark import ArkSteamManager
import ark.mod
import ark.asset
import ark.properties
from ark.common import *

arkman = ArkSteamManager()
loader = arkman.createLoader()

#%% Select asset
# AllDinosAchievementNameTags (89 entries), GlobalCuddleFoodList (15 entries), DinoEntries (journal? 147 entries)
# PlayerLevelEngramPointsSP, PlayerLevelEngramPoints,
# To checkout:
#   StatusValueModifierDescriptions (array of structs, unreadable)
#   StatusValueDefinitions (unsupported struct x 12)
#   StatusStateDefinitions (unsupported struct x 13...maybe not useful)
# ...are server and single-player default mults in here???
# assetname = '/Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP'

# assetname = '/Game/PrimalEarth/CoreBlueprints/PrimalGlobalsBlueprint'  # !*!*! DECODE ERROR
# assetname = '/Game/PrimalEarth/CoreBlueprints/BASE_PrimalGameData_BP'  # master item/engram table
# assetname = '/Game/PrimalEarth/CoreBlueprints/PrimalGameData_BP'  # post-processing effects
# assetname = '/Game/PrimalEarth/CoreBlueprints/PrimalPlayerDataBP'  # not useful
# assetname = '/Game/PrimalEarth/CoreBlueprints/PrimalPlayerDataBP_Base'  # player data - ascention
# assetname = '/Game/Aberration/CoreBlueprints/DinoCharacterStatusComponent_BP_MoleRat'

# assetname = '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant'
# assetname = '/Game/Extinction/Dinos/Owl/Owl_Character_BP'
# assetname = '/Game/Extinction/Dinos/Owl/DinoSettings_Carnivore_Large_Owl'
# assetname = '/Game/Aberration/Dinos/MoleRat/MoleRat_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Diplodocus/Diplodocus_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Tusoteuthis/Tusoteuthis_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Turtle/Turtle_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Troodon/Troodon_Character_BP'

# assetname = '/Game/PrimalEarth/CoreBlueprints/Dino_Character_BP'
# assetname = '/Game/PrimalEarth/CoreBlueprints/Dino_Character_BP_Pack'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoColorSet_Dodo'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Dodo'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Argent'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Diplodocus'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Tuso'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Turtle'

# assetname = '/Game/Mods/ClassicFlyers/Dinos/Ptero/Ptero_Character_BP'
# assetname = '/Game/Mods/895711211/PrimalGameData_BP_ClassicFlyers'

# Failure case: fails to decode the only export (properties, invalid name)
# assetname = '/Game/Mods/ClassicFlyers/Dinos/AdminArgent/Assets/T_AdminArgent_Smaller_Colorize_d'

# Experimenting with CharacterStatusComponentPriority
# assetname = '/Game/PrimalEarth/Dinos/Bigfoot/Yeti_Character_BP'
assetname = '/Game/PrimalEarth/Dinos/Raptor/Uberraptor/Deinonychus_Character_BP'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Deinonychus'

asset = loader[assetname]
print('Decoding complete.')

#%% More display demos
# print('\nNames:')
# pprint(asset.names)
# print('\nImports:')
# pprint(asset.imports)
# print('\nExports:')
# pprint(asset.exports)

#%%
# for i, export in enumerate(asset.exports):
#     print(f'\nExport {i}:')
#     pprint(export)
#     pprint(export.properties)

#%% Try to discover inheritance
print('\nParent package:')
if asset.default_export:
    parent_pkg = ark.asset.findExportSourcePackage(asset.default_export)
    print(parent_pkg)
else:
    print('-not found-')

#%% Try to discover sub-components
print('\nComponents:')
pprint(list(ark.asset.findParentPackages(asset)))
print('\nSub-components:')
pprint(list(ark.asset.findSubComponentParentPackages(asset)))

#%% Mod info
# print('\nMod adds species:')
# pprint(ark.mod.get_species_from_mod(asset))

#%%
print('\nComponents:')
for export in ark.asset.findComponentExports(asset):
    print('Priority:', get_property(export, 'CharacterStatusComponentPriority'))
    print('Type:', export.klass.value)
    print('Props:', len(export.properties.values))
    print('Parent:', export.klass.value.super)

print('\nSub-components:')
for export in ark.asset.findSubComponentExports(asset):
    print('Priority:', get_property(export, 'CharacterStatusComponentPriority'))
    print('Export:', export)
    print('Props:', len(export.properties.values))

#%% Inheritance/component scan


def calc_pkg(obj):
    if isinstance(obj, ObjectIndex):
        return calc_pkg(obj.value)

    this_asset = obj.asset
    pkg = None

    if isinstance(obj, ImportTableItem):
        pkg = str(obj.namespace.value.name)
    elif isinstance(obj, ExportTableItem):
        return "(local export)"
    else:
        raise ValueError('')

    if pkg is None:
        return None

    pkg = str(pkg)
    if pkg == this_asset.assetname:
        return '(local)'

    if not pkg.startswith('/Game'):
        return None

    return f'(from {pkg})'


def show_value(msg, obj, indent=0):
    value = get_clean_name(obj)
    if value:
        pkg = calc_pkg(obj) or ''
        print(f'{"  "*indent}{msg} {value} {pkg}')


INTERESTING_PROPS = (
    'bSpawnNestEgg',
    'CanLevelUpValue',
    'DinoNameTag',
    'MaxStatusValues',
    'RunningspeedModifier',
    'CharacterStatusComponentPriority',
)


def get_interesting_props(props, indent=0):
    pre = '  ' * (indent)
    for prop in props.values:
        # print(str(prop.header.name))
        if str(prop.header.name) not in INTERESTING_PROPS:
            continue

        yield f'{pre}{prop.header.name}[{prop.header.index}] = {prop.value}'


def scan_export(export: ExportTableItem, indent=0):
    print(f'{"  "*indent}{str(export.name)}:')
    show_value('sub-component of', export.namespace, indent=indent + 1)
    show_value('is a', export.klass, indent=indent + 1)
    show_value('inherits from', export.super, indent=indent + 1)
    props = list(sorted(get_interesting_props(export.properties, indent=indent + 2)))
    if not props:
        print(f'{"  "*(indent+1)}no properties')
    else:
        print(f'{"  "*(indent+1)}properties:')
        for prop in props:
            print(prop)
    print()


def scan_asset(asset: UAsset, indent=0):
    pre = '\t' * indent
    print(f'{pre}{asset.assetname}:')

    for export in asset.exports:
        if str(export.name).startswith('Default__'):
            scan_export(export, indent=indent + 1)

        elif export.klass and export.klass.value and 'BlueprintGeneratedClass' in str(export.klass.value):
            scan_export(export, indent=indent + 1)

    print()


#%%
print()

scan_asset(asset)

for parent in ark.asset.findParentPackages(asset):
    scan_asset(loader[parent])

for comp in ark.asset.findSubComponentParentPackages(asset):
    scan_asset(loader[comp])

#%% Taming info
# for assetname in (
#         '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP',
#         '/Game/PrimalEarth/Dinos/Lystrosaurus/Lystro_Character_BP',
#         '/Game/PrimalEarth/Dinos/Leedsichthys/Leedsichthys_Character_BP',
#         '/Game/PrimalEarth/Dinos/Moschops/Moschops_Character_BP',
#         '/Game/ScorchedEarth/Dinos/RockGolem/RockGolem_Character_BP',
# ):
#     print(f'\n{assetname}:')
#     props = ark.properties.gather_properties(loader[assetname])
#     for n in ('bCanBeTamed', 'bPreventSleepingTame', 'bSupportWakingTame', 'RequiredTameAffinity',
#               'Required Tame Affinity Per Base Level', 'TameIneffectivenessByAffinity',
#               'WakingTameFoodConsumptionRateMultiplier', 'Base Food Consumption Rate', 'Prone Water Food Consumption Multiplier',
#               'Knocked Out Torpidity Recovery Rate Multiplier', 'Waking Tame Food Affinity Multiplier',
#               'The Max Torpor Increase Per Base Level'):
#         n = n.replace(' ', '')
#         print(f'{n:>44}: ', end='')
#         if n in props and 0 in props[n] and len(props[n][0]):
#             print(f'{props[n][0][-1]}')
#         else:
#             print(f'')

#     print(f'{"RecoveryRateStatusValue[TORPOR]":>44}: {ark.properties.stat_value(props, "RecoveryRateStatusValue", 2, None)}')

#%% Pre-set variables for experimenting
dcsc = loader.load_class(DCSC_CLS)
chr = loader.load_class(CHR_CLS)

deino_chr = loader.load_class('/Game/PrimalEarth/Dinos/Raptor/Uberraptor/Deinonychus_Character_BP.Deinonychus_Character_BP_C')
deino_chr_dcsc = next(ark.asset.findSubComponentExports(deino_chr.asset))
deino_dcsc = loader.load_related(deino_chr_dcsc.klass.value).default_class

yeti_chr = loader.load_class('/Game/PrimalEarth/Dinos/Bigfoot/Yeti_Character_BP.Yeti_Character_BP_C')
yeti_chr_dcsc = next(ark.asset.findSubComponentExports(yeti_chr.asset))
yeti_dcsc = loader.load_related(yeti_chr_dcsc.klass.value).default_class

#%%
