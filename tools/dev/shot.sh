#!/bin/sh
# 用法：tools/dev/shot.sh <工程副本目录> <输出前缀> <秒数...>（macOS，需要 spx、ImageMagick）
# 运行游戏，在指定时间点只截取游戏窗口（不截整个屏幕），自动裁出 4:3 画面，然后结束游戏
D=$(cd "$(dirname "$0")" && pwd)
[ -x "$D/winid" ] || swiftc -O "$D/winid.swift" -o "$D/winid"
DIR="$1"; OUT="$2"; shift 2
SPX=$(command -v spx) || { echo "找不到 spx（先运行 tools/export/setup_spx.sh，或者把 \$(go env GOPATH)/bin 加进 PATH）" >&2; exit 1; }
cd "$DIR" || exit 1
"$SPX" run . > "$OUT.log" 2>&1 &
PID=$!
n=0; prev=0
for t in "$@"; do
  sleep $((t - prev)); prev=$t; n=$((n+1))
  WID=$("$D/winid" gdspxrt)
  if [ -n "$WID" ]; then screencapture -x -o -l "$WID" "$OUT-$n.png"; else echo "no game window at ${t}s"; fi
done
# 只结束这次启动的游戏：spx 的子进程（引擎 gdspxrt）和 spx 自己，不碰机器上别的游戏进程（例如另一个 clone 在跑的测试）
pkill -P $PID 2>/dev/null
kill $PID 2>/dev/null
wait $PID 2>/dev/null
for f in "$OUT"-*.png; do
  case "$f" in *-c.png) continue;; esac
  [ -f "$f" ] || continue
  W=$(magick "$f" -format '%w' info:); H=$(magick "$f" -format '%h' info:); CH=$((H-32))
  if [ $((W*3)) -gt $((CH*4)) ]; then GH=$CH; GW=$((CH*4/3)); else GW=$W; GH=$((W*3/4)); fi
  X=$(((W-GW)/2)); Y=$((32+(CH-GH)/2))
  magick "$f" -crop ${GW}x${GH}+${X}+${Y} +repage -resize 960x720 "${f%.png}-c.png"
done
grep -i -E 'cannot alloc|error|panic' "$OUT.log" | head -5
