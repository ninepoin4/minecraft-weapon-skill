package com.weapon.item;

import net.minecraft.entity.LivingEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.Formatting;

/**
 * A blaze-forged sword: its texture is an 8-frame fire animation, and hits set
 * the target on fire for 5 seconds.
 */
public class BlazeSwordItem extends DescribedSwordItem {
    private static final int FIRE_TICKS = 100;

    public BlazeSwordItem(Item.Settings settings) {
        super(WeaponMaterials.BLAZE, settings, "item.weapon.blaze_sword.tooltip", Formatting.GOLD);
    }

    @Override
    public boolean postHit(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        if (!target.getWorld().isClient()) {
            target.setOnFireForTicks(FIRE_TICKS);

            if (target.getWorld() instanceof ServerWorld world) {
                world.spawnParticles(ParticleTypes.FLAME,
                    target.getX(), target.getBodyY(0.6), target.getZ(),
                    12, 0.3, 0.4, 0.3, 0.02);
                world.playSound(null, target.getX(), target.getY(), target.getZ(),
                    SoundEvents.ITEM_FIRECHARGE_USE, SoundCategory.PLAYERS, 0.6f, 1.3f);
            }
        }
        return super.postHit(stack, target, attacker);
    }
}
