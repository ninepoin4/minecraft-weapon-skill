# Minecraft 武器像素画：现成 Skill / 教程调研

- 调研日期：2026-11-16
- 范围：剑、镐、斧、弓等物品图标（2D sprite），兼顾 3D 物品模型
- 当前项目状态：9 把武器已全部切回 2D 模型；3D 变体以 `<id>_3d.json` + `<id>_3d.png` 保留

## 0. 结论

1. **本机原有的 skill 里没有“画 Minecraft 武器”的。** 唯一相关的旧 skill 是 `minecraft-fabric-mod`，它负责把 Blockbench 模型接进 Fabric（实体/Boss、盒式 UV、刷怪蛋、构建），不教画 2D 武器图标。
   **2026-11-16 更新：已按本报告的结论落地 `minecraft-weapon-pixel-art`（固定 32×32 画板）；下面的外部 skill 仅作调研记录，实验 clone 已清理。**
2. **外部最接近“直接可用”的是 Blockpixel Artist**：自带 sword / pickaxe / axe / bow 等原版模板，Template First + Canonical Lock，带像素、透明背景、轮廓校验。它是 Agent Skill（`SKILL.md` + Python 脚本），可以移植到 ZCode 的 skills 目录；但默认尺寸是 32/64/128，不含 16×16，也不自带原版贴图，需要按本项目的 16×16/32×32 风格做适配。
3. **Deterministic Pixel Art** 适合做“可复现的像素编辑/校验”，不是武器模板库。
4. **Texel MCP** 能用 JSON spec 生成并检查 1.21 的物品贴图（含 16×16 示例），适合标准物品 sprite，但不提供武器造型模板。
5. **Blockbench MCP 的 texturing / flipbook-textures skill** 只在回到 3D 建模、UV、动画贴图时有用。
6. 教程里最实用的是 Fumora Lab、MiemieMethod 的 Minecraft 美术风格、Blockbench 官方 Style Guide、ResourcePack AI 的物品图标规范。Minecraft Wiki 的 “Tutorial:Pixel art” 是方块建筑，不是物品图标，基本不适用。

## 1. 本地现状

本地 skill 扫描范围：`C:\Users\Administrator\.agents\skills`。用
`grep -ril --include=SKILL.md -e pixel -e 像素 -e minecraft` 只命中一个：

| 本地 skill | 覆盖内容 | 对武器绘制的作用 | 复用判定 |
|---|---|---|---|
| `minecraft-weapon-pixel-art` | 固定 32×32 画板、`board.py`、材质调色板、比例模板、验证/预览 | 直接绘制武器图标 | **已落地，首选** |
| `minecraft-fabric-mod` | Fabric 1.21.1 工程、Blockbench → Java 实体模型、盒式 UV、刷怪蛋、动画、构建 jar | 不画 2D 图标；3D 模型接进游戏可用 | **接线可复用，画画不复用** |
| 其他已装 skill | 钉钉、文档、PDF、表格、Blender、Godot 等 | 无关 | 否 |

结论：原环境不存在“本机已经装好、直接让 agent 画武器”的 skill；现在已落地 `minecraft-weapon-pixel-art`，并清理了三个实验 clone。

## 2. 外部 Skill / 工具

### 2.1 Blockpixel Artist —— 最推荐

- 来源：https://github.com/yzxr123/blockpixel-artist
- 类型：Agent Skill（`SKILL.md` + Python 脚本 + 模板/校验器），Apache-2.0
- 覆盖：
  - 原生像素网格 32×32 / 64×64 / 128×128，不先生成大图再缩小
  - 物品/图标默认透明背景
  - “Template First”：先定轮廓和比例，再上材质
  - “Canonical Lock”：保持原版 Minecraft 物品剪影
  - 游戏美术检查：结构/功能不合理的造型会被拦
  - 自动校验 art plan、alpha、palette、template offset、silhouette
  - 强制预览 + PNG 交付
