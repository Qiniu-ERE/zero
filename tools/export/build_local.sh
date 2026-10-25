#!/bin/bash
# 本地打全部能打的平台（不用 GitHub Actions），每个包打完都做检查；打不了的平台空着，写明原因。
#
# 用法：tools/export/build_local.sh [平台...]     默认：macos web android linux windows ios
#   产物放在 dist/（DIST_DIR），版本号默认取 CHANGELOG.md 的第一节（APP_VERSION 可以指定）。
#   打完以后：git tag vX.Y.Z && git push origin vX.Y.Z，再运行 tools/export/release_local.sh 发布；
#   空着的平台，release_local.sh 会在说明里改成指向上一个版本的下载链接。
#   打包前先删掉 dist/ 里这次要打的平台的同版本旧包；结果表 dist/BUILD_LOCAL.md 记下完整的提交号和工作区是否干净，
#   release_local.sh 发布前核对它等于标签的提交、表里没有 ❌。只打一部分平台时，同一个提交上次打的其余平台的结果会保留。
#
# 各平台怎么打（在一台 Apple 芯片 Mac 上，见 docs/v3/CROSS_PLATFORM.md「本机打包」）：
#   macos    本机 buildlauncher → .app，再用 tools/test/package_boot.sh 运行安装包里的程序做启动测试
#   web      本机 exportweb + 网页外壳，检查包里有游戏、外壳和 PWA 文件
#   android  本机 exportapk（JDK 17：有 JAVA_HOME 就用，没有就用 nix 临时提供；Android SDK / NDK r23c），apksigner 验证签名
#   linux    OrbStack 的 x86_64 Ubuntu 虚拟机（tools/export/linux_vm.sh，第一次先 setup），虚拟机里做启动测试
#   windows  需要 Windows 环境（buildlauncher 只能打本机平台）：暂时空着
#   ios      需要 Xcode：暂时空着
set -uo pipefail
source "$(dirname "$0")/env.sh"
[ $# -gt 0 ] || set -- macos web android linux windows ios
mkdir -p "$DIST_DIR"
SDK=${ANDROID_HOME:-$HOME/Library/Android/sdk}
NDK=${ANDROID_NDK_ROOT:-$SDK/ndk/23.2.8568313}
LOGS=$(mktemp -d "${TMPDIR:-/tmp}/tankbattle-build-local.XXXXXX")
# Android / iOS 的版本号编在 spx 里：和 APP_VERSION 不一致时让 build.sh 自动重新运行 setup_spx.sh（见 build.sh 的 check_template_version）
export SPX_REPATCH=${SPX_REPATCH:-1}
# 记下打包用的提交和工作区是否干净（写进 dist/BUILD_LOCAL.md，release_local.sh 发布前核对）
COMMIT=$(git -C "$ROOT" rev-parse HEAD)
DIRTY=0
[ -z "$(git -C "$ROOT" status --porcelain)" ] || DIRTY=1
META="version=$APP_VERSION commit=$COMMIT dirty=$DIRTY"
rows=""
row() { rows="${rows}| $1 | $2 | $3 | $4 |
"; printf '%s  %-8s %s %s\n' "$2" "$1" "$3" "$4"; }
pattern() {  # 平台 → dist/ 里它的安装包的文件名（通配符只放在平台名后面：4.0.1-* 会匹配到 4.0.1-rc.1-* 的包）
	case "$1" in
	macos) echo "$APP_NAME-$APP_VERSION-macos-*" ;;
	linux) echo "$APP_NAME-$APP_VERSION-linux-*" ;;
	ios) echo "$APP_NAME-$APP_VERSION-ios-*" ;;
	web) echo "$APP_NAME-$APP_VERSION-web.zip" ;;
	android) echo "$APP_NAME-$APP_VERSION-android.apk" ;;
	esac
}
art() { local pat; pat=$(pattern "$1"); [ -n "$pat" ] && ls "$DIST_DIR"/$pat 2>/dev/null | head -1; }
size() { [ -n "$1" ] && du -h "$1" | cut -f1; }

