#!/usr/bin/env python3
"""生成 TankBattle 的美术资源（SVG 造型）。

用法：pip install -r tools/assets/requirements.txt && python3 tools/assets/build.py

约束：spx 用 LunaSVG 光栅化 SVG，不支持 filter（阴影、模糊），所以阴影都画成半透明图形；
文字一律通过 textpath 转成路径，运行时不依赖字体。
布局：舞台 480x360，战场 13x13 格、每格 24px，左上角在 SVG 坐标 (12, 30)，右侧面板 x=336 起。
"""
import json
import math
import os
import re
import sys

from strings import STRINGS
from textpath import text, width

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(ROOT, "TankBattle", "assets")

W, H = 480, 360
C = 24
FX, FY = 12, 30
PX, PY, PW, PH = 336, 26, 132, 320


def svg(w, h, body, defs="", res=1):
    """res 是 bitmapResolution：图片按 res 倍尺寸声明，引擎会按 res 倍光栅化再缩回逻辑尺寸，文字更清晰"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*res:g}" height="{h*res:g}" viewBox="0 0 {w:g} {h:g}">'
            f'<defs>{defs}</defs>{body}</svg>')


def write(rel, content):
    path = os.path.join(ASSETS, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return rel


def lin(id, c1, c2, vertical=True):
    x2, y2 = ("0", "1") if vertical else ("1", "0")
    return f'<linearGradient id="{id}" x1="0" y1="0" x2="{x2}" y2="{y2}"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>'


def rad(id, stops):
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<radialGradient id="{id}" cx="0.5" cy="0.5" r="0.5">{s}</radialGradient>'


# ---------- 背景 ----------
def backdrop_modern():
    defs = (lin("bg", "#121826", "#080b12")
            + rad("ground", [(0, "#2b3838", 1), (0.6, "#1d2729", 1), (1, "#111819", 1)])
            + rad("vig", [(0.6, "#000", 0), (1, "#000", 0.45)])
            + lin("panel", "#182031", "#10151f"))
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>',
         f'<rect x="{FX-4}" y="{FY-4}" width="{13*C+8}" height="{13*C+8}" rx="6" fill="#0a0e14" stroke="#2a3446" stroke-width="0.8"/>',
         f'<rect x="{FX}" y="{FY}" width="{13*C}" height="{13*C}" fill="url(#ground)"/>']
    for i in range(1, 13):
        s.append(f'<path d="M{FX+i*C} {FY}V{FY+13*C}M{FX} {FY+i*C}H{FX+13*C}" stroke="#fff" stroke-opacity="0.035" stroke-width="0.5"/>')
    # 地面上的一些小石子，让地面不那么平
    for i in range(60):
        x = FX + (i * 53) % (13 * C)
        y = FY + (i * 97) % (13 * C)
        s.append(f'<circle cx="{x}" cy="{y}" r="{0.5 + (i % 3) * 0.3:.1f}" fill="#fff" fill-opacity="0.05"/>')
    s.append(f'<rect x="{FX}" y="{FY}" width="{13*C}" height="{13*C}" fill="url(#vig)"/>')
    s.append(f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="6" fill="url(#panel)" stroke="#263046" stroke-width="0.6"/>')
    return svg(W, H, "".join(s), defs)


def backdrop_classic():
    s = [f'<rect width="{W}" height="{H}" fill="#6B6B6B"/>',
         f'<rect x="{FX}" y="{FY}" width="{13*C}" height="{13*C}" fill="#000"/>',
         f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="6" fill="#5A5A5A"/>']
    return svg(W, H, "".join(s))


# ---------- 地形 ----------
def brick_m(cracked=False):
    h = 3  # 墙体厚度（伪 3D）
    defs = lin("t", "#df7448", "#b04a27")
    s = [f'<rect x="0" y="{C-h}" width="{C}" height="{h}" fill="#6e2a12"/>',
         f'<rect x="0" y="0" width="{C}" height="{C-h}" fill="url(#t)"/>']
    bh = (C - h) / 4
    for i in range(4):
        y = i * bh
        if i:
            s.append(f'<rect x="0" y="{y-0.35:.2f}" width="{C}" height="0.7" fill="#7a2e14"/>')
        off = 0 if i % 2 == 0 else C / 4
        for k in range(3):
            x = off + k * C / 2
            if 0 < x < C:
                s.append(f'<rect x="{x-0.35:.2f}" y="{y:.2f}" width="0.7" height="{bh:.2f}" fill="#7a2e14"/>')
    s.append(f'<rect x="0" y="0" width="{C}" height="0.9" fill="#ffb08a" fill-opacity="0.6"/>')
    if cracked:
        s.append('<path d="M5 2l3.5 4.5-2 3.5 4.5 4-1.5 4.5M14 1l-2 5.5 4 3" stroke="#2a0d03" stroke-width="1.1" fill="none"/>')
        s.append('<rect x="16" y="11" width="4" height="3" fill="#1d2729"/>')
    return svg(C, C, "".join(s), defs)


def steel_m():
    h = 3
    defs = lin("t", "#c9d4de", "#55616c")
    s = [f'<rect x="0" y="{C-h}" width="{C}" height="{h}" fill="#2f363d"/>',
         f'<rect x="0" y="0" width="{C}" height="{C-h}" rx="1" fill="url(#t)"/>',
         f'<rect x="3" y="2.5" width="{C-6}" height="{C-h-5}" rx="1" fill="none" stroke="#e8f0f6" stroke-opacity="0.5" stroke-width="0.6"/>']
    for x, y in ((3.5, 3), (C - 3.5, 3), (3.5, C - h - 3), (C - 3.5, C - h - 3)):
        s.append(f'<circle cx="{x}" cy="{y}" r="1" fill="#3a434c"/>')
    s.append(f'<path d="M2 {C-h-2}L{C-9} 2" stroke="#fff" stroke-opacity="0.25" stroke-width="3"/>')
    return svg(C, C, "".join(s), defs)


EAGLE = "M12 4.5l2.8 3.7 5.5-1.8-2.8 5.5 3.7 1.8-6.5 1.8-2.7 4.6-2.7-4.6-6.5-1.8 3.7-1.8-2.8-5.5 5.5 1.8z"


def eagle_m():
    defs = lin("g", "#ffe27a", "#f29a00")
    s = ['<rect x="0.5" y="0.5" width="23" height="23" rx="4" fill="#1b2a3a" stroke="#3ee8ff" stroke-opacity="0.75" stroke-width="0.8"/>',
         f'<path d="{EAGLE}" fill="url(#g)"/>']
    return svg(C, C, "".join(s), defs)


def broken_m():
    s = ['<rect x="0.5" y="0.5" width="23" height="23" rx="4" fill="#1a1d22" stroke="#ff4a3a" stroke-opacity="0.6" stroke-width="0.8"/>',
         f'<path d="{EAGLE}" fill="#4a4f57"/>',
         '<path d="M4 6l5 5-2 4 6 5M20 5l-5 6 3 3" stroke="#0b0d10" stroke-width="1.4" fill="none"/>',
         '<circle cx="8" cy="18" r="2" fill="#2a2d33"/><circle cx="17" cy="17" r="1.5" fill="#2a2d33"/>']
    return svg(C, C, "".join(s))


# ---------- 坦克（spx 和 Scratch 一样：造型按朝右画，heading 90 时不旋转） ----------
TANKS = {
    "player": ("#ffd23a", "#b8860b", "#fff3b0"),
    "basic": ("#ff5a4a", "#9c1f16", "#ffc2b8"),
    "fast": ("#4aa8ff", "#1c4f8f", "#c8e6ff"),
    "heavy": ("#6fd06a", "#2e6e2a", "#d2f5cf"),
}


def tank_body(main, dark, light, heavy=False):
    """朝上的坦克图形（24x24），返回 (defs, body)"""
    defs = rad("sh", [(0, "#000", 0.45), (0.7, "#000", 0.2), (1, "#000", 0)])
    s = ['<ellipse cx="12.8" cy="13.4" rx="11.2" ry="10.6" fill="url(#sh)"/>']
    for x in (1, 17.5):  # 履带
        s.append(f'<rect x="{x}" y="2.5" width="5.5" height="20" rx="2" fill="#1e1e22"/>')
        for i in range(7):
            s.append(f'<rect x="{x+0.5}" y="{3.4+i*2.8:.1f}" width="4.5" height="1.3" fill="#44464c"/>')
    s.append(f'<rect x="5.8" y="4.5" width="12.4" height="17" rx="2.4" fill="{dark}"/>')
    s.append(f'<rect x="6.3" y="4.5" width="11.4" height="15.4" rx="2.4" fill="{main}"/>')
    s.append(f'<rect x="6.3" y="4.5" width="11.4" height="2.3" rx="1" fill="{light}" fill-opacity="0.6"/>')
    if heavy:  # 重型坦克：车身加装甲板
        s.append(f'<rect x="6.8" y="16" width="10.4" height="3" rx="0.8" fill="{dark}"/>')
    s.append(f'<rect x="10.3" y="0.8" width="3.4" height="11" rx="1" fill="{dark}"/>')
    s.append(f'<rect x="11" y="0.8" width="1.2" height="10" fill="{light}" fill-opacity="0.7"/>')
    s.append('<rect x="9.6" y="0" width="4.8" height="2.4" rx="0.7" fill="#2a2a2e"/>')
    s.append(f'<circle cx="12" cy="13" r="5" fill="{dark}"/><circle cx="12" cy="12.4" r="4.6" fill="{main}"/>')
    s.append(f'<circle cx="10.6" cy="11" r="1.7" fill="{light}" fill-opacity="0.8"/>')
    return defs, "".join(s)


def tank_m(main, dark, light, heavy=False):
    defs, body = tank_body(main, dark, light, heavy)
    return svg(C, C, f'<g transform="rotate(90 12 12)">{body}</g>', defs)


# ---------- 子弹与爆炸 ----------
def bullet_m(core, glow):
    defs = rad("g", [(0, "#ffffff", 1), (0.35, core, 1), (0.7, glow, 0.6), (1, glow, 0)])
    return svg(6, 6, '<circle cx="3" cy="3" r="3" fill="url(#g)"/>', defs)


def boom_m(phase):
    r = [9, 15, 19][phase]
    defs = rad("f", [(0, "#fffbe6", 1), (0.25, "#ffd54a", 1), (0.55, "#ff6a1a", 0.85), (1, "#7a1a00", 0)])
    s = [f'<circle cx="20" cy="20" r="{r}" fill="url(#f)" fill-opacity="{[1, 0.95, 0.6][phase]}"/>']
    if phase:
        s.append(f'<circle cx="20" cy="20" r="{r-1}" fill="none" stroke="#ffd27a" stroke-opacity="{0.6 - phase*0.2:.1f}" stroke-width="1.2"/>')
        for i in range(8):
            a = math.radians(i * 45 + 20 * phase)
            d = r * (0.75 + 0.15 * (i % 2))
            x, y = 20 + math.cos(a) * d, 20 + math.sin(a) * d
            s.append(f'<rect x="{x-1:.1f}" y="{y-1:.1f}" width="{2+i%2}" height="2" fill="{["#ffcf4a", "#ff7a2a", "#5a5a5a"][i%3]}"/>')
    return svg(40, 40, "".join(s), defs)


# ---------- HUD（文字全部转成路径；res=4 保证放大后清晰） ----------
HR = 4  # HUD 造型的 bitmapResolution
LANGS = ("zh", "en")
MUTED = "#8a96ad"


def tr(key, lang):
    return STRINGS[key][LANGS.index(lang)]


def text_costume(s, size, fill, bold, anchor, pad=1.0):
    """单行文字造型，返回 (svg, pivot)。pivot 是文字锚点（基线上的起点 / 中点 / 终点）"""
    w = width(s, size, bold)
    h = size * 1.45
    base = size * 1.1
    body = text(pad, base, s, size, fill, bold)
    ax = {"start": pad, "middle": pad + w / 2, "end": pad + w}[anchor]
    return svg(w + 2 * pad, h, body, res=HR), (ax, base)


# 标签：key -> (字号, 颜色, 粗体, 对齐)
LABELS = {
    "stage.1": (10, "#ffffff", True, "start"),
    "enemies": (7.5, MUTED, False, "end"),
    "score": (6.8, MUTED, True, "start"),
    "best": (6.8, MUTED, True, "start"),
    "lives": (6.8, MUTED, True, "start"),
}
# 按键提示：key -> 按键
HINTS = {"hint.move": "WASD", "hint.fire": "J", "hint.style": "T", "hint.lang": "L"}


def hint_costume(key, label):
    kw = width(key, 6.5, True) + 6
    body = (f'<rect x="0" y="0" width="{kw:.2f}" height="11" rx="2.5" fill="#ffffff" fill-opacity="0.1"/>'
            + text(kw / 2, 8.2, key, 6.5, "#ffffff", True, "middle")
            + text(kw + 5, 8.2, label, 6.8, MUTED))
    w = kw + 5 + width(label, 6.8) + 1
    return svg(w, 12, body, res=HR), (0, 8.2)


def toast_costume(s):
    tw = width(s, 9, True)
    w, h = tw + 24, 22
    body = (f'<rect x="0.5" y="0.5" width="{w-1:.2f}" height="{h-1}" rx="{(h-1)/2}" fill="#0b0f18" fill-opacity="0.88" stroke="#3ee8ff" stroke-opacity="0.5" stroke-width="0.8"/>'
            + text(w / 2, 14.6, s, 9, "#ffffff", True, "middle"))
    return svg(w, h, body, res=HR), (w / 2, h / 2)


def toggle_costume(lang):
    hx = 1 if lang == "zh" else 20
    body = ('<rect x="0.3" y="0.3" width="39.4" height="13.4" rx="6.7" fill="#ffffff" fill-opacity="0.06" stroke="#2c3850" stroke-width="0.6"/>'
            f'<rect x="{hx}" y="1" width="19" height="12" rx="6" fill="#3ee8ff" fill-opacity="0.9"/>'
            + text(10.5, 10, "中", 7.5, "#06232b" if lang == "zh" else MUTED, True, "middle")
            + text(29.5, 10, "EN", 7.5, "#06232b" if lang == "en" else MUTED, True, "middle"))
    return svg(40, 14, body, res=HR), (20, 7)


# 数字样式：名字 -> (字号, 颜色)
NUM_STYLES = {"S": (18, "#ffffff"), "B": (8, "#ffe27a"), "C": (14, "#ffe27a")}
DIGITS = "0123456789"


def num_costumes():
    """数字造型：数字等宽（字形在格子里居中），逗号单独一个窄格。返回 (造型列表, 宽度表)"""
    out, widths = [], {}
    for st, (size, fill) in NUM_STYLES.items():
        dw = max(width(d, size, True) for d in DIGITS)
        cw = width(",", size, True)
        widths[st] = (dw, cw)
        for ch in DIGITS + ",":
            cell = cw if ch == "," else dw
            gx = (cell - width(ch, size, True)) / 2
            body = text(gx, size * 1.1, ch, size, fill, True)
            name = st + ("comma" if ch == "," else ch)
            out.append((name, svg(cell, size * 1.45, body, res=HR), (0, size * 1.1)))
    return out, widths


def icon_costumes():
    out = []
    for name, col in (("pip_on", "#ff5a4a"), ("pip_off", "#3a4256")):
        out.append((name, svg(4, 8, f'<rect width="4" height="8" rx="1" fill="{col}"/>', res=HR), (2, 4)))
    defs, body = tank_body(*TANKS["player"])
    for name, op in (("life_on", 1), ("life_off", 0.22)):
        out.append((name, svg(12, 12, f'<g opacity="{op}" transform="scale(0.5)">{body}</g>', defs, res=HR), (6, 6)))
    return out


def write_sprite(name, costumes, res=HR, x=0, y=0, visible=False):
    """写一个由生成器完全管理的精灵：造型文件 + index.json（会删掉不再使用的旧造型）"""
    d = os.path.join(ASSETS, "sprites", name)
    os.makedirs(d, exist_ok=True)
    keep = set()
    configs = []
    for cname, content, (px, py), *opt in costumes:
        r = opt[0] if opt else res  # 造型可以单独指定 bitmapResolution（全屏画面用 2，省内存）
        fname = re.sub(r"[^A-Za-z0-9_.-]", "_", cname) + ".svg"
        keep.add(fname)
        with open(os.path.join(d, fname), "w", encoding="utf-8") as f:
            f.write(content)
        configs.append({"name": cname, "path": fname, "x": round(px * r, 2), "y": round(py * r, 2), "bitmapResolution": r})
    for old in os.listdir(d):
        if old.endswith(".svg") and old not in keep:
            os.remove(os.path.join(d, old))
    cfg = {"costumes": configs, "costumeIndex": 0, "heading": 90, "isDraggable": False,
           "rotationStyle": "normal", "size": 1, "visible": visible, "x": x, "y": y}
    with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
    return len(costumes)


def update_generated_block(path, lines, name="widths"):
    """替换 .spx 文件里 // BEGIN GENERATED <name> 和 // END GENERATED <name> 之间的内容"""
    with open(path, encoding="utf-8") as f:
        src = f.read()
    pat = rf"(// BEGIN GENERATED {name}\n).*?(\t*// END GENERATED {name})"
    new, n = re.subn(pat, lambda m: m.group(1) + "".join(lines) + m.group(2), src, flags=re.S)
    if n != 1:
        sys.exit(f"{path} 里没有找到 GENERATED 区块")
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)


