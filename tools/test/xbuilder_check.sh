#!/bin/bash
# XBuilder 兼容检查（T09，见 docs/v4/TEST_PLAN.md）：用 XBuilder 线上的 spx v3.3.0 编译检查游戏代码
#
# 用法：tools/test/xbuilder_check.sh [工程目录，默认 TankBattle]
#
# 为什么要有：XBuilder 网页版（x.qiniu.com）用的是 spx v3.3.0，本地 spx run 和安装包用的是 spx 4.0，
# 两个版本的接口有差别（例如 rand(整数, 整数) 在 v3.3.0 返回 float64，见 PR #18）。本地测试全过，
# 导入 XBuilder 仍可能编译失败。这里用 v3.3.0 和它对应的 xgo 把 .spx 生成 Go 代码，生成时会做完整的类型检查。
#
# 做法：复制工程到临时目录，写一个依赖 spx v3.3.0 的 go.mod（//xgo:class 让 xgo 把 .spx 交给 spx 处理），
# 运行 xgo go。只读仓库，不改任何文件。第一次运行要下载 spx v3.3.0 和 xgo（Go 模块缓存），之后很快。
# 需要 Go（1.25 以上）。成功退出 0；有编译错误时打印错误并退出 1。
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
SRC=${1:-$ROOT/TankBattle}
SPX_VERSION=v3.3.0                                     # XBuilder 线上的 spx（goplus/builder 的 tools/ispx）
XGO_VERSION=v1.7.6-0.20260818050008-fd36b6192e30       # spx v3.3.0 的 go.mod 里用的 xgo

WORK=$(mktemp -d "${TMPDIR:-/tmp}/tankbattle-xbuilder.XXXXXX")
trap 'rm -rf "$WORK"' EXIT
cp "$SRC"/*.spx "$WORK"/
printf 'module tankbattle\n\ngo 1.25.0\n\nrequire github.com/goplus/spx/v3 %s //xgo:class\n' "$SPX_VERSION" > "$WORK/go.mod"

export XGOROOT
XGOROOT=$(cd "$WORK" && GOFLAGS=-mod=mod go mod download -json "github.com/goplus/xgo@$XGO_VERSION" | sed -n 's/^[[:space:]]*"Dir": "\(.*\)",$/\1/p')
cd "$WORK"
if GOFLAGS=-mod=mod go run "github.com/goplus/xgo/cmd/xgo@$XGO_VERSION" go . > "$WORK/out.log" 2>&1 && [ -f xgo_autogen.go ]; then
	echo "XBuilder 兼容检查通过：spx $SPX_VERSION 能编译 $(ls "$SRC"/*.spx | wc -l | tr -d ' ') 个 .spx 文件"
else
	echo "XBuilder 兼容检查失败：spx $SPX_VERSION 编译不过（导入 XBuilder 会报同样的错）"
	grep -E '\.spx:[0-9]+:[0-9]+:' "$WORK/out.log" || tail -20 "$WORK/out.log"
	exit 1
fi
