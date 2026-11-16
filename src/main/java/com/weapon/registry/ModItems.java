package com.weapon.registry;

import com.weapon.WeaponMod;
import com.weapon.item.BlazeSwordItem;
import com.weapon.item.DarkTachiItem;
import com.weapon.item.DescribedSwordItem;
import com.weapon.item.GreatswordItem;
import com.weapon.item.SickleItem;
import com.weapon.item.StormGreatswordItem;
import com.weapon.item.TrainingDummyItem;
import com.weapon.item.VenomRapierItem;
import com.weapon.item.WeaponAttributes;
import com.weapon.item.WeaponMaterials;
import net.minecraft.item.Item;
import net.minecraft.item.ToolMaterials;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Formatting;
import net.minecraft.util.Rarity;

/**
 * All items of the Weapon mod.
 *
 * <p>To add a weapon: declare a constant below, register it in
 * {@link #register()}, then add it to the Weapon creative tab in
 * {@link ModItemGroups}.</p>
 */
public final class ModItems {
    /** Fast iron rapier: 5.5 damage, 2.8 attack speed. */
    public static final Item IRON_RAPIER = register("iron_rapier",
        new DescribedSwordItem(ToolMaterials.IRON, new Item.Settings()
            .rarity(Rarity.COMMON)
            .attributeModifiers(WeaponAttributes.sword(5.5, 2.8)),
            "item.weapon.iron_rapier.tooltip", Formatting.GRAY));

    /** Venom rapier: 7 damage, 2.2 speed, poison on hit. */
    public static final Item VENOM_RAPIER = register("venom_rapier",
        new VenomRapierItem(new Item.Settings()
            .rarity(Rarity.UNCOMMON)
            .attributeModifiers(WeaponAttributes.sword(7.0, 2.2))));

    /** Copper/iron/gold alloy: 8 damage, diamond durability. */
    public static final Item ALLOY_SWORD = register("alloy_sword",
        new DescribedSwordItem(WeaponMaterials.ALLOY, new Item.Settings()
            .rarity(Rarity.UNCOMMON)
            .attributeModifiers(WeaponAttributes.sword(8.0, 1.6)),
            "item.weapon.alloy_sword.tooltip", Formatting.GOLD));

    /** Blaze-forged sword: 8 damage, animated fire texture, ignites on hit. */
    public static final Item BLAZE_SWORD = register("blaze_sword",
        new BlazeSwordItem(new Item.Settings()
            .rarity(Rarity.RARE)
            .fireproof()
            .attributeModifiers(WeaponAttributes.sword(8.0, 1.6))));

    /** Iron-block greatsword: 13 damage, 0.8 attack speed, charge->lunge ability. */
    public static final Item GREATSWORD = register("greatsword",
        new GreatswordItem(new Item.Settings()
            .rarity(Rarity.RARE)
            .attributeModifiers(WeaponAttributes.sword(13.0, 0.8))));

    /** Diamond sickle: 7 damage, slow, +1.5 reach, double-sweep ability. */
    public static final Item SICKLE = register("sickle",
        new SickleItem(WeaponMaterials.SICKLE, new Item.Settings()
            .rarity(Rarity.UNCOMMON)
            .attributeModifiers(WeaponAttributes.sickle(7.0, 1.0, 1.5)),
            "item.weapon.sickle.tooltip", Formatting.AQUA, false));

    /** Obsidian/netherite hell sickle: 12 damage, slow, +1.5 reach. */
    public static final Item HELL_SICKLE = register("hell_sickle",
        new SickleItem(WeaponMaterials.HELL_SICKLE, new Item.Settings()
            .rarity(Rarity.RARE)
            .fireproof()
            .attributeModifiers(WeaponAttributes.sickle(12.0, 0.9, 1.5)),
            "item.weapon.hell_sickle.tooltip", Formatting.DARK_RED, true));

    /** Boss-drop storm greatsword: 15 damage, extended grip, triple wind blades. */
    public static final Item STORM_GREATSWORD = register("storm_greatsword",
        new StormGreatswordItem(new Item.Settings()
            .rarity(Rarity.EPIC)
            .fireproof()
            .attributeModifiers(WeaponAttributes.sword(15.0, 0.8))));

    /** Obsidian great tachi: 16 damage, blink strike that resets on a kill. */
    public static final Item DARK_TACHI = register("dark_tachi",
        new DarkTachiItem(new Item.Settings()
            .rarity(Rarity.EPIC)
            .attributeModifiers(WeaponAttributes.sword(16.0, 1.0))));

    /** Training tool: places an infinite-health dummy with damage numbers. */
    public static final Item TRAINING_DUMMY = register("training_dummy",
        new TrainingDummyItem(new Item.Settings()
            .maxCount(1)
            .rarity(Rarity.UNCOMMON)));

    private ModItems() {
    }

    /** Forces class loading, registering every constant above. */
    public static void register() {
        WeaponMod.LOGGER.debug("Weapon items registered");
    }

    private static Item register(String name, Item item) {
        return Registry.register(Registries.ITEM, WeaponMod.id(name), item);
    }
}
