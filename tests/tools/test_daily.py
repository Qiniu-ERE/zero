"""D01~D03：每日挑战的地图生成器（tools/levels/daily.py），见 docs/v6/TEST_PLAN.md

游戏里的生成器（main.spx 的 dailyRows）和这里逐格相同，由引擎内测试 tests/spx/daily.spx 读 tests/data/daily_maps.txt 比较。
"""
import os
import re
import sys
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "levels"))

import check  # noqa: E402
import daily  # noqa: E402


class Daily(unittest.TestCase):
    def test_D01_deterministic_and_varied(self):
        self.assertEqual(daily.daily_rows(20800), daily.daily_rows(20800), "同一天必须是同一张图")
        maps = {"".join(daily.daily_rows(d)) for d in range(20758, 20758 + 30)}
        self.assertGreater(len(maps), 25, "30 天里地图基本不重复")
        self.assertEqual(daily.lcg(1), 1103527590)

    def test_D02_365_maps_pass_check(self):
        for d in range(daily.EPOCH + 1, daily.EPOCH + 1 + daily.DAYS):
            rows = daily.daily_rows(d)
            self.assertEqual(check.problems(rows), [], f"第 {d} 天的地图不合格")
            self.assertEqual(daily.map_problem("".join(rows)), 0)

    def test_D03_data_file_up_to_date(self):
        with open(daily.DATA, encoding="utf-8") as f:
            text = f.read()
        blocks = re.findall(r"^(\d+)\n((?:[.BSWGE]{13}\n){13})", text, re.M)
        self.assertEqual(len(blocks), daily.DAYS)
        for d, rows in blocks:
            self.assertEqual(rows.split(), daily.daily_rows(int(d)),
                             f"tests/data/daily_maps.txt 过期了（第 {d} 天）：运行 python3 tools/levels/daily.py --write")

    def test_Q04_daily_maps_leave_room_for_share_card(self):
        # 分享战报是在每日挑战的结算画面上打开的（地图格子还在）：常驻 UI 约 95 个 + 战报 36 个 + 坦克子弹爆炸 30 个，
        # 全部精灵最多 300 个克隆（见 tests/spx/budget.spx），所以每日挑战的地图不能超过 130 格
        most = max(sum(ch != "." for ch in "".join(daily.daily_rows(d))) for d in range(daily.EPOCH + 1, daily.EPOCH + 1 + daily.DAYS))
        self.assertLessEqual(most, 130)

    def test_D03_constants_match_game(self):
        with open(os.path.join(ROOT, "TankBattle", "main.spx"), encoding="utf-8") as f:
            src = f.read()
        self.assertEqual(int(re.search(r"dailyEpoch\s*=\s*(\d+)", src).group(1)), daily.EPOCH)
        body = re.search(r"func dailyRows\(d int\) \[\]string \{(.*?)\n\}", src, re.S).group(1)
        for name, want in (("wb", daily.WB), ("ws", daily.WS), ("ww", daily.WW), ("dOdd", daily.D_ODD), ("dEven", daily.D_EVEN)):
            got = [int(x) for x in re.search(name + r" := \[\]int\{([^}]*)\}", body).group(1).split(",")]
            self.assertEqual(got, want, f"{name} 和 main.spx 不一致")
        self.assertIn("d*7919 + 12345", body)


if __name__ == "__main__":
    unittest.main()
