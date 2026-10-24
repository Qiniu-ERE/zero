"""把文字转成 SVG 路径（字形轮廓），游戏里的文字都用它生成。

为什么不用字体：spx 运行时要靠项目字体渲染文字，字体里缺字就会显示成方块或乱码；
把文字烘焙成路径之后，游戏运行时完全不依赖字体，也就不可能出现乱码。
字体用 Noto Sans SC（SIL OFL 1.1），固定到 google/fonts 的某个提交并校验 sha256。
"""
import hashlib
import os
import urllib.request

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache")
FONT_URL = "https://raw.githubusercontent.com/google/fonts/e7db6ca603fd4862010383ff17ffd6cc4ffac1c0/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
FONT_SHA256 = "a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da"
WEIGHTS = {"medium": 500, "bold": 800}


class MissingGlyph(Exception):
    pass


def _variable_font():
    path = os.path.join(CACHE, "NotoSansSC-VF.ttf")
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        print("downloading Noto Sans SC ...")
        urllib.request.urlretrieve(FONT_URL, path + ".tmp")
        os.replace(path + ".tmp", path)
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    if digest != FONT_SHA256:
        raise SystemExit(f"字体校验失败：{path} 的 sha256 是 {digest}，请删除后重新下载")
    return path


class Font:
    def __init__(self, weight):
        path = os.path.join(CACHE, f"NotoSansSC-{WEIGHTS[weight]}.ttf")
        if not os.path.exists(path):
            vf = TTFont(_variable_font())
            instancer.instantiateVariableFont(vf, {"wght": WEIGHTS[weight]}, inplace=True)
            vf.save(path)
        self.font = TTFont(path)
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.hmtx = self.font["hmtx"]
        self.upem = self.font["head"].unitsPerEm

    def check(self, text):
        missing = [c for c in text if not c.isspace() and ord(c) not in self.cmap]
        if missing:
            raise MissingGlyph("缺字（会显示为乱码）: " + " ".join(f"{c}(U+{ord(c):04X})" for c in missing))

    def width(self, text, size):
        self.check(text)
        k = size / self.upem
        return sum(self.hmtx[self.cmap[ord(c)]][0] for c in text) * k

    def path(self, text, size, x, y, anchor="start"):
        """返回 (路径, 宽度)。(x, y) 是基线位置，anchor 可以是 start / middle / end"""
        w = self.width(text, size)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        k = size / self.upem
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        pen_x = x
        for c in text:
            name = self.cmap[ord(c)]
            self.glyphs[name].draw(TransformPen(pen, (k, 0, 0, -k, pen_x, y)))
            pen_x += self.hmtx[name][0] * k
        return pen.getCommands(), w


_fonts = {}


def font(weight="medium"):
    if weight not in _fonts:
        _fonts[weight] = Font(weight)
    return _fonts[weight]


def text(x, y, s, size, fill, bold=False, anchor="start", opacity=None):
    """SVG <path> 形式的文字，用法和 <text> 类似"""
    d, _ = font("bold" if bold else "medium").path(s, size, x, y, anchor)
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    return f'<path d="{d}" fill="{fill}"{op}/>'


def width(s, size, bold=False):
    return font("bold" if bold else "medium").width(s, size)
