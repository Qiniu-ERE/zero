#!/bin/sh
# 把 TankBattle/ 打包成可以导入 XBuilder 的 TankBattle.xbp（zip，文件在包的根目录）
set -e
cd "$(dirname "$0")/.."
rm -f TankBattle.xbp
(cd TankBattle && zip -q -r -X ../TankBattle.xbp . -x '.temp/*' -x '*.DS_Store')
unzip -l TankBattle.xbp | tail -1
