#!/bin/bash
# 打包坦克大战。先运行 setup_spx.sh 准备好 spx。
#
# 用法：tools/export/build.sh <desktop|web|android|ios>
#   desktop  当前系统的单文件程序（macOS 打成 .app，Windows 是 .exe，Linux 是可执行文件）
#   web      网页版 / PWA（iPhone、安卓、电脑浏览器都能玩，需要放到 HTTPS 静态服务器上）
#   android  APK（需要 ANDROID_NDK_ROOT、JDK 17、Android SDK；用调试证书签名，可以直接安装。
#            证书默认在 ~/.config/tankbattle/debug.keystore，KEYSTORE_DIR 或 GODOT_ANDROID_KEYSTORE_DEBUG_* 可以改）
#   ios      不签名的 IPA（需要 Xcode；用 AltStore / Sideloadly 等工具以自己的 Apple ID 签名后安装）
#   android 和 ios 打包前核对 spx 模板里的版本号（setup_spx.sh 写进去的）和 APP_VERSION 一致；
#   不一致时报错，设置 SPX_REPATCH=1 则自动重新运行 setup_spx.sh（build_local.sh 默认这样做）
#
# 产物放在 dist/，文件名带版本号和平台，例如 TankBattle-3.0.0-macos-arm64.zip
set -euo pipefail
source "$(dirname "$0")/env.sh"
check_go_version

target="${1:?用法：build.sh <desktop|web|android|ios>}"
G="$BUILD_DIR/$APP_NAME"
mkdir -p "$DIST_DIR"
DIST_DIR="$(cd "$DIST_DIR" && pwd)"

# 每个平台都用一份干净的游戏副本：exportweb 会把整个工程目录打进 game.zip，残留的构建产物会让包变得很大
prepare() {
  log "准备游戏副本：$G"
  rm -rf "$G"
  mkdir -p "$G"
  (cd "$ROOT/TankBattle" && tar --exclude .temp --exclude project --exclude .builds --exclude go.mod --exclude go.sum -cf - .) | (cd "$G" && tar -xf -)
  cp "$SPX_DIR/gox.mod" "$G/gox.mod"   # project main.spx / pack assets，buildlauncher 需要
  local spx_path="$SPX_DIR"
  command -v cygpath >/dev/null && spx_path="$(cygpath -m "$SPX_DIR")"  # Windows：/d/a/... → D:/a/...，Go 才认得
  cat > "$G/go.mod" <<EOF
module github.com/goplus/spxdemo

go 1.26.0

require github.com/goplus/spx/v4 v4.0.0 //xgo:class

replace github.com/goplus/spx/v4 => $spx_path
EOF
  cp "$SPX_DIR/go.sum" "$G/go.sum"
}

os_arch() {
  local os arch
  case "$(uname -s)" in
    Darwin) os=macos ;;
    Linux) os=linux ;;
    MINGW*|MSYS*|CYGWIN*) os=windows ;;
    *) os=$(uname -s | tr '[:upper:]' '[:lower:]') ;;
  esac
  case "$(uname -m)" in
    arm64|aarch64) arch=arm64 ;;
    x86_64|amd64) arch=x64 ;;
    *) arch=$(uname -m) ;;
  esac
  echo "$os-$arch"
}

readme() {  # 安装说明：INSTALL.md 里“## $1”这一节（不含标题）
  awk -v h="## $1" '$0 == h {on = 1; next} /^## / {on = 0} on' "$EXPORT_DIR/INSTALL.md"
}

