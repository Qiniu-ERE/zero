#!/bin/bash
# 在 macOS 上用 OrbStack 的 x86_64 Ubuntu 虚拟机打 Linux 包并做启动测试（Rosetta 转译）。
#
# 用法：tools/export/linux_vm.sh setup     第一次：建虚拟机、装依赖和 Go、准备 spx（可以重复运行，已有的会跳过）
#       tools/export/linux_vm.sh build     打 Linux x64 包，放到 ${DIST_DIR}（默认 dist/），并在虚拟机里跑启动测试（B03）
#       tools/export/linux_vm.sh delete    删掉虚拟机，释放磁盘
#
# 虚拟机里能直接访问 macOS 的文件（OrbStack 把 /Users 挂在同一个路径），所以用的就是这个仓库。
# 虚拟机自己的 spx 缓存、Go 缓存放在虚拟机的 ~ 里，不和 macOS 混用。
set -euo pipefail
source "$(dirname "$0")/env.sh"
VM=${LINUX_VM:-tankbattle-linux}
GO_VERSION=${GO_VERSION:-1.26.5}   # 和 .github/workflows/release.yml、spx 的 runtime.lock.json 一致
in_vm() { orb -m "$VM" bash -lc "$*"; }
as_root() { orb -m "$VM" -u root bash -lc "$*"; }

command -v orb >/dev/null || { echo "需要 OrbStack（https://orbstack.dev）" >&2; exit 1; }

case "${1:-}" in
setup)
	if ! orb list | grep -q "^$VM "; then
		log "创建虚拟机 ${VM}（Ubuntu 24.04，x86_64）"
		orb create -a amd64 ubuntu:noble "$VM"
	fi
	log "依赖（和 release.yml 的 Linux 任务相同，再加 Xvfb 和软件 Vulkan 用于启动测试）"
	as_root "apt-get update -q && DEBIAN_FRONTEND=noninteractive apt-get install -y -q git curl ca-certificates python3 gcc make zip unzip \
		libgl1-mesa-dev libegl1-mesa-dev libgles2-mesa-dev libx11-dev xorg-dev libasound2-dev libopenal-dev \
		xvfb xauth mesa-vulkan-drivers libgl1-mesa-dri libvulkan1"
	if ! in_vm "test -x /usr/local/go/bin/go && /usr/local/go/bin/go version | grep -q go$GO_VERSION"; then
		log "Go $GO_VERSION"
		as_root "rm -rf /usr/local/go && curl -fsSL https://go.dev/dl/go$GO_VERSION.linux-amd64.tar.gz | tar -C /usr/local -xz"
	fi
	log "spx（虚拟机里的缓存：~/tankbattle-cache）"
	in_vm "export PATH=/usr/local/go/bin:\$HOME/go/bin:\$PATH CACHE_DIR=\$HOME/tankbattle-cache && cd '$ROOT' && tools/export/setup_spx.sh"
	log "虚拟机准备好了：${VM}"
	;;
build)
	mkdir -p "$DIST_DIR"
	log "打 Linux x64 包（虚拟机 ${VM}）"
	in_vm "export PATH=/usr/local/go/bin:\$HOME/go/bin:\$PATH CACHE_DIR=\$HOME/tankbattle-cache BUILD_DIR=\$HOME/tankbattle-build DIST_DIR='$DIST_DIR' APP_VERSION='$APP_VERSION' && cd '$ROOT' && tools/export/build.sh desktop"
	log "启动测试（Xvfb + 软件 Vulkan）"
	in_vm "export PATH=/usr/local/go/bin:\$HOME/go/bin:\$PATH CACHE_DIR=\$HOME/tankbattle-cache && cd '$ROOT' && xvfb-run -a -s '-screen 0 1280x960x24' tools/test/package_boot.sh"
	log "直接运行要发出去的安装包（B14，tools/test/dist_boot.sh）"
	in_vm "cd '$ROOT' && xvfb-run -a -s '-screen 0 1280x960x24' tools/test/dist_boot.sh '$DIST_DIR/$APP_NAME-$APP_VERSION-linux-x64.tar.gz' ${DIST_BOOT_SECS:-30}"
	ls -la "$DIST_DIR"/*linux* 2>/dev/null
	;;
delete)
	orb delete -f "$VM"
	;;
*)
	sed -n '2,9p' "$0"
	exit 1
	;;
esac
