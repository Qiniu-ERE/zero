# 坦克大战 v4.0 · 测试方案

本文是 v4.0 的测试设计：分几层测、引擎内的测试怎么写怎么跑、要测哪些用例、覆盖率怎么算、怎么在本地检查（不用 CI）。总览和里程碑见 [PLAN.md](PLAN.md)。

> 本文最早是规划稿。第二、四、五节已经按实际实现更新（2026-10-25，v4.0.1；第三节的用例清单和第五节的工具跟进到 v5 第一批修复）：文件名、函数名、数字以仓库里的代码为准，日常用法见[架构文档第 10 节](../ARCHITECTURE.md#10-测试与演示视频)。

## 一、测试分层

| 层 | 测什么 | 工具 | 速度 | 什么时候跑 |
|---|---|---|---|---|
| **L1 构建工具** | `check.py`、`strings.py`、`textpath.py`、`build.py` 的生成结果 | Python `unittest`（不加第三方测试库） | 几秒 | 每个 PR |
| **L2 游戏逻辑** | 舞台函数和精灵：地图、格子、子弹、地形、敌人、得分、生命、编辑器 | 引擎内测试（第二节） | 每组约 10 秒 | 每个 PR |
| **L3 游戏流程** | 状态机的每条边、复活、激励视频奖励、结算、下一关、双人合作 | 引擎内测试，按真实时间等待异步流程 | 每组 10~30 秒 | 每个 PR |
| **L4 网页外壳** | `tools/export/web/play.js`：虚拟按键映射、多点触控、双人按钮 | `node --test`（Node 自带） | 几秒 | 每个 PR |
| **L1.5 XBuilder 兼容**（T09） | 游戏代码在 XBuilder 线上的 spx v3.3.0 下也能编译通过（[PR #18](https://github.com/Qiniu-ERE/zero/pull/18) 的问题：`rand(int, int)` 在 v3.3.0 返回 `float64`，在 4.0 返回 `int`） | 用 spx v3.3.0 的源码和对应版本的 xgo 做类型检查（和 PR #18 的验证方法相同） | 约 1 分钟 | 每个改了 `TankBattle/` 的 PR |
| **L5 平台启动** | 打包后的程序能启动、进入主页、开一局 | 本机打包 + 启动测试（macOS 在本机；Linux 在 `linux_vm.sh` 的虚拟机里自动测；Windows 手工） | 几分钟 | 发布前 |
| **手工** | 按键手感、画面、声音、手机触屏 | 发布前检查表（第七节） | — | 发布前 |

原则：**能在 L1 / L2 测的不放到 L3**（越往下越慢、越容易因为时间不稳定而偶发失败）；L5 只回答“能不能启动”，不重复测规则。

## 二、引擎内测试框架

### 2.1 原理

和 `tools/dev/record_demo.sh` 一样：**不改仓库里的游戏**，复制一份工程，把测试脚本追加到副本的 `main.spx` 末尾，用 `spx run -headless .` 运行。测试脚本在舞台的 `onStart` 里，能直接读写舞台变量、调用舞台函数和精灵的公开函数。2026-10-24 已用 spx 4.0.0 验证可行（见 [PLAN.md 第二节](PLAN.md#二可行性原型已经跑通)）。

### 2.2 目录和命令

```
tests/
├── spx/                      # 引擎内测试：每个文件一组（共 19 组），每组单独起一个进程
│   ├── boot.spx              # 启动（B01、B02），也用于安装包启动测试 B03
│   ├── grid.spx              # 地图与格子（G01~G08）
│   ├── bullets.spx           # 子弹和地形（C01~C07）、真实发射子弹打自己的老鹰（C21~C24）
│   ├── spawn.spx             # 出兵（C08、C09）
│   ├── score.spx             # 得分（C10、C11）、生命显示（C20）
│   ├── player.spx            # 玩家坦克（C12~C14）
│   ├── enemy.spx             # 敌人挨打（C15）
│   ├── theme.spx             # 画风和语言（C16）
│   ├── clash.spx             # 子弹相撞、正对一块砖（C17、C18）
│   ├── flow_home.spx         # 流程：主页出发、回到主页（F01~F04、F16）、主页按钮（F34）、选关画面（F35）
│   ├── flow_revive.spx       # 流程：战败、复活、激励视频（F05~F10、F19、F20、F30~F33）
│   ├── flow_result.spx       # 流程：结算、金币、下一关、全部通关（F11~F15、F18）
│   ├── flow_custom.spx       # 流程：自制地图试玩（F17）
│   ├── flow_demo.spx         # 流程：路演演示（F22）
│   ├── pause.spx             # 暂停菜单（F25~F29）
│   ├── editor.spx            # 地图编辑器（E01~E06、E08~E15）
│   ├── editor_parity.spx     # E07：edCheck() 和 check.py 结论一致（游戏这一半）
│   ├── coop.spx              # 双人合作（P01~P08、P10）
│   └── touch.spx             # 触屏模式（P09、P11、P12，文件里写了 // touch: true）
├── tools/                    # L1（Python unittest）：test_check.py、test_strings.py、test_assets.py、test_editor_maps.py、test_xbuilder.py、
│                             #   test_coverage_tool.py（覆盖率工具）、test_release_tools.py（打包发布工具）
├── web/                      # L4：play.test.mjs
├── data/editor_maps.txt      # E07 用的 248 张编辑器地图（gen_editor_maps.py 生成）
└── coverage-baseline.json    # 覆盖率基线（第八节）
tools/test/
├── run_all.sh                # 一条命令跑完：构建工具 + 网页外壳 + 引擎内测试
├── run_spx.sh                # 跑一组或全部引擎内测试
├── prelude.spx               # 断言函数，插到副本 main.spx 的第一个 func 前面
├── spx_coverage.py           # 插桩并统计覆盖率（第四节）
├── update_baseline.sh        # 完整跑两遍，生成覆盖率基线
├── pr_check.sh               # PR 合入前的本地检查（第五节）
├── xbuilder_check.sh         # XBuilder 兼容检查（T09）
├── package_boot.sh           # 安装包启动测试（B03）
├── dist_boot.sh              # 直接运行要发出去的安装包（B14）
├── difficulty.sh             # 难度模拟（8 关难度曲线，#63）
└── gen_editor_maps.py        # 生成 tests/data/editor_maps.txt
```

```sh
tools/test/run_all.sh                            # 全部
tools/test/run_spx.sh tests/spx/flow_revive.spx  # 只跑一组
tools/test/run_spx.sh --coverage                 # 全部引擎内测试 + 覆盖率报告
SKIP_SPX=1 tools/test/run_all.sh                 # 没装 spx：只跑构建工具和网页外壳的测试（会列为“⚠️ 跳过”）
tools/dev/venv.sh                                # 第一次：建 .venv（锁定版本的 fontTools 等），测试脚本不设 PYTHON 时自动用它
```

### 2.3 输出协议

测试进程的退出码永远是 0（`exit` 不能带状态码），所以 `run_spx.sh` 靠解析输出判断结果：

| 输出行 | 含义 |
|---|---|
| `TEST PASS <用例 ID 和说明>` | 一个断言通过 |
| `TEST FAIL <用例 ID 和说明> got=<实际> want=<期望>` | 一个断言失败（`tCheck` 没有 got / want） |
| `TEST XFAIL <用例 ID 和说明>（已知问题：…）` | 已知问题还没修好，不算失败，汇总里列出 |
| `TEST XPASS <用例 ID 和说明>（…）` | 已知问题已经修好，算失败，提醒把 `tXfail` 改成 `tCheck` |
| `TEST DONE <组>` | 这一组跑完了；通过和失败的个数由 `run_spx.sh` 自己数 |

**判定为失败**：出现任何 `TEST FAIL` 或 `TEST XPASS`；没有 `TEST DONE`（中途崩溃或者卡住）；超时（默认每组 60 秒，测试文件里写 `// timeout: 秒数` 可以改）；输出里有 `panic`、`failed to build`（编译失败）或 `cannot alloc method`（[方法表上限](../ARCHITECTURE.md#91-方法表上限启动报错-cannot-alloc-method--cap2560)）。

### 2.4 写法

```go
// tests/spx/flow_revive.spx（节选；断言函数来自 tools/test/prelude.spx）
// timeout: 90
onStart => {
	wait 3                       // 先让游戏完成初始化（和截图脚本的约定一样）

	playStage 1
	wait 0.5
	tCalm                        // 清掉敌人和子弹、不再出兵，避免随机因素
	baseDestroyed
	tInt "F05 基地被毁 → 复活询问", state, stRevive
	tCheck "F05 战场冻结", gameOver
	// ……
	tDone "flow_revive"          // 输出 TEST DONE 并退出
}
```

`prelude.spx` 提供的函数：

| 函数 | 作用 |
|---|---|
| `tCheck(说明, 条件)` | 条件为 true |
| `tInt` / `tStr` / `tNum(说明, 实际, 期望)` | 整数 / 字符串相等；小数相差不到 0.001 |
| `tXfail(说明, 条件, 问题)` | 已知问题（见第九节） |
| `tAt(行, 列)` | 第几行第几列的格子编号 |
| `tCalm` | 清掉敌人和子弹、不再出兵，地图保留 |
| `tQuiet` | 开第 1 关，`tCalm`，再把地图清空 |
| `tWaitState(状态, 秒)` | 等到 `state` 变成指定状态，最多等几秒，返回是否等到 |
| `tDone(组名)` | 输出 `TEST DONE` 并退出 |

约定：

- **一组一个进程**。游戏状态全在舞台变量里，同一个进程里的用例会互相影响；组内的用例按顺序写，需要干净状态时先调用 `goHome`。
- **用例 ID 写进断言说明**（`F05`），和第三节的清单一一对应，覆盖率报告靠它统计规则覆盖。
- **不依赖随机结果**。`spawnEnemy` 的坦克类型、`edRandom` 的地图都是随机的：要么测不变量（例如“随机地图一定通过检查”“出生点只在 0 / 6 / 12 列”），要么多次采样测比例范围。
- **异步流程要等**。`reviveFlow`、`adFlow`（5 秒）、出生保护等放在消息处理里异步执行，测试用 `tWaitState` 等到状态变化（或者按流程本身的时长 `wait`），不写死很长的等待。
- **不要碰真实的存档**。`edSave` 写到 `os.UserConfigDir()/TankBattle/maps.txt`，`run_spx.sh` 运行前把 `HOME`、`XDG_CONFIG_HOME`（Windows 上是 `APPDATA`）指向临时目录，避免覆盖玩家自己画的地图。
- **函数要写在第一个事件处理之前**（[解释器限制 9.3](../ARCHITECTURE.md#93-其他)），所以断言函数放在 `prelude.spx` 里，测试文件里需要的辅助函数写成 `onStart` 里的闭包。
- 测试只追加到舞台，**不给任何精灵加字段**，不会改变方法表的占用；启动测试 `boot.spx` 本身就能发现“改了精灵字段导致启动失败”的问题。

## 三、测试用例清单

ID 规则：`T` 构建工具、`G` 地图与格子、`C` 对局规则、`F` 流程状态机、`E` 地图编辑器、`P` 双人合作、`W` 网页外壳、`B` 启动。每条用例在实现时写进对应测试文件的断言说明里。

### 3.1 构建工具（L1）

| ID | 用例 |
|---|---|
| T01 | `check.py` 对 `main.spx` 里的 8 张地图全部通过 |
| T02 | `check.py` 能发现：行数 / 列数不对、未知字符、没有基地或基地位置不对、出生点被堵、出生点到不了基地、玩家到不了出生点、基地旁边有钢墙或水面（每种问题一条反例） |
| T03 | `check.py map.txt` 读文本文件；有问题时退出码非零 |
| T04 | `strings.py` 每个 key 都有非空的中文和英文；没有重复 key |
| T05 | `textpath.py` 遇到字体里没有的字直接报错 |
| T06 | 生成文件没有过期：运行 `build.py` 后 `git diff --exit-code TankBattle/` 没有变化（造型、`index.json`、`UI.spx` 的 `GENERATED` 区块） |
| T07 | `build.py` 连续运行两次结果完全相同（生成是确定的） |
| T08 | 游戏代码里引用的每个文案 key（`toast "msg.…"`、`stageTip()` 返回值）在 `strings.py` 里都存在 |
| T09 | 游戏代码在 XBuilder 线上的 spx v3.3.0 下也能编译（`tools/test/xbuilder_check.sh`：复制 `.spx` 到临时目录，写一个依赖 spx v3.3.0 的 `go.mod`（`//xgo:class`），用 spx v3.3.0 对应的 xgo 生成 Go 代码，生成时做完整的类型检查）；把一处 `int(rand(…))` 改回 #18 修复前的写法，必须报出 `mismatched types float64 and int`。在 #18 修复前的代码上运行，报出的两个错误和当时 XBuilder 报的完全相同（`main.spx:545:8`、`main.spx:1113:5`）。spx 4.0 由引擎内测试覆盖 |

v5 第一批（[#68](https://github.com/Qiniu-ERE/zero/pull/68)、[#70](https://github.com/Qiniu-ERE/zero/pull/70)、[#72](https://github.com/Qiniu-ERE/zero/pull/72)）给打包和测试工具也加了单元测试（B13），没有编用例号，跟着 `run_all.sh` 一起跑，都用临时目录里的小样本，不联网、不打包：

| 文件 | 测什么 |
|---|---|
| `tests/tools/test_coverage_tool.py` | `spx_coverage.py`：找函数和事件处理、插桩、读日志、生成基线（只覆盖到一次的记为不稳定）、和基线比较 |
| `tests/tools/test_release_tools.py` | `patch_spx.py` 的版本号换算和报错；`env.sh` 从 CHANGELOG 取版本号（认得 `-rc.1`），Go / xgo 版本和工作流一致、sha256 格式正确；`release_local.sh` 的 `DRY_RUN`（按版本号回退、预发布的包不混入、`--append` 合并校验和、已有 Release 拒绝新建、`BUILD_LOCAL.md` 检查）；`build.sh` 的 `--store` / `--demo` 和补丁校验和 |

### 3.2 地图与格子（L2）

| ID | 用例 |
|---|---|
| G01 | `levelMap()` 对第 1~8 关都返回 13 行、每行 13 个字符 |
| G02 | `cellX` / `cellY` / `cellIndex` 互为逆运算；战场外的坐标 `cellIndex` 返回 -1 |
| G03 | `buildMap()` 之后 `grid` 和 `levelMap()` 一致（字符和数字编码的对应：空地 0、砖 1、钢 2、水 4、草 5、基地 9） |
| G04 | `blocksTank`：砖、钢、裂砖、水、基地挡坦克；空地、草丛不挡 |
| G05 | `tankBlocked` 在边界外返回 true |
| G06 | `stageTune()` 第 1~8 关的重型 / 快速占比、出兵间隔、场上上限和 README 的关卡表一致 |
| G07 | `stageTip()`：第 1 关 `msg.start`，第 n 关 `msg.stage<n>`，自制地图 `msg.ed.play` |
| G08 | `snapX` / `snapY` 把坐标对齐到格子，`dirDX` / `dirDY` 四个方向正确 |

### 3.3 对局规则（L2）

| ID | 用例 |
|---|---|
| C01 | 砖墙要打两下：`breakBrick` 第一次 1 → 3（裂砖），第二次 3 → 0 |
| C02 | `hitPoint` 打钢墙返回 true，钢墙不变 |
| C03 | `hitPoint` 打水面、草丛、空地返回 false（子弹能飞过） |
| C04 | `hitPoint` 打基地 → `baseDestroyed`；路演演示（`autopilot`）时基地不会被打掉 |
| C05 | `bulletHit` 的两个检测点：一发子弹能同时打掉并排的两块砖 |
| C06 | `bulletDir`：2P 子弹朝向加 1000 后能还原；1P 的朝向不变 |
| C07 | `nearestPlayer`：单人时永远是 1；双人时返回离得近的那辆 |
| C08 | `spawnEnemy` 依次在左、中、右三个出生点出兵；`spawned`、`enemiesAlive` 正确增加 |
| C09 | `spawnEnemy` 的坦克类型比例：每关采样 300 次，重型 / 快速占比在 `stageTune()` 配置的 ±10% 以内 |
| C10 | `enemyKilled`：加分、`killed` 加 1（顶栏的敌军剩余按 `killed` 显示，v5 去掉了 `enemiesLeft`）、刷新最高分；第 20 辆 → 胜利结算（战场运行时才判胜利，见 F33） |
| C11 | 最高分只升不降 |
| C12 | 屏幕上同时只能有 1 发自己的子弹（`pbCount`） |
| C13 | 出生时有 3 秒保护，保护期内中弹不扣命 |
| C14 | 生命用完 → `defeat` |
| C15 | 重型坦克要打 3 发；普通 / 快速坦克 1 发 |
| C16 | `switchTheme` / `switchLang` 切换后 `look()` / `langCode()` 的后缀正确，切两次回到原样 |
| C17 | 子弹迎面相撞互相抵消（横着、竖着各 5 次都要抵消，敌人子弹也消失）；错开 3 像素要抵消，错开 12 像素、相邻两行擦肩而过不能抵消。v4.0 时是**已知问题**（`tXfail`），v4.0.1 修复后改回普通断言，见第九节 |
| C18 | 正对一块砖（两个检测点在同一格）只打裂，不会一发打碎（v3.0.2 修复） |
| C19 | 路演演示（自动驾驶）的得分不算最高分（v3.0.2） |
| C20 | 生命显示（`lifeLook`）：3 条、2 条照旧；4 条显示图标、`lifex4`、第 3 个不显示；2P 5 条命是 `life2_on`、`lifex5`；超过 9 条也只显示 ×9（A15） |
| C21 | 真实发射子弹（不直接调用 `hitPoint`）：第 1 关 1P 在出生点朝右打，第 1 发护墙砖裂开、第 2 发砖碎、老鹰还在，第 3 发老鹰被自己打掉 → 复活询问 |
| C22 | 1P 在基地正上方（第 9 行第 6 列）朝下打：第 2 发上方护墙砖碎、老鹰还在，第 3 发打掉老鹰 |
| C23 | 双人，2P 在出生点朝左打：第 2 发右边护墙砖碎，第 3 发打掉老鹰 |
| C24 | 路演演示（`autopilot`）从 1P 出生点朝右打 4 发：护墙砖照样打碎，老鹰打不掉、还在对局 |

### 3.4 流程状态机（L3）

[架构文档第 5 节](../ARCHITECTURE.md#5-游戏流程状态机)的状态图原来一共 16 条边，每条至少一个用例（F01~F16）；v5 加了选关画面的 3 条边，由 F35 覆盖。另加规则用例：

| ID | 用例 |
|---|---|
| F01 | 主页 → 对局：`confirm()`（Enter / 空格）从第 1 关开始，`coop` 为 false |
| F02 | 主页 → 对局：`playStage(n)` 选关，`stage = n`、`stageScore = 0` |
| F03 | 主页 → 对局：`newGame(1, true)` 双人合作 |
| F04 | 主页 → 编辑器：`openEditor()`，`state = stEdit` |
| F05 | 对局 → 复活询问：本关第一次战败（基地被毁） |
| F06 | 对局 → 复活询问：本关第一次战败（生命用完） |
| F07 | 复活询问 → 播放广告：`confirm()` → `watchAd(rewardRevive)` |
| F08 | 复活询问 → 结算：放弃 / 7 秒倒计时结束，判负 |
| F09 | 播放广告 → 对局：复活奖励 = 修复基地、额外 1 条命、`revived = true`（v5 起还会清场，见 F30） |
| F10 | 对局 → 结算：复活过之后再次战败，直接结算 |
| F11 | 对局 → 结算：消灭 20 辆，胜利 |
| F12 | 结算 → 播放广告 → 结算：金币翻倍，`doubled = true`；第二次不能再翻倍 |
| F13 | 结算 → 对局：胜利后 `again()` 进入下一关，得分保留，`stageScore = score` |
| F14 | 结算 → 对局：战败后 `again()` 重打本关，得分回到 `stageScore` |
| F15 | 结算 → 对局：第 8 关胜利显示「全部通关」，`again()` 回到第 1 关、得分清零 |
| F16 | 结算 → 主页：`goHome()`，战场清空、2P 去掉、镜头复位 |
| F17 | 编辑器 → 对局 → 结算 → 编辑器：自制地图的结算画面是 `result_ewin` / `result_elose`，`again()` 回到编辑器 |
| F18 | 金币按本关得分折算：`coins = (score - stageScore) / 50`，胜利额外 +100（v3.0.2 起，得分会带到下一关，不能重复算） |
| F19 | `gameOver` 时战场冻结：`defeat` / `baseDestroyed` 重复调用没有副作用 |
| F20 | 播放广告时再次 `watchAd` 被忽略 |
| F21 | 每个状态下 `setScreen` 的画面名正确（`home`、`revive_*`、`adplay_*`、`result_<win\|final\|lose\|ewin\|elose>_<plain\|done>`） |
| F22 | 路演演示模式：`demoFlow` 跑完会发出 `demoDone`，期间 `autopilot` 为 true，结束后回到主页；v3.0.2 起还经过编辑器和暂停菜单，结束后还原玩家在编辑器里的地图 |
| F23 | 复活询问的弹窗出现之前（战败后 2.2 秒内）按确认键不算数（J / Enter 也是开火键，防止连按开火误点广告） |
| F24 | 结算画面出现后 0.6 秒内按确认键不算数，之后才能看视频翻倍 |
| F25 | 暂停菜单（v3.0.2）：`pauseGame` → `stPause`、战场冻结、`pause` 画面；`resumeGame` / 确认键继续 |
| F26 | 暂停时重新开始本关：得分回到进关时、生命回满 |
| F27 | 暂停时退出：关卡 → 主页；自制地图试玩（`pause_edit` 画面）→ 编辑器 |
| F28 | 不能暂停：主页、开局 / 复活还没准备好（`gameOver`）、路演演示、复活询问 |
| F29 | 暂停时一切停下（出生保护不倒计时），继续后接着走 |
| F30 | 复活清场（A2）：敌人子弹全部消失；基地 3 格以内的敌人消失、远处的还在，清掉的不算击毁、以后重新出场；碎了、裂了的护墙补回来；3 秒内基地打不掉，3 秒后能再被打掉（已经复活过 → 结算） |
| F31 | 复活询问时按 Esc（A12）：基地刚被毁、弹窗还没出现时按 Esc 还在复活询问；弹窗出现后按 Esc = 放弃 → 结算 |
| F32 | 复活次数按关卡记录（A16）：复活后暂停 → 重新开始本关，还算复活过，再战败直接结算；输了以后在结算画面重打本关、从主页进关、赢了进下一关，都可以再复活一次 |
| F33 | 基地先失守（A17）：基地已经被毁时打掉最后一辆敌人，还是复活询问、不判胜利；复活后敌人已经全灭 → 胜利结算 |
| F34 | 主页按钮（v5 去掉每日挑战）：开始战役、双人合作、自己做地图的点击区域都在，没有 `home.daily`；原来每日挑战卡的位置是“选择关卡” |
| F35 | 选关画面（A3）：主页 → 选关（`stLevels`、`levels` 画面）；8 张卡片和返回按钮的点击区域在预期位置；Esc 回主页；选第 6 关 → 第 6 关单人对局 |

### 3.5 地图编辑器（L2 / L3）

| ID | 用例 |
|---|---|
| E01 | 锁定格（3 个敌人出生点、1P / 2P 出生点、基地和护墙）`edPaint` 改不了 |
| E02 | `edPaint` 改普通格子：`ed`、`grid` 都更新；改成一样的字符返回 false |
| E03 | `edCheck`：出生点被围死 → `edProblem = 1`，`edMark` 指向那个出生点 |
| E04 | `edCheck`：玩家到不了某个出生点 → `edProblem = 2`。**测试中发现**：锁定的护墙（砖墙）把 1P / 2P 出生点和基地连在一起，敌人到得了基地，玩家就一定到得了出生点，所以编辑器里画不出问题 2（248 张测试地图里出现 0 次）。测试直接改 `ed` 绕过锁定格来测这段代码 |
| E05 | `edCheck`：砖墙算能通过（能打掉），钢墙和水面不算 |
| E06 | `reachable` 不会从一行末尾“绕”到下一行开头 |
| E07 | **和 `check.py` 一致**：`tools/test/gen_editor_maps.py` 生成 248 张编辑器画得出的地图（8 张关卡 + 不同墙密度的随机地图，种子固定），每张附上 `check.py` 的结论，存在 `tests/data/editor_maps.txt`；Python 测试检查结论确实来自 `check.py`、文件是最新的，引擎内测试检查 `edCheck()` 的结论全部相同 |
| E08 | `edRandom` 生成 50 张地图：全部左右对称、全部通过检查、锁定格没被改 |
| E09 | 对称开关：`edCommand "mirror"` 切换 `edMirror`。对称绘制本身写在 `editLoop` 里，跟着鼠标走，测不到（见第六节），手工检查 |
| E10 | `copy` 依次复制第 1~8 关，再按一次回到第 1 关；复制后 `stage` 不变 |
| E11 | `clear` 之后只剩锁定格 |
| E12 | `edRows` / `edLoadRows` 互为逆运算；格式不对的数据 `edLoadRows` 返回 false |
| E13 | `edSave` → `edLoad` 读回同一张地图（在临时的配置目录里） |
| E14 | 地图不合格时 `playCustom` 不开局，提示 `msg.ed.bad` |
| E15 | 不在编辑器里时 `edCommand` 什么都不做 |

### 3.6 双人合作（L3）

| ID | 用例 |
|---|---|
| P01 | `newGame(n, true)` 后 2P 出生在基地右边，`p2Exists = true`，`lives2 = 3` |
| P02 | 敌人子弹打中 2P 只扣 2P 的命，1P 不受影响（`hitWho`） |
| P03 | 两人先后中弹，两人都能正常重生（[再次广播会打断正在运行的处理](../ARCHITECTURE.md#93-其他)的回归测试） |
| P04 | 基地被毁 → 失败；只有一人没命 → 继续；两人都没命 → 失败 |
| P05 | 复活时两人各加 1 条命，2P 重新出生 |
| P06 | 没有友军伤害：1P 的子弹打不到 2P |
| P07 | 两人各自同时只能有 1 发子弹（`pbCount` / `pbCount2`） |
| P08 | 回主页 / 单人开局时 2P 被去掉（`p2off`），`p2Exists = false` |
| P09 | 触屏模式（手机 App，测试文件写 `// touch: true`，runner 用和打包脚本相同的方法打开）：双人合作被拒绝并提示 `msg.coop.touch`，单人照常（v3.0.2） |
| P10 | 打中敌人只让打中的那一发消失（A1）：2P 往空的一列开火，1P 打中敌人，2P 的子弹还在飞，飞到边界才消失 |
| P11 | 触屏模式：编辑器里“双人试玩”被拒绝，留在编辑器，提示 `msg.coop.touch`；单人试玩照常（A7） |
| P12 | 触屏模式的开火区域（`touchZone`，A18）：战场中间、左上角 → 开火；方向键上下左右；暂停按钮、语言按钮、广告卡、右侧得分 → 不开火；开局后 `Player.fireHeld` 为 true（要先松开手指）。真实的手指按下 / 松开测不到，要在手机上手工试 |

### 3.7 网页外壳（L4）

| ID | 用例 |
|---|---|
| W01 | 虚拟方向键：按下 / 滑动 / 松开发出正确的 keydown / keyup，换方向时先松开旧方向 |
| W02 | 多点触控：方向键和开火键同时按，互不影响；`pointercancel` 时所有键都松开 |
| W03 | 双人按钮切换 1P / 2P 的按键表 |
| W04 | `layout()` 在横屏、竖屏、超宽屏下画面保持 4:3 且不超出屏幕 |

实现（`tests/web/play.test.mjs`，`node --test`，不加依赖）：**不改 `play.js`**，在 Node 的 `vm` 里给它一个最小的假网页环境（几个元素、事件、游戏画布），运行原文件，模拟手指按下 / 滑动 / 松开 / 取消，检查发给游戏画布的键盘事件；布局在电脑 4:3 / 16:9、手机横屏 / 竖屏、超宽屏、平板 6 种屏幕下检查。`run_all.sh` 有 Node.js 时自动运行。

### 3.8 启动（L5）

| ID | 用例 |
|---|---|
| B01 | 启动后进入主页（`state = stHome`），没有 `panic` / `cannot alloc method` |
| B02 | 能开一局并进入对局（`playStage 1`），地图和 HUD 建好（v5 起检查 `killed`，不再检查 `enemiesLeft`） |
| B03 | 打包产物启动后 B01、B02 通过（`tools/test/package_boot.sh`：把 `boot.spx` 加进工程副本，用同一个 `tools/export/build.sh desktop` 打包，解开安装包运行里面的程序，读 TEST 输出）。2026-10-25 在 macOS 上：打包 + 运行共 21 秒，9 个断言通过。Linux 包由 `tools/export/linux_vm.sh build` 在虚拟机里用 Xvfb 运行同一个脚本（`build_local.sh` 会自动调用）；Windows 包要在 Windows 上运行同一个脚本 |
| B14 | 要发出去的那个安装包能直接运行（`tools/test/dist_boot.sh <安装包> [秒数]`）：把 `dist/` 里的 .zip（macOS .app）/ .tar.gz（Linux）解到临时目录运行，到时间进程还活着、输出里没有 panic / 引擎报错才算通过，结束时只结束自己启动的进程。`build_local.sh` 的 macOS 在 B03 之后跑它；Linux 在 `linux_vm.sh build` 的虚拟机里用 Xvfb 跑，B03 和 B14 都通过才算 ✅ |

## 四、覆盖率怎么算

spx 没有现成的覆盖率工具，v4.0 用四种互相补充的指标：

| 指标 | 怎么统计 | 目标 |
|---|---|---|
| **函数覆盖率** | `spx_coverage.py` 在工程副本里给每个 `func` 和每个事件处理（`onStart` `onMsg` `onKey` `onClick` `onCloned`）的第一行插入 `tCov("<文件>:<名字>")`，跑完全部引擎内测试后统计哪些从没出现过 | `main.spx` 的函数 ≥ 85%；全部函数 ≥ 75%；事件处理（不含按键 / 点击）≥ 70%。规划时是 108 个函数、58 个事件处理；v4.0.1 是 113 个函数，58 个事件处理里 40 个计入、18 个是按键 / 点击 |
| **状态机边覆盖** | 第三节 F01~F16 对应架构文档状态图的 16 条边 | 100% |
| **消息覆盖** | 25 种广播消息，每种至少在一个用例里被发出并被处理（插桩的事件处理能看出来） | 100% |
| **规则覆盖** | README「玩法」一节的每条规则都对应至少一个用例 ID，对照表放在覆盖率报告里 | 100% |
| **Python 行覆盖率** | **没有实现**：规划时打算在 CI 里装 `coverage`，后来 Actions 不可用，`pr_check.sh` 也没加这一项。需要时手动运行 `python3 -m coverage run -m unittest discover -s tests/tools` | `check.py`、`strings.py`、`textpath.py` ≥ 85%（没有统计过） |

- 命令：`tools/test/run_all.sh --coverage`（构建工具测试也计入用例清单），或者 `tools/test/run_spx.sh --coverage`。报告写到临时目录的 `coverage.md`，终端里打印目标达成情况。插桩工具是 `tools/test/spx_coverage.py`：`tCov` 是插到副本 `main.spx` 里的舞台函数，用舞台变量记住打印过的名字，同一个名字只打印一次 `COV <文件>:<名字>`（热点函数每帧都会调用）。
- 按键和点击（16 个 `onKey`、1 个 `onKey [Key1…Key8]`、1 个 `onClick`）在无界面测试里触发不了，单独列一栏，不计入事件处理覆盖率。
- 已知时有时无的（`spx_coverage.py` 里的 `KNOWN_UNSTABLE`）：基线里记为不稳定，消息覆盖率不计入，报告里单独列出。v4.0 时只有子弹相撞抵消的 `EBullet.spx:onMsg "clash"`（C17 已知问题）；v4.0.1 修复后这个处理去掉了，现在没有不稳定的项。
- README 的徽章（v5 第一批之后：tests 579 passing：507 个引擎内断言 + 66 个构建工具测试 + 6 个网页外壳测试；coverage 还是 v4.0.1 的 96% functions · 100% handlers）用的是稳定的数字，更新基线时一起更新。v4.0.1 时是 456 passing（416 + 34 + 6），v4.0 时是 450 passing、98% handlers。

**第一次实测（2026-10-25，基于 v3.0.2 的 main）**：

| 指标 | 实际 | 目标 |
|---|---|---|
| `main.spx` 函数 | 70 / 72（97%） | ≥ 85% ✅ |
| 全部函数 | 107 / 112（96%） | ≥ 75% ✅ |
| 事件处理（不含按键 / 点击） | 40 / 41（98%） | ≥ 70% ✅ |
| 消息 | 25 / 26（96%） | 100% ❌：`clash`（子弹迎面相撞抵消）还没有测试 |
| 用例清单 | 81 / 87 | 剩下 W01~W04、B03、T09（还没做的部分） |

**修复子弹相撞后（v4.0.1）**：全部函数 109 / 113（96%）、`main.spx` 函数 72 / 73（99%）、事件处理 40 / 40（100%）、消息 25 / 25（100%），没有不稳定的项；引擎内 416 个断言全部通过。

没覆盖到的 4 个函数（v4.0.1 的基线 `tests/coverage-baseline.json`）：`UI.hit` / `clickAd` / `clickScreen`（只在 `onClick` 里调用）、`edToolChar`（只在跟着鼠标的 `editLoop` 里调用）。第一次实测时还没覆盖的 `quitFromPause`（v3.0.2 新增的暂停菜单），后来由 `pause.spx` 测到了。

- 插桩只改副本，和测试脚本一样不进仓库；`tCov` 只用舞台变量和舞台函数，不给精灵加字段，不影响方法表。
- 报告输出成 Markdown：每个文件的函数覆盖率、没覆盖到的函数列表、规则对照表。`pr_check.sh --coverage` 把它附在本地检查报告里。
- 达不到目标的部分要在报告里写原因（例如 `onKey` 只能手工测、`sfx` 在 headless 下没有意义），不为了数字写没有断言的测试。

## 五、在本地检查（不用 GitHub Actions）

v4 的测试都在本地跑，**不依赖 GitHub Actions**：引擎内测试用 `spx run -headless` 直接解释执行游戏，不需要先编译或打包。2026-10-25 起组织的 Actions 因为额度 / 付款问题任务启动不了，所以 PR 的检查也改在本地做。

| 什么时候 | 命令 | 内容 |
|---|---|---|
| 每个 PR 合入前 | `tools/test/pr_check.sh` | 和 `.github/workflows/check.yml` 相同的三项检查（关卡地图、生成的素材、`.xbp`）+ `run_all.sh` 的全部测试；生成 Markdown 报告，贴到 PR 里 |
| 需要覆盖率时 | `tools/test/pr_check.sh --coverage` | 同上，再加覆盖率报告 |
| 发布前 | `tools/export/build_local.sh`：打包并对每个包做检查，桌面包跑启动测试（B03）和直接运行安装包（B14） | macOS 包在本机测；Linux 包在 `linux_vm.sh` 的 OrbStack 虚拟机里用 Xvfb 测；Windows 包本机打不了，有包时要在 Windows 上手工启动一次 |

- `pr_check.sh` 的第二项在临时副本里运行 `build.py` 再比较，不会改动工作区；第三项把 `.xbp` 解压后和 `TankBattle/` 比较（不算 `.DS_Store`）。
- **报告在哪**：默认写到 `$TMPDIR/pr_check-<校验和>.md`（校验和由仓库路径算出，`cksum`）。
- **跳过 = 不通过**：`run_all.sh` 把每项跳过都列成“⚠️ 跳过”（unittest 的 `skipped=N` 和原因、没有 node、`SKIP_SPX`），有跳过时最后一行不再是“全部通过”；`pr_check.sh` 把它记成 ⚠️，报告里写明“有 N 项检查跳过，不算通过”，**退出码 2**。
- **临时目录按仓库区分**：`run_spx.sh`、`pr_check.sh`、`run_all.sh`、`update_baseline.sh` 的临时目录和日志名都带仓库路径的校验和（例如 `$TMPDIR/tankbattle-test-1491624922`），同一台机器上两个 clone 同时跑测试不会互相删。`run_spx.sh` 可以用 `TEST_WORK=目录` 指定工作目录。
- **Python 环境**：`tools/dev/venv.sh` 在仓库里建 `.venv`，装 `tools/assets/requirements.txt` 里锁定的版本（`fonttools==4.67.0`、`brotli==1.2.1`）；`pr_check.sh`、`run_all.sh` 不设 `PYTHON` 时默认用 `.venv/bin/python`。
- **清理**：`tools/dev/clean.sh` 默认只列出这个仓库的临时文件和大小，`--yes` 才删，`--legacy` 连旧版脚本留下的、不带校验和的 `$TMPDIR/tankbattle-*` 一起删（别的 clone 的新版目录永远不碰）；另外提示 `.build/cache`、`dist/`、Go 编译缓存、OrbStack 虚拟机各占多少。
- 报告里写明提交号、分支、工作区是否干净、spx / Python 版本，评审时能看出是在哪个提交上跑的。
- `.github/workflows/test.yml` 保留，但只能手动触发：Actions 额度恢复后，想在云端（Linux）再确认一次时用。2026-10-25 在云端跑过一次（没有缓存）：构建工具测试 1.5 分钟，引擎内测试 3.3 分钟，Linux 上 `-headless` 不需要 Xvfb。
- `check.yml` 原来会在每个 PR 上自动触发，Actions 不可用时显示失败（任务没启动）；[#51](https://github.com/Qiniu-ERE/zero/pull/51) 起它和 `release.yml` 一样只能手动触发，以本地报告为准。

## 六、已知限制

| 限制 | 影响 | 对策 |
|---|---|---|
| 没有按键 / 触屏事件注入 | `onKey`、`onClick` 里的分支测不到 | 按键处理只做“状态 → 调用哪个函数”的转发，逻辑都在函数里，测试直接调用函数；按键表在手工检查表里逐项确认 |
| 进程退出码永远是 0 | 不能直接靠退出码 | 解析输出（第 2.3 节） |
| 异步流程按真实时间运行 | 等待时间不够会偶发失败，太长会拖慢测试 | 等待时间集中在 `prelude.spx`；用 `waitState` 式的“等到状态变化或超时”代替固定的 `wait` |
| 随机数没有种子接口 | 出兵类型、随机地图每次不同 | 测不变量和比例范围（C09、E08） |
| headless 下没有画面 | 画面对不对测不到 | 画面变化用 PR 截图人工确认（`tools/dev/shot.sh`），测试只检查 `screen`、造型名等状态 |
| 声音 | 测不到 | 手工检查 |
| 引擎内测试只在 spx 4.0 上跑 | XBuilder 用 spx v3.3.0，两个版本的接口有差别（例如 `rand` 的返回类型），4.0 上通过不代表 XBuilder 上能运行 | T09 用 spx v3.3.0 做编译检查（只检查能不能编译，运行时的行为差别仍要靠发布前在 x.qiniu.com 导入 `.xbp` 实际玩一次，见手工检查表） |

## 七、发布前手工检查表

每次发布前在一台电脑和一部手机上过一遍，结果贴在 release PR 里：

- [ ] 主页所有按键：Enter / 空格、1~8、E、C、P、T、L
- [ ] 对局：方向键 / WASD 移动、空格 / J 开火、T 切画风、L 切语言
- [ ] 复活询问：J / Enter 看视频、Esc 放弃、倒计时
- [ ] 结算：J / Enter 翻倍、R 下一关 / 再来、H 回主页
- [ ] 编辑器：鼠标点击和拖动、1~5、M、R、K、C、S、Enter、P、Esc
- [ ] 双人：1P WASD + J / 空格，2P 方向键 + Enter，同时按不冲突
- [ ] 声音：开火、打砖、打钢、爆炸、基地被毁、结算音乐
- [ ] 手机（网页版 PWA）：虚拟按键、多点触控、横竖屏、添加到主屏幕
- [ ] 安装包：Windows、macOS、Linux 各启动一次
- [ ] XBuilder：在 x.qiniu.com 导入 `TankBattle.xbp`，运行并玩一局

## 八、以后的版本怎么保持测试覆盖

v4.0 合入 `main` 之后，测试就是项目的一部分，不再是一个“版本”。以后的每个版本（v5.0 …）、每个修复都按下面的规矩走：

### 8.1 每个 PR 自带测试

| PR 类型 | 要带的测试 |
|---|---|
| 新功能（新关卡、新玩法、新界面） | 同一个 PR 里加上覆盖新规则的用例，并在本文第三节的清单里登记用例 ID（新模块用新的字母前缀） |
| 修复 bug | **先提交一个能复现 bug 的失败测试，再提交修复**（两个提交，PR 里能看到测试从失败变成通过） |
| 改已有规则（例如调整关卡配置） | 改对应的用例，PR 描述里说明为什么改期望值 |
| 只改文档、美术、打包 | 不用加用例，但测试照样要通过（生成文件过期检查 T06 会检查美术改动） |

PR 模板（`.github/pull_request_template.md`，已添加）里有“新增 / 修改的用例 ID”和“本地检查报告”两项，评审时对照检查。

### 8.2 覆盖率只能升不能降（已实现）

- 基线文件 `tests/coverage-baseline.json`：所有函数 / 事件处理的列表、覆盖到的（`covered`）、不稳定的（`unstable`）。
- 生成：`tools/test/update_baseline.sh` 完整跑两遍引擎内测试，**有测试失败就停下、不生成基线**，成功后删掉两遍的工作目录（`KEEP=1` 保留）；**两遍都覆盖到**的才算覆盖到；只有一遍覆盖到的记为不稳定、不强制。例如 v4.0 时子弹相撞抵消（`EBullet.spx:onMsg "clash"`）受已知问题影响时有时无，直接写进基线会让检查随机失败（v4.0.1 修复后已经没有了）。
- 检查：`run_spx.sh --coverage`（`pr_check.sh --coverage` 也一样）在有基线时自动比较，**原来覆盖到的现在没覆盖到，或者新加的函数 / 事件处理没有被任何测试执行，就失败**，报告里列出是哪几个。按键 / 点击处理只能手工测，不算。
- 覆盖率提高了：报告里会提示，运行 `update_baseline.sh` 更新基线，和改动一起提交。需要降低的（例如删掉了一个功能），在 PR 描述里说明原因，再更新基线。
- 状态机、消息、规则三张对照表也一样：状态图加了边、加了新消息、README 加了新规则，都要有对应的用例。

### 8.3 分支和合并

- **合入前必须附上本地检查报告**（`tools/test/pr_check.sh`），报告里所有项都是 ✅（有 ⚠️ 跳过也不算通过）。Actions 恢复后，也可以把云端测试设为 `main` 的必需检查。
- 新版本开集成分支（例如 `v5.0`）时直接从 `main` 拉，测试跟着一起过去；集成分支同步 `main` 时测试也一起同步。
- 换 spx 版本（本地 4.x 升级，或者 XBuilder 线上升级）时，先单独开一个 PR 只换版本、跑全部测试，确认没有行为变化再做别的改动。

### 8.4 文档

- v4.0 发布时，本文的第二、四、五、八节精简后并入[架构文档第 10 节](../ARCHITECTURE.md#10-测试与演示视频)，成为长期的“测试规范”；第三节的用例清单搬到 `tests/README.md`，跟着测试代码一起维护。**实际情况（v4.0.1）**：要点已经写进架构文档第 10 节；用例清单没有搬，仍在本文第三节（`spx_coverage.py` 从这里读取用例 ID，要搬就得一起改脚本）。
- 以后的版本规划（`docs/v5/PLAN.md` …）里要有一节“测试”，列出新功能要加的用例。

## 九、测试发现的问题

| # | 问题 | 状态 | 测试 |
|---|---|---|---|
| 1 | **子弹迎面相撞经常不抵消**（README：“子弹迎面相撞会互相抵消”）。2026-10-25 实测：横着 10 次只抵消 1 次，竖着 10 次只抵消 2 次；有窗口和无界面运行结果相同。**原因**（修复时用实验查清，最初记录的“子弹每次判定之间移动的距离比直径大”是错的）：引擎里子弹的碰撞区域几乎只是一个点，两颗静止的子弹中心重合时 `touching` 是 true，相距 2 像素就是 false；迎面飞来的两颗子弹很少在判定时正好落在同一个点上 | ✅ **v4.0.1 已修复**：改成按距离判断（`main.spx` 的 `bulletClash`：玩家子弹这一帧飞过的路线上，离敌人子弹不到 6 像素 + 敌人子弹这一帧飞的距离就算撞上），10 次都抵消 | `clash.spx` C17（改回 `tCheck`，并加了错开 3 / 12 像素、相邻两行的情况；把判定半径改成 0.5 像素，测试会报错） |
| 2 | 编辑器里画不出“玩家到不了出生点”（问题 2）：锁定的护墙把玩家和基地连在一起 | 不是 bug，`edCheck` 的这段检查目前用不上 | `editor.spx` E04、`editor_parity.spx` |
| 3 | `coop` 在全部测试连着跑时偶发一次中途退出（只出现过 1 次，之后连续 9 次都通过） | 跟踪中：runner 现在会打印失败时的耗时 | `coop.spx` |

`tXfail "说明", 条件, "问题"`：已知问题还没修好时输出 `TEST XFAIL`，不算失败，汇总里单独列出；修好了输出 `TEST XPASS`，算失败，提醒把它改成 `tCheck`。