build_desktop() {
  prepare
  local plat; plat=$(os_arch)
  local name="$APP_NAME-$APP_VERSION-$plat"
  local out="$BUILD_DIR/out-$plat"
  rm -rf "$out" && mkdir -p "$out"
  log "spx buildlauncher（${plat}）"
  local exe="$out/$APP_NAME"
  [ "${plat%%-*}" = windows ] && exe="$exe.exe"
  if ! (cd "$G" && spx buildlauncher --path . -o "$exe") 2>&1 | tee "$BUILD_DIR/buildlauncher.log"; then
    # spx 在 Windows 上的问题：启动器已经生成，但最后清理临时目录时要求权限是 0700，
    # 而 Windows 上 Go 报告的目录权限总是 0777，于是报 "staging directory is not private"
    if [ -f "$exe" ] && grep -q 'staging directory is not private' "$BUILD_DIR/buildlauncher.log"; then
      echo "（忽略 spx 在 Windows 上清理临时目录的权限检查，启动器已生成）"
      rm -rf "$out"/.*spx-launchpack-*
    else
      exit 1
    fi
  fi
  # 先删掉同名的旧包：7z a / zip 遇到已有的压缩包会往里追加，旧包里的文件会留在新包里
  rm -f "$DIST_DIR/$name.zip" "$DIST_DIR/$name.tar.gz"
  case "$plat" in
    macos-*)
      # 包成 .app，双击就能打开
      local app="$out/$APP_TITLE.app"
      mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
      # 真正的程序叫 TankBattle-bin，外面套一个启动脚本：关掉 Go 的异步抢占（GODEBUG=asyncpreemptoff=1）。
      # 游戏的 Go 库运行在引擎进程里，Go 用来抢占的 SIGURG 信号可能落到引擎自己的线程上，
      # 偶尔会让进程崩溃（"non-Go code set up signal handler without SA_ONSTACK flag"，CI 的冒烟测试里遇到过）
      mv "$exe" "$app/Contents/MacOS/$APP_NAME-bin"
      cat > "$app/Contents/MacOS/$APP_NAME" <<'SH'
#!/bin/sh
export GODEBUG="${GODEBUG:+$GODEBUG,}asyncpreemptoff=1"
exec "$(dirname "$0")/TankBattle-bin" "$@"
SH
      chmod +x "$app/Contents/MacOS/$APP_NAME"
      local iconset="$BUILD_DIR/icon.iconset"
      rm -rf "$iconset" && mkdir -p "$iconset"
      for s in 16 32 128 256 512; do
        sips -z $s $s "$EXPORT_DIR/icon.png" --out "$iconset/icon_${s}x${s}.png" >/dev/null
        sips -z $((s * 2)) $((s * 2)) "$EXPORT_DIR/icon.png" --out "$iconset/icon_${s}x${s}@2x.png" >/dev/null
      done
      iconutil -c icns "$iconset" -o "$app/Contents/Resources/icon.icns"
      local base="${APP_VERSION%%-*}"   # Info.plist 的版本号只能是数字（去掉 -dev.N）
      sed -e "s/@NAME@/$APP_NAME/g" -e "s/@TITLE@/$APP_TITLE/g" -e "s/@ID@/$APP_ID/g" -e "s/@VERSION@/$base/g" \
        "$EXPORT_DIR/Info.plist" > "$app/Contents/Info.plist"
      # ad-hoc 签名：Apple Silicon 上的程序必须有签名才能运行。先签真正的程序，再签整个 App
      codesign --force -s - "$app/Contents/MacOS/$APP_NAME-bin"
      codesign --force -s - "$app" 2>/dev/null || true
      readme macOS > "$out/README.txt"
      (cd "$out" && ditto -c -k --sequesterRsrc --keepParent "$APP_TITLE.app" "$DIST_DIR/$name.zip" && zip -q "$DIST_DIR/$name.zip" README.txt)
      ;;
    windows-*)
      # 说明文件用英文文件名（Windows 上 Git Bash 传给 7z 的中文文件名会乱码），加 UTF-8 BOM 让记事本认出编码
      { printf '\xEF\xBB\xBF'; readme Windows | sed 's/$/\r/'; } > "$out/README.txt"
      (cd "$out" && 7z a -tzip -bso0 "$DIST_DIR/$name.zip" "$APP_NAME.exe" README.txt)
      ;;
    *)
      readme Linux > "$out/README.txt"
      # 和 macOS 一样，用启动脚本关掉 Go 的异步抢占（见上面 macOS 部分的说明）
      mv "$exe" "$out/$APP_NAME-bin" && chmod +x "$out/$APP_NAME-bin"
      cat > "$exe" <<'SH'
#!/bin/sh
export GODEBUG="${GODEBUG:+$GODEBUG,}asyncpreemptoff=1"
exec "$(dirname "$0")/TankBattle-bin" "$@"
SH
      chmod +x "$exe"
      tar -C "$out" -czf "$DIST_DIR/$name.tar.gz" "$APP_NAME" "$APP_NAME-bin" README.txt
      ;;
  esac
}

