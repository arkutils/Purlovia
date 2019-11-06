# Asset interactive experiments

#%% Setup

from interactive.setup import *  # pylint: disable=wrong-import-order

import json

import ark.asset
import ark.mod
import ark.properties
import ue.gathering
from ark.common import *
from ark.types import PrimalItem
from ue.base import UEBase
from ue.coretypes import *
from ue.properties import *
from ue.stream import MemoryStream
from ue.utils import get_clean_name

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
# assetname = '/Game/PrimalEarth/Dinos/Raptor/Uberraptor/Deinonychus_Character_BP'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Deinonychus'

# assetname = '/Game/PrimalEarth/CoreBlueprints/Items/PrimalItemDye_ActuallyMagenta'

assetname = '/Game/PrimalEarth/CoreBlueprints/Items/Structures/Halloween/PrimalItemStructure_Pumpkin'

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
# print('\nParent package:')
# if asset.default_export:
#     parent_pkg = ark.asset.findExportSourcePackage(asset.default_export)
#     print(parent_pkg)
# else:
#     print('-not found-')

#%% Try to discover sub-components
# print('\nComponents:')
# pprint(list(ark.asset.findParentPackages(asset)))
# print('\nSub-components:')
# pprint(list(ark.asset.findSubComponentParentPackages(asset)))

#%% Mod info
# print('\nMod adds species:')
# pprint(ark.mod.get_species_from_mod(asset))

#%%
# print('\nComponents:')
# for export in ark.asset.findComponentExports(asset):
#     print('Priority:', get_property(export, 'CharacterStatusComponentPriority'))
#     print('Type:', export.klass.value)
#     print('Props:', len(export.properties.values))
#     print('Parent:', export.klass.value.super)

# print('\nSub-components:')
# for export in ark.asset.findSubComponentExports(asset):
#     print('Priority:', get_property(export, 'CharacterStatusComponentPriority'))
#     print('Export:', export)
#     print('Props:', len(export.properties.values))

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

    return f'(from {pkg})'


def show_value(msg, obj, indent=0):
    value = get_clean_name(obj)
    if value:
        pkg = calc_pkg(obj) or ''
        print(f'{"  "*indent}{msg} {value} {pkg}')


INTERESTING_PROPS = (
    'bSpawnNestEgg',
    'CanLevelUpValue',
    'DescriptiveName',
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


def show_inheritance(obj: Union[ObjectIndex, ExportTableItem, ImportTableItem], indent: int = 0):
    if isinstance(obj, ObjectIndex):
        obj = obj.value

    if isinstance(obj, ImportTableItem):
        fullname = str(obj.namespace.value.name) + '.' + str(obj.name)
        try:
            obj = loader.load_class(fullname, fallback=None)
        except AssetNotFound:
            return

    if not obj or not obj.super:
        return

    show_value('from', obj.super, indent=indent)
    show_inheritance(obj.super, indent=indent + 1)


def scan_export(export: ExportTableItem, indent=0):
    print(f'{"  "*indent}{str(export.name)}:')
    show_value('sub-component of', export.namespace, indent=indent + 1)
    show_value('is a', export.klass, indent=indent + 1)
    show_value('inherits from', export.super, indent=indent + 1)
    show_inheritance(export.super, indent=indent + 2)
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


#%% Break down assets into components and sub-components visually
# print()
# scan_asset(asset)

# for parent in ark.asset.findParentPackages(asset):
#     scan_asset(loader[parent])

# for comp in ark.asset.findSubComponentParentPackages(asset):
#     try:
#         comp_asset = loader[comp]
#     except AssetNotFound:
#         continue
#     scan_asset(comp_asset)

#%% Working out where to find taming info
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

#%% Pre-set variables for experimenting with Deino and Yeti, for component priorities
# dcsc = loader.load_class(DCSC_CLS)
# chr = loader.load_class(CHR_CLS)

# deino_chr = loader.load_class('/Game/PrimalEarth/Dinos/Raptor/Uberraptor/Deinonychus_Character_BP.Deinonychus_Character_BP_C')
# deino_chr_dcsc = next(ark.asset.findSubComponentExports(deino_chr.asset))
# deino_dcsc = loader.load_related(deino_chr_dcsc.klass.value).default_class

# yeti_chr = loader.load_class('/Game/PrimalEarth/Dinos/Bigfoot/Yeti_Character_BP.Yeti_Character_BP_C')
# yeti_chr_dcsc = next(ark.asset.findSubComponentExports(yeti_chr.asset))
# yeti_dcsc = loader.load_related(yeti_chr_dcsc.klass.value).default_class

#%% Look at where UniqueGuidIds come from
# for assetname in ('/Game/PrimalEarth/Dinos/Raptor/Uberraptor/Deinonychus_Character_BP',
#                   '/Game/PrimalEarth/Dinos/Bigfoot/Yeti_Character_BP', '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP',
#                   '/Game/Aberration/Dinos/LanternBird/LanternBird_Character_BP',
#                   '/Game/Aberration/Dinos/LanternGoat/LanternGoat_Character_BP',
#                   '/Game/Aberration/Dinos/LanternLizard/LanternLizard_Character_BP',
#                   '/Game/ScorchedEarth/Dinos/RockGolem/RockGolem_Character_BP',
#                   '/Game/ScorchedEarth/Dinos/Wyvern/Wyvern_Character_BP_Fire',
#                   '/Game/ScorchedEarth/Dinos/Wyvern/Wyvern_Character_BP_Poison',
#                   '/Game/Mods/839162288/Dinos/Toxic/Toxic_Wyvern/Wyvern_Character_BP_Toxic_Ice',
#                   '/Game/Mods/893735676/Dinos/Ancient/BigFoot/Ancient_Bigfoot_Character_BP',
#                   '/Game/Mods/893735676/Dinos/Ancient/Quetz/Ancient_Quetz_Character_BP'):
#     props = ark.properties.gather_properties(loader[assetname])
#     guids = [(str(v.values[0].value), v.asset.assetname) for v in props['UniqueGuidId'][0]]
#     print(f'\n{assetname}:')
#     for guid, srcasset in guids:
#         print(f'  {guid} {srcasset}')

# ...answer is they're copied all over the place, so useless

#%%
# ue.gathering._discover_inheritance_chain(asset.default_class)

# dcsc_export = [e for e in asset.exports if 'Status' in str(e.name)][-1]
# props = ue.gathering.gather_properties(dcsc_export)

props = ue.gathering.gather_properties(asset.default_class)  # type: ignore

#%%
