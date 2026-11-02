#!/bin/sh
# 在本机模拟排行榜上线：和正式部署用同一套文件（Dockerfile、compose.yml、Caddyfile），域名换成 localhost
#
# 用法：server/deploy/local.sh <up|seed|game|status|down>
#   up      用 Docker 起服务和 Caddy（https://localhost，Caddy 自签证书），跑冒烟检查，再填一批模拟玩家
#           没有 Docker 时直接用 python3 起服务（只有 http://127.0.0.1:8787，没有 HTTPS）
#   seed    往今天的每日挑战榜和本周的周榜（海外区）里填 10 个模拟玩家。服务端同一个 IP 60 秒内最多 30 次上传，
#           所以一次只填 20 条；60 秒内再运行会被限频
#   game    复制一份游戏，lbURL 指向本机服务（http://127.0.0.1:8787），运行（需要 spx）
#   status  看服务是否在运行
#   down    停掉服务并删掉数据
#
# 环境变量：LB_LOCAL=http://127.0.0.1:8787（seed / game 连哪个服务）
set -eu
D=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$D/../.." && pwd)
LB="${LB_LOCAL:-http://127.0.0.1:8787}"
LB="${LB%/}"
PROJECT=tankbattle-lb-local
STATE=${TMPDIR:-/tmp}/tankbattle-lb-local
compose() { LB_DOMAIN=localhost docker compose -p "$PROJECT" -f "$D/compose.yml" -f "$D/compose.local.yml" "$@"; }
have_docker() { command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; }

wait_health() {
  i=0
  until curl -fsS --max-time 2 "$LB/v1/health" >/dev/null 2>&1; do
    i=$((i + 1))
    [ $i -lt 60 ] || { echo "❌ 等了 30 秒，服务还没起来：$LB" >&2; exit 1; }
    sleep 0.5
  done
}

# 一条成绩：玩家序号 区 榜 期 分数 用时 关卡 芯片（JSON 数组）。模拟玩家的 ID 第 5~8 位是 5eed
post() {
  n=$1 region=$2 board=$3 period=$4 score=$5 secs=$6 stage=$7 chips=$8
  level=$(( $(printf '%s' "$chips" | tr -cd '"' | wc -c) / 2 + 1 ))  # 等级 = 芯片数 + 1（服务端会核对）
  player=$(printf '%04x5eed%08x' $(( (n * 4099 + 4096) % 65536 )) "$n")  # 前 4 位决定游戏里显示的编号，要各不相同
  body="{\"player\":\"$player\",\"region\":\"$region\",\"board\":\"$board\",\"period\":$period,\"score\":$score,\"secs\":$secs,\"stage\":$stage,\"chips\":$chips,\"level\":$level,\"version\":\"local\"}"
  curl -fsS --max-time 5 -H 'Content-Type: application/json' -d "$body" "$LB/v1/score" >/dev/null || { echo "❌ 上传失败：$body" >&2; exit 1; }
}

seed() {
  health=$(curl -fsS --max-time 5 "$LB/v1/health") || { echo "❌ 连不上 ${LB}（先运行 local.sh up）" >&2; exit 1; }
  day=$(echo "$health" | sed -n 's/.*"day": *\([0-9]*\).*/\1/p')
  week=$(echo "$health" | sed -n 's/.*"week": *\([0-9]*\).*/\1/p')
  set -- '["pierce","bounce","shield"]' '["rapid","double"]' '["double","rapid","engine"]' '["shield"]' '["bounce","pierce"]' \
    '["engine","float","magnet"]' '[]' '["stealth","rapid"]' '["magnet"]' '["rapid","shield","engine"]'
  n=1
  for chips in "$@"; do
    post "$n" global daily "$day" $((9800 - n * 760)) $((150 + n * 23)) 10 "$chips"
    post "$n" global weekly "$week" $((52000 - n * 4300)) $((900 + n * 140)) $((9 - (n + 1) / 2)) "$chips"
    n=$((n + 1))
  done
  echo "✅ 填了 10 个模拟玩家：第 $day 天的每日挑战榜、第 $week 周的周榜（海外区，${LB}）"
}

case "${1:-}" in
up)
  mkdir -p "$STATE"
  if have_docker; then
    compose up -d --build
    wait_health
    compose cp caddy:/data/caddy/pki/authorities/local/root.crt "$STATE/caddy-root.crt" >/dev/null 2>&1 || true
    i=0
    until [ -s "$STATE/caddy-root.crt" ] || [ $i -ge 20 ]; do
      sleep 0.5; i=$((i + 1))
      compose cp caddy:/data/caddy/pki/authorities/local/root.crt "$STATE/caddy-root.crt" >/dev/null 2>&1 || true
    done
    echo "==> 冒烟检查（经过 Caddy 的 HTTPS，和线上一样）"
    CURL_CA_BUNDLE="$STATE/caddy-root.crt" sh "$D/smoke.sh" https://localhost global
  else
    echo "没有可用的 Docker：直接用 python3 起服务（只有 http，没有 Caddy）"
    python3 "$ROOT/server/leaderboard.py" --port 8787 --db "$STATE/lb.sqlite" > "$STATE/server.log" 2>&1 &
    echo $! > "$STATE/server.pid"
    wait_health
    sh "$D/smoke.sh" "$LB" global
  fi
  seed
  echo "下一步：server/deploy/local.sh game（游戏连本机服务），打完一局按 B 看排行榜"
  ;;
seed)
  seed
  ;;
game)
  W="$STATE/game"
  rm -rf "$W" && mkdir -p "$W"
  (cd "$ROOT/TankBattle" && tar --exclude .temp -cf - .) | (cd "$W" && tar -xf -)
  sed -E -i.bak "s|^([[:space:]]*lbURL[[:space:]]*=[[:space:]]*)\"\"|\\1\"$LB\"|" "$W/main.spx" && rm -f "$W/main.spx.bak"
  grep -q "lbURL *= *\"$LB\"" "$W/main.spx" || { echo "❌ 没能把 lbURL 改成 $LB" >&2; exit 1; }
  echo "游戏副本：${W}（lbURL = ${LB}）"
  [ "${LB_GAME_DRY:-}" = 1 ] && exit 0
  cd "$W" && spx run .
  ;;
status)
  if curl -fsS --max-time 2 "$LB/v1/health"; then echo; else echo "没有在运行：$LB"; exit 1; fi
  ;;
down)
  if have_docker; then compose down -v; fi
  if [ -f "$STATE/server.pid" ]; then kill "$(cat "$STATE/server.pid")" 2>/dev/null || true; rm -f "$STATE/server.pid"; fi
  rm -rf "$STATE"
  echo "已停止，本机模拟的数据已删除"
  ;;
*)
  sed -n '2,14p' "$0"
  exit 1
  ;;
esac