build_web() {
  prepare
  log "spx exportweb"
  (cd "$G" && spx exportweb)
  local src="$G/project/.builds/web" out="$BUILD_DIR/web/$APP_NAME"
  rm -rf "$BUILD_DIR/web" && mkdir -p "$out"
  # 去掉 spx 的调试台页面（index.html、lab/），换成我们的外壳页面
  (cd "$src" && tar --exclude ./index.html --exclude ./lab --exclude ./keep.txt -cf - .) | (cd "$out" && tar -xf -)
  cp -R "$EXPORT_DIR/web/." "$out/"
  # Service Worker 的缓存名带版本号，新版本发布后旧缓存自动失效
  sed -i.bak "s/@VERSION@/$APP_VERSION/g" "$out/sw.js" && rm -f "$out/sw.js.bak"
  readme Web > "$BUILD_DIR/web/README.txt"
  cp "$EXPORT_DIR/serve.py" "$BUILD_DIR/web/play-local.py"
  rm -f "$DIST_DIR/$APP_NAME-$APP_VERSION-web.zip"
  (cd "$BUILD_DIR/web" && zip -q -r "$DIST_DIR/$APP_NAME-$APP_VERSION-web.zip" "$APP_NAME" README.txt play-local.py)
}

# Android / iOS 的版本号不是打包时写的：setup_spx.sh 调 patch_spx.py 把它写进 spx 源码里的模板，
# 模板再编进 spx 程序。只改 CHANGELOG / APP_VERSION 然后跑 build.sh，包里还是旧版本号（v4.0.1 的 APK 就是 4.0.0）。
# 所以打包前从 spx 程序里读出模板的版本号核对；不一致时：SPX_REPATCH=1 自动重新运行 setup_spx.sh，否则报错退出。
template_version() {  # 打印 spx 程序里模板的版本：android → "版本名 版本代码"，ios → 所有 short_version（每行一个）
  local spx_bin; spx_bin=$(command -v spx) || { echo "找不到 spx：先运行 tools/export/setup_spx.sh $target" >&2; exit 1; }
  case "$1" in
    android)
      local name code
      name=$(LC_ALL=C grep -a -o 'version/name="[^"]*"' "$spx_bin" | head -1 | sed 's/^version\/name="\(.*\)"$/\1/' || true)
      code=$(LC_ALL=C grep -a -o 'version/code=[0-9]*' "$spx_bin" | head -1 | sed 's/^version\/code=//' || true)
      echo "$name $code"
      ;;
    ios) LC_ALL=C grep -a -o 'application/short_version="[^"]*"' "$spx_bin" | sed 's/^[^"]*"\(.*\)"$/\1/' | sort -u || true ;;
  esac
}

check_template_version() {
  local info base code want got
  info=$(python3 "$EXPORT_DIR/patch_spx.py" --version-info "$APP_VERSION") || exit 1
  base=${info% *}; code=${info#* }
  case "$target" in
    android) want="$APP_VERSION $code" ;;
    ios) want="$base" ;;
  esac
  got=$(template_version "$target")
  [ "$got" = "$want" ] && { echo "spx 模板版本号：${got}（和 APP_VERSION=${APP_VERSION} 一致）"; return; }
  echo "spx 模板里的版本号是「${got:-（读不到）}」，要打的是「${want}」（APP_VERSION=${APP_VERSION}）" >&2
  if [ "${SPX_REPATCH:-}" = 1 ]; then
    log "重新给 spx 模板打补丁并安装 spx（SPX_REPATCH=1）"
    "$EXPORT_DIR/setup_spx.sh" "$target"
    hash -r
    got=$(template_version "$target")
    [ "$got" = "$want" ] && return
    echo "重新运行 setup_spx.sh 以后版本号还是「${got}」：检查 PATH 里的 spx（$(command -v spx)）是不是刚装的那个" >&2
  else
    echo "版本号是 setup_spx.sh 写进 spx 的，请先运行：APP_VERSION=$APP_VERSION tools/export/setup_spx.sh $target" >&2
    echo "（或者设置 SPX_REPATCH=1，让 build.sh 自动重新运行）" >&2
  fi
  exit 1
}

