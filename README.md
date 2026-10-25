# 坦克大战 2026 · XBuilder 复刻重铸版

**[下载安装包](https://github.com/Qiniu-ERE/zero/releases/latest)** · [下载 .xbp](TankBattle.xbp) · [演示视频](docs/demo/tankbattle-v3-demo.mp4) · [快速开始](#快速开始) · [玩法](#玩法) · [更新记录](CHANGELOG.md)

[架构文档](docs/ARCHITECTURE.md) · [v2.0 设计方案](docs/v2/DESIGN.md) · [v3.0 规划](docs/v3/PLAN.md) · [XBuilder](https://x.qiniu.com)

[![1024 HACKATHON](https://img.shields.io/badge/1024_HACKATHON-第五届-e8c020)](#)
[![Made with XBuilder](https://img.shields.io/badge/made_with-XBuilder-b4521e)](https://x.qiniu.com)
[![Language XGo](https://img.shields.io/badge/language-XGo-0a7bbb)](https://xgo.dev)
[![Engine spx](https://img.shields.io/badge/engine-spx_4.0-555)](https://github.com/goplus/spx)
[![Battle City 1985](https://img.shields.io/badge/remake_of-Battle_City_1985-red)](#素材与版权说明)

> 🏆 **第五届 1024 HACKATHON 参赛项目** · 这是一个 Builder 的时代 —— AI 放大执行，我们撬动价值

用 [XBuilder](https://x.qiniu.com) 把 1985 年的 FC 经典《坦克大战》重做成 2026 年的样子：保留“守住老鹰、打穿砖墙”的玩法内核，换上现代画风，支持中英文，并设计了一套**干净、不打扰玩家**的广告方案。

v3.0 加入了 **8 个关卡、双人合作、自己做地图**，并打包成 **Windows / macOS / Linux / 网页版 / Android / iOS** 安装包。

*Talk is cheap, show me what you build.*

![坦克大战 2026 演示](docs/demo/tankbattle-v3.gif)

> 动图：新关卡 → 双人合作 → 暂停菜单 → 编辑器里画地图并试玩。截自[完整演示视频](docs/demo/tankbattle-v3-demo.mp4)（约 1 分半，无声，[v2.0 版](docs/demo/tankbattle-v2-demo.mp4)），由游戏内置的**路演演示模式**（主页按 P）在真实引擎里录制。

| 主页 | 对局（English） | 复活（激励视频） | 结算（金币翻倍） |
|---|---|---|---|
| ![](docs/v2/screens/home-zh.png) | ![](docs/v2/screens/hud-en-modern.png) | ![](docs/v2/screens/revive-zh.png) | ![](docs/v2/screens/result-win-doubled-zh.png) |

## 下载安装

到 [Releases](https://github.com/Qiniu-ERE/zero/releases/latest) 下载，文件名是 `TankBattle-版本号-平台`，每个包里都有 `README.txt` 安装说明。

| 平台 | 文件 | 怎么打开 |
|---|---|---|
| Windows 10 / 11 | `windows-x64.zip` | 双击 `TankBattle.exe` |
| macOS（Apple 芯片） | `macos-arm64.zip` | 第一次右键 → 打开 |
| Linux | `linux-x64.tar.gz` | 运行 `./TankBattle` |
| 网页版 / 手机浏览器 | `web.zip` | 放到 HTTPS 网站，手机“添加到主屏幕” |
| Android | `android.apk` | 直接安装 |
| iPhone / iPad | `ios-unsigned.ipa` | 用 Sideloadly / AltStore 签名安装 |

安装包由 GitHub Actions 自动打包，详见[跨平台文档](docs/v3/CROSS_PLATFORM.md#七实现结果)。

## 快速开始

### 方式一：在 XBuilder 里运行（零安装）

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

**主页**

| 按键 | 作用 |
|---|---|
| Enter / 空格 | 从第 1 关开始 |
| 1 ~ 8 | 直接进入对应关卡 |
| C | 双人合作 |
| E | 自己做地图 |
| P | 路演演示模式（无人值守） |

**对局**

| 按键 | 作用 |
|---|---|
| 方向键 / WASD | 移动 |
| 空格 / J | 开火 |
| Esc / 顶栏 Ⅱ | 暂停：继续、重新开始、返回主页 |
| T | 切换现代画风 / 1985 像素风 |
| L / 右上角「中 \| EN」 | 切换中文 / English |
| 双人合作 | 1P：WASD + J；2P：方向键 + Enter |

**地图编辑器**

| 按键 | 作用 |
|---|---|
| 鼠标点击 / 拖动 | 画格子（触屏也可以） |
| 1 ~ 5 | 砖墙、钢墙、水面、草丛、橡皮擦 |
| M | 对称绘制开关 |
| Enter / P | 试玩 / 双人试玩 |
| R / K / C | 随机起点 / 复制关卡 / 清空 |
| S / Esc | 保存（PC 版）/ 返回主页 |

**弹窗**

| 画面 | 按键 |
|---|---|
| 复活询问 | J / Enter 看视频复活，Esc 放弃 |
| 结算 | J 金币翻倍，R 下一关 / 再来一局，H 主页 |
| 暂停 | Esc / Enter 继续，R 重来，H 主页（试玩时回编辑） |

- **目标**：每关消灭 20 辆敌方坦克，保护好底部的老鹰。共 **8 关**，得分带到下一关；战败后重打本关。
- **失败**：基地被击中（自己的子弹也算），或者生命用完。**每局第一次战败**可以看视频复活一次。
- **地形**：砖墙打两下才碎；钢墙打不碎；**水面**坦克过不去、子弹能飞过；**草丛**能藏身。
- 和原版一样，同时只能有 **1 发**自己的子弹；子弹相撞会互相抵消；出生时有 3 秒保护。
- **结算**：按本关得分折算金币，胜利额外加 100；可以看视频把金币翻倍。

| 敌人 | 现代 / 经典 | 特点 | 分数 |
|---|---|---|---|
| 普通坦克 | 红 / 银 | 速度中等 | 100 |
| 快速坦克 | 蓝 / 蓝 | 速度快 | 200 |
| 重型坦克 | 绿 / 绿 | 要打 3 发 | 400 |

| 关卡 | 地形 | 敌军 |
|---|---|---|
| 1 钢铁峡谷 | 砖墙夹道 | 标准 |
| 2 水乡迷宫 | 水面分割，隔河对射 | 标准 |
| 3 丛林伏击 | 草丛遍地 | 快速 60% |
| 4 钢铁堡垒 | 钢墙林立 | 重型 50% |
| 5 砖城巷战 | 密集砖墙街区 | 出兵更快 |
| 6 闪电突袭 | 开阔地 | 快速 70%，最多 5 辆 |
| 7 双子要塞 | 两座砖堡夹水渠 | 快速 50%，最多 5 辆 |
| 8 最终决战 | 水、草、钢都有 | 重型、快速各 45% |

![8 个关卡](docs/v3/stages/stages.png)

## v3.0 做了什么

| 方向 | 内容 | 文档 |
|---|---|---|
| 关卡 | 8 关、选关、下一关、全部通关 | [PLAN](docs/v3/PLAN.md) |
| 双人合作 | 同一键盘两人一起守基地 | [COOP](docs/v3/COOP.md) |
| 自己做地图 | 画地图、实时检查、马上试玩 | [MAP_EDITOR](docs/v3/MAP_EDITOR.md) |
| 跨平台 | 六个平台的安装包，自动发布 | [CROSS_PLATFORM](docs/v3/CROSS_PLATFORM.md) |
| 暂停（v3.0.1） | 对局中随时继续、重来或退出 | [CHANGELOG](CHANGELOG.md) |

| 8 个关卡 | 双人合作 | 自己做地图 | 手机网页版 |
|---|---|---|---|
| ![](docs/v3/stages/stage-4.png) | ![](docs/v3/coop/coop-zh.png) | ![](docs/v3/editor/editor-zh.png) | ![](docs/v3/release/web-phone-play.png) |

## v2.0 做了什么

| 方向 | 内容 |
|---|---|
| 画面 | 「微缩战场」现代画风，按 T 回到 1985 像素风 |
| 界面 | 新 HUD：关卡名、敌军剩余、得分、生命、提示条 |
| 语言 | 中英文切换；文字烘焙成矢量路径，不会乱码 |
| 玩法 | 主页、复活、结算与金币、草丛和水面 |
| 商业化 | 4 个广告位，全部在战场之外 |
| 路演 | 路演演示模式（P），展台无人值守循环 |

广告位目前是**游戏内的模拟广告位**（画面上标明了“模拟广告位”），用「七牛云 · 广告位招商」的文案展示。设计原则见[设计方案](docs/v2/DESIGN.md#四广告干净不打扰)，正式接入方案见[架构文档](docs/ARCHITECTURE.md#8-广告)。

## 文档

| 文档 | 内容 |
|---|---|
| [架构文档](docs/ARCHITECTURE.md) | 模块规格、消息表、状态机、解释器限制、分工 |
| [更新记录](CHANGELOG.md) | v0 → v2.0.0 → v3.0.0 → v3.0.x |
| [v3.0 规划](docs/v3/PLAN.md) | 关卡、编辑器、双人、跨平台的方案和结果 |
| [v4.0 规划](docs/v4/PLAN.md) | 测试与质量：自动化测试、覆盖率、PR 自动测试，[测试方案](docs/v4/TEST_PLAN.md) |
| [跨平台](docs/v3/CROSS_PLATFORM.md) | 打包方法、实测截图、限制 |
| [微信小游戏](docs/v3/WECHAT_MINIGAME.md) | 可行性评估 |
| [v2.0 设计方案](docs/v2/DESIGN.md) | 玩法、画风、商业化设计和效果图 |
| [演示视频](docs/demo/tankbattle-v3-demo.mp4) | v3.0 完整流程（[v2.0 版](docs/demo/tankbattle-v2-demo.mp4)） |

## 项目结构

```
TankBattle.xbp            # 可直接导入 XBuilder 的项目包（tools/package_xbp.sh 生成）
TankBattle/               # 游戏工程（XGo / spx）
├── main.spx              # 舞台：地图、规则、流程、双人、编辑器、暂停、路演演示
├── Player.spx            # 玩家坦克（1P；双人时克隆出 2P）
├── Enemy.spx             # 敌人坦克
├── PBullet.spx / EBullet.spx   # 玩家子弹 / 敌人子弹
├── Boom.spx              # 爆炸动画
├── Tile.spx              # 地图格子：砖墙、钢墙、水面、草丛、基地
├── UI.spx                # 所有界面元素
└── assets/               # 造型（大部分由生成器产出）、音效
tools/
├── assets/               # 美术与文案生成器：build.py、strings.py
├── levels/check.py       # 关卡地图检查
├── export/               # 各平台打包、网页版外壳、安装说明
├── dev/                  # 截图、录制演示视频
└── package_xbp.sh        # 打包 TankBattle.xbp
docs/
├── ARCHITECTURE.md       # 架构文档
├── v2/                   # v2.0 设计方案、截图
├── v3/                   # v3.0 规划和各方向的文档、截图
├── v4/                   # v4.0 规划：PLAN.md 总览、TEST_PLAN.md 测试方案
└── demo/                 # 演示视频和动图
```

## 开发

```sh
# 改了文案（tools/assets/strings.py）或美术代码：重新生成造型
pip install -r tools/assets/requirements.txt
python3 tools/assets/build.py

# 改了关卡地图（main.spx 的 levelMap）：检查地图
python3 tools/levels/check.py

# 本地运行 / 打包 .xbp
cd TankBattle && spx run .
./tools/package_xbp.sh

# 跑引擎内自动化测试（无界面运行，见 docs/v4/TEST_PLAN.md）
tools/test/run_spx.sh

# 打安装包（第一次先运行 setup_spx.sh）
tools/export/setup_spx.sh web
tools/export/build.sh desktop   # 或 web / android / ios

# 发布：先在 CHANGELOG.md 写好这个版本，再推送标签
git tag v3.0.2 && git push origin v3.0.2

# 重新录制演示视频（需要 ffmpeg）
./tools/dev/record_demo.sh
```

- **版本标签**：`v0` 是导入的基础版本（初版坦克大战），之后的提交都是在它之上新增的；`v2.0.0`、`v3.0.0`、`v3.0.1` 是发布版本。
- **开发规范**：每次改动都通过 Pull Request 合入，详见[架构文档](docs/ARCHITECTURE.md#11-开发流程与分工)。

## 代码里的教学要点

| 知识点 | 在哪里 | 一句话说明 |
|---|---|---|
| 数组 | `grid`、`levelMap()` | 地图是 13×13 的数组 |
| 克隆 | `Tile.build`、`Enemy.spawn` | 先设好模板变量，再 `clone` |
| 消息 | `broadcast` / `onMsg` | 砖墙被打中后广播 `gridChanged` |
| 状态机 | `main.spx` 的 `state` | 同一个键在不同画面含义不同 |
| 按帧移动 | `deltaTime` | 距离 = 速度 × 每帧时间 |
| 碰撞 | `tankBlocked`、`bulletHit` | 撞墙查格子，坦克之间用 `touching` |
| 简单 AI | `pickFace`、`autopilotDir` | 敌人偏向基地，自动驾驶追最近的敌人 |
| 搜索 | `reachable()` | 广度优先搜索：能不能开到基地 |
| 表现分离 | `look()`、`langCode()` | 画风、语言只是一个变量 |

## 素材与版权说明

- **图片**：所有造型和背景都是原创。v2 的现代画风造型、界面和文字由 `tools/assets/build.py` 用代码生成。
- **音效**：经典版用程序模拟 FC 音源合成，现代版用滤波噪声、低频冲击和铜管音色合成，全部原创，**没有**使用 Namco 原版的音乐或采样。
- **字体**：界面文字由 [Noto Sans SC](https://github.com/google/fonts/tree/main/ofl/notosanssc)（SIL Open Font License 1.1）的字形轮廓生成，游戏运行时不再携带字体文件。