# 先删掉这次要打的平台的同版本旧包：某个平台这次打失败或打不了时，旧包不能被当成这次的结果发出去。
# Windows 本机打不了，dist/ 里的 Windows 包是别处拷来的，不删（release_local.sh 会提醒它不在 BUILD_LOCAL.md 里）
for p in "$@"; do
	pat=$(pattern "$p")
	[ -n "$pat" ] || continue
	for old in "$DIST_DIR"/$pat; do
		[ -e "$old" ] || continue
		echo "删掉旧包：$(basename "$old")"
		rm -f "$old"
	done
done
rm -f "$DIST_DIR/SHA256SUMS.txt"   # release_local.sh 会重新生成

for p in "$@"; do
	log "$p"
	log_file="$LOGS/$p.log"
	case "$p" in
	macos)
		if [ "$(uname -s)" != Darwin ]; then row macos ⏸ — "不在 macOS 上"; continue; fi
		if "$EXPORT_DIR/build.sh" desktop > "$log_file" 2>&1 && f=$(art macos) && [ -n "$f" ]; then
			if "$ROOT/tools/test/package_boot.sh" >> "$log_file" 2>&1; then
				row macos ✅ "$(basename "$f")（$(size "$f")）" "启动测试通过（$(grep -o '[0-9]* 个断言' "$log_file" | tail -1)）"
			else
				row macos ❌ "$(basename "$f")" "启动测试失败，见 $log_file"
			fi
		else
			row macos ❌ — "打包失败，见 $log_file"
		fi
		;;
	web)
		if "$EXPORT_DIR/build.sh" web > "$log_file" 2>&1 && f=$(art web) && [ -n "$f" ]; then
			missing=""
			unzip -l "$f" > "$LOGS/web-files.txt"   # 先存下来：开着 pipefail 时 unzip | grep -q 会因为 grep 提前退出而误判
			for need in index.html play.js manifest.webmanifest sw.js game.zip runner.html; do
				grep -q -E "(/| )${need}\$" "$LOGS/web-files.txt" || missing="${missing} ${need}"
			done
			if [ -z "$missing" ]; then row web ✅ "$(basename "$f")（$(size "$f")）" "包里有游戏、外壳和 PWA 文件"
			else row web ❌ "$(basename "$f")" "包里缺少：$missing"; fi
		else
			row web ❌ — "打包失败，见 $log_file"
		fi
		;;
	android)
		if [ ! -d "$NDK" ]; then row android ⏸ — "没有 Android NDK r23c（${NDK}）"; continue; fi
		java_cmd=()
		if [ -z "${JAVA_HOME:-}" ] || [ ! -x "$JAVA_HOME/bin/java" ]; then
			if command -v nix >/dev/null; then java_cmd=(nix shell nixpkgs#jdk17 -c)
			else row android ⏸ — "没有 JDK 17（设置 JAVA_HOME，或者装 nix）"; continue; fi
		fi
		# 有 JAVA_HOME 时 java_cmd 是空数组：macOS 自带的 bash 3.2 在 set -u 下展开空数组 "${a[@]}" 会报 unbound variable，
		# 所以写成 ${a[@]+"${a[@]}"}（数组为空时什么都不展开）
		if ${java_cmd[@]+"${java_cmd[@]}"} bash -c '
			[ -n "${JAVA_HOME:-}" ] || export JAVA_HOME=$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")
			export ANDROID_HOME="'"$SDK"'" ANDROID_NDK_ROOT="'"$NDK"'"
			"'"$EXPORT_DIR"'/build.sh" android && f="'"$DIST_DIR/$APP_NAME-$APP_VERSION"'-android.apk" && [ -f "$f" ] &&
			"$(ls -d "$ANDROID_HOME"/build-tools/*/ | tail -1)apksigner" verify "$f"' > "$log_file" 2>&1 && f=$(art android) && [ -n "$f" ]; then
			# 再核对 APK 里的版本号（v4.0.1 的 APK 写的是 4.0.0：版本号在 spx 模板里，见 build.sh 的 check_template_version）
			want="$APP_VERSION $(python3 "$EXPORT_DIR/patch_spx.py" --version-info "$APP_VERSION" | cut -d' ' -f2)"
			aapt=$(ls "$SDK"/build-tools/*/aapt 2>/dev/null | tail -1)
			got=""
			if [ -n "$aapt" ]; then
				# 不看 aapt 的退出码：Godot 的 APK 会让它报一行 “android:required ... not an integer” 并返回 1，但版本信息照样输出
				"$aapt" dump badging "$f" > "$LOGS/apk-badging.txt" 2>&1
				got="$(sed -n "s/^package: .*versionCode='\([0-9]*\)' versionName='\([^']*\)'.*/\2 \1/p" "$LOGS/apk-badging.txt")"
			fi
			if [ -z "$aapt" ]; then
				row android ✅ "$(basename "$f")（$(size "$f")）" "签名验证通过（没有 aapt，没核对版本号）；本机没有模拟器，启动要在真机上手工检查"
			elif [ "$got" = "$want" ]; then
				row android ✅ "$(basename "$f")（$(size "$f")）" "签名和版本号（${got}）验证通过；本机没有模拟器，启动要在真机上手工检查"
			else
				row android ❌ "$(basename "$f")" "APK 的版本号是「${got:-读不到}」，应该是「${want}」，见 $LOGS/apk-badging.txt"
			fi
		else
			row android ❌ — "打包或签名验证失败，见 $log_file"
		fi
		;;
	linux)
		vm=${LINUX_VM:-tankbattle-linux}
		if ! command -v orb >/dev/null; then row linux ⏸ — "没有 OrbStack"; continue; fi
		if ! orb list | grep -q "^$vm "; then row linux ⏸ — "没有虚拟机 ${vm}：先运行 tools/export/linux_vm.sh setup"; continue; fi
		if "$EXPORT_DIR/linux_vm.sh" build > "$log_file" 2>&1 && f=$(art linux) && [ -n "$f" ] && grep -q 'B03 通过' "$log_file"; then
			row linux ✅ "$(basename "$f")（$(size "$f")）" "虚拟机里启动测试通过（Xvfb + 软件 Vulkan）"
		else
			row linux ❌ "$(basename "$(art linux)" 2>/dev/null)" "打包或启动测试失败，见 $log_file"
		fi
		;;
	windows)
		row windows ⏸ — "暂时空着：buildlauncher 只能打本机平台，需要 Windows 虚拟机（VMware Fusion 已装，磁盘空间不够装 Windows）"
		;;
	ios)
		if xcodebuild -version > /dev/null 2>&1; then
			if "$EXPORT_DIR/build.sh" ios > "$log_file" 2>&1 && f=$(art ios) && [ -n "$f" ]; then row ios ✅ "$(basename "$f")（$(size "$f")）" "不签名 IPA"
			else row ios ❌ — "打包失败，见 $log_file"; fi
		else
			row ios ⏸ — "暂时空着：需要 Xcode（只有命令行工具）"
		fi
		;;
	*)
		row "$p" ❌ — "不认识的平台"
		;;
	esac
