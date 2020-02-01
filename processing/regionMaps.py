# Creates an svg-file with regions that contain links to the according region-page (used on the ARK: Survival evolved Wiki)

import json
import re
import math
import html
import regionMapsFunctions as rmf
from urllib.parse import quote

#mapName = 'Valguero'
mapName = 'TheIslandSubMaps'

biomes = ''
with open('MapExport/' + mapName + '/biomes.json') as biomesJson_file:
    biomes = json.load(biomesJson_file)

worldSettings = ''
with open('MapExport/' + mapName + '/world_settings.json') as worldSettingsJson_file:
    worldSettingsObject = json.load(worldSettingsJson_file)
    worldSettings = worldSettingsObject['worldSettings']

if 'biomes' not in biomes:
    exit('not enough data')

# default values
mapSize = 1024
modSuffix = ' (' + mapName + ')'

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

mapSizeStr = str(mapSize)

svgOutput = ('<svg width="1024" height="1024" viewBox="0 0 1024 1024" style="position: absolute; width:100%; height:100%;">'
            '<defs>'
            '  <filter id="blur" x="-30%" y="-30%" width="160%" height="160%">'
            '    <feColorMatrix type="matrix" values="1 0 0 1 0, 0 1 0 0 0, 0 0 1 0 0, 0 0 0 0.7 0"/>'
            '    <feGaussianBlur stdDeviation="10" />'
            '  </filter>'
            '</defs>\n')

# remove regions without regions or if the name is only \?+, namefixes
regexInvalidBiome = re.compile(r'^\?+$')
validBiomes = []

for b in biomes['biomes']:
    if 'boxes' not in b or len(b['boxes']) == 0 or len(b['name']) == 0 or regexInvalidBiome.search(b['name']):
        continue
    
    if b['name'] == 'Underwater':
        b['priority'] = -1
        # remove underwater in the middle of the map
        validBoxes = []
        for box in b['boxes']:
            if not ((box['start']['x'] > -300000 and box['end']['x'] < 300000) and (box['start']['y'] > -300000 and box['end']['y'] < 300000)):
                validBoxes.append(box)
        b['boxes'] = validBoxes

    elif b['name'] == 'Deep Ocean':
        b['priority'] = -2
    else:
        b['name'] = rmf.fixRegionName(b['name'])

    validBiomes.append(b)

biomesLen = len(validBiomes)
i = 0
# combine regions with the same name
while i < biomesLen:
    j = i + 1
    while j < biomesLen:
        if validBiomes[i]['name'] == validBiomes[j]['name']:
            validBiomes[i]['boxes'] = validBiomes[i]['boxes'] + validBiomes[j]['boxes']
            del(validBiomes[j])
            biomesLen = biomesLen - 1
        else:
            j = j + 1
    i = i + 1

# sorting
validBiomes.sort(key=lambda b: b['priority'], reverse=False)

textX = mapSize / 2
textY = 60

# create svg
for b in validBiomes:
    svgOutput += '<a href="' + quote(b['name'] + modSuffix, safe="()") + '" class="svgRegion">\n <g filter="url(#blur)">\n'
    for box in b['boxes']:
        # rectangle-coords
        xStart = round(rmf.mapTrans(rmf.coordTrans(box['start']['x'], worldSettings['latShift'], worldSettings['latMulti']), borderL, coordsW, mapSize))
        xEnd = round(rmf.mapTrans(rmf.coordTrans(box['end']['x'], worldSettings['latShift'], worldSettings['latMulti']), borderL, coordsW, mapSize))
        yStart = round(rmf.mapTrans(rmf.coordTrans(box['start']['y'], worldSettings['longShift'], worldSettings['longMulti']), borderT, coordsH, mapSize))
        yEnd = round(rmf.mapTrans(rmf.coordTrans(box['end']['y'], worldSettings['longShift'], worldSettings['longMulti']), borderT, coordsH, mapSize))
        if xStart < 0:
            xStart = 0
        if xEnd > mapSize:
            xEnd = mapSize
        if yStart < 0:
            yStart = 0
        if yEnd > mapSize:
            yEnd = mapSize

        svgOutput += '  <rect x="' + str(xStart) + '" y="' + str(yStart) + '" width="' + str(xEnd - xStart) + '" height="' + str(yEnd - yStart) + '" />\n'

    svgOutput += ' </g>\n <text x="' + str(round(textX)) + '" y="' + str(round(textY)) + '">' + html.escape(b['name'], quote=True) + '</text>\n</a>\n'

# end of svg
svgOutput += '</svg>'

folder = 'output/maps/'
# write output
fileName = folder + 'RegionMap_' + mapName + '.svg'
f = open(fileName, 'w')
f.write(svgOutput)
f.close
print('svg file created at ' + fileName)

# html preview
imgSrc = 'maps/' + mapName + '_Topographic_Map.jpg'
htmlStart = ('<!DOCTYPE html>\n<html lang="de">\n<body>\n<div style="position: relative; width: ' + str(mapSize) + 'px; height: ' + str(mapSize) + 'px;">\n\n<style>\n@namespace url(http://www.w3.org/2000/svg);\na:hover, a:focus { text-decoration: none; }\n.svgRegion { fill:transparent; }\n.svgRegion:hover g, .svgRegion.svgRegionHighlight g { fill: #f00; }\n.svgRegion text {\n opacity: 0;\n font-family: arial;\n font-size: 50px;\n font-weight: bold;\n stroke: white;\n stroke-width: 2px;\n fill: black;\n pointer-events: none;\n text-anchor: middle;\n}\n.svgRegion:hover text { opacity: 1; }\n</style>\n'
             '<img src="' + imgSrc + '" style="position:absolute; width:100%; height:100%;"/>\n')
htmlEnd = '</div></body></html>'

fileName = folder + 'RegionMap_' + mapName + '.html'
f = open(fileName,'w')
f.write(htmlStart + svgOutput + htmlEnd)
f.close
print('file for testing created at ' + fileName)