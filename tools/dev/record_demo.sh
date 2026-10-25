#!/bin/sh
# 录制路演演示视频（macOS / Linux，需要 spx 和 ffmpeg）
#
# 做法：复制一份工程，追加“自动开始演示、结束后退出”的脚本（不改仓库里的游戏），
# 用 spx run --movie 录制，再用 ffmpeg 转成 docs/demo/tankbattle-v3-demo.mp4。
#
# 为什么要拉伸时间：spx 的录像器按实际渲染出的帧写视频、每帧记 1/30 秒，
# 但游戏逻辑按真实时间以 60 Hz 运行。机器渲染不到 30 帧/秒时视频会被“快进”。
# 所以这里统计游戏逻辑的真实时长（60 帧 = 1 秒），再把视频等比例拉伸回真实时长。
# 录像器的音频同样被压缩，所以成品不带声音（路演时现场讲解）。
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
WORK=${TMPDIR:-/tmp}/tankbattle-record
rm -rf "$WORK" && mkdir -p "$WORK" && cp -R "$ROOT/TankBattle" "$WORK/"
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
ffmpeg -v error -y -i "$IN" -an -vf "setpts=PTS*$F,fps=30,format=yuv420p" -c:v libx264 -preset slow -crf 23 -movflags +faststart "$ROOT/docs/demo/tankbattle-v3-demo.mp4"
ffmpeg -v error -y -ss 54 -t 30 -i "$ROOT/docs/demo/tankbattle-v3-demo.mp4" -vf "fps=8,scale=420:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" "$ROOT/docs/demo/tankbattle-v3.gif"
ls -la "$ROOT/docs/demo"
