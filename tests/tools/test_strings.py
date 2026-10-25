"""T04、T08：中英文案表 tools/assets/strings.py，以及游戏代码引用的文案 key（见 docs/v4/TEST_PLAN.md 第 3.1 节）"""
import ast
import glob
import json
import os
import re
import sys
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
STRINGS_PY = os.path.join(ROOT, "tools", "assets", "strings.py")
sys.path.insert(0, os.path.dirname(STRINGS_PY))
from strings import STRINGS  # noqa: E402

LAST_STAGE = 8


def game_source():
    out = {}
    for p in glob.glob(os.path.join(ROOT, "TankBattle", "*.spx")):
        with open(p, encoding="utf-8") as f:
            out[os.path.basename(p)] = f.read()
    return out


def ui_costumes():
    with open(os.path.join(ROOT, "TankBattle", "assets", "sprites", "UI", "index.json"), encoding="utf-8") as f:
        return {c["name"] for c in json.load(f)["costumes"]}


def referenced_msg_keys():
    """游戏代码里用到的 msg.* 文案。写成 "msg.stage" + 关卡号、"msg.ed.copy" + 关卡号的，展开成每一关"""
    keys = set()
    for src in game_source().values():
        for k in re.findall(r'"(msg\.[a-z0-9.]+)"', src):
            if k == "msg.stage":
                keys |= {f"msg.stage{n}" for n in range(2, LAST_STAGE + 1)}
            elif k == "msg.ed.copy":
                keys |= {f"msg.ed.copy{n}" for n in range(1, LAST_STAGE + 1)}
            else:
                keys.add(k)
    return keys


class Table(unittest.TestCase):
    def test_T04_zh_and_en_not_empty(self):
        for key, value in STRINGS.items():
            with self.subTest(key=key):
                self.assertIsInstance(value, tuple)
                self.assertEqual(len(value), 2, "应该是 (中文, English)")
                zh, en = value
                self.assertTrue(zh.strip(), "中文是空的")
                self.assertTrue(en.strip(), "English 是空的")

    def test_T04_no_duplicate_keys(self):
        # Python 的字典字面量里写重复的 key 不会报错，后一个会悄悄覆盖前一个，所以直接读源码检查
        with open(STRINGS_PY, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        seen, dup = set(), []
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for k in node.keys:
                    if isinstance(k, ast.Constant):
                        (dup.append(k.value) if k.value in seen else seen.add(k.value))
        self.assertEqual(dup, [], "strings.py 里有重复的 key")

    def test_T04_english_has_no_chinese(self):
        # 允许的例外：语言按钮上的“中”
        allow = {"lang.zh", "hint.lang"}
        for key, (_, en) in STRINGS.items():
            if key in allow:
                continue
            with self.subTest(key=key):
                self.assertIsNone(re.search(r"[一-鿿]", en), f"English 文案里有中文：{en}")


class GameReferences(unittest.TestCase):
    def test_T08_msg_keys_exist(self):
        missing = sorted(k for k in referenced_msg_keys() if k not in STRINGS)
        self.assertEqual(missing, [], "游戏代码引用了 strings.py 里没有的文案")

    def test_T08_msg_keys_have_costumes(self):
        # 提示条的造型由 build.py 生成，名字是 <key>_zh / <key>_en
        names = ui_costumes()
        missing = sorted(f"{k}_{lang}" for k in referenced_msg_keys() for lang in ("zh", "en") if f"{k}_{lang}" not in names)
        self.assertEqual(missing, [], "提示条缺少造型，需要重新运行 build.py")

    def test_T08_stage_names_exist(self):
        for n in range(1, LAST_STAGE + 1):
            with self.subTest(stage=n):
                self.assertIn(f"stage.{n}", STRINGS)


if __name__ == "__main__":
    unittest.main()
