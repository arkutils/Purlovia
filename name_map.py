# Not used yet... fill more in for me...

ark_names_map = '''
    MaxStatusValues = B
    TamingMaxStatMultipliers = Tm
    TamingMaxStatAdditions = Ta
    AmountMaxGainedPerLevelUpValue = Iw
'''
ark_names_map = [tuple(field.strip() for field in line.split('=')) for line in ark_names_map.split('\n') if line.strip()]
