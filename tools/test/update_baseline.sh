#!/bin/sh
# 重新生成覆盖率基线 tests/coverage-baseline.json（见 docs/v4/TEST_PLAN.md 第 8.2 节）
#
# 用法：tools/test/update_baseline.sh
#   完整跑两遍引擎内测试并统计覆盖率（每遍约 5 分钟）：两遍都覆盖到的记为“覆盖到”，只有一遍覆盖到的记为“不稳定”。
#   覆盖率提高了、或者删掉了某个功能时运行，把生成的文件和改动一起提交。
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
RUNS=${TMPDIR:-/tmp}/tankbattle-baseline
rm -rf "$RUNS" && mkdir -p "$RUNS"
for n in 1 2; do
	echo "==> 第 $n 遍"
	NO_BASELINE=1 "$ROOT/tools/test/run_spx.sh" --coverage | grep -E '^(ok|FAIL)|断言'
	cp -R "${TMPDIR:-/tmp}/tankbattle-test" "$RUNS/run$n"
done
python3 "$ROOT/tools/test/spx_coverage.py" baseline "$ROOT/tests/coverage-baseline.json" "$RUNS/run1" "$RUNS/run2"
