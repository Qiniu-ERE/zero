#!/usr/bin/env python3
"""每日挑战的地图生成器（v6，docs/v6/PLAN.md 第四节）：和 TankBattle/main.spx 的 dailyRows 是同一个算法。

种子是日期（北京时间 UTC+8 的第几天），随机数用线性同余，所以全世界同一天是同一张图。
两边逐格相同由测试保证：tests/tools/test_daily.py 用这里生成 tests/data/daily_maps.txt，
引擎内测试 tests/spx/daily.spx 读这个文件和游戏里生成的比较；365 张都要通过 check.py 的规则。

用法：python3 tools/levels/daily.py              # 打印今天的地图
      python3 tools/levels/daily.py 20758        # 打印第 20758 天（2026-11-01，第 1 期）的地图
      python3 tools/levels/daily.py --write      # 重新生成 tests/data/daily_maps.txt（从第 1 期起 365 天）
"""
import os
import sys
import time
from collections import deque

ROWS = COLS = 13
EPOCH = 20757  # 第 1 期的前一天，和 main.spx 的 dailyEpoch 一致
DAYS = 365
DATA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tests", "data", "daily_maps.txt"))

# 五种风格（河流、钢铁、草丛、砖城、开阔）：砖 / 钢 / 水的比例（其余是草），奇数列 / 偶数列的密度，和编辑器的“随机起点”相同
WB = [40, 45, 30, 90, 55]
WS = [10, 50, 5, 10, 30]
WW = [45, 0, 0, 0, 5]
D_ODD = [45, 50, 55, 70, 25]
D_EVEN = [25, 20, 35, 30, 5]

BASE = 12 * COLS + 6
RING = {11 * COLS + 5, 11 * COLS + 6, 11 * COLS + 7, 12 * COLS + 5, 12 * COLS + 7}
LOCKED = {0, 6, 12, 12 * COLS + 4, 12 * COLS + 8, BASE} | RING


def lcg(s):
    return (s * 1103515245 + 12345) % 2147483648


def locked_char(i):
    if i == BASE:
        return "E"
    if i in RING:
        return "B"
    return "."


def reachable(m, start):
    """坦克从 start 能到哪些格子（砖墙能打掉，算能通过），和 main.spx 的 reachable 相同"""
    seen = {start}
    q = deque([start])
    while q:
        i = q.popleft()
        c = i % COLS
        for n in (i - COLS, i + COLS, i - 1, i + 1):
            if n < 0 or n >= ROWS * COLS or n in seen or m[n] not in ".GBE":
                continue
            if (n == i - 1 and c == 0) or (n == i + 1 and c == COLS - 1):
                continue
            seen.add(n)
            q.append(n)
    return seen


def map_problem(m):
    """和 main.spx 的 mapProblem 相同：0 可以玩，1 敌人到不了基地，2 坦克开不到敌人出生点"""
    for s in (0, 6, 12):
        got = reachable(m, s)
        if 11 * COLS + 6 not in got and 12 * COLS + 5 not in got and 12 * COLS + 7 not in got:
            return 1
    for p in (12 * COLS + 4, 12 * COLS + 8):
        got = reachable(m, p)
        if any(s not in got for s in (0, 6, 12)):
            return 2
    return 0


def daily_rows(day):
    s = day * 7919 + 12345

    def nxt(n):
        nonlocal s
        s = lcg(s)
        return (s // 65536) % n

    m = [locked_char(i) for i in range(ROWS * COLS)]
    for attempt in range(80):
        t = nxt(5)
        m = [locked_char(i) for i in range(ROWS * COLS)]
        for r in range(1, 13):
            for c in range(7):
                dens = D_ODD[t] if c % 2 == 1 else D_EVEN[t]
                ch = "."
                if nxt(100) < dens:
                    n = nxt(100)
                    if n < WB[t]:
                        ch = "B"
                    elif n < WB[t] + WS[t]:
                        ch = "S"
                    elif n < WB[t] + WS[t] + WW[t]:
                        ch = "W"
                    else:
                        ch = "G"
                for cc in (c, COLS - 1 - c):
                    if r * COLS + cc not in LOCKED:
                        m[r * COLS + cc] = ch
        if map_problem(m) == 0:
            break
        if attempt == 79:
            m = [locked_char(i) for i in range(ROWS * COLS)]
    return ["".join(m[r * COLS:(r + 1) * COLS]) for r in range(ROWS)]


def today():
    return (int(time.time()) + 8 * 3600) // 86400


def write_data(path=DATA):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 每日挑战地图（tools/levels/daily.py --write 生成，不要手改）：第 {EPOCH + 1} 天起 {DAYS} 天，每张图前面一行是天数\n")
        for d in range(EPOCH + 1, EPOCH + 1 + DAYS):
            f.write(f"{d}\n" + "\n".join(daily_rows(d)) + "\n")


def main():
    args = sys.argv[1:]
    if args == ["--write"]:
        write_data()
        print(f"写好了 {DATA}")
        return
    d = int(args[0]) if args else today()
    print(f"第 {d} 天（每日挑战 #{d - EPOCH}）")
    print("\n".join(daily_rows(d)))


if __name__ == "__main__":
    main()
