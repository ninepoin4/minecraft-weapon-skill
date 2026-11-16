package com.weapon.registry;

import com.weapon.WeaponMod;
import com.weapon.entity.TrainingDummyEntity;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricEntityTypeBuilder;
import net.minecraft.entity.EntityDimensions;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnGroup;
import net.minecraft.entity.mob.ZombieEntity;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;

public final class ModEntities {
    public static final EntityType<TrainingDummyEntity> TRAINING_DUMMY = Registry.register(
        Registries.ENTITY_TYPE,
        WeaponMod.id("training_dummy"),
        FabricEntityTypeBuilder.create(SpawnGroup.MISC, TrainingDummyEntity::new)
            .dimensions(EntityDimensions.fixed(0.6f, 1.95f))
            .build());

    private ModEntities() {
    }

    public static void register() {
        FabricDefaultAttributeRegistry.register(TRAINING_DUMMY,
            ZombieEntity.createZombieAttributes());
    }
}
