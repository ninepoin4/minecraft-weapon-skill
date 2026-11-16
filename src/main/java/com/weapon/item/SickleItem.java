package com.weapon.item;

import java.util.ArrayList;
import java.util.List;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.enchantment.EnchantmentHelper;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.ToolMaterial;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.particle.ParticleEffect;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

/**
 * The two sickles: a long-armed, slow weapon whose right-click ability performs
 * two full-charge swings in quick succession.
 *
 * <p>The weapon itself has extra entity attack reach through
 * {@link WeaponAttributes#sickle}. The ability hits everything in a wide arc in
 * front of the player, twice, with a short cooldown between the two cuts.</p>
 */
public class SickleItem extends DescribedSwordItem {
    private static final int COOLDOWN_TICKS = 80;      // 4 s
    private static final int SECOND_HIT_DELAY = 5;     // 0.25 s between cuts
    private static final double ARC_HALF_ANGLE = Math.toRadians(65.0);
    private static final double ARC_COS = Math.cos(ARC_HALF_ANGLE);
    private static final double EXTRA_RANGE = 0.5;     // beyond interaction reach
    private static final double MIN_RANGE = 0.25;
    private static final double VERTICAL_RANGE = 2.5;

    /** Second cuts that are waiting for their delay to expire. */
    private static final List<PendingStrike> PENDING = new ArrayList<>();

