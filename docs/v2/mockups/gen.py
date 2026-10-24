#!/usr/bin/env python3
"""生成 v2.0 效果图（中 / 英各一套 SVG）。

画布按 XBuilder 真实视口 480x360 设计（XBuilder 固定运行尺寸，不支持 16:9），导出时放大 3 倍。
字体内嵌进 SVG（Noto Sans SC 子集），并在生成时检查每个字符都有字形，缺字直接报错，避免乱码。

用法：python3 gen.py --font NotoSansSC[wght].ttf   （需要 fonttools、brotli）
"""
import argparse
import base64
import io
import math
import os
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

from i18n import STRINGS, tr

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 480, 360
C = 24                  # 格子边长，与游戏一致
FX, FY = 12, 30         # 战场左上角（13x13 = 312）
PX = FX + 13 * C + 12   # 右侧面板 x
PW = W - PX - 12        # 右侧面板宽
FAM = "TankSans"
GBLUE = "#1a73e8"       # 广告按钮使用 Google 蓝，和游戏自身的橙色主按钮区分

USED = set()            # 所有出现过的文字，用于字体子集和缺字检查

LEVEL = [
    ".............",
    ".B.B.B.B.B.B.",
    ".B.b.B.B.B.B.",
    ".B.B.BSB.B.B.",
    ".B.B.....b.B.",
    "GG...B.B...GG",
    "SS.BB...BB.SS",
    "WW...B.B...WW",
    ".B.B.BBB.B.B.",
    ".B.B.B.B.b.B.",
    ".B.B.....B.B.",
    ".B.B.BbB.B.B.",
    ".....BEB.....",
]


def cx(c):
    return FX + c * C + C / 2


def cy(r):
    return FY + r * C + C / 2


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def t(x, y, s, size=10, fill="#e6ecf5", bold=False, anchor="start", extra=""):
    USED.update(s)
    w = 800 if bold else 500
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FAM}" font-size="{size}" font-weight="{w}" '
            f'fill="{fill}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')


DEFS = """
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#121826"/><stop offset="1" stop-color="#080b12"/></linearGradient>
  <radialGradient id="ground" cx="0.5" cy="0.45" r="0.75"><stop offset="0" stop-color="#2b3838"/><stop offset="0.6" stop-color="#1d2729"/><stop offset="1" stop-color="#111819"/></radialGradient>
  <linearGradient id="brickTop" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#df7448"/><stop offset="1" stop-color="#b04a27"/></linearGradient>
  <linearGradient id="steelTop" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c9d4de"/><stop offset="0.5" stop-color="#7f8d9a"/><stop offset="1" stop-color="#55616c"/></linearGradient>
  <linearGradient id="water" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1b6fa8"/><stop offset="1" stop-color="#0d3f66"/></linearGradient>
  <radialGradient id="glowY" r="0.5"><stop offset="0" stop-color="#fff6c2"/><stop offset="0.35" stop-color="#ffd23a" stop-opacity="0.9"/><stop offset="1" stop-color="#ffb000" stop-opacity="0"/></radialGradient>
  <radialGradient id="glowR" r="0.5"><stop offset="0" stop-color="#ffe0e0"/><stop offset="0.35" stop-color="#ff4a3a" stop-opacity="0.9"/><stop offset="1" stop-color="#ff2a2a" stop-opacity="0"/></radialGradient>
  <radialGradient id="boom" r="0.5"><stop offset="0" stop-color="#fffbe6"/><stop offset="0.25" stop-color="#ffd54a"/><stop offset="0.55" stop-color="#ff6a1a" stop-opacity="0.85"/><stop offset="1" stop-color="#7a1a00" stop-opacity="0"/></radialGradient>
  <radialGradient id="shield" r="0.5"><stop offset="0.6" stop-color="#3ee8ff" stop-opacity="0"/><stop offset="0.92" stop-color="#3ee8ff" stop-opacity="0.45"/><stop offset="1" stop-color="#bff8ff" stop-opacity="0.9"/></radialGradient>
  <radialGradient id="vignette" r="0.75"><stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.5"/></radialGradient>
  <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#182031"/><stop offset="1" stop-color="#10151f"/></linearGradient>
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffe27a"/><stop offset="1" stop-color="#f29a00"/></linearGradient>
  <linearGradient id="cta" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff9a1a"/><stop offset="1" stop-color="#ff5a1a"/></linearGradient>
  <linearGradient id="green" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#2ee88a"/><stop offset="1" stop-color="#14b866"/></linearGradient>
  <filter id="drop" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="1.6" dy="2.4" stdDeviation="1.4" flood-color="#000" flood-opacity="0.55"/></filter>
  <filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000" flood-opacity="0.55"/></filter>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="1.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="blur"><feGaussianBlur stdDeviation="3"/></filter>
</defs>
"""


