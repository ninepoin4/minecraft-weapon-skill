package com.weapon.item;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
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
 * Boss-drop storm greatsword: a slower, heavier greatsword with an extended
 * two-handed grip.
 *
 * <p>Hold right-click for two seconds. At full charge three wind blades sweep
 * out in front of the player; each blade travels up to 12 blocks and deals
 * 8 damage to everything it passes. The three waves are launched a quarter
 * second apart, so the same target can be hit three times.</p>
 */
public class StormGreatswordItem extends DescribedSwordItem {
    private static final int CHARGE_TICKS = 40;        // 2 s
    private static final int COOLDOWN_TICKS = 200;     // 10 s
    private static final int SLASH_COUNT = 3;
    private static final int SLASH_INTERVAL = 5;       // 0.25 s
    private static final float SLASH_DAMAGE = 8.0f;
    private static final double MAX_RANGE = 12.0;
    private static final double WAVE_SPEED = 2.0;
    private static final double HALF_WIDTH = 2.0;
    private static final double VERTICAL_RANGE = 3.0;
    private static final int SLOWNESS_DURATION = 5;

    /** Wind blades currently travelling forward. */
    private static final List<WindSlash> SLASHES = new ArrayList<>();

    static {
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            for (int i = SLASHES.size() - 1; i >= 0; i--) {
                if (SLASHES.get(i).tick()) {
                    SLASHES.remove(i);
                }
            }
        });
    }

    public StormGreatswordItem(Item.Settings settings) {
        super(WeaponMaterials.STORM, settings,
            "item.weapon.storm_greatsword.tooltip", Formatting.DARK_AQUA);
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
                SoundEvents.ENTITY_BREEZE_CHARGE, SoundCategory.PLAYERS, 0.9f, 0.8f);
        }
        return TypedActionResult.consume(stack);
    }

    @Override
    public int getMaxUseTime(ItemStack stack, LivingEntity user) {
        return CHARGE_TICKS;
    }

    @Override
    public UseAction getUseAction(ItemStack stack) {
        return UseAction.BLOCK;
    }

    @Override
    public void usageTick(World world, LivingEntity user, ItemStack stack, int remainingUseTicks) {
        if (!(world instanceof ServerWorld serverWorld) || !(user instanceof ServerPlayerEntity player)) {
            return;
        }

        int elapsed = CHARGE_TICKS - remainingUseTicks;
        player.addStatusEffect(new StatusEffectInstance(
            StatusEffects.SLOWNESS, SLOWNESS_DURATION, 0, false, false, false), player);

        double angle = elapsed * 0.55;
        Vec3d hand = player.getEyePos()
            .add(player.getRotationVec(1.0f).multiply(1.0))
            .add(Math.cos(angle) * 0.4, -0.25 + Math.sin(angle * 1.3) * 0.2, Math.sin(angle) * 0.4);
        serverWorld.spawnParticles(ParticleTypes.ELECTRIC_SPARK,
            hand.x, hand.y, hand.z, 3, 0.12, 0.12, 0.12, 0.05);
        serverWorld.spawnParticles(ParticleTypes.CLOUD,
            hand.x, hand.y, hand.z, 1, 0.15, 0.1, 0.15, 0.01);

        if (elapsed % 4 == 0) {
            serverWorld.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.BLOCK_AMETHYST_BLOCK_CHIME, SoundCategory.PLAYERS,
                0.6f, 0.6f + 0.05f * elapsed);
        }
        if (elapsed % 10 == 0) {
            serverWorld.spawnParticles(ParticleTypes.GUST,
                player.getX(), player.getY() + 1.0, player.getZ(),
                1, 0.4, 0.3, 0.4, 0.02);
        }
    }

    @Override
    public ItemStack finishUsing(ItemStack stack, World world, LivingEntity user) {
        // Called when the 2 s charge timer expires; releasing early cancels it.
        if (!world.isClient && user instanceof ServerPlayerEntity player) {
            cast((ServerWorld) world, player, this);
        }
        return stack;
    }

    /** Runs the full triple-wind-blade cast. */
    private static void cast(ServerWorld serverWorld, ServerPlayerEntity player, Item item) {
        Vec3d forward = horizontalFacing(player);

        player.stopUsingItem();
        player.swingHand(Hand.MAIN_HAND);

        serverWorld.playSound(null, player.getX(), player.getY(), player.getZ(),
            SoundEvents.ENTITY_WIND_CHARGE_WIND_BURST.value(),
            SoundCategory.PLAYERS, 1.2f, 0.9f);
        serverWorld.playSound(null, player.getX(), player.getY(), player.getZ(),
            SoundEvents.ENTITY_BREEZE_WIND_BURST.value(),
            SoundCategory.PLAYERS, 1.1f, 0.95f);

        // Radial gust around the caster.
        for (int i = 0; i < 24; i++) {
            double angle = Math.PI * 2.0 * i / 24.0;
            serverWorld.spawnParticles(ParticleTypes.CLOUD,
                player.getX() + Math.cos(angle) * 1.2,
                player.getY() + 0.6 + Math.sin(i) * 0.3,
                player.getZ() + Math.sin(angle) * 1.2,
                2, 0.1, 0.1, 0.1, 0.03);
            serverWorld.spawnParticles(ParticleTypes.ELECTRIC_SPARK,
                player.getX() + Math.cos(angle) * 0.8,
                player.getY() + 1.0,
                player.getZ() + Math.sin(angle) * 0.8,
                1, 0.05, 0.05, 0.05, 0.05);
        }

        Vec3d origin = player.getPos();
        for (int i = 0; i < SLASH_COUNT; i++) {
            SLASHES.add(new WindSlash(serverWorld, player, origin, forward,
                i * SLASH_INTERVAL, i));
        }

        player.getItemCooldownManager().set(item, COOLDOWN_TICKS);
        player.getMainHandStack().damage(1, player, EquipmentSlot.MAINHAND);
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

    @Override
    public void appendTooltip(ItemStack stack, Item.TooltipContext context,
                              List<Text> tooltip, TooltipType type) {
        super.appendTooltip(stack, context, tooltip, type);
        tooltip.add(Text.translatable("item.weapon.storm_greatsword.ability")
            .formatted(Formatting.AQUA));
    }

    /** One wind blade: a wall that travels forward, hitting each target once. */
    private static final class WindSlash {
        private final ServerWorld world;
        private final ServerPlayerEntity player;
        private final Vec3d origin;
        private final Vec3d forward;
        private final Set<UUID> hit = new HashSet<>();
        private final int index;
        private int delay;
        private double front;
        private boolean started;

        private WindSlash(ServerWorld world, ServerPlayerEntity player, Vec3d origin,
                          Vec3d forward, int delay, int index) {
            this.world = world;
            this.player = player;
            this.origin = origin;
            this.forward = forward;
            this.delay = delay;
            this.index = index;
        }

        /** @return true once this wave has finished travelling. */
        private boolean tick() {
            if (delay > 0) {
                delay--;
                return false;
            }
            if (player.isRemoved() || !player.isAlive()) {
                return true;
            }
            if (!started) {
                started = true;
                world.playSound(null, origin.x, origin.y, origin.z,
                    SoundEvents.ENTITY_PLAYER_ATTACK_SWEEP, SoundCategory.PLAYERS,
                    1.0f, 0.85f + index * 0.08f);
            }

            double previous = front;
            front = Math.min(MAX_RANGE, front + WAVE_SPEED);
            spawnWave(previous);
            damage(previous);
            return front >= MAX_RANGE;
        }

        private void spawnWave(double previous) {
            double y = origin.y + 1.1;
            for (double d = previous + 0.4; d <= front + 1.0E-6; d += 0.7) {
                for (int i = -4; i <= 4; i++) {
                    double side = HALF_WIDTH * i / 4.0;
                    double x = origin.x + forward.x * d - forward.z * side;
                    double z = origin.z + forward.z * d + forward.x * side;
                    double py = y + Math.cos(i * 1.1) * 0.25;
                    world.spawnParticles(ParticleTypes.SWEEP_ATTACK,
                        x, py, z, 1, 0.0, 0.0, 0.0, 0.0);
                    world.spawnParticles(ParticleTypes.CLOUD,
                        x, py - 0.2, z, 1, 0.1, 0.05, 0.1, 0.02);
                    if (i % 2 == 0) {
                        world.spawnParticles(ParticleTypes.ELECTRIC_SPARK,
                            x, py, z, 1, 0.1, 0.1, 0.1, 0.03);
                    }
                }
            }
            world.spawnParticles(ParticleTypes.GUST,
                origin.x + forward.x * front, y, origin.z + forward.z * front,
                2, 0.2, 0.2, 0.2, 0.01);
        }

        private void damage(double previous) {
            DamageSource source = world.getDamageSources().playerAttack(player);
            Vec3d mid = origin.add(forward.multiply((previous + front) * 0.5));
            Box box = new Box(mid, mid).expand(HALF_WIDTH + 1.0, VERTICAL_RANGE, HALF_WIDTH + 1.0);

            for (LivingEntity target : world.getEntitiesByClass(LivingEntity.class, box,
                    entity -> entity != player && entity != player.getVehicle()
                        && entity.isAlive() && !entity.isSpectator()
                        && (!(entity instanceof PlayerEntity other) || player.shouldDamagePlayer(other)))) {
                Vec3d offset = target.getPos().subtract(origin);
                double forwardDistance = offset.dotProduct(forward);
                if (forwardDistance < previous - 0.5 || forwardDistance > front + 0.5) {
                    continue;
                }
                double side = Math.abs(offset.x * forward.z - offset.z * forward.x);
                if (side > HALF_WIDTH + target.getWidth() * 0.5) {
                    continue;
                }
                if (Math.abs(target.getBodyY(0.5) - (origin.y + 1.0)) > VERTICAL_RANGE) {
                    continue;
                }
                if (!player.canSee(target)) {
                    continue;
                }
                if (!hit.add(target.getUuid())) {
                    continue;
                }

                // Successive waves are 5 ticks apart; clear the hit cooldown so
                // all three 8-damage hits land.
                target.timeUntilRegen = 0;
                if (target.damage(source, SLASH_DAMAGE)) {
                    Vec3d push = forward.multiply(0.45);
                    target.addVelocity(push.x, 0.2, push.z);
                    target.velocityModified = true;
                    world.spawnParticles(ParticleTypes.SWEEP_ATTACK,
                        target.getX(), target.getBodyY(0.5), target.getZ(),
                        1, 0.0, 0.0, 0.0, 0.0);
                }
            }
        }
    }
}
