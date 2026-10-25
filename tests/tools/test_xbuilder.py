"""T09：游戏代码在 XBuilder 线上的 spx v3.3.0 下也能编译（tools/test/xbuilder_check.sh）。没有 Go 时跳过。"""
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CHECK = os.path.join(ROOT, "tools", "test", "xbuilder_check.sh")


@unittest.skipUnless(shutil.which("go"), "没有 Go")
class XBuilder(unittest.TestCase):
    def run_check(self, game):
        return subprocess.run([CHECK, game], capture_output=True, text=True, timeout=600)

    def test_T09_game_compiles_on_spx_v3_3_0(self):
        r = self.run_check(os.path.join(ROOT, "TankBattle"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_T09_catches_the_pr18_problem(self):
        # 把一处 int(rand(...)) 改回 #18 修复前的写法：spx 4.0 能跑，v3.3.0 编译不过，这里必须报出来
        with tempfile.TemporaryDirectory() as d:
            for f in os.listdir(os.path.join(ROOT, "TankBattle")):
                if f.endswith(".spx"):
                    shutil.copy(os.path.join(ROOT, "TankBattle", f), d)
            main = os.path.join(d, "main.spx")
            src = open(main, encoding="utf-8").read()
            self.assertIn("n := int(rand(1, 100))", src)
            open(main, "w", encoding="utf-8").write(src.replace("n := int(rand(1, 100))", "n := rand(1, 100)", 1))
            r = self.run_check(d)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("mismatched types float64 and int", r.stdout)


if __name__ == "__main__":
    unittest.main()
