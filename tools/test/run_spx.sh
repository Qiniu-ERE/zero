#!/bin/sh
# 跑引擎内测试（macOS / Linux，需要 spx）
#
# 用法：tools/test/run_spx.sh                      # 跑 tests/spx/ 下的全部测试
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
[ $# -gt 0 ] || set -- "$ROOT"/tests/spx/*.spx

rm -rf "$WORK" && mkdir -p "$WORK"
# spx 要用到 Go 的模块和编译缓存，先记下真实的位置（下面会把 HOME 换成临时目录）
GOPATH=${GOPATH:-$(go env GOPATH 2>/dev/null || echo "$HOME/go")}
GOCACHE=${GOCACHE:-$(go env GOCACHE 2>/dev/null || echo "$HOME/.cache/go-build")}
export GOPATH GOCACHE
failed=""
total_pass=0
total_fail=0
for suite in "$@"; do
	name=$(basename "$suite" .spx)
	dir="$WORK/${name}"
	mkdir -p "$dir/home"
	cp -R "$ROOT/TankBattle" "$dir/"
	main="$dir/TankBattle/main.spx"
	awk -v prelude="$ROOT/tools/test/prelude.spx" '
		!done && /^func / { while ((getline line < prelude) > 0) print line; done = 1 }
		{ print }
	' "$main" > "$main.new" && mv "$main.new" "$main"
	{ printf '\n// ---- 测试：%s ----\n' "${name}"; cat "$suite"; } >> "$main"

	# 地图编辑器的存档写到 os.UserConfigDir()，指向临时目录，不碰玩家自己的存档
	log="$dir/run.log"
	(cd "$dir/TankBattle" && HOME="$dir/home" XDG_CONFIG_HOME="$dir/home/.config" APPDATA="$dir/home/AppData" \
		exec spx run -headless . > "${log}" 2>&1) &
	pid=$!
	secs=0
	while kill -0 $pid 2>/dev/null && [ ${secs} -lt "${TIMEOUT}" ]; do sleep 1; secs=$((secs + 1)); done
	timedout=0
	if kill -0 $pid 2>/dev/null; then
		timedout=1
		pkill -P $pid 2>/dev/null || true
		kill $pid 2>/dev/null || true
	fi
	wait $pid 2>/dev/null || true

	pass=$(grep -a -c '^TEST PASS' "${log}" || true)
	fail=$(grep -a -c '^TEST FAIL' "${log}" || true)
	total_pass=$((total_pass + pass))
	total_fail=$((total_fail + fail))
	why=""
	[ "${fail}" -eq 0 ] || why="${fail} 个断言失败"
	grep -a -q "^TEST DONE ${name}" "${log}" || why="${why:+${why}；}没有跑完（缺少 TEST DONE）"
	[ $timedout -eq 0 ] || why="${why:+${why}；}超时（${TIMEOUT} 秒）"
	! grep -a -q -E 'panic|cannot alloc method' "${log}" || why="${why:+${why}；}引擎报错"
	if [ -z "${why}" ]; then
		echo "ok    ${name}  pass=${pass}  (${secs}s)"
	else
		echo "FAIL  ${name}  pass=${pass} fail=${fail}  ${why}  (日志：${log})"
		grep -a -E '^TEST FAIL|panic|cannot alloc method|error' "${log}" | head -20 | sed 's/^/      /'
		failed="${failed} ${name}"
	fi
done

echo "---- 断言：通过 ${total_pass}，失败 ${total_fail}"
if [ -n "${failed}" ]; then
	echo "失败的测试组：${failed}"
	exit 1
fi
