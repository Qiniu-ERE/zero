#!/bin/sh
# 一条命令跑完全部自动化测试：构建工具（Python）+ 网页外壳（Node.js）+ 引擎内测试（spx）
#
# 用法：tools/test/run_all.sh
#   PYTHON=/path/to/python  指定 Python（要跑美术生成器的测试，需要先 pip install -r tools/assets/requirements.txt，
#                           没装 fontTools 时这几项会跳过）
#   SKIP_SPX=1              只跑构建工具的测试（没装 spx 时）
#   --coverage              同时统计覆盖率（见 tools/test/spx_coverage.py），构建工具测试也计入用例清单
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=${PYTHON:-python3}
status=0
COV=""
if [ "${1:-}" = --coverage ]; then COV=--coverage; fi
UNITTEST_LOG=${TMPDIR:-/tmp}/tankbattle-unittest.log
export UNITTEST_LOG

echo "==> 构建工具测试（tests/tools）"
"$PY" -m unittest discover -v -s "$ROOT/tests/tools" > "$UNITTEST_LOG" 2>&1 || status=1
tail -4 "$UNITTEST_LOG"
grep -E '^(FAIL|ERROR):' "$UNITTEST_LOG" || true

echo
echo "==> 网页外壳测试（tests/web，需要 Node.js 18 以上）"
if command -v node > /dev/null 2>&1; then
	node --test "$ROOT"/tests/web/*.test.mjs > "$UNITTEST_LOG.web" 2>&1 || status=1
	grep -E '^# (pass|fail)' "$UNITTEST_LOG.web"
	grep -E '^not ok' "$UNITTEST_LOG.web" || true
	cat "$UNITTEST_LOG.web" >> "$UNITTEST_LOG"
else
	echo "跳过：没有 node"
fi

if [ -z "${SKIP_SPX:-}" ]; then
	echo
	echo "==> 引擎内测试（tests/spx）"
	"$ROOT/tools/test/run_spx.sh" $COV || status=1
fi

echo
[ $status -eq 0 ] && echo "全部通过" || echo "有测试失败"
exit $status
