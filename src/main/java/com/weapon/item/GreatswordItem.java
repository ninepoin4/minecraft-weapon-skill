package com.weapon.item;

import java.util.List;

import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.util.UseAction;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

/**
 * The iron-block greatsword.
 *
 * <p>Right-click and hold for 1s: the player slows to a guard stance while the
 * blade gathers sparks. At full charge the player lunges two blocks forward,
 * hitting everything up to four blocks ahead for 1.5x the greatsword's attack
 * damage.</p>
 */
public class GreatswordItem extends DescribedSwordItem {
    private static final int CHARGE_TICKS = 20;
    private static final int COOLDOWN_TICKS = 60;
    private static final int SLOWNESS_DURATION_TICKS = 5;
    private static final int SLOWNESS_AMPLIFIER = 0;
    private static final double DASH_DISTANCE = 2.0;
    private static final double THRUST_RANGE = 4.0;
    private static final double THRUST_WIDTH = 1.0;
    private static final double DAMAGE_MULTIPLIER = 1.5;

    public GreatswordItem(Item.Settings settings) {
        super(WeaponMaterials.GREATSWORD, settings,
            "item.weapon.greatsword.tooltip", Formatting.DARK_GRAY);
    }

    @Override
    public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
        ItemStack stack = user.getStackInHand(hand);
        if (hand != Hand.MAIN_HAND || user.getItemCooldownManager().isCoolingDown(this)) {
            return TypedActionResult.fail(stack);
        }

