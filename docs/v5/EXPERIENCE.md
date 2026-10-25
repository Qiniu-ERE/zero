# 坦克大战 v5.0 · 各平台的游戏体验

> [v5.0 规划](PLAN.md)的一部分：让游戏在每个平台上都像“原生”的，并且能过认证 / 审核。每条标明**必须**（平台规则，不做就过不了或拿不到评级）还是**建议**（惯例或明显提升体验）。
>
> 依据：2026-10-25 查阅的 Steamworks 文档、Microsoft Store 政策（v7.20，2026-09-14）、Apple 人机界面指南（2025-06-09 更新）和审核准则、Android 开发者文档，以及本仓库代码。官方没写的标“惯例”，社区来源单独注明。文末有来源。

## 一、现状（代码）

| 项目 | 现在 |
|---|---|
| 画面 | 480×360（4:3），等比放大，四周留黑边 |
| 输入 | 键盘：1P WASD + J，2P 方向键 + Enter，Esc 暂停；鼠标：点按钮、编辑器画图；触屏：单指（手机包的 `touchUI` 模式）。**不支持手柄** |
| 文字 | 构建时转成矢量路径（不会缺字）；最小字号 5.8 像素（`build.py`，按键提示和徽章），常用 6~9 |
| 设置 | 只有画风（T）和语言（L）两个开关；没有音量、全屏、按键设置 |
| 存档 | 只有 PC 版能存一张自制地图 |
| 文字输入 | 没有（地图不用命名） |

## 二、所有平台共通

### 2.1 4:3 画面放到宽屏上

| 屏幕 | 放大方式 | 战场大小 | 两侧空白 |
|---|---|---|---|
| 1920×1080 | 整数 3 倍 | 1440×1080 | 左右各 240 |
| Steam Deck 1280×800 | 整数 2 倍 / 等比 2.22 倍 | 960×720 / 1067×800 | 左右各 160 / 107（整数时上下还有 40） |
| iPhone（约 19.5:9） | 等比 | 高度铺满 | 左右各约四分之一屏 |

**建议**（设计判断，平台都没有禁止黑边；只有 Google 自愿参加的 Level Up 计划要求不留黑边）：

- **战场保持 4:3 不变**：扩大战场会改变平衡（敌人出生点、射程都按 13×13 格设计）。
- 两侧空白放**装饰性面板**：剩余敌人、P1 / P2 生命、关卡号、最高分，和 FC 原版的右侧面板一样。手机上面板改成方向键和开火键（现在的 `touchUI` 就是这样做的）。
- 加“整数缩放”开关：像素风画风下画面更清晰。

### 2.2 字号

- Steam Deck 认证：在 1280×800 下最小字符高度**不低于 9 像素（必须）**，建议 12 像素。
- 我们最小的字是 5.8 像素（字号），拉丁字母大写约占字号的七成。放大 2.22 倍后约 9 像素，**正好卡在线上**；整数 2 倍时不到 9 像素。
- **要做**：把 6 号以下的字（按键提示、徽章）放大到至少 6.5；英文按键提示优先改成图标。实机截图测量后写回本节。

### 2.3 设置

| 设置 | 必须 / 建议 | 说明 |
|---|---|---|
| 全屏 / 窗口切换 | 建议（惯例） | spx 有 `set_window_fullscreen`，商店版加一个开关 |
| 音乐、音效两个音量 | 建议（惯例） | 现在没有 |
| 整数缩放 | 建议 | 见 2.1 |
| 按键重设 | 建议（惯例；苹果指南也建议让玩家自定义按键） | 键盘版先不做，手柄版用固定布局 |
| 画风、语言 | 已有 | 保存到存档 |

### 2.4 本地化

- Steam 用户语言（2026-09 硬件调查）：英语 34.2%、**简体中文 31.4%**；Valve 说超过 60% 的用户不用英文界面。**我们已有中英文**。
- 下一步的优先级（按用户数）：日语、俄语、德 / 法 / 西、巴西葡萄牙语、繁体中文。游戏文字都在 `strings.py` 一张表里，加语言主要是翻译成本；注意 `textpath.py` 要换支持对应文字的字体。
- **Microsoft Store（必须）**：在哪些地区发售，就要把**商店页**翻译成那些地区要求的语言（英、法、意、德、西、巴西葡语、日语、简体中文）。v5 可以先只选择英语和中文地区发售，以后再扩。

