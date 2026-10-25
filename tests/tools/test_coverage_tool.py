"""覆盖率工具 tools/test/spx_coverage.py 的测试：找函数和事件处理、插桩、读日志、基线和比较。用临时目录里的小工程。"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "test"))
import spx_coverage as cov  # noqa: E402

MAIN = """var (
\tscore int
)

func addScore(n int) {
\tscore += n
}

func reset() {
\tscore = 0
}

onStart => {
\treset()
}

onStart => {
\taddScore(1)
}

onMsg "hit", => {
\taddScore(2)
}

onKey KeySpace, => {
\taddScore(3)
}
"""

SPRITE = """func fire() {
}

onCloned => {
\tfire()
}

onClick => {
}
"""


class Fixture(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.game = os.path.join(self.dir, "game")
        os.makedirs(self.game)
        self.write("main.spx", MAIN)
        self.write("Tank.spx", SPRITE)

    def write(self, name, text, base=None):
        p = os.path.join(base or self.game, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def read(self, name):
        with open(os.path.join(self.game, name), encoding="utf-8") as f:
            return f.read()


class Points(Fixture):
    def test_points(self):
        pts = cov.all_points(self.game)
        self.assertEqual(pts, {
            "main.spx:addScore": "func",
            "main.spx:reset": "func",
            "main.spx:onStart #1": "handler",
            "main.spx:onStart #2": "handler",
            'main.spx:onMsg "hit"': "handler",
            "main.spx:onKey KeySpace": "input",
            "Tank.spx:fire": "func",
            "Tank.spx:onCloned": "handler",
            "Tank.spx:onClick": "input",
        })

    def test_messages(self):
        self.write("Boss.spx", 'onStart => {\n\tbroadcast "hit"\n\tbroadcastAndWait "boom"\n}\n')
        self.assertEqual(cov.messages(self.game), ["boom", "hit"])

    def test_instrument(self):
        cov.instrument(self.game)
        main = self.read("main.spx")
        # 每个函数 / 事件处理的第一行插一句 tCov
        for name in ("main.spx:addScore", "main.spx:onStart #2", 'main.spx:onMsg "hit"', "main.spx:onKey KeySpace"):
            self.assertIn(f"\ttCov(`{name}`)\n", main)
        self.assertIn("func addScore(n int) {\n\ttCov(`main.spx:addScore`)\n\tscore += n\n", main)
        # covSeen 放进第一个 var 块，tCov 放在第一个 func 前面
        self.assertTrue(main.startswith("var (\n\tcovSeen map[string]bool"))
        self.assertLess(main.index("func tCov(id string)"), main.index("func addScore"))
        tank = self.read("Tank.spx")
        self.assertIn("\ttCov(`Tank.spx:onCloned`)\n", tank)
        self.assertNotIn("func tCov", tank)    # 精灵里不加函数和字段
        # 插桩以后再找一遍，点还是那些（tCov 自己不算）
        pts = cov.all_points(self.game)
        self.assertEqual(len([n for n in pts if n.startswith("main.spx:")]), 6 + 1)
        self.assertIn("main.spx:tCov", pts)


class Logs(Fixture):
    def log(self, run, suite, lines):
        return self.write(os.path.join(run, suite, "run.log"), "\n".join(lines) + "\n", base=self.dir)

    def test_covered_in(self):
        p = self.log("r1", "a", ["COV main.spx:reset", "noise COV x", "COV main.spx:onStart #1  ", "TEST PASS T01 x"])
        self.assertEqual(cov.covered_in([p]), {"main.spx:reset", "main.spx:onStart #1"})

    def test_baseline_marks_unstable(self):
        self.log("r1", "a", ["COV main.spx:reset", "COV Tank.spx:fire", "COV gone.spx:old"])
        self.log("r2", "a", ["COV main.spx:reset"])
        out = os.path.join(self.dir, "baseline.json")
        pts = cov.all_points(self.game)
        with mock.patch.object(cov, "all_points", lambda: pts):
            data = cov.make_baseline(out, [os.path.join(self.dir, "r1"), os.path.join(self.dir, "r2")])
        self.assertEqual(data["covered"], ["main.spx:reset"])
        self.assertEqual(data["unstable"], ["Tank.spx:fire"])     # 只有一次覆盖到
        self.assertEqual(data["runs"], 2)
        self.assertNotIn("gone.spx:old", data["covered"] + data["unstable"])   # 不存在的点不记
        with open(out, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["points"], sorted(pts))

    def test_compare(self):
        pts = cov.all_points(self.game)
        base = {"points": sorted(n for n in pts if n != "main.spx:addScore"),   # addScore 是“新加的”
                "covered": ["main.spx:reset", "Tank.spx:fire"], "unstable": ["main.spx:onStart #2"]}
        bp = self.write("baseline.json", json.dumps(base), base=self.dir)
        with mock.patch.object(cov, "all_points", lambda: pts):
            lines, ok = cov.compare({"main.spx:reset", "Tank.spx:fire", "main.spx:addScore"}, bp)
            self.assertTrue(ok, lines)
            text = "\n".join(lines)
            self.assertIn("没有退步", text)
            self.assertIn("main.spx:onStart #2", text)          # 不稳定的没覆盖到：只提一句，不算退步

            lines, ok = cov.compare({"main.spx:addScore"}, bp)  # 丢了 reset 和 fire
            self.assertFalse(ok)
            self.assertIn("- `main.spx:reset`", lines)

            lines, ok = cov.compare({"main.spx:reset", "Tank.spx:fire"}, bp)   # 新加的 addScore 没人执行
            self.assertFalse(ok)
            self.assertIn("- `main.spx:addScore`", lines)

            # 新加的按键处理不要求覆盖（无界面测试里触发不了）
            base["points"] = sorted(n for n in pts if n != "main.spx:onKey KeySpace")
            self.write("baseline.json", json.dumps(base), base=self.dir)
            lines, ok = cov.compare({"main.spx:reset", "Tank.spx:fire", "main.spx:addScore"}, bp)
            self.assertTrue(ok, lines)


if __name__ == "__main__":
    unittest.main()
