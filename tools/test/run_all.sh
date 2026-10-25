#!/bin/sh
# 一条命令跑完全部自动化测试：构建工具（Python）+ 网页外壳（Node.js）+ 引擎内测试（spx）
#
# 用法：tools/test/run_all.sh
#   PYTHON=/path/to/python  指定 Python（要跑美术生成器的测试，需要 fontTools：tools/dev/venv.sh 建好 .venv，
#                           这里默认就用它；没装 fontTools 时这几项会跳过）
#   SKIP_SPX=1              只跑构建工具的测试（没装 spx 时）
#   --coverage              同时统计覆盖率（见 tools/test/spx_coverage.py），构建工具测试也计入用例清单
# 有测试被跳过时最后一行是“通过，但有跳过的测试”而不是“全部通过”，每一项跳过都以“⚠️ 跳过”开头列出
# （pr_check.sh 看到它就把这一项记为 ⚠️，不算通过）。
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=${PYTHON:-python3}
[ -n "${PYTHON:-}" ] || [ ! -x "$ROOT/.venv/bin/python" ] || PY="$ROOT/.venv/bin/python"
status=0
skips=""
COV=""
if [ "${1:-}" = --coverage ]; then COV=--coverage; fi
# 带上仓库路径的校验和：同一台机器上两个 clone 同时跑不会互相覆盖
REPO_ID=$(printf '%s' "$ROOT" | cksum | cut -d' ' -f1)
UNITTEST_LOG=${TMPDIR:-/tmp}/tankbattle-unittest-$REPO_ID.log
export UNITTEST_LOG

echo "==> 构建工具测试（tests/tools）"
"$PY" -m unittest discover -v -s "$ROOT/tests/tools" > "$UNITTEST_LOG" 2>&1 || status=1
tail -4 "$UNITTEST_LOG"
grep -E '^(FAIL|ERROR):' "$UNITTEST_LOG" || true
n=$(sed -n 's/.*skipped=\([0-9][0-9]*\).*/\1/p' "$UNITTEST_LOG" | tail -1)
if [ -n "$n" ] && [ "$n" -gt 0 ]; then
    echo "⚠️ 跳过 ${n} 个构建工具测试：$(grep -o "skipped '[^']*'" "$UNITTEST_LOG" | sort -u | sed "s/^skipped '\(.*\)'$/\1/" | tr '\n' ' ')"
    skips="${skips} 构建工具测试"
fi

echo
echo "==> 网页外壳测试（tests/web，需要 Node.js 18 以上）"
if command -v node > /dev/null 2>&1; then
    node --test "$ROOT"/tests/web/*.test.mjs > "$UNITTEST_LOG.web" 2>&1 || status=1
    grep -E '^# (pass|fail)' "$UNITTEST_LOG.web"
    grep -E '^not ok' "$UNITTEST_LOG.web" || true
    cat "$UNITTEST_LOG.web" >> "$UNITTEST_LOG"
else
    echo "⚠️ 跳过网页外壳测试：没有 node"
    skips="${skips} 网页外壳测试"
fi

if [ -z "${SKIP_SPX:-}" ]; then
    echo
    echo "==> 引擎内测试（tests/spx）"
    "$ROOT/tools/test/run_spx.sh" $COV || status=1
else
    echo
    echo "⚠️ 跳过引擎内测试：SKIP_SPX=1"
    skips="${skips} 引擎内测试"
fi

echo
if [ $status -ne 0 ]; then echo "有测试失败"
elif [ -n "$skips" ]; then echo "通过，但有跳过的测试：${skips# }"
else echo "全部通过"; fi
exit $status
