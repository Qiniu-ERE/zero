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


def water_m():
    defs = lin("w", "#1b6fa8", "#0d3f66", vertical=False)
    s = [f'<rect width="{C}" height="{C}" fill="url(#w)"/>',
         '<path d="M3 8q3-2.5 6 0t6 0M8 16q3-2.5 6 0t6 0" stroke="#7fd4ff" stroke-opacity="0.55" stroke-width="1" fill="none"/>']
    return svg(C, C, "".join(s), defs)


def water_classic():
    s = [f'<rect width="{C}" height="{C}" fill="#1f3fbf"/>',
         '<path d="M2 6h4M10 6h4M18 6h4M6 12h4M14 12h4M2 18h4M10 18h4M18 18h4" stroke="#9fb6ff" stroke-width="2"/>']
    return svg(C, C, "".join(s))


def grass_m():
    s = []
    for i in range(7):  # 几团树丛，边缘留一点缝隙，能隐约看到下面的坦克
        x = 3 + (i * 8) % 20
        y = 3 + (i * 11) % 18
        s.append(f'<circle cx="{x}" cy="{y}" r="{5 + i % 3}" fill="{["#2f7d3a", "#3c9a46", "#256b30"][i % 3]}"/>')
    s.append('<circle cx="9" cy="8" r="2.4" fill="#6fd06a" fill-opacity="0.5"/>')
    return svg(C, C, "".join(s))


def grass_classic():
    s = [f'<rect width="{C}" height="{C}" fill="#0b5a12" fill-opacity="0.9"/>']
    for y in range(0, C, 6):
        for x in range(0, C, 6):
            s.append(f'<rect x="{x + (3 if (y // 6) % 2 else 0)}" y="{y}" width="3" height="3" fill="#5ccf3a"/>')
    return svg(C, C, "".join(s))


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
    "player2": ("#4fe3c1", "#1f7a66", "#c9fff1"),  # 2P：青绿色
}
# v6 敌我区分（docs/v6/PLAN.md 第一节）：我方亮色、圆角车身、圆炮塔；敌方统一枪灰色切角车身、六角炮塔，
# 标识色红色（警示条、炮口、“眼睛”），种类看外形（快速窄、重型带装甲板）；精英的标识色换成紫色。
# 深灰和红色只留给敌方，我方的颜色和涂装都不能用
FOE_RED = "#ff3b30"
ELITE = "#c46bff"
HULL = ("#5b6271", "#2a2e37", "#8a93a6")  # 敌方车身：主色、暗部、亮部
FOE_KINDS = ("basic", "fast", "heavy")


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


def hex_fill(cx, cy, r, fill):
    pts = " ".join(f"{cx + math.cos(math.radians(i * 60)) * r:.2f},{cy + math.sin(math.radians(i * 60)) * r:.2f}" for i in range(6))
    return f'<polygon points="{pts}" fill="{fill}"/>'


def foe_body(accent=FOE_RED, kind="basic"):
    """朝上的敌方坦克（24x24），返回 (defs, body)。kind：basic / fast / heavy"""
    main, dark, light = HULL
    defs = rad("sh", [(0, "#000", 0.45), (0.7, "#000", 0.2), (1, "#000", 0)])
    s = ['<ellipse cx="12.8" cy="13.4" rx="11.2" ry="10.6" fill="url(#sh)"/>']
    hx, hw = {"fast": (7.4, 9.2), "heavy": (5.2, 13.6)}.get(kind, (5.8, 12.4))
    tw = 4.6 if kind == "fast" else 5.5
    for x in (hx - tw + 0.4, hx + hw - 0.4):  # 履带
        s.append(f'<rect x="{x:.1f}" y="2.5" width="{tw}" height="20" rx="1.2" fill="#141418"/>')
        for i in range(7):
            s.append(f'<rect x="{x + 0.5:.1f}" y="{3.4 + i * 2.8:.1f}" width="{tw - 1}" height="1.3" fill="{accent}" fill-opacity="0.35"/>')
    c = 2.6  # 切角车身，和我方的圆角车身区分
    x1, y1, x2, y2 = hx, 4.5, hx + hw, 21.5
    pts = f"{x1 + c},{y1} {x2 - c},{y1} {x2},{y1 + c} {x2},{y2 - c} {x2 - c},{y2} {x1 + c},{y2} {x1},{y2 - c} {x1},{y1 + c}"
    s.append(f'<polygon points="{pts}" fill="{dark}"/>')
    s.append(f'<polygon points="{pts}" fill="{main}" transform="translate(0 -0.8)"/>')
    s.append(f'<rect x="{x1 + 1.2}" y="5.6" width="{hw - 2.4}" height="1.8" fill="{accent}"/>')  # 车头警示条
    if kind == "heavy":  # 重型：两侧装甲板 + 铆钉
        for x in (x1 + 0.8, x2 - 3.4):
            s.append(f'<rect x="{x:.1f}" y="9" width="2.6" height="10" rx="0.5" fill="{dark}"/>')
            s.append(f'<circle cx="{x + 1.3:.1f}" cy="10.5" r="0.6" fill="{accent}"/><circle cx="{x + 1.3:.1f}" cy="17.5" r="0.6" fill="{accent}"/>')
    if kind == "fast":  # 快速：车尾两道箭头
        s.append(f'<path d="M9.4 18.6l2.6-1.8 2.6 1.8M9.4 21l2.6-1.8 2.6 1.8" stroke="{accent}" stroke-width="0.9" fill="none"/>')
    bw = 4.6 if kind == "heavy" else 3.2
    s.append(f'<rect x="{12 - bw / 2}" y="0.8" width="{bw}" height="11" fill="{dark}"/>')
    s.append(f'<rect x="{12 - bw / 2 - 0.6}" y="0" width="{bw + 1.2}" height="2.2" fill="{accent}"/>')  # 红色炮口
    s.append(hex_fill(12, 13, 5.4, dark) + hex_fill(12, 12.4, 4.8, main))  # 六角炮塔
    s.append(f'<rect x="9.2" y="11.4" width="5.6" height="1.8" rx="0.9" fill="{accent}"/>')  # “眼睛”
    s.append('<rect x="9.2" y="11.4" width="5.6" height="1.8" rx="0.9" fill="#ffffff" fill-opacity="0.35"/>')
    return defs, "".join(s)


def foe_m(kind, accent=FOE_RED):
    defs, body = foe_body(accent, kind)
    return svg(C, C, f'<g transform="rotate(90 12 12)">{body}</g>', defs)


# 经典画风（1985 像素风）的敌人：和玩家同一个像素坦克的外形，统一银灰色 + 红色“眼睛”；精英是紫色。
# 种类看外形：快速坦克车身窄、车尾两道箭头，重型坦克炮管粗、车身两侧有装甲板
PIXEL_FOE = ("#404048", "#9a9aa2", "#e0e0e6", FOE_RED)
PIXEL_ELITE = ("#4a2070", "#9a5ad0", "#ecd2ff", "#ffffff")


def foe_classic(kind, palette=PIXEL_FOE):
    dark, mid, light, eye = palette
    s = [f'<rect x="1" y="1" width="20" height="7" fill="{dark}"/>', f'<rect x="1" y="16" width="20" height="7" fill="{dark}"/>']
    for x in (3, 7, 11, 15):
        s.append(f'<rect x="{x}" y="2" width="2" height="5" fill="{light}"/><rect x="{x}" y="17" width="2" height="5" fill="{light}"/>')
    if kind == "fast":
        s.append(f'<rect x="4" y="8" width="15" height="8" fill="{mid}"/>')
        s.append(f'<path d="M2 9.5l2 2.5-2 2.5M5 9.5l2 2.5-2 2.5" stroke="{eye}" stroke-width="1" fill="none"/>')
    else:
        s.append(f'<rect x="4" y="7" width="15" height="10" fill="{mid}"/>')
    if kind == "heavy":
        s.append(f'<rect x="5" y="7" width="10" height="2" fill="{dark}"/><rect x="5" y="15" width="10" height="2" fill="{dark}"/>')
    s.append(f'<circle cx="11" cy="12" r="4.5" fill="{light}" stroke="{dark}" stroke-width="1.2"/>')
    bh = 4 if kind == "heavy" else 3
    s.append(f'<rect x="12" y="{12 - bh / 2}" width="11" height="{bh}" fill="{light}" stroke="{dark}" stroke-width="0.8"/>')
    s.append(f'<rect x="21" y="{12 - bh / 2}" width="2" height="{bh}" fill="{eye}"/>')  # 炮口
    s.append(f'<rect x="10" y="11" width="2.4" height="2" fill="{eye}"/>')  # “眼睛”
    return svg(C, C, "".join(s))