# ---------- 地形 ----------
def brick(x, y, cracked=False):
    h = 3
    s = ['<g filter="url(#drop)">',
         f'<rect x="{x}" y="{y+h}" width="{C}" height="{C-h}" fill="#6e2a12"/>',
         f'<rect x="{x}" y="{y}" width="{C}" height="{C-h}" fill="url(#brickTop)"/>']
    bh = (C - h) / 4
    for i in range(4):
        yy = y + i * bh
        s.append(f'<line x1="{x}" y1="{yy:.2f}" x2="{x+C}" y2="{yy:.2f}" stroke="#7a2e14" stroke-width="0.7"/>')
        off = 0 if i % 2 == 0 else C / 4
        for k in range(3):
            xx = x + off + k * C / 2
            if x < xx < x + C:
                s.append(f'<line x1="{xx:.2f}" y1="{yy:.2f}" x2="{xx:.2f}" y2="{yy+bh:.2f}" stroke="#7a2e14" stroke-width="0.7"/>')
    s.append(f'<rect x="{x}" y="{y}" width="{C}" height="0.9" fill="#ffb08a" opacity="0.6"/>')
    if cracked:
        s.append(f'<path d="M{x+5} {y+2} l3.5 4.5 l-2 3.5 l4.5 4 l-1.5 4.5 M{x+14} {y+1} l-2 5.5 l4 3" stroke="#2a0d03" stroke-width="1.1" fill="none"/>')
    s.append('</g>')
    return "".join(s)


def steel(x, y):
    h = 3
    s = ['<g filter="url(#drop)">',
         f'<rect x="{x}" y="{y+h}" width="{C}" height="{C-h}" fill="#2f363d"/>',
         f'<rect x="{x}" y="{y}" width="{C}" height="{C-h}" rx="1" fill="url(#steelTop)"/>',
         f'<rect x="{x+3}" y="{y+2.5}" width="{C-6}" height="{C-h-5}" rx="1" fill="none" stroke="#e8f0f6" stroke-opacity="0.5" stroke-width="0.6"/>']
    for dx, dy in ((3.5, 3), (C - 3.5, 3), (3.5, C - h - 3), (C - 3.5, C - h - 3)):
        s.append(f'<circle cx="{x+dx}" cy="{y+dy}" r="1" fill="#3a434c"/>')
    s.append(f'<path d="M{x+2} {y+C-h-2} L{x+C-9} {y+2}" stroke="#fff" stroke-opacity="0.25" stroke-width="3"/>')
    s.append('</g>')
    return "".join(s)


def grass(x, y):
    s = []
    for i in range(7):
        bx = x + 3 + (i * 8) % 20
        by = y + 3 + (i * 11) % 18
        s.append(f'<circle cx="{bx}" cy="{by}" r="{5 + i % 3}" fill="{["#2f7d3a","#3c9a46","#256b30"][i%3]}"/>')
    return f'<g opacity="0.96">{"".join(s)}</g>'


def water(x, y):
    return (f'<rect x="{x}" y="{y}" width="{C}" height="{C}" fill="url(#water)"/>'
            f'<path d="M{x+3} {y+8} q3 -2.5 6 0 t6 0 M{x+8} {y+16} q3 -2.5 6 0 t6 0" stroke="#7fd4ff" stroke-opacity="0.55" stroke-width="1" fill="none"/>')


def eagle(x, y):
    m, k = x + C / 2, C / 52
    return (f'<g filter="url(#drop)"><rect x="{x+1}" y="{y+1}" width="{C-2}" height="{C-2}" rx="4" fill="#1b2a3a" stroke="#3ee8ff" stroke-opacity="0.7"/>'
            f'<g transform="translate({m},{y}) scale({k})"><path d="M0 10 l6 8 l12 -4 l-6 12 l8 4 l-14 4 l-6 10 l-6 -10 l-14 -4 l8 -4 l-6 -12 l12 4 z" fill="url(#gold)"/></g></g>')


def field():
    s = [f'<rect x="{FX-4}" y="{FY-4}" width="{13*C+8}" height="{13*C+8}" rx="6" fill="#0a0e14" stroke="#2a3446" stroke-width="0.8"/>',
         f'<rect x="{FX}" y="{FY}" width="{13*C}" height="{13*C}" fill="url(#ground)"/>']
    for i in range(1, 13):
        s.append(f'<path d="M{FX+i*C} {FY} V{FY+13*C} M{FX} {FY+i*C} H{FX+13*C}" stroke="#fff" stroke-opacity="0.03" stroke-width="0.5"/>')
    under, walls, over = [], [], []
    for r, row in enumerate(LEVEL):
        for c, ch in enumerate(row):
            x, y = FX + c * C, FY + r * C
            if ch == "W":
                under.append(water(x, y))
            elif ch in "Bb":
                walls.append(brick(x, y, ch == "b"))
            elif ch == "S":
                walls.append(steel(x, y))
            elif ch == "E":
                walls.append(eagle(x, y))
            elif ch == "G":
                over.append(grass(x, y))
    return "".join(s + under + walls), "".join(over)