# ---------- 画面：主页、复活、模拟广告、结算，以及广告卡片 / 横幅 ----------
# 坐标都是 SVG 坐标（左上角原点，y 向下）。按钮区域记在 BUTTONS 里，生成到 UI.spx 的 hit()，
# 这样点击区域永远和画面一致。
GBLUE = "#1a73e8"  # 广告按钮统一用 Google 蓝，和游戏自己的橙色按钮区分
BUTTONS = {}       # 名字 -> (x, y, w, h)，SVG 坐标


def button(name, x, y, w, h):
    BUTTONS[name] = (x, y, w, h)


def chip(x, y, k, dark=False):
    """按键提示小方块，(x, y) 是左上角，返回 (svg, 宽度)"""
    w = width(k, 6, True) + 6
    fill, op, col = ("#000000", 0.25, "#ffffff") if dark else ("#ffffff", 0.12, "#ffffff")
    return (f'<rect x="{x:.2f}" y="{y}" width="{w:.2f}" height="10" rx="2.5" fill="{fill}" fill-opacity="{op}"/>'
            + text(x + w / 2, y + 7.4, k, 6, col, True, "middle")), w


def ad_badge(x, y, lang):
    s = tr("ad.badge", lang)
    w = width(s, 6, True) + 6
    return (f'<rect x="{x:.2f}" y="{y}" width="{w:.2f}" height="9" rx="2" fill="none" stroke="#f2c94c" stroke-width="0.6"/>'
            + text(x + w / 2, y + 6.8, s, 6, "#f2c94c", True, "middle")), w


