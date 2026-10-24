#!/usr/bin/env python3
"""v3.0 效果图：自己做地图（地图编辑器）、双人合作、新主页。

直接调用游戏的美术生成器（tools/assets/build.py）里的地形、坦克、按钮函数，所以风格和游戏完全一致。
用法：pip install -r tools/assets/requirements.txt
      python3 docs/v3/mockups/gen_v3.py && sh docs/v3/mockups/render.sh
"""
import base64
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools", "assets"))

import build as B  # noqa: E402
from textpath import text, width  # noqa: E402

W, H, C, FX, FY = 480, 360, 24, 12, 30
PX, PY, PW, PH = 336, 26, 132, 320
MUTED = B.MUTED
P2 = ("#4fe3c1", "#1f7a66", "#c9fff1")  # 2P 坦克：青绿色，和三种敌人（红、蓝、绿）都区分开


def img(svg, x, y, w, h, extra=""):
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/svg+xml;base64,{data}" {extra}/>'


TILE = {"B": B.brick_m(), "S": B.steel_m(), "W": B.water_m(), "G": B.grass_m(), "E": B.eagle_m()}


def cell(r, c):
    return FX + c * C, FY + r * C


def field(rows, skip_grass=False):
    """战场：背景 + 地形格子（用游戏里真实的造型）"""
    s = [img(B.backdrop_modern(), 0, 0, W, H)]
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch in TILE and not (skip_grass and ch == "G"):
                x, y = cell(r, c)
                s.append(img(TILE[ch], x, y, C, C))
    return s


def tank(colors, r, c, heading=0, op=1.0, heavy=False):
    x, y = cell(r, c)
    t = B.tank_m(*colors, heavy=heavy)  # 造型朝右，heading 0（朝上）要转 -90 度
    return f'<g transform="rotate({heading - 90} {x + 12} {y + 12})" opacity="{op}">{img(t, x, y, C, C)}</g>'


def panel_btn(x, y, w, h, label, key, primary=False, note=""):
    s = []
    if primary:
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="url(#cta)"/>')
        s.append(text(x + 10, y + h / 2 + 3.4, label, 9, "#ffffff", True))
        c, cw = B.chip(0, 0, key, dark=True)
    else:
        s.append(f'<rect x="{x+0.3}" y="{y+0.3}" width="{w-0.6}" height="{h-0.6}" rx="{h/2}" fill="#ffffff" fill-opacity="0.05" stroke="#2c3850" stroke-width="0.6"/>')
        s.append(text(x + 10, y + h / 2 + 3, label, 8, "#c8d2e3", True))
        if note:
            s.append(text(x + 12 + width(label, 8, True), y + h / 2 + 2.8, note, 5.6, "#5a6680"))
        c, cw = B.chip(0, 0, key)
    s.append(f'<g transform="translate({x + w - 8 - cw:.2f},{y + (h - 10) / 2:.2f})">{c}</g>')
    return "".join(s)


def toggle(x, y, lang):
    return img(B.toggle_costume(lang)[0], x, y, 40, 14)


# ---------- 自己做地图（地图编辑器） ----------
EDIT_MAP = [
    ".............",
    ".BBB.....BBB.",
    ".B.........B.",
    ".B..WWWWW..B.",
    "....W...W....",
    "GG..W.S.W..GG",
    "....W...W....",
    ".B..WW.WW..B.",
    ".B.........B.",
    ".BBB.....BBB.",
    ".............",
    ".....BBB.....",
    ".....BEB.....",
]
EDIT_BAD = EDIT_MAP[:10] + ["WWWWWWWWWWWWW"] + EDIT_MAP[11:]  # 一整排水面：敌人到不了基地

ED = {
    "zh": dict(title="自己做地图", hint="点击或拖动鼠标绘制 · 触屏也可以", tools="工具", mirror="对称绘制",
               ok="地图可以玩", bad="敌人到不了基地", bad2="一整排水面挡住了路", play="试玩", rand="随机起点",
               clear="清空", save="保存", save_note="PC 版", back="返回", locked="锁定格：出生点和基地",
               enemy="敌", copy="从关卡复制", copy_note="K"),
    "en": dict(title="Map Maker", hint="Click or drag to draw · touch works too", tools="TOOLS", mirror="Mirror",
               ok="Map is playable", bad="Enemies can't reach base", bad2="A row of water blocks the way", play="Play test",
               rand="Random start", clear="Clear", save="Save", save_note="PC", back="Back", locked="Locked: spawns and base",
               enemy="E", copy="Copy a stage", copy_note="K"),
}