# ---------- 角色与特效 ----------
PAL = {
    "player": ("#ffd23a", "#b8860b", "#fff3b0"),
    "red": ("#ff5a4a", "#9c1f16", "#ffc2b8"),
    "blue": ("#4aa8ff", "#1c4f8f", "#c8e6ff"),
    "green": ("#6fd06a", "#2e6e2a", "#d2f5cf"),
}


def tank(x, y, ang, kind, size=22, hp=None, hpmax=None, shield=False, shadow=True):
    main, dark, light = PAL[kind]
    k = size / 46
    treads = "".join(f'<rect x="-22" y="{-20+i*6}" width="10" height="3" fill="#44464c"/><rect x="12" y="{-20+i*6}" width="10" height="3" fill="#44464c"/>' for i in range(7))
    body = f"""<g transform="translate({x:.2f},{y:.2f}) rotate({ang}) scale({k:.4f})">
  <rect x="-23" y="-22" width="12" height="44" rx="4" fill="#1e1e22"/><rect x="11" y="-22" width="12" height="44" rx="4" fill="#1e1e22"/>{treads}
  <rect x="-13" y="-17" width="26" height="36" rx="5" fill="{dark}"/><rect x="-12" y="-17" width="24" height="32" rx="5" fill="{main}"/>
  <rect x="-12" y="-17" width="24" height="5" rx="2" fill="{light}" opacity="0.6"/>
  <rect x="-3.5" y="-34" width="7" height="24" rx="2" fill="{dark}"/><rect x="-2" y="-34" width="2.5" height="22" fill="{light}" opacity="0.7"/>
  <rect x="-5" y="-36" width="10" height="5" rx="1.5" fill="#2a2a2e"/>
  <circle cx="0" cy="2" r="10" fill="{dark}"/><circle cx="0" cy="0" r="9.5" fill="{main}"/><circle cx="-3" cy="-3" r="3.5" fill="{light}" opacity="0.8"/>
</g>"""
    s = [f'<g filter="url(#drop)">{body}</g>' if shadow else body]
    if shield:
        s.append(f'<circle cx="{x}" cy="{y}" r="{size*0.78:.1f}" fill="url(#shield)"/>')
        s.append(f'<circle cx="{x}" cy="{y}" r="{size*0.78:.1f}" fill="none" stroke="#9ff4ff" stroke-width="0.7" stroke-dasharray="4 3" opacity="0.8"/>')
    if hp is not None:
        w = 20
        s.append(f'<rect x="{x-w/2}" y="{y-size/2-7}" width="{w}" height="3" rx="1.5" fill="#000" opacity="0.6"/>')
        s.append(f'<rect x="{x-w/2+0.5}" y="{y-size/2-6.5}" width="{(w-1)*hp/hpmax:.1f}" height="2" rx="1" fill="#ff4a3a"/>')
    return "".join(s)


def bullet(x, y, ang, color="Y"):
    g = "glowY" if color == "Y" else "glowR"
    c = "#fff2a0" if color == "Y" else "#ffb0a0"
    dx, dy = math.sin(math.radians(ang)), -math.cos(math.radians(ang))
    return (f'<line x1="{x}" y1="{y}" x2="{x-dx*20:.1f}" y2="{y-dy*20:.1f}" stroke="{c}" stroke-opacity="0.35" stroke-width="2.4" stroke-linecap="round"/>'
            f'<circle cx="{x}" cy="{y}" r="6" fill="url(#{g})"/><circle cx="{x}" cy="{y}" r="1.8" fill="#fff"/>')


def explosion(x, y, r=16):
    s = [f'<circle cx="{x}" cy="{y}" r="{r*1.6}" fill="url(#boom)" opacity="0.5"/>',
         f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#boom)"/>',
         f'<circle cx="{x}" cy="{y}" r="{r*1.25}" fill="none" stroke="#ffd27a" stroke-opacity="0.5" stroke-width="1.2"/>']
    for i in range(10):
        a = i * 36 + 10
        d = r * (0.9 + (i % 3) * 0.35)
        px, py = x + math.cos(math.radians(a)) * d, y + math.sin(math.radians(a)) * d
        s.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{2+i%3}" height="{2+i%2*1.5}" fill="{["#ffcf4a","#ff7a2a","#5a5a5a"][i%3]}" transform="rotate({a} {px:.1f} {py:.1f})"/>')
    return "".join(s)