def play_icon(x, y, col, k=1.0):
    return f'<path d="M{x-3*k:.2f} {y-4*k:.2f}L{x+4*k:.2f} {y}L{x-3*k:.2f} {y+4*k:.2f}Z" fill="{col}"/>'


def brand_logo(cx, cy, r):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{GBLUE}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r*0.43:.2f}" fill="#ffffff"/>')


def defs_ui():
    return (lin("cta", "#ff9a1a", "#ff5a1a", vertical=False) + lin("gold", "#ffe27a", "#f29a00")
            + lin("bgH", "#141b2b", "#07090f"))


def native_card(lang):
    """对局中右侧面板底部的原生广告卡（120x86）"""
    w, h = 120, 86
    b, _ = ad_badge(6, 6, lang)
    body = [f'<rect x="0.3" y="0.3" width="{w-0.6}" height="{h-0.6}" rx="6" fill="#ffffff" fill-opacity="0.04" stroke="#2c3850" stroke-width="0.6"/>', b,
            f'<path d="M{w-17} 7.5l5 3-5 3z" fill="none" stroke="#6b778f" stroke-width="0.7"/>',
            f'<path d="M{w-9} 8l5 5M{w-4} 8l-5 5" stroke="#6b778f" stroke-width="0.9"/>',
            '<rect x="6" y="21" width="20" height="20" rx="4" fill="#ffffff"/>', brand_logo(16, 31, 6),
            text(31, 29, tr("ad.brand", lang), 7.5, "#e6ecf5", True),
            text(31, 39, tr("ad.head", lang), 5.8, MUTED),
            f'<rect x="6" y="{h-22}" width="{w-12}" height="15" rx="7.5" fill="{GBLUE}"/>',
            text(w / 2, h - 12, tr("ad.cta", lang), 7.2, "#ffffff", True, "middle")]
    return svg(w, h, "".join(body), res=HR), (w / 2, h / 2)


