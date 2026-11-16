package com.weapon.item;

import java.util.List;

import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.SwordItem;
import net.minecraft.item.ToolMaterial;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;

/**
 * A sword with one extra flavour line in its tooltip.
 */
public class DescribedSwordItem extends SwordItem {
    private final String tooltipKey;
    private final Formatting color;

    public DescribedSwordItem(ToolMaterial material, Item.Settings settings,
                              String tooltipKey, Formatting color) {
        super(material, settings);
        this.tooltipKey = tooltipKey;
        this.color = color;
    }

    @Override
    public void appendTooltip(ItemStack stack, Item.TooltipContext context, List<Text> tooltip, TooltipType type) {
        tooltip.add(Text.translatable(tooltipKey).formatted(color));
    }
}
