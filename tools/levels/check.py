#!/usr/bin/env python3
"""检查关卡地图是否合法：从 TankBattle/main.spx 的 levelMap() 读出每一关，逐条检查规则。

用法：python3 tools/levels/check.py            # 检查 main.spx 里的所有关卡
      python3 tools/levels/check.py map.txt   # 检查一个文本文件里的地图（13 行，每行 13 个字符）

v3.0 规划中的“自己做地图”（docs/v3/MAP_EDITOR.md）也用这套规则做实时检查。
不依赖第三方库。发现问题时打印原因并以非零状态退出。
"""
import os
import re
import sys
from collections import deque

ROWS = COLS = 13
CHARS = set(".BSWGE")     # 空地 砖墙 钢墙 水面 草丛 基地
PASS = set(".G")          # 坦克能直接开过去的格子
BREAK = set("B")          # 能打掉的格子（打掉以后就能通过）
SPAWNS = [(0, 0), (0, 6), (0, 12)]  # 敌人出生点（main.spx 的 spawnEnemy）
PLAYER = (12, 4)          # 玩家出生点（Player.spx 的 respawn）
BASE = (12, 6)            # 基地（老鹰）


def problems(rows):
    """返回地图的问题列表，空列表表示合法"""
    out = []
    if len(rows) != ROWS:
        return [f"应该有 {ROWS} 行，实际 {len(rows)} 行"]
    for r, line in enumerate(rows):
        if len(line) != COLS:
            out.append(f"第 {r} 行应该有 {COLS} 个字符，实际 {len(line)} 个")
        bad = set(line) - CHARS
        if bad:
            out.append(f"第 {r} 行有不认识的字符 {''.join(sorted(bad))}（只能用 {''.join(sorted(CHARS))}）")
    if out:
        return out

    at = lambda p: rows[p[0]][p[1]]
    bases = [(r, c) for r in range(ROWS) for c in range(COLS) if rows[r][c] == "E"]
    if bases != [BASE]:
        out.append(f"基地 E 必须有且只有一个，位置在第 {BASE[0]} 行第 {BASE[1]} 列，实际 {bases}")
    for p in SPAWNS:
        if at(p) != ".":
            out.append(f"敌人出生点（第 {p[0]} 行第 {p[1]} 列）必须是空地 .")
    if at(PLAYER) != ".":
        out.append(f"玩家出生点（第 {PLAYER[0]} 行第 {PLAYER[1]} 列）必须是空地 .")

    # 连通性：砖墙能打掉，所以算“可以通过”；钢墙和水面不行
    def reach(start):
        seen = {start}
        q = deque([start])
        while q:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (r + dr, c + dc)
                if 0 <= n[0] < ROWS and 0 <= n[1] < COLS and n not in seen and at(n) in PASS | BREAK:
                    seen.add(n)
                    q.append(n)
        return seen

    near_base = {(BASE[0] + dr, BASE[1] + dc) for dr, dc in ((-1, 0), (0, -1), (0, 1))}
    for p in SPAWNS:
        if at(p) == "." and not (reach(p) & near_base):
            out.append(f"从出生点（第 {p[0]} 行第 {p[1]} 列）到不了基地旁边（钢墙或水面把路堵死了）")
    if at(PLAYER) == ".":
        got = reach(PLAYER)
        for p in SPAWNS:
            if p not in got:
                out.append(f"玩家开不到敌人出生点（第 {p[0]} 行第 {p[1]} 列）")

    # 基地不能被钢墙或水面完全包住，否则敌人永远打不到它，关卡失去意义
    for p in near_base:
        if at(p) in "SW":
            out.append(f"基地旁边（第 {p[0]} 行第 {p[1]} 列）不能是钢墙或水面")
    return out


def levels_from_spx(path):
    """读出 levelMap() 里的所有关卡：{关卡号: [13 行]}"""
    with open(path, encoding="utf-8") as f:
        src = f.read()
    m = re.search(r"func levelMap\(\) \[\]string \{(.*?)\n\}", src, re.S)
    if not m:
        sys.exit("main.spx 里没有找到 func levelMap()")
    body = m.group(1)
    rows = lambda block: re.findall(r'"([^"]*)"', block)
    levels = {int(n): rows(b) for n, b in re.findall(r"case (\d+):[^\n]*\n\s*return \[\]string\{(.*?)\}", body, re.S)}
    tail = re.search(r"\n\treturn \[\]string\{(.*?)\}\s*$", body, re.S)
    if tail:
        levels[1] = rows(tail.group(1))
    return dict(sorted(levels.items()))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            levels = {sys.argv[1]: [l.strip() for l in f if l.strip()]}
    else:
        levels = levels_from_spx(os.path.join(here, "..", "..", "TankBattle", "main.spx"))
    failed = 0
    for name, rows in levels.items():
        ps = problems(rows)
        counts = {ch: sum(line.count(ch) for line in rows) for ch in "BSWG"}
        if ps:
            failed += 1
            print(f"✗ 关卡 {name}")
            for p in ps:
                print(f"    {p}")
        else:
            print(f"✓ 关卡 {name}  砖 {counts['B']}  钢 {counts['S']}  水 {counts['W']}  草 {counts['G']}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
