#!/bin/bash
# 打包坦克大战。先运行 setup_spx.sh 准备好 spx。
#
# 用法：tools/export/build.sh <desktop|web|android|ios>
#   desktop  当前系统的单文件程序（macOS 打成 .app，Windows 是 .exe，Linux 是可执行文件）
#   web      网页版 / PWA（iPhone、安卓、电脑浏览器都能玩，需要放到 HTTPS 静态服务器上）
#   android  APK（需要 ANDROID_NDK_ROOT、JDK 17、Android SDK；用调试证书签名，可以直接安装）
#   ios      不签名的 IPA（需要 Xcode；用 AltStore / Sideloadly 等工具以自己的 Apple ID 签名后安装）
#
# 产物放在 dist/，文件名带版本号和平台，例如 TankBattle-3.0.0-macos-arm64.zip
set -euo pipefail
source "$(dirname "$0")/env.sh"

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
  case "$plat" in
    macos-*)
      # 包成 .app，双击就能打开
      local app="$out/$APP_TITLE.app"
      mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
      mv "$exe" "$app/Contents/MacOS/$APP_NAME"
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
      codesign --force --deep -s - "$app" 2>/dev/null || true  # ad-hoc 签名，Apple Silicon 必须有签名才能运行
      readme macOS > "$out/安装说明.txt"
      (cd "$out" && ditto -c -k --sequesterRsrc --keepParent "$APP_TITLE.app" "$DIST_DIR/$name.zip" && zip -q "$DIST_DIR/$name.zip" 安装说明.txt)
      ;;
    windows-*)
      readme Windows > "$out/安装说明.txt"
      (cd "$out" && 7z a -tzip -mcu=on -bso0 "$DIST_DIR/$name.zip" "$APP_NAME.exe" 安装说明.txt)  # -mcu=on：中文文件名用 UTF-8
      ;;
    *)
      readme Linux > "$out/安装说明.txt"
      chmod +x "$exe"
      tar -C "$out" -czf "$DIST_DIR/$name.tar.gz" "$APP_NAME" 安装说明.txt
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
  readme Web > "$BUILD_DIR/web/安装说明.txt"
  cp "$EXPORT_DIR/serve.py" "$BUILD_DIR/web/本地试玩.py"
  rm -f "$DIST_DIR/$APP_NAME-$APP_VERSION-web.zip"
  (cd "$BUILD_DIR/web" && zip -q -r "$DIST_DIR/$APP_NAME-$APP_VERSION-web.zip" "$APP_NAME" 安装说明.txt 本地试玩.py)
}

# 手机 App：打开游戏的触屏模式（右侧面板变成方向键，按住移动并自动开火）
touch_mode() {
  sed -i.bak 's/^\(\ttouchUI *= *\)false/\1true/' "$G/main.spx" && rm -f "$G/main.spx.bak"
  grep -q 'touchUI *= *true' "$G/main.spx" || { echo "没能打开触屏模式（main.spx 里的 touchUI）" >&2; exit 1; }
}

build_android() {
  : "${ANDROID_NDK_ROOT:?需要设置 ANDROID_NDK_ROOT（NDK r23c，23.2.8568313）}"
  prepare
  # 调试证书：Godot 从环境变量读取。没有就临时生成一个（每次打包都一样的话，覆盖安装不用先卸载）
  if [ -z "${GODOT_ANDROID_KEYSTORE_DEBUG_PATH:-}" ]; then
    export GODOT_ANDROID_KEYSTORE_DEBUG_PATH="$CACHE_DIR/debug.keystore"
    export GODOT_ANDROID_KEYSTORE_DEBUG_USER="androiddebugkey"
    export GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD="android"
    if [ ! -f "$GODOT_ANDROID_KEYSTORE_DEBUG_PATH" ]; then
      keytool -genkeypair -v -keystore "$GODOT_ANDROID_KEYSTORE_DEBUG_PATH" -storepass android -keypass android \
        -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1
    fi
  fi
  touch_mode
  log "spx exportapk"
  (cd "$G" && spx exportapk)
  cp "$G/project/.builds/android/game.apk" "$DIST_DIR/$APP_NAME-$APP_VERSION-android.apk"
}

build_ios() {
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
      mv "$tarball.tmp" "$tarball"
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
