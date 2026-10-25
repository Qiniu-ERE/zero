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
# 默认版本号：CHANGELOG.md 里最新的一节（"## v3.0.1" → 3.0.1，"## v4.0.1-rc.1" → 4.0.1-rc.1，标题后面的文字不算）；
# CI 打标签发布时会传入标签上的版本。tests/tools/test_release_tools.py 测这一行
changelog_version() {
  LC_ALL=C awk 'match($0, /^## v[0-9][0-9A-Za-z.+-]*/) { print substr($0, 5, RLENGTH - 4); exit }' "$1"
}
APP_VERSION="${APP_VERSION:-$(changelog_version "$ROOT/CHANGELOG.md")}"

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
# MoltenVK-ios.tar 的 sha256（GitHub 上这个旧版本的附件没有 digest，是下载后算的，2026-10-25）
MOLTENVK_SHA256="8cff295513dea3ec754d3662070404d2db54b66f110d5fda1e51f9ed5023c9e1"

# Go：和 spx 的 runtime.lock.json、.github/workflows/*.yml 一致。本机装的 Go 版本不一样时打包前给出提醒，
# GO_STRICT=1 时直接报错（CI 和正式发布建议打开）。linux_vm.sh 在虚拟机里装的就是这个版本，下载后核对 sha256
GO_VERSION="1.26.5"
GO_LINUX_AMD64_SHA256="5c2c3b16caefa1d968a94c1daca04a7ca301a496d9b086e17ad77bb81393f053"  # https://go.dev/dl/?mode=json&include=all

# 注意：spx 运行时和 Godot 导出模板由 spx 的 buildctl 下载（setup_spx.sh），校验在 spx 那边，这里管不到

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

patches_digest() {  # tools/export/patches/*.patch 的文件名和内容的校验和（没有补丁时是 none）
  local p found=""
  for p in "$EXPORT_DIR"/patches/*.patch; do
    [ -f "$p" ] || continue
    found=1
    basename "$p"
    cat "$p"
  done > "${TMPDIR:-/tmp}/tankbattle-patches.$$"
  if [ -n "$found" ]; then
    sha256_of "${TMPDIR:-/tmp}/tankbattle-patches.$$"
  else
    echo none
  fi
  rm -f "${TMPDIR:-/tmp}/tankbattle-patches.$$"
}

check_spx_patches() {  # 装好的 spx 打过的源码补丁和现在的 patches/ 一致（没有记录时当成没打过补丁）
  local want got
  want="$(patches_digest)"
  got="$(cat "$SPX_DIR/.bin/tankbattle-patches.txt" 2>/dev/null || echo none)"
  [ "$want" = "$got" ] && return 0
  echo "tools/export/patches/ 里的 spx 源码补丁和装好的 spx 不一致（补丁改过，或者 spx 是在加补丁之前装的）：" >&2
  echo "先重新运行 tools/export/setup_spx.sh" >&2
  return 1
}

verify_sha256() {  # 文件 期望的 sha256：不一致时打印两个值并返回 1
  local got; got="$(sha256_of "$1")"
  [ "$got" = "$2" ] && return 0
  echo "sha256 不对：$1" >&2
  echo "  应该是 $2" >&2
  echo "  实际是 $got" >&2
  return 1
}

check_go_version() {  # 本机 go version 和 GO_VERSION 比较：不一样就提醒，GO_STRICT=1 时返回 1
  local got
  got="$(go version 2>/dev/null | awk '{print $3}')"
  got="${got#go}"
  [ "$got" = "$GO_VERSION" ] && return 0
  local msg="本机 Go 是 ${got:-（没装）}，打包环境锁定的是 ${GO_VERSION}（和 CI、spx 的 runtime.lock.json 一致），打出来的包可能和 CI 的不完全一样"
  if [ "${GO_STRICT:-}" = 1 ]; then
    echo "❌ ${msg}。GO_STRICT=1：停止" >&2
    return 1
  fi
  echo "⚠️  ${msg}（GO_STRICT=1 时会报错）" >&2
}

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
