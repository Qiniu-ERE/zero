# 坦克大战 v3.0 · 微信小游戏可行性评估

> 本文评估用 `spx exportminigame` 把游戏导出成**微信小游戏**的可行性，是 [v3.0 规划](PLAN.md)里程碑 P2 的一项，也是 [跨平台评估](CROSS_PLATFORM.md) 3.4 节的展开。**只做评估和文档，不改游戏代码。**
>
> 依据分三类，文中都已标明：
> - **源码**：读 [goplus/spx](https://github.com/goplus/spx) 源码确认的（`c3c0da5`，spx 4.0.0，2026-10-24）。
> - **官方文档**：2026-10-24 查阅的微信开发者文档。微信规则经常变，发布前要重新核对。
> - **推测**：没有条件验证的判断。
>
> **这次没有在微信开发者工具或手机微信里运行过**（没有小游戏账号和 AppID），所以文中没有任何实测结果。

## 结论

**技术上可行，但不是“导出就能上线”。** spx 官方已经做好了导出命令和微信适配层，包体按现在的规则也放得下。真正要花工夫的是下面四件事：

| # | 卡点 | 严重程度 | 说明 |
|---|---|---|---|
| 1 | **广告接不进去** | 高 | 游戏代码跑在 wasm 解释器里，spx 没有给游戏脚本提供调用 JS 的接口，`watchAd` 没法直接调 `wx.createRewardedVideoAd`。要自己做一座桥（见第四节） |
| 2 | **只能触屏，而且只认一根手指** | 中 | 小游戏没有键盘，也没有 HTML，不能用 Web 版的“HTML 虚拟按键”。只能用游戏内的触屏模式 `touchUI`（已在 `feat/v3-release` 分支实现，给手机 App 用） |
| 3 | **真机性能和内存未知** | 中（未验证） | 要同时加载 Godot 引擎（31 MB）和 XGo 解释器（48 MB）两个 wasm，解释执行游戏脚本。iPhone 上能不能流畅跑、会不会被系统杀掉，只有真机能回答 |
| 4 | **账号和上线资质** | 中 | 需要注册小游戏账号拿 AppID；上线要过审核，游戏类目的资质要求要按微信当前规则准备；开广告要先开通流量主 |

包体**不是**卡点：按官方文档现在的规则（主包 ≤ 4 MB，主包 + 分包 ≤ 30 MB，普通分包单个不限），导出包估算约 15 MB（见第三节）。

建议：先花 1 天用测试号在开发者工具和两台真机（iPhone、安卓）上跑通，确认第 3 点。跑不动就不用继续；跑得动再做广告桥和触屏适配。

---

## 一、背景

- 游戏是 480×360 横屏，全键盘操作（1P WASD + J，2P 方向键 + Enter）。
- UI 文字在构建时已转成 SVG 路径，**运行时不用字体**（见 [架构文档第 7 节](../ARCHITECTURE.md)）。
- 有 4 个**模拟**广告位：主页横幅、右侧原生广告卡、复活激励视频、金币翻倍激励视频（见 [架构文档第 8 节](../ARCHITECTURE.md)）。

## 二、技术路径

### 2.1 `spx exportminigame` 做了什么（源码）

代码在 `cmd/spx/internal/command/export_web.go` 的 `ExportMinigame()`：

1. 和 `exportweb` 走同一段公共流程 `exportWebCommon("minigame")`：复制 Godot Web 运行时、`ispx.wasm`（XGo 解释器）、Go 的 `wasm_exec.js`，把工程打成 `game.zip`。
2. 把 Web 产物挪到 `rawWeb/`，再铺上小游戏模板 `cmd/spx/template/platform/webminigame/`。
3. **默认模式**：用 `brotli -q 11` 压缩 `engine.wasm` 和 `ispx.wasm`，把 `.br` 文件和 `*.zip` 放进 `engine/` 目录。本机必须装有 `brotli` 命令，否则报错。
   **`-build=fast`**：不压缩，直接放原始 `.wasm`，用于本地调试。
4. 把 `header.js`、`engine.js`、`go.wasm.exec.js`、`worker.message.manager.js`、`game.js` 合并成一个 `js/engine.js`，开头写入 `isWasmCompressed = true/false`。
5. 如果设置了环境变量 `WECHAT_DEV_TOOLS`，就调用 `$WECHAT_DEV_TOOLS/cli open --project <目录>` 打开微信开发者工具；没设置就提示手动打开。

导出前要先装小游戏运行时：在 spx 源码目录执行 `make setup-web MODE=minigame`（源码 `Makefile`，和 [跨平台评估 2.6](CROSS_PLATFORM.md) 里 Web 的坑一样）。

### 2.2 单线程（源码）

`docs/zh/dev/engine/web.md` 写明：`normal`、`minigame`、`miniprogram` 都是单线程构建（`threads=no`），只有 `worker` 模式用 pthread。小游戏不能用 `SharedArrayBuffer` 多线程，所以引擎、解释器、游戏逻辑都在同一个线程上跑。

另外，Release `runtime-v4.0.0` 里的 `web-minigame.zip`（7,427,766 字节）和 `web.zip` 的 SHA-256 **完全相同**，里面是 `godot.wasm`（32.8 MB）等 7 个文件。也就是说，小游戏用的就是普通单线程 Web 引擎，差别全在 JS 适配层。

### 2.3 导出包的结构（源码）

```
.builds/web/                    ← 用微信开发者工具打开这个目录
├─ game.js                      入口：检查更新 → Loader.load()
├─ game.json                    deviceOrientation: "portrait"；分包 engine/
├─ project.config.json          compileType: game；appid 写死为 spx 的示例 AppID
├─ images/                      加载页的 logo 和背景
├─ js/
│  ├─ loader.js                 画加载进度条，wx.loadSubpackage("engine")
│  ├─ runner.js                 读 engine/game.zip，创建 GameRunner，启动游戏
│  ├─ adpter.js                 WebAssembly → WXWebAssembly；crypto、TextEncoder 等补丁
│  ├─ weapp-adapter.js          模拟 DOM / canvas / 触摸事件
│  ├─ fetch.js                  用 wx.request 和文件系统 API 模拟 fetch
│  ├─ sdk.js                    文件系统读写（存到 wx.env.USER_DATA_PATH）
│  └─ engine.js                 合并后的 Godot JS + Go 启动代码 + spx 运行器
└─ engine/                      分包
   ├─ engine.wasm.br            Godot 引擎
   ├─ ispx.wasm.br              XGo 解释器
   ├─ engine.zip                Godot 资源包
   └─ game.zip                  我们的 .spx 源码和素材
```

启动顺序（源码 `loader.js`、`runner.js`、`cmd/ispx/web/game.js`）：加载页 → 下载 `engine` 分包 → `WXWebAssembly` 实例化 Godot → 实例化 `ispx.wasm`，套一层兼容对象骗过 Go 的 `instanceof WebAssembly.Instance` 检查 → `ispx_build(源码)` 编译 → `ispx_start()` 运行。

spx 自己的文档提醒了两个已知坑：Go wasm 实例的兼容层（`docs/zh/dev/wxgame_go_wasm_adapter.md`），以及部分真机上 Go 字符串解码出错导致 `panic: syscall/js: call of Value.Get on undefined`（`docs/zh/dev/wechat_minigame_go_wasm_panic.md`）。后者 spx 只给了排查方法，没有说已经解决。

### 2.4 导出和打开的步骤

| 步骤 | 内容 | 依据 |
|---|---|---|
| 1 | 在 [微信公众平台](https://mp.weixin.qq.com/) 注册小游戏账号，拿到 AppID；或者先用开发者工具的测试号 | 推测（常规流程） |
| 2 | 安装微信开发者工具 | — |
| 3 | spx 源码目录：`make setup-web MODE=minigame` | 源码 |
| 4 | 在工程副本里：`spx exportminigame`（要有 `brotli`）。可选：`export WECHAT_DEV_TOOLS=<开发者工具 cli 所在目录>` 自动打开 | 源码 |
| 5 | **改 `project.config.json` 的 `appid`**：模板里写死的是 `wx85fbcedfa360a1ce`，不是我们的 | 源码 |
| 6 | **改 `game.json` 的 `deviceOrientation` 为 `landscape`**：模板默认竖屏，我们的游戏是 4:3 横屏 | 源码 |
| 7 | 开发者工具里编译、预览，扫码在真机上看 | 未验证 |

第 5、6 步每次导出都会被模板覆盖，要写进导出脚本 `tools/export/` 做后处理。

注意：模板的 `project.config.json` 设置了 `packOptions.ignore: **/*.wasm`，打包时会忽略所有原始 `.wasm`。所以 `-build=fast` 的产物（原始 `.wasm`）**推测**只能在开发者工具本机调试，预览和上传要用默认的压缩模式（`.wasm.br` 不受影响）。

## 三、包体

### 3.1 微信的限制（官方文档，2026-10-24 查阅，需重新核对）

| 项目 | 规则 | 来源 |
|---|---|---|
| 主包 | 不超过 4 MB | 小游戏文档「分包加载 · 使用分包」 |
| 普通分包 | 单个不限大小 | 同上 |
| 独立分包 | 单个不超过 4 MB | 同上 |
| 主包 + 全部分包 | 不超过 30 MB | 同上 |
| wasm 加载 | `WXWebAssembly.instantiate` **只接受代码包内路径**，支持 `.wasm` 和 `.wasm.br`（基础库 2.14.0 起） | 小游戏文档「WebAssembly」 |

spx 自己的文档也提醒：“微信平台的包体限制可能调整，不能把 30M 当作永久规则”。这些数字上线前要再查一次。

### 3.2 我们的估算

用 [跨平台评估 5.2](CROSS_PLATFORM.md) 在 Web 导出上实测的大小（Web 和小游戏用的是同一个引擎和解释器，见 2.2）：

| 文件 | 位置 | 大小 |
|---|---|---|
| `engine.wasm.br` | 分包 `engine/` | 4.7 MB |
| `ispx.wasm.br` | 分包 `engine/` | 6.4 MB |
| `game.zip` | 分包 `engine/` | 3.3 MB |
| `engine.zip`（Godot 资源包） | 分包 `engine/` | 未测，推测很小 |
| `js/`、`images/` | 主包 | 未测；`godot.js` 原始 550 KB，模板 JS 合计 81 KB，推测远小于 4 MB |
| **合计** | | **约 15 MB** |

结论：按现在的规则，**主包 < 4 MB、总量约 15 MB < 30 MB，放得下**。

注意两点：

- **解释器最占地方**：`ispx.wasm` 占总量的四成多。它在内存里解压后是 48 MB，加上引擎 31 MB，真机内存压力比包体更值得担心（见第六节）。
- `game.zip` 要导出干净：`exportweb` 会把整个工程目录打进去，留着 `.builds/` 会涨到 85 MB（[跨平台评估 5.2](CROSS_PLATFORM.md)），小游戏导出同一段代码，问题也一样。

### 3.3 如果以后包体不够用

| 办法 | 能不能用 | 依据 |
|---|---|---|
| 拆更多分包 | 可以；普通分包单个不限，但受 30 MB 总量限制 | 官方文档 |
| wasm 放 CDN | **不行**，`WXWebAssembly` 只能读包内路径 | 官方文档 |
| `game.zip` 放 CDN | 理论上可以，但要改适配层：`runner.js` 写死读 `engine/game.zip`；`fetch.js` 只有请求头带 `Accept: application/octet-stream` 时才按二进制下载，否则按文本处理，zip 会被损坏 | 源码 |
| 用编译模式代替解释器，去掉 `ispx.wasm` | **现在不行**。`spx buildweb` 能把项目编译成 Go wasm，但 `exportminigame` 固定复制解释器的 `ispx.wasm`，运行器也依赖只有解释器才注册的 `ispx_build` / `ispx_start`。要改 spx 才能用 | 源码（`build.go`、`export_web.go`、`pkg/ispx/js.go`） |

## 四、广告接入

### 4.1 广告位对照

| 我们的模拟广告位 | 微信广告组件 | 接口 | 说明 |
|---|---|---|---|
| 主页底部横幅 | Banner 广告 | `wx.createBannerAd` | 原生组件，盖在画布上方，位置用屏幕像素指定 |
| 右侧面板原生广告卡 | 原生模板广告 | `wx.createCustomAd` | 同上；要把游戏坐标（中心 (162, -113)，120×86）换算成屏幕像素，还要考虑横屏和黑边 |
| 复活：激励视频 | 激励视频广告 | `wx.createRewardedVideoAd` | `onClose` 回调里 `res.isEnded === true` 才发奖励（官方文档） |
| 结算：金币 ×2 | 激励视频广告 | 同上 | 同一个实例；官方文档提醒每个用户每天能看的次数有限，要先判断能不能加载成功 |
| （没有） | 插屏广告 | `wx.createInterstitialAd` | 可以放在关卡之间；现在的设计里没有，**不建议加**，和“战场里没有广告”的原则一致 |

这次查到的官方广告文档目录里只有 Banner、插屏、原生模板和激励视频，没有格子广告，推测已被原生模板广告取代，不考虑。

**开广告的前提是开通“流量主”。** 开通条件（用户量门槛等）要在微信公众平台上查当前规则，这次没有核实。

### 4.2 `watchAd` 怎么接到微信（关键问题）

现在的流程：`watchAd(reward)` 把状态设成 `stAd`，广播 `adFlow`，播 5 秒示例素材，然后发奖励。

难点：游戏脚本在 `ispx.wasm` 解释器里运行。我们查了 spx 源码：

- spx **没有**给游戏脚本提供调用 JS 或宿主的 API（没有类似 Godot `JavaScriptBridge` 的东西）。`pkg/ispx/js.go` 只向 JS 暴露了 `ispx_build`、`ispx_start`、`ispx_stop` 等给宿主用的函数。
- 但是 Web 版解释器**注册了 `syscall/js` 包**（`pkg/ispx/embedded_pkgs_js.go`，只在 `js && wasm` 构建里有）。理论上游戏脚本可以 `import "syscall/js"`，调用 `js.Global()`。**这一点没有实测**，不确定 XGo 类文件里能不能这样导入、`js.FuncOf` 回调到解释器函数是否稳定。

可选方案：

| 方案 | 做法 | 优点 | 风险 |
|---|---|---|---|
| **A. 脚本里用 `syscall/js`（推荐先试）** | 小游戏版的 `watchAd` 调 `js.Global().Call("tankShowAd", reward)`；JS 侧（加在模板的 `runner.js` 后面）调 `wx.createRewardedVideoAd`，看完后把结果写进一个全局变量；游戏每帧用 `js.Global().Get(...)` **轮询**这个变量，拿到结果再发奖励 | 不改 spx；轮询避免从 JS 回调进解释器 | 未验证能否导入；PC 版和 `spx run` 没有 `syscall/js`，所以要由导出脚本替换一个文件（和 `touchUI` 的做法一样），不能写进主代码 |
| B. 给 spx 提 PR，加一个通用的宿主消息接口 | 例如脚本 `callHost(name, arg)`，宿主回一条 `onMsg` | 干净，Web、App 都能用 | 要等上游合并 |
| C. 借文件系统传消息 | 脚本写文件，JS 定时读 Godot 文件系统 | 不依赖 `syscall/js` | 很别扭；模板的文件同步是每 5 秒一次（`runner.js`），延迟大 |

横幅和原生广告卡比较简单：不需要回调结果，只要在状态变化时通知 JS“显示 / 隐藏哪个广告位”，用同一座桥即可。游戏里原来画模拟广告的位置要改成留空，让微信的原生组件盖在上面。

## 五、输入和适配

| 项目 | 现状 | 小游戏里怎么办 | 依据 |
|---|---|---|---|
| 操作 | 全键盘 | 小游戏没有键盘，也没有 HTML 页面，[跨平台评估 2.4](CROSS_PLATFORM.md) 的“HTML 虚拟按键”**用不了**。复用 `touchUI` 触屏模式：右侧方向盘，按住移动并自动开火 | `touchUI` 在 `feat/v3-release` 分支的 `main.spx` / `Player.spx` / `UI.spx`，给 Android / iOS 包用 |
| 多指 | — | Godot 把触屏当作单点鼠标，只认一根手指，所以 `touchUI` 才设计成“按方向就自动开火” | 跨平台评估 4.2 |
| 触摸事件 | — | 模板的 `weapp-adapter.js` 会把微信的触摸事件转成 DOM `TouchEvent` 交给引擎；能不能正确变成鼠标事件**未验证** | 源码 |
| 另一个办法 | — | 在 JS 适配层把触摸转成合成键盘事件发给引擎（Web 版已验证引擎收得到合成键盘事件），这样可以多指；但小游戏里只有一块屏幕画布被引擎占着，按钮还得画在游戏里。**未验证** | 推测 |
| 双人合作 | 一台电脑两套键位 | 手机单指输入做不了，小游戏版隐藏双人入口 | 推测 |
| 地图编辑器 | 鼠标点击 / 拖动 | 单指点击和拖动可以用；键盘快捷键（1~5、M、R、K、Enter）要换成按钮，或者小游戏版先不开放 | 推测 |
| 屏幕方向 | 480×360 横屏 | `game.json` 改成 `landscape`；引擎等比缩放留黑边 | 源码 |
| 字体 | UI 文字是 SVG 路径 | **不受影响**。只有模板加载页的进度百分比用了 canvas 文字 | 源码 |
| 音效 | `assets/sounds/` | spx 文档说小游戏音频要特殊适配，由模板处理；效果**未验证** | spx `web.md` |
| 存档 | 只在内存里 | 模板的 `sdk.js` 会把引擎文件系统每 5 秒同步到 `wx.env.USER_DATA_PATH`，以后做最高分持久化可以用 | 源码 |

## 六、风险和待验证

下面这些没有小游戏账号和真机就验证不了：

| # | 待验证 | 怎么验证 | 不行怎么办 |
|---|---|---|---|
| 1 | 开发者工具里能不能跑起来（导出包本身是否完整） | 测试号 + 开发者工具 | 对照 spx 的两篇排查文档定位，给 spx 提 issue |
| 2 | **iPhone 真机的内存和帧率**：两个 wasm 解压后约 80 MB，还要解释执行 | 真机预览，看帧率和是否闪退 | 等 spx 支持小游戏用编译模式；否则放弃小游戏 |
| 3 | 安卓真机是否出现 Go 字符串解码 panic | 真机预览 | 按 spx 文档的方法给 `go.wasm.exec.js` 打补丁 |
| 4 | 首次加载时间（下载约 15 MB 分包 + 解压 + 编译） | 真机 4G / Wi-Fi 计时 | 加载页做好进度提示；分包预下载 |
| 5 | 触摸能不能驱动 `touchUI` | 真机操作 | 在 JS 适配层把触摸转成键盘事件 |
| 6 | 游戏脚本能不能 `import "syscall/js"` | 本地 `spx exportweb` 在浏览器里先试（不需要微信账号） | 方案 B：给 spx 提 PR |
| 7 | 音效是否正常、是否需要用户先点一下 | 真机 | 主页加“点击开始” |
| 8 | 流量主开通条件、游戏类目上线资质、审核时间 | 公众平台 | 先上线无广告版本 |
| 9 | 包体规则和基础库版本是否有变化 | 上线前查官方文档 | — |

第 6 项不需要微信账号，可以最先做。

## 七、里程碑

| 阶段 | 内容 | 前提 | 估算 |
|---|---|---|---|
| **M0 跑通** | 导出脚本加小游戏模式（改 AppID、横屏、打开 `touchUI`），测试号在开发者工具和两台真机上跑；记录加载时间、帧率、内存 | 测试号、真机 | 1 天 |
| **M1 桥** | 验证 `syscall/js`（风险 6）；做 `watchAd` 桥和 JS 侧的激励视频、Banner、原生模板广告；广告未开通时退回“不显示广告位” | M0 通过 | 1.5~2 天 |
| **M2 适配** | 小游戏版隐藏双人入口；编辑器快捷键换成按钮或先关闭；原生广告卡的屏幕坐标换算 | M0 通过 | 1~1.5 天 |
| **M3 上线** | 正式 AppID、类目资质、审核；开通流量主后换成正式广告单元 ID | 账号、资质 | 视审核而定 |

合计开发约 3.5~4.5 天，不含审核。M0 不通过（主要是 iPhone 性能）就停在 M0，不做后面的事。
