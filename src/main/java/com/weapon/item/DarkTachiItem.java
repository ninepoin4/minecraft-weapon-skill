package com.weapon.item;

import java.util.List;

import net.minecraft.enchantment.EnchantmentHelper;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.projectile.ProjectileUtil;
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
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.EntityHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;
import net.minecraft.world.World;

/**
 * The obsidian great tachi "Ryūgiri".
 *
 * <p>Right-click a living target that is under the crosshair (within 20
 * blocks). The player blinks in front of it and cuts once for 1.5x attack
 * damage (24 with the base 16), setting it on fire. If the cut kills the
 * target the 8 s cooldown is cleared immediately.</p>
 */
public class DarkTachiItem extends DescribedSwordItem {
    private static final double TARGET_RANGE = 20.0;
    private static final int COOLDOWN_TICKS = 160;     // 8 s
    private static final double[] BLINK_DISTANCES = {1.8, 1.45, 1.1, 0.85};
    private static final float DAMAGE_MULTIPLIER = 1.5f;
    private static final int FIRE_SECONDS = 5;

    public DarkTachiItem(Item.Settings settings) {
        super(WeaponMaterials.DARK_TACHI, settings,
            "item.weapon.dark_tachi.tooltip", Formatting.DARK_PURPLE);
    }

    @Override
    public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
        ItemStack stack = user.getStackInHand(hand);
        if (hand != Hand.MAIN_HAND || user.getItemCooldownManager().isCoolingDown(this)) {
            return TypedActionResult.fail(stack);
        }
        if (world.isClient || !(user instanceof ServerPlayerEntity player)) {
            return TypedActionResult.consume(stack);
        }

