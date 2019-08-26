KNOWN_KLASS_NAMES = [
    # NPC spawns
    'NPCZoneManager',
    'NPCZoneManagerBlueprint_Cave_C',
    'NPCZoneManagerBlueprint_Land_C',
    'NPCZoneManagerBlueprint_Water_C',
    # Biomes
    'BiomeZoneVolume',
    # Supply Drops
    'SupplyCrateSpawningVolume',
    # Nests and Veins
    'CustomActorList', # Nests of Wyverns, Deinonychus
    'WaterVein_Base_BP_C',
    'OilVein_Base_BP_C',
    'OilVein_2_BP_C'
]

ACTOR_FIELD_MAP = {
    '/Game/ScorchedEarth/Structures/OilPump/OilVein_Base_BP.OilVein_Base_BP_C': 'oil_veins',
    '/Game/ScorchedEarth/Structures/WaterWell/WaterVein_Base_BP.WaterVein_Base_BP_C': 'water_veins',
}

ACTOR_LIST_TAG_FIELD_MAP = {
    'DragonNestSpawns': 'wyvern_nests',
    'IceNestSpawns': 'ice_wyvern_nests',
    'DrakeNestSpawns': 'drake_nests',
    'DeinonychusNestSpawns': 'deinonychus_nests',
    'AB_DeinonychusNestSpawns': 'deinonychus_nests'
}
