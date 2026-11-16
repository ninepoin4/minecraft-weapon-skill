package com.weapon.item;

import java.util.function.Supplier;

import net.minecraft.block.Block;
import net.minecraft.item.Items;
import net.minecraft.item.ToolMaterial;
import net.minecraft.recipe.Ingredient;
import net.minecraft.registry.tag.BlockTags;
import net.minecraft.registry.tag.TagKey;

/**
 * Custom tool materials for the mod's non-vanilla weapons.
 *
 * <p>Attack damage is set per item through
 * {@link com.weapon.item.WeaponAttributes}, so the material's attack value is
 * only a fallback for other tool components.</p>
 */
public enum WeaponMaterials implements ToolMaterial {
    /** Copper + iron + gold: diamond durability, warm alloy colour. */
    ALLOY(1561, 8.0f, 3.0f, 18, () -> Ingredient.ofItems(Items.IRON_INGOT)),
    /** Blaze rod + magma: diamond durability, fireproof in the item settings. */
    BLAZE(1561, 8.0f, 3.0f, 20, () -> Ingredient.ofItems(Items.BLAZE_ROD)),
    /** Two iron blocks + an iron sword: netherite-tier durability and weight. */
    GREATSWORD(2031, 9.0f, 4.0f, 15, () -> Ingredient.ofItems(Items.IRON_INGOT)),
    /** Diamond sickle: diamond-tier durability. */
    SICKLE(1561, 8.0f, 3.0f, 18, () -> Ingredient.ofItems(Items.DIAMOND)),
    /** Obsidian/netherite hell sickle: netherite-tier durability. */
    HELL_SICKLE(2031, 9.0f, 4.0f, 15, () -> Ingredient.ofItems(Items.NETHERITE_INGOT)),
    /** Boss-drop storm greatsword: extra durability, repaired with wind charges. */
    STORM(2500, 9.0f, 4.0f, 18, () -> Ingredient.ofItems(Items.WIND_CHARGE)),
    /** Legendary obsidian tachi: extra durability, repaired with obsidian. */
    DARK_TACHI(2500, 9.0f, 4.0f, 18, () -> Ingredient.ofItems(Items.OBSIDIAN));

    private final int durability;
    private final float miningSpeedMultiplier;
    private final float attackDamage;
    private final int enchantability;
    private final Supplier<Ingredient> repairIngredient;

    WeaponMaterials(int durability, float miningSpeedMultiplier, float attackDamage,
                    int enchantability, Supplier<Ingredient> repairIngredient) {
        this.durability = durability;
        this.miningSpeedMultiplier = miningSpeedMultiplier;
        this.attackDamage = attackDamage;
        this.enchantability = enchantability;
        this.repairIngredient = repairIngredient;
    }

    @Override
    public int getDurability() {
        return durability;
    }

    @Override
    public float getMiningSpeedMultiplier() {
        return miningSpeedMultiplier;
    }

    @Override
    public float getAttackDamage() {
        return attackDamage;
    }

    @Override
    public TagKey<Block> getInverseTag() {
        return BlockTags.INCORRECT_FOR_IRON_TOOL;
    }

    @Override
    public int getEnchantability() {
        return enchantability;
    }

    @Override
    public Ingredient getRepairIngredient() {
        return repairIngredient.get();
    }
}
