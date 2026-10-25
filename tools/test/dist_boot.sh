#!/bin/bash
# 直接启动 dist/ 里要发出去的那个安装包，确认它能运行（B14）。
#
# 用法：tools/test/dist_boot.sh <安装包> [秒数]      秒数默认 20（DIST_BOOT_SECS）
#   支持 macOS 的 .zip（里面是 .app）和 Linux 的 .tar.gz。解到临时目录里运行，到时间后结束它：
#   进程到时还活着、输出里没有 panic / 引擎报错，就算通过。
#
# 和 package_boot.sh 的区别：package_boot.sh 另打一个带启动测试脚本的包，能检查进入主页、开一局，
# 但发出去的不是那个包；这里运行的就是发出去的包本身（不带测试脚本，只能看它能不能起来、会不会崩）。
# 会弹出游戏窗口（macOS），结束时只结束这次启动的进程。
set -euo pipefail
pkg="${1:?用法：dist_boot.sh <安装包> [秒数]}"
SECS=${2:-${DIST_BOOT_SECS:-20}}
[ -f "$pkg" ] || { echo "没有这个文件：$pkg" >&2; exit 1; }
pkg="$(cd "$(dirname "$pkg")" && pwd)/$(basename "$pkg")"
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
REPO_ID=$(printf '%s' "$ROOT" | cksum | cut -d' ' -f1)
WORK=$(mktemp -d "${TMPDIR:-/tmp}/tankbattle-distboot-$REPO_ID.XXXXXX")
pid=""

kill_tree() {  # 结束一个进程和它的所有子进程（先子后父）
  local c
  for c in $(pgrep -P "$1" 2>/dev/null); do kill_tree "$c"; done
  kill "$1" 2>/dev/null || true
}
cleanup() {
  [ -z "$pid" ] || kill_tree "$pid"
  rm -rf "$WORK"
}
trap cleanup EXIT

case "$pkg" in
  *.zip) (cd "$WORK" && unzip -q "$pkg") ;;
  *.tar.gz) tar -xzf "$pkg" -C "$WORK" ;;
  *) echo "不认识的安装包：$(basename "$pkg")（支持 .zip / .tar.gz）" >&2; exit 1 ;;
esac
exe=$(find "$WORK" -path '*.app/Contents/MacOS/TankBattle' -type f | head -1)
[ -n "$exe" ] || exe=$(find "$WORK" -maxdepth 2 -name TankBattle -type f -perm -u+x | head -1)
[ -n "$exe" ] || { echo "安装包里没有找到程序"; find "$WORK" -maxdepth 3 | head; exit 1; }

log="$WORK/run.log"
echo "==> 启动 $(basename "$pkg")（${SECS} 秒）"
"$exe" > "$log" 2>&1 &
pid=$!
secs=0
while kill -0 "$pid" 2>/dev/null && [ "$secs" -lt "$SECS" ]; do sleep 1; secs=$((secs + 1)); done
alive=0
kill -0 "$pid" 2>/dev/null && alive=1
kill_tree "$pid"
wait "$pid" 2>/dev/null || true
pid=""

bad=$(grep -a -E 'panic|cannot alloc method|SIGSEGV|fatal error|Engine failed' "$log" | head -5 || true)
if [ $alive -eq 1 ] && [ -z "$bad" ]; then
  echo "B14 通过：$(basename "$pkg") 运行 ${SECS} 秒没有退出，输出里没有 panic"
else
  [ $alive -eq 1 ] || echo "B14 失败：程序 ${secs} 秒就退出了"
  [ -z "$bad" ] || { echo "B14 失败：输出里有错误"; echo "$bad" | sed 's/^/    /'; }
  echo "---- 输出的最后 30 行"
  tail -30 "$log"
  exit 1
fi
