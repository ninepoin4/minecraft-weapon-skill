package com.weapon.entity;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.decoration.DisplayEntity;
import net.minecraft.entity.decoration.DisplayEntity.TextDisplayEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;

/**
 * Floating damage numbers for the training dummy, rendered with vanilla text
 * display entities (no client code needed).
 */
public final class TrainingDummyVisuals {
    private static final int LIFETIME_TICKS = 20;
    private static final List<FloatingDamage> FLOATING = new ArrayList<>();

    private TrainingDummyVisuals() {
    }

    public static void init() {
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            if (FLOATING.isEmpty()) {
                return;
            }
            Iterator<FloatingDamage> iterator = FLOATING.iterator();
            while (iterator.hasNext()) {
                FloatingDamage damage = iterator.next();
                long now = damage.world.getTime();
                if (now >= damage.expire || damage.display.isRemoved()) {
                    damage.display.discard();
                    iterator.remove();
                    continue;
                }

                float progress = 1.0f - (float) (damage.expire - now) / LIFETIME_TICKS;
                damage.display.setPosition(
                    damage.display.getX(),
                    damage.startY + progress * 0.55,
                    damage.display.getZ());
                damage.display.setTextOpacity((byte) (255 * (1.0f - progress)));
            }
        });
    }

    public static void showDamage(ServerWorld world, LivingEntity target, float amount) {
        TextDisplayEntity display = EntityType.TEXT_DISPLAY.create(world);
        if (display == null) {
            return;
        }

        double x = target.getX() + (world.random.nextDouble() - 0.5) * 0.5;
        double y = target.getY() + target.getHeight() + 0.85;
        double z = target.getZ() + (world.random.nextDouble() - 0.5) * 0.5;
        display.refreshPositionAndAngles(x, y, z, 0.0f, 0.0f);
        display.setText(Text.literal(format(amount))
            .formatted(amount >= 15.0f ? Formatting.GOLD : Formatting.RED));
        display.setBillboardMode(DisplayEntity.BillboardMode.CENTER);
        display.setBackground(0x66000000);
        display.setDisplayFlags((byte) (TextDisplayEntity.SHADOW_FLAG
            | TextDisplayEntity.SEE_THROUGH_FLAG));
        world.spawnEntity(display);

        FLOATING.add(new FloatingDamage(world, display, world.getTime() + LIFETIME_TICKS, y));
    }

    private static String format(float amount) {
        if (!Float.isFinite(amount) || amount > 10000.0f) {
            return "??";
        }
        if (Math.abs(amount - Math.round(amount)) < 0.05f) {
            return Integer.toString(Math.round(amount));
        }
        return String.format(Locale.ROOT, "%.1f", amount);
    }

    private record FloatingDamage(ServerWorld world, TextDisplayEntity display,
                                  long expire, double startY) {
    }
}