# 手机 App：打开游戏的触屏模式（右侧面板变成方向键，按住移动并自动开火）
touch_mode() {
  sed -i.bak 's/^\(\ttouchUI *= *\)false/\1true/' "$G/main.spx" && rm -f "$G/main.spx.bak"
  grep -q 'touchUI *= *true' "$G/main.spx" || { echo "没能打开触屏模式（main.spx 里的 touchUI）" >&2; exit 1; }
}

# Godot 只在第一次生成编辑器设置时从 JAVA_HOME / ANDROID_HOME 取默认值；本机以前跑过 Godot 的话，设置里的路径可能是空的，
# 也可能是已经失效的旧路径（换过 JDK），导出会报“需要有效的 Java SDK 路径”。所以每次都改成这次的 JAVA_HOME / ANDROID_HOME。
# 这会改用户自己的 Godot 设置（~/Library/Application Support/Godot 或 ~/.local/share/godot）；没有用临时 HOME，
# 因为 spx 的运行时缓存、Gradle 缓存都在 HOME 下面，换成临时目录每次都要重新下载几百 MB。
set_editor_setting() {  # 设置文件 键 值：值不一样才改，没有这个键就加在最后（[resource] 段）
  local es="$1" key="$2" val="$3" cur=""
  if grep -q "^$key = " "$es"; then
    cur="$(sed -n "s|^$key = \"\(.*\)\"\$|\1|p" "$es")"
    [ "$cur" = "$val" ] && return 0
    sed -i.bak "s|^$key = .*|$key = \"$val\"|" "$es" && rm -f "$es.bak"
  else
    printf '%s = "%s"\n' "$key" "$val" >> "$es"
  fi
  echo "Godot 编辑器设置 ${key}：\"${cur}\" → \"${val}\"（${es}）"
}

godot_android_paths() {
  local es
  for es in "$HOME/Library/Application Support/Godot/editor_settings-4.4.tres" \
            "${XDG_DATA_HOME:-$HOME/.local/share}/godot/editor_settings-4.4.tres"; do
    [ -f "$es" ] || continue
    if [ -n "${JAVA_HOME:-}" ] && [ -x "$JAVA_HOME/bin/java" ]; then
      set_editor_setting "$es" export/android/java_sdk_path "$JAVA_HOME"
    else
      echo "⚠️  没有有效的 JAVA_HOME，Godot 设置里的 java_sdk_path 保持原样：$(grep '^export/android/java_sdk_path' "$es" || echo '（没有）')" >&2
    fi
    if [ -n "${ANDROID_HOME:-}" ] && [ -d "$ANDROID_HOME" ]; then
      set_editor_setting "$es" export/android/android_sdk_path "$ANDROID_HOME"
    fi
  done
}

build_android() {
  : "${ANDROID_NDK_ROOT:?需要设置 ANDROID_NDK_ROOT（NDK r23c，23.2.8568313）}"
  check_template_version
  prepare
  # 调试证书：Godot 从环境变量读取（GODOT_ANDROID_KEYSTORE_DEBUG_PATH / _USER / _PASSWORD，设置了就用设置的）。
  # 没设置时用仓库外固定位置的证书 $KEYSTORE_DIR/debug.keystore（默认 ~/.config/tankbattle/），没有就生成一个。
  # 证书必须每次都一样，玩家才能覆盖安装新版本；以前放在 .build/cache/ 里，删掉 .build 就换了证书。
  # 这个文件不要提交到仓库（.gitignore 已忽略 *.keystore），换电脑打包时自己拷过去。
  if [ -z "${GODOT_ANDROID_KEYSTORE_DEBUG_PATH:-}" ]; then
    local dir="${KEYSTORE_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/tankbattle}"
    export GODOT_ANDROID_KEYSTORE_DEBUG_PATH="$dir/debug.keystore"
    export GODOT_ANDROID_KEYSTORE_DEBUG_USER="androiddebugkey"
    export GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD="android"
    if [ ! -f "$GODOT_ANDROID_KEYSTORE_DEBUG_PATH" ]; then
      mkdir -p "$dir" && chmod 700 "$dir"
      if [ -f "$CACHE_DIR/debug.keystore" ]; then
        # 旧位置的证书（v4.0.1 的 APK 就是用它签的）：搬过来继续用，从 v4.0.1 升级不用卸载
        log "调试证书从 $CACHE_DIR 搬到 $dir"
        cp "$CACHE_DIR/debug.keystore" "$GODOT_ANDROID_KEYSTORE_DEBUG_PATH"
      else
        log "生成调试证书：${GODOT_ANDROID_KEYSTORE_DEBUG_PATH}（备份好它，换了证书玩家就得先卸载旧版）"
        keytool -genkeypair -v -keystore "$GODOT_ANDROID_KEYSTORE_DEBUG_PATH" -storepass android -keypass android \
          -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1
      fi
      chmod 600 "$GODOT_ANDROID_KEYSTORE_DEBUG_PATH"
    fi
    echo "调试证书：$GODOT_ANDROID_KEYSTORE_DEBUG_PATH"
  fi
  godot_android_paths
  touch_mode
  log "spx exportapk"
  (cd "$G" && spx exportapk)
  cp "$G/project/.builds/android/game.apk" "$DIST_DIR/$APP_NAME-$APP_VERSION-android.apk"
}