    static {
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            for (int i = PENDING.size() - 1; i >= 0; i--) {
                PendingStrike pending = PENDING.get(i);
                if (--pending.ticksLeft > 0) {
                    continue;
                }
                PENDING.remove(i);
                pending.fire();
            }
        });
    }

    private final boolean hellish;

    public SickleItem(ToolMaterial material, Item.Settings settings, String tooltipKey,
                      Formatting color, boolean hellish) {
        super(material, settings, tooltipKey, color);
        this.hellish = hellish;
    }

    @Override
    public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
        ItemStack stack = user.getStackInHand(hand);
        if (hand != Hand.MAIN_HAND || user.getItemCooldownManager().isCoolingDown(this)) {
            return TypedActionResult.fail(stack);
        }

        if (!world.isClient && user instanceof ServerPlayerEntity player) {
            ServerWorld serverWorld = (ServerWorld) world;
            strike(serverWorld, player, stack);
            PENDING.add(new PendingStrike(serverWorld, player, this, SECOND_HIT_DELAY));
            player.getItemCooldownManager().set(this, COOLDOWN_TICKS);
            stack.damage(1, player, EquipmentSlot.MAINHAND);
        }
        return TypedActionResult.consume(stack);
    }

    /** One full-charge sweep: a 130-degree arc up to the weapon's reach. */
    private void strike(ServerWorld world, ServerPlayerEntity player, ItemStack stack) {
        player.swingHand(Hand.MAIN_HAND);
        player.resetLastAttackedTicks();

        Vec3d look = player.getRotationVec(1.0f);
        Vec3d flat = new Vec3d(look.x, 0.0, look.z);
        if (flat.lengthSquared() < 1.0E-6) {
            double yaw = Math.toRadians(player.getYaw());
            flat = new Vec3d(-Math.sin(yaw), 0.0, Math.cos(yaw));
        }
        flat = flat.normalize();

        double range = Math.max(MIN_RANGE, player.getEntityInteractionRange() + EXTRA_RANGE);
        Box searchBox = player.getBoundingBox().expand(range + 1.0, VERTICAL_RANGE + 1.0, range + 1.0);

        float baseDamage = (float) player.getAttributeValue(EntityAttributes.GENERIC_ATTACK_DAMAGE);
        DamageSource source = world.getDamageSources().playerAttack(player);
        Vec3d origin = player.getPos();
        boolean hitAny = false;

        for (LivingEntity target : world.getEntitiesByClass(LivingEntity.class, searchBox,
                entity -> entity != player && entity != player.getVehicle()
                    && entity.isAlive() && !entity.isSpectator()
                    && (!(entity instanceof PlayerEntity other) || player.shouldDamagePlayer(other)))) {
            Vec3d offset = target.getPos().subtract(origin);
            double horizontalDistance = Math.sqrt(offset.x * offset.x + offset.z * offset.z);
            if (horizontalDistance < MIN_RANGE || horizontalDistance > range) {
                continue;
            }
            if ((offset.x * flat.x + offset.z * flat.z) / horizontalDistance < ARC_COS) {
                continue;
            }
            if (Math.abs(target.getBodyY(0.5) - player.getEyeY()) > VERTICAL_RANGE) {
                continue;
            }
            if (!player.canSee(target)) {
                continue;
            }

            // The two cuts are only a few ticks apart, so clear the target's
            // damage cooldown to let both full-charge hits land.
            target.timeUntilRegen = 0;
            float damage = EnchantmentHelper.getDamage(world, stack, target, source, baseDamage);
            if (target.damage(source, damage)) {
                hitAny = true;
                EnchantmentHelper.onTargetDamaged(world, target, source, stack);
                player.addCritParticles(target);
                Vec3d push = offset.normalize();
                target.addVelocity(push.x * 0.3, 0.15, push.z * 0.3);
                target.velocityModified = true;
                world.spawnParticles(hitParticle(),
                    target.getX(), target.getBodyY(0.55), target.getZ(),
                    hellish ? 10 : 1, 0.3, 0.35, 0.3, 0.02);
            }
        }

        spawnSwingParticles(world, player, flat, range);
        world.playSound(null, player.getX(), player.getY(), player.getZ(),
            SoundEvents.ENTITY_PLAYER_ATTACK_SWEEP, SoundCategory.PLAYERS,
            0.85f, hellish ? 0.7f : 1.0f);
        if (hitAny) {
            world.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.ENTITY_PLAYER_ATTACK_CRIT, SoundCategory.PLAYERS, 1.0f, 0.9f);
        }
    }

    private void spawnSwingParticles(ServerWorld world, ServerPlayerEntity player,
                                     Vec3d flat, double range) {
        double baseAngle = Math.atan2(flat.z, flat.x);
        for (int i = -3; i <= 3; i++) {
            double angle = baseAngle + ARC_HALF_ANGLE * i / 3.0;
            double distance = range * 0.55;
            double x = player.getX() + Math.cos(angle) * distance;
            double z = player.getZ() + Math.sin(angle) * distance;
            double y = player.getY() + 1.05;
            if (hellish) {
                world.spawnParticles(ParticleTypes.SOUL_FIRE_FLAME, x, y, z,
                    2, 0.12, 0.15, 0.12, 0.01);
            } else {
                world.spawnParticles(ParticleTypes.SWEEP_ATTACK, x, y, z,
                    1, 0.0, 0.0, 0.0, 0.0);
            }
        }
    }

    private ParticleEffect hitParticle() {
        return hellish ? ParticleTypes.SOUL_FIRE_FLAME : ParticleTypes.SWEEP_ATTACK;
    }

    @Override
    public void appendTooltip(ItemStack stack, Item.TooltipContext context,
                              List<Text> tooltip, TooltipType type) {
        super.appendTooltip(stack, context, tooltip, type);
        tooltip.add(Text.translatable(hellish
            ? "item.weapon.hell_sickle.ability"
            : "item.weapon.sickle.ability").formatted(Formatting.GRAY));
    }

    /** A queued second cut, executed on the server tick loop. */
    private static final class PendingStrike {
        private final ServerWorld world;
        private final ServerPlayerEntity player;
        private final SickleItem item;
        private int ticksLeft;

        private PendingStrike(ServerWorld world, ServerPlayerEntity player,
                              SickleItem item, int ticksLeft) {
            this.world = world;
            this.player = player;
            this.item = item;
            this.ticksLeft = ticksLeft;
        }

        private void fire() {
            if (player.isRemoved() || !player.isAlive()) {
                return;
            }
            ItemStack stack = player.getMainHandStack();
            if (stack.isEmpty() || stack.getItem() != item) {
                return;
            }
            item.strike(world, player, stack);
        }
    }
}