def editor(lang, bad=False):
    t = ED[lang]
    rows = EDIT_BAD if bad else EDIT_MAP
    s = field(rows)
    # 网格线，方便对准格子
    for i in range(1, 13):
        s.append(f'<path d="M{FX+i*C} {FY}V{FY+13*C}M{FX} {FY+i*C}H{FX+13*C}" stroke="#3ee8ff" stroke-opacity="0.12" stroke-width="0.5"/>')
    # 对称线
    s.append(f'<path d="M{FX+6.5*C} {FY}V{FY+13*C}" stroke="#3ee8ff" stroke-opacity="0.55" stroke-width="0.8" stroke-dasharray="3 3"/>')
    # 锁定格：敌人出生点、玩家出生点
    for c in (0, 6, 12):
        x, y = cell(0, c)
        s.append(f'<rect x="{x+1}" y="{y+1}" width="{C-2}" height="{C-2}" rx="3" fill="#ff4a3a" fill-opacity="0.18" stroke="#ff4a3a" stroke-opacity="0.7" stroke-width="0.8" stroke-dasharray="2 1.5"/>')
        s.append(text(x + 12, y + 15.5, t["enemy"], 8, "#ff8a7a", True, "middle"))
    for c, lab, col in ((4, "1P", "#ffd23a"), (8, "2P", P2[0])):
        x, y = cell(12, c)
        s.append(f'<rect x="{x+1}" y="{y+1}" width="{C-2}" height="{C-2}" rx="3" fill="{col}" fill-opacity="0.15" stroke="{col}" stroke-opacity="0.8" stroke-width="0.8" stroke-dasharray="2 1.5"/>')
        s.append(text(x + 12, y + 15, lab, 7.5, col, True, "middle"))
    # 光标：正在画砖墙（左右对称的位置一起画）
    for c in (2, 10):
        x, y = cell(4, c)
        s.append(img(TILE["B"], x, y, C, C, 'opacity="0.55"'))
        s.append(f'<rect x="{x+0.5}" y="{y+0.5}" width="{C-1}" height="{C-1}" rx="2" fill="none" stroke="#3ee8ff" stroke-width="1.4"/>')
    if bad:  # 出问题的那一排标红
        x, y = cell(10, 0)
        s.append(f'<rect x="{x}" y="{y}" width="{13*C}" height="{C}" fill="#ff2a2a" fill-opacity="0.25" stroke="#ff4a3a" stroke-width="1.2"/>')
    # 顶栏
    s.append(text(12, 21, t["title"], 10, "#ffffff", True))
    s.append(text(330, 20.5, t["hint"], 6.5, MUTED, False, "end"))
    s.append(toggle(428, 9, lang))
    # 右侧面板
    x0 = PX + 8
    s.append(text(x0, 42, t["tools"], 6.8, MUTED, True))
    tools = ["B", "S", "W", "G", None]
    for i, k in enumerate(tools):
        x, y = x0 + i * 24.5, 48
        sel = i == 0
        s.append(f'<rect x="{x-1.5}" y="{y-1.5}" width="23" height="23" rx="4" fill="#ffffff" fill-opacity="{0.12 if sel else 0.03}" stroke="{"#3ee8ff" if sel else "#2c3850"}" stroke-width="{1.2 if sel else 0.6}"/>')
        if k:
            s.append(img(TILE[k], x + 1, y + 1, 18, 18))
        else:  # 橡皮擦
            s.append(f'<path d="M{x+5} {y+5}l10 10M{x+15} {y+5}l-10 10" stroke="#c8d2e3" stroke-width="1.6" stroke-linecap="round"/>')
        c, cw = B.chip(0, 0, str(i + 1))
        s.append(f'<g transform="translate({x + 10 - cw / 2:.2f},{y + 24})">{c}</g>')
    # 对称开关
    y = 92
    c, cw = B.chip(x0, y, "M")
    s.append(c + text(x0 + cw + 5, y + 7.6, t["mirror"], 7.5, "#c8d2e3", True))
    s.append(f'<rect x="{PX+PW-30}" y="{y}" width="20" height="10" rx="5" fill="#3ee8ff"/><circle cx="{PX+PW-15}" cy="{y+5}" r="3.8" fill="#06232b"/>')
    # 检查结果
    y = 110
    col = "#ff5a4a" if bad else "#2ee88a"
    s.append(f'<rect x="{x0}" y="{y}" width="{PW-16}" height="{30 if bad else 22}" rx="6" fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-opacity="0.6" stroke-width="0.7"/>')
    if bad:
        s.append(f'<path d="M{x0+8} {y+7}l6 6M{x0+14} {y+7}l-6 6" stroke="{col}" stroke-width="1.6"/>')
        s.append(text(x0 + 20, y + 12.5, t["bad"], 7, col, True))
        s.append(text(x0 + 20, y + 23, t["bad2"], 5.8, "#e8b4ad"))
    else:
        s.append(f'<path d="M{x0+7} {y+11}l3 3 6-6" fill="none" stroke="{col}" stroke-width="1.6"/>')
        s.append(text(x0 + 20, y + 14.5, t["ok"], 7.5, col, True))
    # 按钮
    y = 150
    bw = PW - 16
    s.append(panel_btn(x0, y, bw, 22, t["play"], "Enter", primary=True))
    s.append(panel_btn(x0, y + 28, bw, 18, t["rand"], "R"))
    s.append(panel_btn(x0, y + 50, bw, 18, t["copy"], t["copy_note"]))
    s.append(panel_btn(x0, y + 72, bw, 18, t["clear"], "C"))
    s.append(panel_btn(x0, y + 94, bw, 18, t["save"], "S", note=t["save_note"]))
    s.append(panel_btn(x0, y + 116, bw, 18, t["back"], "Esc"))
    # 图例
    y = 300
    s.append(f'<rect x="{x0}" y="{y}" width="9" height="9" rx="2" fill="#ff4a3a" fill-opacity="0.18" stroke="#ff4a3a" stroke-opacity="0.7" stroke-width="0.7" stroke-dasharray="2 1.5"/>')
    s.append(text(x0 + 13, y + 7.4, t["locked"], 5.8, MUTED))
    return B.svg(W, H, "".join(s), B.defs_ui(), res=3)


