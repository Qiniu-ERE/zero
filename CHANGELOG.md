# 更新记录

安装包在 [Releases](https://github.com/Qiniu-ERE/zero/releases) 下载。每个版本对应一个 Git 标签。

## v5.0.0

v5.0 是**商业化落地探索**：评估怎么把游戏放到 Steam、Xbox（Microsoft Store）、App Store、Google Play 上卖，算清楚盈利预期和每个平台的盈利周期；同时把全面审查发现的问题先修掉一批。英文名定为 **Brickline Tanks**。

安装包：macOS、Linux、网页版、Android。Windows 和 iOS 没有新包，仍是 v3.0.1 的。**Android**：调试证书换到了固定位置，以后升级不用再卸载；如果安装时提示签名不一致，先卸载旧版（只需这一次）。

**这一版玩家能感受到的变化**

- 主页新增**选择关卡**，鼠标、触屏点一下就开局；去掉了“每日挑战 · 即将推出”。
- **复活更有用**：复活时清掉敌人子弹和基地附近的敌人，补回护墙，基地有 3 秒保护。
- 修复：双人时一个人打中敌人，另一个人的子弹也会消失；基地刚被毁时按 Esc 会直接放弃复活；暂停里“重新开始本关”可以无限复活；触屏版点按钮会顺便开火。
- 生命超过 3 条显示“图标 ×N”；英文名改为 Brickline Tanks。

**商业化规划**（文档，见 [docs/v5/PLAN.md](https://github.com/Qiniu-ERE/zero/blob/main/docs/v5/PLAN.md)）：平台评估、各平台的游戏体验、盈利方案（PC 买断 $4.99 + 免费试玩版，不放广告）、推广方案（目标发售前 5000 个愿望单）、盈利周期与现金流、路演故事、商店页材料、全面审查清单（56 项）（[#48](https://github.com/Qiniu-ERE/zero/pull/48)）。

<details><summary>详细改动（开发者）</summary>

#### 游戏

- **复活时清场**：看视频复活后，敌人的子弹全部消失，基地 3 格以内的敌人也消失（不算击毁、不加分，之后重新出场，每关还是 20 辆）；基地四周碎了、裂了的护墙恢复成砖墙；基地有 3 秒保护，子弹打到只会消失（A2，[#60](https://github.com/Qiniu-ERE/zero/pull/60)）。
- **复活询问时按 Esc**：要等复活弹窗出现才算“放弃”。基地刚被毁的 2.2 秒内（爆炸和特写）按 Esc 不会再直接放弃复活（A12，[#61](https://github.com/Qiniu-ERE/zero/pull/61)）。
- **复活次数按关卡记录**：暂停菜单里“重新开始本关”不会再给一次复活；输了以后在结算画面重打本关，可以再复活一次；从主页进关、过关进入下一关、试玩自制地图也可以（A16，[#61](https://github.com/Qiniu-ERE/zero/pull/61)、[#77](https://github.com/Qiniu-ERE/zero/pull/77)）。
- **基地先失守不判胜利**：同一帧里基地被打掉、又打掉了最后一辆敌人，按战败走复活询问；复活后敌人已经全灭就直接胜利结算（A17，[#61](https://github.com/Qiniu-ERE/zero/pull/61)）。
- **双人时只让打中敌人的那一发子弹消失**：原来一个人打中敌人，另一个人正在飞的子弹也会消失（A1，[#59](https://github.com/Qiniu-ERE/zero/pull/59)）。
- **触屏版**：编辑器里的“双人试玩”也会提示需要键盘或手柄（A7）；只有按在战场或方向键上才开火，点按钮不再顺便开一枪，开局要先松开手指（A18）（[#62](https://github.com/Qiniu-ERE/zero/pull/62)）。
- **生命超过 3 条显示“图标 ×N”**（复活后可能有 4 条，最多显示 ×9）（A15，[#64](https://github.com/Qiniu-ERE/zero/pull/64)）。
- **主页去掉“每日挑战 · 即将推出”卡**：v5 不做每日挑战（[#69](https://github.com/Qiniu-ERE/zero/pull/69)）。
- **选择关卡画面**：主页新的“选择关卡”卡片，点开有 8 张关卡卡片，鼠标、触屏点一下就开局（单人）；按 1~8 也行，Esc 回主页。主页按 1~8 直接进关照旧（A3，[#74](https://github.com/Qiniu-ERE/zero/pull/74)）。
- **英文名改为 Brickline Tanks**（中文名“坦克大战”不变）：英文主页标题、窗口标题“坦克大战 2026 · Brickline Tanks”、网页版标题都改了（[#76](https://github.com/Qiniu-ERE/zero/pull/76)、[#77](https://github.com/Qiniu-ERE/zero/pull/77)）。
- 代码清理：去掉只写不读的 `enemiesLeft`，敌军剩余按 `killed` 显示（A22，[#73](https://github.com/Qiniu-ERE/zero/pull/73)）。
- 新测试：P10、F30~F35、P11、P12、C20、C21~C24（真实发射子弹打自己的老鹰，[#71](https://github.com/Qiniu-ERE/zero/pull/71)）；B02、C10 改成检查 `killed`。引擎内断言从 416 个增加到 507 个。

#### 打包与测试工具

- **Android 版本号和调试证书**：打 Android / iOS 前核对 spx 模板里的版本号，不一致就停下（`SPX_REPATCH=1` 自动重装）；调试证书移到仓库外的 `~/.config/tankbattle/debug.keystore`（旧位置 `.build/cache/` 里的会自动搬过去），**请备份**。以前的版本用过不同的证书，装过旧版、提示签名不一致时先卸载一次（B1 B2，[#65](https://github.com/Qiniu-ERE/zero/pull/65)）。
- **本机打包发布更可靠**：`build_local.sh` 打包前删掉这次要打的平台的同版本旧包，`dist/BUILD_LOCAL.md` 记下提交号和工作区是否干净；`release_local.sh` 发布前核对版本号、标签提交、工作区干净、没有 ❌，不对就停下（别的机器打的包用 `SKIP_BUILD_CHECK=1`）；`--append` 给已有的 Release 补包；`DRY_RUN=1` 只检查、不发布、不需要标签；回退版本按版本号排序；修复 macOS 自带 bash 3.2 下安卓必定失败（B3~B6，[#66](https://github.com/Qiniu-ERE/zero/pull/66)）。
- **测试工具**：临时目录按仓库路径的校验和区分（两个 clone 同时跑不会互删），`TEST_WORK` 可以指定目录；`pr_check.sh` 的报告默认在 `$TMPDIR/pr_check-<校验和>.md`；有检查跳过时不算通过（退出码 2）；`update_baseline.sh` 测试失败就停；Python 依赖锁定版本，新增 `tools/dev/venv.sh`（建 `.venv`）和 `tools/dev/clean.sh`（清理临时文件，默认只列出）（B8~B11，[#67](https://github.com/Qiniu-ERE/zero/pull/67)）。
- **工具测试和安装包启动**：新增覆盖率工具、打包发布工具的单元测试；`env.sh` 认得 `-rc.1` 这样的预发布版本号；新增 `tools/test/dist_boot.sh`，直接运行要发出去的安装包（B14）（B13 B14，[#68](https://github.com/Qiniu-ERE/zero/pull/68)）。
- **打包环境**：Godot 编辑器设置里的 Java / Android SDK 路径每次改成当前的；MoltenVK 和虚拟机里的 Go 核对 sha256；Go 版本不对时提醒，`GO_STRICT=1` 时报错（B15 B16，[#70](https://github.com/Qiniu-ERE/zero/pull/70)）。
- **商店版 / 试玩版**：`build.sh <平台> [--store] [--demo]`，产物放在 `dist/store/`、`dist/demo/`、`dist/store-demo/`；`setup_spx.sh` 按顺序打 `tools/export/patches/` 里的 spx 补丁（B18 的 P1 部分，[#72](https://github.com/Qiniu-ERE/zero/pull/72)）。
- **`release.yml`**：手动运行可以选 `platforms`（只打几个平台）、`upload_to`（补进已有的 Release）、`create_release`（新建 Release），**都不选时不发布**；第三方 Action 锁定到提交 SHA（B7 B17，[#75](https://github.com/Qiniu-ERE/zero/pull/75)）。
- 难度模拟脚本 `tools/test/difficulty.sh`：8 关难度曲线数据和调参建议（A4 A11，[#63](https://github.com/Qiniu-ERE/zero/pull/63)）。
- **发布说明里缺的平台指向最近一个有包的版本**：`release_local.sh` 遇到本机没打的平台（Windows、iOS），不再固定指向上一个版本，而是找最近一个真的有这个平台安装包的版本（v3.0.2 没有这两个包，所以指向 v3.0.1）；`DRY_RUN=1` 只打印发布说明、不发布（[#53](https://github.com/Qiniu-ERE/zero/pull/53)）。

#### 文档

- v4 之后的文档补漏：README、架构文档、测试方案、跨平台文档、更新记录（[#54](https://github.com/Qiniu-ERE/zero/pull/54)–[#58](https://github.com/Qiniu-ERE/zero/pull/58)）。
- 上面这些改动对应的文档：README 的玩法（复活规则、选择关卡、英文名）、打包和测试；架构文档的状态机、新的舞台变量和消息、工具表、PR 记录；测试方案的新用例；跨平台文档的打包与发布。

</details>

## v4.0.1

安装包：macOS、Linux、网页版、Android。Windows 和 iOS 没有新包，仍是 v3.0.1 的（不含 v3.0.2 和本版的修复）。

- **修复子弹迎面相撞经常不抵消**（v4.0 的测试 C17 发现的已知问题）：原来 10 次只有 1~2 次能抵消。原因是引擎里子弹的碰撞区域几乎只是一个点（两颗子弹相距 2 像素就不算碰到），迎面飞来时很少正好落在同一个点上。现在改成按距离判断：玩家子弹这一帧飞过的路线上，离敌人子弹不到一颗子弹的直径就算撞上，两颗一起消失。实测 10 次都抵消；错开 3 像素（画面上重叠）也抵消，错开 12 像素或者相邻两行擦肩而过不会误判。
- 测试 C17 从“已知问题”改回普通断言，并增加错开和擦肩而过的情况：引擎内 416 个断言全部通过，没有已知问题。覆盖率：事件处理从 98% 到 100%，不再有“不稳定”的项；README 徽章更新为 tests 456 passing、coverage 96% functions · 100% handlers。
- 重新打包 `TankBattle.xbp`；已用 XBuilder 线上的 spx v3.3.0 编译检查通过。
- **打包改为全部在本机做，GitHub Actions 只能手动触发**：新增 `tools/export/build_local.sh`（打本机能打的全部平台：macOS、网页版、Android、Linux，每个包都检查，结果写在 `dist/BUILD_LOCAL.md`）和 `linux_vm.sh`（在 OrbStack 的 x86_64 Ubuntu 虚拟机里打 Linux 包并做启动测试）；`release.yml`、`check.yml` 不再在推送标签或 PR 时自动运行（组织的 Actions 额度用完）（[#51](https://github.com/Qiniu-ERE/zero/pull/51)）。

## v4.0.0

> **只打了标签，没有安装包**：推送 `v4.0.0` 标签时 Actions 已经启动不了，这一版没有创建 GitHub Release。安装包请用 [v4.0.1](https://github.com/Qiniu-ERE/zero/releases/tag/v4.0.1)（包含 v4.0.0 的全部内容，另外修复了子弹相撞）。

v4.0 不加新玩法，专门做**测试与质量**：每条游戏规则都有自动化测试，合入前在本地一条命令跑完，覆盖率只升不降。详见 [v4.0 规划](docs/v4/PLAN.md) 和 [测试方案](docs/v4/TEST_PLAN.md)。

- **引擎内自动化测试**：用 `spx run -headless` 在工程副本里运行测试脚本，直接调用游戏函数并检查结果，不改游戏代码。19 组测试、410 多个断言：地图与格子、子弹与地形、出兵、得分、玩家、敌人、画风语言、流程状态机（主页、复活、广告、结算、自制地图、路演演示）、地图编辑器、双人合作、暂停菜单、触屏模式（[#26](https://github.com/Qiniu-ERE/zero/pull/26)–[#43](https://github.com/Qiniu-ERE/zero/pull/43)）。
- **构建工具测试**：关卡检查 `check.py`、中英文案表、文字转路径、美术生成器（生成文件是否过期、生成是否确定）。
- **两套地图规则一致**：248 张地图上，游戏里的 `edCheck()` 和 `check.py` 结论完全相同。
- **网页外壳测试**：`play.js` 的虚拟方向键、多点触控、双人按键、6 种屏幕下的 4:3 布局（Node.js，不改 `play.js`）。
- **XBuilder 兼容检查**：用 XBuilder 线上的 spx v3.3.0 编译检查游戏代码，#18 那类“本地能跑、XBuilder 编译不过”的问题合入前就能发现。
- **安装包启动测试**：打出桌面安装包后运行里面的程序，确认能启动、进入主页、开一局。
- **覆盖率**：自己插桩统计函数和事件处理的覆盖率（`main.spx` 函数 99%、全部函数 96%、事件处理 98%（子弹相撞抵消的处理受已知问题影响、时有时无，不计入）、消息 100%），并保存基线：覆盖率退步时检查失败。
- **本地检查代替 GitHub Actions**：`tools/test/pr_check.sh` 跑和 `check.yml` 相同的检查加全部测试，生成报告贴在 PR 里（组织的 Actions 额度用完，任务启动不了）；新增 PR 模板。
- **测试发现的问题**：子弹迎面相撞经常不抵消（实测 10 次只抵消 1~2 次），已用“已知问题”标记记录，在 v4.0.1 修复；编辑器里画不出“玩家到不了出生点”（不是 bug）。
- 跟进 v3.0.2 的行为变化，更新了相关测试。

## v3.0.2

- **修复点按钮进入编辑器时误画一格**：点击在鼠标按下时就触发，进入编辑器后要先等鼠标松开再开始绘制（主页「自己做地图」、结算「继续编辑」、暂停「返回编辑」都会遇到）。
- **修复连按开火误点“看视频”**：基地被毁后 2.2 秒才弹出复活询问，结算刚出现时也还在按开火键；现在复活询问要等弹窗出现、结算要等 0.6 秒后才接受确认键（J / Enter）。
- **修复手机 App 的双人合作**：原生 App 只认一根手指，2P 没法操作；现在点双人合作会提示“需要键盘或两只手柄”，按键说明也不会盖住方向键。
- **修复路演演示的副作用**：自动驾驶打出的分数不再计入最高分；演示结束后还原玩家在编辑器里的地图；演示开局时不再闪现暂停按钮。
- **金币按本关得分折算**：得分会带到下一关，原来后面的关卡会把前面的分数重复算进金币。
- 开局或复活还没完成时不能暂停（避免暂停菜单开着、战场却在动）；PC 版保存失败的提示不再只说“网页版”。
- 工具：`check.py` 也检查 2P 出生点；新增 PR 检查流水线（关卡地图、生成的素材和 `.xbp` 是否最新）；冒烟测试在游戏没跑起来时会失败，发布要等冒烟测试通过；打包的默认版本号从本文件读取。
- README 表格排版：在 GitHub 上不再换行。

## v3.0.1

- **暂停菜单**：对局中按 Esc，或点顶栏的 Ⅱ 按钮（手机上靠它）暂停，可以继续、重新开始本关、返回主页；自制地图试玩时是返回编辑。原来对局中没有办法退出。网页版的按键区也加了“暂停”。
- **修复 XBuilder 里编译不过**：XBuilder 线上用的 spx v3.3.0 里 `rand(整数, 整数)` 返回浮点数，和整数比较时编译失败；现在统一转成整数（[#18](https://github.com/Qiniu-ERE/zero/pull/18)）。
- **修复砖墙一发就碎**：正对一块砖打时，子弹的两个检测点落在同一格，被算了两次；现在和文档一样，要打两下才碎（[#20](https://github.com/Qiniu-ERE/zero/pull/20)）。
- **路演演示模式**（主页按 P）加入 v3.0 内容：新关卡、双人合作、暂停菜单、在编辑器里画地图并试玩；重新录制了演示视频（[#19](https://github.com/Qiniu-ERE/zero/pull/19)）。
- 文档：README、规划总览、架构文档按 v3.0 更新；新增本更新记录（[#17](https://github.com/Qiniu-ERE/zero/pull/17)）。

## v3.0.0

- **8 个关卡**：钢铁峡谷、水乡迷宫、丛林伏击、钢铁堡垒、砖城巷战、闪电突袭、双子要塞、最终决战；选关、下一关、全部通关（[#10](https://github.com/Qiniu-ERE/zero/pull/10)）。
- **双人合作**：主页按 C，同一键盘两人一起守基地（[#13](https://github.com/Qiniu-ERE/zero/pull/13)）。
- **自己做地图**：主页按 E，画地图、实时检查、试玩、PC 版保存（[#14](https://github.com/Qiniu-ERE/zero/pull/14)）。
- **跨平台安装包**：Windows / macOS / Linux / 网页版（PWA）/ Android / iOS，GitHub Actions 自动打包发布；手机 App 的触屏模式（[#15](https://github.com/Qiniu-ERE/zero/pull/15)）。
- 规划与评估文档：v3.0 规划、跨平台、双人合作、地图编辑器、微信小游戏（[#9](https://github.com/Qiniu-ERE/zero/pull/9)、[#12](https://github.com/Qiniu-ERE/zero/pull/12)、[#16](https://github.com/Qiniu-ERE/zero/pull/16)）。

## v2.0.0

- 480×360 新布局、「微缩战场」现代画风（按 T 切回 1985 像素风）、新 HUD、中英文切换（文字烘焙成矢量路径，不会乱码）。
- 主页、复活、结算与金币、草丛和水面地形、路演演示模式。
- 4 个广告位（模拟）：主页横幅、原生广告卡、复活激励视频、结算金币 ×2（[#1](https://github.com/Qiniu-ERE/zero/pull/1)–[#8](https://github.com/Qiniu-ERE/zero/pull/8)）。

## v1.0.0

2026-10-23 上午，导入初版（v0）之后的第一批改动，没有单独发布安装包：

- 加入音效、中文字体，砖墙要打两下才碎，README 加上玩法动图（`48286af`）。
- README 头部排版（`24cb06e`、`3fec2c9`、`6c99e67`）。
- 现代 / 经典画风切换（按 T，`3f5d829`）。

这 5 个提交是**直接推到 main 的，没有走 Pull Request**：当时团队还没开始按 PR 流程开发。从 v2.0 起，main 上的每个改动都通过 PR 合入。`v1.0.0` 标签是事后补打在 `3f5d829` 上的，用来标出这一段历史，代码没有改动。

## v0

- 导入的基础版本：初版坦克大战（2026-10-23 的首次提交）。之后的版本都是在它之上新增的。