CARD = (342, 250, 120, 86)       # 原生广告卡在屏幕上的位置
BANNER = (16, 316, 448, 32)      # 主页横幅的位置


def banner(lang):
    """主页底部横幅（Anchor Banner）"""
    w, h = BANNER[2], BANNER[3]
    b, bw = ad_badge(8, 11.5, lang)
    body = [f'<rect x="0.3" y="0.3" width="{w-0.6}" height="{h-0.6}" rx="6" fill="#ffffff" fill-opacity="0.04" stroke="#2c3850" stroke-width="0.6"/>', b,
            f'<rect x="{bw+14}" y="6" width="20" height="20" rx="4" fill="#ffffff"/>', brand_logo(bw + 24, 16, 6),
            text(bw + 42, 19.5, tr("ad.banner", lang), 7.8, "#c8d2e3"),
            f'<rect x="{w-84}" y="8" width="58" height="16" rx="8" fill="{GBLUE}"/>',
            text(w - 55, 18.8, tr("ad.cta", lang), 7, "#ffffff", True, "middle"),
            f'<path d="M{w-15} 6.5l5 3-5 3z" fill="none" stroke="#6b778f" stroke-width="0.7"/>',
            f'<path d="M{w-15} 19l5 5M{w-10} 19l-5 5" stroke="#6b778f" stroke-width="0.9"/>']
    return svg(w, h, "".join(body), res=HR), (w / 2, h / 2)