# ---------- 图标（不用 emoji，游戏里同样用矢量图） ----------
def icon(kind, x, y, s=1.0, col="#fff"):
    """以 (x, y) 为中心、约 12*s 大小的图标"""
    g = f'<g transform="translate({x},{y}) scale({s})">'
    if kind == "bullet":
        g += f'<rect x="-2" y="-5" width="4" height="10" rx="2" fill="{col}"/><rect x="-2" y="3" width="4" height="2" fill="#000" opacity="0.3"/>'
    elif kind == "double":
        g += f'<rect x="-5" y="-5" width="3.5" height="10" rx="1.75" fill="{col}"/><rect x="1.5" y="-5" width="3.5" height="10" rx="1.75" fill="{col}"/>'
    elif kind == "shield":
        g += f'<path d="M0 -6 L5.5 -4 V0.5 C5.5 4 3 5.5 0 6.5 C-3 5.5 -5.5 4 -5.5 0.5 V-4 Z" fill="{col}"/>'
    elif kind == "drone":
        g += (f'<circle cx="0" cy="0" r="2.4" fill="{col}"/><path d="M-4.5 -4.5 L4.5 4.5 M4.5 -4.5 L-4.5 4.5" stroke="{col}" stroke-width="1.3"/>'
              + "".join(f'<circle cx="{a}" cy="{b}" r="2" fill="none" stroke="{col}" stroke-width="0.9"/>' for a, b in ((-4.5, -4.5), (4.5, -4.5), (-4.5, 4.5), (4.5, 4.5))))
    elif kind == "ricochet":
        g += f'<path d="M-5 5 L0 -3 L5 5" fill="none" stroke="{col}" stroke-width="1.6" stroke-linejoin="round"/><rect x="-6" y="-6" width="12" height="2" fill="{col}" opacity="0.6"/>'
    elif kind == "play":
        g += f'<path d="M-3 -4 L4 0 L-3 4 Z" fill="{col}"/>'
    elif kind == "gem":
        g += f'<path d="M-5 -2 L-2.5 -5 H2.5 L5 -2 L0 5 Z" fill="{col}"/><path d="M-5 -2 H5 M-2.5 -5 L0 5 L2.5 -5" stroke="#fff" stroke-opacity="0.5" stroke-width="0.5" fill="none"/>'
    elif kind == "coin":
        g += f'<circle r="5" fill="url(#gold)"/><circle r="3.2" fill="none" stroke="#a86a00" stroke-width="0.8"/>'
    elif kind == "close":
        g += f'<path d="M-2.5 -2.5 L2.5 2.5 M2.5 -2.5 L-2.5 2.5" stroke="{col}" stroke-width="1"/>'
    elif kind == "adchoices":
        g += f'<path d="M-3 -3.5 L3.5 0 L-3 3.5 Z" fill="none" stroke="{col}" stroke-width="0.8"/><circle cx="-0.5" cy="0" r="0.8" fill="{col}"/>'
    elif kind == "star":
        pts = " ".join(f"{math.cos(math.radians(-90+k*36))*(6 if k%2==0 else 2.6):.2f},{math.sin(math.radians(-90+k*36))*(6 if k%2==0 else 2.6):.2f}" for k in range(10))
        g += f'<polygon points="{pts}" fill="{col}"/>'
    elif kind == "chev":
        g += f'<path d="M-1.5 -3 L1.5 0 L-1.5 3" fill="none" stroke="{col}" stroke-width="1.2"/>'
    return g + "</g>"


def ad_badge(x, y, lang):
    """Google 风格的 “广告/Ad” 标识：小号描边胶囊"""
    s = tr("ad.badge", lang)
    w = 7 + len(s) * (7 if lang == "zh" else 5)
    return (f'<rect x="{x}" y="{y}" width="{w}" height="9" rx="2" fill="none" stroke="#f2c94c" stroke-width="0.6"/>'
            + t(x + w / 2, y + 7, s, 6.2, "#f2c94c", True, "middle")), w


def lang_toggle(x, y, lang):
    """语言切换：中 | EN，当前语言高亮"""
    s = [f'<rect x="{x}" y="{y}" width="40" height="14" rx="7" fill="#ffffff" fill-opacity="0.06" stroke="#2c3850" stroke-width="0.6"/>']
    hx = x + 1 if lang == "zh" else x + 20
    s.append(f'<rect x="{hx}" y="{y+1}" width="19" height="12" rx="6" fill="#3ee8ff" fill-opacity="0.9"/>')
    s.append(t(x + 10.5, y + 10, tr("lang.zh", lang), 7.5, "#06232b" if lang == "zh" else "#9fb0cc", True, "middle"))
    s.append(t(x + 29.5, y + 10, tr("lang.en", lang), 7.5, "#06232b" if lang == "en" else "#9fb0cc", True, "middle"))
    return "".join(s)


