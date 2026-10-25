#!/bin/sh
# 难度模拟（docs/v5 REVIEW 的 A4，顺带看 A11 出生重叠）：每关跑几局无头对局，统计难度指标
#
# 用法：tools/test/difficulty.sh                     # 8 关 × 2 种场景 × 每关 3 局
#       RUNS=5 tools/test/difficulty.sh               # 每关每种场景跑几局（默认 3）
#       STAGES="4 8" MODES=idle tools/test/difficulty.sh
#       CAP=120 JOBS=2 tools/test/difficulty.sh       # 每局时间上限（秒，默认 120）；同时跑几个 spx（默认 2）
#       SIM_SED=try.sed STAGES=4 tools/test/difficulty.sh  # 试调参：先对副本 main.spx 执行 sed -f try.sed
#       KEEP=1 tools/test/difficulty.sh              # 跑完保留工程副本和日志（默认每关跑完就删，只留结果）
#
# 两种场景（MODES，默认 "idle auto"）：
#   idle  无人防守：玩家坦克藏起来不参战，看基地多久失守。衡量“地图 + 敌军配置”本身的压力
#   auto  自动驾驶：用路演演示的自动驾驶（autopilotDir）当一个很笨的玩家。演示模式下基地打不掉、
#         玩家不会死，所以副本里把这两处保护去掉（只改临时副本，仓库里的游戏不动）
#
# 做法和 run_spx.sh 一样：每关复制一份工程，打几处补丁（见下面的 patch），把 difficulty/sim.spx
# 追加到副本 main.spx 末尾，用 spx run -headless 运行；一个进程里连打 RUNS 局。
# 结果：$WORK/results.csv（每局一行）和 $WORK/report.md（每关的中位数 / 最小 / 最大），report.md 也会打印出来。
#
# 计时说明：游戏里移动按每帧 deltaTime（最多 0.05 秒）算，出兵按真实时间 wait。报告用“游戏秒数”；
# 机器很忙时两者会差开（CSV 里两个都有），这时把 JOBS 调小。
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
RUNS=${RUNS:-3}
CAP=${CAP:-120}
JOBS=${JOBS:-2}
STAGES=${STAGES:-1 2 3 4 5 6 7 8}
MODES=${MODES:-idle auto}
WORK=${TMPDIR:-/tmp}/tankbattle-difficulty
GOPATH=${GOPATH:-$(go env GOPATH 2>/dev/null || echo "$HOME/go")}
GOCACHE=${GOCACHE:-$(go env GOCACHE 2>/dev/null || echo "$HOME/.cache/go-build")}
XDG_CACHE_HOME=${XDG_CACHE_HOME:-$HOME/.cache}
export GOPATH GOCACHE XDG_CACHE_HOME

rm -rf "$WORK" && mkdir -p "$WORK"
PIDS=""
trap 'for p in $PIDS; do pkill -P $p 2>/dev/null; kill $p 2>/dev/null; done' INT TERM

# 打补丁；补丁没打上（游戏代码改过了）就报错退出，免得统计出错的数据
patch() { # 文件 sed表达式 打完后应该能搜到的内容
	sed -i.bak "$2" "$1" && rm -f "$1.bak"
	grep -q -- "$3" "$1" || { echo "补丁没打上：$1（$3），游戏代码可能改过了，请更新 difficulty.sh" >&2; exit 1; }
}

