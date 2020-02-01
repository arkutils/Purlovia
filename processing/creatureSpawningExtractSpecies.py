# Helper for creatureSpawningMaps.py

import json
import re
import os

def ExtractSpecies(jsonSpawngroups):
    # load file with species names for blueprint paths
    bps = LoadBPSpecies()

    blueprintSpecies = {}
    
    if 'spawngroups' not in jsonSpawngroups:
        exit('no spawnGroups data')
    
    for sg in jsonSpawngroups['spawngroups']:
        if 'entries' not in sg:
            continue

        for e in sg['entries']:
            if 'classes' not in e:
                continue

            for bp in e['classes']:
                if bp not in blueprintSpecies and bp in bps:
                    blueprintSpecies[bp] = {bps[bp]: 1}
    
    # extra classes
    if 'npcRandomSpawnClassWeights' in jsonSpawngroups:
        for scw in jsonSpawngroups['npcRandomSpawnClassWeights']:
            if 'chances' not in scw or len(scw['chances']) == 0 or 'to' not in scw or 'from' not in scw or len(scw['from']) == 0 or len(scw['to']) != len(scw['chances']):
                continue

            for num, bp in enumerate(scw['to']):
                if bp in bps:
                    if scw['from'] in blueprintSpecies:
                        blueprintSpecies[scw['from']][bps[bp]] = scw['chances'][num]
                    else:
                        blueprintSpecies[scw['from']] = {bps[bp]: scw['chances'][num]}
    
    return blueprintSpecies

# Loads the file that contains a dictionary to map blueprint paths to species names.
# If the file doesn't exist, it will be created from the file values.json (ASB)
def LoadBPSpecies():
    filePath = 'BPSpeciesNames.json'
    if not os.path.isfile(filePath):
        CreateBPNameFile(filePath)
    
    if os.path.isfile(filePath):
        with open(filePath) as json_file:
            return json.load(json_file)
    
    exit('no blueprint species name file')

def CreateBPNameFile(bpFilePath):
    sourceFilePath = 'values.json'

    jo = ''
    speciesBPNames = {}
    if os.path.isfile(sourceFilePath):
        with open(sourceFilePath) as json_file:
            jo = json.load(json_file)
    
    if 'species' not in jo:
        exit('invalid ' + sourceFilePath + ' without species')
    
    for s in jo['species']:
        speciesName = s['name']
        
        if speciesName == 'Rock Elemental':
            if re.search(r'IceGolem', s['blueprintPath']):
                speciesName = 'Ice Golem'
            elif re.search(r'ChalkGolem', s['blueprintPath']):
                speciesName = 'Chalk Golem'
        
        blueprintPath = s['blueprintPath'] 
        if not blueprintPath.endswith('_C'):
            blueprintPath += '_C'

        speciesBPNames[blueprintPath] = speciesName
    
    with open(bpFilePath,'x') as json_file:
        json.dump(speciesBPNames,json_file)