- 内置模板：pickaxe、sword、axe、shovel、hoe、helmet、chestplate、leggings、boots、bow、crossbow、trident、book、potion、elytra
- 对剑/镐/斧/弓：**四类都有模板**。弓要注意游戏内是 `bow_standby` + `bow_pulling_0/1/2` 四张图/四个模型，模板通常只给 standby 图标。
- 安装：
  - README 给的是 Codex 的 `$skill-installer install https://github.com/yzxr123/blockpixel-artist/tree/main/skill/blockpixel-artist`
  - ZCode 下的建议路径：把 `skill/blockpixel-artist` 目录放到
    `C:\Users\Administrator\.agents\skills\blockpixel-artist`，再
    `pip install -r requirements.txt`（Python 3.10+）。**这是建议路径，尚未实际安装/验证。**
- 直接复用：**可以，但需适配。**
  - 默认尺寸不含 16×16；本项目多数武器是 16×16
  - Canonical Lock 需要自备合法获得的 Bedrock 资源包或 `textures/items` 目录（仓库不附带原版贴图）
  - 我们的调色板、32×32 镰刀、64×64 太刀、垂直动画条都需要额外规则
- 最适合：快速出符合原版轮廓的剑/镐/斧/弓底稿，再用项目脚本精修。

### 2.2 Deterministic Pixel Art

- 来源：https://github.com/Chenamel/deterministic-pixel-art
- 类型：Agent Skill / Python CLI（Python 3.10+，Pillow 12.3.0）
- 覆盖：
  - 文本网格、整数绘图命令、Python mask → PNG
  - 导入现有 PNG 不做量化
  - 只改选定区域，并精确报告哪些像素变了
  - 命名精灵图集
- 对剑/镐/斧/弓：不提供武器造型模板；适合改我们的 `art/make_*_sprites.py` 输出、调色、做动画帧、验证 diff。
- 直接复用：**可以作为工具/校验用，不能当美术模板。**
- 注意：Minecraft 风格是 optional，项目不验证游戏集成。

### 2.3 Texel MCP

- 来源：https://github.com/Brunovncs/texel-mcp
- 类型：MCP server + CLI + Claude Code plugin，MIT，Node 20+
- 覆盖：
  - 用 JSON spec 描述纹理，确定性编译成 PNG
  - Java Edition 1.21 布局；玩家皮肤 + 68 种纹理，含 items、blocks、GUI、particles、paintings
  - review 步骤按 JSON path 报错并给修复提示
  - 可组装并检查资源包
- 对剑/镐/斧/弓：支持标准物品贴图（示例 `ember-blade` 是 16×16 item），适合 2D 图标；**不支持自定义 3D 几何**。
- 直接复用：**部分可以。** 需要手写 JSON spec；没有武器造型模板；作为“生成 + 校验”管线有价值。

### 2.4 Blockbench MCP skills

- 来源：https://github.com/jasonjgardner/blockbench-mcp-project
- 类型：Agent Skills + Blockbench MCP server
- 覆盖：
  - `blockbench-texturing`：画笔、UV、图层、填充、渐变、形状
  - `blockbench-flipbook-textures`：生成垂直 flipbook PNG 并在 Blockbench/Minecraft 里播放
  - 另有 modeling、animation、pbr-materials 等
- 安装示例：
  `npx skills add https://github.com/jasonjgardner/blockbench-mcp-project --skill blockbench-texturing`
- 对剑/镐/斧/弓：2D 图标不适用；3D 物品模型、UV、动画贴图适用。
- 直接复用：**3D 路线可直接复用；2D 路线不需要。**

### 2.5 不推荐 / 不适用

| 来源 | 原因 |
|---|---|
| Photo2Skin MCP | 照片 → 皮肤/材质包，偏玩家皮肤，不适合武器图标（未深入验证） |
| minecraft-3d-avatar | 头像生成，不相关 |
| Minecraft Wiki “Tutorial:Pixel art” | 用方块搭像素画，不是物品 sprite |

## 3. 教程 / 规范