def player2_classic():
    """经典画风的 2P：把 1P 的像素坦克换成绿色（和 FC 原版一样）"""
    with open(os.path.join(ASSETS, "sprites", "Player", "player.svg"), encoding="utf-8") as f:
        s = f.read()
    for a, b in (("#8A6A00", "#1B6B2A"), ("#E8C020", "#3CB44B"), ("#FFE680", "#B8F5B0")):
        s = s.replace(a, b)
    return s


def enemy_index():
    """Enemy 精灵的造型表：三种敌人 × 普通 / 精英 × 经典 / 现代"""
    p = os.path.join(ASSETS, "sprites", "Enemy", "index.json")
    with open(p, encoding="utf-8") as f:
        cfg = json.load(f)
    names = [k + e + m for m in ("", "_m") for e in ("", "_e") for k in FOE_KINDS]
    cfg["costumes"] = [{"name": n, "path": n + ".svg", "x": 12, "y": 12} for n in names]
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")


def player_index():
    """Player 精灵的造型表：1P、2P × 经典、现代"""
    p = os.path.join(ASSETS, "sprites", "Player", "index.json")
    with open(p, encoding="utf-8") as f:
        cfg = json.load(f)
    names = ["player", "player_m", "player2", "player2_m"] + [f"player_s{i}_m" for i in range(1, len(SKINS))]
    cfg["costumes"] = [{"name": n, "path": n + ".svg", "x": 12, "y": 12} for n in names]
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")


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
    **{f"stage.{n}": (10, "#ffffff", True, "start") for n in range(1, 9)},
    "stage.daily": (10, "#d9b8ff", True, "start"),
    "stage.custom": (10, "#ffffff", True, "start"),
    "enemies": (7.5, MUTED, False, "end"),
    "score": (6.8, MUTED, True, "start"),
    "best": (6.8, MUTED, True, "start"),
    "lives": (6.8, MUTED, True, "start"),
    "tag.1p": (7.5, "#ffd23a", True, "start"),
    "tag.2p": (7.5, "#4fe3c1", True, "start"),
    "chips": (6.8, MUTED, True, "start"),
    "tag.c1": (6.5, "#ffd23a", True, "start"),
    "tag.c2": (6.5, "#4fe3c1", True, "start"),
}
# 按键提示：key -> 按键
HINTS = {"hint.move": "WASD", "hint.fire": "J", "hint.style": "T", "hint.lang": "L", "hint.p1": "1P", "hint.p2": "2P"}


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
    for name, col in (("pip_on", "#ff5a4a"), ("pip_off", "#3a4256"), ("pip_elite", ELITE)):
        out.append((name, svg(4, 8, f'<rect width="4" height="8" rx="1" fill="{col}"/>', res=HR), (2, 4)))
    defs, body = tank_body(*TANKS["player"])
    for name, op in (("life_on", 1), ("life_off", 0.22)):
        out.append((name, svg(12, 12, f'<g opacity="{op}" transform="scale(0.5)">{body}</g>', defs, res=HR), (6, 6)))
    defs, body = tank_body(*TANKS["player2"])
    for name, op in (("life2_on", 1), ("life2_off", 0.22)):
        out.append((name, svg(12, 12, f'<g opacity="{op}" transform="scale(0.5)">{body}</g>', defs, res=HR), (6, 6)))
    # 超过 3 条命时跟在第一个图标后面的“×N”（放在第 2 个图标的位置，锚点让文字紧挨着第一个图标）
    for n in range(4, 10):
        s = f"×{n}"
        out.append((f"lifex{n}", svg(width(s, 8, True) + 2, 12, text(1, 9.2, s, 8, "#ffffff", True), res=HR), (9, 6)))
    return out


def ally_costume(p, lv):
    """我方标识（v6 敌我区分）：坦克脚下的光圈 + 头顶的标签“1P · Lv3”。UI 克隆每帧跟着坦克走，
    不画进坦克造型：造型变大会改变碰撞范围。锚点是光圈中心"""
    col = TANKS["player" if p == 1 else "player2"][0]
    w, h, cy, r = 44, 46, 28, 15
    tag = f"{p}P · Lv{lv}"
    tw = width(tag, 6.5, True) + 8
    body = (f'<circle cx="{w/2}" cy="{cy}" r="{r}" fill="{col}" fill-opacity="0.1" stroke="{col}" stroke-width="1.3"/>'
            f'<rect x="{(w-tw)/2:.2f}" y="1" width="{tw:.2f}" height="10" rx="5" fill="{col}"/>'
            + text(w / 2, 8.6, tag, 6.5, "#1a1405", True, "middle"))
    return svg(w, h, body, res=HR), (w / 2, cy)


def stage_coop_costume(key, lang):
    """双人时的关卡名：关卡名后面跟一个「双人」标签"""
    s, size = tr(key, lang), 10
    w = width(s, size, True)
    b = tr("coop", lang)
    bw = width(b, 6, True) + 8
    body = (text(1, size * 1.1, s, size, "#ffffff", True)
            + f'<rect x="{1+w+6:.2f}" y="{size*1.1-8.6:.2f}" width="{bw:.2f}" height="11" rx="5.5" fill="#4fe3c1"/>'
            + text(1 + w + 6 + bw / 2, size * 1.1 - 1, b, 6, "#06232b", True, "middle"))
    if w + 6 + bw > 158:
        sys.exit(f"双人关卡名太长，会和顶栏的“敌军”重叠：{s}")
    return svg(w + 6 + bw + 2, size * 1.45, body, res=HR), (1, size * 1.1)


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


# 主页上的其他模式：(文案 key, 按键)。v5 去掉了“每日挑战 · 即将推出”（需要服务器和排行榜，不会做）
# 选择关卡（v5）放在原来每日挑战的位置；按键提示是“1-8”（主页直接按数字键进关）
HOME_MODES = [("m.coop", "C"), ("m.maker", "E"), ("m.levels", "1-8")]
HOME_TILES = [("daily", "D", 226), ("garage", "G", 308)]  # v6：(名字, 按键, x)


def home_tile_icon(k, cx, cy):
    if k == "daily":  # 日历
        return (f'<rect x="{cx-8}" y="{cy-7}" width="16" height="14" rx="2.5" fill="{ELITE}" fill-opacity="0.25" stroke="{ELITE}" stroke-width="1.2"/>'
                f'<path d="M{cx-8} {cy-3}h16M{cx-4} {cy-9}v4M{cx+4} {cy-9}v4" stroke="{ELITE}" stroke-width="1.2"/>'
                + text(cx, cy + 5, "1", 6.5, "#f3dcff", True, "middle"))
    if k == "garage":
        defs, body = tank_body(*TANKS["player"])
        defs, body = defs.replace('id="sh"', 'id="shg"'), body.replace("url(#sh)", "url(#shg)")
        return f'<defs>{defs}</defs><g transform="translate({cx-9} {cy-9}) scale(0.75)">{body}</g>'
    return ""


