#!/usr/bin/env python3
"""生成 TankBattle 的美术资源（SVG 造型）。

用法：pip install -r tools/assets/requirements.txt && python3 tools/assets/build.py

约束：spx 用 LunaSVG 光栅化 SVG，不支持 filter（阴影、模糊），所以阴影都画成半透明图形；
文字一律通过 textpath 转成路径，运行时不依赖字体。
布局：舞台 480x360，战场 13x13 格、每格 24px，左上角在 SVG 坐标 (12, 30)，右侧面板 x=336 起。
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(ROOT, "TankBattle", "assets")

W, H = 480, 360
C = 24
FX, FY = 12, 30
PX, PY, PW, PH = 336, 26, 132, 320


def svg(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
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


def tank_m(main, dark, light, heavy=False):
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
    return svg(C, C, f'<g transform="rotate(90 12 12)">{"".join(s)}</g>', defs)


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


def main():
    out = [
        write("field.svg", backdrop_classic()),
        write("field_m.svg", backdrop_modern()),
        write("sprites/Brick/brick_m.svg", brick_m()),
        write("sprites/Brick/cracked_m.svg", brick_m(True)),
        write("sprites/Steel/steel_m.svg", steel_m()),
        write("sprites/Base/eagle_m.svg", eagle_m()),
        write("sprites/Base/broken_m.svg", broken_m()),
        write("sprites/Player/player_m.svg", tank_m(*TANKS["player"])),
        write("sprites/Enemy/basic_m.svg", tank_m(*TANKS["basic"])),
        write("sprites/Enemy/fast_m.svg", tank_m(*TANKS["fast"])),
        write("sprites/Enemy/heavy_m.svg", tank_m(*TANKS["heavy"], heavy=True)),
        write("sprites/PBullet/bullet_m.svg", bullet_m("#ffe27a", "#ffb000")),
        write("sprites/EBullet/bullet_m.svg", bullet_m("#ff8a7a", "#ff2a2a")),
    ]
    for i in range(3):
        out.append(write(f"sprites/Boom/b{i+1}_m.svg", boom_m(i)))
    print(f"generated {len(out)} files")


if __name__ == "__main__":
    main()
