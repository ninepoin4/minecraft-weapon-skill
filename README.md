# 我的世界武器 Skill / Minecraft Weapon Skill

A fixed 32×32 pixel-art workflow for Minecraft weapons, plus the Fabric 1.21.1 weapon mod used to test it.

![Selected weapon concepts](docs/images/weapon_selection_4.png)

*Selected 32×32 concepts: Echo Blade, Ender Folding Blade, Longsword v1, and Crystal Saber v2. These four are concept art; the playable weapons are listed below.*

## The skill

The skill lives in [`skill/minecraft-weapon-pixel-art/`](skill/minecraft-weapon-pixel-art/).

- `SKILL.md` — fixed-board workflow, weapon proportions, material rules, common failures, delivery checklist.
- `scripts/board.py` — `init` / `render` / validation; writes a single `review.png` with 8x light/dark/mid, GUI 16px, and silhouette panels.
- `assets/palette.json` — steel, deepslate, echo, sculk, copper, redstone, honey, amber, crystal, ender, amethyst, magnetite, obsidian, tidal, prismarine, shell, seaweed, blaze, gold, wood, and leather ramps.
- `templates/` — longsword, crystal saber, war axe, knife, spear.
- `examples/emerald_war_axe.json` — a calibration example.

Quick start:

```bash
python skill/minecraft-weapon-pixel-art/scripts/board.py init \
  --out spec.json --template longsword \
  --primary deepslate --secondary echo --grip sculk --name echo_blade

python skill/minecraft-weapon-pixel-art/scripts/board.py render \
  --spec spec.json --out candidate.png --preview-dir . --fast
```

Read `review.png`, fix the silhouette first, then paint the materials. Final render without `--fast`.

## The mod

A Fabric 1.21.1 weapon mod with hand-authored pixel-art sprites and custom combat abilities.

- Nine playable weapons in the **Weapon / 武器** creative tab.
- Custom right-click abilities: charge lunge, double reap, triple wind blade, blink strike.
- Animated sprites for Blaze Sword, Storm Greatsword, Hell Sickle, and Dark Tachi.
- A training dummy for damage testing.

Current weapons:

Iron Rapier · Venom Rapier · Alloy Sword · Blaze Sword · Greatsword · Sickle · Hell Sickle · Storm Greatsword · Dark Tachi

Plus the Training Dummy test tool. See [docs/WEAPONS.md](docs/WEAPONS.md) for stats, recipes, and ability details.

## Build

Requires Java 21.

```bash
./gradlew build
```

Windows:

```bat
gradlew.bat build
```

The jar is written to `build/libs/weapon-1.0.0.jar`. Drop it into the instance's `mods/` folder and restart the game.

## Art notes

The palette, templates, validation rules, and design notes are in [docs/minecraft-weapon-art-resources.md](docs/minecraft-weapon-art-resources.md).

## License

No license has been added yet. Add one before redistributing or reusing the code or art.
