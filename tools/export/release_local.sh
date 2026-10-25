#!/usr/bin/env bash
# 本机发布：把 dist/ 里打好的安装包发布成 GitHub Release（GitHub Actions 用不了时的替代）。
# 用法：
#   tools/export/build_local.sh                          先打包（结果写在 dist/BUILD_LOCAL.md）
#   git tag v3.0.2 && git push origin v3.0.2             在 main 上、打包的那个提交上打标签并推送
#   tools/export/release_local.sh                        新建 Release
#   tools/export/release_local.sh --append               给已有的 Release 补包（例如后来在别的机器上打的 Windows / iOS 包）：
#                                                        只上传 Release 里还没有的文件，重算 SHA256SUMS.txt，重新生成说明
# 版本号默认取 CHANGELOG.md 的第一节，也可以用 APP_VERSION=3.0.2 指定。
# dist/ 里没有的平台（比如本机打不了的 Windows、iOS），说明里会改成指向版本号最近的、有这个平台安装包的以前的版本
# （一个一个往前找：v3.0.2 本身也没有 Windows / iOS 包，就会找到 v3.0.1）。
#
# 发布前的检查（不通过就停）：
#   - 标签存在、已经推送；
#   - dist/BUILD_LOCAL.md 里记录的版本号和提交等于这个标签，打包时工作区是干净的，表里没有 ❌；
#     dist/ 里有 BUILD_LOCAL.md 没列出的安装包时给出提醒（可能是别的机器打的，也可能是旧包）。
#   别的机器上用 build.sh 打的包没有 BUILD_LOCAL.md：确认无误后用 SKIP_BUILD_CHECK=1 跳过这一项。
#
# DRY_RUN=1：只做检查（不通过也继续）、打印发布说明和要上传的文件，不创建 / 修改 Release（不需要标签）。
# 测试用：RELEASE_ASSETS_FILE=文件 代替 gh 查询已有的 Release（每行“标签 文件名”），REPO=owner/name 代替 gh repo view。
set -euo pipefail
source "$(dirname "$0")/env.sh"

APPEND=""
for a in "$@"; do
  case "$a" in
    --append) APPEND=1 ;;
    -h|--help) sed -n '2,21p' "$0"; exit 0 ;;
    *) echo "不认识的参数：${a}（可选 --append）" >&2; exit 1 ;;
  esac
done

V="$APP_VERSION"
[ -n "$V" ] || { echo "没有版本号：CHANGELOG.md 里找不到「## vX.Y.Z」，或者设置 APP_VERSION" >&2; exit 1; }
TAG="v$V"
REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
SUFFIXES="windows-x64.zip macos-arm64.zip linux-x64.tar.gz web.zip android.apk ios-unsigned.ipa"

tmp="$(mktemp -d "${TMPDIR:-/tmp}/tankbattle-release.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

problems=0
stop() {  # 检查不通过：正式发布时退出，DRY_RUN 时只提示
  echo "❌ $*" >&2
  problems=$((problems + 1))
  [ -n "${DRY_RUN:-}" ] || exit 1
}

# ---- 要发布的文件：只认这几种文件名（不用通配符：4.0.1-* 会匹配到 4.0.1-rc.1-* 的包）
files=()
for suffix in $SUFFIXES; do
  f="$DIST_DIR/$APP_NAME-$V-$suffix"
  [ -f "$f" ] && files+=("$f")
