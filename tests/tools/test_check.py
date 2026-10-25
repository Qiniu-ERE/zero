"""T01~T03：关卡地图检查工具 tools/levels/check.py（见 docs/v4/TEST_PLAN.md 第 3.1 节）"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CHECK = os.path.join(ROOT, "tools", "levels", "check.py")
sys.path.insert(0, os.path.dirname(CHECK))
import check  # noqa: E402

# 一张合格的地图：除了基地全是空地
OK = ["." * 13 for _ in range(12)] + ["......E......"]


def edit(rows, r, c, ch):
    """返回把第 r 行第 c 列改成 ch 之后的新地图"""
    out = list(rows)
    out[r] = out[r][:c] + ch + out[r][c + 1:]
    return out


def wall(rows, r, cols, ch="S"):
    for c in cols:
        rows = edit(rows, r, c, ch)
    return rows


class LevelsInGame(unittest.TestCase):
    def test_T01_all_stages_pass(self):
        levels = check.levels_from_spx(os.path.join(ROOT, "TankBattle", "main.spx"))
        self.assertEqual(sorted(levels), list(range(1, 9)), "main.spx 里应该有第 1~8 关")
        for n, rows in levels.items():
            with self.subTest(stage=n):
                self.assertEqual(check.problems(rows), [])


class Problems(unittest.TestCase):
    def assertProblem(self, rows, words):
        ps = check.problems(rows)
        self.assertTrue(any(words in p for p in ps), f"应该报告“{words}”，实际 {ps}")

    def test_T02_ok_map(self):
        self.assertEqual(check.problems(OK), [])

    def test_T02_row_count(self):
        self.assertProblem(OK[:12], "应该有 13 行")

    def test_T02_column_count(self):
        self.assertProblem(OK[:5] + ["." * 12] + OK[6:], "应该有 13 个字符")

    def test_T02_unknown_char(self):
        self.assertProblem(edit(OK, 3, 3, "X"), "不认识的字符")

    def test_T02_no_base(self):
        self.assertProblem(edit(OK, 12, 6, "."), "基地 E 必须有且只有一个")

    def test_T02_two_bases(self):
        self.assertProblem(edit(OK, 5, 5, "E"), "基地 E 必须有且只有一个")

    def test_T02_base_moved(self):
        self.assertProblem(edit(edit(OK, 12, 6, "."), 12, 2, "E"), "基地 E 必须有且只有一个")

    def test_T02_enemy_spawn_blocked(self):
        for c in (0, 6, 12):
            with self.subTest(col=c):
                self.assertProblem(edit(OK, 0, c, "B"), f"敌人出生点（第 0 行第 {c} 列）")

    def test_T02_player_spawn_blocked(self):
        self.assertProblem(edit(OK, 12, 4, "B"), "玩家出生点")

    def test_T02_enemy_cannot_reach_base(self):
        # 第 1 行整行钢墙：三个出生点都过不来
        self.assertProblem(wall(OK, 1, range(13)), "到不了基地旁边")

    def test_T02_water_also_blocks(self):
        self.assertProblem(wall(OK, 1, range(13), "W"), "到不了基地旁边")

    def test_T02_bricks_do_not_block(self):
        # 砖墙能打掉，整行砖墙不算堵死
        self.assertEqual(check.problems(wall(OK, 1, range(13), "B")), [])

    def test_T02_grass_does_not_block(self):
        self.assertEqual(check.problems(wall(OK, 1, range(13), "G")), [])

    def test_T02_player_cannot_reach_spawn(self):
        # 只把左上角出生点围起来：敌人能从别的出生点到基地，但玩家开不到左上角
        rows = edit(edit(OK, 0, 1, "S"), 1, 0, "S")
        self.assertProblem(rows, "玩家开不到敌人出生点（第 0 行第 0 列）")

    def test_T02_steel_or_water_next_to_base(self):
        for (r, c), ch in [((11, 6), "S"), ((12, 5), "W"), ((12, 7), "S")]:
            with self.subTest(cell=(r, c), ch=ch):
                self.assertProblem(edit(OK, r, c, ch), f"基地旁边（第 {r} 行第 {c} 列）")

    def test_T02_no_wrap_around_rows(self):
        # 第 0~11 行在第 1 列竖着一道钢墙，左边一条只有 1 格宽的通道；
        # 如果连通性计算错误地从一行末尾“绕”到下一行开头，就会以为左上角出生点能到达
        rows = OK
        for r in range(12):
            rows = edit(rows, r, 1, "S")
        rows = edit(rows, 11, 0, "S")
        self.assertProblem(rows, "从出生点（第 0 行第 0 列）到不了基地旁边")


class CommandLine(unittest.TestCase):
    def run_check(self, *args):
        return subprocess.run([sys.executable, CHECK, *args], capture_output=True, text=True)

    def test_T03_game_maps_exit_zero(self):
        r = self.run_check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.count("✓"), 8)

    def test_T03_text_file(self):
        with tempfile.TemporaryDirectory() as d:
            good = os.path.join(d, "good.txt")
            bad = os.path.join(d, "bad.txt")
            with open(good, "w", encoding="utf-8") as f:
                f.write("\n".join(OK) + "\n")
            with open(bad, "w", encoding="utf-8") as f:
                f.write("\n".join(wall(OK, 1, range(13))) + "\n")
            self.assertEqual(self.run_check(good).returncode, 0)
            r = self.run_check(bad)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("✗", r.stdout)


if __name__ == "__main__":
    unittest.main()
