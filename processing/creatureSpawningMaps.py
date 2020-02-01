# Creates an svg-file with spawning regions of a species colored depending on the rarity

import json
import re
import os
import math
import creatureSpawningClasses
import creatureSpawningExtractSpecies

def main():
	#modName = 'Primal_Fear'
	modName = 'official'
	mapName = 'TheIslandSubMaps'
	dataPath = 'MapExport\\'
		
	spawns = ''
	with open(dataPath + mapName + '/npc_spawns.json') as spawnsJson_file:
		spawns = json.load(spawnsJson_file)
	
	spawngroups = ''
	with open(dataPath + 'spawngroups-core.json') as sgJson_file:
		spawngroups = json.load(sgJson_file)
	
	if 'spawns' not in spawns or 'spawngroups' not in spawngroups:
		exit('not enough data')
    
	# default values
	mapSize = 300
	# coordinates of map-border
	#borderL = 7.2
	#borderT = 7.2
	#borderR = 92.8
	#borderB = 92.8
	borderL = 0
	borderT = 0
	borderR = 100
	borderB = 100
	
	# calculated values
	coordsW = borderR - borderL
	coordsH = borderB - borderT
	pointRadius = mapSize // 150
	if pointRadius < 2:
		pointRadius = 2
	
	# create ouput directory
	if not os.path.isdir('./output'):
		try:
			os.mkdir('./output')
		except:
			exit('path output' + 'could not be created')
		
	if not os.path.isdir('./output' + '\\' + modName):
		try:
			os.mkdir('./output' + '\\' + modName)
		except:
			exit('path output' + '\\' + modName + 'could not be created')
	
	blueprintSpecies = creatureSpawningExtractSpecies.ExtractSpecies(spawngroups)

	if len(blueprintSpecies) == 0:
		exit('no blueprintspecies. (is there a file that contains the blueprints?)')
	
	for bp in blueprintSpecies:
		for speciesName in blueprintSpecies[bp]:
			CreateSvgFile(spawns, spawngroups, mapSize, modName, mapName, borderL, borderT, coordsW, coordsH, pointRadius, bp, speciesName, blueprintSpecies[bp][speciesName])
		

