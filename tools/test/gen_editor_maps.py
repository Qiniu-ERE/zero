#!/usr/bin/env python3
"""生成 tests/data/editor_maps.txt：检查 edCheck() 和 tools/levels/check.py 是否一致用的地图（E07）。

每张地图 13 行，后面跟一行结论（ok 或 bad，由 check.py 判定），地图之间空一行。
地图都是编辑器里画得出来的：锁定格（出生点、基地、护墙）和 main.spx 的 edLockedChar 一致。
包括 8 张关卡地图，以及不同墙密度的随机地图（随机数种子固定，每次生成的结果相同）。

用法：python3 tools/test/gen_editor_maps.py   # 改了 check.py 的规则或者锁定格以后重新生成并提交
"""
import os
import random
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "levels"))
import check  # noqa: E402

OUT = os.path.join(ROOT, "tests", "data", "editor_maps.txt")
N = 13
# 和 main.spx 的 edLocked / edLockedChar 相同
LOCKED = {(0, 0): ".", (0, 6): ".", (0, 12): ".", (12, 4): ".", (12, 8): ".", (12, 6): "E",
          (11, 5): "B", (11, 6): "B", (11, 7): "B", (12, 5): "B", (12, 7): "B"}


def lock(rows):
    grid = [list(r) for r in rows]
    for (r, c), ch in LOCKED.items():
        grid[r][c] = ch
    return ["".join(r) for r in grid]


def random_map(rng, density, mix):
    rows = ["".join(rng.choices(".BSWG", weights=[100 - density] + [density * w for w in mix])[0] for _ in range(N)) for _ in range(N)]
    return lock(rows)


def main():
    rng = random.Random(1024)
    maps = [lock(rows) for rows in check.levels_from_spx(os.path.join(ROOT, "TankBattle", "main.spx")).values()]
    # 墙越密，越容易把路堵死：从稀到密都要有，合格和不合格的都要足够多
    mixes = [(0.4, 0.3, 0.2, 0.1), (0.1, 0.6, 0.2, 0.1), (0.1, 0.2, 0.6, 0.1), (0.25, 0.25, 0.25, 0.25)]
    for density in (20, 35, 45, 55, 65, 80):
        for mix in mixes:
            for _ in range(10):
                maps.append(random_map(rng, density, mix))
    ok = 0
    with open(OUT, "w", encoding="utf-8") as f:
        for rows in maps:
            verdict = "bad" if check.problems(rows) else "ok"
            ok += verdict == "ok"
            f.write("\n".join(rows) + "\n" + verdict + "\n\n")
    print(f"{len(maps)} 张地图：合格 {ok}，不合格 {len(maps) - ok} → {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
