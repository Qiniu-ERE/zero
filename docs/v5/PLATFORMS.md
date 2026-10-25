# 坦克大战 v5.0 · 平台评估

> [v5.0 规划](PLAN.md)的第一个方向：Steam、Xbox、PlayStation、Apple App Store、Google Play 逐个评估。**公开资料**都是 2026-10-25 查阅的，有官方文档也有第三方文章，来源列在文末。**提交前一律以官方文档重新核对。** 本文不是法律或税务意见。

## 一、总表

| 平台 | 账号与费用 | 主体 | 我们的包 | 主要缺口 | 结论 |
|---|---|---|---|---|---|
| **Steam** | 每款游戏 $100，销售额达到 $1000 后返还 | 个人可以 | ✅ Windows / macOS / Linux 单文件程序 | 手柄、商店版、改名、商店页素材 | ✅ **首选** |
| **Microsoft Store（PC）** | 个人注册免费（2025-09 起） | 个人可以（身份验证） | ✅ Windows 包，要封装成 MSIX | MSIX 封装、商店版、改名 | ✅ 和 Steam 一起做 |
| **Apple App Store** | $99 / 年 | 个人可以 | ⚠️ 不签名的 IPA | 签名、Xcode 26 / iOS 26 SDK、隐私清单、一台装 Xcode 的 Mac | ⚠️ 中国区以外可以 |
| **Google Play** | 一次性 $25 | 个人可以，但新应用要 12 人连续 14 天封闭测试 | ⚠️ 调试签名的 APK | AAB、目标 API 36、16 KB 页对齐、正式签名 | ⚠️ 等 spx 升级引擎 |
| **Xbox 主机** | ID@Xbox 免费加入，开发机申请 | 需要公司信息（注册号、法定名称） | ❌ | 主机移植模板、**Go 不支持主机系统** | ❌ 近期不做 |
| **PlayStation 5** | PlayStation Partners 免费，开发机可借用 | 法人主体（欧洲可以个体户） | ❌ | 同上 | ❌ 近期不做 |

## 二、Steam

### 2.1 门槛（公开资料）

- **Steam Direct 费用**：每款新应用 $100，不退，但游戏在 Steam 上的调整后总收入达到 $1000 后返还（Steamworks 官方文档）。
- 个人可以注册 Steamworks，需要提交税务和银行信息，有一段等待期。
- 新游戏要先开“即将推出”页面，审核商店页和构建，之后才能发售（具体时长以 Steamworks 文档为准）。
- **AI 内容披露**（2026-01 更新）：游戏里**直接呈现给玩家**的 AI 生成美术、音频、文字要在商店页披露；**用 AI 辅助写代码、调试不需要披露**。我们的造型由 `build.py` 用代码生成，音效由程序合成，文字是人写的文案表，按这个规则推测不需要披露；如果宣传素材用了 AI 生成的图，要披露。

### 2.2 Steam Deck 认证

Steam Deck 和 Steam Machine 的兼容性评级要求（Steamworks 官方文档）：

