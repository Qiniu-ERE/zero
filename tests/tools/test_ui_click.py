"""Q08：点击不会被盖在按钮上面的小部件吞掉（见 docs/v6/TEST_PLAN.md）

spx 一次点击只交给最上层的那一个精灵（spx 的 inputManager.onLeftButtonDown → findClickTarget）。
三选一卡片、车库涂装、排行榜选项卡这些 UI 克隆正好盖在画面的按钮上；它们的 onClick 要是什么都不做，
点击就被吞掉了（v6.0.0 的问题：鼠标、手机都点不动三选一，手机上会卡住）。
无界面测试里触发不了真实点击，所以这里检查 UI.spx 的 onClick：没有专门处理的克隆都交给 clickScreen。
"""
import os
import re
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def on_click_body():
    with open(os.path.join(ROOT, "TankBattle", "UI.spx"), encoding="utf-8") as f:
        src = f.read()
    m = re.search(r"^onClick => \{\n(.*?)^\}", src, re.S | re.M)
    return m.group(1)


class UiClick(unittest.TestCase):
    def test_Q08_widgets_forward_clicks(self):
        body = on_click_body()
        m = re.search(r"default:\n(.*?)(?:\n\tcase |\n\t\}\n)", body, re.S)
        self.assertIsNotNone(m, "onClick 要有 default 分支")
        self.assertIn("clickScreen", m.group(1), "没有专门处理的克隆，点击要交给 clickScreen")

    def test_Q08_only_known_kinds_handled_specially(self):
        """专门处理的只有语言按钮、广告位、暂停按钮、每日挑战标签；其余（kPick、kGarage、kRanks、kLbNum、kShare、kToast……）都走 default"""
        cases = re.findall(r"\tcase ([^:]+):", on_click_body())
        kinds = {k.strip() for c in cases for k in c.split(",")}
        self.assertEqual(kinds, {"kLang", "kAd", "kPauseBtn", "kDailyTag"})


if __name__ == "__main__":
    unittest.main()
