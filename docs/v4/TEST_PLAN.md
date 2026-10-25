# 坦克大战 v4.0 · 测试方案

本文是 v4.0 的测试设计：分几层测、引擎内的测试怎么写怎么跑、要测哪些用例、覆盖率怎么算、怎么接进 CI。总览和里程碑见 [PLAN.md](PLAN.md)。

## 一、测试分层

| 层 | 测什么 | 工具 | 速度 | 什么时候跑 |
|---|---|---|---|---|
| **L1 构建工具** | `check.py`、`strings.py`、`textpath.py`、`build.py` 的生成结果 | Python `unittest`（不加第三方测试库） | 几秒 | 每个 PR |
| **L2 游戏逻辑** | 舞台函数和精灵：地图、格子、子弹、地形、敌人、得分、生命、编辑器 | 引擎内测试（第二节） | 每组约 10 秒 | 每个 PR |
| **L3 游戏流程** | 状态机的每条边、复活、激励视频奖励、结算、下一关、双人合作 | 引擎内测试，按真实时间等待异步流程 | 每组 10~30 秒 | 每个 PR |
| **L4 网页外壳** | `tools/export/web/play.js`：虚拟按键映射、多点触控、双人按钮 | `node --test`（Node 自带） | 几秒 | 每个 PR |
| **L5 平台启动** | 打包后的程序在 Windows / macOS / Linux 能启动、进入主页、开一局 | 打包产物 + 启动测试 | 每平台几分钟 | 打标签发布、`[ci smoke]` |
| **手工** | 按键手感、画面、声音、手机触屏 | 发布前检查表（第七节） | — | 发布前 |

原则：**能在 L1 / L2 测的不放到 L3**（越往下越慢、越容易因为时间不稳定而偶发失败）；L5 只回答“能不能启动”，不重复测规则。

## 二、引擎内测试框架

### 2.1 原理

