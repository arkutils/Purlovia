#%% Setup
from interactive_utils import *

import json
import os
import re
from collections import defaultdict, deque
from typing import Generator

import networkx as nx

from automate.ark import ArkSteamManager
from ark.asset import findDependencies, findSubComponents, findComponentExports, findParentPackage

#%% Create loader
arkman = ArkSteamManager(skipInstall=True)
loader = arkman.createLoader()


#%% Utility functions
def loadAssetsFromDir(assetpath, include_related=False):
    '''Load all assets from the given directory, optionally loading all of their parent and sub-component assets.'''
    results = set()
    for assetname in loader.find_assetnames('.*', assetpath):
        print(f'Loading {assetname}')

        try:
            asset = loader[assetname]
        except Exception as ex:
            # Skip unloadable
            print(f'(skipping due to exception: {ex})')
            continue

        results.add(assetname)

        if include_related:
            loadRelatedContent(asset)

    return list(results)


def loadRelatedContent(asset):
    '''Load all parent classes and referenced component types.'''
    for subassetname in findDependencies(asset):
        if subassetname in asset.loader.cache:
            continue

        if not subassetname.startswith('/Game'):
            continue

        print(f'Loading related {subassetname}')
        subasset = asset.loader[subassetname]
        loadRelatedContent(subasset)


def selectAssetsOfType(assetnames, basetype) -> Generator[str, None, None]:
    '''Select only assets that have a parent (or parent of parent, etc) of the given type.'''
    for assetname in assetnames:
        if isAssetOfType(assetname, basetype):
            yield assetname


def isAssetOfType(assetname, basetype):
    '''Checks up the inheritance chain of an asset to see if it inherits from `basetype`.'''

    if assetname == basetype:
        return True

    if assetname.startswith('/Script'):
        return False

    for export in findComponentExports(loader[assetname]):
        parentName = findParentPackage(export)
        if parentName == basetype or isAssetOfType(parentName, basepath):
            return True

    return False


def getAssetBase(assetname):
    '''Get the top-most Ark-related package in the inheritance chain.'''
    if assetname.startswith('/Script'):
        return None

    for export in findComponentExports(loader[assetname]):
        parentName = findParentPackage(export)


def showAllParents(assetnames):
    for assetname in assetnames:
        print(assetname)
        showParents(assetname, indent=1)


def showParents(assetname, indent=0):
    if assetname.startswith('/Script'):
        return

    for export in findComponentExports(loader[assetname]):
        parentName = findParentPackage(export)
        print(f'{"  "*indent}{parentName}')
        showParents(parentName, indent=indent + 1)


#%% Choose top search path (bigger == slower)
# basepath = '/Game/PrimalEarth/Dinos'
basepath = '/Game/Mods/ClassicFlyers'
print(f'Base path: {basepath}')

#%% Load everything
assetnames = loadAssetsFromDir(basepath, include_related=True)
print('\nLoad complete')

#%% Analyse stuff
species = assetnames
# species = list(selectAssetsOfType(assetnames, '/Game/PrimalEarth/CoreBlueprints/Dino_Character_BP'))
# print('\nFound species:')
# pprint(species)

showAllParents(species)

#%%


#%% Graph experiments
def generateGraph(assetnames, excludeRes=[]):
    graph = nx.DiGraph()

    queue = deque()
    queue.extend(assetnames)
    done = list()

    while queue:
        assetname = queue.popleft()
        if assetname in done:
            continue
        print(assetname)

        asset = loader[assetname]

        if any(re.match(pattern, assetname, re.RegexFlag.IGNORECASE) for pattern in excludeRes):
            return

        name = shortenAssetName(assetname)
        graph.add_node(name, assetname=assetname, label=name)

        # Inheritance
        for export in findComponentExports(asset):
            parentAssetname = findParentPackage(export.klass.value)
            print('  inheritance: ' + parentAssetname)
            if not parentAssetname.startswith('/Game'):
                continue
            parentShortname = shortenAssetName(parentAssetname)
            graph.add_edge(parentShortname, name, type='inheritance')
            queue.append(parentAssetname)

        # Components
        for export in findSubComponents(asset):
            cmpAssetname = findParentPackage(export.klass.value)
            print('  component: ' + cmpAssetname)
            if not cmpAssetname.startswith('/Game'):
                continue
            cmpShortname = shortenAssetName(cmpAssetname)
            graph.add_edge(cmpShortname, name, type='component')
            queue.append(cmpAssetname)

        done.append(assetname)

    return graph


def shortenAssetName(name):
    name = re.sub(r'/Game/Mods/([^/]+)/', r'\1/', name)
    name = name.replace('ClassicFlyers', 'CF')
    name = name.replace('DinoCharacterStatusComponent', 'DCSC')
    name = name.replace('Character', 'Chr')
    name = name.replace('/Game/', '')
    return name


def createConnectedSubgraph(g, nodename):
    nodes = set()
    nodes.add(nodename)


print('\nGraph generation:')
g = generateGraph(assetnames)

#%% Select anything that inherits from the main Character asset
target = 'PrimalEarth/CoreBlueprints/Dino_Chr_BP'
chr_subgraph = g.subgraph([n for n in nx.dfs_tree(g, target)])

# Show if each asset has a sub-component that's a DCSC
print('\nSpecies candidates:')
for node in sorted(chr_subgraph.nodes):
    if any(True for src, _, data in g.in_edges([node], data=True) if data['type'] == 'component' and 'DCSC' in src):
        print('+' + node)
    else:
        print('-' + node)

# Actually need to find everything that inherits from anything that has a parent of base Chr and has a DCSC

#%% Draw graph using matplotlib
# import matplotlib.pyplot as plt
# nx.draw(chr_subgraph)

#%% Output graph using pydot
import networkx.drawing.nx_pydot as nx_pydot
nx_pydot.write_dot(chr_subgraph, 'output/cf-chrs.dot')

#%%
