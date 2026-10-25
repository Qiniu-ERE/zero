## 改了什么

<!-- 一两句话说清楚这个 PR 做了什么 -->

## 为什么

<!-- 要解决的问题；有对应的 issue 或测试发现的问题，写上编号 -->

## 测试

- 新增 / 修改的用例 ID：<!-- 例如 C20、F30；用例清单在 docs/v4/TEST_PLAN.md 第三节，新用例要登记 -->
- 修 bug 的 PR：先提交一个能复现问题的失败测试，再提交修复（PR 里能看到测试从失败变成通过）

## 本地检查报告

<!--
运行 tools/test/pr_check.sh --coverage，把生成的报告（默认在 $TMPDIR/pr_check.md）整个贴在这里。
GitHub 上的 Actions 检查目前启动不了（组织额度），以本地报告为准，所有项都要是 ✅。
覆盖率提高了：运行 tools/test/update_baseline.sh，把 tests/coverage-baseline.json 一起提交。
-->

## 合入前确认

- [ ] 目标分支对（功能分支 → 集成分支，例如 `v4.0`；集成分支 → `main`）
- [ ] 改了游戏代码：重新打包 `TankBattle.xbp`（`./tools/package_xbp.sh`）；改了文案或美术代码：重新运行 `python3 tools/assets/build.py`
- [ ] 本地检查报告全部 ✅，没有覆盖率退步
- [ ] 合入方式选 **Create a merge commit**（不要 Squash / Rebase）