def native_ad(x, y, w, h, lang):
    """原生广告卡：Google AdMob Native 样式，安静地放在 HUD 面板底部，不进入战场"""
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#ffffff" fill-opacity="0.035" stroke="#2c3850" stroke-width="0.6"/>']
    b, bw = ad_badge(x + 6, y + 6, lang)
    s.append(b)
    s.append(icon("adchoices", x + w - 15, y + 10.5, 0.8, "#6b778f") + icon("close", x + w - 7, y + 10.5, 0.9, "#6b778f"))
    # 品牌 logo 占位
    s.append(f'<rect x="{x+6}" y="{y+20}" width="20" height="20" rx="4" fill="#ffffff"/>')
    s.append(f'<circle cx="{x+16}" cy="{y+30}" r="6" fill="{GBLUE}"/><circle cx="{x+16}" cy="{y+30}" r="2.6" fill="#fff"/>')
    s.append(t(x + 31, y + 28, tr("ad.brand", lang), 7.5, "#e6ecf5", True))
    s.append(t(x + 31, y + 38, tr("ad.head", lang), 6.2, "#8a96ad"))
    s.append(f'<rect x="{x+6}" y="{y+h-20}" width="{w-12}" height="14" rx="7" fill="{GBLUE}"/>')
    s.append(t(x + w / 2, y + h - 10.2, tr("ad.cta", lang), 7.2, "#fff", True, "middle"))
    return "".join(s)


def panel(x, y, w, h, r=6):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#panel)" stroke="#263046" stroke-width="0.6"/>'


def topbar(lang):
    s = [t(FX, 20, tr("stage", lang), 10, "#fff", True)]
    s.append(t(PX - 12 - 120, 20, tr("enemies", lang), 7.5, "#8a96ad", False, "end"))
    for i in range(20):
        x = PX - 12 - 115 + i * 5.8
        col = "#ff5a4a" if i >= 7 else "#3a4256"
        s.append(f'<rect x="{x:.1f}" y="13" width="4" height="8" rx="1" fill="{col}"/>')
    s.append(lang_toggle(W - 12 - 40, 9, lang))
    return "".join(s)


def right_hud(lang):
    x, w = PX, PW
    s = [panel(x, FY - 4, w, 13 * C + 8)]
    s.append(t(x + 8, FY + 10, tr("score", lang), 6.8, "#8a96ad", True))
    s.append(t(x + 8, FY + 30, "12,450", 18, "#fff", True))
    s.append(t(x + 8, FY + 46, tr("combo", lang), 6.8, "#8a96ad", True))
    s.append(t(x + w - 8, FY + 46, "×3", 8, "#ff9a6a", True, "end"))
    s.append(f'<rect x="{x+8}" y="{FY+50}" width="{w-16}" height="4" rx="2" fill="#fff" fill-opacity="0.08"/><rect x="{x+8}" y="{FY+50}" width="{(w-16)*0.62:.1f}" height="4" rx="2" fill="url(#cta)"/>')
    s.append(t(x + 8, FY + 70, tr("lives", lang), 6.8, "#8a96ad", True))
    for i in range(3):
        tk = tank(x + 14 + i * 16, FY + 82, 0, "player", 12, shadow=False)
        s.append(tk if i < 2 else f'<g opacity="0.22">{tk}</g>')
    s.append(t(x + 8, FY + 104, tr("perks", lang), 6.8, "#8a96ad", True))
    perks = [("bullet", "#ffd23a"), ("double", "#4aa8ff"), ("shield", "#3ee8ff"), ("drone", "#6fd06a")]
    for i, (k, col) in enumerate(perks):
        px = x + 8 + i * 28
        s.append(f'<rect x="{px}" y="{FY+110}" width="22" height="22" rx="5" fill="{col}" fill-opacity="0.13" stroke="{col}" stroke-opacity="0.55" stroke-width="0.7"/>')
        s.append(icon(k, px + 11, FY + 121, 1.0, col))
    s.append(t(x + 8, FY + 152, tr("rank", lang), 6.8, "#8a96ad", True))
    s.append(t(x + w - 8, FY + 152, "#128", 8, "#ffe27a", True, "end"))
    s.append(f'<line x1="{x+8}" y1="{FY+162}" x2="{x+w-8}" y2="{FY+162}" stroke="#263046" stroke-width="0.6"/>')
    for i, (key, k) in enumerate((("T", "hint.style"), ("L", "hint.lang"))):
        ky = FY + 170 + i * 16
        s.append(f'<rect x="{x+8}" y="{ky}" width="11" height="11" rx="2.5" fill="#fff" fill-opacity="0.1"/>' + t(x + 13.5, ky + 8.2, key, 7, "#fff", True, "middle"))
        s.append(t(x + 24, ky + 8.2, tr(k, lang), 6.8, "#8a96ad"))
    s.append(native_ad(x + 6, FY + 13 * C - 92, w - 12, 86, lang))
    return "".join(s)


