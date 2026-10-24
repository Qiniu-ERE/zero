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
APP_VERSION="${APP_VERSION:-3.0.0}"

CACHE_DIR="${CACHE_DIR:-$ROOT/.build/cache}"
SPX_DIR="${SPX_DIR:-$CACHE_DIR/spx}"
BUILD_DIR="${BUILD_DIR:-$ROOT/.build/work}"
DIST_DIR="${DIST_DIR:-$ROOT/dist}"

# xgo 命令行要知道自己的源码在哪（XGOROOT），否则 spx 调用它生成代码时会 panic
export XGOROOT="${XGOROOT:-$(go env GOMODCACHE)/github.com/goplus/xgo@$XGO_VERSION}"
export PATH="$(go env GOPATH)/bin:$PATH"

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
