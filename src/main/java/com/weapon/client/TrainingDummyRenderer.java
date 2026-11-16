package com.weapon.client;

import com.weapon.WeaponMod;
import com.weapon.entity.TrainingDummyEntity;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.render.entity.MobEntityRenderer;
import net.minecraft.client.render.entity.model.EntityModelLayers;
import net.minecraft.client.render.entity.model.ZombieEntityModel;
import net.minecraft.util.Identifier;

/**
 * Reuses the vanilla zombie humanoid model (arms out) with a straw/pumpkin
 * scarecrow texture.
 */
public class TrainingDummyRenderer
    extends MobEntityRenderer<TrainingDummyEntity, ZombieEntityModel<TrainingDummyEntity>> {
    private static final Identifier TEXTURE =
        WeaponMod.id("textures/entity/training_dummy.png");

    public TrainingDummyRenderer(EntityRendererFactory.Context context) {
        super(context, new ZombieEntityModel<>(context.getPart(EntityModelLayers.ZOMBIE)), 0.5f);
    }

    @Override
    public Identifier getTexture(TrainingDummyEntity entity) {
        return TEXTURE;
    }
}