# ---------- 双人合作 ----------
STAGE1 = [
    ".............", ".B.B.B.B.B.B.", ".B.B.B.B.B.B.", ".B.B.BSB.B.B.", ".B.B.....B.B.", "GG...B.B...GG", "SS.BB...BB.SS",
    "WW...B.B...WW", ".B.B.BBB.B.B.", ".B.B.B.B.B.B.", ".B.B.....B.B.", ".B.B.BBB.B.B.", ".....BEB.....",
]
CO = {
    "zh": dict(stage="第 1 关 · 钢铁峡谷", coop="双人", enemies="敌军", score="得分", best="最高分", lives="生命",
               h1="WASD 移动 · J 开火", h2="方向键 · Enter 开火", style="切换画风", lang="中 / EN"),
    "en": dict(stage="Stage 1 · Steel Canyon", coop="CO-OP", enemies="Enemies", score="SCORE", best="BEST", lives="LIVES",
               h1="WASD move · J fire", h2="Arrows · Enter fire", style="Art style", lang="中 / EN"),
}


def life_icons(x, y, colors, n, total=3):
    s = []
    defs, body = B.tank_body(*colors)
    for i in range(total):
        icon = B.svg(12, 12, f'<g opacity="{1 if i < n else 0.22}" transform="scale(0.5)">{body}</g>', defs)
        s.append(img(icon, x + i * 14, y - 6, 12, 12))
    return "".join(s)


