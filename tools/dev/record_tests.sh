#!/bin/bash
# 录制“一条命令跑完全部测试”的演示视频（v4.0）：docs/demo/tankbattle-v4-tests.mp4
#
# 用法：tools/dev/record_tests.sh       （需要 spx、ffmpeg；PYTHON 指向装了 fontTools 的 Python 时美术测试也会跑）
#
# 做法：真实运行一次 tools/test/run_all.sh，记下每一行输出的时间；再用 ffmpeg 画成“终端”画面，
# 每一行在它真实出现的时刻出现，整体按比例加速到大约 45 秒，画面上标明实际用时和倍速。
# 不是屏幕录像（不需要录屏权限），内容就是这次运行的真实输出。
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT="$ROOT/docs/demo/tankbattle-v4-tests.mp4"
FONT="$ROOT/tools/assets/.cache/NotoSansSC-500.ttf"   # tools/assets/build.py 第一次运行时下载
[ -f "$FONT" ] || { echo "缺少字体 $FONT：先运行一次 python3 tools/assets/build.py"; exit 1; }
WORK=$(mktemp -d "${TMPDIR:-/tmp}/tankbattle-rectests.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

echo "==> 运行 tools/test/run_all.sh（约 6 分钟）"
(cd "$ROOT" && tools/test/run_all.sh 2>&1 || true) | python3 -u -c '
import sys, time
t0 = time.time()
for line in sys.stdin:
    line = line.rstrip("\n")
    if line.strip() and not line.startswith(("test_", "  ")):   # unittest 的逐条输出太多，只留汇总
        print(f"{time.time() - t0:.2f}\t{line}", flush=True)
        print(line, file=sys.stderr, flush=True)
' > "$WORK/lines.tsv"

echo "==> 生成视频"
python3 - "$WORK" "$FONT" "$OUT" <<'PY'
import os, subprocess, sys
work, font, out = sys.argv[1:4]
rows = [l.split("\t", 1) for l in open(os.path.join(work, "lines.tsv"), encoding="utf-8").read().splitlines()]
rows = [(float(t), s) for t, s in rows]
total = rows[-1][0] if rows else 1
speed = max(1, round(total / 45))           # 加速到大约 45 秒
head = ["$ tools/test/run_all.sh", ""]
screens, shown = [], []
for i, (t, s) in enumerate(rows):
    shown.append(s)
    nxt = rows[i + 1][0] if i + 1 < len(rows) else t + 4 * speed   # 最后一屏停 4 秒
    screens.append((max((nxt - t) / speed, 0.15), head + shown[-24:]))
mins, secs = divmod(int(total), 60)
note = f"坦克大战 v4.0 · 一条命令跑完全部自动化测试 · 实际用时 {mins} 分 {secs} 秒 · 视频 {speed} 倍速"
segs = []
for k, (dur, lines) in enumerate(screens):
    tf = os.path.join(work, f"s{k}.txt")
    nf = os.path.join(work, "note.txt")
    open(tf, "w", encoding="utf-8").write("\n".join(lines))
    open(nf, "w", encoding="utf-8").write(note)
    seg = os.path.join(work, f"s{k}.mp4")
    vf = (f"drawtext=fontfile={font}:textfile={tf}:fontcolor=0xE6E6E6:fontsize=22:line_spacing=6:x=40:y=70,"
          f"drawtext=fontfile={font}:textfile={nf}:fontcolor=0xE8C020:fontsize=22:x=40:y=24")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x1E1E1E:s=1280x800:r=30:d={dur:.3f}",
                    "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", seg], check=True)
    segs.append(seg)
lst = os.path.join(work, "list.txt")
open(lst, "w").write("".join(f"file '{p}'\n" for p in segs))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "26",
                "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
print(f"{out}：{len(rows)} 行输出，实际 {total:.0f} 秒，{speed} 倍速")
PY
ls -la "$OUT"