def home(lang):
    s = [f'<rect width="{W}" height="{H}" fill="url(#bgH)"/>',
         '<circle cx="330" cy="170" r="140" fill="#3ee8ff" fill-opacity="0.05"/><circle cx="330" cy="170" r="90" fill="#ffd23a" fill-opacity="0.05"/>']
    t = tr("title", lang)
    if 16 + width(t, 22, True) + 6 + width("2026", 22, True) > 290:
        sys.exit(f"主页标题太长，会压到右边的坦克展示台：{t} 2026")
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
    # 其他模式：带「新」标签和按键
    for i, (k, key) in enumerate(HOME_MODES):
        y = 144 + i * 44
        button(f"home.{k[2:]}", 16, y, 170, 38)
        s.append(f'<rect x="16.4" y="{y+0.4}" width="169.2" height="37.2" rx="8" fill="#3ee8ff" fill-opacity="0.08" stroke="#3ee8ff" stroke-opacity="0.7" stroke-width="0.8"/>')
        s.append(text(28, y + 17, tr(k, lang), 10.5, "#ffffff", True))
        s.append(text(28, y + 29, tr(k + ".d", lang), 6.2, "#9fdcea"))
        nw = width(tr("new", lang), 5.8, True) + 10
        c, cw = chip(0, 0, key, dark=True)
        s.append(f'<rect x="{186-10-cw-6-nw:.2f}" y="{y+8}" width="{nw:.2f}" height="11" rx="5.5" fill="#3ee8ff"/>')
        s.append(text(186 - 10 - cw - 6 - nw / 2, y + 15.6, tr("new", lang), 5.8, "#06232b", True, "middle"))
        s.append(f'<g transform="translate({186-10-cw:.2f},{y+8.5})">{c}</g>')
    # v6 的入口：右下角的小卡片（每日挑战、车库、排行榜按顺序放在 x = 226、308、390）
    for k, key, x in HOME_TILES:
        button(f"home.{k}", x, 262, 74, 44)
        s.append(f'<rect x="{x+0.4}" y="262.4" width="73.2" height="43.2" rx="8" fill="#ffffff" fill-opacity="0.05" stroke="#2c3850" stroke-width="0.7"/>')
        s.append(home_tile_icon(k, x + 37, 278))
        s.append(text(x + 10, 298, tr(f"home.{k}", lang), 7.5, "#e6ecf5", True))
        c, cw = chip(0, 0, key, dark=True)
        s.append(f'<g transform="translate({x+74-8-cw:.2f},290)">{c}</g>')
    # 路演演示模式提示（选关的“1-8”已经在选择关卡卡片上）
    c, cw = chip(16, 290, "P")
    s.append(c + text(16 + cw + 5, 297.4, tr("home.demo", lang), 7, "#7f8ba3"))
    # 展示台和坦克
    s.append('<ellipse cx="330" cy="236" rx="92" ry="20" fill="#3ee8ff" fill-opacity="0.1" stroke="#3ee8ff" stroke-opacity="0.45" stroke-width="0.8"/>')
    # 展示台上的 1P、2P 两辆坦克（各自的渐变 id 不同，避免冲突）
    for colors, tx, rot, tag in ((TANKS["player"], 300, 20, "a"), (TANKS["player2"], 362, -20, "b")):
        defs, body = tank_body(*colors)
        defs, body = defs.replace('id="sh"', f'id="sh{tag}"'), body.replace("url(#sh)", f"url(#sh{tag})")
        s.append(f'<defs>{defs}</defs><g transform="translate({tx} 192) rotate({rot}) scale(3.4) translate(-12 -12)">{body}</g>')
    return svg(W, H, "".join(s), defs_ui(), res=2), (W / 2, H / 2)


LV_W, LV_H, LV_GAP = 104, 84, 8  # 选关画面的关卡卡片


def levels(lang):
    """选择关卡（v5）：8 张关卡卡片（4 x 2）和返回按钮，鼠标、触屏、键盘（1~8、Esc）都能用"""
    s = [f'<rect width="{W}" height="{H}" fill="url(#bgH)"/>',
         '<circle cx="380" cy="300" r="140" fill="#3ee8ff" fill-opacity="0.04"/>']
    s.append(text(16, 46, tr("lv.title", lang), 22, "#ffffff", True))
    s.append(text(16, 60, tr("lv.sub", lang), 7.5, "#7f8ba3", True))
    for n in range(1, 9):
        x = 16 + (n - 1) % 4 * (LV_W + LV_GAP)
        y = 80 + (n - 1) // 4 * (LV_H + LV_GAP)
        final = n == 8
        col = "#ffd23a" if final else "#3ee8ff"
        button(f"lv.{n}", x, y, LV_W, LV_H)
        s.append(f'<rect x="{x+0.4}" y="{y+0.4}" width="{LV_W-0.8}" height="{LV_H-0.8}" rx="10" fill="{col}" fill-opacity="0.08" stroke="{col}" stroke-opacity="0.7" stroke-width="0.8"/>')
        s.append(text(x + 12, y + 36, str(n), 26, "url(#gold)" if final else "#ffffff", True))
        name = tr(f"stage.{n}", lang).split(" · ", 1)[1]
        if width(name, 9.5, True) > LV_W - 20:
            sys.exit(f"选关画面的关卡名太长：{name}")
        s.append(text(x + 12, y + 64, name, 9.5, "#ffe9a8" if final else "#ffffff", True))
        c, cw = chip(0, 0, str(n), dark=True)
        s.append(f'<g transform="translate({x+LV_W-10-cw:.2f},{y+10})">{c}</g>')
    # 返回主页
    bx, by, bw, bh = 16, 276, 110, 26
    button("lv.back", bx, by, bw, bh)
    s.append(f'<rect x="{bx+0.3}" y="{by+0.3}" width="{bw-0.6}" height="{bh-0.6}" rx="{bh/2}" fill="#ffffff" fill-opacity="0.05" stroke="#2c3850" stroke-width="0.6"/>')
    s.append(text(bx + 14, by + 16.5, tr("lv.back", lang), 8.5, "#c8d2e3", True))
    c, cw = chip(0, 0, "Esc")
    s.append(f'<g transform="translate({bx+bw-10-cw:.2f},{by+8})">{c}</g>')
    return svg(W, H, "".join(s), defs_ui(), res=2), (W / 2, H / 2)


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
    # 广告素材（七牛云广告位招商）
    s.append('<rect x="90" y="62" width="300" height="220" rx="16" fill="#ffffff"/>')
    s.append(brand_logo(240, 112, 22))
    s.append(text(240, 158, tr("ad.brand", lang), 13, "#202124", True, "middle"))
    s.append(text(240, 190, tr("ap.big", lang), 22, GBLUE, True, "middle"))
    s.append(text(240, 210, tr("ap.sub", lang), 8, "#5f6368", False, "middle"))
    s.append(f'<rect x="185" y="232" width="110" height="28" rx="14" fill="{GBLUE}"/>')
    s.append(text(240, 250, tr("ad.cta", lang), 9, "#ffffff", True, "middle"))
    s.append(text(240, 336, tr("ap.demo", lang), 6.8, "#6b778f", False, "middle"))
    return svg(W, H, "".join(s), defs_ui(), res=2), (W / 2, H / 2)


COIN_POS = (MX + 50, MY + 70)  # 结算弹窗里金币数字的锚点（SVG 坐标，基线左端）


def result(kind, done, lang):
    """kind：win 过关（按钮是“下一关”）、final 最后一关也赢了（全部通关）、lose 战败、
    ewin / elose 自制地图试玩的胜负（按钮是“继续编辑”）"""
    win = kind not in ("lose", "elose")
    m = MX + MW / 2
    s = [f'<rect width="{W}" height="{H}" fill="#05070c" fill-opacity="0.5"/>', modal_frame("#f2c94c" if win else "#3a4660")]
    title = {"win": "rs.win", "final": "rs.final", "lose": "rs.lose", "ewin": "rs.win", "elose": "rs.lose"}[kind]
    s.append(text(m, MY + 34, tr(title, lang), 18, "#ffe27a" if win else "#c8d2e3", True, "middle"))
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
    s.append(text(m - 6, ay + 19.5, tr({"win": "rs.next", "ewin": "rs.edit", "elose": "rs.edit"}.get(kind, "rs.again"), lang), 10, "#ffffff", True, "middle"))
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


# ---------- 自己做地图（地图编辑器） ----------
# 编辑器画面：顶栏和右侧面板不透明，战场区域透明（地形由 Tile 克隆显示）。
# 会变的部分（选中的工具、对称开关和对称线、检查结果、光标、问题标记）是 UI 的单独 kind，见 UI.spx
ED_X0 = PX + 8          # 面板内容左边
ED_TOOL_Y = 48          # 工具格子的上边
ED_TOOL_STEP = 24.5     # 工具格子的间距
ED_STATUS = (ED_X0, 110)  # 检查结果的左上角
ED_SWITCH = (PX + PW - 30, 92)  # 对称开关的左上角（20x10）
ED_LOCKED = [(0, 0, "enemy"), (0, 6, "enemy"), (0, 12, "enemy"), (12, 4, "1P"), (12, 8, "2P")]


