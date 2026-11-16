package com.weapon.item;

import java.util.List;

import com.weapon.entity.TrainingDummyEntity;
import com.weapon.registry.ModEntities;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.ItemUsageContext;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

/**
 * Places the training dummy on the clicked block face.
 */
public class TrainingDummyItem extends Item {
    public TrainingDummyItem(Item.Settings settings) {
        super(settings);
    }

    @Override
    public ActionResult useOnBlock(ItemUsageContext context) {
        World world = context.getWorld();
        if (!world.isClient) {
            BlockPos pos = context.getBlockPos().offset(context.getSide());
            spawn((ServerWorld) world,
                pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5,
                context.getPlayer());
        }
        return ActionResult.success(world.isClient);
    }

    public static TrainingDummyEntity spawn(ServerWorld world, double x, double y, double z,
                                            PlayerEntity player) {
        TrainingDummyEntity dummy = ModEntities.TRAINING_DUMMY.create(world);
        if (dummy == null) {
            return null;
        }
        float yaw = player != null ? player.getYaw() + 180.0f : 0.0f;
        dummy.refreshPositionAndAngles(x, y, z, yaw, 0.0f);
        world.spawnEntity(dummy);
        return dummy;
    }

    @Override
    public void appendTooltip(ItemStack stack, Item.TooltipContext context,
                              List<Text> tooltip, TooltipType type) {
        tooltip.add(Text.translatable("item.weapon.training_dummy.tooltip")
            .formatted(Formatting.GRAY));
    }
}