prepare() { # 模式 关卡 → 目录
	dir="$WORK/$1-s$2"
	mkdir -p "$dir/home"
	cp -R "$ROOT/TankBattle" "$dir/"
	g="$dir/TankBattle"
	# 计数变量放进 main.spx 的 var 块
	awk '!done && /^var \($/ { print; print "\tsimSpawnOverlap int"; print "\tsimOverlapSecs float64"; print "\tsimSelfHits int"; done = 1; next } { print }' \
		"$g/main.spx" > "$g/main.new" && mv "$g/main.new" "$g/main.spx"
	grep -q simSpawnOverlap "$g/main.spx" || { echo "没找到 main.spx 的 var 块" >&2; exit 1; }
	# 去掉演示模式的两处保护：基地能被敌人打掉、玩家会被击毁。
	# 但自动驾驶一直在开火，常常朝自己的基地打（真人不会），所以玩家子弹打到基地不算失守，只记次数
	patch "$g/main.spx" 's,if !autopilot { // 路演演示时基地不会被打掉,if byPlayer { simSelfHits++ } else { // 模拟：去掉演示保护,' '模拟：去掉演示保护'
	patch "$g/Player.spx" 's,if dead || gameOver || shield > 0 || autopilot {,if dead || gameOver || shield > 0 { // 模拟：去掉演示保护,' '模拟：去掉演示保护'
	# 自动驾驶炮口正对基地（同一行或同一列、基地在前方）时不开火，免得一直打自己的基地
	awk '
		/d = autopilotDir\(dt\)/ { print; ap = 1; next }
		ap && /^\t\t\tshoot$/ {
			print "\t\t\tsimAim := (face == 90 && xpos < baseX) || (face == -90 && xpos > baseX)"
			print "\t\t\tsimAim = (simAim && math.Abs(ypos-baseY) < 20) || (face == 180 && ypos > baseY && math.Abs(xpos-baseX) < 20)"
			print "\t\t\tif !simAim {"; print "\t\t\t\tshoot"; print "\t\t\t}"
			ap = 0; next }
		{ ap = 0; print }
	' "$g/Player.spx" > "$g/Player.new" && mv "$g/Player.new" "$g/Player.spx"
	grep -q simAim "$g/Player.spx" || { echo "Player.spx 的补丁没打上" >&2; exit 1; }
	# A11：敌人出生后第一帧是否和别的坦克重叠；敌人互相重叠的累计时间
	awk '
		/^\tfor alive \{$/ && !a { print "\tsimFirst := true"; print; a = 1; next }
		/^\t\tdrive dt$/ && a && !b { print
			print "\t\tif simFirst {"; print "\t\t\tsimFirst = false"; print "\t\t\tif touchingTank() {"; print "\t\t\t\tsimSpawnOverlap++"; print "\t\t\t}"; print "\t\t}"
			print "\t\tif touching(\"Enemy\") {"; print "\t\t\tsimOverlapSecs += dt"; print "\t\t}"
			b = 1; next }
		{ print }
	' "$g/Enemy.spx" > "$g/Enemy.new" && mv "$g/Enemy.new" "$g/Enemy.spx"
	grep -q simOverlapSecs "$g/Enemy.spx" || { echo "Enemy.spx 的补丁没打上" >&2; exit 1; }
	# 试调参：SIM_SED 是一个 sed 脚本文件，先用在副本的 main.spx 上（改 stageTune / levelMap 看效果，不动仓库）
	if [ -n "${SIM_SED:-}" ]; then
		sed -i.bak -f "$SIM_SED" "$g/main.spx" && rm -f "$g/main.spx.bak"
	fi
	{ printf '\n// ---- 难度模拟 ----\n'
	  sed -e "s/SIM_STAGE/$2/g" -e "s/SIM_RUNS/$RUNS/g" -e "s/SIM_CAP/$CAP.0/g" -e "s/SIM_MODE/\"$1\"/g" "$ROOT/tools/test/difficulty/sim.spx"
	} >> "$g/main.spx"
}

run() { # 模式 关卡（在后台跑）
	dir="$WORK/$1-s$2"
	log="$dir/run.log"
	limit=$((RUNS * (CAP + 15) + 60))
	(cd "$dir/TankBattle" && HOME="$dir/home" XDG_CONFIG_HOME="$dir/home/.config" APPDATA="$dir/home/AppData" \
		exec spx run -headless . > "$log" 2>&1) &
	pid=$!
	secs=0
	while kill -0 $pid 2>/dev/null && [ $secs -lt $limit ]; do sleep 1; secs=$((secs + 1)); done
	if kill -0 $pid 2>/dev/null; then
		echo "  超时：$1 第 $2 关（$limit 秒）" >&2
		pkill -P $pid 2>/dev/null || true
		kill $pid 2>/dev/null || true
	fi
	wait $pid 2>/dev/null || true
	n=$(grep -a -c '^SIM [ia]' "$log" || true)
	echo "  $1 第 $2 关：$n 局（${secs}s）"
	grep -a '^SIM [ia]' "$log" >> "$WORK/$1-s$2.sim" || true
	if grep -a -q -E 'panic|cannot alloc method|failed to build' "$log"; then
		echo "  引擎报错，见 $log" >&2
		grep -a -E 'panic|cannot alloc|failed|error' "$log" | head -5 >&2
	elif [ -z "${KEEP:-}" ]; then
		rm -rf "$dir" # 每份副本约 100 MB（spx 会解压一份运行时），跑完就删
	fi
}

start=$(date +%s)
echo "==> 难度模拟：场景 ${MODES}，关卡 ${STAGES}，每关 ${RUNS} 局，上限 ${CAP}s，并行 ${JOBS}"
for m in $MODES; do
	for s in $STAGES; do
		prepare "$m" "$s"
		run "$m" "$s" &
		PIDS="$PIDS $!"
		while [ "$(jobs -p | wc -l)" -ge "$JOBS" ]; do sleep 1; done
	done
done
wait
echo "mode,stage,run,result,real_secs,game_secs,killed,spawned,max_alive,lives_lost,spawn_overlap,overlap_secs,self_base_hits" > "$WORK/results.csv"
cat "$WORK"/*.sim 2>/dev/null | sed 's/^SIM //' | tr ' ' ',' | sort -t, -k1,1 -k2,2n -k3,3n >> "$WORK/results.csv"
python3 "$ROOT/tools/test/difficulty/report.py" "$WORK/results.csv" "$CAP" > "$WORK/report.md"
cat "$WORK/report.md"
echo
echo "---- 用时 $(( $(date +%s) - start )) 秒；结果：$WORK/results.csv、$WORK/report.md"
echo "     几次的结果可以合起来看：python3 tools/test/difficulty/report.py 1.csv 2.csv ..."