def inline_svg(src, x, y, size, prefix):
    """把一个造型 SVG 内嵌进另一个 SVG（重命名渐变 id，避免冲突）"""
    m = re.match(r'<svg[^>]*viewBox="0 0 ([\d.]+) [\d.]+"[^>]*>(.*)</svg>$', src, re.S)
    vb, body = float(m.group(1)), m.group(2)
    body = re.sub(r'id="([^"]+)"', lambda g: f'id="{prefix}{g.group(1)}"', body)
    body = re.sub(r'url\(#([^)]+)\)', lambda g: f'url(#{prefix}{g.group(1)})', body)
    return f'<g transform="translate({x:.2f} {y:.2f}) scale({size / vb:.4f})">{body}</g>'


def ed_button(name, x, y, w, h, label, key, primary=False):
    button(name, x, y, w, h)
    if primary:
        s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="url(#cta)"/>'
             + text(x + 10, y + h / 2 + 3.4, label, 9, "#ffffff", True))
        c, cw = chip(0, 0, key, dark=True)
    else:
        s = (f'<rect x="{x+0.3}" y="{y+0.3}" width="{w-0.6}" height="{h-0.6}" rx="{h/2}" fill="#ffffff" fill-opacity="0.05" stroke="#2c3850" stroke-width="0.6"/>'
             + text(x + 10, y + h / 2 + 3, label, 8, "#c8d2e3", True))
        c, cw = chip(0, 0, key)
    return s + f'<g transform="translate({x + w - 8 - cw:.2f},{y + (h - 10) / 2:.2f})">{c}</g>'


def editor(lang):
    tiles = [brick_m(), steel_m(), water_m(), grass_m()]
    s = [f'<rect width="{W}" height="{FY-4}" fill="#121826"/>',                      # 顶栏
         f'<rect x="{FX+13*C+4}" y="{FY-4}" width="{W-FX-13*C-4}" height="{H-FY+4}" fill="#0c111b"/>',  # 右侧
         f'<rect y="{FY+13*C+4}" width="{FX+13*C+4}" height="{H-FY-13*C-4}" fill="#0c111b"/>',          # 下边
         f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="6" fill="#141b2b" stroke="#263046" stroke-width="0.6"/>']
    for i in range(1, 13):  # 网格线，方便对准格子
        s.append(f'<path d="M{FX+i*C} {FY}V{FY+13*C}M{FX} {FY+i*C}H{FX+13*C}" stroke="#3ee8ff" stroke-opacity="0.12" stroke-width="0.5"/>')
    for r, c, lab in ED_LOCKED:  # 锁定格
        x, y = FX + c * C, FY + r * C
        col = {"enemy": "#ff4a3a", "1P": "#ffd23a", "2P": "#4fe3c1"}[lab]
        s.append(f'<rect x="{x+1}" y="{y+1}" width="{C-2}" height="{C-2}" rx="3" fill="{col}" fill-opacity="0.15" stroke="{col}" stroke-opacity="0.75" stroke-width="0.8" stroke-dasharray="2 1.5"/>')
        t = tr("ed.enemy", lang) if lab == "enemy" else lab
        s.append(text(x + 12, y + 15.2, t, 7.5, "#ff8a7a" if lab == "enemy" else col, True, "middle"))
    s.append(text(12, 21, tr("ed.title", lang), 10, "#ffffff", True))
    s.append(text(330, 20.5, tr("ed.hint", lang), 6.5, MUTED, False, "end"))
    x0 = ED_X0
    s.append(text(x0, 42, tr("ed.tools", lang), 6.8, MUTED, True))
    for i in range(5):
        x, y = x0 + i * ED_TOOL_STEP, ED_TOOL_Y
        button(f"ed.t{i+1}", x - 2, y - 2, 24, 24)
        s.append(f'<rect x="{x-1.5}" y="{y-1.5}" width="23" height="23" rx="4" fill="#ffffff" fill-opacity="0.03" stroke="#2c3850" stroke-width="0.6"/>')
        if i < 4:
            s.append(inline_svg(tiles[i], x + 1, y + 1, 18, f"t{i}"))
        else:  # 橡皮擦
            s.append(f'<path d="M{x+5} {y+5}l10 10M{x+15} {y+5}l-10 10" stroke="#c8d2e3" stroke-width="1.6" stroke-linecap="round"/>')
        c, cw = chip(0, 0, str(i + 1))
        s.append(f'<g transform="translate({x + 10 - cw / 2:.2f},{y + 24})">{c}</g>')
    c, cw = chip(x0, 92, "M")
    s.append(c + text(x0 + cw + 5, 99.6, tr("ed.mirror", lang), 7.5, "#c8d2e3", True))
    button("ed.mirror", x0, 88, PW - 16, 18)
    bw = PW - 16
    s.append(ed_button("ed.play", x0, 150, bw, 22, tr("ed.play", lang), "Enter", primary=True))
    for n, (k, key) in enumerate((("ed.play2", "P"), ("ed.rand", "R"), ("ed.copy", "K"), ("ed.clear", "C"), ("ed.save", "S"), ("ed.back", "Esc"))):
        s.append(ed_button(k, x0, 178 + n * 22, bw, 18, tr(k, lang), key))
    y = 318
    s.append(f'<rect x="{x0}" y="{y}" width="9" height="9" rx="2" fill="#ff4a3a" fill-opacity="0.18" stroke="#ff4a3a" stroke-opacity="0.7" stroke-width="0.7" stroke-dasharray="2 1.5"/>')
    s.append(text(x0 + 13, y + 7.4, tr("ed.locked", lang), 5.8, MUTED))
    return svg(W, H, "".join(s), defs_ui(), res=2), (W / 2, H / 2)


def ed_status(k, lang):
    """检查结果框：edok 合格，edbad1 敌人到不了基地，edbad2 坦克开不到出生点。锚点是左上角"""
    w = PW - 16
    bad = k != "edok"
    h = 30 if bad else 22
    col = "#ff5a4a" if bad else "#2ee88a"
    s = [f'<rect x="0.4" y="0.4" width="{w-0.8}" height="{h-0.8}" rx="6" fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-opacity="0.6" stroke-width="0.7"/>']
    if bad:
        s.append(f'<path d="M8 7l6 6M14 7l-6 6" stroke="{col}" stroke-width="1.6"/>')
        s.append(text(20, 12.5, tr(f"ed.{k[2:]}", lang), 7, col, True))
        s.append(text(20, 23, tr(f"ed.{k[2:]}.d", lang), 5.8, "#e8b4ad"))
    else:
        s.append(f'<path d="M7 11l3 3 6-6" fill="none" stroke="{col}" stroke-width="1.6"/>')
        s.append(text(20, 14.5, tr("ed.ok", lang), 7.5, col, True))
    return svg(w, h, "".join(s), res=HR), (0, 0)


def touch_pads():
    """触屏模式（手机 App）的方向键：画在右侧面板里，下面两行说明"""
    out = []
    for lang in LANGS:
        r = 46
        cx, cy = 60, 50
        s = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#ffffff" fill-opacity="0.05" stroke="#3ee8ff" stroke-opacity="0.45" stroke-width="1"/>',
             f'<rect x="{cx-11}" y="{cy-r+6}" width="22" height="{2*r-12}" rx="4" fill="#ffffff" fill-opacity="0.12"/>',
             f'<rect x="{cx-r+6}" y="{cy-11}" width="{2*r-12}" height="22" rx="4" fill="#ffffff" fill-opacity="0.12"/>']
        for path in (f"M{cx} {cy-r+10}l7 9h-14z", f"M{cx} {cy+r-10}l7 -9h-14z", f"M{cx-r+10} {cy}l9 7v-14z", f"M{cx+r-10} {cy}l-9 7v-14z"):
            s.append(f'<path d="{path}" fill="#3ee8ff" fill-opacity="0.85"/>')
        s.append(text(cx, cy + r + 13, tr("touch.pad", lang), 6.6, "#c8d2e3", True, "middle"))
        s.append(text(cx, cy + r + 23, tr("touch.tap", lang), 5.8, MUTED, False, "middle"))
        out.append((f"touchpad_{lang}", svg(120, 2 * r + 30, "".join(s), res=HR), (cx, cy)))
    return out


