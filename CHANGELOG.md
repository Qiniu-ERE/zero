# 更新记录

安装包在 [Releases](https://github.com/Qiniu-ERE/zero/releases) 下载。每个版本对应一个 Git 标签。

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

## v0

- 导入的基础版本：初版坦克大战（2026-10-23 的首次提交）。之后的版本都是在它之上新增的。
