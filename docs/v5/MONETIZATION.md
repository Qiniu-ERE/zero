# 坦克大战 v5.0 · 盈利方案

> [v5.0 规划](PLAN.md)的一部分：每个平台**怎么收钱**、游戏里**放不放广告**、能赚多少。给游戏打广告（推广）见 [MARKETING.md](MARKETING.md)。
>
> 依据：2026-10-25 查阅的平台官方文档（Steamworks、Apple、Google Play、AdMob、Microsoft）、行业数据（GameDiscoverCo、Gamalytic、GameAnalytics、Sensor Tower、Appodeal / Tenjin），以及本仓库代码和 spx 源码。可信度：**高** = 官方文档；**中** = 知名数据方或有日期的报道；**低** = 第三方站点或个案。**收入试算全部是推测**，只用来说明量级和怎么算。文末有来源。

## 一、结论

| 平台 | 收费方式 | 游戏里的广告 | 平台抽成（年收入 < $100 万） | 什么时候做 |
|---|---|---|---|---|
| **Steam** | **买断 $4.99**（区域定价）+ 免费试玩版 | 无 | 30% | P2 |
| **Microsoft Store（PC）** | 买断，和 Steam 同价 | 无 | **12%**（PC 游戏） | P2，顺手上架 |
| **App Store** | 第一步**付费下载 $2.99**；SDK 接得上之后改成**免费下载 + 一次性解锁完整版** | 第一步无；第三步只给没付费的玩家放**自愿的激励视频** | 15%（小型企业计划，要申请） | P3 |
| **Google Play** | 同 App Store，等引擎升级 | 同上 | 美国 / 欧洲 / 英国约 15%（10% + 5% 结算费，2026-06-30 起）；其他地区 15% | P4 |
| Xbox 主机 | — | — | — | 只评估 |

**为什么 PC 不放广告**：Steam 和 Microsoft Store 的玩家习惯买断；付费游戏里放广告会被差评；而且游戏脚本调不到任何广告 SDK（第五节）。

**为什么手机不能一步到位**：手机游戏 96% 的下载是免费下载（Google Play 上 99%，Sensor Tower 2026，中），付费下载的曝光和转化都差，所以“免费 + 解锁”或“免费 + 激励视频”更合适。但这两种都要接平台 SDK（StoreKit、Play 结算、AdMob），**spx 现在接不上**（第五节）。所以分三步：先付费下载（不需要任何 SDK），等 SDK 能接再改免费 + 解锁，最后才考虑激励视频。

## 二、Steam 和 Microsoft Store：买断制

### 2.1 规则（高）

| 项目 | 规则 | 来源 |
|---|---|---|
| Valve 分成 | 单款游戏累计收入 $1000 万以内 30%，$1000 万~5000 万 25%，以上 20%；按扣除税、退款、拒付后的收入计算 | presskit.gg 汇总（多家一致） |
| 上架费 | $100 / 款，收入达到 $1000 后返还；试玩版、原声、DLC 不用另交 | Steamworks |
| 定价 | Valve 提供区域定价建议，也可以每个币种自己定；**发售后 30 天内不要改价，涨价后 30 天内不能打折** | Steamworks |
| 退款 | 购买 14 天内、游玩不到 2 小时可以退 | Steam 退款政策 |
| Microsoft Store 分成 | PC 游戏 12%（2021-08 起），游戏必须用商店的支付 | Microsoft Learn |

### 2.2 定什么价

- Steam 新品前 50 名的首月销量中位价已经从 $19.50（2023-02）降到 $15.64（2025-10），爆款里有一批 $5~10 的游戏（GameDiscoverCo，中）。
- 2022 年上半年 75% 的独立游戏定价低于 $10（VG Insights，中，数据旧）。
- 我们的体量：8 关 + 地图编辑器 + 本地双人，一个人通关大约 1~2 小时（推测）。**2 小时以内退款**的规则对短流程游戏不利，定价低一些能降低退款冲动。

**建议 $4.99**（人民币按 Valve 区域定价建议，约 ¥22 档），首发 8 折。以后加内容（新关卡包）再考虑涨到 $6.99。

