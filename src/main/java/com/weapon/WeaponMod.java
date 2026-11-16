package com.weapon;

import com.weapon.entity.TrainingDummyVisuals;
import com.weapon.registry.ModEntities;
import com.weapon.registry.ModItemGroups;
import com.weapon.registry.ModItems;
import net.fabricmc.api.ModInitializer;
import net.minecraft.util.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Entry point for the Weapon mod.
 *
 * <p>Kept intentionally thin: everything a weapon needs lives in
 * {@link ModItems} (stats and effects) and {@link ModItemGroups} (creative tab),
 * so adding a new weapon is a one-file change.</p>
 */
public class WeaponMod implements ModInitializer {
    public static final String MOD_ID = "weapon";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    @Override
    public void onInitialize() {
        ModEntities.register();
        ModItems.register();
        ModItemGroups.register();
        TrainingDummyVisuals.init();
        LOGGER.info("Weapon mod initialized");
    }

    public static Identifier id(String path) {
        return Identifier.of(MOD_ID, path);
    }
}
