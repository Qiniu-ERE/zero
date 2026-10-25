#!/bin/sh
# 跑引擎内测试（macOS / Linux，需要 spx）
#
# 用法：tools/test/run_spx.sh                      # 跑 tests/spx/ 下的全部测试
#       TEST_TIMEOUT=90 tools/test/run_spx.sh       # 每组默认超时（秒），默认 60
#       tools/test/run_spx.sh --coverage           # 同时统计覆盖率，报告写到 $WORK/coverage.md（见 spx_coverage.py）
#       tools/test/run_spx.sh tests/spx/grid.spx   # 只跑一组
#
# 做法（详见 docs/v4/TEST_PLAN.md 第二节）：每组测试复制一份工程，把 prelude.spx 的断言函数插到
# 副本 main.spx 的第一个 func 前面（类文件里 func 必须写在事件处理之前），把测试脚本追加到末尾，
# 用 spx run -headless 运行。仓库里的游戏不会被改动。
#
# spx 进程的退出码永远是 0，所以靠输出判断：出现 TEST FAIL、没有 TEST DONE、超时、
# 或者输出里有 panic / cannot alloc method（解释器方法表上限）都算失败。
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TIMEOUT=${TEST_TIMEOUT:-60}
WORK=${TMPDIR:-/tmp}/tankbattle-test
COVERAGE=""
if [ "${1:-}" = --coverage ]; then COVERAGE=1; shift; fi
[ $# -gt 0 ] || set -- "$ROOT"/tests/spx/*.spx

rm -rf "$WORK" && mkdir -p "$WORK"
# spx 要用到 Go 的模块和编译缓存，先记下真实的位置（下面会把 HOME 换成临时目录）
GOPATH=${GOPATH:-$(go env GOPATH 2>/dev/null || echo "$HOME/go")}
GOCACHE=${GOCACHE:-$(go env GOCACHE 2>/dev/null || echo "$HOME/.cache/go-build")}
# Linux 上 spx 的缓存在 XDG_CACHE_HOME（默认 ~/.cache），也保持在真实位置，免得每组测试都重新准备
XDG_CACHE_HOME=${XDG_CACHE_HOME:-$HOME/.cache}
# 测试脚本用 TB_ROOT 找到仓库里的测试数据（tests/data）
TB_ROOT=$ROOT
export GOPATH GOCACHE XDG_CACHE_HOME TB_ROOT
failed=""
total_pass=0
total_fail=0
total_xfail=0
for suite in "$@"; do
	name=$(basename "$suite" .spx)
	dir="$WORK/${name}"
	mkdir -p "$dir/home"
	cp -R "$ROOT/TankBattle" "$dir/"
	main="$dir/TankBattle/main.spx"
	[ -z "$COVERAGE" ] || python3 "$ROOT/tools/test/spx_coverage.py" instrument "$dir/TankBattle"
	awk -v prelude="$ROOT/tools/test/prelude.spx" '
		!done && /^func / { while ((getline line < prelude) > 0) print line; done = 1 }
		{ print }
	' "$main" > "$main.new" && mv "$main.new" "$main"
	# 测试文件里写一行 “// touch: true”：打开触屏模式（和 tools/export/build.sh 打手机包时的改法相同）
	if grep -q '^// touch: true' "$suite"; then
		sed -i.bak 's/^\(\ttouchUI *= *\)false/\1true/' "$main" && rm -f "$main.bak"
		grep -q 'touchUI *= *true' "$main" || { echo "FAIL  ${name}  没能打开触屏模式（main.spx 里的 touchUI）"; failed="${failed} ${name}"; continue; }
	fi
	{ printf '\n// ---- 测试：%s ----\n' "${name}"; cat "$suite"; } >> "$main"

	# 地图编辑器的存档写到 os.UserConfigDir()，指向临时目录，不碰玩家自己的存档
	log="$dir/run.log"
	(cd "$dir/TankBattle" && HOME="$dir/home" XDG_CONFIG_HOME="$dir/home/.config" APPDATA="$dir/home/AppData" \
		exec spx run -headless . > "${log}" 2>&1) &
	pid=$!
	# 测试文件里可以写一行 “// timeout: 秒数” 改这一组的超时（例如路演演示要跑一分多钟）
	limit=$(sed -n 's,^// timeout: *\([0-9][0-9]*\).*,\1,p' "$suite" | head -1)
	limit=${limit:-$TIMEOUT}
	secs=0
	while kill -0 $pid 2>/dev/null && [ ${secs} -lt "${limit}" ]; do sleep 1; secs=$((secs + 1)); done
	timedout=0
	if kill -0 $pid 2>/dev/null; then
		timedout=1
		pkill -P $pid 2>/dev/null || true
		kill $pid 2>/dev/null || true
	fi
	wait $pid 2>/dev/null || true

	pass=$(grep -a -c '^TEST PASS' "${log}" || true)
	fail=$(grep -a -c '^TEST FAIL' "${log}" || true)
	xfail=$(grep -a -c '^TEST XFAIL' "${log}" || true)
	xpass=$(grep -a -c '^TEST XPASS' "${log}" || true)
	total_xfail=$((total_xfail + xfail))
	grep -a '^TEST XFAIL' "${log}" | sed "s/^TEST XFAIL /  ${name}: /" >> "$WORK/xfail.txt" || true
	total_pass=$((total_pass + pass))
	total_fail=$((total_fail + fail))
	why=""
	[ "${fail}" -eq 0 ] || why="${fail} 个断言失败"
	[ "${xpass}" -eq 0 ] || why="${why:+${why}；}${xpass} 个已知问题已经修好（把 tXfail 改成 tCheck）"
	grep -a -q "^TEST DONE ${name}" "${log}" || why="${why:+${why}；}没有跑完（缺少 TEST DONE）"
	[ $timedout -eq 0 ] || why="${why:+${why}；}超时（${limit} 秒）"
	! grep -a -q -E 'panic|cannot alloc method|failed to build|Engine failed: exit status' "${log}" || why="${why:+${why}；}引擎报错（编译失败或崩溃）"
	if [ -z "${why}" ]; then
		echo "ok    ${name}  pass=${pass}  (${secs}s)"
	else
		echo "FAIL  ${name}  pass=${pass} fail=${fail}  ${why}  (${secs}s，日志：${log})"
		grep -a -E '^TEST FAIL|^TEST XPASS|panic|cannot alloc method|failed to build|error' "${log}" | head -20 | sed 's/^/      /'
		failed="${failed} ${name}"
	fi
done

echo "---- 断言：通过 ${total_pass}，失败 ${total_fail}，已知问题 ${total_xfail}"
[ ! -s "$WORK/xfail.txt" ] || { echo "---- 已知问题（还没修好，不算失败）："; cat "$WORK/xfail.txt"; }
if [ -n "$COVERAGE" ]; then
	base=""
	[ ! -f "$ROOT/tests/coverage-baseline.json" ] || [ -n "${NO_BASELINE:-}" ] || base="$ROOT/tests/coverage-baseline.json"
	if ! python3 "$ROOT/tools/test/spx_coverage.py" report ${UNITTEST_LOG:+--unittest-log "$UNITTEST_LOG"} ${base:+--baseline "$base"} "$WORK"/*/run.log > "$WORK/coverage.md"; then
		failed="${failed} 覆盖率比基线退步"
	fi
	echo "---- 覆盖率报告：$WORK/coverage.md"
	sed -n '/^## 目标/,/^## 没覆盖/p' "$WORK/coverage.md" | grep '^|'
	sed -n '/^## 和基线比较/,$p' "$WORK/coverage.md"
fi
if [ -n "${failed}" ]; then
	echo "失败的测试组：${failed}"
	exit 1
fi