### 2.3 试玩版

- 免费，第 1~2 关；不能保存地图；结尾“加入愿望单 / 购买完整版”。
- 用途：参加 Next Fest（必须有试玩版）、让主播能直接玩。试玩版峰值在线超过 50 人的游戏，正式版峰值中位数约是试玩版的 3 倍（GameDiscoverCo 2026，中）。

### 2.4 能赚多少（推测）

公式：**到手收入 ≈ 销量 × 售价 × (1 − 30%) × (1 − 区域折扣、税、退款约 25%)**，每卖一份 $4.99 到手约 $2.6。

| 情景 | 发售时愿望单 | 首周销量（0.15 倍） | 第一年销量（首周 × 3，推测） | 第一年到手 |
|---|---|---|---|---|
| 没推广 | 500 | 75 | ~225 | ~$590 |
| 铜档 | 5000 | 750 | ~2250 | ~$5900 |
| 银档 | 8000 | 1200 | ~3600 | ~$9400 |

参考基准：2025 年 Steam 上 65.9% 的游戏收入不到 $1000（Gamalytic，中）。**推广决定了我们落在哪一行**，所以 v5 的推广目标定在 5000 个愿望单（见 MARKETING.md）。

Microsoft Store：自然流量很少，曝光主要靠 Game Pass（Windows Central，中）；投入保持最小，同时申请 ID@Xbox（免费）争取编辑推荐。

## 三、App Store 和 Google Play：分三步

### 3.1 规则（高）

| 项目 | App Store | Google Play |
|---|---|---|
| 开发者费 | $99 / 年 | $25 一次性；2023-11-13 后注册的个人账号，上架前要 12 人连续 14 天封闭测试 |
| 抽成 | 小型企业计划 15%（上一年和当年收入都不超过 $100 万，**要手动申请**） | 美国 / 欧洲 / 英国（2026-06-30 起）、澳洲 / 日本（2026-09-30 起）：首 $100 万 10% + 用 Play 结算 5%；其他地区首 $100 万 15% |
| 游戏内解锁 | 必须用苹果内购（准则 3.1.1） | 必须用 Play 结算，Billing Library ≥ 8（2026-08-31 起，可延期到 2026-11-01） |

### 3.2 三步走