        ServerWorld serverWorld = (ServerWorld) world;
        LivingEntity target = findTarget(serverWorld, player);
        if (target == null) {
            serverWorld.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.ENTITY_PLAYER_ATTACK_NODAMAGE, SoundCategory.PLAYERS, 0.6f, 1.2f);
            player.sendMessage(Text.translatable("item.weapon.dark_tachi.no_target"), true);
            return TypedActionResult.fail(stack);
        }

        Vec3d approach = horizontal(target.getPos().subtract(player.getPos()));
        if (approach.lengthSquared() < 1.0E-4) {
            approach = horizontal(player.getRotationVec(1.0f));
        }

        Vec3d destination = findBlinkSpot(serverWorld, player, target, approach);
        if (destination == null) {
            serverWorld.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.ENTITY_PLAYER_ATTACK_NODAMAGE, SoundCategory.PLAYERS, 0.6f, 0.8f);
            return TypedActionResult.fail(stack);
        }

        Vec3d origin = player.getPos();
        spawnBlinkBurst(serverWorld, origin);
        serverWorld.playSound(null, origin.x, origin.y, origin.z,
            SoundEvents.ENTITY_ENDERMAN_TELEPORT, SoundCategory.PLAYERS, 0.9f, 1.25f);

        double dx = target.getX() - destination.x;
        double dz = target.getZ() - destination.z;
        double horizontalDistance = Math.sqrt(dx * dx + dz * dz);
        float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
        double eyeOffset = target.getEyeY()
            - (destination.y + player.getStandingEyeHeight());
        float pitch = (float) -Math.toDegrees(Math.atan2(eyeOffset, horizontalDistance));

        player.teleport(serverWorld, destination.x, destination.y, destination.z, yaw, pitch);
        serverWorld.playSound(null, player.getX(), player.getY(), player.getZ(),
            SoundEvents.ENTITY_ENDERMAN_TELEPORT, SoundCategory.PLAYERS, 0.9f, 0.75f);
        spawnBlinkBurst(serverWorld, player.getPos());

        strike(serverWorld, player, stack, target, approach);

        player.getItemCooldownManager().set(this, COOLDOWN_TICKS);
        if (!target.isAlive()) {
            // A kill refills the blink instantly.
            player.getItemCooldownManager().remove(this);
        }
        stack.damage(1, player, EquipmentSlot.MAINHAND);
        return TypedActionResult.consume(stack);
    }

    /** The living entity currently under the player's crosshair. */
    private static LivingEntity findTarget(ServerWorld world, ServerPlayerEntity player) {
        Vec3d eye = player.getEyePos();
        Vec3d look = player.getRotationVec(1.0f);
        Vec3d end = eye.add(look.multiply(TARGET_RANGE));
        Box searchBox = player.getBoundingBox()
            .stretch(look.multiply(TARGET_RANGE)).expand(1.0);

        EntityHitResult hit = ProjectileUtil.raycast(player, eye, end, searchBox,
            entity -> entity instanceof LivingEntity living
                && living != player && living != player.getVehicle()
                && living.isAlive() && !living.isSpectator()
                && (!(living instanceof PlayerEntity other) || player.shouldDamagePlayer(other)),
            TARGET_RANGE * TARGET_RANGE);

        if (hit != null && hit.getEntity() instanceof LivingEntity living
                && player.canSee(living)) {
            BlockHitResult wall = world.raycast(new RaycastContext(eye, hit.getPos(),
                RaycastContext.ShapeType.COLLIDER, RaycastContext.FluidHandling.NONE, player));
            if (wall.getType() == HitResult.Type.MISS) {
                return living;
            }
        }
        return null;
    }

    /** A free spot just in front of the target, on the player's approach side. */
    private static Vec3d findBlinkSpot(ServerWorld world, ServerPlayerEntity player,
                                       LivingEntity target, Vec3d approach) {
        for (double distance : BLINK_DISTANCES) {
            Vec3d candidate = target.getPos().subtract(approach.multiply(distance));
            Box box = player.getBoundingBox().offset(candidate.subtract(player.getPos()));
            if (world.isBlockSpaceEmpty(player, box)) {
                return candidate;
            }
        }
        return null;
    }

    private void strike(ServerWorld world, ServerPlayerEntity player, ItemStack stack,
                        LivingEntity target, Vec3d approach) {
        player.swingHand(Hand.MAIN_HAND);

        DamageSource source = world.getDamageSources().playerAttack(player);
        float baseDamage = EnchantmentHelper.getDamage(world, stack, target, source,
            (float) player.getAttributeValue(EntityAttributes.GENERIC_ATTACK_DAMAGE));
        float damage = baseDamage * DAMAGE_MULTIPLIER;

        target.timeUntilRegen = 0;
        boolean hit = target.damage(source, damage);
        if (hit) {
            target.setOnFireFor(FIRE_SECONDS);
            EnchantmentHelper.onTargetDamaged(world, target, source, stack);
            player.addCritParticles(target);

            Vec3d push = approach.multiply(0.6);
            target.addVelocity(push.x, 0.25, push.z);
            target.velocityModified = true;

            world.spawnParticles(ParticleTypes.SWEEP_ATTACK,
                target.getX(), target.getBodyY(0.55), target.getZ(),
                2, 0.15, 0.25, 0.15, 0.0);
            world.spawnParticles(ParticleTypes.SOUL_FIRE_FLAME,
                target.getX(), target.getBodyY(0.5), target.getZ(),
                18, 0.35, 0.5, 0.35, 0.06);
            world.spawnParticles(ParticleTypes.CRIT,
                target.getX(), target.getBodyY(0.6), target.getZ(),
                14, 0.3, 0.4, 0.3, 0.2);
            world.playSound(null, target.getX(), target.getY(), target.getZ(),
                SoundEvents.ENTITY_PLAYER_ATTACK_CRIT, SoundCategory.PLAYERS, 1.0f, 0.85f);

            // A kill refills the blink instantly.
            if (!target.isAlive()) {
                world.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.ENTITY_ENDER_DRAGON_GROWL, SoundCategory.PLAYERS, 0.7f, 1.15f);
                world.spawnParticles(ParticleTypes.PORTAL,
                    player.getX(), player.getBodyY(0.6), player.getZ(),
                    40, 0.8, 0.9, 0.8, 0.35);
            }
        }
    }

    private static void spawnBlinkBurst(ServerWorld world, Vec3d pos) {
        for (int i = 0; i < 20; i++) {
            double angle = Math.PI * 2.0 * i / 20.0;
            double radius = 0.35 + (i % 4) * 0.18;
            world.spawnParticles(ParticleTypes.PORTAL,
                pos.x + Math.cos(angle) * radius, pos.y + 0.5 + (i % 5) * 0.28,
                pos.z + Math.sin(angle) * radius, 2, 0.06, 0.06, 0.06, 0.12);
            if (i % 3 == 0) {
                world.spawnParticles(ParticleTypes.SOUL_FIRE_FLAME,
                    pos.x + Math.cos(angle) * radius, pos.y + 0.7,
                    pos.z + Math.sin(angle) * radius, 1, 0.05, 0.1, 0.05, 0.01);
            }
        }
        world.spawnParticles(ParticleTypes.SMOKE, pos.x, pos.y + 1.0, pos.z,
            10, 0.3, 0.4, 0.3, 0.02);
    }

    private static Vec3d horizontal(Vec3d vector) {
        Vec3d flat = new Vec3d(vector.x, 0.0, vector.z);
        return flat.lengthSquared() < 1.0E-6 ? Vec3d.ZERO : flat.normalize();
    }

    @Override
    public void appendTooltip(ItemStack stack, Item.TooltipContext context,
                              List<Text> tooltip, TooltipType type) {
        super.appendTooltip(stack, context, tooltip, type);
        tooltip.add(Text.translatable("item.weapon.dark_tachi.ability")
            .formatted(Formatting.DARK_PURPLE));
    }
}
