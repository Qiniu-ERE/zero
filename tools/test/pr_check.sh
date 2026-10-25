#!/bin/sh
# PR 合入前的本地检查（替代 GitHub Actions，见 docs/v4/TEST_PLAN.md 第五节）
#
# 用法：tools/test/pr_check.sh [--coverage]
#   PYTHON=/path/to/python  要有 fontTools（pip install -r tools/assets/requirements.txt），否则“生成的素材”一项跳过
#   OUT=文件                 结果报告（Markdown），默认 $TMPDIR/pr_check.md；把它贴到 PR 里
#
# 检查的内容和 .github/workflows/check.yml 相同，再加上 v4 的全部测试：
#   1. 关卡地图合法（tools/levels/check.py）
#   2. 生成的美术和界面和提交的一致（在临时副本里运行 build.py 再比较，不改工作区）
#   3. TankBattle.xbp 和 TankBattle/ 一致
#   4. 构建工具测试 + 引擎内测试（tools/test/run_all.sh；--coverage 同时统计覆盖率）
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=${PYTHON:-python3}
OUT=${OUT:-${TMPDIR:-/tmp}/pr_check.md}
TMP=${TMPDIR:-/tmp}/tankbattle-prcheck
rm -rf "$TMP" && mkdir -p "$TMP"
status=0
rows=""

row() { # 名字 结果 耗时 说明
	rows="${rows}| $1 | $2 | ${3}s | $4 |
"
	[ "$2" != "❌" ] || status=1
	echo "$2 $1（${3}s）$4"
}

cd "$ROOT" || exit 1

t=$(date +%s)
if python3 tools/levels/check.py > "$TMP/levels.log" 2>&1; then
	row "关卡地图" ✅ $(($(date +%s) - t)) "$(grep -c '✓' "$TMP/levels.log") 张合格"
else
	row "关卡地图" ❌ $(($(date +%s) - t)) "$(grep '✗' "$TMP/levels.log" | tr '\n' ' ')"
fi

t=$(date +%s)
if "$PY" -c "import fontTools" 2>/dev/null; then
	mkdir -p "$TMP/gen/tools"
	cp -R TankBattle "$TMP/gen/" && cp -R tools/assets "$TMP/gen/tools/"
	rm -rf "$TMP/gen/TankBattle/.temp"
	if (cd "$TMP/gen" && "$PY" tools/assets/build.py > "$TMP/build.log" 2>&1) && diff -rq TankBattle "$TMP/gen/TankBattle" -x .temp > "$TMP/gen.diff" 2>&1; then
		row "生成的素材是最新的" ✅ $(($(date +%s) - t)) ""
	else
		row "生成的素材是最新的" ❌ $(($(date +%s) - t)) "$(head -3 "$TMP/gen.diff" "$TMP/build.log" 2>/dev/null | tr '\n' ' ')；运行 python3 tools/assets/build.py 并提交"
	fi
else
	row "生成的素材是最新的" ⚠️ 0 "跳过：${PY} 没有 fontTools"
fi

t=$(date +%s)
mkdir -p "$TMP/xbp"
if (cd "$TMP/xbp" && unzip -q "$ROOT/TankBattle.xbp") && diff -rq "$TMP/xbp" TankBattle -x .temp > "$TMP/xbp.diff" 2>&1; then
	row "TankBattle.xbp 是最新的" ✅ $(($(date +%s) - t)) ""
else
	row "TankBattle.xbp 是最新的" ❌ $(($(date +%s) - t)) "$(head -3 "$TMP/xbp.diff" | tr '\n' ' ')；运行 ./tools/package_xbp.sh 并提交"
fi

t=$(date +%s)
# 用这个提交里有的测试脚本：run_all.sh（构建工具 + 引擎内），较早的提交只有其中一部分
if [ -x tools/test/run_all.sh ]; then
	what="run_all.sh $*"
	PYTHON="$PY" tools/test/run_all.sh "$@" > "$TMP/tests.log" 2>&1
	rc=$?
else
	what=""
	rc=0
	: > "$TMP/tests.log"
	if [ -d tests/tools ]; then
		what="unittest"
		{ echo "==> 构建工具测试（tests/tools）"; "$PY" -m unittest discover -s tests/tools 2>&1 | tail -3; } >> "$TMP/tests.log" || rc=1
		grep -q '^FAILED' "$TMP/tests.log" && rc=1
	fi
	if [ -x tools/test/run_spx.sh ]; then
		what="${what:+${what} + }run_spx.sh"
		{ echo "==> 引擎内测试（tests/spx）"; tools/test/run_spx.sh 2>&1; } >> "$TMP/tests.log" || rc=1
	fi
fi
if [ -z "$what" ]; then
	row "自动化测试" ⚠️ $(($(date +%s) - t)) "这个提交里还没有测试（只有文档）"
elif [ $rc -eq 0 ]; then
	row "自动化测试（${what}）" ✅ $(($(date +%s) - t)) ""
else
	row "自动化测试（${what}）" ❌ $(($(date +%s) - t)) "见下面的输出"
fi

{
	echo "### 本地检查（tools/test/pr_check.sh）"
	echo
	echo "- 提交：\`$(git rev-parse --short HEAD)\`（$(git rev-parse --abbrev-ref HEAD)）$( [ -z "$(git status --porcelain)" ] || echo '，⚠️ 工作区有未提交的改动')"
	echo "- 环境：$(uname -s) $(uname -r)，$(spx version 2>/dev/null | head -1)，$("$PY" --version 2>&1)"
	echo "- 时间：$(date '+%Y-%m-%d %H:%M')"
	echo
	echo "| 检查 | 结果 | 耗时 | 说明 |"
	echo "|---|---|---|---|"
	printf '%s' "$rows"
	echo
	echo '<details><summary>测试输出</summary>'
	echo
	echo '```'
	grep -E '^(==>|ok |FAIL|Ran |OK|FAILED|---- |  [a-z_]+: |\|)' "$TMP/tests.log" | grep -v -E '^\|---'
	echo '```'
	echo
	echo '</details>'
} > "$OUT"

echo
echo "报告：${OUT}（贴到 PR 的描述或评论里）"
exit $status
