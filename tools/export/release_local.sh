#!/usr/bin/env bash
# 本机发布：把 dist/ 里打好的安装包发布成 GitHub Release（GitHub Actions 用不了时的替代）。
# 用法：
#   tools/export/build.sh desktop / web / android ...   先打包（每台机器只能打本机平台的桌面版）
#   git tag v3.0.2 && git push origin v3.0.2             在 main 上打标签并推送
#   tools/export/release_local.sh                        发布
# 版本号默认取 CHANGELOG.md 的第一节，也可以用 APP_VERSION=3.0.2 指定。
# dist/ 里没有的平台（比如本机打不了的 Windows、iOS），说明里会改成指向最近一个有这个平台安装包的版本
# （一个一个往前找：v3.0.2 本身也没有 Windows / iOS 包，就会找到 v3.0.1）。
# DRY_RUN=1：只打印发布说明，不创建 Release（不需要标签）。
set -euo pipefail
source "$(dirname "$0")/env.sh"

V="$APP_VERSION"
TAG="v$V"
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"

if [ -z "${DRY_RUN:-}" ]; then
  git -C "$ROOT" rev-parse -q --verify "refs/tags/$TAG" >/dev/null || { echo "没有标签 ${TAG}：先在 main 上 git tag $TAG 并推送" >&2; exit 1; }
  git -C "$ROOT" ls-remote --exit-code --tags origin "$TAG" >/dev/null || { echo "标签 $TAG 还没推送到 GitHub" >&2; exit 1; }
fi

shopt -s nullglob
files=("$DIST_DIR"/"$APP_NAME-$V-"*)
[ ${#files[@]} -gt 0 ] || { echo "dist/ 里没有 $V 的安装包，先运行 build.sh" >&2; exit 1; }

# 上一个正式版：缺的平台从这里取
# 以前的正式版（新的在前）和它们的安装包：缺的平台从最近一个有这个平台的版本取
releases="$(gh release list --exclude-drafts --exclude-pre-releases --limit 50 --json tagName -q '.[].tagName' | grep -vx "$TAG" || true)"
all_assets="$(for t in $releases; do gh release view "$t" --json assets -q '.assets[].name' | sed "s|^|$t |"; done)"

(cd "$DIST_DIR" && shasum -a 256 "$APP_NAME-$V-"* > SHA256SUMS.txt)

notes="$(mktemp)"
sed "s/@VERSION@/$V/g" "$ROOT/tools/export/RELEASE_NOTES.md" > "$notes"
for suffix in windows-x64.zip macos-arm64.zip linux-x64.tar.gz web.zip android.apk ios-unsigned.ipa; do
  [ -f "$DIST_DIR/$APP_NAME-$V-$suffix" ] && continue
  PREV=""
  for t in $releases; do
    old="$APP_NAME-${t#v}-$suffix"
    if grep -qx "$t $old" <<<"$all_assets"; then PREV=$t; break; fi
  done
  if [ -n "$PREV" ]; then
    link="[\`$old\`](https://github.com/$REPO/releases/download/$PREV/$old)（本版没有打包，沿用 ${PREV}）"
  else
    link="（本版没有打包）"
  fi
  # 用 awk 替换，避免链接里的 / 和 & 被 sed 当成特殊字符
  awk -v f="\`$APP_NAME-$V-$suffix\`" -v r="$link" '{ i = index($0, f); if (i) $0 = substr($0, 1, i - 1) r substr($0, i + length(f)); print }' "$notes" > "$notes.tmp"
  mv "$notes.tmp" "$notes"
  echo "缺少 $suffix → $link"
done
changes="$(awk -v h="## $TAG" '$0 == h {on = 1; next} /^## / {on = 0} on' "$ROOT/CHANGELOG.md")"
[ -n "$changes" ] && printf '\n### 本次更新\n%s\n' "$changes" >> "$notes"

if [ -n "${DRY_RUN:-}" ]; then
  echo; cat "$notes"; rm -f "$notes"; exit 0
fi

pre=""
case "$V" in *-*) pre="--prerelease" ;; esac
log "发布 ${TAG}：${files[*]##*/}"
gh release create "$TAG" "${files[@]}" "$DIST_DIR/SHA256SUMS.txt" $pre --verify-tag \
  --title "坦克大战 2026 $TAG" --notes-file "$notes"
rm -f "$notes"
