# 坦克大战 v5.0 · 技术前提

> [v5.0 规划](PLAN.md)的第三个方向：上架前游戏在技术上要补的能力。标注方式同规划总览：**代码**、**公开资料**、**推测**。本文的方案**都还没有实测**，P1 的验证结果会写回各节的“实测”小节。

| # | 能力 | 哪些平台需要 | 难度 | 阶段 |
|---|---|---|---|---|
| 1 | **手柄** | Steam Deck、Xbox；iPad 外接手柄、Steam 上的双人合作 | 中：要改 spx | P1 |
| 2 | 商店版构建（去掉模拟广告、解锁制） | 全部 | 低 | P1 |
| 3 | 存档 | 全部 | 低 | P1 |
| 4 | 平台打包：Steam depot、MSIX、iOS 签名、Android AAB | 各自 | 低~高 | P2~P4 |
| 5 | Xbox 主机：改写游戏逻辑 | Xbox 主机 | 很高 | v5 只评估 |

## 一、手柄

### 1.1 现状（代码）

- 游戏只认键盘、鼠标和单指触屏。1P：WASD + J，2P：方向键 + Enter，Esc 暂停。
- **spx 没有给游戏脚本提供手柄接口**：在 spx 源码（`c3c0da5`）里搜 `joypad` / `gamepad`，只有网页版引擎的 JS 输入库里有；Go 侧的输入管理（`input_manager.go`、`runtime_input.go`）只处理键盘和鼠标。
- Godot 引擎本身完整支持手柄（Windows、macOS、Linux、iOS 的 Game Controller、Android）。

### 1.2 方案

