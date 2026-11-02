"""K11~K12：车库的美术和游戏代码一致（docs/v6/PLAN.md 第三节）。需要 fontTools（生成器 import 了 textpath）。

- 涂装都是亮色，不能落进敌方色域（深灰和红色只留给敌方，见 test_iff.py 的 V04）
- 生成器里的价格、解锁等级、任务目标和 main.spx 一致（画面上写的数字和游戏里实际的规则对得上）
"""
import os
import re
import sys
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "assets"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import fontTools  # noqa: F401
    HAVE_FONTTOOLS = True
except ImportError:
    HAVE_FONTTOOLS = False

from test_iff import foe_domain  # noqa: E402


def main_spx():
    with open(os.path.join(ROOT, "TankBattle", "main.spx"), encoding="utf-8") as f:
        return f.read()


def int_list(func):
    """main.spx 里形如 func xxx(...) int { return []int{...}[i] } 的表"""
    m = re.search(r"func " + func + r"\(.*?\{.*?\[\]int\{([^}]*)\}", main_spx(), re.S)
    return [int(x) for x in m.group(1).split(",")]


@unittest.skipUnless(HAVE_FONTTOOLS, "没有安装 fontTools（pip install -r tools/assets/requirements.txt）")
class Garage(unittest.TestCase):
    def test_K11_skins_bright(self):
        import build
        for i, cols in enumerate(build.SKINS):
            self.assertFalse(foe_domain(cols[0]), f"涂装 {i} 的主色 {cols[0]} 落进了敌方色域")
        self.assertEqual(len(build.SKINS), int(re.search(r"skinCount\s*=\s*(\d+)", main_spx()).group(1)))

    def test_K12_tables_match_game(self):
        import build
        self.assertEqual(build.SKIN_PRICES, int_list("skinPrice"))
        self.assertEqual(build.TASK_TARGETS, int_list("taskTarget")[1:])
        src = main_spx()
        body = re.search(r"func chipUnlockLv\(id int\) int \{(.*?)\n\}", src, re.S).group(1)
        got = {k.lower(): int(v) for k, v in re.findall(r"case c(\w+):\s*return (\d+)", body)}
        self.assertEqual(got, build.CHIP_UNLOCK)
        self.assertEqual(build.MAX_CMD, int(re.search(r"maxCmdLevel\s*=\s*(\d+)", src).group(1)))


if __name__ == "__main__":
    unittest.main()
