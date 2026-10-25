# 坦克大战 v5.0 · 技术前提

> [v5.0 规划](PLAN.md)的第三个方向：变现方案落地前，游戏在技术上必须先具备的能力。标注方式同规划总览：**代码**、**公开资料**、**推测**。本文的方案**都还没有实测**，P1 的验证结果会写回各节的“实测”小节。

## 一、宿主桥

### 1.1 问题（代码）

广告、支付、埋点、排行榜都是平台提供的 JS / Java SDK，而游戏脚本运行在 spx 的 XGo 解释器里：

- spx **没有**给游戏脚本提供调用宿主的 API（[v3.0 小游戏评估 4.2](../v3/WECHAT_MINIGAME.md#42-watchad-怎么接到微信关键问题)，读 spx 源码确认）。
- 现在的 `watchAd()` 只是把状态切到 `stAd`、广播 `adFlow`、播 5 秒示例素材，然后直接发奖励。

所以“游戏 ↔ 宿主”的通道是整个商业化的前提。

### 1.2 协议：请求 + 轮询

不管底下用哪种通道，游戏这一侧都用同一套很小的协议，便于测试，也避开解释器的限制（[架构文档第 9 节](../ARCHITECTURE.md)：方法表有上限；从宿主回调进解释器的稳定性未知）：

```
游戏 → 宿主：hostSend(kind, arg string)       // 例如 "ad.reward", "revive"
宿主 → 游戏：游戏每帧调用 hostPoll() string     // 没有结果时返回 ""，有结果时返回 "ad.reward:ok" / "ad.reward:fail"
```

| kind | arg | 宿主做什么 | 返回 |
|---|---|---|---|
| `ad.reward` | `revive` / `double` | 播激励视频 | `ok`（看完）/ `skip`（中途关闭）/ `fail`（没有广告或出错） |
| `ad.banner` | `show` / `hide` | 显示或隐藏平台横幅（只在主页） | 无 |
| `game.state` | `play` / `pause` / `menu` | 门户 SDK 的 `gameplayStart/Stop`；广告期间宿主负责静音 | 无 |
| `track` | `事件名 k=v k=v` | 埋点（第三节） | 无 |
| `save` / `load` | 存档文本 | 网页版存档（第二节，只在 `os` 写不进去时用） | `load` 返回存档文本 |
| `config` | — | 读远程配置（第四节） | `key=value` 文本 |

`watchAd` 改成：发 `ad.reward` → 进入 `stAd` 等待 → `hostPoll()` 拿到结果 → `ok` 才发奖励；`fail` 时提示“暂时没有广告”，并提供金币复活。**等待最多 30 秒**，超时按 `fail` 处理，游戏不会卡死。

### 1.3 每个平台的通道

| 平台 | 通道 | 依据 | 状态 |
|---|---|---|---|
| **网页版 / H5 门户** | 游戏脚本 `import "syscall/js"`，`js.Global().Call("tankHostSend", ...)` 和 `js.Global().Get("tankHostResult")`；外壳页面 `play.js` 再转给门户 SDK。游戏在 `runner.html` 的 iframe 里，外壳和 iframe 同源，可以直接访问 `window.parent` | spx 的 Web 版解释器注册了 `syscall/js`（源码，[v3.0 评估 4.2](../v3/WECHAT_MINIGAME.md#42-watchad-怎么接到微信关键问题)） | **未验证**：不确定 XGo 类文件里能否导入、解释器里调用是否稳定。P1 第一件事 |
| 微信 / 抖音小游戏 | 同上，JS 侧接 `wx.*` / `tt.*` | 同上 | 未验证，依赖网页版的结论 |
| Android App | spx 的 Android 导出不带插件接口，游戏脚本调不到 Java；需要给 spx 提 PR，暴露 Godot 的 `Engine.get_singleton()` 或一个通用宿主消息接口，再用 Godot 的 AdMob 插件 | 推测 | 依赖上游，P4 再看 |
| 桌面版 | 不需要（不放广告） | — | — |
| 本地 `spx run`、XBuilder | 不需要；`hostSend` 走**模拟实现**，和现在的模拟广告一样 | — | 路演、XBuilder 里继续用 |

**桌面版和 XBuilder 没有 `syscall/js`**，所以真实桥的代码不能写进主代码。做法和 `touchUI` 一样：主代码只有协议和模拟实现，渠道版由 `build.sh` 在导出前替换一个文件（或把 `channel` 常量改成渠道名），XBuilder 里打开的 `.xbp` 永远是模拟版。

### 1.4 桥不通时的退路

| 退路 | 能做什么 | 代价 |
|---|---|---|
| 给 spx 提 PR，加官方的宿主消息接口 | 所有平台统一 | 要等上游合并，时间不可控 |
| 借文件系统传消息（游戏写文件、JS 读 Godot 文件系统） | 网页版、小游戏 | 小游戏模板每 5 秒同步一次文件，延迟太大（[v3.0 评估 4.2](../v3/WECHAT_MINIGAME.md#42-watchad-怎么接到微信关键问题)） |
| 只在外壳层放广告 | 例如进游戏前的片头广告、门户自己在游戏外放的横幅 | 没有激励视频，收入大幅降低；但门户版仍然能上线拿数据 |

### 1.5 实测

（P1 完成后填写：环境、步骤、结果、截图。）

## 二、存档

### 2.1 现在（代码）

- 只有自制地图能保存：`edFile()` 用 `os.UserConfigDir()` + `/TankBattle/maps.txt`，PC 版可用。
- 网页版里 `os.UserConfigDir()` 拿不到目录，`edFile()` 返回 `""`，保存会提示失败。
- 金币、最高分、设置都只在内存里。

### 2.2 设计

- **一个存档文件**，纯文本 `key=value`，第一行是存档版本号（`v=1`）。纯文本方便调试，也方便 v4 的测试框架直接构造存档。
- 内容：金币、已购物品、最高分、每日记录（日期 + 是否已领每日奖励）、画风、语言、地图槽位（每张图一行，沿用 `edRows()` 的格式）。
- 时机：结算、购买、改设置、编辑器保存时写；启动时读。读到不认识的版本号就当作新存档，**不崩溃**。

| 平台 | 存在哪里 | 状态 |
|---|---|---|
| Windows / macOS / Linux | `os.UserConfigDir()/TankBattle/save.txt`（和现在的 `maps.txt` 同一个目录） | 已验证能写（地图保存） |
| Android / iOS App | 同上，Go 的 `os.UserConfigDir()` 在 Android 上的返回值要核实 | 未验证 |
| 网页版 | 先试 `os` 能不能写到引擎的虚拟文件系统并持久化（Godot Web 的 `user://` 存在 IndexedDB，但 Go 的 `os` 是否落到那里不确定）；不行就走宿主桥的 `save` / `load`，存到 `localStorage` | 未验证（P1） |
| 微信小游戏 | 宿主桥 `save` / `load` → `wx.setStorageSync`；或者依赖模板把文件系统同步到 `wx.env.USER_DATA_PATH` | 未验证 |

### 2.3 实测

（P1 完成后填写。）

## 三、数据埋点

### 3.1 事件

| 事件 | 字段 | 触发 |
|---|---|---|
| `session_start` | 版本、渠道、语言、是否触屏 | 进入主页（每次启动一次） |
| `stage_start` | 关卡（1~8 / custom）、模式（单人 / 双人） | `startGame` |
| `stage_end` | 关卡、结果（win / lose / quit）、用时、得分、剩余生命、是否复活过 | `endGame`、暂停菜单退出 |
| `ad_offer` | 位置（revive / double） | 复活询问出现、结算出现 |
| `ad_start` / `ad_reward` / `ad_fail` | 位置、失败原因 | 宿主桥返回 |
| `revive_choice` | ad / coin / giveup | 复活询问点击 |
| `mode_enter` | coop / editor / demo | 进入模式 |
| `coin_earn` / `coin_spend` | 数量、来源 / 物品 | 结算、购买 |

指标和这些事件的对应关系见 [MONETIZATION.md 第五节](MONETIZATION.md#五指标与决策)。

### 3.2 怎么发出去

- 游戏 → 宿主桥 `track` → 外壳页面批量发送（每 10 秒或页面隐藏时，用 `navigator.sendBeacon`）。
- 接收端先用最简单的方案：一个 HTTP 接口把每条事件追加成一行 JSON，按天存到七牛云 Kodo；分析时下载下来用脚本统计。日活上来之后再换正式的统计服务。
- 门户自己的后台也有播放量、留存等数据，可以互相对照。

### 3.3 隐私

- 只用一个**随机生成的匿名 ID**（存在存档里），不收集姓名、手机号、设备号、位置。
- 网页版加隐私政策页面，说明收集什么、为什么、存多久。
- 广告的个性化同意（欧盟 GDPR 等）由门户 SDK / 平台处理；我们自己的埋点不做个性化，也不和广告共享。
- **桌面版和 App 版默认不发埋点**（没有宿主桥，也没有必要）。

## 四、远程配置

价格、广告等待超时、每日奖励数量这些数值，上线后需要调，不能每次都重新打包审核：

- 外壳页面启动时从 CDN 读一个 `config.txt`（`key=value`），通过宿主桥 `config` 交给游戏。
- 游戏里每个数值都有**内置默认值**，读不到配置时照常运行。
- 只调数值，不下发代码，不改玩法，避免平台审核问题。

## 五、渠道版构建

`build.sh` 增加渠道版目标，复用现在的打包流程：

| 目标 | 产物 | 和现有目标的区别 |
|---|---|---|
| `web`（已有） | 自有网页版 | 不变：模拟广告，路演用 |
| `web-crazygames`（新） | 上传到 CrazyGames 的包 | `channel = "crazygames"`；外壳加门户 SDK；去掉游戏内的模拟横幅和原生广告卡 |
| `minigame`（新） | 微信小游戏工程 | `spx exportminigame`；`channel = "wechat"`；打开 `touchUI`；隐藏双人入口（[v3.0 评估第五节](../v3/WECHAT_MINIGAME.md#五输入和适配)） |
| `android`（已有） | APK | P4 改成正式签名；上架 Google Play 要 AAB，spx 的 `exportapk` 是否能出 AAB 要核实 |

正式签名的证书**不进仓库**：放在本机，路径和密码通过环境变量传给 `build.sh`（现在的调试证书就是这样处理的，见 `GODOT_ANDROID_KEYSTORE_DEBUG_*`）。证书丢了就没法更新已上架的 App，要备份到安全的地方。

## 六、测试

沿用 v4.0 的引擎内测试框架（`tools/test/run_spx.sh`）：

- 宿主桥的模拟实现可以由测试控制返回值（`ok` / `skip` / `fail` / 超时），测“看完才发奖励”“失败时不发奖励”“超时不卡死”。
- 存档：构造各种存档文本（正常、旧版本、损坏）测读取；测试时 `HOME` 指向临时目录（v4 已经这样做）。
- 金币：结算公式、×2、每日奖励、购买、金币不足。
- 渠道版的差异（去掉的广告位、隐藏的入口）各写一条用例。
- 新功能的 PR 合入前跑 `tools/test/pr_check.sh`，覆盖率不能低于基线（[v4.0 测试方案第八节](../v4/TEST_PLAN.md#八以后的版本怎么保持测试覆盖)）。
