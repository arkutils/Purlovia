from ue.asset import UAsset


# Gathers sublevels that are streamed into the persistent
# level at any point of its existence.
def gather_sublevel_names(level: UAsset):
    sublevels = []

    for export in level.exports:
        if str(export.klass.value.name) != 'TileStreamingVolume':
            continue
        properties = export.properties.as_dict()
        for level_name in properties['StreamingLevelNames'][0].values:
            level_name = str(level_name.value)

            if level_name not in sublevels:
                sublevels.append(level_name)

    return sublevels