build_ios() {
  check_template_version
  prepare
  touch_mode
  log "spx exportios（只导出 Xcode 工程）"
  (cd "$G" && spx exportios)
  local proj; proj=$(find "$G/project/.builds/ios" -maxdepth 1 -name '*.xcodeproj' | head -1)
  [ -n "$proj" ] || { echo "没有找到导出的 Xcode 工程" >&2; exit 1; }
  local scheme; scheme=$(basename "$proj" .xcodeproj)
  # Xcode 工程引用的 MoltenVK.xcframework：用 Khronos 发布的静态版本
  local ios_dir; ios_dir=$(dirname "$proj")
  if grep -q MoltenVK "$proj/project.pbxproj" && [ ! -d "$ios_dir/MoltenVK.xcframework" ]; then
    local tarball="$CACHE_DIR/MoltenVK-ios-$MOLTENVK_VERSION.tar"
    if [ ! -f "$tarball" ]; then
      log "下载 MoltenVK $MOLTENVK_VERSION"
      curl -fsSL -o "$tarball.tmp" "https://github.com/KhronosGroup/MoltenVK/releases/download/$MOLTENVK_VERSION/MoltenVK-ios.tar"
      verify_sha256 "$tarball.tmp" "$MOLTENVK_SHA256" || { rm -f "$tarball.tmp"; exit 1; }
      mv "$tarball.tmp" "$tarball"
    else
      # 以前下载的（那时还不核对）也核对一次：不对就删掉，下次重新下载
      verify_sha256 "$tarball" "$MOLTENVK_SHA256" || { rm -f "$tarball"; echo "已删除缓存的 MoltenVK，重新运行会重新下载" >&2; exit 1; }
    fi
    rm -rf "$BUILD_DIR/moltenvk" && mkdir -p "$BUILD_DIR/moltenvk"
    tar -xf "$tarball" -C "$BUILD_DIR/moltenvk" MoltenVK/MoltenVK/static/MoltenVK.xcframework
    cp -R "$BUILD_DIR/moltenvk/MoltenVK/MoltenVK/static/MoltenVK.xcframework" "$ios_dir/"
  fi
  log "xcodebuild（不签名）：$scheme"
  local dd="$BUILD_DIR/ios-derived"
  rm -rf "$dd"
  xcodebuild -project "$proj" -scheme "$scheme" -configuration Release -sdk iphoneos -derivedDataPath "$dd" \
    CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY="" DEVELOPMENT_TEAM="" build | tail -20
  local app; app=$(find "$dd/Build/Products" -maxdepth 2 -name '*.app' -type d | head -1)
  [ -n "$app" ] || { echo "xcodebuild 没有产出 .app" >&2; exit 1; }
  local pay="$BUILD_DIR/ios-ipa"
  rm -rf "$pay" && mkdir -p "$pay/Payload"
  cp -R "$app" "$pay/Payload/"
  rm -f "$DIST_DIR/$APP_NAME-$APP_VERSION-ios-unsigned.ipa"
  (cd "$pay" && zip -q -r "$DIST_DIR/$APP_NAME-$APP_VERSION-ios-unsigned.ipa" Payload)
}

case "$target" in
  desktop) build_desktop ;;
  web) build_web ;;
  android) build_android ;;
  ios) build_ios ;;
  *) echo "未知平台：$target" >&2; exit 1 ;;
esac
log "完成，产物："
ls -la "$DIST_DIR"
