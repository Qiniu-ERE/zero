#!/bin/sh
# 用 Chrome 无头模式把 v6 效果图（先运行 gen_v6.py 生成 SVG）导出为 PNG
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
render() { "$CHROME" --headless --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --window-size="$2" --screenshot="$PWD/${1%.svg}.png" "file://$PWD/$1" 2>/dev/null; }
for f in v6-*.svg; do render "$f" 1440,1080; done
ls -la v6-*.png
