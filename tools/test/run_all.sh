#!/bin/sh
# 一条命令跑完全部自动化测试：构建工具（Python）+ 引擎内测试（spx）
#
# 用法：tools/test/run_all.sh
#   PYTHON=/path/to/python  指定 Python（要跑美术生成器的测试，需要先 pip install -r tools/assets/requirements.txt，
#                           没装 fontTools 时这几项会跳过）
#   SKIP_SPX=1              只跑构建工具的测试（没装 spx 时）
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=${PYTHON:-python3}
status=0

echo "==> 构建工具测试（tests/tools）"
"$PY" -m unittest discover -s "$ROOT/tests/tools" || status=1

if [ -z "${SKIP_SPX:-}" ]; then
	echo
	echo "==> 引擎内测试（tests/spx）"
	"$ROOT/tools/test/run_spx.sh" || status=1
fi

echo
[ $status -eq 0 ] && echo "全部通过" || echo "有测试失败"
exit $status
