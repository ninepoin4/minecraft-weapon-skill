# Weapon / 武器 — full reference

This is the detailed weapon reference. See the root [README](../README.md) for the project overview and concept art.

# Weapon / 武器

A standalone Fabric 1.21.1 mod that hosts the weapon collection. Kept separate
from `lightninggreatsword` so weapons can be added without touching other mods.

All weapons live in the mod's own **Weapon / 武器** creative tab and work in
survival through shaped recipes. Every item uses a vanilla `item/handheld` model
with a hand-drawn sprite (16x16 for most weapons; the scythes use 32x32 for the
long blade), so it holds like a vanilla sword.

3D item-model variants were also built for every weapon (direct `elements`,
vanilla-legal 22.5° rotations, 64x64 pixel atlases). They are preserved as
`models/item/<id>_3d.json` plus `textures/item/<id>_3d.png`, but the **active
item models are the 2D sprites**; swap the `_3d` files in to use a 3D model.

## Current weapons

### Iron Rapier / 细剑

- Item id: `weapon:iron_rapier`
- **5.5 attack damage**, **2.8 attack speed** — very fast, low burst.
- Iron-tier durability (250), repair with iron ingots.
- Rarity: common.
- Recipe:

```
 I
 C
 S
```

`I` = iron ingot, `C` = chain, `S` = stick.

### Venom Rapier / 蛇毒细剑

- Item id: `weapon:venom_rapier`
- **7 attack damage**, **2.2 attack speed**.
- Iron-tier durability (250), repair with iron ingots.
- On hit: **Poison I for 5s** and a splash of green slime particles.
- Rarity: uncommon.
- Recipe:

```
 P
 IE
 S
```

`P` = spider eye, `I` = iron ingot, `E` = emerald, `S` = stick.

### Alloy Sword / 合金剑

- Item id: `weapon:alloy_sword`
- **8 attack damage**, **1.6 attack speed**.
- Diamond-tier durability (**1561**), enchantability 18, repair with iron
  ingots.
- Rarity: uncommon. Custom `ToolMaterial` (`WeaponMaterials.ALLOY`).
- Recipe:

```
 I
CIG
 S
```

`I` = iron ingot, `C` = copper ingot, `G` = gold ingot, `S` = stick.

### Blaze Sword / 烈焰剑

- Item id: `weapon:blaze_sword`
- **8 attack damage**, **1.6 attack speed**.
- Diamond-tier durability (1561), enchantability 20, fireproof, repair with
  blaze rods. Custom `ToolMaterial` (`WeaponMaterials.BLAZE`).
- On hit: **ignites the target for 5s**, flame particles + fire charge sound.
- The item texture is an **8-frame animated fire blade**
  (`blaze_sword.png` 16x128 + `blaze_sword.png.mcmeta`, 10 fps).
- Rarity: rare.
- Recipe:

```
 B
 M
 S
```

`B` = blaze rod, `M` = magma block, `S` = stick.

### Greatsword / 巨剑

- Item id: `weapon:greatsword`
- **13 attack damage**, **0.8 attack speed** — devastating per hit, very slow.
- Netherite-tier durability (**2031**), enchantability 15, repair with iron
  ingots. Custom `ToolMaterial` (`WeaponMaterials.GREATSWORD`).
- **1.5x the size of a normal sword when held**: the model overrides the vanilla
  `item/handheld` display scales (`0.85 -> 1.275` third person, `0.68 -> 1.02`
  first person). The GUI icon stays 16x16 so it fits the inventory slot.
- **Right-click ability (charge lunge)**: hold right-click for 1s. While
  charging, the player is in a guard stance (and gets Slowness I), with sparks
  and a rising chime. At full charge the player **lunges 2 blocks forward**
  (stopping at walls / stepping up one block) with a dust trail and a heavy
  impact sound, performs a visible swing, then **thrusts up to 4 blocks ahead**
  of the new position: every visible living entity in that corridor takes
  **1.5x attack damage (19.5)**, with knockback, a spark trail, sweep particles
  and a crit sound. 3s cooldown, 1 durability per use. Releasing early cancels
  the lunge.
- Rarity: rare.
- Recipe (2 iron blocks + 1 iron sword):

```
 B
 B
 S
```

`B` = iron block, `S` = iron sword.

### Sickle / 镰刀

- Item id: `weapon:sickle`
- **7 attack damage**, **1.0 attack speed** — slow, long-reaching.
- **+1.5 blocks of entity attack reach** while held (player interaction range
  3 -> 4.5).
- Diamond-tier durability (1561), enchantability 18, repair with diamonds.
- **Right-click ability (double reap)**: two full-charge sweeps 0.25s apart.
  Each sweep hits every visible living entity in a 130-degree arc up to the
  weapon's reach for full attack damage, with crit particles, sweep particles
  and knockback. 4s cooldown, 1 durability per use.
- Rarity: uncommon.
- Sprite: 32x32 reaper scythe (`art/make_sickle_sprites.py`) — a long slender
  snath with a big tapered crescent blade; held at 1.2x scale.
- Recipe (2 diamonds + 2 sticks):

```
 DD
  S
  S
```

`D` = diamond, `S` = stick.

### Hell Sickle / 地狱镰刀

- Item id: `weapon:hell_sickle`
- **12 attack damage**, **0.9 attack speed**, **+1.5 reach**.
- Netherite-tier durability (2031), enchantability 15, fireproof, repair with
  netherite ingots.
- Same double-reap ability, with soul-fire particles and a deeper swing sound.
- Rarity: rare.
- Recipe (2 obsidian + 1 netherite ingot + 2 sticks):

```
 OO
 NS
  S
```

`O` = obsidian, `N` = netherite ingot, `S` = stick.