| 方案 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| **A. spx 补丁：手柄转按键（推荐）** | 在 spx 的输入层读 Godot 的手柄状态，转成游戏已经认识的按键事件：手柄 1 → 1P（WASD / J），手柄 2 → 2P（方向键 / Enter）；A → 开火 / 确认，B → 返回，Start → Esc；摇杆加死区 | **游戏代码基本不用改**，`onKey` 和 `keyPressed` 照常工作；双人合作直接支持两只手柄；补丁用现有的 `patch_spx.py` 维护 | 要读懂 spx 的输入管线；以后 spx 升级要重新适配。做通后给上游提 PR |
| B. Steam Input 键盘模拟 | 在 Steamworks 后台给游戏配一套“手柄 → 键盘”的官方配置 | 不改代码 | **只在 Steam 上有效**；按键提示对不上，Steam Deck 只能评“可玩”；**两只手柄映射出的按键会合并成同一个键盘输入，游戏分不清 1P / 2P，双人合作用不了**（[EXPERIENCE.md 3.2](EXPERIENCE.md#32-手柄与双人合作)）；其他平台没用 |
| C. 等 spx 上游加手柄接口 | 提 issue / PR | 最干净 | 时间不可控 |

先做 A 的验证（P1 spike）：能在 macOS 上用一只 Xbox 手柄控制 1P、两只手柄控制双人合作，就算通过。不通过就用 B 先上 Steam。

### 1.3 游戏里要跟着改的

| 内容 | 改动 |
|---|---|
| 按键提示 | `strings.py` 的 `hint.p1`、`hint.p2` 等只有键盘文字；`build.py` 再生成一套手柄版（A / B / Start 图标），检测到手柄时切换 |
| 菜单 | 主页、暂停、结算、复活询问都要能用十字键选、A 确认、B 返回。现在菜单靠快捷键（Enter、C、E、1~8）和鼠标点击，要加“当前选中项”的高亮 |
| 地图编辑器 | 现在靠鼠标点击 / 拖动和键盘快捷键（1~5、M、R、K、Enter）。手柄版：十字键移动光标，A 画，LB / RB 换工具，Y 镜像，Start 试玩 |
| 解释器限制 | 新增函数会占方法表（[架构文档 9.1](../ARCHITECTURE.md)），菜单选择尽量用舞台变量和已有的 `UI` kind |

### 1.4 实测

（P1 完成后填写：手柄型号、平台、结果。）

## 二、商店版构建

- `main.spx` 的常量块里加两行 `storeBuild = false`、`demoBuild = false`（各占一行，导出脚本按整行替换）。
- 打包命令：`build.sh <平台> --store [--demo]`，只在工作副本里把常量改成 `true`，产物放在 `dist/store/`、`dist/demo/` 或 `dist/store-demo/`。`--store` 找不到常量会直接失败，`--demo` 找不到只警告。打包脚本这部分已在 [#72](https://github.com/Qiniu-ERE/zero/pull/72) 做好，游戏里的常量和对应逻辑还没加。XBuilder 里打开的 `.xbp` 永远是路演版。
- `storeBuild` 为 `true` 时：不画横幅和原生广告卡；复活询问只有“免费复活 / 金币复活 / 放弃”；结算没有金币 ×2；选关按存档里的进度解锁。
- **试玩版**：再加一个 `demoBuild` 常量，只开放第 1~2 关、编辑器不能保存，结尾显示“购买完整版”。
- v4 的测试框架里给商店版和试玩版各加一组用例（差异点逐条测）。

## 三、存档与匿名统计

- 一个纯文本文件 `save.txt`，`key=value`，第一行是版本号（`v=1`）；读到不认识的版本就当作新存档，**不崩溃**。
- 内容：解锁进度、每关最高分、金币、已购外观、画风、语言、地图槽位（每张图一行，沿用 `edRows()` 的格式）。
- 位置：`os.UserConfigDir()/<新名字>/save.txt`，和现在的 `maps.txt` 同一个目录（PC 版已经验证能写）。iOS / Android 上 Go 的 `os.UserConfigDir()` 返回什么**要实测**；iOS 应用沙盒里应该落在应用自己的目录（推测）。
- Steam 云存档不用接 SDK：在 Steamworks 后台配置 Auto-Cloud，三个系统的目录对应见 [EXPERIENCE.md 3.4](EXPERIENCE.md#34-steam-云存档不用接-sdk)。

**匿名统计和远程配置（已验证可行）**：spx 的解释器注册了标准库的 `net/http`（还有 `os`、`os/exec` 等），游戏脚本可以直接发 HTTP 请求。2026-10-25 本机实测（spx 4.0，macOS，`spx run -headless`）：脚本 `import "net/http"` 后从本地 HTTP 服务读到配置文件，输出 `NETTEST OK 200 v=1 price=399`。注意解释器里 `io.ReadAll`、`io.Copy` 编译不过，要用 `resp.Body.Read` 读。

- 用途：关卡通过率、复活率、每关用时（判断难度）；远程调整金币价格等数值。
- 做法：玩家**第一次启动时询问是否发送匿名统计**（默认不发），只发随机 ID 和游戏事件，不收集个人信息；接收端一个 HTTP 接口按天存成文本文件。
- XBuilder（spx v3.3.0）里是否也有 `net/http` 没有验证；统计只在商店版打开。

## 四、暂不做：SDK 集成

Steamworks（成就、排行榜、创意工坊）、StoreKit / Play 结算（内购）、AdMob（广告）都要游戏脚本调用平台 SDK。spx 没有提供这样的接口：

- spx 的引擎是**带 spx 模块的定制版 Godot**（源码 `godot_modules/spx`），游戏脚本能用的引擎功能是一张**固定的函数表**（约 340 个 `SPX_BIND` 函数，Go 侧代码由生成器产生），里面没有调用任意 Godot 单例或插件的接口。
- 要接 SDK，需要在 spx 模块里加一个“宿主消息”接口（例如 `host_send(kind, arg)` / `host_poll()`），C++ 侧转给对应的 Godot 插件；然后**每个平台重新编译引擎**（spx 的 `buildctl` 有引擎构建流程）；Android 还要启用 Gradle 构建，因为 AdMob、Play 结算都是 Android 插件 v2。
- 主流 AdMob 插件的新版本要求 Godot 4.5 以上（[MONETIZATION.md 第五节](MONETIZATION.md#五技术前提为什么-sdk-现在接不上代码)），spx 是 4.4.1。所以手机上的内购和广告，实际都要等 spx 升级引擎。
- 网页版有 `syscall/js` 这条路（[v3.0 小游戏评估 4.2](../v3/WECHAT_MINIGAME.md#42-watchad-怎么接到微信关键问题)），但网页版不在本次的四个平台里。

PC 的 $0.99 买断不需要这些；手机和微信小游戏的激励视频、$0.99 去广告需要（[MONETIZATION.md 第一节](MONETIZATION.md#一结论2026-10-28-更新)），所以 PC 先上，宿主接口和微信 JS 桥同时推进。等商店版上架、有了真实数据，再决定要不要给 spx 做宿主接口。

## 五、Xbox 主机：改写还是等待

### 5.1 为什么现在的工程上不了主机

spx 游戏 = Godot 引擎 + Go 写的扩展（gdspx）+ Go 写的 XGo 解释器。主机移植模板（例如 W4 Games）解决的是 Godot 引擎这一层，**Go 不支持 Xbox 主机系统**，所以游戏逻辑跑不起来（[PLATFORMS.md 第四节](PLATFORMS.md#四xbox-主机为什么近期做不了)）。

### 5.2 三个选项

| 选项 | 做法 | 工作量（推测） | 风险 |
|---|---|---|---|
| **A. 改写成 GDScript** | 游戏逻辑（8 个 `.spx` 文件，约 2700 行、108 个函数）改写成 Godot 原生的 GDScript；造型 SVG、音效、地图数据、文案表直接复用 | 2~4 周，加上把 v4 的测试改写成 Godot 的测试 | 两套代码要同步（spx 版继续给 XBuilder 用）；主机移植模板的费用；需要公司主体 |
| B. 等 Go / spx 支持主机 | 例如通过 WASM 运行 | 不可控 | 可能永远不会有 |
| C. 只做 Xbox PC | Microsoft Store（PC），以后争取 PC Game Pass | 已在 P2 | 不是真正的主机 |

**建议**：v5 只做 C；Steam 达到决策点 2 的标准后，在 P5 出一份选项 A 的详细评估（报价、时间、主体），v6 再决定。

## 六、平台打包

| 平台 | 现在 | 要做的 |
|---|---|---|
| **Steam** | 三个平台的单文件程序（`build.sh desktop`） | 用 Steamworks 的上传工具传三个 depot；macOS 和 Linux 包的启动脚本里设了 `GODEBUG=asyncpreemptoff=1`（防止 Go 的 SIGURG 崩溃），Steam 的启动选项要指向启动脚本，而不是 `TankBattle-bin` |
| **Microsoft Store** | Windows zip | 用 MSIX Packaging Tool 封装；微软重新签名，不需要自己买证书。注意：spx 的启动器第一次运行时把引擎解压到用户缓存目录，MSIX 容器里能不能写**要实测** |
| **iOS** | 不签名的 IPA（`exportios` + `xcodebuild CODE_SIGNING_ALLOWED=NO`） | 用 Xcode 26 编译、开发者证书和描述文件签名、加隐私清单、上传 TestFlight。需要一台装 Xcode 26 的 Mac；GitHub Actions 额度恢复后也可以在 CI 上做 |
| **Android** | 调试签名的 APK | 等 spx 升级 Godot（AAB、目标 API 36、16 KB 页，见 [PLATFORMS.md 第六节](PLATFORMS.md#六google-play)）；gdspx 的 Go 库用新 NDK 加 16 KB 对齐参数重新编译；上传密钥不进仓库 |

所有正式签名的证书和密钥**都不进仓库**，路径和密码通过环境变量传给 `build.sh`（现在 Android 调试证书就是这样处理的）。证书丢了就没法更新已上架的应用，要备份到安全的地方。

## 七、测试

沿用 v4.0 的引擎内测试框架（`tools/test/run_spx.sh`）：

- 商店版、试玩版：广告位都不出现；复活只有免费 / 金币 / 放弃；试玩版只能玩第 1~2 关。
- 存档：正常、旧版本、损坏的存档文本都能读；测试时 `HOME` 指向临时目录（v4 已经这样做）。
- 解锁进度：通关解锁下一关，全部通关后能任意选关。
- 手柄：映射本身在 spx 里，游戏侧的测试直接调用映射后的按键处理；实机检查写进上架前检查表（[v4.0 测试方案第七节](../v4/TEST_PLAN.md#七发布前手工检查表)）。
- 新功能的 PR 合入前跑 `tools/test/pr_check.sh`，覆盖率不能低于基线（[v4.0 测试方案第八节](../v4/TEST_PLAN.md#八以后的版本怎么保持测试覆盖)）。