def ed_widgets():
    """编辑器里会动的小部件：工具选中框、对称开关、对称线、光标、问题标记"""
    sel = svg(25, 25, '<rect x="0.7" y="0.7" width="23.6" height="23.6" rx="4.5" fill="#3ee8ff" fill-opacity="0.12" stroke="#3ee8ff" stroke-width="1.4"/>', res=HR)
    on = svg(20, 10, '<rect width="20" height="10" rx="5" fill="#3ee8ff"/><circle cx="15" cy="5" r="3.8" fill="#06232b"/>', res=HR)
    off = svg(20, 10, '<rect width="20" height="10" rx="5" fill="#2c3850"/><circle cx="5" cy="5" r="3.8" fill="#8a96ad"/>', res=HR)
    line = svg(2, 13 * C, f'<path d="M1 0V{13*C}" stroke="#3ee8ff" stroke-opacity="0.6" stroke-width="0.9" stroke-dasharray="3 3"/>', res=HR)
    cur = svg(C, C, f'<rect x="0.7" y="0.7" width="{C-1.4}" height="{C-1.4}" rx="2" fill="#3ee8ff" fill-opacity="0.15" stroke="#3ee8ff" stroke-width="1.4"/>', res=HR)
    mark = svg(C, C, f'<rect x="0.8" y="0.8" width="{C-1.6}" height="{C-1.6}" rx="3" fill="#ff2a2a" fill-opacity="0.3" stroke="#ff4a3a" stroke-width="1.6"/>'
               + text(12, 17, "!", 13, "#ffffff", True, "middle"), res=HR)
    pause = svg(14, 14, '<rect x="0.4" y="0.4" width="13.2" height="13.2" rx="4" fill="#ffffff" fill-opacity="0.06" stroke="#2c3850" stroke-width="0.6"/>'
                '<rect x="4.3" y="3.8" width="1.9" height="6.4" rx="0.6" fill="#c8d2e3"/><rect x="7.8" y="3.8" width="1.9" height="6.4" rx="0.6" fill="#c8d2e3"/>', res=HR)
    return [*touch_pads(), ("pausebtn", pause, (7, 7)), ("edsel", sel, (12.5, 12.5)), ("edsw_on", on, (10, 5)), ("edsw_off", off, (10, 5)),
            ("edline", line, (1, 13 * C / 2)), ("edcursor", cur, (C / 2, C / 2)), ("edmark", mark, (C / 2, C / 2))]


def pause_screen(lang, edit=False):
    """暂停菜单：继续（Esc / Enter）、重新开始（R）、返回主页或返回编辑（H）"""
    m = MX + MW / 2
    s = [f'<rect width="{W}" height="{H}" fill="#05070c" fill-opacity="0.55"/>', modal_frame("#3ee8ff", 0.5)]
    s.append(f'<rect x="{m-9}" y="{MY+22}" width="6" height="18" rx="1.5" fill="#3ee8ff"/><rect x="{m+3}" y="{MY+22}" width="6" height="18" rx="1.5" fill="#3ee8ff"/>')
    s.append(text(m, MY + 62, tr("ps.title", lang), 16, "#ffffff", True, "middle"))
    bx, by, bw, bh = MX + 20, MY + 82, MW - 40, 30
    button("pause.resume", bx, by, bw, bh)
    s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="15" fill="url(#cta)"/>')
    s.append(text(m - 6, by + 19.5, tr("ps.resume", lang), 10, "#ffffff", True, "middle"))
    c, cw = chip(0, 0, "Esc", dark=True)
    s.append(f'<g transform="translate({bx+bw-10-cw:.2f},{by+10})">{c}</g>')
    by = MY + 124
    button("pause.restart", bx, by, bw, 26)
    s.append(f'<rect x="{bx+0.5}" y="{by+0.5}" width="{bw-1}" height="25" rx="12.5" fill="#ffffff" fill-opacity="0.05" stroke="#3a4660" stroke-width="0.8"/>')
    s.append(text(m - 6, by + 16.5, tr("ps.restart", lang), 8.5, "#c8d2e3", True, "middle"))
    c, cw = chip(0, 0, "R")
    s.append(f'<g transform="translate({bx+bw-10-cw:.2f},{by+8})">{c}</g>')
    hx, hy, hw, hh = m - 50, MY + 168, 100, 22
    button("pause.home", hx, hy, hw, hh)
    label = tr("ps.edit" if edit else "ps.home", lang)
    c, cw = chip(0, 0, "H")
    tw = width(label, 8)
    x0 = m - (tw + 5 + cw) / 2
    s.append(text(x0, hy + 14.5, label, 8, MUTED))
    s.append(f'<g transform="translate({x0+tw+5:.2f},{hy+6})">{c}</g>')
    return svg(W, H, "".join(s), defs_ui(), res=2), (W / 2, H / 2)


def screen_costumes():
    out = []
    for lang in LANGS:
        out.append((f"card_{lang}", *native_card(lang)))
        out.append((f"banner_{lang}", *banner(lang)))
        out.append((f"home_{lang}", *home(lang), 2))
        out.append((f"levels_{lang}", *levels(lang), 2))
        out.append((f"pause_{lang}", *pause_screen(lang), 2))
        out.append((f"pause_edit_{lang}", *pause_screen(lang, True), 2))
        out.append((f"editor_{lang}", *editor(lang), 2))
        for k in ("edok", "edbad1", "edbad2"):
            out.append((f"{k}_{lang}", *ed_status(k, lang)))
        for n in range(1, 8):
            out.append((f"revive_{n}_{lang}", *revive(n, lang), 2))
        for n in range(1, 6):
            out.append((f"adplay_{n}_{lang}", *adplay(n, lang), 2))
        for kind in ("win", "final", "lose", "ewin", "elose"):
            for done in (False, True):
                name = f"result_{kind}_{'done' if done else 'plain'}_{lang}"
                out.append((name, *result(kind, done, lang), 2))
    # 广告卡片和横幅上的关闭按钮
    x, y, w, h = CARD
    button("card.close", x + w - 16, y, 16, 16)
    button("card", x, y, w, h)
    x, y, w, h = BANNER
    button("banner.close", x + w - 22, y, 22, h)
    button("banner", x, y, w, h)
    return out


# ---------- v6 芯片：图标、三选一卡片、右侧面板的芯片格、战场上掉落的芯片（docs/v6/PLAN.md 第二节） ----------
# 顺序和 main.spx 的 chipKey 一致（编号 1~12）
CHIP_KEYS = ("rapid", "double", "pierce", "bounce", "shield", "engine", "float", "stealth", "magnet", "fortify", "bomb", "freeze")
CHIP_RARITY = {"pierce": 3, "double": 2, "bounce": 2, "float": 2, "bomb": 2, "freeze": 2}  # 其余是 1（普通）
CHIP_TACTICAL = ("fortify", "bomb", "freeze")
RARITY_COL = {1: "#8fb3ff", 2: ELITE, 3: "#ffb020"}
CHIP_COL = {"rapid": "#ffd54a", "double": "#ffd54a", "pierce": "#ff8a3a", "bounce": "#ffd54a", "shield": "#5ad1ff",
            "engine": "#2ee88a", "float": "#5ad1ff", "stealth": "#2ee88a", "magnet": "#ff7ab8", "fortify": "#c8d2e3",
            "bomb": "#ff5a4a", "freeze": "#9fe8ff"}
COMBO_PARTNER = {"pierce": "bounce", "bounce": "pierce", "rapid": "double", "double": "rapid"}


