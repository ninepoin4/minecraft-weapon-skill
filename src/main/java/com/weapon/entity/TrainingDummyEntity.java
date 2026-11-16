package com.weapon.entity;

import net.minecraft.entity.EntityData;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.SpawnReason;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.damage.DamageTypes;
import net.minecraft.entity.mob.ZombieEntity;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.LocalDifficulty;
import net.minecraft.world.ServerWorldAccess;
import net.minecraft.world.World;

/**
 * A scarecrow training dummy: stands still, never dies, and pops a floating
 * damage number whenever it is hit.
 *
 * <p>Extends the zombie only to reuse its humanoid (arms-out) model. It has
 * no AI goals at all, so it never walks or attacks, but its AI flag stays on
 * so knockback, explosions and other external pushes still move it. Daylight
 * burning and water conversion are also disabled.</p>
 */
public class TrainingDummyEntity extends ZombieEntity {
    public static final String DUMMY_TAG = "weapon_dummy";

    public TrainingDummyEntity(EntityType<? extends ZombieEntity> entityType, World world) {
        super(entityType, world);
        this.applyDummySettings();
    }

    private void applyDummySettings() {
        // Keep the AI flag ON. NoAI makes canMoveVoluntarily() false, which
        // makes isLogicalSideForUpdatingMovement() false, which skips
        // LivingEntity.travel() entirely: the dummy would then have velocity
        // but never actually move, ignoring knockback, explosions and water.
        // It stays still because initGoals() registers no goals at all.
        this.setAiDisabled(false);
        this.setSilent(true);
        this.setPersistent();
        if (this.getCustomName() == null) {
            this.setCustomName(Text.translatable("entity.weapon.training_dummy"));
        }
        this.setCustomNameVisible(true);
        this.addCommandTag(DUMMY_TAG);
    }

    @Override
    public void readCustomDataFromNbt(NbtCompound nbt) {
        super.readCustomDataFromNbt(nbt);
        this.applyDummySettings();
        this.setBaby(false);
    }

    @Override
    protected void initGoals() {
        // No goals at all: the dummy never moves or attacks on its own, but
        // the AI flag itself stays on so its physics keep working.
    }

    @Override
    public boolean canPickUpLoot() {
        // With the AI flag on, MobEntity.tickMovement scans for dropped items;
        // a scarecrow should not hoover them up.
        return false;
    }

    @Override
    public boolean damage(DamageSource source, float amount) {
        if (this.getWorld().isClient || amount <= 0.0f) {
            return false;
        }

        // /kill must still be able to clean the dummy up.
        if (source.isOf(DamageTypes.GENERIC_KILL)) {
            return super.damage(source, amount);
        }

        // Only direct hits (player/mob/projectile/explosion source) get a
        // floating number. Fire/poison/fall ticks stay silent but never
        // reduce health.
        boolean directHit = source.getAttacker() != null || source.getSource() != null;
        if (directHit) {
            if (this.getWorld() instanceof ServerWorld serverWorld) {
                TrainingDummyVisuals.showDamage(serverWorld, this, amount);
                serverWorld.sendEntityDamage(this, source);
                serverWorld.spawnParticles(ParticleTypes.DAMAGE_INDICATOR,
                    this.getX(), this.getBodyY(0.6), this.getZ(),
                    6, 0.25, 0.3, 0.25, 0.05);
            }

            this.animateDamage(source.getAttacker() != null
                ? source.getAttacker().getYaw()
                : this.getYaw());
            this.getWorld().playSound(null, this.getX(), this.getY(), this.getZ(),
                SoundEvents.ENTITY_ARMOR_STAND_HIT, SoundCategory.NEUTRAL, 0.9f, 1.0f);

            // We bypass LivingEntity.damage (to keep infinite health), so apply
            // the base knockback ourselves.
            if (source.getAttacker() instanceof LivingEntity attacker) {
                Vec3d away = this.getPos().subtract(attacker.getPos());
                if (away.lengthSquared() > 1.0E-6) {
                    away = away.normalize();
                    this.addVelocity(away.x * 0.45, 0.12, away.z * 0.45);
                    this.velocityModified = true;
                }
            }
        }

        // Report a successful hit without ever losing health.
        return true;
    }

    @Override
    protected boolean isAffectedByDaylight() {
        return false;
    }

    @Override
    protected boolean isDisallowedInPeaceful() {
        return false;
    }

    @Override
    protected boolean canConvertInWater() {
        return false;
    }

    @Override
    public EntityData initialize(ServerWorldAccess world, LocalDifficulty difficulty,
                                 SpawnReason spawnReason, EntityData entityData) {
        EntityData data = super.initialize(world, difficulty, spawnReason, entityData);
        this.setBaby(false);
        return data;
    }
}