### 2.5 年龄分级

| 平台 | 方式 |
|---|---|
| Steam | 自家内容问卷；德国区从 2024-11-15 起没有分级的游戏会被隐藏（必须填） |
| Microsoft Store、Google Play | IARC 问卷（必须） |
| App Store | 自家问卷，2026 年新增 13+ / 16+ / 18+，2026-09 起新增社交相关题目（必须） |

游戏没有血腥、没有联网聊天、没有内购（第一步），预计是最低档。

## 三、Steam 和 Steam Deck

### 3.1 Steam Deck 认证（“已验证”）

| 要求 | 必须 / 建议 | 我们要做什么 |
|---|---|---|
| **默认手柄配置就能玩全部内容**，不用改游戏设置 | 必须 | 手柄支持（[TECH.md 第一节](TECH.md#一手柄)）：菜单、暂停、复活询问、结算、地图编辑器都能用手柄 |
| 屏幕上的按键图标和当前输入设备一致，用手柄时不能出现键盘 / 鼠标图标 | 必须 | `build.py` 生成手柄版提示，检测到手柄就切换 |
| 需要输入文字时，提供手柄可用的方式 | 必须（如果有） | 我们没有文字输入 ✅ |
| 不能有启动器，不能弹“不支持该系统”的警告 | 必须 | 单文件程序直接进游戏 ✅ |
| 支持 1280×800（推荐）或 1280×720 | 必须 | 等比放大已支持；实机确认 |
| 最小字符高度 9 像素 | 必须 | 见 2.2 |
| 默认设置下 800p 稳定 30 帧 | 必须 | 2D、很轻，预计没问题；实机确认 |

**测试顺序**：Valve 先测 Linux 原生包，不过再测 Windows 包在 Proton 下的表现，用好的那个。**建议两个都上传，先在 Deck 实机上确认 Linux 包**（Linux 包已在 x86_64 Ubuntu 虚拟显示器里启动过，见 [CROSS_PLATFORM.md](../v3/CROSS_PLATFORM.md)）。

### 3.2 手柄与双人合作

- Steam Input 的“键盘模拟”模板有一个致命问题：**两只手柄映射出来的按键会合并成同一个键盘输入**，游戏分不清 1P 和 2P，**本地双人合作没法用**。
- 所以必须**在游戏里按设备号区分两只手柄**（TECH.md 第一节的方案 A），并在 Steamworks 后台发布一份官方推荐配置。
- **Remote Play Together**：商店页勾选“本地合作 / 同屏”就会自动开启，只需要房主拥有游戏（官方）。社区反馈访客默认用虚拟手柄、键盘要房主手动开启，所以 **2P 能用手柄才能让远程同乐稳定**。

### 3.3 商店页要如实填写

| 项目 | 说明 |
|---|---|
| 手柄支持标签 | “完全支持”= 从启动到游玩全程只用手柄；“部分支持”= 有时需要键鼠。地图编辑器如果不做手柄操作，只能标“部分支持” |
| 无障碍向导（2025 年上线） | 可以声明“可调难度、随时存档、可调字号”等，玩家能按这些条件搜索。如实填 |
| 本地合作、同屏、Remote Play Together | 勾选（Couch Co-Op Fest 也要求勾选 Local Co-op） |

### 3.4 Steam 云存档（不用接 SDK）

在 Steamworks 后台配置 **Auto-Cloud**：设每个用户的空间和文件数配额 → 添加根路径（根目录 + 子目录 + 文件匹配，例如 `save.txt`、`maps.txt`）→ 用“根路径覆盖”对应三个系统 → 发布，约 10 分钟生效。我们用 Go 的 `os.UserConfigDir()`：Windows 是 `%AppData%`（Roaming），macOS 是 `~/Library/Application Support`，Linux 是 `~/.config`；在后台选对应的根目录（Linux 的 XDG 配置目录根要核实）。**画面设置不要同步**（Valve 建议）。

## 四、Microsoft Store（Xbox PC）

| 要求（政策条款） | 必须 / 建议 | 我们要做什么 |
|---|---|---|
| 10.2.5 游戏必须用商店支持的包格式提交，只能通过商店安装和更新 | 必须 | MSIX 封装。**不用 GDK 的普通 Win32 游戏能不能只用 MSIX 提交，官方没写清楚**，提交前在 Partner Center 确认 |
| 10.1.1 商店描述写清支持的输入设备 | 必须 | 写“键盘；手柄（如果做了）” |
| 10.4 适配各种分辨率；启动快、不崩溃、能正常退出 | 必须 | 已有；实测 |
| 10.7 / 10.13.14 商店页本地化 | 必须 | 见 2.4 |
| 10.13.12 PC 上支持手柄 | 建议 | 手柄做了就勾 |
| 11.11 IARC 分级 | 必须 | 填问卷 |
| Xbox 网络服务的要求（成就等） | 只在接入 Xbox 服务时适用 | 不接，不适用 |

**Xbox 主机**（只评估）：要通过 ID@Xbox；认证要求包括挂起 / 恢复后重新确认用户和手柄配对（XR-112）、Series S 和 X 功能一致（XR-130）、挂起恢复不丢进度。写进 P5 的评估文档。

## 五、App Store（iPhone / iPad）

| 要求 | 必须 / 建议 | 我们要做什么 |
|---|---|---|
| 适配 16:10、19.5:9、4:3 等比例，用安全区避开刘海、灵动岛和 Home 指示条 | 必须（指南 + 审核 4.2 的实质要求） | 现在的 `touchUI` 面板要加安全区内边距；实机截图确认 |
| 触控按钮至少 44×44 pt（菜单类至少 28×28 pt）；按下有视觉、声音、震动反馈 | 指南 | 量一下现在方向键的实际尺寸；加震动反馈需要原生接口，先做视觉和声音 |
| 手柄不能是唯一的操作方式 | 指南 | 触屏一直保留 ✅ |
| 支持手柄时按键图标跟随手柄，Menu 键暂停 | 建议 | 和 Steam 版共用手柄方案 |
| **App Store 页面显示“支持手柄”标识**：`Info.plist` 设置 `GCSupportsControllerUserInteraction` | 建议 | 做了手柄就加；**手柄是手机上双人合作的唯一办法**（两只手柄） |
| 虚拟摇杆建议跟随拇指落点出现；让玩家调整按钮位置和大小 | 建议 | v5 先用固定方向键，后续再做 |
| 4.1 不能用别人的名字和品牌（*Battle City* 是 Namco 的） | 必须 | 改名（[PLATFORMS.md 第七节](PLATFORMS.md#七知识产权上架前必须处理)） |
| 4.2 要有持久的娱乐价值 | 必须 | 8 关 + 编辑器 + 手柄双人；不要做成“玩两分钟就没了” |
| 隐私清单 `PrivacyInfo.xcprivacy` | 必须（2024-05 起） | 导出后检查 IPA 里有没有；没有就在 `build.sh ios` 里加 |
| 年龄分级问卷（2026 新版） | 必须 | 填 |

## 六、Google Play

| 要求 | 必须 / 建议 | 我们要做什么 |
|---|---|---|
| 目标 API 36（2026-08-31 起，可延期到 11-01）、AAB、16 KB 页（更新从 2027-02-01 起强制） | 必须 | 等 spx 升级到 Godot 4.5+，或自己编译模板（[PLATFORMS.md 第六节](PLATFORMS.md#六google-play)） |
| Android vitals：用户可感知的崩溃率不超过 1.09%、ANR 率不超过 0.47%（单机型 8%） | 必须（超过会降低曝光、商店页显示警告） | 上线前跑 Play 的发布前测试报告；Go 运行时的崩溃（例如 macOS 上遇到过的 SIGURG）要特别留意 |
| 大屏（平板、Chromebook）全屏运行，不进兼容模式 | 建议 | 横屏锁定 + 等比放大，实机确认 |
| 手柄、键盘、鼠标都能玩，manifest 加手柄标识 | 建议（Level Up 计划要求） | 和 Steam 版共用手柄方案；Chromebook 上键盘已经能玩 |
| Play Games on PC | 默认会上 PC，可以退出 | 先退出，等手柄和键鼠体验确认后再开 |

## 七、合并清单（按优先级）

| 优先级 | 项目 | 平台 | 必须 / 建议 | 阶段 |
|---|---|---|---|---|
| 1 | 手柄：两只手柄按设备号区分 1P / 2P；菜单、暂停、编辑器都能操作 | Steam Deck、Xbox PC、iOS、Android | 必须（Deck 认证、远程同乐、手机双人） | P1 |
| 2 | 按键图标跟随输入设备 | 全部 | 必须（Deck） | P1 |
| 3 | 改名、去掉原作名称 | 全部 | 必须 | P1 |
| 4 | 去掉模拟广告（商店版） | 全部 | 必须（付费游戏） | P1 |
| 5 | 最小字号放大到 6.5 以上，Deck 实测 9 像素 | Steam Deck | 必须 | P1 |
| 6 | 存档 + Steam Auto-Cloud | Steam | 建议 | P1 / P2 |
| 7 | 设置：全屏、两个音量、整数缩放 | PC | 建议 | P1 |
| 8 | 两侧装饰面板（代替黑边） | 全部 | 建议 | P2 |
| 9 | 内容问卷 / IARC / 苹果分级 | 全部 | 必须 | P2~P3 |
| 10 | 商店页多语言 | Microsoft Store | 必须（按发售地区） | P2 |
| 11 | MSIX 封装，确认普通 Win32 游戏可行 | Microsoft Store | 必须 | P2 |
| 12 | 安全区、44 pt 按钮、隐私清单、手柄标识 | iOS | 必须 / 建议 | P3 |
| 13 | API 36、AAB、16 KB、vitals | Android | 必须 | P4 |

## 来源

- Steam：[Steam Deck 兼容性评审](https://partner.steamgames.com/doc/steamhardware/compat)、[为 Steam Deck 做准备](https://partner.steamgames.com/doc/steamhardware/recommendations)、[Steam Input 开发者入门](https://partner.steamgames.com/doc/features/steam_controller/getting_started_for_devs)、[Steam 云](https://partner.steamgames.com/doc/features/cloud)、[Remote Play](https://partner.steamgames.com/doc/features/remoteplay)、[商店页设置](https://partner.steamgames.com/doc/store/page)、[无障碍功能](https://partner.steamgames.com/doc/accessibility_features)、[本地化](https://partner.steamgames.com/doc/store/localization)、[德国内容分级](https://partner.steamgames.com/doc/gettingstarted/contentsurvey/germany)、[Steam 硬件调查](https://store.steampowered.com/hwsurvey)、[社区：远程同乐的键盘输入](https://steamcommunity.com/discussions/forum/1/3279193518786199684)、[steam-runtime issue #585](https://github.com/ValveSoftware/steam-runtime/issues/585)
- Microsoft：[Microsoft Store 政策](https://learn.microsoft.com/en-us/windows/apps/publish/store-policies)、[PC 上的 Xbox 服务政策](https://learn.microsoft.com/en-us/gaming/gdk/docs/store/policies/pc/live-policies-pc)、[Xbox 主机认证要求](https://learn.microsoft.com/en-us/gaming/gdk/docs/store/policies/console/console-certification-requirements-and-tests)
- Apple：[为游戏设计（HIG）](https://developer.apple.com/design/human-interface-guidelines/designing-for-games)、[游戏操控（HIG）](https://developer.apple.com/design/human-interface-guidelines/game-controls)、[App 审核准则](https://developer.apple.com/app-store/review/guidelines/)、[年龄分级新要求](https://developer.apple.com/news/upcoming-requirements/?id=07242025a)、[WWDC21：游戏手柄](https://developer.apple.com/videos/play/wwdc2021/10081/)
- Android：[目标 API 要求](https://developer.android.com/google/play/requirements/target-sdk)、[16 KB 页](https://developer.android.com/guide/practices/page-sizes)、[Android vitals](https://developer.android.com/topic/performance/vitals)、[大屏应用质量](https://developer.android.com/docs/quality-guidelines/large-screen-app-quality)、[游戏质量指南](https://developer.android.com/games/guidelines)、[Play Games on PC](https://developer.android.com/games/playgames/pc-compatibility)
- Godot：[多分辨率（4.4 文档）](https://docs.godotengine.org/en/4.4/tutorials/rendering/multiple_resolutions.html)、[Godot 4.5 发布说明](https://godotengine.org/releases/4.5/)
