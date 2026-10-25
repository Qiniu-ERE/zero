# 坦克大战 v5.0 · 全面审查清单

> 2026-10-25 对整个项目（`main`，`373a20e`，v4.0.1 之后）做的一次全面审查，分三部分：**游戏本身**、**打包发布与测试工具**、**文档与仓库**。已经在 v5 其他文档里计划好的事（去掉每日挑战、商店版去广告、手柄、存档、改名、最小字号、老鹰友伤的回归测试）不在这里重复。
>
> 全部条目经确认列入 v5.0，排期见第四节和 [PLAN.md 第六节](PLAN.md#六里程碑与-pr-拆分)。**本文只是清单，还没有改代码。**
>
> “验证”一栏说明是怎么确认的：**实测** = 跑过测试或工具复现；**读代码** = 追过调用链；**待验证** = 推断，实施前要先复现。

## 一、游戏本身（A）

| 编号 | 级别 | 问题 | 位置 | 验证 | 改法 | 阶段 |
|---|---|---|---|---|---|---|
| A1 | 高 | **双人时，一个人的子弹打中敌人，另一个人正在飞的子弹也会消失**：敌人被打中时广播 `pbHit`，所有活着的玩家子弹收到后都会消失 | `Enemy.spx:72`、`PBullet.spx:59-63` | 实测：2P 先开枪、1P 打中敌人，0.25 秒后 `pbCount2 = 0`；去掉敌人则 `pbCount2 = 1` | 只让打中的那一发消失：按距离判断，或者像敌人子弹的 `ebHit` 一样做标记 | P1 |
| A2 | 高 | **复活时不清场**：只修好基地、加命，敌人和敌人子弹都还在，护墙也不补。贴在基地旁的敌人一解冻就能再打掉基地，这时已经复活过，直接进结算 | `main.spx:943-965` `revive()` | 读代码 | 复活时清掉敌人子弹和基地附近的敌人，补回护墙，给几秒保护 | P1 |
| A3 | 高 | **选关只能按键盘 1~8**：主页只有“开始、双人、做地图”三个可点的按钮，鼠标和手机玩家每次只能从第 1 关开始 | `main.spx:1426-1434`、`UI.spx:420-427`、`build.py:499` | 读代码 | 做一个选关画面（`kScreen` 的一种，按钮区域用 `button()` 生成）；和存档的解锁进度一起做 | P1 |
| A4 | 高 | **8 关难度不是递增的**：玩家不动、只看基地多久失守，第 6 关约 23 秒、第 7 关约 21 秒、**最终关约 49 秒**、第 1 关约 50 秒，第 4 关 95 秒都没失守（钢墙多，敌人开不到基地）；每关都重置为 3 条命 | `main.spx:249-267` `stageTune`、`main.spx:1317` | 模拟（每关只跑 1 次，结果仅供参考） | 每关多跑几次模拟，定一条难度曲线，调整地图和敌人配置；模拟脚本放进 `tools/test/` | P2 前 |
| A5 | 中 | 作为付费游戏内容偏少：没有原版的道具（星星、铲子、头盔、炸弹、定时器），也没有奖励坦克 | — | 读代码 | 评估加入道具；注意解释器的方法表上限（[架构文档 9.1](../ARCHITECTURE.md)） | P2 前 |
| A6 | 中 | 触屏版画面上全是键盘按键提示（Enter、P、1-8、J、Esc、R、H） | `build.py:473、496-500、535、546、597、609、614`；`UI.spx:248` 只隐藏了右侧面板的提示 | 读代码 | 生成一套不带按键提示的触屏造型；和手柄版提示（[TECH.md 1.3](TECH.md#13-游戏里要跟着改的)）一起做“按输入设备切换” | P1 |
| A7 | 中 | 触屏版仍能从编辑器进入双人试玩：`newGame` 检查了 `touchUI`，`playCustom(true)` 没检查，开出一个没法操作的 2P | `main.spx:605-616、629-631`；`UI.spx:444` | 读代码 | `playCustom` 也检查 `touchUI` 并提示，或触屏版隐藏这个按钮 | P1 |
| A8 | 中 | 路演演示模式（主页按 P）停不下来：对局中 Esc 无效（`pauseGame` 遇到 `autopilot` 直接返回）；演示进到编辑器后按 Esc 回主页，`demoV3` 还在后台画格子，接着又自动开一局 | `main.spx:1458-1460、1543-1581、1199-1215` | 读代码 | 商店版去掉 P 键和提示；路演版加一个取消标志，每一步都检查 | P1 |
| A9 | 中 | **没有退出游戏的入口**：主页按 Esc 没有处理，也没有退出按钮 | `main.spx:1436-1446` | 读代码 | PC 版主页加“退出”（spx 有 `exit`） | P1 |
| A10 | 中 | 没有设置界面，没有音量；画风只能按 T 切换，触屏版切不了 | 搜不到音量相关调用 | 读代码 | 主页和暂停菜单加“设置”：音乐、音效、画风、语言、全屏（spx 有 `SetVolume`、`set_window_fullscreen`）；见 [EXPERIENCE.md 2.3](EXPERIENCE.md#23-设置) | P1 |
| A11 | 中 | 敌人出生不检查出生点有没有被占；已经重叠的坦克能互相穿过（碰撞用“刚刚碰上”判断），玩家可以蹲在出生点刷敌人 | `main.spx:1260-1273`、`Enemy.spx:60-64、18-27`、`Player.spx:80-84` | 读代码 | 出生点被占就推迟出兵（像原版先闪星星）；对齐半格时也检查坦克 | P2 前 |
| A12 | 中 | 基地刚被毁、复活窗还没弹出（2.2 秒内）时按 Esc（本想暂停），会直接放弃复活。Enter / J 有保护，Esc 没有 | `main.spx:1437-1438` | 读代码 | Esc 也要等复活窗出现（检查 `screen` 前缀） | P1 |
| A13 | 中 | 编辑器的清空（C）、随机（R）、复制关卡（K）没有确认也不能撤销；只有一个手动保存位，不会自动保存 | `main.spx:1398-1404、1448-1455、1417、636-644` | 读代码 | 保留上一份地图做一步撤销；离开编辑器时自动保存；和存档的地图槽位一起做 | P1 |
| A14 | 中 | 手机上保存地图大概率失败（Android 上 `os.UserConfigDir()` 可能拿不到目录），提示还写着“网页版不能存文件” | `main.spx:525-531`、`strings.py:41` | 待验证 | 存到应用数据目录（spx 引擎里有 `persistent_data_dir`，要看能否暴露给脚本）；提示按平台区分 | P3 |
| A15 | 低 | 生命超过 3 条时界面只显示 3 个图标（复活后可能有 4 条） | `UI.spx:281-292`、`main.spx:786-789` | 读代码 | 显示成“图标 ×N” | P1 |
| A16 | 低 | 暂停菜单“重开本关”会把复活次数清零，可以无限复活 | `main.spx:1451`、`1326` | 读代码 | 复活次数按关卡记录 | P1 |
| A17 | 低 | 最后一辆敌人和基地在同一帧被打掉时，可能判成胜利（`enemyKilled` 不检查 `gameOver`） | `main.spx:1231-1257` | 待验证 | `enemyKilled` 遇到 `gameOver` 不再结算；补一条测试 | P1 |
| A18 | 低 | 触屏模式下点任何按钮都会顺便开一枪；点“再来一局”后开局就打出一发 | `Player.spx:192-211` | 读代码 | 只在战场或方向键上按下才开火，并先等手指松开 | P1 |
| A19 | 低 | 胜利结算太突然（最后一辆敌人被打掉立刻结算），没有原版的分类击毁统计和“STAGE N”过场 | `main.spx:1254` | 读代码 | 延迟 1~2 秒再结算；结算页做击毁统计（商店版去掉金币 ×2 后正好有位置） | P2 前 |
| A20 | 低 | 手机切到后台不会自动暂停，安卓返回键没有处理（商店审核会看） | — | 待验证 | 确认 spx 能否拿到焦点事件；能拿到就失去焦点时暂停，返回键 = 暂停 | P3 |
| A21 | 低 | 52 张全屏造型都是 960×720 位图，4K 全屏会发虚；全部解码约占 140 MB，手机上有压力 | `index.json`、造型 `bitmapResolution 2` | 待验证 | 先实测内存和清晰度，再决定是否拆分背景和按钮 | P3 |
| A22 | 低 | 死代码和遗留：`enemiesLeft` 只写不读；`strings.py` 里大量只给效果图用的文案（连击、强化、钻石、“35 story stages”、“Ad · 15s”）；演示模式的状态分散在主逻辑里 | `main.spx:13、1249、1324`；`strings.py` | 读代码 | 清理；演示相关逻辑尽量集中 | P1 |
| A23 | 低 | 碰撞检测每次都重建空间索引（spx v3.3.0 实现），现在每帧约 30 次调用没问题；敌人或特效变多后低端手机可能掉帧 | spx `collision_optimizer.go` | 待验证 | 加了道具和特效后在低端机测帧率 | P3 |

## 二、打包发布与测试工具（B）

| 编号 | 级别 | 问题 | 位置 | 验证 | 改法 | 阶段 |
|---|---|---|---|---|---|---|
| B1 | 高 | **v4.0.1 的 APK 版本号还是 4.0.0**（`versionCode = 40000`）：版本号只在 `setup_spx.sh` 调 `patch_spx.py` 时写进 spx 模板，模板编进 spx 二进制；之后只跑 `build.sh` 不会更新。代码本身是新的 | `setup_spx.sh`、`patch_spx.py`、spx 模板 `export_presets.cfg` | 实测：`aapt dump badging` 发布的 APK | `build.sh android / ios` 开头核对模板版本号和 `APP_VERSION`，不一致就重打补丁或报错；`build_local.sh` 打完再核对一次 | P1 |
| B2 | 高 | **安卓签名证书每个版本都不一样**：v3.0.1（CI）和 v4.0.1（本机）证书不同，用户没法覆盖升级。本机证书是 `build.sh` 临时生成在 `.build/cache/` 里的，删掉 `.build` 就换了 | `build.sh:157-164` | 实测：对比两个 APK 的证书 | 调试证书放到仓库外的固定位置（例如 `~/.config/tankbattle/`）；发布说明告诉老用户先卸载一次；v5 另做正式证书；`.gitignore` 加 `*.keystore *.jks *.p12 *.mobileprovision .env` | P1 |
| B3 | 高 | `build_local.sh` 在 macOS 自带的 bash 3.2 下，只要设了 `JAVA_HOME`，安卓打包必定失败：空数组在 `set -u` 下展开报 unbound variable | `build_local.sh:63-70` | 实测：复现报错 | 改成 `${java_cmd[@]+"${java_cmd[@]}"}` | P1 |
| B4 | 中 | `release_local.sh` 找缺失平台的回退版本：**主要问题已在 [#53](https://github.com/Qiniu-ERE/zero/pull/53) 修好**（会一直往回找到有这个平台的版本）；剩下的是 `gh release list` 按创建时间排序，不是按版本号 | `release_local.sh` | 读代码 | 按版本号排序 | P1 |
| B5 | 高 | 发布前不检查安装包是不是从这个标签打的：只检查标签存在，不检查 `HEAD` 是否等于标签、工作区是否干净；`build_local.sh` 打包前不清同版本的旧包，某个平台这次打失败时旧包照样被发出去 | `release_local.sh:16-20`、`build_local.sh` | 读代码 | 打包前删掉 `dist/` 里同版本的旧包；发布前核对 `dist/BUILD_LOCAL.md` 里的提交号和标签，表里有 ❌ 就停 | P1 |
| B6 | 中 | 没法给已有的 Release 补包（`gh release create` 遇到已存在的 Release 直接失败），以后补 Windows / iOS 只能手工上传、重算校验和、改说明 | `release_local.sh:51` | 读代码 | 加 `--append` 模式：上传、重算 `SHA256SUMS.txt`、更新说明 | P1 |
| B7 | 中 | `release.yml` 名不副实：注释说手动运行不发布，但在标签上手动运行会发布，并和本地建好的 Release 冲突；不能只打指定平台；发布说明的生成逻辑和 `release_local.sh` 是两份 | `release.yml:6-9、53、284` | 读代码 | 手动运行加“平台”和“上传到已有 Release”两个输入；说明统一调用一个脚本 | P2 |
| B8 | 中 | 测试临时目录路径写死（`$TMPDIR/tankbattle-*`），并且先 `rm -rf`：同一台机器上两个 clone 同时跑测试会互相删 | `run_spx.sh:18、23`、`pr_check.sh:16-17`、`run_all.sh:15`、`update_baseline.sh:9` | 读代码 | 路径里带上仓库路径的哈希，或用 `mktemp -d` | P1 |
| B9 | 中 | 临时文件没人清：覆盖率基线目录 1.2 GB、录屏 217 MB 等，OrbStack 虚拟机 4.9 GB；本机磁盘本来就紧 | `update_baseline.sh` 等 | 实测 | 新增 `tools/dev/clean.sh`；`update_baseline.sh` 结束时清理；`build_local.sh` 开始前检查剩余空间 | P1 |
| B10 | 中 | 本机系统 Python 没装 fontTools，生成素材的检查（T06 / T07、`pr_check` 第 2 项）被跳过，`run_all` 仍显示“全部通过”；`requirements.txt` 没锁版本，T07“生成结果可复现”依赖 fontTools 版本 | `tools/assets/requirements.txt`、`pr_check.sh` | 实测 | 锁版本；新增 `tools/dev/venv.sh` 建 `.venv`，`pr_check` 默认用它；有跳过项也算不合格 | P1 |
| B11 | 中 | `update_baseline.sh` 在测试失败时也会生成覆盖率基线（`sh` 没有 pipefail，管道吞掉了失败） | `update_baseline.sh:13` | 读代码 | 先把输出存文件、检查退出码，再统计 | P1 |
| B12 | 中 | 覆盖率偏乐观：没覆盖的 22 个点里 20 个是按键 / 点击处理（`onKey`、`onClick`），按键和动作的对应、触屏的点击判断都没测；统计只看函数入口，不看分支 | `tests/coverage-baseline.json` | 读代码 | 把按键处理抽成函数，测试直接调用；`hit()` 用坐标表测试；README 徽章注明是“函数入口覆盖率” | P1 |
| B13 | 中 | 几个工具本身没有测试：`spx_coverage.py`、`patch_spx.py`（缺选项时应失败、版本号换算）、`release_local.sh` 生成说明的替换、`env.sh` 解析版本号（`## v4.0.1-rc.1` 匹配不上，会得到空版本号） | `tools/` | 读代码 | 在 `tests/tools` 下用小样本补测试 | P1 |
| B14 | 中 | 安装包启动测试另打了一个带测试脚本的包，**发出去的那个包没被启动过** | `build_local.sh:32-36` | 读代码 | 再直接启动一次 `dist/` 里的安装包，检查进程能存活、日志没有 panic | P1 |
| B15 | 中 | `build.sh` 会改用户全局的 Godot 设置；如果 `JAVA_HOME` 后来失效，因为只替换空值，以后不会再修 | `build.sh:168-174` | 读代码 | 每次覆盖为当前值，或打包时用临时的 HOME / XDG 目录 | P1 |
| B16 | 中 | 下载没有校验和：MoltenVK（`build.sh:195`）、虚拟机里的 Go（`linux_vm.sh:31`）、spx 运行时和导出模板；本机 Go 1.26.8，打包环境写的是 1.26.5，`env.sh` 却说“版本都锁死” | `build.sh`、`linux_vm.sh`、`env.sh` | 读代码 | `env.sh` 写死 sha256 并校验；生成的 `go.mod` 加 `toolchain go1.26.5` 或检查 `go version` | P2 |
| B17 | 低 | 零散问题：Actions 引用没锁到提交；`test.yml` 只是 `pr_check` 的一部分（没有网页外壳测试和覆盖率）；Windows zip 用 `7z a` 会追加到旧文件里；`release_local.sh` 没有 trap，临时文件残留；`tools/dev/shot.sh` 结束时会杀掉机器上所有游戏进程、端口固定 8080；`pr_check` 的 `.xbp` 比较没排除 `.DS_Store`，在 Finder 里打开过就会误报 | `.github/workflows/*`、`build.sh:113`、`shot.sh`、`pr_check.sh:53` | 读代码 | 逐个修 | P1~P2 |
| B18 | 中 | **v5 需要的打包能力都还没有**：`build.sh` 没有参数解析，接不了 `--store`；没有给 spx 源码打补丁的机制（手柄要用，建议 `setup_spx.sh` 按顺序 `git apply tools/export/patches/*.patch`，补丁内容算进缓存）；macOS 主程序是 shell 启动脚本（为了设 `GODEBUG`），只有 ad-hoc 签名且 `codesign` 错误被吞掉，公证和 Mac App Store 需要真正的签名；iOS 用的是占位 Team ID，没有描述文件和导出选项；没有 AAB；没有 Steam depot 配置；Windows 和签名 iOS 本机打不了 | `build.sh:88-106`、`patch_spx.py:41` | 读代码 | 分到 P1（参数、补丁机制）、P2（Steam depot、MSIX、macOS 签名）、P3（iOS）、P4（AAB）；本机打不了的平台用 B6 的 `--append` 或 B7 的指定平台补 | P1~P4 |

## 三、文档与仓库（C）

| 编号 | 级别 | 问题 | 位置 | 改法 | 阶段 |
|---|---|---|---|---|---|
| C1 | 高 | **v4.0.0 有标签但没有 GitHub Release** | GitHub | 用 `release_local.sh` 补发；补不了就在更新记录里注明“只打标签，没有安装包” | P1 |
| C2 | 高 | 最新版缺 Windows 和 iOS 包，README 还写着“v3.0.2 没有，请用 v3.0.1”；这两个平台的玩家拿不到 v3.0.2 之后的修复（误点广告、子弹相撞等）；仓库描述也写着有这两个平台 | `README.md:44`、仓库描述 | README 改成“v3.0.2 起本机打包，Windows / iOS 暂无新包，v3.0.1 不含之后的修复”；能借到 Windows 机器和 Xcode 就补包（B6） | P1 |
| C3 | 高 | README 首屏主页截图是 v2 的旧图：双人合作标着“即将推出”，还有已删掉的“AI 造关”入口 | `README.md:29` 引用 `docs/v2/screens/home-zh.png` | 换成当前主页截图；HUD 截图换成带 Ⅱ 暂停按钮的；去掉每日挑战后再截一次 | P1 |
| C4 | 高 | 多处还写“推送标签后 GitHub Actions 自动打包发布”，和现在本地打包、Actions 只能手动触发矛盾 | `README.md:155`、`docs/v3/PLAN.md:62、67、75`、`docs/ARCHITECTURE.md:116`（同文件 292 行又说只能手动）、`docs/v3/CROSS_PLATFORM.md:11、240`、`docs/v4/PLAN.md:5、105`、`docs/v4/TEST_PLAN.md:286` | 统一改成“v3.0.2 起本机打包（`build_local.sh` + `release_local.sh`），Actions 只能手动触发”；v3.0.0 当时用 Actions 发布，写成历史 | P1 |
| C5 | 中 | ARCHITECTURE 停在 v3 / v4.0：开头写“本文说明游戏（v3.0）”；版本列表缺 v4.0.0、v4.0.1；PR 记录只到 #47，缺 #48~#53，也没提关闭的 #11；“v3.0 的新功能还没在 XBuilder 里实测”已过时（v4 有 XBuilder 编译检查 T09）；分工表缺 v4.0.1 的子弹相撞修复 | `docs/ARCHITECTURE.md:3、25、290`、第 11 节 | 逐项补齐 | P1 |
| C6 | 中 | README 版本信息没跟上 v4（文档表、发布版本列表、顶部导航）；快速开始里 `git clone goplus/spx && make setup` 拿的是最新主分支，而打包脚本固定在 `c3c0da5`，评委照着装可能装到不兼容的版本 | `README.md:5、59、180、257` | 补上 v4 和 v5；写明 `git checkout c3c0da5`，或推荐 `tools/export/setup_spx.sh` | P1 |
| C7 | 中 | 更新记录漏了 #51（打包改为本地、Actions 改手动）和 #53（发布回退） | `CHANGELOG.md` | v4.0.1 一节补一条，加“未发布”一节 | P1 |
| C8 | 中 | TEST_PLAN 第二、四节是规划稿写法，和实际对不上：目录写 6 个文件（实际 19 个），工具名写 `coverage.py`（实际 `spx_coverage.py`）等，示例函数写 `check / done`（实际 `tCheck / tDone`），插桩写 `println("COV")`（实际 `tCov`）；“5 个函数没覆盖”已变成 4 个；“Python 覆盖率只在 CI 里装”已无 CI；“Linux 只能手工启动”已由 `linux_vm.sh` 自动测试 | `docs/v4/TEST_PLAN.md` | 按实际更新，或标明“规划稿，实际见架构文档第 10 节” | P1 |
| C9 | 中 | README 的测试说明缺前置条件：网页外壳测试要 Node.js 18 以上（没有会静默跳过）；没装 spx 可以 `SKIP_SPX=1`；`xbuilder_check.sh` 要 Go 和网络 | `README.md:236-242` | 加一张前置条件表 | P1 |
| C10 | 中 | **演示视频没有覆盖 v4 和 v5**，而且无声 | `docs/demo/` | 为最终交付录一段约 3 分钟、带字幕的总演示：玩法 → 双人 → 编辑器 → 一条命令跑完测试 → v5 商业化，配合 [PITCH.md](PITCH.md) 的讲稿 | 路演前 |
| C11 | 中 | v4 PLAN 说“每个 PR 都附本地检查报告”，抽查 #26、#35、#53 没附 | `docs/v4/PLAN.md:94` | 改成如实描述（“#34 之后大部分 PR 附报告”），或补贴到评论里 | P1 |
| C12 | 低 | 历史文档没标注后来的变化：v2 设计稿里“本地双人待做”“AI 造关”；v3 PLAN 的 P2 还列着每日挑战，里程碑表缺 v3.0.2；CROSS_PLATFORM 7.5 节的 Actions 分钟数和“真机在 CI 上打”；发布说明模板“一份README.txt”缺空格、只提 `docs/v3/`；v4.0.1 的 Release 正文写了“徽章更新为 tests 456 passing”这类开发细节 | `docs/v2/DESIGN.md:107-108`、`docs/v3/PLAN.md:78`、`docs/v3/CROSS_PLATFORM.md`、`tools/export/RELEASE_NOTES.md:16、25` | 加一句“状态以后续版本文档为准”；逐项修 | P1 |
| C13 | 低 | 提交说明和多数 PR 标题是英文（README 里的比赛口号可以保留） | git 历史、PR 标题 | **以后的 PR 标题和提交说明用中文**（feat / fix 等前缀可以保留）；历史不改写 | 从现在起 |
| C14 | 低 | 仓库整洁度：`v3.0.2` 是轻量标签（其余都是附注标签）；main 上有三次失败的 Actions 运行，提交旁显示红叉；仓库没有主页和 topics；`docs/tankbattle.gif` 没被引用 | GitHub | 可选：`v3.0.2` 改附注标签；README 说明红叉是额度问题；加 topics（`tank`、`pwa`、`godot`、`1024-hackathon`）；删掉或用上那张 gif | P1 |
| C15 | 低 | v5 规划合入前要更新：README 文档表和更新记录还没有链接 v5 | `README.md`、`CHANGELOG.md` | v5 规划合入后补链接 | P0 合入后 |

## 四、排期

| 阶段 | 包含 | 说明 |
|---|---|---|
| **P1 第一批：先修**（约 3 天） | A1、A2、A3、A12、A15~A18、A22；B1~B5、B8、B11；C1~C9、C11、C12、C14 | 直接影响玩家或发布正确性的问题，改动小。修完发一个修复版（版本号按 [CHANGELOG](../../CHANGELOG.md) 的惯例定，例如 v4.0.2） |
| **P1 第二批：和商店版一起做** | A6~A10、A13；B6、B9、B10、B12~B15、B17、B18（参数、补丁机制） | 本来就要在商店版、手柄、存档里改的界面和工具 |
| **P2 前：玩法打磨**（约 3~4 天） | A4、A5、A11、A19 | 先多跑模拟定难度曲线，再定道具方案；Steam 发售前完成，影响评测和退款率 |
| **P2** | B7、B16、B18（Steam depot、MSIX、macOS 签名） | 和 Steam、Microsoft Store 上架一起 |
| **P3** | A14、A20、A21、A23；B18（iOS 签名） | 手机版专项 |
| **P4** | B18（AAB） | 等 spx 升级引擎 |
| **路演前** | C10 | 最终演示视频 |
| **从现在起** | C13 | 中文 PR 标题和提交说明 |

每一项实施时一个 PR（小项可以同类合并），PR 描述写明对应的编号；改游戏代码的 PR 附 `tools/test/pr_check.sh` 的结果，修 bug 的 PR 先提交能复现的失败测试。