def coop(lang):
    t = CO[lang]
    rows = [list(r) for r in STAGE1]
    for r, c in ((8, 3), (9, 3), (10, 9), (11, 9)):  # 打掉几块砖，看起来像正在对战
        rows[r][c] = "."
    rows = ["".join(r) for r in rows]
    s = field(rows, skip_grass=True)
    s.append(tank(B.TANKS["player"], 10, 4, 0))
    s.append(tank(P2, 9, 8, 0))
    s.append(tank(B.TANKS["basic"], 2, 6, 180))
    s.append(tank(B.TANKS["fast"], 4, 10, -90))
    s.append(tank(B.TANKS["heavy"], 1, 0, 180, heavy=True))
    # 子弹
    bx, by = cell(7, 8)
    s.append(img(B.bullet_m("#ffe27a", "#ffb000"), bx + 9, by + 9, 6, 6))
    bx, by = cell(5, 4)
    s.append(img(B.bullet_m("#ffe27a", "#ffb000"), bx + 9, by + 9, 6, 6))
    for r, line in enumerate(rows):  # 草丛盖在坦克上面
        for c, ch in enumerate(line):
            if ch == "G":
                x, y = cell(r, c)
                s.append(img(TILE["G"], x, y, C, C))
    # 顶栏
    s.append(text(12, 21, t["stage"], 10, "#ffffff", True))
    sw = width(t["stage"], 10, True)
    cw = width(t["coop"], 6, True) + 8
    s.append(f'<rect x="{12+sw+6:.2f}" y="11" width="{cw:.2f}" height="11" rx="5.5" fill="{P2[0]}"/>')
    s.append(text(12 + sw + 6 + cw / 2, 18.6, t["coop"], 6, "#06232b", True, "middle"))
    s.append(text(204, 20, t["enemies"], 7.5, MUTED, False, "end"))
    for i in range(20):
        s.append(f'<rect x="{209+i*5.8:.1f}" y="13" width="4" height="8" rx="1" fill="{"#3a4256" if i < 6 else "#ff5a4a"}"/>')
    s.append(toggle(428, 9, lang))
    # 右侧面板
    x0 = PX + 8
    s.append(text(x0, 42, t["score"], 6.8, MUTED, True))
    s.append(text(x0, 62, "3,200", 18, "#ffffff", True))
    s.append(text(x0, 78, t["best"], 6.8, MUTED, True))
    s.append(text(PX + PW - 8, 78, "3,200", 8, "#ffe27a", True, "end"))
    s.append(text(x0, 98, t["lives"], 6.8, MUTED, True))
    s.append(text(x0, 113, "1P", 7.5, "#ffd23a", True))
    s.append(life_icons(x0 + 16, 110, B.TANKS["player"], 3))
    s.append(text(x0, 129, "2P", 7.5, P2[0], True))
    s.append(life_icons(x0 + 16, 126, P2, 2))
    y = 146
    for lab, col, hint in (("1P", "#ffd23a", t["h1"]), ("2P", P2[0], t["h2"])):
        s.append(f'<rect x="{x0}" y="{y}" width="14" height="11" rx="2.5" fill="{col}" fill-opacity="0.2"/>')
        s.append(text(x0 + 7, y + 8.2, lab, 6.2, col, True, "middle"))
        s.append(text(x0 + 19, y + 8.2, hint, 6.4, MUTED))
        y += 16
    for k, lab in (("T", t["style"]), ("L", t["lang"])):
        c, cw = B.chip(x0, y, k)
        s.append(c + text(x0 + cw + 5, y + 7.8, lab, 6.6, MUTED))
        y += 16
    s.append(img(B.native_card(lang)[0], 342, 250, 120, 86))
    return B.svg(W, H, "".join(s), B.defs_ui(), res=3)


# ---------- 新主页 ----------
HOME = {
    "zh": dict(start="开始战役", start_d="8 个关卡，消灭敌军，守住基地", coop="双人合作", coop_d="同一台电脑，两人一起守基地",
               maker="自己做地图", maker_d="画一张地图，马上试玩", daily="每日挑战", daily_d="每天一张新地图",
               new="新", soon="即将推出", demo="路演演示模式", pick="选择关卡"),
    "en": dict(start="Start", start_d="8 stages · Destroy tanks, guard the base", coop="Co-op", coop_d="Two players, one keyboard",
               maker="Map Maker", maker_d="Draw a map, play it now", daily="Daily Challenge", daily_d="A new map every day",
               new="NEW", soon="SOON", demo="Demo mode", pick="Pick a stage"),
}


