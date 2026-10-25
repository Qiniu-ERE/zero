"""E07（Python 这一半）：tests/data/editor_maps.txt 里每张地图的结论和 check.py 一致，并且文件是最新生成的。
另一半在 tests/spx/editor_parity.spx：游戏里的 edCheck() 对同一批地图给出相同的结论。"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA = os.path.join(ROOT, "tests", "data", "editor_maps.txt")
sys.path.insert(0, os.path.join(ROOT, "tools", "levels"))
import check  # noqa: E402


def read_maps(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for block in f.read().strip().split("\n\n"):
            lines = block.split("\n")
            out.append((lines[:13], lines[13]))
    return out


class EditorMaps(unittest.TestCase):
    def test_E07_verdicts_match_check_py(self):
        maps = read_maps(DATA)
        self.assertGreater(len(maps), 200)
        for k, (rows, verdict) in enumerate(maps):
            with self.subTest(map=k):
                self.assertEqual("bad" if check.problems(rows) else "ok", verdict)

    def test_E07_both_verdicts_present(self):
        verdicts = [v for _, v in read_maps(DATA)]
        self.assertGreater(verdicts.count("ok"), 50)
        self.assertGreater(verdicts.count("bad"), 50)

    def test_E07_file_is_up_to_date(self):
        # 重新生成一遍，和提交的文件比较（规则或锁定格改了却没重新生成，这里会失败）
        with open(DATA, encoding="utf-8") as f:
            committed = f.read()
        gen = os.path.join(ROOT, "tools", "test", "gen_editor_maps.py")
        with tempfile.TemporaryDirectory() as d:
            src = open(gen, encoding="utf-8").read().replace(
                'OUT = os.path.join(ROOT, "tests", "data", "editor_maps.txt")', f"OUT = {os.path.join(d, 'm.txt')!r}")
            script = os.path.join(d, "gen.py")
            with open(script, "w", encoding="utf-8") as f:
                f.write(src.replace('os.path.dirname(os.path.abspath(__file__)), "..", ".."', repr(ROOT)))
            subprocess.run([sys.executable, script], check=True, capture_output=True)
            with open(os.path.join(d, "m.txt"), encoding="utf-8") as f:
                self.assertEqual(f.read(), committed, "运行 python3 tools/test/gen_editor_maps.py 重新生成")


if __name__ == "__main__":
    unittest.main()
