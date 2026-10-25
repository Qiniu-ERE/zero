"""T05~T07：文字转路径和美术生成器（需要 fontTools 和字体，见 tools/assets/requirements.txt；没装就跳过）

T06 在临时目录里复制一份 TankBattle/ 和 tools/assets/ 运行 build.py，和仓库里的文件逐个比较，
不会改动仓库。字体缓存（tools/assets/.cache）会复制过去，避免重复下载。
"""
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ASSETS_TOOLS = os.path.join(ROOT, "tools", "assets")
sys.path.insert(0, ASSETS_TOOLS)

try:
    import fontTools  # noqa: F401
    HAVE_FONTTOOLS = True
except ImportError:
    HAVE_FONTTOOLS = False

need_fonttools = unittest.skipUnless(HAVE_FONTTOOLS, "没有安装 fontTools（pip install -r tools/assets/requirements.txt）")


def diff_tree(a, b):
    """返回两个目录里内容不同、或者只在一边存在的文件（相对路径）"""
    out = []
    cmp = filecmp.dircmp(a, b, ignore=[".temp", ".DS_Store"])

    def walk(c, rel):
        out.extend(os.path.join(rel, n) for n in c.left_only + c.right_only + c.funny_files)
        _, mismatch, errors = filecmp.cmpfiles(c.left, c.right, c.common_files, shallow=False)
        out.extend(os.path.join(rel, n) for n in mismatch + errors)
        for name, sub in c.subdirs.items():
            walk(sub, os.path.join(rel, name))

    walk(cmp, "")
    return sorted(out)


def build_copy(dst):
    shutil.copytree(os.path.join(ROOT, "TankBattle"), os.path.join(dst, "TankBattle"), ignore=shutil.ignore_patterns(".temp"))
    shutil.copytree(ASSETS_TOOLS, os.path.join(dst, "tools", "assets"), ignore=shutil.ignore_patterns("__pycache__"))
    r = subprocess.run([sys.executable, os.path.join(dst, "tools", "assets", "build.py")], capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError("build.py 运行失败：\n" + r.stdout + r.stderr)


@need_fonttools
class TextPath(unittest.TestCase):
    def test_T05_missing_glyph_raises(self):
        import textpath
        font = textpath.Font("medium")
        font.check("坦克大战 BATTLE CITY")  # 正常的文字不报错
        with self.assertRaises(textpath.MissingGlyph):
            font.check("坦克\U0001F600")  # 字体里没有表情符号


@need_fonttools
class Generated(unittest.TestCase):
    def test_T06_generated_files_up_to_date(self):
        with tempfile.TemporaryDirectory() as d:
            build_copy(d)
            changed = diff_tree(os.path.join(ROOT, "TankBattle"), os.path.join(d, "TankBattle"))
        self.assertEqual(changed, [], "生成的文件过期了：运行 python3 tools/assets/build.py 并提交生成结果")

    def test_T07_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            build_copy(a)
            build_copy(b)
            self.assertEqual(diff_tree(os.path.join(a, "TankBattle"), os.path.join(b, "TankBattle")), [])


if __name__ == "__main__":
    unittest.main()
