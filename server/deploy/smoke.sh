#!/bin/sh
# 部署后的冒烟检查：健康检查、上传一条测试成绩、读榜单、查名次
# 用法：server/deploy/smoke.sh https://lb.example.com [global|cn]
# 测试成绩记在一个固定的测试玩家（ffff000000000000）名下的每日挑战榜，分数 0，不会挤占真实玩家的名次
set -eu
base="${1:?用法：smoke.sh <服务地址> [global|cn]}"
base="${base%/}"
region="${2:-global}"
player=ffff000000000000
fail() { echo "❌ $1" >&2; exit 1; }
get() { curl -fsS --max-time 10 "$base$1" || fail "GET $1 失败"; }

health=$(get /v1/health)
echo "$health" | grep -q '"ok": *true' || fail "健康检查没有返回 ok：$health"
day=$(echo "$health" | sed -n 's/.*"day": *\([0-9]*\).*/\1/p')
[ -n "$day" ] || fail "健康检查里没有 day：$health"
echo "✅ 健康检查：$health"

body="{\"player\":\"$player\",\"region\":\"$region\",\"board\":\"daily\",\"period\":$day,\"score\":0,\"secs\":60,\"stage\":10,\"chips\":[],\"level\":1,\"version\":\"smoke\"}"
up=$(curl -fsS --max-time 10 -H 'Content-Type: application/json' -d "$body" "$base/v1/score") || fail "上传失败"
echo "$up" | grep -q '"ok": *true' || fail "上传没有返回 ok：$up"
echo "✅ 上传：$up"

board=$(get "/v1/board?region=$region&board=daily&period=$day&limit=3")
echo "$board" | grep -q '"ok": *true' || fail "读榜单失败：$board"
echo "✅ 榜单：$board"

rank=$(get "/v1/rank?region=$region&board=daily&period=$day&player=$player")
echo "$rank" | grep -q '"rank": *[1-9]' || fail "查不到测试玩家的名次：$rank"
echo "✅ 名次：$rank"
echo "冒烟检查通过：${base}（${region}）"
