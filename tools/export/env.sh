# 打包用的公共配置（被其他脚本 source）。版本都锁死，保证本地和 CI 打出来的包一致。
#
# spx 4.0.0 刚发布：运行时（runtime-v4.0.0）已发布，但 Go 模块的 v4.0.0 tag 还没有，
# 所以从固定的 spx 提交编译安装 spx，游戏的 go.mod 用 replace 指向这份源码。

EXPORT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$EXPORT_DIR/../.." && pwd)"

SPX_REPO="https://github.com/goplus/spx.git"
SPX_COMMIT="c3c0da57ee7ffd2e15b55721785bb0641583a058"  # 2026-10-24，runtime 4.0.0
XGO_VERSION="v1.7.5"                                   # 和 spx 的 runtime.lock.json 一致

APP_NAME="TankBattle"
APP_TITLE="坦克大战 2026"
APP_ID="com.qiniu.tankbattle"
# 默认版本号：CHANGELOG.md 里最新的一节（"## v3.0.1" → 3.0.1）；CI 打标签发布时会传入标签上的版本
APP_VERSION="${APP_VERSION:-$(LC_ALL=C sed -n 's/^## v\([0-9][0-9.]*\)$/\1/p' "$ROOT/CHANGELOG.md" | head -1)}"

CACHE_DIR="${CACHE_DIR:-$ROOT/.build/cache}"
SPX_DIR="${SPX_DIR:-$CACHE_DIR/spx}"
BUILD_DIR="${BUILD_DIR:-$ROOT/.build/work}"
DIST_DIR="${DIST_DIR:-$ROOT/dist}"

# 用 go install 装的 xgo 要知道自己的源码在哪（XGOROOT），否则 spx 调用它生成代码时会 panic。
# CI 里用 goplus/setup-xgo 安装的 xgo 自己知道，这时不要设置（指向不存在的目录同样会 panic）
if [ -z "${XGOROOT:-}" ] && [ -d "$(go env GOMODCACHE)/github.com/goplus/xgo@$XGO_VERSION" ]; then
  export XGOROOT="$(go env GOMODCACHE)/github.com/goplus/xgo@$XGO_VERSION"
fi
export PATH="$(go env GOPATH)/bin:$PATH"

# Windows 上 Python 默认用系统编码（cp1252）输出，打印中文会报错
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

# iOS 模板的 Xcode 工程引用了 MoltenVK.xcframework（Vulkan 在 iOS 上的实现），导出模板里没有，要另外下载
MOLTENVK_VERSION="v1.3.0"  # 2025-05，和 spx 用的 Godot 4.4.1 时间最接近

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
