package com.weapon.registry;

import com.weapon.WeaponMod;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.minecraft.item.ItemGroup;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.text.Text;

/**
 * The mod's own creative-inventory tab. Every weapon is added to
 * {@link #WEAPONS} here, keeping the mod's items in one place instead of
 * scattering them across vanilla tabs.
 */
public final class ModItemGroups {
    public static final RegistryKey<ItemGroup> WEAPONS =
        RegistryKey.of(RegistryKeys.ITEM_GROUP, WeaponMod.id("weapons"));

    private ModItemGroups() {
    }

    public static void register() {
        Registry.register(Registries.ITEM_GROUP, WEAPONS, FabricItemGroup.builder()
            .displayName(Text.translatable("itemGroup.weapon.weapons"))
            .icon(() -> new ItemStack(ModItems.VENOM_RAPIER))
            .entries((context, entries) -> {
                entries.add(ModItems.IRON_RAPIER);
                entries.add(ModItems.VENOM_RAPIER);
                entries.add(ModItems.ALLOY_SWORD);
                entries.add(ModItems.BLAZE_SWORD);
                entries.add(ModItems.GREATSWORD);
                entries.add(ModItems.SICKLE);
                entries.add(ModItems.HELL_SICKLE);
                entries.add(ModItems.STORM_GREATSWORD);
                entries.add(ModItems.DARK_TACHI);
                entries.add(ModItems.TRAINING_DUMMY);
            })
            .build());
    }
}