def home(lang):
    s = [f'<rect width="{W}" height="{H}" fill="url(#bgH)"/>',
         '<circle cx="330" cy="170" r="140" fill="#3ee8ff" fill-opacity="0.05"/><circle cx="330" cy="170" r="90" fill="#ffd23a" fill-opacity="0.05"/>']
    t = tr("title", lang)
    s.append(text(16, 46, t, 22, "#ffffff", True))
    s.append(text(16 + width(t, 22, True) + 6, 46, "2026", 22, "url(#gold)", True))
    s.append(text(16, 60, tr("subtitle", lang), 7.5, "#7f8ba3", True))
    # 开始按钮
    button("home.start", 16, 84, 170, 50)
    s.append('<rect x="16" y="84" width="170" height="50" rx="10" fill="url(#cta)"/>')
    s.append(text(28, 106, tr("home.start", lang), 13, "#ffffff", True))
    s.append(text(28, 122, tr("home.start.d", lang), 6.8, "#fff2e0"))
    c, cw = chip(0, 0, "Enter", dark=True)
    s.append(f'<g transform="translate({186-10-cw:.2f},96)">{c}</g>')
    # 其他模式：即将推出
    for i, k in enumerate(("m.daily", "m.coop", "m.ai")):
        y = 144 + i * 44
        s.append(f'<rect x="16.3" y="{y+0.3}" width="169.4" height="37.4" rx="8" fill="#ffffff" fill-opacity="0.035" stroke="#263046" stroke-width="0.6"/>')
        s.append(text(28, y + 17, tr(k, lang), 10.5, "#7f8ba3", True))
        s.append(text(28, y + 29, tr(k + ".d", lang), 6.2, "#5a6680"))
        sw = width(tr("soon", lang), 5.8, True) + 10
        s.append(f'<rect x="{186-10-sw:.2f}" y="{y+8}" width="{sw:.2f}" height="11" rx="5.5" fill="#2c3850"/>')
        s.append(text(186 - 10 - sw / 2, y + 15.6, tr("soon", lang), 5.8, MUTED, True, "middle"))
    # 展示台和坦克
    s.append('<ellipse cx="330" cy="236" rx="92" ry="20" fill="#3ee8ff" fill-opacity="0.1" stroke="#3ee8ff" stroke-opacity="0.45" stroke-width="0.8"/>')
    defs, body = tank_body(*TANKS["player"])
    s.append(f'<g transform="translate(330 186) rotate(30) scale(4.2) translate(-12 -12)">{body}</g>')
    return svg(W, H, "".join(s), defs_ui() + defs, res=2), (W / 2, H / 2)


