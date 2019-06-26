#%% Run Me
import json
import os
from automate.ark import ArkSteamManager, readModData

arkman = ArkSteamManager('./livedata', skipInstall=True)
loader = arkman.createLoader()

#%% Gather all assets from all mods
assets_to_load = []
with open('asb_json/values.json') as json_file:
    data = json.load(json_file)
    for species in data['species']:
        assets_to_load.append(species['blueprintPath'])
for r, d, f in os.walk('./output'):
    for file in f:
        with open(os.path.join(r, file)) as json_file:
            data = json.load(json_file)
            for species in data['species']:
                assets_to_load.append(species['blueprintPath'])

print(len(assets_to_load))

#%% Extract Names from assets and compare them
real_names = []
names = []
first_run = True
skipped_count = 0
for asset_to_load in assets_to_load:
    asset = loader[asset_to_load.split('.')[0]]
    if first_run:
        for name in asset.names.values:
            real_names.append(name.value)
        print(real_names)
    else:
        for name in asset.names.values:
            names.append(name.value)
        initial_len = len(real_names)
        real_names = list(set(names) & set(real_names))
        if initial_len > len(real_names):
            print(f'Parsed {skipped_count} without removing any names')
            skipped_count = 0
            print(f'Removed {initial_len - len(real_names)} names')
        else:
            skipped_count += 1

        # print(real_names)

    if first_run:
        first_run = False

    # input("Skip...")

print(f'Parsed {skipped_count} without removing any names')
print(real_names)

#%% Attempt to load assets and verify if they're a species asset or not
required_names = [
    'DescriptiveName', 'CapsuleComponent', 'DefaultSceneRootNode', 'CharMoveComp', 'ShooterCharacterMovement',
    'CollisionCylinder', 'UpdatedComponent', 'SkeletalMesh', 'AttachParent', 'CategoryName', 'CharacterMesh0', 'Game',
    'MaterialInstanceConstant', 'SkeletalMeshComponent', 'RootComponent', 'Default', 'CharacterMovement',
    'SimpleConstructionScript', 'VariableName', 'UserConstructionScript', 'SCS_Node', 'bUseColorization', 'ComponentTemplate',
    'Mesh', 'DefaultSceneRoot', 'SceneComponent'
]

names = []

asset = loader['/Game/Mods/ClassicFlyers/Dinos/AdminArgent/ClassicAdminArgent_Character_BP']
asset = loader['/Game/Mods/ClassicFlyers/Dinos/AdminArgent/DinoCharacterStatusComponent_BP_ClassicAdminArgent']
asset = loader['/Game/Mods/ClassicFlyers/Dinos/AdminArgent/DinoCharacterStatusComponent_BP_ClassicAdminArgent']
asset = loader['/Game/Mods/ClassicFlyers/Dinos/AdminArgent/DinoCharacterStatusComponent_BP_ClassicAdminArgent']
asset = loader['/Game/Mods/ClassicFlyers/Dinos/AdminArgent/DinoCharacterStatusComponent_BP_ClassicAdminArgent']
asset = loader['/Game/Mods/ClassicFlyers/Dinos/AdminArgent/Assets/DinoColorSet_AdminArgent']

for name in asset.names.values:
    names.append(name.value)

output = list(set(required_names) - set(names))
print(output)

#%%