def battle_layer(lang):
    base, over = field()
    s = [base]
    s.append(tank(cx(4), cy(12) - 2, 0, "player", shield=True))
    s.append(bullet(cx(4), cy(9) + 5, 0))
    s.append(tank(cx(6), cy(4), 180, "red"))
    s.append(bullet(cx(6), cy(5) + 16, 180, "R"))
    s.append(tank(cx(12), cy(4), 0, "green", hp=2, hpmax=3))
    s.append(tank(cx(2), cy(4), 90, "blue", 20))
    s.append(tank(cx(0), cy(10), 0, "player", 20))
    s.append(t(cx(0), cy(10) + 18, "2P", 6.5, "#ffe9a0", True, "middle"))
    s.append(explosion(cx(8), cy(4) - 2))
    s.append(over)
    s.append(t(cx(8), cy(4) - 20, "+200", 10, "#ffe27a", True, "middle", 'filter="url(#glow)"'))
    s.append(t(cx(8), cy(4) + 22, "COMBO ×3", 6.5, "#ff9a6a", True, "middle"))
    s.append(f'<circle cx="{cx(12)}" cy="{cy(0)}" r="10" fill="none" stroke="#ff4a3a" stroke-width="0.9" stroke-dasharray="2.5 2"/>')
    s.append(f'<rect x="{FX}" y="{FY}" width="{13*C}" height="{13*C}" fill="url(#vignette)"/>')
    return "".join(s)


def full_battle(lang):
    return battle_layer(lang) + topbar(lang) + right_hud(lang)


# ---------- 画面 1：对局 ----------
def mock_battle(lang):
    return full_battle(lang)


# ---------- 画面 2：通关 + 强化三选一 ----------
def mock_clear(lang):
    s = [f'<g filter="url(#blur)" opacity="0.5">{full_battle(lang)}</g>',
         f'<rect width="{W}" height="{H}" fill="#05070c" opacity="0.62"/>']
    m = W / 2
    s.append(t(m, 46, tr("clear", lang), 20, "#fff", True, "middle"))
    for i, on in enumerate([1, 1, 0]):
        s.append(icon("star", m - 18 + i * 18, 62, 1.15, "url(#gold)" if on else "#3a4256"))
    stats = [("st.kills", "20"), ("st.time", "2:41"), ("st.combo", "×7"), ("st.base", "100%")]
    for i, (k, v) in enumerate(stats):
        x = m - 135 + i * 90
        s.append(t(x, 92, v, 12, "#fff", True, "middle") + t(x, 104, tr(k, lang), 6.8, "#8a96ad", False, "middle"))
    # 奖励：金币 + 可选的激励视频（次要按钮，不抢主按钮）
    s.append(f'<rect x="{m-120}" y="114" width="240" height="28" rx="8" fill="#fff" fill-opacity="0.05" stroke="#2c3850" stroke-width="0.6"/>')
    s.append(icon("coin", m - 104, 128, 1.0) + t(m - 94, 131.5, f'{tr("coins", lang)} +320', 9.5, "#ffe27a", True))
    s.append(f'<rect x="{m+8}" y="119" width="106" height="18" rx="9" fill="none" stroke="{GBLUE}" stroke-width="0.9"/>')
    s.append(icon("play", m + 20, 128, 0.9, "#8ab4f8") + t(m + 66, 131, tr("ad.double", lang), 7.2, "#8ab4f8", True, "middle"))
    # 三选一
    s.append(t(m, 162, tr("choose", lang), 8.5, "#c8d2e3", True, "middle"))
    cards = [("r.rare", "#4aa8ff", "pk.ricochet", "ricochet"), ("r.epic", "#b06bff", "pk.drone", "drone"), ("r.common", "#9fb0cc", "pk.iron", "shield")]
    for i, (rk, col, pk, ic) in enumerate(cards):
        x, y, w, h = m - 156 + i * 106, 170, 100, 118
        sel = i == 1
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#141b29" stroke="{col}" stroke-width="{1.4 if sel else 0.7}" filter="url(#soft)"/>')
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="54" rx="8" fill="{col}" fill-opacity="0.14"/>')
        s.append(f'<circle cx="{x+w/2}" cy="{y+29}" r="15" fill="{col}" fill-opacity="0.22" stroke="{col}" stroke-width="0.9"/>')
        s.append(icon(ic, x + w / 2, y + 29, 1.5, col))
        rw = 8 + len(tr(rk, lang)) * (6.2 if lang == "zh" else 4.6)
        s.append(f'<rect x="{x+5}" y="{y+5}" width="{rw:.1f}" height="10" rx="5" fill="{col}"/>' + t(x + 5 + rw / 2, y + 12.6, tr(rk, lang), 5.8, "#0b0f18", True, "middle"))
        s.append(t(x + w / 2, y + 74, tr(pk, lang), 9.5, "#fff", True, "middle"))
        s.append(t(x + w / 2, y + 90, tr(pk + ".d", lang), 6.5, "#a8b4ca", False, "middle"))
        if sel:
            s.append(icon("star", x + w / 2, y + 106, 0.7, col))
    s.append(f'<rect x="{m-55}" y="300" width="110" height="24" rx="12" fill="url(#cta)" filter="url(#soft)"/>')
    s.append(t(m - 4, 316, tr("continue", lang), 9.5, "#fff", True, "middle") + icon("chev", m + 30, 312, 1, "#fff"))
    return "".join(s)