### Storm Greatsword / 风暴大剑

- Item id: `weapon:storm_greatsword`
- **Boss drop — no crafting recipe.** It is only available in the creative tab
  (and from the future boss loot table).
- **15 attack damage**, **0.8 attack speed** — a heavier greatsword.
- 2500 durability, enchantability 18, fireproof, repaired with wind charges.
- Extra-long two-handed grip with two collar sections, and an **animated 64x64
  divine texture** (8-frame white-gold radiance over pale-blue steel, gold
  wing-guards and a glowing gem pommel; `art/make_storm_greatsword.py`).
- **Right-click ability (triple wind blade)**: hold right-click for **2s**. At
  full charge three wind blades sweep out in front of the player; each wave
  travels up to **12 blocks**, hitting everything it passes for **8 damage**.
  The three waves are 0.25s apart, so one target can take 24 damage. 10s
  cooldown, 1 durability per use. Releasing early cancels the charge.
- Rarity: epic.

### Dark Tachi: Ryūgiri / 黑暗太刀：龙切

- Item id: `weapon:dark_tachi`
- **16 attack damage**, **1.0 attack speed**, 2500 durability,
  enchantability 18, repaired with obsidian.
- An obsidian ōdachi with a violet cutting edge, gold tsuba with a red
  dragon-eye gem, and a black wrapped grip. Two visual variants exist:
  - **2D sprite (active)** — 64×64 texture, 8-frame animated violet edge/gem
    glow (`art/make_dark_tachi.py`), used by `models/item/dark_tachi.json`.
  - **3D pixel model (preserved)** — Blockbench-modeled curved blade built from
    86 cuboids (30 body segments + 9 tip segments + fittings) with a
    purpose-built **64×64 pixel-art atlas**
    (`art/make_dark_tachi_atlas_pixel.py`, `art/build_dark_tachi_3d.py`).
    Preserved as `models/item/dark_tachi_3d.json` +
    `textures/item/dark_tachi_3d.png`; not currently referenced by the item.
  - Vanilla 1.21.1 only accepts element rotations of -45/-22.5/0/22.5/45°.
    The 3D curve was snapped to -45°/-22.5° with overlapping slices; the
    unsnapped reference is kept in `art/dark_tachi_3d_full.json`. A custom
    loader that bypassed the angle check was tried and removed.
- **Right-click ability (blink strike)**: locks onto the living entity under
  the crosshair (up to 20 blocks, line of sight required). The player blinks to
  a free spot in front of it and delivers one heavy cut for **1.5× damage**
  (24 with the base 16), setting the target on fire for 5s. If the cut kills
  the target, the **8s cooldown is cleared immediately**. No target → actionbar
  message and no cooldown. 1 durability per use.
- Rarity: epic.

## Training Dummy / 训练稻草人

A test tool in the **Weapon** creative tab (reusable item, no recipe).

- Right-click a block face to place a scarecrow dummy.
- **Infinite health**: hits never reduce its health and it cannot die, except
  from `/kill`.
- **No AI goals**: it never walks or attacks on its own. The AI flag itself
  stays enabled on purpose: `NoAI` also disables entity movement physics
  (`isLogicalSideForUpdatingMovement()`), which made the dummy ignore
  knockback. With no goals it stands still but can be **knocked back, launched,
  pushed, set on fire, poisoned**, etc.
- Every **direct hit** pops a floating damage number above it (red for normal
  hits, gold for 15+). Fire/poison/fall ticks never reduce health and do not
  spam numbers.
- Uses the zombie humanoid model with a custom straw/pumpkin texture
  (`textures/entity/training_dummy.png`), rendered arms-out like a scarecrow.
- Entity id: `weapon:training_dummy`; item id: `weapon:training_dummy`.
- Command: `/summon weapon:training_dummy`

## Stats formula

`WeaponAttributes.sword(damage, speed)` writes the final tooltip values
directly. Minecraft's player base is 1 attack damage and 4 attack speed, so the
component stores `damage - 1` and `speed - 4` as `ADD_VALUE` modifiers on
`MAINHAND`. This is why fractional values such as 5.5 work.

## Adding the next weapon

1. Draw a sprite on the fixed 32×32 pixel board with the local
   `minecraft-weapon-pixel-art` skill (see
   [`docs/minecraft-weapon-art-resources.md`](minecraft-weapon-art-resources.md)).
   The skill's `board.py` handles init/render/validation and writes `review.png`
   with 8x light/dark/GUI/silhouette previews. Older weapons still use their
   original 16x16/32x32 sprites. For an animated texture, stack N frames
   vertically and add a `.png.mcmeta` with
   `{"animation": {"frametime": 2}}`.
2. Add a class in `com.weapon.item` if the weapon needs custom behaviour
   (override `postHit`, `use`, etc.), or reuse `DescribedSwordItem` /
   `SwordItem`.
3. Declare and register the item in `com.weapon.registry.ModItems` using
   `WeaponAttributes.sword(damage, speed)`. Use `WeaponMaterials` or a vanilla
   `ToolMaterials` value for durability/enchantability/repair.
4. Add the item to `ModItemGroups.WEAPONS`.
5. Drop the sprite in `assets/weapon/textures/item/`, add the
   `item/handheld` model and lang entries (`en_us.json`, `zh_cn.json`), and a
   recipe in `data/weapon/recipe/`.
6. Rebuild and reinstall the jar (see below).

## Build

```bash
./gradlew build
```

Windows:

```bat
gradlew.bat build
```

Jar: `build/libs/weapon-1.0.0.jar`

Install to:

```
E:\mc1.21.1\versions\fabric-loader-0.19.5-1.21.1\mods\
```

Fully restart the game after replacing the jar.