done

summary="$DIST_DIR/BUILD_LOCAL.md"
# 只打了一部分平台、而上次的结果是同一个版本和提交时，保留上次其余平台的结果（release_local.sh 按这张表核对）
kept=""
if [ -f "$summary" ] && grep -qxF "<!-- build_local $META -->" "$summary"; then
	while IFS= read -r line; do
		plat=$(echo "$line" | cut -d'|' -f2 | tr -d ' ')
		case " $* " in *" $plat "*) ;; *) kept="${kept}${line}
" ;; esac
	done < <(grep -E '^\| [a-z]+ \| ' "$summary")
fi
{
	echo "### 本地打包结果（tools/export/build_local.sh）"
	echo
	echo "- 版本：${APP_VERSION}，提交：\`${COMMIT:0:10}\`$([ "$DIRTY" = 0 ] || echo '（⚠️ 工作区有未提交的改动）')，$(date '+%Y-%m-%d %H:%M')，$(uname -s) $(uname -m)"
	echo
	echo "| 平台 | 结果 | 安装包 | 说明 |"
	echo "|---|---|---|---|"
	printf '%s' "$kept"
	printf '%s' "$rows"
	echo
	# release_local.sh 读这一行，核对安装包是不是从要发布的标签打的
	echo "<!-- build_local $META -->"
	echo "✅ 打好并检查通过 · ❌ 失败 · ⏸ 本机暂时打不了（发布说明会指向上一个版本的下载）"
} > "$summary"
echo
cat "$summary"
echo
echo "日志：$LOGS"
! grep -q '| ❌ |' "$summary"
