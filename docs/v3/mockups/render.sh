#!/bin/sh
# 用 Chrome 无头模式把 v3 概念示意图（SVG，引用 ../screens 下的真实截图）导出为 PNG
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
render() { "$CHROME" --headless --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --window-size="$2" --screenshot="$PWD/${1%.svg}.png" "file://$PWD/$1" 2>/dev/null; }
render phone-landscape.svg 1400,720
render phone-portrait.svg 560,1100
ls -la *.png
# v3.0 效果图（先运行 gen_v3.py 生成 SVG）
for f in v3-*.svg; do render "$f" 1440,1080; done
ls -la v3-*.png