| 来源 | 内容 | 对剑/镐/斧/弓 | 复用判定 |
|---|---|---|---|
| [Fumora Lab：Minecraft Pixel Art Guide](https://www.fumora.net/lab/minecraft-pixel-art-painter-guide) | 16/32/64 尺寸选择；每种材质 3–5 个明暗；左上打光；深色描边；避免孤立像素/枕形阴影；复制原版结构；资源包路径 | 直接适用 2D 武器 | **当规则清单用** |
| [MiemieMethod：Minecraft 美术风格](https://github.com/MiemieMethod/bedrock-docs/blob/main/docs/guides/tools/blockbench/minecraft-style.md) | 模型先概括形体；保持像素比例；midstone→阴影/高光；用色相/饱和度变化而不只是明度；避免 pillow shading、banding、jaggies、过度抖动；物品 16×16 左上高光右下阴影 | 直接适用 | **当检查清单用** |
| [Blockbench 官方 Minecraft Style Guide](https://blockbench.net/wiki/guides/minecraft-style-guide/) | Box UV vs per-face UV；纹理模板；实体贴图流程（先铺色 → 阴影/高光 → 扩色板 → 定义材质） | 3D 模型/UV | 3D 时用 |
| [Blockbench Bedrock Wiki](https://wiki.bedrock.dev/guide/blockbench) | 勾选 Box UV、Texture Template、Paint 模式、保存路径 | 3D 模型 | 3D 时用 |
| [ResourcePack AI Docs — Items](https://resourcepack.ai/docs/items) | 16/32/64/128 尺寸；深色且不间断的描边；右下角给堆叠数字留空间 | 直接适用，尤其 GUI | **当规格用** |
| [ExecutableItems Wiki：自定义物品贴图](https://splugins.net/docs/executableitems/questions-or-guides/custom-textures/custom-textures-1.21/general-items) | 自定义物品贴图 + 资源包结构（pickaxe 例子）、全小写命名、`pack_format` | 技术接入，不是美术 | 打包时参考 |
| MCBBS / 原版 bow 资料 | `bow_standby` + `bow_pulling_0/1/2` 四张图 + 四个模型 + `pulling` predicate；只改 standby 会出现“弓永远不拉”的 bug | 弓必须用 | **加弓时照做** |
| [Lospec Tutorials](https://lospec.com/pixel-art-tutorials) / [Palettes](https://lospec.com/palette-list) | 大量通用像素画教程；4000+ 调色板；明度/色相 ramp、轮廓、动画 | 通用技法/调色 | 选 palette/ramp 时用 |
| [Minecraft Wiki：Tutorial:Pixel art](https://minecraft.wiki/w/Tutorial:Pixel_art) | 用羊毛/混凝土等方块搭像素画 | 不适用 | 否 |

## 4. 四类武器的具体复用建议

### 剑

- 模板：Blockpixel Artist 的 sword；原版 `iron_sword` / `diamond_sword` 轮廓。
- 规则：16×16，斜握，左上高光，深色描边，右下 1px 留给堆叠数字。
- 本项目现状：已有 iron_rapier、venom_rapier、alloy_sword、blaze_sword、greatsword、storm_greatsword、dark_tachi 的 2D sprite。可以用 Blockpixel Artist 重画底稿，再用现有脚本上材质/动画。

### 镐

- 模板：pickaxe；原版 `iron_pickaxe` 的斜头 + 短柄。
- 16×16；头部 3–5 个明暗；柄用木色 ramp。
- 本项目目前没有镐；若新增，直接套模板。

### 斧

- 模板：axe；原版 `iron_axe` 的斧刃 + 柄。
- 16×16；刃口高光、斧背暗部。
- 本项目目前没有斧。

### 弓

- 模板：bow；但游戏内需要 4 张图：
  - `bow_standby.png`
  - `bow_pulling_0.png`
  - `bow_pulling_1.png`
  - `bow_pulling_2.png`
- 还需要 4 个 model（`bow.json`、`bow_pulling_0/1/2.json`）和 `overrides` 里的 `pulling` predicate。
- Blockpixel Artist 只能给 standby 图标；拉弓帧要自己衍生（缩短弓弦、箭上移、手臂姿势变化）。
- 本项目目前没有弓；若新增，先做 standby，再做 3 帧拉弓。
- Crossbow / trident 也有多状态纹理，思路相同。

### 镰刀 / 太刀等非原版武器

- 没有 canonical template；用 sword/axe 模板改轮廓，或继续用我们的 `art/make_*_sprites.py`。
- 32×32 大武器保持像素比例；不要在同一资产里混 16 和 64 分辨率。

## 5. 推荐落地方式

### 方案 A（最快）：装 Blockpixel Artist + 项目适配层

1. 复制 skill 到 `~/.agents/skills/blockpixel-artist`，安装 Python 依赖。
2. 加一个项目级 `art/weapon_style.md`（或 skill 的 reference），规定：
   - 16×16 / 32×32 / 64×64 的适用场景
   - 透明底
   - 右下 1px 留空
   - 每种材质 3–5 个明暗
   - 左上打光
   - 深色不间断描边
   - 调色板从现有武器取
   - 动画条垂直堆叠 + `.mcmeta` `{"animation":{"frametime":2}}`
3. 生成底稿后，用 `art/make_*_sprites.py` 或 Deterministic Pixel Art 精修/校验。
4. 输出到 `textures/item/<id>.png`，模型仍用 `item/handheld`；Java 属性、配方、2D 贴图保持不变。

### 方案 B（最稳）：自建 `minecraft-weapon-pixel-art` skill

把以下内容固化成 `SKILL.md` + scripts：

- 输入：武器类型 / 材质 / 尺寸 / 是否动画
- 模板：剑/镐/斧/弓 standby 的 16×16 轮廓（可参考 Blockpixel Artist，遵守 Apache-2.0）
- 规则：第 5 节的 checklist
- 校验：
  - PNG 尺寸
  - alpha bbox
  - 颜色数
  - 孤立像素
  - 动画帧高
  - `.mcmeta`
  - 右下留空
- 预览：100% + GUI slot + 手持缩放
- 输出：贴图 + model json + lang + recipe 占位

这样不依赖外部 skill 的 32/64 默认尺寸，也完全贴合本项目。

### 方案 C（回到 3D 时）

- Blockbench MCP + `blockbench-texturing` / `blockbench-flipbook-textures`
- 继续用 `_3d.json` / `_3d.png` 保留件
- 注意 1.21.1 的限制：
  - element 旋转只允许 -45 / -22.5 / 0 / 22.5 / 45
  - item model 必须直接包含 `elements`，不能只靠 parent 继承
  - 完整 `display` 块（第三人称/第一人称/GUI/ground/fixed/head）

## 6. 核验说明

- 四个 GitHub 项目已通过 WebFetch 读取仓库首页核实：Blockpixel Artist、Deterministic Pixel Art、Blockbench MCP project、Texel MCP。
- 教程链接来自搜索结果；Fumora、MiemieMethod、ResourcePack AI、Blockbench、Lospec、Minecraft Wiki 的页面标题与内容摘要已核对，未逐页全文抓取。
- 本地 skill 扫描范围：`C:\Users\Administrator\.agents\skills`，仅 `minecraft-fabric-mod` 命中 Minecraft/像素关键词。
- Blockpixel Artist 的 ZCode 安装路径是建议方案，**尚未实际安装验证**。

## 7. 落地结果

本报告的外部方案仅作调研记录。项目最终采用**固定 32×32 像素画板**，已固化为本机 skill：

`C:\Users\Administrator\.agents\skills\minecraft-weapon-pixel-art`

它包含 `SKILL.md`、`scripts/board.py`（init/render/validate/review）、材质调色板、长剑/军刀/战斧比例模板，以及翡翠战斧校准例。Blockpixel Artist、Deterministic Pixel Art、Texel MCP 的实验 clone 已清理；`minecraft-fabric-mod` 保留，用于把模型接进 Fabric。
