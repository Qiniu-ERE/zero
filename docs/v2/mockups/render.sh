#!/bin/sh
# 用 Chrome 无头模式把 SVG 效果图导出为 PNG（1440x1080，即 480x360 的 3 倍）
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for f in *.svg; do
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
    --window-size=1440,1080 --default-background-color=00000000 \
    --screenshot="$PWD/${f%.svg}.png" "file://$PWD/$f" 2>/dev/null
done
ls -la *.png
