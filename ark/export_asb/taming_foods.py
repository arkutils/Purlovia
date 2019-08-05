# Hard coded 2.0 for taming_multiplier (multiplied against the server's taming_multiplier)
# Unsure if this is stored in an asset or the game's binary

# DinoSettings.FoodEffectivenessMultipliers[i].FoodEffectivenessMultiplier = food_mult
# DinoSettings.FoodEffectivenessMultipliers[i].HealthEffectivenessMultiplier = health_mult
# DinoSettings.FoodEffectivenessMultipliers[i].TorpidityEffectivenessMultiplier = torpor_mult
# DinoSettings.FoodEffectivenessMultipliers[i].AffinityEffectivenessMultiplier = affinity_mult
# DinoSettings.FoodEffectivenessMultipliers[i].AffinityOverride = affinity
# DinoSettings.FoodEffectivenessMultipliers[i].StaminaEffectivenessMultiplier = stamina_mult
# DinoSettings.FoodEffectivenessMultipliers[i].FoodItemCategory = food_category
# DinoSettings.FoodEffectivenessMultipliers[i].FoodItemParent = food_parent
# DinoSettings.FoodEffectivenessMultipliers[i].UntamedFoodConsumptionPriority = food_priority

# DinoSettings.ExtraFoodEffectivenessMultipliers[i].FoodEffectivenessMultiplier = extra_food_mult
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].HealthEffectivenessMultiplier = extra_health_mult
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].TorpidityEffectivenessMultiplier = extra_torpor_mult
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].AffinityEffectivenessMultiplier = extra_affinity_mult
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].AffinityOverride = extra_affinity
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].StaminaEffectivenessMultiplier = extra_stamina_mult
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].FoodItemCategory = extra_food_category
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].FoodItemParent = extra_food_parent
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].UntamedFoodConsumptionPriority = extra_food_priority

# Item.UseItemAddCharacterStatusValues[i].BaseAmountToAdd = base_value
# Item.UseItemAddCharacterStatusValues[i].bPercentOfMaxStatusValue = is_percent_of_max
# Item.UseItemAddCharacterStatusValues[i].bPercentofCurrentStatusValue = is_percent_of_current
# Item.UseItemAddCharacterStatusValues[i].bUseItemQuality = use_quality
# Item.UseItemAddCharacterStatusValues[i].bDontRequireLessThanMaxToUse = not_require_less_than_max
# Item.UseItemAddCharacterStatusValues[i].bAddOverTime = is_over_time
# Item.UseItemAddCharacterStatusValues[i].bAddOverTimeSpeedInSeconds = is_over_time_in_secs
# Item.UseItemAddCharacterStatusValues[i].bSetValue = set_value
# Item.UseItemAddCharacterStatusValues[i].bSetAdditionalValue = set_add_value
# Item.UseItemAddCharacterStatusValues[i].bResetExistingModifierDescritionIndex = reset_existing_mod_desc_index
# Item.UseItemAddCharacterStatusValues[i].bForceUseStatOnDinos = use_stat_on_dino
# Item.UseItemAddCharacterStatusValues[i].LimitExistingModifierDescriptionToMaxAmount = limit_mod_desc_to_max
# Item.UseItemAddCharacterStatusValues[i].AddOverTimeSpeed = add_over_time_speed
# Item.UseItemAddCharacterStatusValues[i].PercentAbsoluteMaxValue = percent_absolute_max_value
# Item.UseItemAddCharacterStatusValues[i].PercentAbsoluteMinValue = percent_absolute_max_value
# Item.UseItemAddCharacterStatusValues[i].StatusValueModifierDescriptionIndex = stat_value_mod_desc_index #  2 (Used for Creatures?) || 1 (Used for Players?)
# Item.UseItemAddCharacterStatusValues[i].ItemQualityAddValueMultiplier = item_quality_add_value_multiplier
# Item.UseItemAddCharacterStatusValues[i].StatusValueType = stat_value_type #  EPrimalCharacterStatusValue::Food || EPrimalCharacterStatusValue::Torpidity || EPrimalCharacterStatusValue::Health
# Item.UseItemAddCharacterStatusValues[i].StopAtValueNearMax = stop_at_value_near_max
# Item.UseItemAddCharacterStatusValues[i].ScaleValueByCharacterDamageType = scale_value_by_character_damage_type

# for food_group in DinoSettings.FoodEffectivenessMultipliers:
#   for food in items[food_group]:
#        for food_stat in food.UseItemAddCharacterStatusValues:
#            if food_stat.StatusValueType == 'EPrimalCharacterStatusValue::Health'
#                health_value = food_group.HealthEffectivenessMultiplier * food.BaseAmountToAdd
#            elif food_stat.StatusValueType == 'EPrimalCharacterStatusValue::Stamina'
#                stamina_value = food_group.StaminaEffectivenessMultiplier * food.BaseAmountToAdd
#            elif food_stat.StatusValueType == 'EPrimalCharacterStatusValue::Food'
#                food_value = food_group.FoodEffectivenessMultiplier * food.BaseAmountToAdd
#            elif food_stat.StatusValueType == 'EPrimalCharacterStatusValue::Torpidity'
#                torpor_value = food_group.TorpidityEffectivenessMultiplier * food.BaseAmountToAdd
#
#   affinity = food_group.AffinityOverride
#   foods.add({food_name=food, affinity=affinity, food=food_value})
