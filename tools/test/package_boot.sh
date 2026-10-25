#!/bin/bash
# 安装包启动测试（B03，见 docs/v4/TEST_PLAN.md）：打出当前系统的桌面安装包，运行它，确认能启动、进入主页、开一局
#
# 用法：tools/test/package_boot.sh        （先运行过 tools/export/setup_spx.sh）
#
# 做法：把 tools/ 和 TankBattle/ 复制到临时目录，在副本的游戏里加上启动测试 tests/spx/boot.spx（B01、B02），
# 用同一个 tools/export/build.sh desktop 打包（macOS 是 .app，Linux 是单文件程序），解开安装包，运行里面的程序，
# 读它打印的 TEST 结果。测的是真正打出来的程序，不是 spx run。仓库和 dist/ 都不会被改动。
# 本机只能测本机系统的包；Windows / Linux 包在对应系统上运行同一个脚本。
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TIMEOUT=${TEST_TIMEOUT:-120}
WORK=$(mktemp -d "${TMPDIR:-/tmp}/tankbattle-package.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

echo "==> 准备带启动测试的工程副本"
mkdir -p "$WORK/repo"
cp -R "$ROOT/tools" "$ROOT/TankBattle" "$WORK/repo/"
rm -rf "$WORK/repo/TankBattle/.temp"
main="$WORK/repo/TankBattle/main.spx"
awk -v prelude="$ROOT/tools/test/prelude.spx" '
	!done && /^func / { while ((getline line < prelude) > 0) print line; done = 1 }
	{ print }
' "$main" > "$main.new" && mv "$main.new" "$main"
{ printf '\n// ---- 测试：boot（安装包启动测试）----\n'; cat "$ROOT/tests/spx/boot.spx"; } >> "$main"

echo "==> 打包（tools/export/build.sh desktop）"
export CACHE_DIR="${CACHE_DIR:-$ROOT/.build/cache}"   # 用已经准备好的 spx 源码（setup_spx.sh）
export BUILD_DIR="$WORK/build" DIST_DIR="$WORK/dist" APP_VERSION="${APP_VERSION:-boot-test}"
"$WORK/repo/tools/export/build.sh" desktop > "$WORK/build.log" 2>&1 || { tail -30 "$WORK/build.log"; echo "打包失败"; exit 1; }
pkg=$(ls "$DIST_DIR"/TankBattle-* | head -1)
echo "    安装包：$(basename "$pkg")（$(du -h "$pkg" | cut -f1)）"

echo "==> 解开安装包并运行"
mkdir -p "$WORK/install"
case "$pkg" in
	*.zip) (cd "$WORK/install" && unzip -q "$pkg") ;;
	*.tar.gz) tar -xzf "$pkg" -C "$WORK/install" ;;
esac
exe=$(find "$WORK/install" -path '*.app/Contents/MacOS/TankBattle' -o -name TankBattle -type f -perm -u+x | head -1)
[ -n "$exe" ] || { echo "安装包里没有找到程序"; find "$WORK/install" | head; exit 1; }
log="$WORK/run.log"
"$exe" > "$log" 2>&1 &
pid=$!
secs=0
while kill -0 $pid 2>/dev/null && [ $secs -lt "$TIMEOUT" ]; do sleep 1; secs=$((secs + 1)); done
if kill -0 $pid 2>/dev/null; then pkill -P $pid 2>/dev/null || true; kill $pid 2>/dev/null || true; fi
wait $pid 2>/dev/null || true

pass=$(grep -a -c '^TEST PASS' "$log" || true)
fail=$(grep -a -c '^TEST FAIL' "$log" || true)
grep -a -E '^TEST' "$log" | sed 's/^/    /'
if [ "$fail" -eq 0 ] && [ "$pass" -gt 0 ] && grep -a -q '^TEST DONE boot' "$log" && ! grep -a -q -E 'panic|cannot alloc method' "$log"; then
	echo "B03 通过：安装包 $(basename "$pkg") 能启动、进入主页、开一局（${pass} 个断言，${secs}s）"
else
	echo "B03 失败：通过 ${pass}、失败 ${fail}（${secs}s）"
	tail -30 "$log"
	exit 1
fi