# ---------- 画面 3：基地失守 · 复活 ----------
def mock_revive(lang):
    s = [f'<g filter="url(#blur)" opacity="0.55">{full_battle(lang)}{explosion(cx(6), cy(12), 26)}</g>',
         f'<rect width="{W}" height="{H}" fill="#1f0407" opacity="0.62"/>']
    m, mx, my, mw, mh = W / 2, W / 2 - 100, 58, 200, 248
    s.append(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="12" fill="#121826" stroke="#ff4a3a" stroke-opacity="0.5" stroke-width="0.8" filter="url(#soft)"/>')
    s.append(t(m, my + 30, tr("lost", lang), 17, "#ff5a4a", True, "middle"))
    s.append(t(m, my + 46, tr("lost.sub", lang), 7.5, "#c8d2e3", False, "middle"))
    r, ccy = 22, my + 84
    circ = 2 * math.pi * r
    s.append(f'<circle cx="{m}" cy="{ccy}" r="{r}" fill="none" stroke="#2a3346" stroke-width="4"/>')
    s.append(f'<circle cx="{m}" cy="{ccy}" r="{r}" fill="none" stroke="#ff9a1a" stroke-width="4" stroke-linecap="round" stroke-dasharray="{circ*0.7:.1f} {circ:.1f}" transform="rotate(-90 {m} {ccy})"/>')
    s.append(t(m, ccy + 7.5, "7", 21, "#fff", True, "middle"))
    # 激励视频复活（主按钮）
    by = my + 122
    s.append(f'<rect x="{mx+16}" y="{by}" width="{mw-32}" height="34" rx="17" fill="url(#cta)" filter="url(#soft)"/>')
    s.append(icon("play", mx + 34, by + 13, 1.0, "#fff") + t(m + 6, by + 16, tr("revive.ad", lang), 9.5, "#fff", True, "middle"))
    s.append(t(m + 6, by + 27, tr("revive.ad.sub", lang), 6.2, "#fff2e0", False, "middle"))
    s.append(t(m, by + 46, tr("revive.ad.len", lang), 6.2, "#8a96ad", False, "middle"))
    # 钻石复活
    gy = by + 54
    s.append(f'<rect x="{mx+16}" y="{gy}" width="{mw-32}" height="26" rx="13" fill="#fff" fill-opacity="0.05" stroke="#3a4660" stroke-width="0.7"/>')
    s.append(icon("gem", m - 44 if lang == "zh" else m - 52, gy + 13, 0.95, "#8ad4ff") + t(m + 6, gy + 16.5, tr("revive.gem", lang), 8.5, "#c8e6ff", True, "middle"))
    s.append(t(m, gy + 46, tr("giveup", lang), 7.5, "#6b778f", False, "middle"))
    return "".join(s)


# ---------- 画面 4：主页 ----------
def mock_home(lang):
    s = [f'<circle cx="300" cy="190" r="140" fill="#3ee8ff" opacity="0.05"/><circle cx="300" cy="190" r="90" fill="#ffd23a" opacity="0.05"/>']
    s.append(t(16, 30, tr("title", lang), 18, "#fff", True))
    tw = 76 if lang == "zh" else 116
    s.append(t(16 + tw, 30, "2026", 18, "url(#gold)", True))
    s.append(t(16, 42, tr("subtitle", lang), 7, "#7f8ba3", True, "start", 'letter-spacing="1.5"'))
    # 顶部货币 + 语言
    s.append(f'<rect x="300" y="15" width="56" height="16" rx="8" fill="#fff" fill-opacity="0.06"/>' + icon("coin", 309, 23, 0.9) + t(318, 26.5, "8,640", 8, "#ffe27a", True))
    s.append(f'<rect x="362" y="15" width="48" height="16" rx="8" fill="#fff" fill-opacity="0.06"/>' + icon("gem", 371, 23, 0.85, "#8ad4ff") + t(380, 26.5, "320", 8, "#c8e6ff", True))
    s.append(lang_toggle(W - 16 - 40, 16, lang))
    # 左侧菜单
    menu = [("m.campaign", True), ("m.daily", False), ("m.coop", False), ("m.ai", False)]
    for i, (k, hi) in enumerate(menu):
        y = 58 + i * 52
        fill = 'fill="url(#cta)" filter="url(#soft)"' if hi else 'fill="#fff" fill-opacity="0.05" stroke="#263046" stroke-width="0.6"'
        s.append(f'<rect x="16" y="{y}" width="150" height="44" rx="8" {fill}/>')
        s.append(t(28, y + 20, tr(k, lang), 11, "#fff", True) + t(28, y + 34, tr(k + ".d", lang), 6.8, "#fff2e0" if hi else "#8a96ad"))
        if k == "m.ai":
            nw = 18 if lang == "zh" else 22
            s.append(f'<rect x="{166-8-nw}" y="{y+8}" width="{nw}" height="11" rx="5.5" fill="#3ee8ff"/>' + t(166 - 8 - nw / 2, y + 16, tr("new", lang), 6.5, "#05222a", True, "middle"))
    # 展示台
    s.append(f'<ellipse cx="320" cy="250" rx="92" ry="20" fill="#3ee8ff" opacity="0.1"/><ellipse cx="320" cy="250" rx="92" ry="20" fill="none" stroke="#3ee8ff" stroke-opacity="0.45" stroke-width="0.8"/>')
    s.append(tank(320, 196, 30, "player", 104))
    # 右侧：每日挑战卡
    s.append(panel(400, 58, 64, 148, 8))
    s.append(t(432, 76, tr("m.daily", lang) if lang == "zh" else "Daily", 7.5, "#fff", True, "middle"))
    s.append(t(432, 88, "#1023", 7, "#7f8ba3", False, "middle"))
    for i in range(3):
        s.append(icon("star", 416 + i * 16, 104, 0.8, "url(#gold)" if i < 2 else "#3a4256"))
    s.append(t(432, 130, "#128", 12, "#ffe27a", True, "middle"))
    s.append(t(432, 142, "/ 34,920", 6.5, "#8a96ad", False, "middle"))
    s.append(f'<rect x="408" y="172" width="48" height="18" rx="9" fill="#3ee8ff"/>' + t(432, 183.8, tr("go", lang), 7.5, "#05222a", True, "middle"))
    # 底部横幅广告（Google Anchor Banner 样式），只在菜单出现，对局中不出现
    bx, by, bw, bh = 16, H - 44, W - 32, 32
    s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="6" fill="#ffffff" fill-opacity="0.035" stroke="#2c3850" stroke-width="0.6"/>')
    b, _ = ad_badge(bx + 8, by + 11.5, lang)
    s.append(b)
    s.append(f'<rect x="{bx+34}" y="{by+6}" width="20" height="20" rx="4" fill="#fff"/><circle cx="{bx+44}" cy="{by+16}" r="6" fill="{GBLUE}"/><circle cx="{bx+44}" cy="{by+16}" r="2.6" fill="#fff"/>')
    s.append(t(bx + 62, by + 19.5, tr("ad.banner", lang), 7.8, "#c8d2e3"))
    s.append(f'<rect x="{bx+bw-80}" y="{by+8}" width="58" height="16" rx="8" fill="{GBLUE}"/>' + t(bx + bw - 51, by + 18.8, tr("ad.cta", lang), 7, "#fff", True, "middle"))
    s.append(icon("adchoices", bx + bw - 13, by + 10, 0.8, "#6b778f") + icon("close", bx + bw - 13, by + 22, 0.9, "#6b778f"))
    return "".join(s)


# ---------- 字体 ----------
def build_fonts(src, chars):
    full = TTFont(src)
    cmap = full.getBestCmap()
    missing = sorted(c for c in chars if not c.isspace() and ord(c) not in cmap)
    if missing:
        sys.exit("缺字（会显示为乱码）: " + " ".join(f"{c}(U+{ord(c):04X})" for c in missing))
    css = []
    for wght in (500, 800):
        f = instancer.instantiateVariableFont(TTFont(src), {"wght": wght})
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(chars))
        sub.subset(f)
        buf = io.BytesIO()
        f.flavor = "woff2"
        f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        css.append(f"@font-face{{font-family:'{FAM}';font-weight:{wght};src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
    return "<style>" + "".join(css) + "</style>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True, help="Noto Sans SC 可变字体路径")
    args = ap.parse_args()

    # 先把文案表里的全部字符纳入检查，保证游戏用到的中英文都有字形
    for zh, en in STRINGS.values():
        USED.update(zh + en)
    screens = [("01-battle", mock_battle), ("02-clear", mock_clear), ("03-revive", mock_revive), ("04-home", mock_home)]
    bodies = {f"{name}-{lang}": fn(lang) for name, fn in screens for lang in ("zh", "en")}
    style = build_fonts(args.font, USED)
    for name, body in bodies.items():
        doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*3}" height="{H*3}" viewBox="0 0 {W} {H}">'
               f'{style}{DEFS}<rect width="{W}" height="{H}" fill="url(#bg)"/>{body}</svg>')
        with open(os.path.join(HERE, name + ".svg"), "w", encoding="utf-8") as f:
            f.write(doc)
        print("wrote", name + ".svg")
    print(f"字形检查通过：{len(USED)} 个字符")


if __name__ == "__main__":
    main()
