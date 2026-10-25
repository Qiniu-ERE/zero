#!/bin/sh
# 清理测试和打包留下的临时文件（覆盖率基线的工作目录、测试副本、打包日志、.build/work 等，常常有几个 GB）。
#
# 用法：tools/dev/clean.sh            只列出会删什么、各多大（默认不删）
#       tools/dev/clean.sh --yes      真的删
#       tools/dev/clean.sh --yes --legacy   连旧版脚本留下的、不带仓库校验和的 $TMPDIR/tankbattle-* 一起删
#                                           （分不清是哪个 clone 的，确认没有别的 clone 在跑测试再用）
#
# 只删这个仓库自己的东西：
#   $TMPDIR/tankbattle-*-<仓库路径的校验和>*   run_spx.sh、pr_check.sh、run_all.sh、update_baseline.sh、build_local.sh 的临时目录和日志
#   .build/work                                  build.sh 的工作目录（每次打包会重新生成）
# 不删（只给提示）：.build/cache（spx 源码和 MoltenVK 下载，删了要重新下载）、dist/、Go 编译缓存、OrbStack 虚拟机、
#   Android 调试证书 ~/.config/tankbattle/。
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TMP=${TMPDIR:-/tmp}
TMP=${TMP%/}
REPO_ID=$(printf '%s' "$ROOT" | cksum | cut -d' ' -f1)
YES=""
LEGACY=""
for a in "$@"; do
    case "$a" in
        --yes|-y) YES=1 ;;
        --legacy) LEGACY=1 ;;
        -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
        *) echo "不认识的参数：${a}（可选 --yes --legacy）" >&2; exit 1 ;;
    esac
done

size() { du -sh "$1" 2>/dev/null | cut -f1; }
found=0
take() {  # 列出（--yes 时删掉）一个文件或目录
    [ -e "$1" ] || return 0
    found=$((found + 1))
    if [ -n "$YES" ]; then
        printf '删除  %6s  %s\n' "$(size "$1")" "$1"
        rm -rf "$1"
    else
        printf '      %6s  %s\n' "$(size "$1")" "$1"
    fi
}

echo "==> 这个仓库的临时文件（${TMP}，仓库校验和 ${REPO_ID}）"
for f in "$TMP"/tankbattle-*-"$REPO_ID" "$TMP"/tankbattle-*-"$REPO_ID".* "$TMP"/tankbattle-*-"$REPO_ID"-* "$TMP"/pr_check-"$REPO_ID".md; do
    take "$f"
done
take "$ROOT/.build/work"

echo
echo "==> 旧版脚本留下的临时文件（不带仓库校验和，分不清是哪个 clone 的）"
legacy=0
for f in "$TMP"/tankbattle-*; do
    [ -e "$f" ] || continue
    case "$f" in *"$REPO_ID"*) continue ;; esac
    # 别的 clone 的新版临时文件：名字里有别的校验和（一串数字），不碰
    case "$(basename "$f")" in
        tankbattle-test-[0-9]*|tankbattle-prcheck-[0-9]*|tankbattle-baseline-[0-9]*|tankbattle-unittest-[0-9]*|tankbattle-build-local-[0-9]*) continue ;;
    esac
    legacy=$((legacy + 1))
    if [ -n "$LEGACY" ]; then take "$f"; else printf '      %6s  %s\n' "$(size "$f")" "$f"; fi
done
[ $legacy -eq 0 ] && echo "      （没有）"
[ $legacy -eq 0 ] || [ -n "$LEGACY" ] || echo "      加 --legacy 才会删这些"

echo
if [ $found -eq 0 ]; then
    echo "这个仓库没有可以清理的临时文件。"
elif [ -z "$YES" ]; then
    echo "以上是会删除的内容（共 $found 项）。确认后运行：tools/dev/clean.sh --yes"
else
    echo "已删除 $found 项。"
fi

echo
echo "==> 其他占空间的地方（不会自动删，需要时手动处理）"
[ -d "$ROOT/.build/cache" ] && echo "  $(size "$ROOT/.build/cache")  .build/cache：spx 源码和下载缓存，删了下次 setup_spx.sh 要重新下载"
[ -d "$ROOT/dist" ] && echo "  $(size "$ROOT/dist")  dist/：打好的安装包，发布以后可以删"
if command -v go >/dev/null 2>&1; then
    gc=$(go env GOCACHE 2>/dev/null)
    [ -n "$gc" ] && [ -d "$gc" ] && echo "  $(size "$gc")  Go 编译缓存 ${gc}：go clean -cache（下次编译会慢一些）"
fi
if command -v orb >/dev/null 2>&1 && orb list 2>/dev/null | grep -q "^${LINUX_VM:-tankbattle-linux} "; then
    echo "  OrbStack 虚拟机 ${LINUX_VM:-tankbattle-linux}（约 5 GB）：tools/export/linux_vm.sh delete（以后打 Linux 包要重新 setup）"
fi