def chip_icon_body(key, col):
    """芯片图标：24x24 的线条图"""
    st = f'stroke="{col}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    return {
        "rapid": f'<circle cx="16" cy="12" r="4" fill="{col}"/><path d="M3 8h7M2 12h8M3 16h7" {st}/>',
        "double": f'<circle cx="8" cy="15" r="3.4" fill="{col}"/><circle cx="16" cy="9" r="3.4" fill="{col}"/><path d="M8 22v-3M16 16v-3" {st}/>',
        "pierce": f'<rect x="8" y="7" width="8" height="10" rx="1.2" fill="{col}" fill-opacity="0.3" stroke="{col}" stroke-width="1.4"/><path d="M2 12h20M18 8l4 4-4 4" {st}/>',
        "bounce": f'<path d="M3 20l8-14 8 14" {st}/><path d="M2 21h20" stroke="{col}" stroke-width="1.4" stroke-opacity="0.5"/><circle cx="19" cy="20" r="2.4" fill="{col}"/>',
        "shield": f'<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z" fill="{col}" fill-opacity="0.25" stroke="{col}" stroke-width="2" stroke-linejoin="round"/><path d="M9 12l2.2 2.2L15.5 10" {st}/>',
        "engine": f'<path d="M5 5l7 7-7 7M12 5l7 7-7 7" {st}/>',
        "float": f'<path d="M3 15c2-2 4-2 6 0s4 2 6 0 4-2 6 0M3 20c2-2 4-2 6 0s4 2 6 0 4-2 6 0" {st}/><rect x="7" y="4" width="10" height="7" rx="2" fill="{col}"/>',
        "stealth": f'<path d="M2 13s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6z" {st}/><circle cx="12" cy="13" r="2.6" fill="{col}"/><path d="M4 22l16-18" {st}/>',
        "magnet": f'<path d="M6 4v8a6 6 0 0 0 12 0V4" stroke="{col}" stroke-width="3.4" fill="none"/><path d="M4.4 4h3.2M16.4 4h3.2" stroke="#ffffff" stroke-width="3.4"/>',
        "fortify": f'<path d="M12 6l2 2.6 3.8-1.2-2 3.8 2.6 1.3-4.5 1.2L12 17l-1.9-3.3-4.5-1.2 2.6-1.3-2-3.8 3.8 1.2z" fill="{col}"/><rect x="2.5" y="2.5" width="19" height="19" rx="2" fill="none" stroke="{col}" stroke-width="1.6" stroke-dasharray="3 1.6"/>',
        "bomb": f'<circle cx="11" cy="14" r="7" fill="{col}"/><path d="M15 8l3-3M19 3l1 1M21 6h1" {st}/>',
        "freeze": f'<path d="M12 2v20M3.3 7l17.4 10M3.3 17L20.7 7M9 4l3 3 3-3M9 20l3-3 3 3" {st}/>',
    }[key]


def chip_icon(key, x, y, size):
    return f'<g transform="translate({x:.2f},{y:.2f}) scale({size / 24:.4f})">{chip_icon_body(key, CHIP_COL[key])}</g>'


def chip_badge(key, s=14):
    """右侧面板的芯片格（s x s），边框是稀有度的颜色"""
    rc = RARITY_COL[CHIP_RARITY.get(key, 1)]
    body = (f'<rect x="0.4" y="0.4" width="{s-0.8}" height="{s-0.8}" rx="{s*0.22:.2f}" fill="{rc}" fill-opacity="0.16" stroke="{rc}" stroke-opacity="0.85" stroke-width="0.7"/>'
            + chip_icon(key, s * 0.15, s * 0.15, s * 0.7))
    return svg(s, s, body, res=HR), (s / 2, s / 2)


def chip_empty(s=14):
    body = (f'<rect x="0.4" y="0.4" width="{s-0.8}" height="{s-0.8}" rx="{s*0.22:.2f}" fill="none" stroke="#3a4256" stroke-width="0.7" stroke-dasharray="2 1.6"/>'
            + text(s / 2, s / 2 + 2.6, "+", 7, "#3a4256", True, "middle"))
    return svg(s, s, body, res=HR), (s / 2, s / 2)


def chip_drop():
    """精英被击毁后掉在战场上的芯片：紫色六边形 + 星，外面一圈光"""
    defs = rad("cg", [(0, ELITE, 0.75), (0.5, ELITE, 0.25), (1, ELITE, 0)])
    pts = " ".join(f"{16 + math.cos(math.radians(30 + i * 60)) * 8:.2f},{16 + math.sin(math.radians(30 + i * 60)) * 8:.2f}" for i in range(6))
    star = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        r = 4.8 if i % 2 == 0 else 2.16
        star.append(f"{16 + math.cos(a) * r:.2f},{16.4 + math.sin(a) * r:.2f}")
    body = (f'<circle cx="16" cy="16" r="16" fill="url(#cg)"/><polygon points="{pts}" fill="#2a0f45" stroke="{ELITE}" stroke-width="1.3"/>'
            f'<polygon points="{" ".join(star)}" fill="#f3dcff"/>')
    return svg(32, 32, body, defs, res=HR), (16, 16)


PK_CW, PK_CH, PK_GAP, PK_Y = 120, 150, 14, 92  # 三选一的卡片
PK_X0 = (W - 3 * PK_CW - 2 * PK_GAP) / 2
PK_REROLL = (W / 2 - 95, 266, 190, 24)


def pick_card(key, lang, combo=False):
    """三选一的一张卡片（不含按键数字，按键画在底图上）。锚点是卡片中心"""
    w, h = PK_CW, PK_CH
    rar = CHIP_RARITY.get(key, 1)
    rc = RARITY_COL[rar]
    s = [f'<rect x="0.8" y="0.8" width="{w-1.6}" height="{h-1.6}" rx="11" fill="url(#card)" stroke="{rc}" stroke-width="1.2"/>']
    lab = tr(f"rar.{rar}", lang)
    pw = width(lab, 5.6, True) + 8
    s.append(f'<rect x="10" y="10" width="{pw:.2f}" height="10" rx="5" fill="{rc}"/>' + text(10 + pw / 2, 17.2, lab, 5.6, "#120a1f", True, "middle"))
    s.append(f'<circle cx="{w/2}" cy="56" r="25" fill="{rc}" fill-opacity="0.12"/>')
    s.append(chip_icon(key, w / 2 - 18, 38, 36))
    name, desc = tr(f"chip.{key}", lang), tr(f"chip.{key}.d", lang)
    if width(name, 12, True) > w - 12 or width(desc, 6.4) > w - 10:
        sys.exit(f"芯片卡片的文字太长：{name} / {desc}")
    s.append(text(w / 2, 102, name, 12, "#ffffff", True, "middle"))
    s.append(text(w / 2, 116, desc, 6.4, "#c8d2e3", False, "middle"))
    if key in CHIP_TACTICAL:
        s.append(text(w / 2, 136, tr("tactical", lang), 5.8, "#8fb3ff", True, "middle"))
    if combo:
        lab = tr(f"pk.combo.{key}", lang)
        if width(lab, 5.6, True) > w - 24:
            sys.exit(f"连携提示太长：{lab}")
        s.append(f'<rect x="10" y="126" width="{w-20}" height="16" rx="5" fill="#ff8a3a" fill-opacity="0.16"/>')
        s.append(text(w / 2, 137, lab, 5.6, "#ffc08a", True, "middle"))
    return svg(w, h, "".join(s), lin("card", "#1b2335", "#10151f"), res=2), (w / 2, h / 2)


def pick_screen(lang):
    """三选一的底图：压暗的战场、标题、三个卡片位置下面的按键。卡片、刷新按钮、1P / 2P 标签是 UI 的 kPick 克隆"""
    s = [f'<rect width="{W}" height="{H}" fill="#07040d" fill-opacity="0.74"/>']
    s.append(text(W / 2, 64, tr("pk.title", lang), 17, "#ffffff", True, "middle"))
    s.append(text(W / 2, 80, tr("pk.sub", lang), 7, "#c8b4e8", False, "middle"))
    for i in range(3):
        x = PK_X0 + i * (PK_CW + PK_GAP)
        button(f"pick.{i+1}", x, PK_Y, PK_CW, PK_CH)
        c, cw = chip(0, 0, str(i + 1))
        s.append(f'<g transform="translate({x + PK_CW / 2 - cw / 2:.2f},{PK_Y + PK_CH + 6})">{c}</g>')
    x, y, w, h = PK_REROLL
    button("pick.reroll", x, y, w, h)
    s.append(text(W / 2, 320, tr("pk.keys", lang), 6.8, "#c8d2e3", True, "middle"))
    return svg(W, H, "".join(s), defs_ui(), res=2), (W / 2, H / 2)