done
if [ ${#files[@]} -eq 0 ] && [ -z "$APPEND" ]; then
  echo "dist/ 里没有 $V 的安装包，先运行 build_local.sh" >&2
  exit 1
fi

# ---- 标签
tag_commit=""
if git -C "$ROOT" rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  tag_commit="$(git -C "$ROOT" rev-list -n 1 "$TAG")"
  if [ -z "${DRY_RUN:-}" ]; then
    git -C "$ROOT" ls-remote --exit-code --tags origin "$TAG" >/dev/null || stop "标签 $TAG 还没推送到 GitHub"
  fi
else
  stop "没有标签 ${TAG}：先在 main 上 git tag $TAG 并推送"
fi

# ---- 安装包是不是从这个标签打的（dist/BUILD_LOCAL.md，build_local.sh 写的）
summary="$DIST_DIR/BUILD_LOCAL.md"
if [ -n "${SKIP_BUILD_CHECK:-}" ]; then
  echo "⚠️  SKIP_BUILD_CHECK=1：不核对 dist/BUILD_LOCAL.md，请自己确认安装包是从 $TAG 打的"
elif [ ! -f "$summary" ]; then
  stop "没有 ${summary}：先用 build_local.sh 打包（别的机器上打的包，确认无误后用 SKIP_BUILD_CHECK=1）"
else
  # build_local.sh 写的一行：<!-- build_local version=4.0.1 commit=<完整提交号> dirty=0 -->
  meta="$(sed -n 's/^<!-- build_local \(.*\) -->$/\1/p' "$summary" | head -1)"
  b_version="$(sed -n 's/.*version=\([^ ]*\).*/\1/p' <<<"$meta")"
  b_commit="$(sed -n 's/.*commit=\([0-9a-f]*\).*/\1/p' <<<"$meta")"
  b_dirty="$(sed -n 's/.*dirty=\([01]\).*/\1/p' <<<"$meta")"
  if [ -z "$meta" ]; then
    stop "$summary 是旧版 build_local.sh 写的，没有记录完整的提交号：重新运行 build_local.sh"
  else
    [ "$b_version" = "$V" ] || stop "dist/ 里的包是 ${b_version} 版打的，要发布的是 $V"
    [ -z "$tag_commit" ] || [ "$b_commit" = "$tag_commit" ] ||
      stop "dist/ 里的包是从提交 ${b_commit:0:10} 打的，标签 $TAG 指向 ${tag_commit:0:10}：在标签的提交上重新运行 build_local.sh"
    [ "$b_dirty" = 0 ] || stop "打包时工作区有未提交的改动，包里的内容和标签不一定一致：提交或丢弃改动后重新打包"
  fi
  if grep -q '| ❌ |' "$summary"; then
    stop "BUILD_LOCAL.md 里有失败的平台：$(grep '| ❌ |' "$summary" | cut -d'|' -f2 | tr -d ' ' | tr '\n' ' ')（修好后重新打这个平台：build_local.sh <平台>；这次不发它的话，删掉 dist/BUILD_LOCAL.md 再用 build_local.sh 只打要发的平台）"
  fi
  for f in ${files[@]+"${files[@]}"}; do
    grep -qF "$(basename "$f")" "$summary" ||
      echo "⚠️  $(basename "$f") 不在 BUILD_LOCAL.md 里（别的机器打的？还是以前留下的旧包？）"
  done
fi

# ---- 已有的 Release 和它们的安装包
if [ -n "${RELEASE_ASSETS_FILE:-}" ]; then
  all_assets="$(cat "$RELEASE_ASSETS_FILE")"
  release_exists() { awk -v t="$1" '$1 == t {f = 1} END {exit !f}' <<<"$all_assets"; }
  tags="$(cut -d' ' -f1 <<<"$all_assets" | sort -u)"
else
  release_exists() { gh release view "$1" --json tagName >/dev/null 2>&1; }
  tags="$(gh release list --exclude-drafts --exclude-pre-releases --limit 100 --json tagName -q '.[].tagName')"
  all_assets="$(for t in $tags; do gh release view "$t" --json assets -q '.assets[].name' | sed "s|^|$t |"; done)"
  if [ -n "$APPEND" ] && ! grep -qxF "$TAG" <<<"$tags" && release_exists "$TAG"; then   # 预发布不在上面的列表里
    all_assets="$all_assets
$(gh release view "$TAG" --json assets -q '.assets[].name' | sed "s|^|$TAG |")"
  fi
fi
# 比这个版本旧的正式版，按版本号从新到旧（gh release list 是按创建时间排的，补发旧版本时会排错）
prev_tags="$({ grep -vxF "$TAG" <<<"$tags" || true; echo "$TAG"; } | sed '/^$/d' | sort -V -r | awk -v t="$TAG" 'found; $0 == t {found = 1}')"

if [ -n "$APPEND" ]; then
  release_exists "$TAG" || { echo "还没有 $TAG 的 Release：去掉 --append 新建" >&2; exit 1; }
  existing="$(awk -v t="$TAG" '$1 == t {print $2}' <<<"$all_assets")"
else
  if release_exists "$TAG"; then
    stop "已经有 $TAG 的 Release：补包用 --append"
  fi
  existing=""
fi

# ---- 要上传的文件（--append 时跳过 Release 里已经有的）
upload=()
for f in ${files[@]+"${files[@]}"}; do
  if grep -qxF "$(basename "$f")" <<<"$existing"; then
    echo "已经有了，跳过：$(basename "$f")（要替换的话先在网页上删掉它）"
  else
    upload+=("$f")
  fi
done
[ -n "$APPEND" ] && [ ${#upload[@]} -eq 0 ] && echo "没有要补的文件，只更新说明和校验和"

# ---- 校验和：本地的文件重新算；--append 时保留 Release 里原有文件的那几行
sums="$tmp/SHA256SUMS.txt"
: > "$tmp/new-sums.txt"
for f in ${upload[@]+"${upload[@]}"}; do
  (cd "$(dirname "$f")" && shasum -a 256 "$(basename "$f")") >> "$tmp/new-sums.txt"
done
if [ -n "$APPEND" ] && grep -qxF SHA256SUMS.txt <<<"$existing"; then
  if [ -n "${RELEASE_ASSETS_FILE:-}" ]; then
    cp "${RELEASE_SUMS_FILE:-/dev/null}" "$tmp/old-sums.txt"   # 测试用
  else
    gh release download "$TAG" -p SHA256SUMS.txt -O "$tmp/old-sums.txt" --clobber
  fi
  awk 'NR == FNR { new[$2] = 1; next } !($2 in new)' "$tmp/new-sums.txt" "$tmp/old-sums.txt" > "$sums"
fi
cat "$tmp/new-sums.txt" >> "$sums"
sort -k 2 -o "$sums" "$sums"

# ---- 发布说明：Release 里会有的平台列出文件，没有的指向以前的版本
present="$(for f in ${files[@]+"${files[@]}"}; do basename "$f"; done; echo "$existing")"
notes="$tmp/notes.md"
sed "s/@VERSION@/$V/g" "$ROOT/tools/export/RELEASE_NOTES.md" > "$notes"
for suffix in $SUFFIXES; do
  grep -qxF "$APP_NAME-$V-$suffix" <<<"$present" && continue
  PREV=""
  for t in $prev_tags; do
    old="$APP_NAME-${t#v}-$suffix"
    if grep -qxF "$t $old" <<<"$all_assets"; then PREV=$t; break; fi
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
[ -z "$changes" ] || printf '\n### 本次更新\n%s\n' "$changes" >> "$notes"

if [ -n "${DRY_RUN:-}" ]; then
  echo
  echo "DRY_RUN：${APPEND:+补包 }${TAG}，要上传：$(for f in ${upload[@]+"${upload[@]}"}; do printf '%s ' "$(basename "$f")"; done)SHA256SUMS.txt"
  [ $problems -eq 0 ] || echo "（有 $problems 项检查没通过，正式发布时会停下）"
  echo "---- SHA256SUMS.txt"; cat "$sums"
  echo "---- 发布说明"; cat "$notes"
  exit 0
fi

cp "$sums" "$DIST_DIR/SHA256SUMS.txt"
if [ -n "$APPEND" ]; then
  log "给 $TAG 补包：$(for f in ${upload[@]+"${upload[@]}"}; do printf '%s ' "$(basename "$f")"; done)"
  [ ${#upload[@]} -eq 0 ] || gh release upload "$TAG" "${upload[@]}"
  gh release upload "$TAG" "$DIST_DIR/SHA256SUMS.txt" --clobber
  gh release edit "$TAG" --notes-file "$notes"
else
  pre=()
  case "$V" in *-*) pre=(--prerelease) ;; esac
  log "发布 ${TAG}：$(for f in "${upload[@]}"; do printf '%s ' "$(basename "$f")"; done)"
  gh release create "$TAG" "${upload[@]}" "$DIST_DIR/SHA256SUMS.txt" ${pre[@]+"${pre[@]}"} --verify-tag \
    --title "坦克大战 2026 $TAG" --notes-file "$notes"
fi
