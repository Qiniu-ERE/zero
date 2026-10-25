# 坦克大战 2026 · 商店页材料（Steam / Microsoft Store）

> [v5.0 规划](PLAN.md) P2 的准备工作：账号注册之前先把文案、素材规格、预告片脚本准备好，注册后直接填。**名字已定**：中文 **坦克大战 2026**，英文 **Brickline Tanks**（2026-10-25 查过，没有同名游戏；“Tank Battle 2026”在 itch.io 上已有人使用，所以不用）。
>
> 规格数字来自 Steamworks 的图片素材文档，**上传前以后台显示的要求为准**。商店文案不提原作名称（[PLATFORMS.md 第七节](PLATFORMS.md#七知识产权上架前必须处理)）。

## 一、基本信息

| 项目 | 内容 |
|---|---|
| 名称 | 中文：坦克大战 2026；英文：Brickline Tanks |
| 类型 | 动作、街机、复古 |
| 开发者 / 发行商 | 待定（个人或公司名，和 Steamworks 账号一致） |
| 价格 | $4.99，区域定价按 Valve 建议（[MONETIZATION.md 第二节](MONETIZATION.md#二steam-和-microsoft-store买断制)） |
| 语言 | 简体中文、英语（界面、字幕；没有配音） |
| 平台 | Windows、macOS（Apple 芯片）、Linux / Steam Deck |
| 玩家人数 | 单人；本地双人合作（同一键盘或两只手柄）；Remote Play Together |
| 手柄 | 做完手柄支持后勾“完全支持”；编辑器不能用手柄时勾“部分支持”（[EXPERIENCE.md 3.3](EXPERIENCE.md#33-商店页要如实填写)） |
| 云存档 | Steam Auto-Cloud（[EXPERIENCE.md 3.4](EXPERIENCE.md#34-steam-云存档不用接-sdk)） |
| 成人内容 | 无；卡通坦克爆炸，无血腥 |
| AI 内容披露 | 游戏里的美术由代码生成、音效由程序合成、文字由人编写，按 2026 年规则不需要披露；宣传素材如果用了 AI 生成的图要披露（[PLATFORMS.md 2.1](PLATFORMS.md#21-门槛公开资料)） |

## 二、标签（按重要性）

本地合作、同屏 / 分屏、复古、街机、像素图形、关卡编辑器、2D、俯视角射击、坦克、休闲、单人、中文

勾选：Local Co-op、Shared/Split Screen Co-op、Remote Play Together、Steam Cloud（做完后）、Full / Partial Controller Support。

## 三、商店文案

### 3.1 简短描述（Steam 限 300 字符以内）

**中文**：
> 守住老鹰，打穿砖墙！经典坦克玩法重铸：8 个关卡、本地双人合作，还能自己画地图马上试玩。现代“微缩战场”画风和复古像素风一键切换。

**English**:
> Guard the eagle, blast through the bricks! A classic tank shooter reforged: 8 handcrafted stages, local two-player co-op, and a map editor that lets you draw a level and play it in seconds. Switch between a modern miniature look and retro pixel art at any time.

### 3.2 详细描述

**中文**：

> **和朋友一起守住老鹰**
> 敌人的坦克从三个方向涌来，你的任务只有一个：守住基地里的老鹰。砖墙可以打穿，钢墙挡得住子弹，草丛能藏身，水面过不去——利用地形，消灭一关的 20 辆敌人。
>
> **8 个关卡，每关都不一样**
> 钢铁峡谷、水乡迷宫、丛林伏击、钢铁堡垒、砖城巷战、闪电突袭、双子要塞、最终决战。敌人的数量、速度和火力逐关变化。
>
> **本地双人合作**
> 同一个键盘或两只手柄，两个人各开一辆坦克。朋友不在身边？Steam 的远程同乐让他不用购买也能在线加入。
>
> **自己做地图**
> 用鼠标画砖墙、钢墙、水面和草丛，编辑器会实时检查地图能不能玩，画完马上试玩。
>
> **两种画风**
> 现代“微缩战场”画风，或者 1985 年的像素风，随时一键切换。支持中文和英文。

**English**:

> **Guard the eagle together**
> Enemy tanks pour in from three directions, and you have one job: protect the eagle at your base. Bricks can be blasted, steel stops bullets, grass hides you, water blocks the way — use the terrain and destroy all 20 enemy tanks in each stage.
>
> **8 stages, each one different**
> Steel Canyon, River Maze, Jungle Ambush, Iron Fortress, Brick City, Blitz, Twin Forts and Final Stand. Enemy numbers, speed and firepower change from stage to stage.
>
> **Local two-player co-op**
> One keyboard or two gamepads, one tank each. Friend not around? Steam Remote Play Together lets them join online without owning the game.
>
> **Make your own maps**
> Paint bricks, steel, water and grass with the mouse. The editor checks in real time whether the map is playable, and you can test it right away.
>
> **Two art styles**
> A modern "miniature battlefield" look or 1985-style pixel art — switch with one key. Chinese and English supported.

（关卡英文名和游戏里 `strings.py` 的英文文案一致；改名 PR 合入后再核对一次。）

### 3.3 Microsoft Store

同一套文案。注意 Microsoft Store 要求在哪些地区发售，就要把商店页翻译成那些地区要求的语言（[EXPERIENCE.md 2.4](EXPERIENCE.md#24-本地化)）：v5 先只选英语和中文地区。描述里要写明输入设备：“键盘；手柄（如支持）；鼠标（地图编辑器）”。

## 四、图片素材

| 素材 | 尺寸（像素） | 内容 | 谁做 |
|---|---|---|---|
| 主胶囊图（Main Capsule） | 1232×706 | 插画风：两辆坦克守着老鹰，砖墙、Logo | 外包画师（[CASHFLOW.md](CASHFLOW.md) 预算约 $800 含全套胶囊图） |
| 页头胶囊图（Header Capsule） | 920×430 | 同上，构图横向 | 外包 |
| 小胶囊图（Small Capsule） | 462×174 | **Logo 为主**，小尺寸下也要能看清名字 | 外包 |
| 竖版胶囊图（Vertical Capsule） | 748×896 | 竖构图 | 外包 |
| 库存胶囊图（Library Capsule） | 600×900 | 竖构图 | 外包 |
| 库存主视觉（Library Hero） | 3840×1240 | 无文字背景 | 外包 |
| 库存 Logo | 透明背景 PNG | Brickline Tanks / 坦克大战 2026 | 外包，或由 `build.py` 用现有字形生成 |
| 截图 | 1920×1080，至少 5 张 | 见下表 | 游戏内截取 |
| 页面背景（可选） | 1438×810 | — | 外包 |

截图清单（游戏是 4:3，截图两侧用装饰面板或战场背景补成 16:9）：

1. 单人战斗：第 2 关，砖墙被打穿、爆炸瞬间（现代画风）
2. 双人合作：两辆坦克一起守老鹰
3. 地图编辑器：正在画对称地图，检查提示为“可以玩”
4. 两种画风对比：同一画面的现代风和像素风（拼成一张）
5. 最终关：敌人从三个方向进攻
6. 结算画面（商店版去掉广告和金币 ×2 之后再截）

**截图要在商店版（去掉模拟广告、改名之后）里截**，不能出现“广告”“模拟广告位”和 BATTLE CITY。

## 五、预告片脚本（30 秒）

| 时间 | 画面 | 字幕（中 / 英） |
|---|---|---|
| 0~2 秒 | **直接进对局**：敌人涌来，砖墙被打穿 | （无字幕，玩法先行） |
| 2~6 秒 | 两辆坦克一起守老鹰，爆炸连发 | 和朋友一起守住老鹰 / Guard the eagle together |
| 6~10 秒 | 快速切换 8 个关卡的开局画面 | 8 个关卡 / 8 stages |
| 10~16 秒 | 编辑器里画地图 → 点试玩 → 进入战斗 | 自己画地图，马上试玩 / Draw a map, play it now |
| 16~20 秒 | 按 T 切换画风：现代风 ↔ 像素风 | 两种画风，一键切换 / Two art styles |
| 20~26 秒 | 最终关激战，基地险些失守，最后一辆敌人被击毁 | — |
| 26~30 秒 | Logo + “加入愿望单” | 坦克大战 2026 · Brickline Tanks / Wishlist now |

录制：用路演演示模式和 `tools/dev/record_demo.sh` 录素材，剪辑加字幕；**录制前先确认商店版的改名和去广告已经合入**。现在的录屏器会压缩音频，预告片的音效要另外配。

## 六、注册后要做的事（按顺序）

1. 注册 Steamworks（个人或公司），交 $100，填税务表（W-8BEN：非美国人，纳税人识别号填身份证号，申请中美税收协定 10%）和银行信息（[CASHFLOW.md 2.1](CASHFLOW.md#21-steam)）。
2. 新建应用，填本文第一、二、三节；上传第四节素材和第五节预告片。
3. 勾选本地合作、同屏、Remote Play Together；填内容问卷（德国区需要）。
4. 提交商店页审核，通过后发布 **Coming Soon** 页面。
5. 报名 Couch Co-Op Fest（2027-02-08）和 Next Fest（2027-02-22，试玩版 2027-01-18 前提交审核）（[MARKETING.md 第三节](MARKETING.md#三时间线按-2027-年春季发售倒排)）。
6. Microsoft Store：注册（个人免费）→ 确认普通 Win32 游戏能否只用 MSIX 提交 → 填同一套文案（只选英语和中文地区）。