MX, MY, MW, MH = 58, 76, 220, 220  # 弹窗位置（盖在战场中央）


def modal_frame(stroke, op=0.6):
    return f'<rect x="{MX}" y="{MY}" width="{MW}" height="{MH}" rx="12" fill="#121826" stroke="{stroke}" stroke-opacity="{op}" stroke-width="1"/>'


def revive(n, lang):
    m = MX + MW / 2
    s = [f'<rect width="{W}" height="{H}" fill="#1f0407" fill-opacity="0.55"/>', modal_frame("#ff4a3a")]
    s.append(text(m, MY + 30, tr("rv.title", lang), 15, "#ff5a4a", True, "middle"))
    s.append(text(m, MY + 45, tr("rv.sub", lang), 7.5, "#c8d2e3", False, "middle"))
    r, cy = 18, MY + 76
    circ = 2 * math.pi * r
    s.append(f'<circle cx="{m}" cy="{cy}" r="{r}" fill="none" stroke="#2a3346" stroke-width="3.5"/>')
    s.append(f'<circle cx="{m}" cy="{cy}" r="{r}" fill="none" stroke="#ff9a1a" stroke-width="3.5" stroke-linecap="round" '
             f'stroke-dasharray="{circ*n/7:.2f} {circ:.2f}" transform="rotate(-90 {m} {cy})"/>')
    s.append(text(m, cy + 6, str(n), 17, "#ffffff", True, "middle"))
    # 看视频复活（广告按钮）
    bx, by, bw, bh = MX + 20, MY + 108, MW - 40, 28
    button("revive.ad", bx, by, bw, bh)
    s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="14" fill="{GBLUE}"/>')
    s.append(play_icon(bx + 16, by + 14, "#ffffff"))
    s.append(text(m + 2, by + 17.5, tr("revive.ad", lang), 9.5, "#ffffff", True, "middle"))
    c, cw = chip(0, 0, "J", dark=True)
    s.append(f'<g transform="translate({bx+bw-10-cw:.2f},{by+9})">{c}</g>')
    b, abw = ad_badge(0, 0, lang)
    rw = width(tr("rv.reward", lang), 6.5)
    x0 = m - (abw + 4 + rw) / 2
    s.append(f'<g transform="translate({x0:.2f},{by+bh+7})">{b}</g>')
    s.append(text(x0 + abw + 4, by + bh + 14, tr("rv.reward", lang), 6.5, "#c8d2e3"))
    # 放弃
    gx, gy, gw, gh = m - 55, MY + 170, 110, 22
    button("revive.giveup", gx, gy, gw, gh)
    s.append(f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" rx="11" fill="#ffffff" fill-opacity="0.04" stroke="#3a4660" stroke-width="0.7"/>')
    c, cw = chip(0, 0, "Esc")
    tw = width(tr("giveup", lang), 8)
    x0 = m - (tw + 5 + cw) / 2
    s.append(text(x0, gy + 14.5, tr("giveup", lang), 8, MUTED))
    s.append(f'<g transform="translate({x0+tw+5:.2f},{gy+6})">{c}</g>')
    return svg(W, H, "".join(s), defs_ui(), res=2), (W / 2, H / 2)


def adplay(n, lang, total=5):
    """模拟的激励视频广告（全屏），n 是剩余秒数"""
    s = [f'<rect width="{W}" height="{H}" fill="#05070c"/>']
    b, _ = ad_badge(16, 14, lang)
    s.append(b)
    s.append(text(464, 21, tr("ap.reward", lang).format(n=n), 8, "#c8d2e3", True, "end"))
    s.append(f'<rect x="16" y="32" width="448" height="2.5" rx="1.25" fill="#ffffff" fill-opacity="0.12"/>')
    s.append(f'<rect x="16" y="32" width="{448*(total-n+1)/total:.2f}" height="2.5" rx="1.25" fill="{GBLUE}"/>')
    # 广告素材（示例品牌）
    s.append('<rect x="90" y="62" width="300" height="220" rx="16" fill="#ffffff"/>')
    s.append(brand_logo(240, 112, 22))
    s.append(text(240, 158, tr("ad.brand", lang), 13, "#202124", True, "middle"))
    s.append(text(240, 190, tr("ap.big", lang), 22, GBLUE, True, "middle"))
    s.append(text(240, 210, tr("ad.head", lang), 8, "#5f6368", False, "middle"))
    s.append(f'<rect x="185" y="232" width="110" height="28" rx="14" fill="{GBLUE}"/>')
    s.append(text(240, 250, tr("ad.cta", lang), 9, "#ffffff", True, "middle"))
    s.append(text(240, 336, tr("ap.demo", lang), 6.8, "#6b778f", False, "middle"))
    return svg(W, H, "".join(s), defs_ui(), res=2), (W / 2, H / 2)


COIN_POS = (MX + 50, MY + 70)  # 结算弹窗里金币数字的锚点（SVG 坐标，基线左端）


def result(win, done, lang):
    m = MX + MW / 2
    s = [f'<rect width="{W}" height="{H}" fill="#05070c" fill-opacity="0.5"/>', modal_frame("#f2c94c" if win else "#3a4660")]
    s.append(text(m, MY + 34, tr("rs.win" if win else "rs.lose", lang), 18, "#ffe27a" if win else "#c8d2e3", True, "middle"))
    # 金币（数字由 UI 克隆显示在 COIN_POS）
    s.append(f'<rect x="{MX+20}" y="{MY+48}" width="{MW-40}" height="32" rx="8" fill="#ffffff" fill-opacity="0.05"/>')
    s.append(f'<circle cx="{MX+38}" cy="{MY+64}" r="6.5" fill="url(#gold)"/><circle cx="{MX+38}" cy="{MY+64}" r="4.2" fill="none" stroke="#a86a00" stroke-width="0.9"/>')
    s.append(text(MX + MW - 28, MY + 68, tr("coins", lang), 7.5, MUTED, True, "end"))
    # 看视频双倍（广告按钮）/ 已领取
    bx, by, bw, bh = MX + 20, MY + 90, MW - 40, 26
    if not done:
        button("result.ad", bx, by, bw, bh)
        s.append(f'<rect x="{bx+0.5}" y="{by+0.5}" width="{bw-1}" height="{bh-1}" rx="12.5" fill="none" stroke="{GBLUE}" stroke-width="1"/>')
        b, abw = ad_badge(bx + 8, by + 8.5, lang)
        s.append(b + play_icon(bx + abw + 18, by + 13, "#8ab4f8", 0.9))
        s.append(text(m + 6, by + 16.5, tr("ad.double", lang), 8.5, "#8ab4f8", True, "middle"))
        c, cw = chip(0, 0, "J")
        s.append(f'<g transform="translate({bx+bw-10-cw:.2f},{by+8})">{c}</g>')
    else:
        s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="13" fill="#14b866" fill-opacity="0.15"/>')
        tw = width(tr("rs.doubled", lang), 8.5, True)
        s.append(text(m - 6, by + 16.5, tr("rs.doubled", lang), 8.5, "#2ee88a", True, "middle"))
        s.append(f'<path d="M{m+tw/2-2:.2f} {by+13}l3 3 6-6" fill="none" stroke="#2ee88a" stroke-width="1.6"/>')
    # 再来一局
    ax, ay, aw, ah = MX + 20, MY + 128, MW - 40, 30
    button("result.again", ax, ay, aw, ah)
    s.append(f'<rect x="{ax}" y="{ay}" width="{aw}" height="{ah}" rx="15" fill="url(#cta)"/>')
    s.append(text(m - 6, ay + 19.5, tr("rs.again", lang), 10, "#ffffff", True, "middle"))
    c, cw = chip(0, 0, "R", dark=True)
    s.append(f'<g transform="translate({ax+aw-10-cw:.2f},{ay+10})">{c}</g>')
    # 主页
    hx, hy, hw, hh = m - 45, MY + 172, 90, 22
    button("result.home", hx, hy, hw, hh)
    c, cw = chip(0, 0, "H")
    tw = width(tr("rs.home", lang), 8)
    x0 = m - (tw + 5 + cw) / 2
    s.append(text(x0, hy + 14.5, tr("rs.home", lang), 8, MUTED))
    s.append(f'<g transform="translate({x0+tw+5:.2f},{hy+6})">{c}</g>')
    return svg(W, H, "".join(s), defs_ui(), res=2), (W / 2, H / 2)


def screen_costumes():
    out = []
    for lang in LANGS:
        out.append((f"card_{lang}", *native_card(lang)))
        out.append((f"banner_{lang}", *banner(lang)))
        out.append((f"home_{lang}", *home(lang), 2))
        for n in range(1, 8):
            out.append((f"revive_{n}_{lang}", *revive(n, lang), 2))
        for n in range(1, 6):
            out.append((f"adplay_{n}_{lang}", *adplay(n, lang), 2))
        for win in (True, False):
            for done in (False, True):
                name = f"result_{'win' if win else 'lose'}_{'done' if done else 'plain'}_{lang}"
                out.append((name, *result(win, done, lang), 2))
    # 广告卡片和横幅上的关闭按钮
    x, y, w, h = CARD
    button("card.close", x + w - 16, y, 16, 16)
    button("card", x, y, w, h)
    x, y, w, h = BANNER
    button("banner.close", x + w - 22, y, 22, h)
    button("banner", x, y, w, h)
    return out


def stage_xy(x, y):
    """SVG 坐标 -> 舞台坐标"""
    return x - W / 2, H / 2 - y


def hit_lines():
    lines = ["\tswitch name {\n"]
    for name, (x, y, w, h) in BUTTONS.items():
        x0, y1 = stage_xy(x, y)
        x1, y0 = stage_xy(x + w, y + h)
        lines.append(f'\tcase "{name}":\n\t\treturn x >= {x0:g} && x <= {x1:g} && y >= {y0:g} && y <= {y1:g}\n')
    lines.append("\t}\n")
    return lines


def build_hud():
    """所有界面造型都放进一个 UI 精灵（spx 解释器对精灵类型数量有上限，见 UI.spx）"""
    costumes = []
    for key, (size, fill, bold, anchor) in LABELS.items():
        for lang in LANGS:
            c, piv = text_costume(tr(key, lang), size, fill, bold, anchor)
            costumes.append((f"{key}_{lang}", c, piv))
    for key, k in HINTS.items():
        for lang in LANGS:
            c, piv = hint_costume(k, tr(key, lang))
            costumes.append((f"{key}_{lang}", c, piv))
    for key in STRINGS:
        if key.startswith("msg."):
            for lang in LANGS:
                costumes.append((f"{key}_{lang}", *toast_costume(tr(key, lang))))
    costumes += [(f"toggle_{lang}", *toggle_costume(lang)) for lang in LANGS]
    nums, widths = num_costumes()
    costumes += nums
    costumes += icon_costumes()
    update_generated_block(os.path.join(ROOT, "TankBattle", "UI.spx"), [
        f'\tif st == "{st}" {{\n\t\treturn {dw:.3f}, {cw:.3f}\n\t}}\n' for st, (dw, cw) in widths.items()])
    costumes += screen_costumes()
    update_generated_block(os.path.join(ROOT, "TankBattle", "UI.spx"), hit_lines(), "hit")
    return write_sprite("UI", costumes)


def main():
    out = [
        write("field.svg", backdrop_classic()),
        write("field_m.svg", backdrop_modern()),
        write("sprites/Tile/brick_m.svg", brick_m()),
        write("sprites/Tile/cracked_m.svg", brick_m(True)),
        write("sprites/Tile/steel_m.svg", steel_m()),
        write("sprites/Tile/eagle_m.svg", eagle_m()),
        write("sprites/Tile/broken_m.svg", broken_m()),
        write("sprites/Player/player_m.svg", tank_m(*TANKS["player"])),
        write("sprites/Enemy/basic_m.svg", tank_m(*TANKS["basic"])),
        write("sprites/Enemy/fast_m.svg", tank_m(*TANKS["fast"])),
        write("sprites/Enemy/heavy_m.svg", tank_m(*TANKS["heavy"], heavy=True)),
        write("sprites/PBullet/bullet_m.svg", bullet_m("#ffe27a", "#ffb000")),
        write("sprites/EBullet/bullet_m.svg", bullet_m("#ff8a7a", "#ff2a2a")),
    ]
    for i in range(3):
        out.append(write(f"sprites/Boom/b{i+1}_m.svg", boom_m(i)))
    hud = build_hud()
    print(f"generated {len(out)} art files, {hud} HUD costumes")


if __name__ == "__main__":
    main()