        user.setCurrentHand(hand);
        if (!world.isClient) {
            world.playSound(null, user.getX(), user.getY(), user.getZ(),
                SoundEvents.BLOCK_RESPAWN_ANCHOR_CHARGE, SoundCategory.PLAYERS, 0.8f, 0.75f);
        }
        return TypedActionResult.consume(stack);
    }

    @Override
    public int getMaxUseTime(ItemStack stack, LivingEntity user) {
        return CHARGE_TICKS;
    }

    @Override
    public UseAction getUseAction(ItemStack stack) {
        // A guard stance reads as "winding up" and already slows movement.
        return UseAction.BLOCK;
    }

    @Override
    public void usageTick(World world, LivingEntity user, ItemStack stack, int remainingUseTicks) {
        if (!(world instanceof ServerWorld serverWorld) || !(user instanceof ServerPlayerEntity player)) {
            return;
        }

        int elapsed = CHARGE_TICKS - remainingUseTicks;
        player.addStatusEffect(new StatusEffectInstance(
            StatusEffects.SLOWNESS, SLOWNESS_DURATION_TICKS, SLOWNESS_AMPLIFIER,
            false, false, false), player);

        Vec3d hand = player.getEyePos()
            .add(player.getRotationVec(1.0f).multiply(0.9))
            .add(0.0, -0.35, 0.0);
        serverWorld.spawnParticles(ParticleTypes.CRIT, hand.x, hand.y, hand.z,
            3, 0.12, 0.12, 0.12, 0.04);

        if (elapsed > 0 && elapsed % 4 == 0) {
            serverWorld.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.BLOCK_AMETHYST_BLOCK_CHIME, SoundCategory.PLAYERS,
                0.5f, 0.7f + 0.04f * elapsed);
        }
    }

    @Override
    public ItemStack finishUsing(ItemStack stack, World world, LivingEntity user) {
        // Called server-side when the 1s use timer runs out. Releasing early
        // goes through onStoppedUsing and therefore never reaches this method.
        if (!world.isClient && user instanceof ServerPlayerEntity player) {
            ServerWorld serverWorld = (ServerWorld) world;
            Vec3d forward = horizontalFacing(player);

            // Drop the charge pose first so the vanilla attack swing is visible.
            player.stopUsingItem();
            player.swingHand(Hand.MAIN_HAND);

            dash(serverWorld, player, forward);
            strike(serverWorld, player, forward);

            player.getItemCooldownManager().set(this, COOLDOWN_TICKS);
            stack.damage(1, player, EquipmentSlot.MAINHAND);
        }
        return stack;
    }

    private static Vec3d horizontalFacing(PlayerEntity player) {
        Vec3d look = player.getRotationVec(1.0f);
        Vec3d flat = new Vec3d(look.x, 0.0, look.z);
        if (flat.lengthSquared() < 1.0E-6) {
            Direction facing = player.getHorizontalFacing();
            flat = new Vec3d(facing.getOffsetX(), 0.0, facing.getOffsetZ());
        }
        return flat.normalize();
    }

    /** Lunges up to two blocks, stopping at walls and stepping up one block. */
    private static void dash(ServerWorld world, ServerPlayerEntity player, Vec3d forward) {
        if (player.hasVehicle()) {
            return;
        }

        Vec3d start = player.getPos();
        double moved = freeDistance(world, player, forward, 0.0);
        double y = start.y;

        if (moved < DASH_DISTANCE) {
            // Try the whole lunge one block higher (stairs, low ledges).
            if (freeDistance(world, player, forward, 1.0) >= DASH_DISTANCE) {
                moved = DASH_DISTANCE;
                y += 1.0;
            }
        }
        if (moved <= 0.0) {
            return;
        }

        double dx = forward.x * moved;
        double dz = forward.z * moved;

        // Dust trail along the actual dash path.
        for (double d = 0.35; d <= moved + 1.0E-6; d += 0.35) {
            world.spawnParticles(ParticleTypes.CLOUD,
                start.x + forward.x * d, start.y + 0.25, start.z + forward.z * d,
                4, 0.16, 0.1, 0.16, 0.01);
        }
        world.spawnParticles(ParticleTypes.SWEEP_ATTACK,
            start.x + forward.x * moved, start.y + 0.8, start.z + forward.z * moved,
            1, 0.0, 0.0, 0.0, 0.0);
        world.playSound(null, start.x, start.y, start.z,
            SoundEvents.ENTITY_RAVAGER_ATTACK, SoundCategory.PLAYERS, 0.9f, 0.85f);

        player.requestTeleport(start.x + dx, y, start.z + dz);
    }

    /** Furthest free distance up to the dash length at the given Y offset. */
    private static double freeDistance(ServerWorld world, ServerPlayerEntity player,
                                       Vec3d forward, double yOffset) {
        double moved = 0.0;
        for (double step = 0.5; step <= DASH_DISTANCE + 1.0E-6; step += 0.5) {
            Box box = player.getBoundingBox().offset(forward.x * step, yOffset, forward.z * step);
            if (!world.isBlockSpaceEmpty(player, box)) {
                break;
            }
            moved = step;
        }
        return moved;
    }

    /** Hits every living entity in a 4-block thrust corridor for 1.5x damage. */
    private static void strike(ServerWorld world, ServerPlayerEntity player, Vec3d forward) {
        float damage = (float) (player.getAttributeValue(EntityAttributes.GENERIC_ATTACK_DAMAGE)
            * DAMAGE_MULTIPLIER);

        Vec3d start = player.getPos();
        Vec3d end = start.add(forward.multiply(THRUST_RANGE));
        Box searchBox = new Box(
            Math.min(start.x, end.x) - 1.5, start.y - 1.0, Math.min(start.z, end.z) - 1.5,
            Math.max(start.x, end.x) + 1.5, start.y + 2.5, Math.max(start.z, end.z) + 1.5);

        // Visible thrust trail along the full 4-block reach.
        Vec3d eye = player.getEyePos();
        for (double d = 0.8; d <= THRUST_RANGE; d += 0.55) {
            Vec3d point = eye.add(forward.multiply(d)).add(0.0, -0.3, 0.0);
            world.spawnParticles(ParticleTypes.CRIT,
                point.x, point.y, point.z, 1, 0.05, 0.05, 0.05, 0.0);
        }
        world.spawnParticles(ParticleTypes.SWEEP_ATTACK,
            eye.x + forward.x * THRUST_RANGE, eye.y - 0.45, eye.z + forward.z * THRUST_RANGE,
            1, 0.0, 0.0, 0.0, 0.0);

        boolean hit = false;
        for (LivingEntity target : world.getEntitiesByClass(LivingEntity.class, searchBox,
                entity -> entity != player && entity != player.getVehicle()
                    && entity.isAlive() && !entity.isSpectator())) {
            if (target instanceof PlayerEntity other && !player.shouldDamagePlayer(other)) {
                continue;
            }

            Vec3d offset = target.getPos().subtract(start);
            double forwardDistance = offset.dotProduct(forward);
            double sideDistance = Math.abs(offset.x * forward.z - offset.z * forward.x);
            if (forwardDistance < -0.5 || forwardDistance > THRUST_RANGE
                || sideDistance > THRUST_WIDTH + target.getWidth() * 0.5) {
                continue;
            }
            if (!player.canSee(target)) {
                continue;
            }

            if (target.damage(world.getDamageSources().playerAttack(player), damage)) {
                hit = true;
                Vec3d push = forward.multiply(0.7);
                target.addVelocity(push.x, 0.35, push.z);
                target.velocityModified = true;
                world.spawnParticles(ParticleTypes.SWEEP_ATTACK,
                    target.getX(), target.getBodyY(0.5), target.getZ(), 1, 0.0, 0.0, 0.0, 0.0);
            }
        }

        if (hit) {
            world.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.ENTITY_PLAYER_ATTACK_CRIT, SoundCategory.PLAYERS, 1.0f, 0.9f);
        }
    }

    @Override
    public void appendTooltip(ItemStack stack, Item.TooltipContext context, List<Text> tooltip, TooltipType type) {
        super.appendTooltip(stack, context, tooltip, type);
        tooltip.add(Text.translatable("item.weapon.greatsword.ability").formatted(Formatting.GRAY));
    }
}