def reroll_button(kind, lang):
    """三选一的刷新按钮：ad 看视频（广告蓝），free 免费，used 本关已刷新。锚点是中心"""
    w, h = PK_REROLL[2], PK_REROLL[3]
    lab = tr(f"pk.reroll.{kind}", lang)
    if kind == "ad":
        b, bw = ad_badge(10, 7.5, lang)
        s = (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{(h-1)/2}" fill="none" stroke="{GBLUE}" stroke-width="1"/>'
             + b + play_icon(bw + 20, h / 2, "#8ab4f8", 0.9) + text(w / 2 + 12, 15.5, lab, 8, "#8ab4f8", True, "middle"))
    elif kind == "free":
        s = (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{(h-1)/2}" fill="#ffffff" fill-opacity="0.06" stroke="#3ee8ff" stroke-opacity="0.7" stroke-width="0.8"/>'
             + text(w / 2 - 6, 15.5, lab, 8, "#9fdcea", True, "middle"))
    else:
        s = (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{(h-1)/2}" fill="#ffffff" fill-opacity="0.03" stroke="#2c3850" stroke-width="0.6"/>'
             + text(w / 2, 15.5, lab, 8, "#5a6680", True, "middle"))
    if kind != "used":
        c, cw = chip(0, 0, "R")
        s += f'<g transform="translate({w - 10 - cw:.2f},7)">{c}</g>'
    return svg(w, h, s, res=HR), (w / 2, h / 2)


def pick_who(p):
    col = TANKS["player" if p == 1 else "player2"][0]
    tw = width(f"{p}P", 9, True) + 14
    body = f'<rect width="{tw:.2f}" height="15" rx="7.5" fill="{col}"/>' + text(tw / 2, 11, f"{p}P", 9, "#1a1405", True, "middle")
    return svg(tw, 15, body, res=HR), (tw / 2, 7.5)


def daily_tag(key, lang):
    s = tr(key, lang)
    w = width(s, 7, True) + 16
    body = f'<rect width="{w:.2f}" height="14" rx="7" fill="{ELITE}"/>' + text(w / 2, 9.8, s, 7, "#1a0b2b", True, "middle")
    return svg(w, 14, body, res=HR), (w / 2, 7)


def chip_costumes():
    out = [("drop", *chip_drop()), ("ci_empty", *chip_empty())]
    out += [(f"ci_{k}", *chip_badge(k)) for k in CHIP_KEYS]
    out += [(f"pickwho_{p}", *pick_who(p)) for p in (1, 2)]
    out += [(f"dtag_{k}_{lang}", *daily_tag(f"dtag.{k}", lang)) for k in ("off", "prac") for lang in LANGS]
    for lang in LANGS:
        for k in CHIP_KEYS:
            out.append((f"pc_{k}_{lang}", *pick_card(k, lang), 2))
            if k in COMBO_PARTNER:
                out.append((f"pc_{k}_combo_{lang}", *pick_card(k, lang, True), 2))
        out.append((f"pick_{lang}", *pick_screen(lang), 2))
        for kind in ("ad", "free", "used"):
            out.append((f"reroll_{kind}_{lang}", *reroll_button(kind, lang)))
    return out


# ---------- v6 车库：指挥官等级、芯片图鉴、涂装、今日任务（docs/v6/PLAN.md 第三节） ----------
# 涂装（1P，只换现代画风的外观）：都是亮色，深灰和红色留给敌方（tests/tools/test_garage.py 检查）
SKINS = [TANKS["player"], ("#ff9a3a", "#8a3d00", "#ffe0b8"), ("#eef4ff", "#7f8fb0", "#ffffff"),
         ("#ff7ab8", "#8a1f55", "#ffd6ea"), ("#8fd14f", "#3f6e1a", "#e2ffc8")]
SKIN_PRICES = [0, 1500, 2000, 2500, 3000]  # 和 main.spx 的 skinPrice 一致
CHIP_UNLOCK = {"float": 3, "stealth": 5, "magnet": 8}  # 和 main.spx 的 chipUnlockLv 一致
TASK_TARGETS = [30, 3, 2, 3, 1, 1, 1, 1]  # 任务 1~8 的目标，和 main.spx 的 taskTarget 一致
MAX_CMD = 30
GR_CELL = (200, 74, 60, 46, 66, 52)   # 图鉴格子：左上角、宽高、横竖间距
GR_SKIN = (16, 216, 30, 34)            # 涂装格子：左上角、边长、间距
GR_TASK = (200, 250, 260, 18, 22)      # 任务行：左上角、宽高、行距
GR_BACK = (16, 316, 110, 24)


def tank_icon(colors, size, rot=0):
    """独立的坦克小图（size x size）"""
    defs, body = tank_body(*colors)
    k = size / 24
    return svg(size, size, f'<g transform="rotate({rot} {size/2} {size/2}) scale({k:.4f})">{body}</g>', defs, res=HR)


def garage_screen(lang):
    s = [f'<rect width="{W}" height="{H}" fill="url(#bgH)"/>']
    s.append(text(16, 30, tr("gr.title", lang), 16, "#ffffff", True))
    s.append('<rect x="16" y="42" width="170" height="150" rx="10" fill="#ffffff" fill-opacity="0.04" stroke="#263046" stroke-width="0.7"/>')
    s.append('<rect x="28" y="66" width="146" height="5" rx="2.5" fill="#ffffff" fill-opacity="0.1"/>')
    s.append('<ellipse cx="101" cy="172" rx="58" ry="11" fill="#3ee8ff" fill-opacity="0.1" stroke="#3ee8ff" stroke-opacity="0.45" stroke-width="0.8"/>')
    s.append(text(16, 210, tr("gr.skins", lang), 7, MUTED, True))
    x0, y0, cs, gap = GR_SKIN
    for i in range(len(SKINS)):
        button(f"gr.sk.{i+1}", x0 + i * gap, y0, cs, cs)
    s.append('<circle cx="22" cy="281" r="5.5" fill="url(#gold)"/><circle cx="22" cy="281" r="3.5" fill="none" stroke="#a86a00" stroke-width="0.8"/>')
    s.append(text(16, 300, tr("gr.coins.d", lang), 5.8, MUTED))
    s.append(text(200, 54, tr("gr.codex", lang), 9, "#ffffff", True))
    s.append(text(200, 66, tr("gr.codex.d", lang), 5.8, MUTED))
    s.append(text(200, 244, tr("gr.tasks", lang), 7, MUTED, True))
    s.append(text(460, 244, tr("gr.tasks.d", lang), 5.8, MUTED, False, "end"))
    x, y, w, h = GR_BACK
    button("gr.back", x, y, w, h)
    s.append(f'<rect x="{x+0.3}" y="{y+0.3}" width="{w-0.6}" height="{h-0.6}" rx="{h/2}" fill="#ffffff" fill-opacity="0.05" stroke="#2c3850" stroke-width="0.6"/>')
    s.append(text(x + 14, y + 15.5, tr("lv.back", lang), 8.5, "#c8d2e3", True))
    c, cw = chip(0, 0, "Esc")
    s.append(f'<g transform="translate({x+w-10-cw:.2f},{y+7})">{c}</g>')
    c, cw = chip(0, 0, "1-5")
    s.append(f'<g transform="translate({186-cw:.2f},203)">{c}</g>')
    return svg(W, H, "".join(s), defs_ui(), res=2), (W / 2, H / 2)


def codex_cell(key, lang, unlocked):
    w, h = GR_CELL[2], GR_CELL[3]
    rc = RARITY_COL[CHIP_RARITY.get(key, 1)]
    if unlocked:
        s = (f'<rect x="0.4" y="0.4" width="{w-0.8}" height="{h-0.8}" rx="7" fill="#ffffff" fill-opacity="0.05" stroke="{rc}" stroke-opacity="0.7" stroke-width="0.7"/>'
             + chip_icon(key, 20, 6, 20) + text(30, 39, tr(f"chip.{key}", lang), 6.2, "#e6ecf5", True, "middle"))
    else:
        lock = f'<rect x="24" y="16" width="12" height="9" rx="2" fill="#3a4256"/><path d="M26.5 16v-3a3.5 3.5 0 0 1 7 0v3" stroke="#3a4256" stroke-width="2" fill="none"/>'
        s = (f'<rect x="0.4" y="0.4" width="{w-0.8}" height="{h-0.8}" rx="7" fill="#ffffff" fill-opacity="0.02" stroke="#263046" stroke-width="0.7"/>'
             + lock + text(30, 39, tr("gr.locklv", lang).format(n=CHIP_UNLOCK[key]), 6, "#5a6680", True, "middle"))
    return svg(w, h, s, res=HR), (w / 2, h / 2)