def CreateSvgFile(spawns, spawngroups, mapSize, modName, mapName, borderL, borderT, coordsW, coordsH, pointRadius, bp, speciesName, spawningModifier):
	alwaysUntameable = re.match(r'Alpha ', speciesName) is not None
	mapSizeStr = str(mapSize)
	svgOutput = ('<svg xmlns="http://www.w3.org/2000/svg" '
				'width="' + mapSizeStr + '" height="' + mapSizeStr + '" viewBox="0 0 ' + mapSizeStr + ' ' + mapSizeStr + '" class="creatureMap" style="position:absolute;">\n'
				'<defs>\n  <filter id="blur" x="-30%" y="-30%" width="160%" height="160%">\n'
				'	<feGaussianBlur stdDeviation="' + str(round(mapSize / 100)) + '" />\n</filter>'
				'\n<pattern id="pattern-untameable" width="10" height="10" patternTransform="rotate(135)" patternUnits="userSpaceOnUse">\n'
				'<rect width="4" height="10" fill="black"></rect>\n</pattern>'
				'<filter id="groupStroke">'
				'<feFlood result="outsideColor" flood-color="black"/>'
				'<feMorphology in="SourceAlpha" operator="dilate" radius="2"/>'
				'<feComposite result="strokeoutline1" in="outsideColor" operator="in"/>'
				'<feComposite result="strokeoutline2" in="strokeoutline1" in2="SourceAlpha" operator="out"/>'
				'<feGaussianBlur in="strokeoutline2" result="strokeblur" stdDeviation="1"/>'
				'</filter>'
				'<style>'
				'.spawningMap-very-common { fill: #0F0;}.spawningMap-common { fill: #B2FF00;}.spawningMap-uncommon { fill: #FF0;}.spawningMap-very-uncommon { fill: #FC0;}.spawningMap-rare { fill: #F60;}.spawningMap-very-rare { fill: #F00; }.spawning-map-point {stroke:black; stroke-width:1;}'
				'</style>'
				'</defs>\n')

	svgRarityRegions = []
	svgRarityPoints = []
	# the rarity is arbitrarily divided in 6 groups from very rare (0) to very common (5)
	for _ in range(6):
		svgRarityRegions.append([])
		svgRarityPoints.append([])

	spawnEntriesFrequencies = []

	# spawngroups
	for g in spawngroups['spawngroups']:
		if 'entries' not in g:
			continue
		frequency = g['maxNPCNumberMultiplier']
		entryFrequencySum = 0

		for entry in g['entries']:
			if 'classes' not in entry or len(entry['classes']) == 0:
				continue

			spawnIndices = []
			entryClassesChance = 0 # the combined chance of all entries for the current bp
			i = 0

			# calculate total weight of the spawning group
			totalWeights = 0
			if 'classChances' not in entry or len(entry['classChances']) == 0:
				totalWeights = len(entry['classes'])
			else:
				for w in entry['classChances']:
					totalWeights += w
	
			if totalWeights == 0:
				totalWeights = 1

			# check all entries for the current blueprint, some groups have multiple entries for the same blueprint
			for npcSpawn in entry['classes']:
				if npcSpawn != None and bp in npcSpawn:
					spawnIndices.append(i)
				i += 1
			
			for i in spawnIndices:
				if len(entry['classChances']) > i:
					entryClassesChance += entry['classChances'][i]
				# assume default weight of 1 if there is no specific value
				else:
					entryClassesChance += 1
			entryClassesChance *= (entry['chance'] / totalWeights)
			entryFrequencySum += entryClassesChance
		
		frequency *= entryFrequencySum * spawningModifier
		if frequency > 0:
			spawnEntriesFrequencies.append(creatureSpawningClasses.SpawnFrequency(g['blueprintPath'], frequency))
				
	# spawns
	regionSpawnsExist = False
	pointSpawnsExist = False
	for s in spawns['spawns']:
		# check if spawngroup exists for current species

		if 'minDesiredNumberOfNPC' not in s or 'locations' not in s:
			continue

		frequency = 0
		for sef in spawnEntriesFrequencies:
			if sef.path == s['spawnGroup']:
				frequency = sef.frequency
				break
		
		if frequency == 0:
			continue

		number = frequency * s['minDesiredNumberOfNPC']
		# calculate density from number of creatures and area
		creatureDensity = number / ((s['locations'][0]['end']['long'] - s['locations'][0]['start']['long']) * (s['locations'][0]['end']['lat'] - s['locations'][0]['start']['lat']))
		# this formula is arbitrarily constructed to create 5 naturally feeling groups of rarity 0..5 (very rare to very common)
		rarity = round(1.5 * (math.log(1 + 50 * creatureDensity)))
		if rarity > 5:
			rarity = 5

		if 'spawnLocations' in s:
			for region in s['spawnLocations']:
				# add small border to avoid gaps
				xStart = round((region['start']['long'] - borderL) * mapSize / coordsW) - 3
				xEnd = round((region['end']['long'] - borderL) * mapSize / coordsW) + 3
				yStart = round((region['start']['lat'] - borderT) * mapSize / coordsH) - 3
				yEnd = round((region['end']['lat'] - borderT) * mapSize / coordsH) + 3
			
				svgRarityRegions[rarity].append(creatureSpawningClasses.SpawnRectangle(xStart, yStart, xEnd, yEnd, ('Cave' in s['spawnGroup'] or 'UnderwaterGround' in s['spawnGroup']), (alwaysUntameable or s['forceUntameable'])))
				regionSpawnsExist = True

		if 'spawnPoints' in s:
			for point in s['spawnPoints']:
				# add small border to avoid gaps
				x = round((point['long'] - borderL) * mapSize / coordsW)
				y = round((point['lat'] - borderT) * mapSize / coordsW)
				if x < 0:
					x = 0
				if x > mapSize:
					x = mapSize
				if y < 0:
					y = 0
				if y > mapSize:
					y = mapSize
			
				svgRarityPoints[rarity].append(creatureSpawningClasses.SpawnPoint(x, y, ('Cave' in s['spawnGroup'] or 'UnderwaterGround' in s['spawnGroup']), (alwaysUntameable or s['forceUntameable'])))
				pointSpawnsExist = True

	# these css class names are also defined on the ARK-wiki at https://ark.gamepedia.com/MediaWiki:Common.css and thus shouldn't be renamed here.
	cssRarityClasses = ['spawningMap-very-rare',
						'spawningMap-rare',
						'spawningMap-very-uncommon',
						'spawningMap-uncommon',
						'spawningMap-common',
						'spawningMap-very-common']

	untameableRegionsExist = False
	caveRegionsExist = False

	# spawnRegions
	if regionSpawnsExist:
		svgOutput += '<g filter="url(#blur)" opacity="0.7">'
		cssRarity = -1
		for rarityRegions in svgRarityRegions:
			cssRarity += 1
			if len(rarityRegions) == 0:
				continue
			svgOutput += '<g class="' + cssRarityClasses[cssRarity] + '">'
			for region in rarityRegions:
				svgOutput += '<rect x="' + str(region.x) + '" y="' + str(region.y) + '" width="' + str(region.w) + '" height="' + str(region.h) + '" />'
				if region.untameable:
					untameableRegionsExist = True
				if region.cave:
					caveRegionsExist = True

			svgOutput += '</g>'
		svgOutput += '</g>\n'

	# spawnPoints
	if pointSpawnsExist:
		svgOutput += '<g class="spawning-map-point" opacity="0.8">'
		cssRarity = -1
		for rarityPoints in svgRarityPoints:
			cssRarity += 1
			if len(rarityPoints) == 0:
				continue
			svgOutput += '<g class="' + cssRarityClasses[cssRarity] + '">'
			for point in rarityPoints:
				svgOutput += '<circle cx="' + str(point.x) + '" cy="' + str(point.y) + '" r="' + str(2 * pointRadius) + '" />'
				if point.untameable:
					untameableRegionsExist = True
				if point.cave:
					caveRegionsExist = True

			svgOutput += '</g>'
		svgOutput += '</g>\n'

	# untameable stripes (without blurfilter)
	if untameableRegionsExist:
		svgOutput += '\n<g fill="url(#pattern-untameable)" opacity="0.3">'
		for rarityRegions in svgRarityRegions:
			for region in rarityRegions:
				if region.untameable:
					svgOutput += '<rect x="' + str(region.x) + '" y="' + str(region.y) + '" width="' + str(region.w) + '" height="' + str(region.h) + '"/>'
		svgOutput += '</g>'

	# cave outlines
	if caveRegionsExist:
		caveOutlineRegions = ''
		for rarityRegions in svgRarityRegions:
			for region in rarityRegions:
				if region.cave:
					caveOutlineRegions += '<rect x="' + str(region.x) + '" y="' + str(region.y) + '" width="' + str(region.w) + '" height="' + str(region.h) + '"/>'
		if len(caveOutlineRegions) > 0:
			svgOutput += '\n<g filter="url(#groupStroke)" opacity="0.8">' + caveOutlineRegions + '</g>'

	# end of svg
	svgOutput += '</svg>'

	if not regionSpawnsExist and not pointSpawnsExist:
		print('no spawns for ' + speciesName)
		return

	# write output
	fileName = 'output\\' + modName + '\\Spawning_' + speciesName + '_' + mapName + '.svg'
	f = open(fileName,'w')
	f.write(svgOutput)
	f.close

	print('file created at ' + fileName)

main()