和 `tools/dev/record_demo.sh` 一样：**不改仓库里的游戏**，复制一份工程，把测试脚本追加到副本的 `main.spx` 末尾，用 `spx run -headless .` 运行。测试脚本在舞台的 `onStart` 里，能直接读写舞台变量、调用舞台函数和精灵的公开函数。2026-10-24 已用 spx 4.0.0 验证可行（见 [PLAN.md 第二节](PLAN.md#二可行性原型已经跑通)）。

### 2.2 目录和命令

```
tests/
├── spx/                    # 引擎内测试，每个文件一组，单独起一个进程
│   ├── boot.spx            # 启动测试：能启动、初始状态正确（也用于 L5）
│   ├── grid.spx            # 地图与格子
│   ├── combat.spx          # 子弹、地形、敌人、得分、生命
│   ├── flow.spx            # 流程状态机、复活、广告、结算
│   ├── editor.spx          # 地图编辑器
│   └── coop.spx            # 双人合作
├── tools/                  # L1：test_check.py、test_strings.py、test_textpath.py、test_generated.py
└── web/                    # L4：play.test.mjs
tools/test/
├── run_spx.sh              # 跑一组或全部引擎内测试
├── prelude.spx             # 断言函数，拼在每组测试前面
├── coverage.py             # 插桩并统计覆盖率（第四节）
└── run_all.sh              # 一条命令跑完 L1 + L2 + L3 + L4
```

```sh
tools/test/run_all.sh                   # 全部
tools/test/run_spx.sh tests/spx/flow.spx  # 只跑一组
tools/test/run_spx.sh --coverage        # 全部引擎内测试 + 覆盖率报告
```

### 2.3 输出协议

测试进程的退出码永远是 0（`exit` 不能带状态码），所以 `run_spx.sh` 靠解析输出判断结果：

| 输出行 | 含义 |
|---|---|
| `TEST PASS <组>/<用例 ID> <说明>` | 一个断言通过 |
| `TEST FAIL <组>/<用例 ID> <说明> got=<实际> want=<期望>` | 一个断言失败 |
| `TEST DONE <组> pass=<n> fail=<n>` | 这一组跑完了 |

**判定为失败**：出现任何 `TEST FAIL`；没有 `TEST DONE`（中途崩溃或者卡住）；超时（默认每组 60 秒）；输出里有 `panic` 或 `cannot alloc method`（[方法表上限](../ARCHITECTURE.md#91-方法表上限启动报错-cannot-alloc-method--cap2560)）。

### 2.4 写法

```go
// tests/spx/flow.spx（prelude.spx 提供 check / checkInt / done）
onStart => {
	wait 3                       // 先让游戏完成初始化（和截图脚本的约定一样）
	suite = "flow"

	playStage 1
	wait 0.5
	checkInt "F01 主页开始 → 对局", state, stPlay

	baseDestroyed
	wait 0.5
	checkInt "F05 第一次战败 → 复活询问", state, stRevive
	check "F05 基地被毁", baseDown

	done
}
```

约定：

- **一组一个进程**。游戏状态全在舞台变量里，同一个进程里的用例会互相影响；组内的用例按顺序写，需要干净状态时先调用 `goHome`。
- **用例 ID 写进断言说明**（`F05`），和第三节的清单一一对应，覆盖率报告靠它统计规则覆盖。
- **不依赖随机结果**。`spawnEnemy` 的坦克类型、`edRandom` 的地图都是随机的：要么测不变量（例如“随机地图一定通过检查”“出生点只在 0 / 6 / 12 列”），要么多次采样测比例范围。
- **异步流程要等**。`reviveFlow`、`adFlow`（5 秒）、出生保护等放在消息处理里异步执行，测试用 `wait` 等到状态变化，等待时间写成常量，统一在 `prelude.spx` 里调。
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
| C10 | `enemyKilled`：加分、`killed` 加 1、`enemiesLeft` 减 1、刷新最高分；第 20 辆 → 胜利结算 |
| C11 | 最高分只升不降 |
| C12 | 屏幕上同时只能有 1 发自己的子弹（`pbCount`） |
| C13 | 出生时有 3 秒保护，保护期内中弹不扣命 |
| C14 | 生命用完 → `defeat` |
| C15 | 重型坦克要打 3 发；普通 / 快速坦克 1 发 |
| C16 | `switchTheme` / `switchLang` 切换后 `look()` / `langCode()` 的后缀正确，切两次回到原样 |

### 3.4 流程状态机（L3）

[架构文档第 5 节](../ARCHITECTURE.md#5-游戏流程状态机)的状态图一共 16 条边，每条至少一个用例（F01~F16），另加规则用例：

| ID | 用例 |
|---|---|
| F01 | 主页 → 对局：`confirm()`（Enter / 空格）从第 1 关开始，`coop` 为 false |
| F02 | 主页 → 对局：`playStage(n)` 选关，`stage = n`、`stageScore = 0` |
| F03 | 主页 → 对局：`newGame(1, true)` 双人合作 |
| F04 | 主页 → 编辑器：`openEditor()`，`state = stEdit` |
| F05 | 对局 → 复活询问：本局第一次战败（基地被毁） |
| F06 | 对局 → 复活询问：本局第一次战败（生命用完） |
| F07 | 复活询问 → 播放广告：`confirm()` → `watchAd(rewardRevive)` |
| F08 | 复活询问 → 结算：放弃 / 7 秒倒计时结束，判负 |
| F09 | 播放广告 → 对局：复活奖励 = 修复基地、额外 1 条命、`revived = true` |
| F10 | 对局 → 结算：复活过之后再次战败，直接结算 |
| F11 | 对局 → 结算：消灭 20 辆，胜利 |
| F12 | 结算 → 播放广告 → 结算：金币翻倍，`doubled = true`；第二次不能再翻倍 |
| F13 | 结算 → 对局：胜利后 `again()` 进入下一关，得分保留，`stageScore = score` |
| F14 | 结算 → 对局：战败后 `again()` 重打本关，得分回到 `stageScore` |
| F15 | 结算 → 对局：第 8 关胜利显示「全部通关」，`again()` 回到第 1 关、得分清零 |
| F16 | 结算 → 主页：`goHome()`，战场清空、2P 去掉、镜头复位 |
| F17 | 编辑器 → 对局 → 结算 → 编辑器：自制地图的结算画面是 `result_ewin` / `result_elose`，`again()` 回到编辑器 |
| F18 | 金币：`coins = score / 50`，胜利额外 +100 |
| F19 | `gameOver` 时战场冻结：`defeat` / `baseDestroyed` 重复调用没有副作用 |
| F20 | 播放广告时再次 `watchAd` 被忽略 |
| F21 | 每个状态下 `setScreen` 的画面名正确（`home`、`revive_*`、`adplay_*`、`result_<win\|final\|lose\|ewin\|elose>_<plain\|done>`） |
| F22 | 路演演示模式：`demoFlow` 跑完会发出 `demoDone`，期间 `autopilot` 为 true，结束后回到主页 |

### 3.5 地图编辑器（L2 / L3）

| ID | 用例 |
|---|---|
| E01 | 锁定格（3 个敌人出生点、1P / 2P 出生点、基地和护墙）`edPaint` 改不了 |
| E02 | `edPaint` 改普通格子：`ed`、`grid` 都更新；改成一样的字符返回 false |
| E03 | `edCheck`：出生点被围死 → `edProblem = 1`，`edMark` 指向那个出生点 |
| E04 | `edCheck`：玩家到不了某个出生点 → `edProblem = 2` |
| E05 | `edCheck`：砖墙算能通过（能打掉），钢墙和水面不算 |
| E06 | `reachable` 不会从一行末尾“绕”到下一行开头 |
| E07 | **和 `check.py` 一致**：对 8 张关卡地图和一批构造的反例，`edCheck` 和 `check.py` 的合格 / 不合格判断相同（脚本把同一批地图分别交给两边，对比结果） |
| E08 | `edRandom` 生成 50 张地图：全部左右对称、全部通过检查、锁定格没被改 |
| E09 | 对称绘制：`edMirror` 打开时画一格，对称的格子也被画上 |
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

### 3.7 网页外壳（L4）

| ID | 用例 |
|---|---|
| W01 | 虚拟方向键：按下 / 滑动 / 松开发出正确的 keydown / keyup，换方向时先松开旧方向 |
| W02 | 多点触控：方向键和开火键同时按，互不影响；`pointercancel` 时所有键都松开 |
| W03 | 双人按钮切换 1P / 2P 的按键表 |
| W04 | `layout()` 在横屏、竖屏、超宽屏下画面保持 4:3 且不超出屏幕 |

为了能在 Node 里测，`play.js` 的按键映射和布局计算要抽成不依赖 DOM 的纯函数（单独一个 PR，不改行为）。

### 3.8 启动（L5）

| ID | 用例 |
|---|---|
| B01 | 启动后进入主页（`state = stHome`），没有 `panic` / `cannot alloc method` |
| B02 | 能开一局并进入对局（`playStage 1`），地图和 HUD 建好 |
| B03 | 打包产物（Windows / macOS / Linux 单文件程序）启动后 B01、B02 通过 |

## 四、覆盖率怎么算

spx 没有现成的覆盖率工具，v4.0 用四种互相补充的指标：

| 指标 | 怎么统计 | 目标 |
|---|---|---|
| **函数覆盖率** | `coverage.py` 在工程副本里给每个 `func` 和每个事件处理（`onStart` `onMsg` `onKey` `onClick` `onCloned` …）的第一行插入 `println("COV", "<文件>:<名字>")`，跑完全部引擎内测试后统计哪些从没出现过 | `main.spx` 的函数 ≥ 85%；全部 108 个函数 ≥ 75%；58 个事件处理 ≥ 70% |
| **状态机边覆盖** | 第三节 F01~F16 对应架构文档状态图的 16 条边 | 100% |
| **消息覆盖** | 25 种广播消息，每种至少在一个用例里被发出并被处理（插桩的事件处理能看出来） | 100% |
| **规则覆盖** | README「玩法」一节的每条规则都对应至少一个用例 ID，对照表放在覆盖率报告里 | 100% |
| **Python 行覆盖率** | `python3 -m coverage`（只在 CI 里装） | `check.py`、`strings.py`、`textpath.py` ≥ 85% |

- 插桩只改副本，和测试脚本一样不进仓库；插入的是 `println`，不加变量，不影响方法表。
- 报告输出成 Markdown：每个文件的函数覆盖率、没覆盖到的函数列表、规则对照表。CI 把它贴到 PR 的检查结果里。
- 达不到目标的部分要在报告里写原因（例如 `onKey` 只能手工测、`sfx` 在 headless 下没有意义），不为了数字写没有断言的测试。

## 五、持续集成

新增 `.github/workflows/test.yml`，和发布用的 `release.yml` 分开：

| 触发 | 任务 | 平台 |
|---|---|---|
| 每个 PR、推送到 `v4.0` | L1 + L4（不需要 spx） | ubuntu |
| 每个 PR、推送到 `v4.0` | L2 + L3 + 覆盖率报告 | ubuntu（先确认 `-headless` 不需要 Xvfb；需要的话沿用 smoke 任务的 Xvfb 设置） |
| 打 `v*` 标签、提交信息带 `[ci smoke]` | L5：用打包产物跑 `boot.spx` | Windows / macOS / Linux |

- spx 环境用 `tools/export/setup_spx.sh` 准备，按 spx 的固定提交缓存，避免每次都从头编译。
- 仓库是私有的，Actions 分钟数有限：PR 只跑 ubuntu；三平台只在发布和手动触发时跑。
- L5 会替换现在的“启动后等 40 秒截一张图”：截图保留（方便人看），但通过 / 失败由 `boot.spx` 的输出决定。
- PR 合入前要求测试通过（在仓库设置里把 `test` 设为必需的检查，由仓库管理员操作）。

## 六、已知限制

| 限制 | 影响 | 对策 |
|---|---|---|
| 没有按键 / 触屏事件注入 | `onKey`、`onClick` 里的分支测不到 | 按键处理只做“状态 → 调用哪个函数”的转发，逻辑都在函数里，测试直接调用函数；按键表在手工检查表里逐项确认 |
| 进程退出码永远是 0 | 不能直接靠退出码 | 解析输出（第 2.3 节） |
| 异步流程按真实时间运行 | 等待时间不够会偶发失败，太长会拖慢测试 | 等待时间集中在 `prelude.spx`；用 `waitState` 式的“等到状态变化或超时”代替固定的 `wait` |
| 随机数没有种子接口 | 出兵类型、随机地图每次不同 | 测不变量和比例范围（C09、E08） |
| headless 下没有画面 | 画面对不对测不到 | 画面变化用 PR 截图人工确认（`tools/dev/shot.sh`），测试只检查 `screen`、造型名等状态 |
| 声音 | 测不到 | 手工检查 |

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