def home(lang):
    t = HOME[lang]
    s = [f'<rect width="{W}" height="{H}" fill="url(#bgH)"/>',
         '<circle cx="330" cy="170" r="140" fill="#3ee8ff" fill-opacity="0.05"/><circle cx="330" cy="170" r="90" fill="#ffd23a" fill-opacity="0.05"/>']
    title = B.tr("title", lang)
    s.append(text(16, 46, title, 22, "#ffffff", True))
    s.append(text(16 + width(title, 22, True) + 6, 46, "2026", 22, "url(#gold)", True))
    s.append(text(16, 60, B.tr("subtitle", lang), 7.5, "#7f8ba3", True))
    s.append('<rect x="16" y="84" width="170" height="50" rx="10" fill="url(#cta)"/>')
    s.append(text(28, 106, t["start"], 13, "#ffffff", True))
    s.append(text(28, 122, t["start_d"], 6.4, "#fff2e0"))
    c, cw = B.chip(0, 0, "Enter", dark=True)
    s.append(f'<g transform="translate({186-10-cw:.2f},96)">{c}</g>')
    for i, (k, key, live) in enumerate((("coop", "C", True), ("maker", "E", True), ("daily", "", False))):
        y = 144 + i * 44
        stroke, op = ("#3ee8ff", 0.7) if live else ("#263046", 1)
        s.append(f'<rect x="16.4" y="{y+0.4}" width="169.2" height="37.2" rx="8" fill="{"#3ee8ff" if live else "#ffffff"}" fill-opacity="{0.08 if live else 0.035}" stroke="{stroke}" stroke-opacity="{op}" stroke-width="0.8"/>')
        s.append(text(28, y + 17, t[k], 10.5, "#ffffff" if live else "#7f8ba3", True))
        s.append(text(28, y + 29, t[k + "_d"], 6.2, "#9fdcea" if live else "#5a6680"))
        if live:
            nw = width(t["new"], 5.8, True) + 10
            c, cw = B.chip(0, 0, key, dark=True)
            s.append(f'<rect x="{186-10-cw-6-nw:.2f}" y="{y+8}" width="{nw:.2f}" height="11" rx="5.5" fill="#3ee8ff"/>')
            s.append(text(186 - 10 - cw - 6 - nw / 2, y + 15.6, t["new"], 5.8, "#06232b", True, "middle"))
            s.append(f'<g transform="translate({186-10-cw:.2f},{y+8.5})">{c}</g>')
        else:
            sw = width(t["soon"], 5.8, True) + 10
            s.append(f'<rect x="{186-10-sw:.2f}" y="{y+8}" width="{sw:.2f}" height="11" rx="5.5" fill="#2c3850"/>')
            s.append(text(186 - 10 - sw / 2, y + 15.6, t["soon"], 5.8, MUTED, True, "middle"))
    c, cw = B.chip(16, 290, "P")
    s.append(c + text(16 + cw + 5, 297.4, t["demo"], 7, "#7f8ba3"))
    x = 16 + cw + 5 + width(t["demo"], 7) + 14
    c, cw = B.chip(x, 290, "1-8")
    s.append(c + text(x + cw + 5, 297.4, t["pick"], 7, "#7f8ba3"))
    # 展示台：两辆坦克（1P 黄、2P 青绿）
    s.append('<ellipse cx="330" cy="236" rx="92" ry="20" fill="#3ee8ff" fill-opacity="0.1" stroke="#3ee8ff" stroke-opacity="0.45" stroke-width="0.8"/>')
    for colors, tx, rot in ((B.TANKS["player"], 300, 20), (P2, 368, -20)):
        defs, body = B.tank_body(*colors)
        icon = B.svg(24, 24, body, defs)
        s.append(f'<g transform="translate({tx} 196) rotate({rot}) translate(-42 -42)">{img(icon, 0, 0, 84, 84)}</g>')
    toggle_svg = img(B.toggle_costume(lang)[0], 428, 9, 40, 14)
    s.append(toggle_svg)
    s.append(img(B.banner(lang)[0], 16, 316, 448, 32))
    return B.svg(W, H, "".join(s), B.defs_ui(), res=3)


def main():
    out = {}
    for lang in ("zh", "en"):
        out[f"v3-home-{lang}.svg"] = home(lang)
        out[f"v3-editor-{lang}.svg"] = editor(lang)
        out[f"v3-editor-bad-{lang}.svg"] = editor(lang, bad=True)
        out[f"v3-coop-{lang}.svg"] = coop(lang)
    for name, content in out.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
            f.write(content)
    print("wrote", ", ".join(out))


if __name__ == "__main__":
    main()