| 要求 | 我们现在 | 要做什么 |
|---|---|---|
| 默认手柄配置就能玩全部内容，不用改游戏设置 | ❌ 不支持手柄 | 手柄支持（[TECH.md 第一节](TECH.md#一手柄)）；没做之前可以用 Steam Input 把手柄映射成键盘，但只能评为“可玩” |
| 屏幕上的按键提示和实际输入一致（Deck / Xbox 图标） | ❌ 只有键盘提示（`WASD`、`J`、`Enter`） | 生成手柄版提示 |
| 文字输入要能用手柄完成 | ✅ 游戏里没有文字输入 | — |
| 默认分辨率和文字可读 | 480×360 等比放大，文字是矢量路径 | Deck 屏幕 1280×800，上下会有黑边；实机确认文字大小 |
| 性能 | 2D、很轻 | 实机确认帧率和发热 |

Linux 包可以在 Steam Deck 上原生运行（Steam Deck 是 x86_64 Linux）；也可以让 Deck 用 Proton 跑 Windows 包。v3.0.2 的 Linux 包在 x86_64 Ubuntu 的虚拟显示器里已经能启动（[CROSS_PLATFORM.md](../v3/CROSS_PLATFORM.md)），实机还没测。

### 2.3 卖点和 Steam 功能

| 功能 | 怎么用 | 要不要接 Steamworks SDK |
|---|---|---|
| **Remote Play Together** | 本地双人合作直接变成在线合作：一个人买游戏，朋友通过 Steam 串流加入 | 不需要（Steam 串流画面和输入）；**前提是两个人都能用手柄或键盘的不同区域操作**，这正是我们已有的双人键位 |
| 试玩版 | Steam 支持独立的 Demo 应用 | 不需要 |
| 成就、云存档、排行榜 | 加分项 | 需要；游戏脚本调不到 SDK（[TECH.md 第四节](TECH.md#四暂不做sdk-集成)），v5 不做 |
| 创意工坊（分享自制地图） | 很契合地图编辑器 | 需要，v5 不做 |

### 2.4 风险

- **Windows 包被杀毒软件误报**：spx 的单文件程序第一次运行时把引擎解压到用户缓存目录，这种行为容易被误报（推测）。上架前用 VirusTotal 检查；需要时买代码签名证书。
- **macOS 包**：现在是 ad-hoc 签名，Steam 上的 macOS 版最好做公证（需要 Apple 开发者账号，和 iOS 共用）。

## 三、Xbox

Xbox 分成三条路，难度差别很大：

| 路线 | 要什么 | 我们能不能做 |
|---|---|---|
| **Microsoft Store（PC）** | 个人开发者注册免费（2025-09-10 起）；Win32 程序封装成 MSIX 后提交，微软负责签名；付费应用微软抽成（以官方说明为准） | ✅ 能做。Windows 包封装成 MSIX，审核一般 1~7 天 |
| **PC Game Pass / Xbox PC 应用** | 通过 ID@Xbox，和微软谈 | ⚠️ 要先有 ID@Xbox 资格；Microsoft 的 Godot 示例（XBOX-Godot-Sample，C++）提供了 PC 上的 GDK 绑定 |
| **Xbox 主机** | ID@Xbox：注册 Xbox 合作伙伴、签保密协议、提交游戏概念（审批一般 10~15 个工作日）、签授权协议；申请表要填公司注册号和法定名称；概念通过后可以订开发机（有报道说 2026 年初开发机交付有延迟） | ❌ 见第五节 |

## 四、PlayStation

- 在 partners.playstation.net 注册，要求**法人主体**（公司），欧洲接受个体户；提交项目计划，签 Sony 的开发与发行协议后获得 SDK（公开资料）。
- Sony 对新注册的合作伙伴免费借出一台开发机和一台测试机，两年内归还（Sony 官方博客，2026）。
- 技术上和 Xbox 主机一样卡在引擎（第五节）。

## 五、主机为什么近期做不了

1. **Godot 本身没有官方主机支持**：主机 SDK 受保密协议约束，开源引擎不能附带。用 Godot 的游戏上主机要通过第三方移植（例如 W4 Games 的主机模板，支持 Xbox Series、PS5、Switch，适配 Godot 4.3 以上）。W4 的价格公开资料说法不一：早期公布过“单平台每年 $800 起”，后来的文章说按项目报价，没有公开价。
2. **spx 的游戏逻辑跑在 Go 里**：spx 游戏 = Godot 引擎 + 一个 Go 写的扩展（gdspx）+ Go 写的 XGo 解释器（ixgo）。Go 官方支持的操作系统里没有任何主机系统；Go 的 Godot 绑定项目也写明“不支持主机，以后可能通过 WASM 实现”（公开资料）。**也就是说，即使拿到主机移植模板，我们的游戏代码也跑不起来。**
3. **出路**：把游戏逻辑改写成 GDScript（或 C#），美术、音效、地图数据可以直接复用。工作量评估见 [TECH.md 第五节](TECH.md#五主机改写还是等待)。

## 六、Apple App Store

| 项目 | 要求（公开资料） | 我们现在 |
|---|---|---|
| 账号 | Apple Developer Program，$99 / 年 | 没有 |
| 编译工具 | **2026-04-28 起，上传的应用必须用 Xcode 26 和 iOS 26 SDK 编译**；最低支持 iOS 13 以上 | CI 用 `macos-15` 机器编译，Xcode 版本要确认；本机没有 Xcode，磁盘也不够 |
| 签名 | 开发者证书 + 描述文件 | 不签名（`CODE_SIGNING_ALLOWED=NO`） |
| 隐私清单 | `PrivacyInfo.xcprivacy`，声明用到的“需要说明理由的 API”（2024-05 起，凭记忆，要核实） | 没有；Godot 模板可能已带，要检查 |
| 年龄分级 | App Store Connect 里回答分级问卷（2026 年更新过问题） | — |
| 审核 | 4.1（模仿）、4.3（重复应用）等条款 | 改名、强调原创内容（地图编辑器、双人合作、8 张原创地图） |
| **中国区** | 所有 App 要 ICP 备案，**游戏要版号**，免费游戏也没有例外 | **不上中国区** |

体验上的问题：

- iPhone 上只能单指触屏（`touchUI`），双人合作入口在触屏模式下会提示“需要键盘或两只手柄”。**做了手柄支持之后，iPad / iPhone 外接手柄就能玩双人合作**（Godot 支持 iOS 的 Game Controller，但要经过 spx 的补丁，见 TECH.md）。
- 地图编辑器在 iPad 上用手指画，比手机好用。

Mac App Store 可以作为附带：同一个开发者账号；要求沙盒，spx 的启动器把引擎解压到 `~/Library/Caches`，在沙盒里会落到应用容器目录，**能不能运行要实测**。优先级低于 Steam 的 macOS 版。

## 七、Google Play

| 要求（公开资料） | 我们现在（代码） | 怎么解决 |
|---|---|---|
| **新应用必须提交 AAB** | spx 的导出模板 `use_gradle_build=false`，只能出 APK；Godot 出 AAB 必须用 Gradle 构建 | 改 spx 模板启用 Gradle 构建（要装 Android 构建模板、Gradle） |
| **目标 API 36**（2026-08-31 起，新应用和更新都要；可以申请延期到 2026-11-01） | Godot 4.4.1 的预编译模板目标 API 34；不用 Gradle 构建改不了 | Godot 4.5 把目标 API 升到 35，再往后的版本升到 36；要 spx 升级 Godot，或者用 Gradle 构建自己设 |
| **16 KB 页大小**（目标 API 35 以上的应用要支持；更新包从 2027-02-01 起不支持就不能发布） | Godot 4.4.1 的库和我们用 NDK r23c 编译的 `libgdspx-android-arm64.so` 都是按 4 KB 页对齐的（推测，要用 `zipalign`/`readelf` 检查） | Godot 4.5 换成 NDK r28 后自动支持；gdspx 的 Go 库要用新 NDK 重新编译并加 16 KB 对齐的链接参数 |
| 正式签名，Play 应用签名 | 调试证书 | 生成上传密钥，**不进仓库**；Play 托管应用签名密钥 |
| 个人账号新应用：**至少 12 名测试者连续 14 天参加封闭测试**才能申请正式发布（2023-11-13 之后注册的个人账号；公司账号免除） | — | 提前找测试者（同学、同事），按 16~20 人准备 |
| 数据安全表、内容分级（IARC）、隐私政策 | — | 不收集数据，表格照实填 |

结论：**Google Play 卡在 spx 的引擎版本上**，不是我们自己改几行能解决的。P4 先跟踪 spx 上游的 Godot 升级；如果上游迟迟不升，再评估自己维护一套 Gradle 构建的成本。

## 八、知识产权：上架前必须处理

游戏是 1985 年 FC《坦克大战》（Namco，英文名 *Battle City*）的复刻重铸版。比赛作品这样写没有问题，上架商店就不一样了：

| 项目 | 现状（代码） | 风险 | 处理 |
|---|---|---|---|
| **英文标题** | `strings.py` 里英文标题就是 `BATTLE CITY` | 原作名称，可能侵犯商标；商店审核（例如 App Store 4.1 模仿条款）会因此拒绝 | **改名**（中英文都换），先查商标和商店里有没有重名 |
| README 徽章 | “remake of Battle City 1985” | 仓库里可以保留（说明来历） | 商店页、截图、预告片里不提原作名称，不用原作画面 |
| 玩法 | 守老鹰、打砖墙、20 辆敌人一关 | 玩法本身一般不受著作权保护，但太像会影响审核和口碑 | 突出差异：现代画风、地图编辑器、双人合作、8 张原创地图；评估把“老鹰”换成自己的基地造型 |
| 美术 | 全部原创，由 `build.py` 生成 | 低 | 保留生成脚本和提交记录作为原创证明 |
| 音效 | 全部程序合成，没有用原版音乐或采样（README 版权说明） | 低 | 同上 |
| 字体 | Noto Sans SC，SIL OFL 1.1，构建时转成路径 | 低，OFL 允许商用 | 在“关于”里注明 |
| 引擎和工具 | spx（Apache-2.0）、Godot（MIT） | 低 | 安装包里附上许可证文本 |

## 九、暂不聚焦的渠道

之前评估过的海外 H5 门户（CrazyGames 等）、微信 / 抖音小游戏、国内安卓商店，这一版不做：小游戏和国内商店需要软著、ICP 备案甚至版号；H5 门户和小游戏都靠广告变现，而广告需要游戏脚本调用平台 SDK，这正是 spx 做不到的。技术细节见 [v3.0 微信小游戏评估](../v3/WECHAT_MINIGAME.md)。

## 来源

- Steam：[Steam Direct 费用（Steamworks 文档）](https://partner.steamgames.com/doc/gettingstarted/appfee)、[Steam Deck / Steam Machine 兼容性评审（Steamworks 文档）](https://partner.steamgames.com/doc/steamhardware/compat)、[为 Steam Deck 做准备（Steamworks 文档）](https://partner.steamgames.com/doc/steamhardware/recommendations)、[Steam 2026 年 AI 披露规则解读](https://www.strayspark.studio/blog/steam-ai-disclosure-rules-2026-indie-developer-guide)
- Microsoft Store：[Windows 开发者博客（2025-05）](https://blogs.windows.com/windowsdeveloper/2025/05/19/microsoft-store-expands-opportunities-for-windows-app-developers/)、[Windows Central：个人开发者免注册费](https://www.windowscentral.com/microsoft/windows-11/microsoft-store-drops-fees-for-individual-developers-apple-still-charges-usd99-per-year)
- Xbox：[加入 ID@XBOX（Microsoft Learn）](https://learn.microsoft.com/en-us/gaming/game-publishing/onboarding/onboarding-join-id-at-xbox)、[Xbox 合作伙伴入门（devdocs.xbox.com）](https://devdocs.xbox.com/home/onboarding)、[Windows Central：ID@Xbox 开发机延迟](https://www.windowscentral.com/gaming/indies-idxbox/indie-studio-says-xbox-is-encouraging-development-for-its-platform-yet-id-xbox-dev-kit-delays-are-leaving-approved-projects-stuck-in-limbo)
- PlayStation：[Sony：免费开发硬件](https://sonyinteractive.com/en/news/blog/complimentary-development-hardware/)、[2026 年主机移植指南](https://gamedo.live/news/how-to-port-indie-game-consoles-2026/)
- Godot 主机移植与 Go：[GamingOnLinux：W4 Games 主机移植定价](https://www.gamingonlinux.com/forum/topic/5925/)、[2026 年 Godot 游戏移植主机](https://zivadotsh.hashnode.dev/how-to-port-a-godot-game-to-switch-ps5-and-xbox-in-2026)、[Heroic Labs 论坛：Godot 游戏的主机支持](https://forum.heroiclabs.com/t/console-support-for-godot-games/6518)、[graphics.gd（Go 的 Godot 绑定）](https://github.com/grow-graphics/gd)
- Apple：[App Store Connect 发布说明](https://developer.apple.com/app-store-connect/release-notes)、[Xcode 26 要求（2026-04-28）](https://ptkd.com/journal/app-store-xcode-26-sdk-requirement)、[IT之家：中国区 App 必须有 ICP 备案号](https://www.ithome.com/0/722/535.htm)、[搜狐：苹果游戏上架资质（2026）](https://www.sohu.com/a/1004819505_122670629)
- Google Play：[新个人开发者账号的测试要求（Play Console 帮助）](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en)、[目标 API 36 截止日期](https://primetestlab.com/blog/google-play-target-api-level-2026)、[Godot PR #106358：NDK r28 与 16 KB 页](https://github.com/godotengine/godot/pull/106358)、[Godot PR #106152：Android 版本升级](https://github.com/godotengine/godot/pull/106152)、[Godot 论坛：16 KB 页警告](https://forum.godotengine.org/t/godot-and-google-play-policy-warning-about-16-kb-memory-page-size/120934)
