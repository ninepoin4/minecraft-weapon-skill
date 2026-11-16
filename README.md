# Weapon / 武器

A Fabric 1.21.1 weapon mod with hand-authored pixel-art sprites and custom combat abilities.

![Selected weapon concepts](docs/images/weapon_selection_4.png)

*Selected 32×32 concepts from the fixed-board art workflow: Echo Blade, Ender Folding Blade, Longsword v1, and Crystal Saber v2. These four are concept art; the playable weapons are listed below.*

## Features

- Fabric 1.21.1, Java 21.
- Nine playable weapons in the **Weapon / 武器** creative tab.
- Custom right-click abilities: charge lunge, double reap, triple wind blade, blink strike.
- Animated sprites for Blaze Sword, Storm Greatsword, Hell Sickle, and Dark Tachi.
- A training dummy for damage testing.
- A fixed 32×32 pixel-board workflow for designing new weapon concepts.

## Current weapons

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

## Art workflow

Weapon sprites are authored on a fixed 32×32 pixel board. The palette, templates, validation rules, and design notes are in [docs/minecraft-weapon-art-resources.md](docs/minecraft-weapon-art-resources.md).

## License

No license has been added yet. Add one before redistributing or reusing the code or art.
