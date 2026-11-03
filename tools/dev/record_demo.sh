#!/bin/sh
# 录制路演演示视频（macOS / Linux，需要 spx 和 ffmpeg）
#
# 做法：复制一份工程，追加“自动开始演示、结束后退出”的脚本（不改仓库里的游戏），
# 用 spx run --movie 录制，再用 ffmpeg 转成 docs/demo/<NAME>-demo.mp4 和 <NAME>.gif。
# NAME 默认 tankbattle-v6（以前版本的视频保留不动），可以用 DEMO_NAME 环境变量改。
# 动图截视频里的一段：GIF_START（秒）起 GIF_LEN 秒，默认是 v6 那段（芯片三选一、车库、每日挑战、分享战报、排行榜、助战码）。
#
# 为什么要拉伸时间：spx 的录像器按实际渲染出的帧写视频、每帧记 1/30 秒，
# 但游戏逻辑按真实时间以 60 Hz 运行。机器渲染不到 30 帧/秒时视频会被“快进”。
# 所以这里统计游戏逻辑的真实时长（60 帧 = 1 秒），再把视频等比例拉伸回真实时长。
# 录像器的音频同样被压缩，所以成品不带声音（路演时现场讲解）。
#
# 排行榜：设了 LB_URL 就把副本的 lbURL 指向它，演示里的排行榜画面显示真实数据，例如
#   server/deploy/local.sh up && LB_URL=http://127.0.0.1:8787 tools/dev/record_demo.sh && server/deploy/local.sh down
# 不设时排行榜画面显示“排行榜服务还没上线”。
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
NAME=${DEMO_NAME:-tankbattle-v6}
GIF_START=${GIF_START:-53}
GIF_LEN=${GIF_LEN:-44}
WORK=${TMPDIR:-/tmp}/tankbattle-record
rm -rf "$WORK" && mkdir -p "$WORK" && cp -R "$ROOT/TankBattle" "$WORK/"
if [ -n "${LB_URL:-}" ]; then
  sed -E -i.bak "s|^([[:space:]]*lbURL[[:space:]]*=[[:space:]]*)\"\"|\\1\"$LB_URL\"|" "$WORK/TankBattle/main.spx" && rm -f "$WORK/TankBattle/main.spx.bak"
  grep -q "lbURL *= *\"$LB_URL\"" "$WORK/TankBattle/main.spx" || { echo "❌ 没能把 lbURL 改成 $LB_URL" >&2; exit 1; }
fi
cat >> "$WORK/TankBattle/main.spx" <<'SPX'

// ---- 录屏用：自动开始演示，统计真实时长，结束后退出以写完视频文件 ----
onStart => {
	wait 4
	broadcast "demoFlow"
}

onStart => {
	ticks := 0
	for {
		waitNextFrame
		ticks++
		if ticks%6 == 0 {
			println("GAMETIME", float64(ticks)/60)
		}
	}
}

onMsg "demoDone", => {
	wait 2.5
	exit
}
SPX
cd "$WORK/TankBattle"
spx run --movie . > "$WORK/run.log" 2>&1 || true
IN="$WORK/TankBattle/.temp/output/movie.avi_merged.avi"
REAL=$(grep -a GAMETIME "$WORK/run.log" | tail -1 | awk '{print $2}')
VID=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
F=$(echo "$REAL / $VID" | bc -l)
echo "game time ${REAL}s, video ${VID}s, stretch x$F"
mkdir -p "$ROOT/docs/demo"
ffmpeg -v error -y -i "$IN" -an -vf "setpts=PTS*$F,fps=30,format=yuv420p" -c:v libx264 -preset slow -crf 23 -movflags +faststart "$ROOT/docs/demo/$NAME-demo.mp4"
ffmpeg -v error -y -ss "$GIF_START" -t "$GIF_LEN" -i "$ROOT/docs/demo/$NAME-demo.mp4" -vf "fps=8,scale=420:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" "$ROOT/docs/demo/$NAME.gif"
ls -la "$ROOT/docs/demo"
