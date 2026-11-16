package com.weapon.item;

import java.util.List;

import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.SwordItem;
import net.minecraft.item.ToolMaterials;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;

/**
 * A light, fast rapier that injects venom on every hit: Poison I for 5 seconds,
 * with a splash of green particles at the wound.
 */
public class VenomRapierItem extends SwordItem {
    private static final int POISON_TICKS = 100;
    private static final int POISON_AMPLIFIER = 0;

    public VenomRapierItem(Item.Settings settings) {
        super(ToolMaterials.IRON, settings);
    }

    @Override
    public boolean postHit(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        if (!target.getWorld().isClient()) {
            target.addStatusEffect(
                new StatusEffectInstance(StatusEffects.POISON, POISON_TICKS, POISON_AMPLIFIER), attacker);

            if (target.getWorld() instanceof ServerWorld world) {
                world.spawnParticles(ParticleTypes.ITEM_SLIME,
                    target.getX(), target.getBodyY(0.6), target.getZ(),
                    10, 0.25, 0.35, 0.25, 0.02);
            }
        }
        return super.postHit(stack, target, attacker);
    }

    @Override
    public void appendTooltip(ItemStack stack, Item.TooltipContext context, List<Text> tooltip, TooltipType type) {
        tooltip.add(Text.translatable("item.weapon.venom_rapier.tooltip").formatted(Formatting.GREEN));
    }
}