| 步骤 | 做法 | 需要的技术 | 前提 |
|---|---|---|---|
| **第一步：付费下载** | iOS $2.99，完整游戏；不放广告。手机上隐藏双人合作入口（单指触屏），接手柄后再开放 | **不需要任何 SDK** | 苹果开发者账号、Xcode 26 编译签名（[TECH.md 第六节](TECH.md#六平台打包)） |
| **第二步：免费 + 一次性解锁** | 免费开放第 1~3 关；**一次性购买 $2.99~4.99** 解锁全部 8 关、地图编辑器保存、双人合作 | StoreKit / Play 结算插件（`godot-google-play-billing` 3.x 支持 Godot 4.2+，iOS 有 4.4 可用的社区插件，中） | spx 能加载 Godot 插件（第五节） |
| **第三步：激励视频（可选）** | 只对**没有购买**的玩家：复活、金币 ×2 两个位置，玩家自己选择看；买了就再也看不到广告 | AdMob 插件（官方插件 v5 起要求 Godot 4.5+，中） | spx 升级到 Godot 4.5+ 且能加载插件 |

Google Play 的第一步也要等引擎升级（AAB、目标 API 36、16 KB 页，见 [PLATFORMS.md 第六节](PLATFORMS.md#六google-play)）。

**Apple Arcade**：只收**还没发布**的游戏，按游玩时长分成。想试就要在 iOS 发布之前投递（免费，概率低，高）。建议 P3 开始前投一次。

### 3.3 为什么激励视频放最后：算一笔账

| 数据 | 数字 | 可信度 |
|---|---|---|
| 激励视频 eCPM（每千次展示收入） | 北美 iOS 约 $13.6 / Android 约 $9.0；欧洲 $8.9 / $5.1；亚太 $7.5 / $8.2（Appodeal 2024 Q4）。另一份 2026 数据美国 $24~30。各来源差异很大 | 中 |
| 纯广告休闲游戏每日每用户收入（ARPDAU） | $0.01~0.05 | 低~中 |
| 留存（全品类中位数） | 次日约 22%，7 日不到 4%，30 日约 0.7%（GameAnalytics 2026）；街机类次日高、长线差 | 中~高 |
| 付费率（免费游戏里买过东西的玩家） | 一般 2~5% | 中 |

试算（推测）：日活 1000、ARPDAU $0.03 → 每天 $30，一年约 $1.1 万，前提是持续有 1000 日活，而这需要持续买量或者被推荐。对比：同样 1000 个新玩家里 3% 花 $2.99 解锁 → 约 $90（扣 15% 后约 $76），是一次性的。**广告收入靠日活规模，解锁收入靠玩家质量**。我们没有买量预算，日活大概率很小，所以先做解锁；广告只在第二步跑出日活之后再加，作为没付费玩家的补充。

### 3.4 广告上线时必须满足的合规要求（高）

| 要求 | 做法 |
|---|---|
| 欧洲经济区 / 英国 / 瑞士：投放广告要用 Google 认证的同意管理平台 | 用 Google 免费的 UMP，提供“随时撤回同意”的入口 |
| iOS 广告追踪授权（ATT） | 我们不买量，**先不弹 ATT**，广告按非个性化投放（游戏类同意率约 39%，Adjust 2026，中） |
| Google Play 家庭政策 | 目标受众填 **13 岁以上**，避开儿童广告的额外要求（家庭自认证广告 SDK 计划已不接受新申请） |
| App Store 2.5.18 | 广告符合年龄分级、有关闭按钮、有“举报不当广告”的入口 |
| AdMob 激励广告规则 | 玩家每次都要主动选择，观看前说明奖励（我们现有的设计已经符合） |
| 隐私标签 / 数据安全表 | 按 Google 的披露指引填写；Google 广告 SDK 11.2.0 起自带隐私清单 |

## 四、怎么判断卖得好不好

### 4.1 数据从哪来

| 平台 | 数据 |
|---|---|
| Steam | 商店页访问（含 UTM 来源）、**愿望单**、试玩版玩家数、销量、退款率和原因、评测 |
| Microsoft Store / App Store / Google Play | 商店页访问、下载 / 购买、转化率、崩溃报告、评分 |
| 游戏自己 | 可选：匿名的关卡通过率、复活率（[TECH.md 第三节](TECH.md#三存档与匿名统计)，已验证 spx 脚本可以发 HTTP 请求） |

### 4.2 决策点 2 的标准

| 指标 | 继续扩平台 | 先改游戏 | 依据 |
|---|---|---|---|
| 发售前愿望单 | ≥ 5000 | < 2000 | Zukowski 铜档 5000（中） |
| 首周销量 / 愿望单 | ≥ 0.15 | < 0.08 | GameDiscoverCo 中位数 0.10~0.15（中） |
| 退款率 | < 10% | > 20% | 推测 |
| 好评率 | ≥ 80% | < 70% | 推测 |

### 4.3 金币：只换外观

金币现在按本关得分折算（每关约 140~260），不保存、没有用处。商店版给它用处，但**只能换外观、不卖数值、不能用钱买**：金币复活（300，代替点不了的“钻石复活”）、坦克涂装（1500~3000）、基地造型（2000）、地图槽位（1000 / 个）。价格要按真实通关数据调。

## 五、技术前提：为什么 SDK 现在接不上（代码）

在 spx 源码（`c3c0da5`）里确认：

- spx 的引擎是**带 spx 模块的定制版 Godot**（`godot_modules/spx`），游戏脚本能调用的引擎功能是一张**固定的函数表**（约 340 个 `SPX_BIND` 函数，Go 侧代码由生成器产生）。表里没有调用任意 Godot 单例或插件的接口。
- 要接 AdMob / StoreKit / Play 结算，需要：在 spx 模块里加一个“宿主消息”接口（例如 `host_send(kind, arg)` / `host_poll()`），在 C++ 侧转给对应的 Godot 插件；然后**为每个平台重新编译引擎**；Android 还要启用 Gradle 构建（AdMob 和 Play 结算插件都是 Android 插件 v2，必须 Gradle 构建）。
- 主流 AdMob 插件的新版本都要求 Godot 4.5 以上，而 spx 是 4.4.1。

**能直接用的**：游戏脚本可以 `import "net/http"`（spx 的解释器注册了标准库的 `net/http`、`os`、`os/exec` 等）。2026-10-25 本机实测：脚本从本地 HTTP 服务读到了配置文件（`NETTEST OK 200 v=1 price=399`）。所以**匿名统计、远程配置**不需要改 spx（注意：解释器里 `io.ReadAll`、`io.Copy` 不可用，要用 `Body.Read` 读）。

## 来源

- Steam / Microsoft：[Steam Direct 费用](https://partner.steamgames.com/doc/gettingstarted/appfee)、[Steam 定价](https://partner.steamgames.com/doc/store/pricing)、[Steam 退款](https://store.steampowered.com/steam_refunds/)、[Steam 分成汇总](https://presskit.gg/field-guides/how-much-does-steam-take)、[GameDiscoverCo：Steam 价格](https://newsletter.gamediscover.co/p/are-steam-game-prices-dropping-and)、[GameDiscoverCo：愿望单转化](https://newsletter.gamediscover.co/p/the-state-of-steam-wishlist-conversions)、[GameDiscoverCo：试玩版在线人数](https://newsletter.gamediscover.co/p/does-your-steam-demo-ccu-predict)、[VG Insights 2022 上半年](https://gamedevreports.substack.com/p/video-game-insights-steam-h1-2022)、[80.lv：Steam 收入报告](https://80.lv/articles/analysts-report-drop-in-game-revenue-on-steam-despite-growing-number-of-releases)、[Microsoft Store 分成](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/why-distribute-through-store)、[ID@Xbox](https://www.xbox.com/developers/id)
- Apple：[小型企业计划](https://developer.apple.com/app-store/small-business-program/)、[App 审核准则](https://developer.apple.com/app-store/review/guidelines/)、[Apple Arcade](https://developer.apple.com/apple-arcade/)
- Google Play：[服务费](https://support.google.com/googleplay/android-developer/answer/112622)、[2026 年费率调整](https://support.google.com/googleplay/android-developer/answer/16954621)、[家庭政策](https://support.google.com/googleplay/android-developer/answer/9893335)、[结算库版本要求](https://developer.android.com/google/play/billing/deprecation-faq)、[16 KB 页](https://android-developers.googleblog.com/2025/05/prepare-play-apps-for-devices-with-16kb-page-size.html)
- 广告：[AdMob GDPR / UMP](https://developers.google.com/admob/android/privacy/gdpr)、[AdMob 激励广告政策](https://support.google.com/admob/answer/7313578)、[AdMob iOS 数据披露](https://developers.google.com/admob/ios/privacy/data-disclosure)、[Adjust：ATT 同意率](https://www.adjust.com/blog/att-opt-in-rates-2025/)、[eCPM 基准汇总（2026-09）](https://blog.playio.co/mobile-game-ecpm-benchmarks-2026)、[GameAnalytics 2026 基准](https://www.gameanalytics.com/reports/2026-mobile-pc-gaming-benchmarks)、[Unity 变现指南](https://unity.com/resources/mobile-game-monetization-guide)
- Godot 插件：[godot-admob 版本](https://github.com/godot-sdk-integrations/godot-admob/releases)、[godot-google-play-billing 版本](https://github.com/godot-sdk-integrations/godot-google-play-billing/releases)、[Godot Android 插件（4.4 文档）](https://docs.godotengine.org/en/4.4/tutorials/platform/android/android_plugin.html)、[AppLovin MAX Godot](https://github.com/AppLovin/AppLovin-MAX-Godot)
