# 坦克大战 2026 · XBuilder 复刻重铸版

[x.qiniu.com](https://x.qiniu.com) | [下载安装包](https://github.com/Qiniu-ERE/zero/releases/latest) | [下载 .xbp](TankBattle.xbp) | [演示视频](docs/demo/tankbattle-v3-demo.mp4) | [快速开始](#快速开始) | [玩法](#玩法) | [架构文档](docs/ARCHITECTURE.md) | [设计方案](docs/v2/DESIGN.md) | [v3.0 规划](docs/v3/PLAN.md) | [更新记录](CHANGELOG.md) | [XGo](https://xgo.dev) | [spx 引擎](https://github.com/goplus/spx)

[![1024 HACKATHON](https://img.shields.io/badge/1024_HACKATHON-第五届-e8c020)](#)
[![Made with XBuilder](https://img.shields.io/badge/made_with-XBuilder-b4521e)](https://x.qiniu.com)
[![Language XGo](https://img.shields.io/badge/language-XGo-0a7bbb)](https://xgo.dev)
[![Engine spx](https://img.shields.io/badge/engine-spx_4.0-555)](https://github.com/goplus/spx)
[![Battle City 1985](https://img.shields.io/badge/remake_of-Battle_City_1985-red)](#素材与版权说明)

> 🏆 **第五届 1024 HACKATHON 参赛项目** · 这是一个 Builder 的时代 —— AI 放大执行，我们撬动价值

用 [XBuilder](https://x.qiniu.com) 把 1985 年的 FC 经典《坦克大战》重做成 2026 年的样子：保留“守住老鹰、打穿砖墙”的玩法内核，换上现代画风，支持中英文，并且设计了一套**干净、不打扰玩家**的广告商业化方案。

v3.0 加入了 **8 个关卡、双人合作和自己做地图**，并打包成 **Windows / macOS / Linux / 网页版（PWA）/ Android / iOS** 安装包，在 [Releases](https://github.com/Qiniu-ERE/zero/releases/latest) 下载。

*Talk is cheap, show me what you build.*

![坦克大战 2026 演示](docs/demo/tankbattle-v3.gif)

> 动图是 v3.0 的新内容（新关卡 → 双人合作 → 暂停菜单 → 编辑器里画地图并试玩），截自[完整演示视频](docs/demo/tankbattle-v3-demo.mp4)（约 1 分半，无声）。视频由 spx 引擎实际运行录制，用的是游戏内置的**路演演示模式**（主页按 P）：玩家坦克自动驾驶，脚本依次展示画风切换、中英文切换、复活、激励视频广告和结算，然后是 v3.0 的新关卡、双人合作、暂停菜单和自己做地图（在编辑器里对称画出一张“河流城堡”并试玩）。v2.0 的演示视频见 [tankbattle-v2-demo.mp4](docs/demo/tankbattle-v2-demo.mp4)。

| 主页 + 横幅广告 | 对局（English） | 复活询问（激励视频） | 结算（金币翻倍） |
|---|---|---|---|
| ![](docs/v2/screens/home-zh.png) | ![](docs/v2/screens/hud-en-modern.png) | ![](docs/v2/screens/revive-zh.png) | ![](docs/v2/screens/result-win-doubled-zh.png) |

## 下载安装

到仓库的 [Releases](https://github.com/Qiniu-ERE/zero/releases) 下载对应平台的安装包（每个包里都有安装说明）：

| 平台 | 安装包 |
|---|---|
| Windows 10 / 11 | `TankBattle-<版本>-windows-x64.zip`，解压后双击 `TankBattle.exe` |
| macOS（Apple 芯片） | `TankBattle-<版本>-macos-arm64.zip`，第一次右键 → 打开 |
| Linux | `TankBattle-<版本>-linux-x64.tar.gz` |
| iPhone / 安卓 / 浏览器 | `TankBattle-<版本>-web.zip`：网页版（PWA），带触屏虚拟按键，放到 HTTPS 网站后手机“添加到主屏幕” |
| Android | `TankBattle-<版本>-android.apk`，直接安装 |
| iPhone / iPad | `TankBattle-<版本>-ios-unsigned.ipa`，用 Sideloadly / AltStore 签名安装 |

安装包由 GitHub Actions 自动打包，打包方法见 [跨平台文档](docs/v3/CROSS_PLATFORM.md#七实现结果)。

## 快速开始

### 方式一：在 XBuilder 里运行（推荐，零安装）

1. 下载本仓库中的 [`TankBattle.xbp`](TankBattle.xbp)
2. 打开 <https://x.qiniu.com> 并登录
3. 点击「文件 → 导入」，选择 `TankBattle.xbp`
4. 点击右上角的「运行」按钮

### 方式二：在本地用 spx 运行

```sh
# 1. 安装 spx 运行时（需要 Git、Make、Go，详见 goplus/spx 的 README）
git clone https://github.com/goplus/spx.git && cd spx && make setup

# 2. 运行游戏
cd /path/to/zero/TankBattle
spx run .
```

## 玩法

| 按键 | 作用 |
|---|---|
| Enter / 空格 / 点击「开始战役」 | 从第 1 关开始 |
| 1 ~ 8 | 主页：直接进入对应关卡 |
| E / 点击「自己做地图」 | 主页：地图编辑器。鼠标点击或拖动绘制；1~5 选工具，M 对称，Enter 试玩，P 双人试玩，R 随机起点，K 复制关卡，C 清空，S 保存，Esc 返回 |
| C / 点击「双人合作」 | 主页：双人合作。1P：WASD 移动、J / 空格开火；2P：方向键移动、Enter 开火 |
| 方向键 / WASD | 移动坦克 |
| 空格 / J | 开火 |
| T | 切换 2026 现代画风 / 1985 经典像素风 |
| L / 点击右上角「中 \| EN」 | 切换中文 / English |
| J / Enter | 复活询问、结算时：看视频（激励广告） |
| Esc / 点击顶栏的 Ⅱ | 对局中：暂停（菜单里可以继续、重新开始本关、返回主页；自制地图试玩时是返回编辑）；复活询问时：放弃 |
| R / H | 结算时：下一关（胜利）或再来一局（战败）/ 回到主页 |
| P | 主页：路演演示模式（无人值守自动展示） |

- **目标**：每关消灭 20 辆敌方坦克，同时保护好底部的老鹰基地。共 **8 关**，得分会带到下一关；战败后重打本关。
- **失败**：基地被击中，或者生命用完。**每局第一次战败**时，可以选择看一段视频复活（修复基地，额外 1 条命）。
- **地形**：砖墙要打两下才会碎；钢墙打不碎；**水面**坦克过不去、子弹能飞过；**草丛**能把坦克藏起来。
- 和原版一样，屏幕上同时只能有 **1 发**自己的子弹；子弹迎面相撞会互相抵消；出生时有 3 秒保护。
- **结算**：按得分折算金币，胜利额外加 100；可以看视频把金币翻倍。

| 敌人 | 外观（现代 / 经典） | 特点 | 分数 |
|---|---|---|---|
| 普通坦克 | 红色 / 银色 | 速度中等 | 100 |
| 快速坦克 | 蓝色 / 蓝色 | 速度快 | 200 |
| 重型坦克 | 绿色 / 绿色 | 要打 3 发才会被消灭 | 400 |

| 关卡 | 特点 | 敌军配置 |
|---|---|---|
| 1 钢铁峡谷 | 经典布局，砖墙夹道 | 标准 |
| 2 水乡迷宫 | 大片水面分割战场，坦克要绕路，子弹能隔河对射 | 标准 |
| 3 丛林伏击 | 草丛遍地，敌人藏在草里 | 快速坦克占 60% |
| 4 钢铁堡垒 | 钢墙林立，射击角度很少 | 重型坦克占 50% |
| 5 砖城巷战 | 密集的砖墙街区，要自己打出一条路 | 出兵更快 |
| 6 闪电突袭 | 开阔地，几乎无处可躲 | 快速坦克占 70%，出兵最快，场上最多 5 辆 |
| 7 双子要塞 | 左右两座砖堡，中间一道水渠，交叉火力 | 快速 50%、重型 30%，场上最多 5 辆 |
| 8 最终决战 | 水面、草丛、钢墙都有，基地两侧有钢墙 | 重型和快速各 45%，每 1.3 秒出兵，场上最多 5 辆 |

![8 个关卡](docs/v3/stages/stages.png)

## v3.0 做了什么

| 方向 | 内容 | 文档 |
|---|---|---|
| 关卡 | 从 1 关扩展到 8 关，每关地形和敌军配置不同；主页按 1~8 选关，胜利后进入下一关，第 8 关胜利显示「全部通关」 | [规划总览](docs/v3/PLAN.md) |
| 双人合作 | 主页按 C：同一键盘两人各开一辆坦克（1P WASD + J，2P 方向键 + Enter），一起守基地 | [COOP.md](docs/v3/COOP.md) |
| 自己做地图 | 主页按 E：鼠标或手指画地图，出生点和基地锁定，实时检查能不能玩，马上试玩（也能双人试玩）；PC 版可以保存 | [MAP_EDITOR.md](docs/v3/MAP_EDITOR.md) |
| 跨平台 | 推送 `v*` 标签后 GitHub Actions 打出六个平台的安装包并发布 Release；网页版带触屏虚拟按键（PWA），手机 App 带触屏模式 | [CROSS_PLATFORM.md](docs/v3/CROSS_PLATFORM.md) |
| 暂停与退出（v3.0.1） | 对局中按 Esc 或点顶栏 Ⅱ：继续 / 重新开始本关 / 返回主页（试玩自制地图时返回编辑） | [更新记录](CHANGELOG.md) |

| 8 个关卡 | 双人合作 | 自己做地图 | 手机网页版（虚拟按键） |
|---|---|---|---|
| ![](docs/v3/stages/stage-4.png) | ![](docs/v3/coop/coop-zh.png) | ![](docs/v3/editor/editor-zh.png) | ![](docs/v3/release/web-phone-play.png) |

## v2.0 做了什么

| 方向 | 内容 |
|---|---|
| 画面 | 「微缩战场」现代画风（伪 3D 墙体、发光子弹、爆炸粒子、暗角），默认开启；按 T 回到 1985 像素风 |
| 界面 | 全新 HUD：关卡名、敌军剩余、得分（千分位）、最高分、生命、按键提示、提示条 |
| 语言 | 中文 / English 随时切换。所有文字都被**烘焙成矢量路径**，运行时不依赖字体，从根本上杜绝乱码 |
| 玩法 | 主页、复活机制、结算与金币、草丛和水面地形 |
| 商业化 | 4 个广告位全部在战场之外：主页横幅、原生广告卡、复活激励视频、结算金币 ×2 激励视频。统一使用 Google 风格（「广告」标识、AdChoices、关闭按钮、Google 蓝按钮） |
| 路演 | 路演演示模式（P）：自动驾驶 + 脚本，在展台上无人值守地循环展示 |

广告位目前用「七牛云 · 广告位招商」的文案做模拟展示。广告的设计原则和收入结构见[设计方案](docs/v2/DESIGN.md#四广告干净不打扰)。目前的广告是**游戏内的模拟广告位**（画面上标明了「模拟广告位」）；正式上线的接入方案见[架构文档](docs/ARCHITECTURE.md#8-广告)。

## 文档

| 文档 | 内容 |
|---|---|
| [架构文档](docs/ARCHITECTURE.md) | 模块规格、消息表、流程状态机、资源管线、spx 解释器的限制与对策、测试方法、分工 |
| [设计方案](docs/v2/DESIGN.md) | 2026 年的玩法、画风、商业化设计，附中英文效果图 |
| [演示视频](docs/demo/tankbattle-v3-demo.mp4) | 约 1 分半的完整流程演示（v3.0；[v2.0 版](docs/demo/tankbattle-v2-demo.mp4)） |
| [更新记录](CHANGELOG.md) | 每个版本改了什么（v0 → v2.0.0 → v3.0.0 → v3.0.1） |
| [v3.0 规划](docs/v3/PLAN.md) | 8 个关卡（已实现）、[自己做地图](docs/v3/MAP_EDITOR.md)、[双人合作](docs/v3/COOP.md)、[跨平台运行](docs/v3/CROSS_PLATFORM.md)（iPhone / Android / Windows / Mac）的方案与可行性评估 |

## 项目结构

```
TankBattle.xbp            # 可直接导入 XBuilder 的项目包（tools/package_xbp.sh 生成）
TankBattle/               # 游戏工程（XGo / spx）
├── main.spx              # 舞台：地图、规则、流程状态机、HUD 布局、路演演示
├── Player.spx            # 玩家坦克：键盘控制 / 自动驾驶、开火、引擎声
├── Enemy.spx             # 敌人坦克：随机转向、偏向基地、定时开火
├── PBullet.spx / EBullet.spx   # 玩家子弹 / 敌人子弹
├── Boom.spx              # 爆炸动画
├── Tile.spx              # 地图格子：砖墙、钢墙、水面、草丛、基地
├── UI.spx                # 所有界面元素：标签、数字、图标、提示条、广告位、弹窗画面
└── assets/               # 造型（SVG，大部分由生成器产出）、音效（WAV）
tools/
├── assets/               # 美术与文案生成器：build.py、textpath.py、strings.py（中英文案表）
├── dev/                  # 本地截图、录制演示视频的脚本
├── levels/check.py       # 关卡地图检查：出生点、基地、连通性
├── export/               # 各平台打包：setup_spx.sh、build.sh、网页版外壳 web/、安装说明
└── package_xbp.sh        # 打包 TankBattle.xbp
docs/
├── ARCHITECTURE.md       # 架构文档
├── v2/                   # 设计方案、效果图、实机截图
├── v3/                   # v3.0 规划：PLAN.md 总览、MAP_EDITOR.md、COOP.md、CROSS_PLATFORM.md，效果图和实测截图
└── demo/                 # 演示视频和动图
```

## 开发

```sh
# 修改了文案（tools/assets/strings.py）或美术代码之后，重新生成造型
pip install -r tools/assets/requirements.txt
python3 tools/assets/build.py

# 修改了关卡地图（main.spx 的 levelMap）之后，检查地图是否合法
python3 tools/levels/check.py

# 本地运行
cd TankBattle && spx run .

# 重新打包 .xbp，导入 XBuilder
./tools/package_xbp.sh

# 打各平台的安装包（第一次先运行 setup_spx.sh）
tools/export/setup_spx.sh web
tools/export/build.sh desktop   # 或 web / android / ios

# 发布：推送 v* 标签，GitHub Actions 打全部平台并创建 Release
git tag v3.0.0 && git push origin v3.0.0

# 重新录制演示视频（需要 ffmpeg）
./tools/dev/record_demo.sh
```

版本标签：`v0` 是导入的基础版本（初版坦克大战），之后的提交都是在它之上新增的内容；`v2.0.0`、`v3.0.0` 是两次发布。

开发规范：每次改动都通过 Pull Request 合入，详见[架构文档的开发流程](docs/ARCHITECTURE.md#11-开发流程与分工)。

## 代码里的教学要点

| 知识点 | 在哪里 | 说明 |
|---|---|---|
| 数组 | `main.spx` 中的 `grid`、`levelMap()` | 地图是一个 13×13 的数组：0 空地、1 砖墙、2 钢墙、3 裂开的砖墙、4 水面、5 草丛、9 基地 |
| 克隆 | `Tile.build`、`Enemy.spawn`、`UI.label` | 先设置好“模板精灵”的变量，再调用 `clone`；克隆体在 `onCloned` 里开始工作 |
| 消息 | `broadcast` / `onMsg` | 例如砖墙被打中后广播 `"gridChanged"`，每块砖自己对照 `grid` 更新 |
| 状态机 | `main.spx` 中的 `state` | 主页 → 对局 → 复活询问 → 播放广告 → 结算，每个按键在不同状态下含义不同 |
| 按帧移动 | `waitNextFrame` + `deltaTime` | 移动距离 = 速度 × 每帧时间，在快电脑和慢电脑上速度一样 |
| 碰撞 | `tankBlocked`、`bulletHit` | 撞墙通过查格子数组判断；坦克之间、子弹之间用 `touching` 判断 |
| 简单 AI | `Enemy.spx` 的 `pickFace`、`main.spx` 的 `autopilotDir` | 敌人随机转向并偏向基地；自动驾驶先和最近的敌人对齐，再开火 |
| 逻辑与表现分离 | `look()`、`langCode()` | 画风和语言都只是一个变量：造型按名字加 `_m` 或 `_zh` / `_en` 后缀切换，游戏逻辑一行不改 |

## 素材与版权说明

- **图片**：所有造型和背景都是原创。v2 的现代画风造型、界面和文字由 `tools/assets/build.py` 用代码生成。
- **音效**：经典版用程序模拟 FC 音源合成，现代版用滤波噪声、低频冲击和铜管音色合成，全部原创，**没有**使用 Namco 原版的音乐或采样。
- **字体**：界面文字由 [Noto Sans SC](https://github.com/google/fonts/tree/main/ofl/notosanssc)（SIL Open Font License 1.1）的字形轮廓生成，游戏运行时不再携带字体文件。
