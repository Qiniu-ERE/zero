#!/bin/bash
# 准备打包环境：下载固定版本的 spx 源码 → 打模板补丁 → 安装 xgo → 编译安装 spx 和运行时。
#
# 用法：tools/export/setup_spx.sh [web] [android] [ios]
#   不带参数只准备桌面版（buildlauncher）；web / android / ios 额外下载对应平台的导出模板。
#
# spx 和运行时会装进 $(go env GOPATH)/bin。本地测试时可以先 export GOPATH=/tmp/xxx，不影响自己已经装好的 spx。
set -euo pipefail
source "$(dirname "$0")/env.sh"
check_go_version

log "spx 源码 ($SPX_COMMIT)"
if [ ! -d "$SPX_DIR/.git" ]; then
  mkdir -p "$(dirname "$SPX_DIR")"
  git init -q "$SPX_DIR"
  git -C "$SPX_DIR" remote add origin "$SPX_REPO"
fi
if [ "$(git -C "$SPX_DIR" rev-parse HEAD 2>/dev/null || true)" != "$SPX_COMMIT" ]; then
  git -C "$SPX_DIR" fetch -q --depth 1 origin "$SPX_COMMIT"
fi
# 每次都先恢复成干净的源码（上次的模板补丁和源码补丁都去掉），再按顺序重新打补丁
git -C "$SPX_DIR" checkout -q -f "$SPX_COMMIT"
git -C "$SPX_DIR" clean -q -fdx -e .bin

# 源码补丁：tools/export/patches/*.patch 按文件名顺序 git apply（例如给 spx 加手柄支持，见 patches/README.md）。
# 补丁内容的校验和写进 .bin/tankbattle-patches.txt，build.sh 打包前核对，补丁改了而 spx 没重装时会报错
shopt -s nullglob
patches=("$EXPORT_DIR"/patches/*.patch)
shopt -u nullglob
for p in ${patches[@]+"${patches[@]}"}; do
  log "spx 源码补丁：$(basename "$p")"
  git -C "$SPX_DIR" apply --whitespace=nowarn "$p" || {
    echo "补丁 $(basename "$p") 打不上：spx 提交（SPX_COMMIT）变了的话，要按新源码重新生成补丁" >&2
    exit 1
  }
done

log "给 spx 模板打补丁（包名、版本、图标、iOS 不签名）"
python3 "$EXPORT_DIR/patch_spx.py" "$SPX_DIR" "$APP_ID" "$APP_TITLE" "$APP_VERSION"

log "xgo $XGO_VERSION"
# 注意：不要写成 xgo version | grep -q ...，开了 pipefail 时 grep 提前退出会让 xgo 收到 SIGPIPE（退出码 141）
xgo_ver="$(xgo version 2>/dev/null || true)"
case "$xgo_ver" in
  *"${XGO_VERSION#v}"*) ;;
  *) go install "github.com/goplus/xgo/cmd/xgo@$XGO_VERSION"; xgo_ver="$(xgo version 2>/dev/null || true)" ;;
esac
echo "${xgo_ver%%$'\n'*}"

# 直接调用 spx 的 buildctl（和 make setup 相同；Windows 的 Git Bash 里没有 make）
log "编译 buildctl"
BUILDCTL="$SPX_DIR/.bin/buildctl$(go env GOEXE)"
(cd "$SPX_DIR" && mkdir -p .bin && go build -o "$BUILDCTL" ./internal/cmd/buildctl)

log "安装 spx 和运行时（buildctl setup host --published-runtime）"
(cd "$SPX_DIR" && "$BUILDCTL" setup host --published-runtime)
patches_digest > "$SPX_DIR/.bin/tankbattle-patches.txt"   # 装好的 spx 打过哪些源码补丁（build.sh 核对）

for target in "$@"; do
  case "$target" in
    web)
      log "Web 运行时（buildctl setup web --mode normal）"
      (cd "$SPX_DIR" && "$BUILDCTL" setup web --mode normal)
      ;;
    android|ios)
      log "$target 导出模板"
      (cd "$SPX_DIR" && "$BUILDCTL" engine download --platform "$target")
      ;;
    *)
      echo "未知平台：${target}（可选 web android ios）" >&2
      exit 1
      ;;
  esac
done

log "spx 已就绪：$(command -v spx)"
spx_ver="$(spx version 2>&1 || true)"
echo "${spx_ver%%$'\n'*}"
