"""V01~V06：敌我区分（docs/v6/PLAN.md 第一节）。直接读 TankBattle/assets 里生成好的造型，不需要 fontTools。

规则：我方亮色、圆角车身、圆炮塔；敌方统一枪灰色车身 + 红色标识（警示条、炮口、“眼睛”），精英的标识色是紫色；
深灰和红色只留给敌方，我方的颜色（以后的涂装也一样）不能落进这个色域。
"""
import colorsys
import json
import os
import re
import sys
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SPRITES = os.path.join(ROOT, "TankBattle", "assets", "sprites")
sys.path.insert(0, os.path.join(ROOT, "tools", "assets"))

FOE_RED = "#ff3b30"
ELITE = "#c46bff"
HULL_MAIN = "#5b6271"
PLAYERS = {"player": ("#ffd23a", "#b8860b", "#fff3b0"), "player2": ("#4fe3c1", "#1f7a66", "#c9fff1")}
KINDS = ("basic", "fast", "heavy")


def read(*parts):
    with open(os.path.join(SPRITES, *parts), encoding="utf-8") as f:
        return f.read()


def colors(svg):
    return {c.lower() for c in re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{6})"', svg)}


def foe_domain(hex_color):
    """敌方专用的色域：低饱和的深灰（枪灰色车身）或者红色"""
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    gray = s < 0.25 and l < 0.6
    red = s > 0.5 and (h < 15 / 360 or h > 345 / 360) and 0.25 < l < 0.8
    return gray or red


class Iff(unittest.TestCase):
    def test_V01_modern_enemies_gunmetal_red(self):
        for k in KINDS:
            c = colors(read("Enemy", f"{k}_m.svg"))
            self.assertIn(HULL_MAIN, c, f"{k}_m 要用枪灰色车身")
            self.assertIn(FOE_RED, c, f"{k}_m 要有红色标识")
            for p in PLAYERS.values():
                self.assertFalse(c & set(p), f"{k}_m 不能用我方的颜色")

    def test_V02_elites_purple(self):
        for k in KINDS:
            c = colors(read("Enemy", f"{k}_e_m.svg"))
            self.assertIn(HULL_MAIN, c, f"精英 {k} 也是敌方车身")
            self.assertIn(ELITE, c, f"精英 {k} 的标识是紫色")
            self.assertNotIn(FOE_RED, c, f"精英 {k} 不再用红色标识")
        for k in KINDS:  # 经典画风的精英：紫色像素坦克
            self.assertIn("#9a5ad0", colors(read("Enemy", f"{k}_e.svg")), f"经典画风的精英 {k} 是紫色")

    def test_V03_classic_enemies_silver_red_eye(self):
        shapes = set()
        for k in KINDS:
            svg = read("Enemy", f"{k}.svg")
            c = colors(svg)
            self.assertIn("#9a9aa2", c, f"经典画风的 {k} 是银灰色")
            self.assertIn(FOE_RED, c, f"经典画风的 {k} 有红色眼睛和炮口")
            self.assertFalse(c & {"#e8c020", "#ffe680", "#3cb44b"}, f"经典画风的 {k} 不能用 1P / 2P 的颜色")
            shapes.add(re.sub(r"#[0-9a-fA-F]{6}", "#", svg))
        self.assertEqual(len(shapes), 3, "三种敌人的外形要各不相同（种类看外形，不靠颜色）")

    def test_V04_player_colors_outside_foe_domain(self):
        for name, cols in PLAYERS.items():
            self.assertFalse(foe_domain(cols[0]), f"{name} 的主色落进了敌方色域")
            self.assertIn(cols[0], colors(read("Player", f"{name}_m.svg")))
        self.assertTrue(foe_domain(HULL_MAIN) and foe_domain(FOE_RED), "色域判断本身要认得敌方的颜色")
        import build  # 生成器里的我方颜色和这里一致
        self.assertEqual(build.TANKS, PLAYERS)
        self.assertEqual((build.FOE_RED, build.ELITE, build.HULL[0]), (FOE_RED, ELITE, HULL_MAIN))

    def test_V05_bullets_yellow_vs_red(self):
        mine = read("PBullet", "bullet_m.svg")
        theirs = read("EBullet", "bullet_m.svg")
        self.assertIn("#ffe27a", mine.lower())
        self.assertIn("#ff2a2a", theirs.lower())

    def test_V06_costume_tables(self):
        with open(os.path.join(SPRITES, "Enemy", "index.json"), encoding="utf-8") as f:
            names = {c["name"] for c in json.load(f)["costumes"]}
        want = {k + e + m for k in KINDS for e in ("", "_e") for m in ("", "_m")}
        self.assertEqual(names, want, "Enemy 的造型表：三种 × 普通 / 精英 × 经典 / 现代")
        with open(os.path.join(SPRITES, "UI", "index.json"), encoding="utf-8") as f:
            ui = {c["name"] for c in json.load(f)["costumes"]}
        self.assertTrue({"ally_1", "ally_2"} <= ui, "UI 里有 1P / 2P 的我方标识")
        self.assertIn("#ffd23a", read("UI", "ally_1.svg"))
        self.assertIn("#4fe3c1", read("UI", "ally_2.svg"))


if __name__ == "__main__":
    unittest.main()
