package com.weapon.item;

import com.weapon.WeaponMod;
import net.minecraft.component.type.AttributeModifierSlot;
import net.minecraft.component.type.AttributeModifiersComponent;
import net.minecraft.entity.attribute.EntityAttributeModifier;
import net.minecraft.entity.attribute.EntityAttributes;

/**
 * Builds the attack damage / speed component for the mod's swords.
 *
 * <p>Minecraft's player base attack damage is 1 and base attack speed is 4, so
 * the modifier values are offset by those amounts. This lets a weapon declare
 * the final number shown in its tooltip directly, including fractional damage
 * such as the rapier's 5.5.</p>
 */
public final class WeaponAttributes {
    private static final double PLAYER_BASE_ATTACK_DAMAGE = 1.0;
    private static final double PLAYER_BASE_ATTACK_SPEED = 4.0;

    private WeaponAttributes() {
    }

    public static AttributeModifiersComponent sword(double attackDamage, double attackSpeed) {
        return AttributeModifiersComponent.builder()
            .add(EntityAttributes.GENERIC_ATTACK_DAMAGE,
                new EntityAttributeModifier(WeaponMod.id("base_attack_damage"),
                    attackDamage - PLAYER_BASE_ATTACK_DAMAGE,
                    EntityAttributeModifier.Operation.ADD_VALUE),
                AttributeModifierSlot.MAINHAND)
            .add(EntityAttributes.GENERIC_ATTACK_SPEED,
                new EntityAttributeModifier(WeaponMod.id("base_attack_speed"),
                    attackSpeed - PLAYER_BASE_ATTACK_SPEED,
                    EntityAttributeModifier.Operation.ADD_VALUE),
                AttributeModifierSlot.MAINHAND)
            .build();
    }

    /**
     * Sword stats plus extra entity attack reach, for the long-armed sickles.
     *
     * <p>{@code reachBonus} is added to the player's base 3-block entity
     * interaction range while the weapon is held.</p>
     */
    public static AttributeModifiersComponent sickle(double attackDamage, double attackSpeed,
                                                    double reachBonus) {
        return AttributeModifiersComponent.builder()
            .add(EntityAttributes.GENERIC_ATTACK_DAMAGE,
                new EntityAttributeModifier(WeaponMod.id("base_attack_damage"),
                    attackDamage - PLAYER_BASE_ATTACK_DAMAGE,
                    EntityAttributeModifier.Operation.ADD_VALUE),
                AttributeModifierSlot.MAINHAND)
            .add(EntityAttributes.GENERIC_ATTACK_SPEED,
                new EntityAttributeModifier(WeaponMod.id("base_attack_speed"),
                    attackSpeed - PLAYER_BASE_ATTACK_SPEED,
                    EntityAttributeModifier.Operation.ADD_VALUE),
                AttributeModifierSlot.MAINHAND)
            .add(EntityAttributes.PLAYER_ENTITY_INTERACTION_RANGE,
                new EntityAttributeModifier(WeaponMod.id("sickle_reach"),
                    reachBonus,
                    EntityAttributeModifier.Operation.ADD_VALUE),
                AttributeModifierSlot.MAINHAND)
            .build();
    }
}