def skin_cell(i, st):
    """涂装格子（30x30）下面带价格；st：sel 正在用、own 已拥有、lock 没买"""
    cs = GR_SKIN[2]
    sel = st == "sel"
    s = [f'<rect x="0.6" y="0.6" width="{cs-1.2}" height="{cs-1.2}" rx="6" fill="#ffffff" fill-opacity="{0.1 if sel else 0.04}" stroke="{"#3ee8ff" if sel else "#263046"}" stroke-width="{1.2 if sel else 0.6}"/>']
    defs, body = tank_body(*SKINS[i])
    s.append(f'<g transform="translate(3 3)">{body}</g>')
    if st == "lock":
        s.append(f'<rect x="0.6" y="0.6" width="{cs-1.2}" height="{cs-1.2}" rx="6" fill="#07090f" fill-opacity="0.55"/>')
        s.append(f'<circle cx="7" cy="38" r="3" fill="url(#gold)"/>')
        s.append(text(12, 40.5, str(SKIN_PRICES[i]), 5.6, "#ffe27a", True))
    return svg(cs + 2, 44, "".join(s), defs + lin("gold", "#ffe27a", "#f29a00"), res=HR), (cs / 2, cs / 2)


def task_row(k, done, lang):
    w, h = GR_TASK[2], GR_TASK[3]
    col = "#2ee88a" if done else "#e6ecf5"
    s = [f'<rect width="{w}" height="{h}" rx="5" fill="{"#2ee88a" if done else "#ffffff"}" fill-opacity="{0.12 if done else 0.04}"/>',
         text(8, 12, tr(f"tk.{k}", lang), 6.6, col, True)]
    if done:
        s.append(f'<path d="M{w-16} 9l3 3 6-6" fill="none" stroke="#2ee88a" stroke-width="1.6"/>')
    else:
        s.append(f'<circle cx="{w-12}" cy="9" r="3.4" fill="url(#gold)"/>' + text(w - 18, 11.5, "+50", 5.6, "#ffe27a", True, "end"))
    return svg(w, h, "".join(s), lin("gold", "#ffe27a", "#f29a00"), res=HR), (0, 0)


def bar(n, total, w, h, fill):
    body = f'<rect width="{w}" height="{h}" rx="{h/2}" fill="#ffffff" fill-opacity="0.1"/>'
    if n:
        body += f'<rect width="{w*n/total:.2f}" height="{h}" rx="{h/2}" fill="{fill}"/>'
    return svg(w, h, body, lin("xpg", ELITE, "#ff7ab8", vertical=False), res=HR), (0, h / 2)


def garage_costumes():
    out = []
    for lang in LANGS:
        out.append((f"garage_{lang}", *garage_screen(lang), 2))
        for n in range(1, MAX_CMD + 1):
            out.append((f"cmd_{n}_{lang}", *text_costume(tr("gr.cmd", lang).format(n=n), 10, "#ffe27a", True, "start")))
        for i, k in enumerate(CHIP_KEYS):
            out.append((f"cx_{k}_{lang}", *codex_cell(k, lang, True)))
            if k in CHIP_UNLOCK:
                out.append((f"cxl_{k}_{lang}", *codex_cell(k, lang, False)))
                out.append((f"nx_{k}_{lang}", *text_costume(tr("gr.next", lang).format(chip=tr(f"chip.{k}", lang), n=CHIP_UNLOCK[k]), 6, "#d9b8ff", False, "start")))
        out.append((f"nx_all_{lang}", *text_costume(tr("gr.next.all", lang), 6, "#d9b8ff", False, "start")))
        for k in range(1, len(TASK_TARGETS) + 1):
            for done in (0, 1):
                out.append((f"tk_{k}_{done}_{lang}", *task_row(k, done, lang)))
    for n in range(21):
        out.append((f"xp_{n}", *bar(n, 20, 146, 5, "url(#xpg)")))
    for n in range(11):
        out.append((f"tp_{n}", *bar(n, 10, 60, 4, "#2ee88a" if n == 10 else ELITE)))
    for i in range(len(SKINS)):
        out.append((f"skp_{i}", tank_icon(SKINS[i], 70, 20), (35, 35)))
        for st in ("sel", "own", "lock"):
            out.append((f"sk_{i}_{st}", *skin_cell(i, st)))
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


STAGE_LABEL_MAX = 150  # 关卡名最宽多少：顶栏右边还有“敌军”和剩余格子


def build_hud():
    """所有界面造型都放进一个 UI 精灵（spx 解释器对精灵类型数量有上限，见 UI.spx）"""
    costumes = []
    for key, (size, fill, bold, anchor) in LABELS.items():
        for lang in LANGS:
            if key.startswith("stage.") and width(tr(key, lang), size, bold) > STAGE_LABEL_MAX:
                sys.exit(f"关卡名太长，会和顶栏的“敌军”重叠：{tr(key, lang)}")
            c, piv = text_costume(tr(key, lang), size, fill, bold, anchor)
            costumes.append((f"{key}_{lang}", c, piv))
    for k in [f"stage.{n}" for n in range(1, 9)] + ["stage.custom"]:
        for lang in LANGS:
            c, piv = stage_coop_costume(k, lang)
            costumes.append((f"{k}.co_{lang}", c, piv))
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
    costumes += [(f"ally_{p}_{lv}", *ally_costume(p, lv)) for p in (1, 2) for lv in range(1, 5)]
    costumes += chip_costumes()
    costumes += garage_costumes()
    costumes += ed_widgets()
    update_generated_block(os.path.join(ROOT, "TankBattle", "UI.spx"), [
        f'\tif st == "{st}" {{\n\t\treturn {dw:.3f}, {cw:.3f}\n\t}}\n' for st, (dw, cw) in widths.items()])
    costumes += screen_costumes()
    update_generated_block(os.path.join(ROOT, "TankBattle", "UI.spx"), hit_lines(), "hit")
    return write_sprite("UI", costumes)


def stage_index():
    """舞台配置：窗口标题（桌面版窗口上显示；不设置时 spx 会用临时目录名，是一串哈希）"""
    p = os.path.join(ASSETS, "index.json")
    with open(p, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["run"] = {**cfg.get("run", {}), "title": "坦克大战 2026 · Brickline Tanks"}
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")


def main():
    out = [
        write("field.svg", backdrop_classic()),
        write("field_m.svg", backdrop_modern()),
        write("sprites/Tile/brick_m.svg", brick_m()),
        write("sprites/Tile/cracked_m.svg", brick_m(True)),
        write("sprites/Tile/steel_m.svg", steel_m()),
        write("sprites/Tile/water.svg", water_classic()),
        write("sprites/Tile/water_m.svg", water_m()),
        write("sprites/Tile/grass.svg", grass_classic()),
        write("sprites/Tile/grass_m.svg", grass_m()),
        write("sprites/Tile/eagle_m.svg", eagle_m()),
        write("sprites/Tile/broken_m.svg", broken_m()),
        write("sprites/Player/player_m.svg", tank_m(*TANKS["player"])),
        write("sprites/Player/player2_m.svg", tank_m(*TANKS["player2"])),
        write("sprites/Player/player2.svg", player2_classic()),
        *[write(f"sprites/Player/player_s{i}_m.svg", tank_m(*SKINS[i])) for i in range(1, len(SKINS))],
        *[write(f"sprites/Enemy/{k}_m.svg", foe_m(k)) for k in FOE_KINDS],
        *[write(f"sprites/Enemy/{k}_e_m.svg", foe_m(k, ELITE)) for k in FOE_KINDS],
        *[write(f"sprites/Enemy/{k}.svg", foe_classic(k)) for k in FOE_KINDS],
        *[write(f"sprites/Enemy/{k}_e.svg", foe_classic(k, PIXEL_ELITE)) for k in FOE_KINDS],
        write("sprites/PBullet/bullet_m.svg", bullet_m("#ffe27a", "#ffb000")),
        write("sprites/EBullet/bullet_m.svg", bullet_m("#ff8a7a", "#ff2a2a")),
    ]
    for i in range(3):
        out.append(write(f"sprites/Boom/b{i+1}_m.svg", boom_m(i)))
    player_index()
    enemy_index()
    stage_index()
    hud = build_hud()
    print(f"generated {len(out)} art files, {hud} HUD costumes")


if __name__ == "__main__":
    main()
