#!/bin/sh
# 在仓库根目录建 Python 虚拟环境 .venv，装上 tools/assets/requirements.txt 里锁定版本的 fontTools 等
# （系统 Python 没有 fontTools 时，生成素材的检查和 T05~T07 会被跳过）。
#
# 用法：tools/dev/venv.sh            建好或更新 .venv（可以重复运行）
#   PYTHON=/path/to/python3          用指定的 Python 建（默认 python3，要 3.9 以上）
# 建好以后 tools/test/pr_check.sh、tools/test/run_all.sh 不设 PYTHON 时自动用 .venv/bin/python。
# .venv 已在 .gitignore 里；不要了直接删掉这个目录。
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=${PYTHON:-python3}
VENV="$ROOT/.venv"
if [ ! -x "$VENV/bin/python" ]; then
    echo "==> 建虚拟环境：${VENV}（$("$PY" --version 2>&1)）"
    "$PY" -m venv "$VENV"
fi
echo "==> 安装 tools/assets/requirements.txt"
"$VENV/bin/python" -m pip install -q --disable-pip-version-check -r "$ROOT/tools/assets/requirements.txt"
"$VENV/bin/python" -c 'import fontTools, brotli; print("fontTools", fontTools.version, "· brotli", brotli.__version__)'
echo "好了：$VENV/bin/python"
