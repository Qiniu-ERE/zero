"""把 difficulty.sh 的 results.csv 汇总成 Markdown 表（每关中位数 / 最小 / 最大）。

用法：python3 tools/test/difficulty/report.py results.csv [更多 results.csv ...] [时间上限秒数，默认 120]
（几次的结果可以合起来统计）
"""
import csv
import statistics
import sys


def stat(xs, fmt="{:.0f}"):
    if not xs:
        return "-"
    return "{} ({}~{})".format(fmt.format(statistics.median(xs)), fmt.format(min(xs)), fmt.format(max(xs)))


def main():
    args = sys.argv[1:]
    cap = args.pop() if args and args[-1].isdigit() else "120"
    rows = []
    for path in args:
        rows += list(csv.DictReader(open(path, encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault((r["mode"], int(r["stage"])), []).append(r)
    f = lambda rs, k: [float(r[k]) for r in rs]

    print("## 无人防守（玩家不参战，基地多久失守）")
    print()
    print(f"游戏秒数，中位数（最小~最大）；没失守的局按上限 {cap} 秒计入，并在“失守”列里看出来。")
    print()
    print("| 关卡 | 局数 | 失守 | 失守时间 s | 出兵 | 场上最多 | 出生重叠（次/局） | 敌人重叠 s |")
    print("|---|---|---|---|---|---|---|---|")
    for (m, s), rs in sorted(by.items()):
        if m != "idle":
            continue
        fell = sum(r["result"] == "base" for r in rs)
        print(f"| {s} | {len(rs)} | {fell}/{len(rs)} | {stat(f(rs, 'game_secs'))} | {stat(f(rs, 'spawned'))} "
              f"| {stat(f(rs, 'max_alive'))} | {stat(f(rs, 'spawn_overlap'))} | {stat(f(rs, 'overlap_secs'))} |")
    print()
    print("## 自动驾驶（路演演示的自动驾驶当玩家，去掉了演示保护）")
    print()
    print("结局：胜 = 消灭全部 20 辆，基 = 基地被敌人打掉，命 = 3 条命用完，时 = 到上限没分出胜负。")
    print("自动驾驶一直开火，常打到自己的基地；模拟里玩家子弹打基地不算失守，只在最后一列记次数。")
    print()
    print("| 关卡 | 局数 | 胜/基/命/时 | 用时 s | 消灭 | 丢命 | 出生重叠（次/局） | 敌人重叠 s | 自己打基地（次） |")
    print("|---|---|---|---|---|---|---|---|---|")
    for (m, s), rs in sorted(by.items()):
        if m != "auto":
            continue
        c = lambda k: sum(r["result"] == k for r in rs)
        print(f"| {s} | {len(rs)} | {c('win')}/{c('base')}/{c('lives')}/{c('cap')} | {stat(f(rs, 'game_secs'))} "
              f"| {stat(f(rs, 'killed'))} | {stat(f(rs, 'lives_lost'))} | {stat(f(rs, 'spawn_overlap'))} "
              f"| {stat(f(rs, 'overlap_secs'))} | {stat(f(rs, 'self_base_hits'))} |")
    lag = [float(r["real_secs"]) - float(r["game_secs"]) for r in rows]
    if lag and max(lag) > 5:
        print()
        print(f"注意：有的局真实时间比游戏时间多了 {max(lag):.0f} 秒（机器忙、掉帧），出兵按真实时间算，"
              "这些局的敌军压力偏大。把 JOBS 调小重跑。")


if __name__ == "__main__":
    main()
