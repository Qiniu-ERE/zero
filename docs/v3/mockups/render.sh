#!/bin/sh
# 用 Chrome 无头模式把 v3 概念示意图（SVG，引用 ../screens 下的真实截图）导出为 PNG
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
render() { "$CHROME" --headless --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --window-size="$2" --screenshot="$PWD/${1%.svg}.png" "file://$PWD/$1" 2>/dev/null; }
render phone-landscape.svg 1400,720
render phone-portrait.svg 560,1100
ls -la *.png
