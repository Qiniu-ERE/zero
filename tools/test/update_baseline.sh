#!/bin/sh
# 重新生成覆盖率基线 tests/coverage-baseline.json（见 docs/v4/TEST_PLAN.md 第 8.2 节）
#
# 用法：tools/test/update_baseline.sh
#   完整跑两遍引擎内测试并统计覆盖率（每遍约 5 分钟）：两遍都覆盖到的记为“覆盖到”，只有一遍覆盖到的记为“不稳定”。
#   覆盖率提高了、或者删掉了某个功能时运行，把生成的文件和改动一起提交。
#   任何一遍有测试失败就停下，不生成基线（失败的那一遍的日志留着）；成功后删掉两遍的工作目录（每遍约 600 MB）。
#   KEEP=1：成功后也保留工作目录。
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
# 带上仓库路径的校验和：同一台机器上两个 clone 同时跑不会互相删
REPO_ID=$(printf '%s' "$ROOT" | cksum | cut -d' ' -f1)
RUNS=${TMPDIR:-/tmp}/tankbattle-baseline-$REPO_ID
rm -rf "$RUNS" && mkdir -p "$RUNS"
for n in 1 2; do
    echo "==> 第 $n 遍"
    # 先把输出存到文件再看退出码：sh 没有 pipefail，写成 run_spx.sh | grep 的话测试失败也会继续生成基线
    rc=0
    NO_BASELINE=1 TEST_WORK="$RUNS/run$n" "$ROOT/tools/test/run_spx.sh" --coverage > "$RUNS/run$n.log" 2>&1 || rc=$?
    grep -E '^(ok|FAIL)|断言' "$RUNS/run$n.log" || true
    if [ $rc -ne 0 ]; then
        echo "第 $n 遍有测试失败（退出码 ${rc}），不生成基线。完整输出：$RUNS/run$n.log"
        exit 1
    fi
done
python3 "$ROOT/tools/test/spx_coverage.py" baseline "$ROOT/tests/coverage-baseline.json" "$RUNS/run1" "$RUNS/run2"
if [ -z "${KEEP:-}" ]; then
    rm -rf "$RUNS"
    echo "已删除工作目录 ${RUNS}（KEEP=1 可以保留）"
fi
