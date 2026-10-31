#!/usr/bin/env python3
"""v6.0 效果图：打精英升级、三选一芯片、车库（局外成长）、排行榜、每日挑战主页、分享战报。

和 v3 一样直接调用游戏的美术生成器（tools/assets/build.py）里的地形、坦克、按钮函数，风格和游戏一致。
这些只是规划用的示意图，游戏里还没有这些画面。
用法：tools/dev/venv.sh
      .venv/bin/python docs/v6/mockups/gen_v6.py && sh docs/v6/mockups/render.sh
"""
import base64
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools", "assets"))

import build as B  # noqa: E402
from textpath import text, width  # noqa: E402

W, H, C, FX, FY = 480, 360, 24, 12, 30
PX, PW = 336, 132
X0 = PX + 8
MUTED = B.MUTED
P1 = B.TANKS["player"]
ELITE = ("#c46bff", "#5d2391", "#ecd2ff")  # 精英坦克：紫色，和玩家（黄、青绿）、三种敌人（红、蓝、绿）都区分开
PURPLE = ELITE[0]
CYAN = "#3ee8ff"
GOLD = "#ffe27a"
GREEN = "#2ee88a"


def img(svg, x, y, w, h, extra=""):
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/svg+xml;base64,{data}" {extra}/>'


TILE = {"B": B.brick_m(), "S": B.steel_m(), "W": B.water_m(), "G": B.grass_m(), "E": B.eagle_m()}


def cell(r, c):
    return FX + c * C, FY + r * C


def field(rows, grass=True):
    s = [img(B.backdrop_modern(), 0, 0, W, H)]
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch in TILE and (grass or ch != "G"):
                x, y = cell(r, c)
                s.append(img(TILE[ch], x, y, C, C))
    return s


def grass_over(rows):
    s = []
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch == "G":
                x, y = cell(r, c)
                s.append(img(TILE["G"], x, y, C, C))
    return s


def tank(colors, r, c, heading=0, op=1.0, heavy=False, dx=0, dy=0):
    x, y = cell(r, c)
    x, y = x + dx, y + dy
    t = B.tank_m(*colors, heavy=heavy)
    return f'<g transform="rotate({heading - 90} {x + 12} {y + 12})" opacity="{op}">{img(t, x, y, C, C)}</g>'


def tank_icon(colors, x, y, size, rot=0, heavy=False):
    defs, body = B.tank_body(*colors, heavy=heavy)
    icon = B.svg(24, 24, body, defs)
    return f'<g transform="translate({x + size / 2} {y + size / 2}) rotate({rot}) translate({-size / 2} {-size / 2})">{img(icon, 0, 0, size, size)}</g>'


def star(cx, cy, r, fill, op=1.0):
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(f"{cx + math.cos(a) * rr:.2f},{cy + math.sin(a) * rr:.2f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}" fill-opacity="{op}"/>'


def hexagon(cx, cy, r, fill, stroke, op=1.0, sw=1.0):
    pts = " ".join(f"{cx + math.cos(math.radians(30 + i * 60)) * r:.2f},{cy + math.sin(math.radians(30 + i * 60)) * r:.2f}" for i in range(6))
    return f'<polygon points="{pts}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"/>'


def pill(x, y, label, size, bg, fg, pad=8, h=11):
    w = width(label, size, True) + pad
    return (f'<rect x="{x:.2f}" y="{y}" width="{w:.2f}" height="{h}" rx="{h / 2}" fill="{bg}"/>'
            + text(x + w / 2, y + h / 2 + size * 0.36, label, size, fg, True, "middle")), w


def toggle(x, y, lang):
    return img(B.toggle_costume(lang)[0], x, y, 40, 14)


def chip_at(x, y, k, dark=False):
    c, cw = B.chip(0, 0, k, dark)
    return f'<g transform="translate({x:.2f},{y:.2f})">{c}</g>', cw


# ---------- 芯片（升级）图标：24x24 的线条图，画在 (x, y) 处，缩放 k ----------
def _icon_body(key, col):
    st = f'stroke="{col}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    if key == "rapid":    # 子弹加速：子弹 + 速度线
        return f'<circle cx="16" cy="12" r="4" fill="{col}"/><path d="M3 8h7M2 12h8M3 16h7" {st}/>'
    if key == "double":   # 双发
        return f'<circle cx="8" cy="15" r="3.4" fill="{col}"/><circle cx="16" cy="9" r="3.4" fill="{col}"/><path d="M8 22v-3M16 16v-3" {st}/>'
    if key == "pierce":   # 穿甲弹：箭头穿过钢块
        return f'<rect x="8" y="7" width="8" height="10" rx="1.2" fill="{col}" fill-opacity="0.3" stroke="{col}" stroke-width="1.4"/><path d="M2 12h20M18 8l4 4-4 4" {st}/>'
    if key == "bounce":   # 跳弹
        return f'<path d="M3 20l8-14 8 14" {st}/><path d="M2 21h20" stroke="{col}" stroke-width="1.4" stroke-opacity="0.5"/><circle cx="19" cy="20" r="2.4" fill="{col}"/>'
    if key == "shield":   # 护盾：挡一发
        return f'<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z" fill="{col}" fill-opacity="0.25" stroke="{col}" stroke-width="2" stroke-linejoin="round"/><path d="M9 12l2.2 2.2L15.5 10" {st}/>'
    if key == "engine":   # 加速
        return f'<path d="M5 5l7 7-7 7M12 5l7 7-7 7" {st}/>'
    if key == "float":    # 浮桥：能过水
        return f'<path d="M3 15c2-2 4-2 6 0s4 2 6 0 4-2 6 0M3 20c2-2 4-2 6 0s4 2 6 0 4-2 6 0" {st}/><rect x="7" y="4" width="10" height="7" rx="2" fill="{col}"/>'
    if key == "fortify":  # 铲子：基地钢墙
        return f'<path d="M12 6l2 2.6 3.8-1.2-2 3.8 2.6 1.3-4.5 1.2L12 17l-1.9-3.3-4.5-1.2 2.6-1.3-2-3.8 3.8 1.2z" fill="{col}"/><rect x="2.5" y="2.5" width="19" height="19" rx="2" fill="none" stroke="{col}" stroke-width="1.6" stroke-dasharray="3 1.6"/>'
    if key == "bomb":     # 炸弹：清掉场上敌人
        return f'<circle cx="11" cy="14" r="7" fill="{col}"/><path d="M15 8l3-3M19 3l1 1M21 6h1" {st}/>'
    if key == "freeze":   # 冻结：敌人停 5 秒
        return f'<path d="M12 2v20M3.3 7l17.4 10M3.3 17L20.7 7M9 4l3 3 3-3M9 20l3-3 3 3" {st}/>'
    if key == "stealth":  # 草丛隐身
        return f'<path d="M2 13s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6z" {st}/><circle cx="12" cy="13" r="2.6" fill="{col}"/><path d="M4 22l16-18" {st}/>'
    if key == "magnet":   # 磁铁：自动吸芯片
        return f'<path d="M6 4v8a6 6 0 0 0 12 0V4" stroke="{col}" stroke-width="3.4" fill="none"/><path d="M4.4 4h3.2M16.4 4h3.2" stroke="#ffffff" stroke-width="3.4"/>'
    if key == "lock":
        return f'<rect x="6" y="11" width="12" height="9" rx="2" fill="{col}"/><path d="M8.5 11V8a3.5 3.5 0 0 1 7 0v3" {st}/>'
    raise KeyError(key)


def icon(key, x, y, size, col):
    return f'<g transform="translate({x},{y}) scale({size / 24})">{_icon_body(key, col)}</g>'


RARITY = {"c": "#8fb3ff", "r": PURPLE, "l": "#ffb020"}  # 普通、稀有、传奇
PERKS = {
    #           稀有度, 颜色,      中文名,     中文说明,                         英文名,          英文说明
    "rapid":   ("c", "#ffd54a", "疾速弹", "子弹速度 +40%", "Rapid Shells", "Bullet speed +40%"),
    "double":  ("r", "#ffd54a", "双联炮", "同时最多 2 发子弹", "Twin Cannon", "Up to 2 bullets at once"),
    "pierce":  ("l", "#ff8a3a", "穿甲弹", "能打穿钢墙", "AP Rounds", "Shots break steel"),
    "bounce":  ("r", "#ffd54a", "跳弹", "打到墙反弹一次", "Ricochet", "Bounces off walls once"),
    "shield":  ("c", "#5ad1ff", "能量护盾", "挡住 1 发子弹，30 秒恢复", "Energy Shield", "Blocks 1 hit, recharges in 30s"),
    "engine":  ("c", GREEN, "涡轮引擎", "移动速度 +25%", "Turbo Engine", "Move speed +25%"),
    "float":   ("r", "#5ad1ff", "浮桥履带", "可以开过水面", "Pontoon Treads", "Drive over water"),
    "fortify": ("c", "#c8d2e3", "钢铁堡垒", "基地外围变钢墙 15 秒", "Fortify", "Steel around base for 15s"),
    "bomb":    ("r", "#ff5a4a", "空袭", "立刻炸掉场上所有敌人", "Air Strike", "Destroy all enemies now"),
    "freeze":  ("r", "#9fe8ff", "冰冻", "敌人原地停 5 秒", "Freeze", "Enemies stop for 5s"),
    "stealth": ("c", GREEN, "迷彩", "在草丛里敌人看不见你", "Camouflage", "Invisible in grass"),
    "magnet":  ("c", "#ff7ab8", "磁吸", "芯片自动飞向你", "Magnet", "Chips fly to you"),
}


def perk_name(k, lang):
    return PERKS[k][2] if lang == "zh" else PERKS[k][4]


def perk_desc(k, lang):
    return PERKS[k][3] if lang == "zh" else PERKS[k][5]


def perk_badge(k, x, y, s=20):
    col = PERKS[k][1]
    rc = RARITY[PERKS[k][0]]
    return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * 0.22}" fill="{rc}" fill-opacity="0.16" stroke="{rc}" stroke-opacity="0.8" stroke-width="0.7"/>'
            + icon(k, x + s * 0.15, y + s * 0.15, s * 0.7, col))


def chip_drop(cx, cy, r=8):
    """精英坦克掉落的升级芯片：紫色六边形 + 星"""
    return (f'<circle cx="{cx}" cy="{cy}" r="{r * 2}" fill="url(#chipGlow)"/>'
            + hexagon(cx, cy, r, "#2a0f45", PURPLE, 1, 1.3)
            + star(cx, cy + 0.4, r * 0.6, "#f3dcff"))


def defs():
    return (B.defs_ui()
            + B.rad("chipGlow", [(0, PURPLE, 0.75), (0.5, PURPLE, 0.25), (1, PURPLE, 0)])
            + B.rad("eliteGlow", [(0, PURPLE, 0), (0.55, PURPLE, 0), (0.75, PURPLE, 0.55), (1, PURPLE, 0)])
            + B.lin("xp", PURPLE, "#ff7ab8", vertical=False)
            + B.lin("season", "#ffb020", "#ff5a1a", vertical=False)
            + B.lin("card", "#1b2335", "#10151f"))


def lv_stars(x, y, lv, total=4, r=3.4, gap=8.5):
    return "".join(star(x + i * gap, y, r, GOLD if i < lv else "#3a4256") for i in range(total))


# ---------- 文案 ----------
T = {
    "zh": dict(
        stage="第 3 关 · 丛林伏击", elite_toast="精英来袭！击毁它掉落升级芯片", enemies="敌军", score="得分", level="坦克等级",
        next="再打 1 辆精英升到 Lv4", chips="已装芯片", elite_left="本关精英", elite_n="剩 2 辆", pickup="拾取芯片",
        style="切换画风", lang="中 / EN",
        pick_title="升级！选一块芯片", pick_sub="Lv2 → Lv3 · 本局有效，被击毁掉 1 级", pick_key="按 1 / 2 / 3 选择",
        rarity_c="普通", rarity_r="稀有", rarity_l="传奇", reroll="看视频再刷新一次", reroll_pc="每局免费刷新 1 次（PC 版）", combo="和「跳弹」组成连携：弹幕",
        g_title="车库", g_lv="指挥官 Lv12", g_xp="再 340 经验解锁「磁吸」", g_pool="芯片图鉴 · 已解锁 9 / 24",
        g_pool_d="解锁的芯片会出现在三选一里；只增加选择，不加数值", g_skin="涂装（金币兑换，不卖数值）", g_coins="金币",
        g_tasks="今日任务", g_t1="用穿甲弹击毁 5 辆重型", g_t2="通关每日挑战", g_t3="和好友打一局双人", g_new="新",
        s_free="赛季免费奖励", s_name="S1 · 雨林行动", s_left="还剩 23 天",
        r_title="排行榜", tabs=("好友", "全球", "每日挑战", "赛季段位"), scope="Steam 好友",
        scope_note="好友榜由各平台提供：Steam / Game Center / 微信好友各自独立",
        r_cols=("名次", "玩家", "芯片组合", "得分"), you="你", r_foot="全球榜和每日挑战榜跨平台，由我们自己的服务器提供",
        g_scope="海外榜", g_scope_note="国内（微信小游戏）是单独的一个榜，数据存在境内", g_season="本周 · 周一 0 点重置",
        h_start="开始战役", h_start_d="8 个关卡 · 打精英升级", h_daily="每日挑战", h_daily_d="全球同一张地图、同一组芯片",
        h_daily_t="还剩 08:12:45", h_daily_rank="昨天：全球前 12%", h_coop="双人合作", h_maker="自己做地图",
        h_garage="车库", h_rank="排行榜", h_season="赛季", h_hot="热门",
        sh_title="每日挑战 #301", sh_time="用时 3:42", sh_score="得分 12,800", sh_rank="全球第 1,204 名 · 前 8%",
        sh_friend="连续打卡 7 天", sh_build="我的芯片", sh_cta="长按识别，一起守老鹰", sh_btn="分享到微信", sh_btn2="保存图片",
        sh_chal="挑战我的分数", sh_help="点开链接，你的坦克会来给我助战一关",
    ),
    "en": dict(
        stage="Stage 3 · Jungle Ambush", elite_toast="Elite incoming! Destroy it for an upgrade chip", enemies="Enemies", score="SCORE", level="TANK LEVEL",
        next="1 more elite to reach Lv4", chips="CHIPS", elite_left="ELITES", elite_n="2 left", pickup="Grab the chip",
        style="Art style", lang="中 / EN",
        pick_title="Level up! Pick a chip", pick_sub="Lv2 → Lv3 · lasts this run, lose 1 level when destroyed", pick_key="Press 1 / 2 / 3",
        rarity_c="COMMON", rarity_r="RARE", rarity_l="LEGENDARY", reroll="Watch a video to reroll", reroll_pc="1 free reroll per run (PC)", combo="Combo with Ricochet: Barrage",
        g_title="Garage", g_lv="Commander Lv12", g_xp="340 XP to unlock Magnet", g_pool="Chip codex · 9 / 24 unlocked",
        g_pool_d="Unlocked chips join the pick-3 pool: more choices, not more power", g_skin="Skins (coins only, cosmetic)", g_coins="Coins",
        g_tasks="DAILY TASKS", g_t1="Destroy 5 heavies with AP Rounds", g_t2="Clear the Daily Challenge", g_t3="Play co-op with a friend", g_new="NEW",
        s_free="Free season rewards", s_name="S1 · Operation Rainforest", s_left="23 days left",
        r_title="Leaderboards", tabs=("Friends", "Global", "Daily", "Season"), scope="Steam friends",
        scope_note="Friend boards come from each platform: Steam / Game Center / WeChat",
        r_cols=("#", "Player", "Build", "Score"), you="You", r_foot="Global and Daily boards are cross-platform, on our own server",
        g_scope="Overseas", g_scope_note="China (WeChat) is a separate board", g_season="This week · resets Monday",
        h_start="Start", h_start_d="8 stages · Beat elites to level up", h_daily="Daily Challenge", h_daily_d="Same map, same chips, whole world",
        h_daily_t="08:12:45 left", h_daily_rank="Yesterday: top 12%", h_coop="Co-op", h_maker="Map Maker",
        h_garage="Garage", h_rank="Ranks", h_season="Season", h_hot="HOT",
        sh_title="Daily Challenge #301", sh_time="Time 3:42", sh_score="Score 12,800", sh_rank="#1,204 worldwide · top 8%",
        sh_friend="7-day streak", sh_build="My build", sh_cta="Scan to guard the eagle with me", sh_btn="Share", sh_btn2="Save image",
        sh_chal="Beat my score", sh_help="Open the link and your tank joins my next stage",
    ),
}

JUNGLE = [
    "GG...........", "GGB.B.G.B.BGG", "..B.B.GGB.B..", "GGB...G...BGG", "....BBGBB....", "GG.........GG",
    "BB.GG.S.GG.BB", ".....GGG.....", "GG.B.B.B.B.GG", "...B.....B...", ".B.B.BBB.B.B.", ".B...B.B...B.", ".....BEB.....",
]


def hud_top(t, lang, title):
    s = [text(12, 21, title, 10, "#ffffff", True)]
    s.append(text(204, 20, t["enemies"], 7.5, MUTED, False, "end"))
    for i in range(20):
        col = "#3a4256" if i < 9 else (PURPLE if i in (10, 17) else "#ff5a4a")
        s.append(f'<rect x="{209 + i * 5.8:.1f}" y="13" width="4" height="8" rx="1" fill="{col}"/>')
    s.append(toggle(428, 9, lang))
    return s


# ---------- 1. 战斗：打精英掉芯片 ----------
def battle(lang):
    t = T[lang]
    s = field(JUNGLE, grass=False)
    # 玩家（Lv3）在中路，刚击毁一辆精英；芯片掉在爆炸处
    s.append(tank(P1, 9, 6, 0))
    px, py = cell(9, 6)
    s.append(f'<circle cx="{px + 12}" cy="{py + 12}" r="15" fill="none" stroke="#5ad1ff" stroke-opacity="0.7" stroke-width="1.1" stroke-dasharray="3 2"/>')  # 能量护盾
    b, bw = pill(px + 12 - 12, py - 9, "Lv3", 5.6, GOLD, "#2a1d00", pad=6, h=9)
    s.append(b)
    ex, ey = cell(5, 6)
    s.append(img(B.boom_m(2), ex - 8, ey - 8, 40, 40))
    s.append(chip_drop(ex + 12, ey + 12))
    # 双联炮：两发子弹
    for r, dy in ((7, 6), (8, 2)):
        bx, by = cell(r, 6)
        s.append(img(B.bullet_m("#ffe27a", "#ffb000"), bx + 9, by + dy, 6, 6))
    # 另一辆精英从上方冲下来，带紫色光圈
    s.append(f'<circle cx="{cell(1, 9)[0] + 12}" cy="{cell(1, 9)[1] + 12}" r="18" fill="url(#eliteGlow)"/>')
    s.append(tank(ELITE, 1, 9, 180, heavy=True))
    s.append(tank(B.TANKS["fast"], 3, 2, 90))
    s.append(tank(B.TANKS["basic"], 4, 11, 180))
    s += grass_over(JUNGLE)
    # 提示气泡
    tw = width(t["elite_toast"], 7.5, True) + 22
    s.append(f'<rect x="{168 - tw / 2:.1f}" y="40" width="{tw:.1f}" height="17" rx="8.5" fill="#1a0b2b" fill-opacity="0.9" stroke="{PURPLE}" stroke-width="0.8"/>')
    s.append(star(168 - tw / 2 + 10, 48.5, 4, PURPLE))
    s.append(text(168 + 6, 51.4, t["elite_toast"], 7.5, "#f3dcff", True, "middle"))
    # 指向芯片的提示
    s.append(text(ex + 34, ey + 15, t["pickup"], 6.5, "#f3dcff", True))
    s.append(f'<path d="M{ex + 32} {ey + 12}h-6" stroke="#f3dcff" stroke-width="0.9"/>')
    s += hud_top(t, lang, t["stage"])
    # 右侧面板
    s.append(text(X0, 42, t["score"], 6.8, MUTED, True))
    s.append(text(X0, 62, "4,650", 18, "#ffffff", True))
    s.append(text(X0, 82, t["level"], 6.8, MUTED, True))
    s.append(text(X0, 101, "Lv3", 15, GOLD, True))
    s.append(lv_stars(X0 + 40, 96.5, 3))
    s.append(f'<rect x="{X0}" y="108" width="{PW - 16}" height="5" rx="2.5" fill="#ffffff" fill-opacity="0.1"/>')
    s.append(f'<rect x="{X0}" y="108" width="{(PW - 16) * 0.66:.1f}" height="5" rx="2.5" fill="url(#xp)"/>')
    s.append(text(X0, 122, t["next"], 5.8, "#d9b8ff"))
    s.append(text(X0, 142, t["chips"], 6.8, MUTED, True))
    for i, k in enumerate(("double", "shield", "engine")):
        s.append(perk_badge(k, X0 + i * 26, 148, 22))
    s.append(f'<rect x="{X0 + 78}" y="148" width="22" height="22" rx="4.8" fill="none" stroke="#3a4256" stroke-width="0.7" stroke-dasharray="2 2"/>')
    s.append(text(X0 + 89, 162, "+", 10, "#3a4256", True, "middle"))
    s.append(text(X0, 190, t["elite_left"], 6.8, MUTED, True))
    s.append(tank_icon(ELITE, X0 - 2, 194, 18, heavy=True))
    s.append(text(X0 + 20, 206, t["elite_n"], 8, "#d9b8ff", True))
    y = 222
    for k, lab in (("T", t["style"]), ("L", t["lang"])):
        c, cw = B.chip(X0, y, k)
        s.append(c + text(X0 + cw + 5, y + 7.8, lab, 6.6, MUTED))
        y += 16
    s.append(img(B.native_card(lang)[0], 342, 250, 120, 86))
    return B.svg(W, H, "".join(s), defs(), res=3)


# ---------- 2. 三选一 ----------
def pick(lang):
    t = T[lang]
    s = field(JUNGLE)
    s += hud_top(t, lang, t["stage"])
    s.append(f'<rect width="{W}" height="{H}" fill="#07040d" fill-opacity="0.72"/>')
    s.append(text(240, 62, t["pick_title"], 17, "#ffffff", True, "middle"))
    s.append(text(240, 78, t["pick_sub"], 7.5, "#c8b4e8", False, "middle"))
    cards = ("pierce", "freeze", "rapid")
    cw, ch, gap = 120, 168, 14
    x = 240 - (3 * cw + 2 * gap) / 2
    for i, k in enumerate(cards):
        rar = PERKS[k][0]
        rc = RARITY[rar]
        cx = x + i * (cw + gap)
        sel = i == 0
        y0 = 94 - (6 if sel else 0)
        if sel:
            s.append(f'<rect x="{cx - 4}" y="{y0 - 4}" width="{cw + 8}" height="{ch + 8}" rx="14" fill="{rc}" fill-opacity="0.18"/>')
        s.append(f'<rect x="{cx}" y="{y0}" width="{cw}" height="{ch}" rx="11" fill="url(#card)" stroke="{rc}" stroke-width="{1.6 if sel else 0.9}"/>')
        b, bw = pill(cx + 10, y0 + 10, t["rarity_" + rar], 5.6, rc, "#120a1f", pad=8, h=10)
        s.append(b)
        k2, kw = chip_at(cx + cw - 10 - width(str(i + 1), 6, True) - 6, y0 + 10, str(i + 1))
        s.append(k2)
        s.append(f'<circle cx="{cx + cw / 2}" cy="{y0 + 62}" r="27" fill="{rc}" fill-opacity="0.12"/>')
        s.append(icon(k, cx + cw / 2 - 19, y0 + 43, 38, PERKS[k][1]))
        s.append(text(cx + cw / 2, y0 + 112, perk_name(k, lang), 12, "#ffffff", True, "middle"))
        s.append(text(cx + cw / 2, y0 + 127, perk_desc(k, lang), 6.6, "#c8d2e3", False, "middle"))
        if k == "pierce":
            s.append(f'<rect x="{cx + 10}" y="{y0 + 138}" width="{cw - 20}" height="18" rx="5" fill="#ff8a3a" fill-opacity="0.14"/>')
            s.append(text(cx + cw / 2, y0 + 150, t["combo"], 5.6, "#ffc08a", True, "middle"))
    # 刷新（激励视频）
    bx, by, bw2, bh = 240 - 95, 282, 190, 24
    s.append(f'<rect x="{bx}" y="{by}" width="{bw2}" height="{bh}" rx="12" fill="none" stroke="{B.GBLUE}" stroke-width="1"/>')
    ab, abw = B.ad_badge(bx + 10, by + 7.5, lang)
    s.append(ab + B.play_icon(bx + abw + 20, by + 12, "#8ab4f8", 0.9))
    s.append(text(bx + bw2 / 2 + 12, by + 15.5, t["reroll"], 8, "#8ab4f8", True, "middle"))
    s.append(text(240, 318, t["reroll_pc"], 6.4, MUTED, False, "middle"))
    s.append(text(240, 334, t["pick_key"], 6.8, "#c8d2e3", True, "middle"))
    return B.svg(W, H, "".join(s), defs(), res=3)


# ---------- 3. 车库（局外成长） ----------
POOL = ["rapid", "double", "pierce", "bounce", "shield", "engine", "float", "fortify", "bomb", "freeze", "stealth", "magnet"]
UNLOCKED = {"rapid", "double", "pierce", "bounce", "shield", "engine", "fortify", "bomb", "freeze"}


def garage(lang):
    t = T[lang]
    s = [f'<rect width="{W}" height="{H}" fill="url(#bgH)"/>']
    s.append(text(16, 30, t["g_title"], 16, "#ffffff", True))
    s.append(toggle(428, 14, lang))
    # 左：指挥官等级 + 坦克展示台
    s.append('<rect x="16" y="42" width="170" height="150" rx="10" fill="#ffffff" fill-opacity="0.04" stroke="#263046" stroke-width="0.7"/>')
    s.append(text(28, 60, t["g_lv"], 10, GOLD, True))
    s.append('<rect x="28" y="66" width="146" height="5" rx="2.5" fill="#ffffff" fill-opacity="0.1"/>')
    s.append('<rect x="28" y="66" width="104" height="5" rx="2.5" fill="url(#xp)"/>')
    s.append(text(28, 81, t["g_xp"], 6, "#d9b8ff"))
    s.append('<ellipse cx="101" cy="170" rx="60" ry="12" fill="#3ee8ff" fill-opacity="0.1" stroke="#3ee8ff" stroke-opacity="0.45" stroke-width="0.8"/>')
    s.append(tank_icon(("#ff9a3a", "#8a3d00", "#ffe0b8"), 66, 98, 70, rot=20))
    # 左下：涂装
    s.append(text(16, 210, t["g_skin"], 7, MUTED, True))
    skins = [P1, ("#ff9a3a", "#8a3d00", "#ffe0b8"), ("#b0b8c8", "#4a5266", "#eef2f8"), ("#ff7ab8", "#8a1f55", "#ffd6ea"), ("#2b2f3a", "#0d0f14", "#7a8296")]
    for i, cols in enumerate(skins):
        x = 16 + i * 34
        sel = i == 1
        s.append(f'<rect x="{x}" y="216" width="30" height="30" rx="6" fill="#ffffff" fill-opacity="{0.1 if sel else 0.04}" stroke="{CYAN if sel else "#263046"}" stroke-width="{1.2 if sel else 0.6}"/>')
        s.append(tank_icon(cols, x + 3, 219, 24, 0))
        if i >= 3:
            s.append(f'<rect x="{x}" y="216" width="30" height="30" rx="6" fill="#07090f" fill-opacity="0.55"/>')
            s.append(f'<circle cx="{x + 15}" cy="254" r="3" fill="url(#gold)"/>')
            s.append(text(x + 20, 256.5, "2000" if i == 3 else "3000", 5.4, GOLD, True))
    s.append(f'<circle cx="22" cy="272" r="5" fill="url(#gold)"/>')
    s.append(text(31, 275, f'{t["g_coins"]}  1,860', 8, GOLD, True))
    # 右：芯片图鉴
    s.append(text(200, 54, t["g_pool"], 9, "#ffffff", True))
    s.append(text(200, 66, t["g_pool_d"], 5.8, MUTED))
    for i, k in enumerate(POOL):
        r, c = divmod(i, 4)
        x, y = 200 + c * 66, 74 + r * 52
        un = k in UNLOCKED
        rc = RARITY[PERKS[k][0]]
        s.append(f'<rect x="{x}" y="{y}" width="60" height="46" rx="7" fill="#ffffff" fill-opacity="{0.05 if un else 0.02}" stroke="{rc if un else "#263046"}" stroke-opacity="{0.7 if un else 1}" stroke-width="0.7"/>')
        if un:
            s.append(icon(k, x + 20, y + 6, 20, PERKS[k][1]))
            s.append(text(x + 30, y + 39, perk_name(k, lang), 6.2, "#e6ecf5", True, "middle"))
        else:
            s.append(icon("lock", x + 22, y + 8, 16, "#3a4256"))
            s.append(text(x + 30, y + 39, {"magnet": "Lv13", "float": "Lv14", "stealth": "Lv16"}[k], 6, "#5a6680", True, "middle"))
        if k == "freeze":
            b, _ = pill(x + 38, y - 4, t["g_new"], 5, CYAN, "#06232b", pad=6, h=9)
            s.append(b)
    # 右下：今日任务
    s.append(text(200, 244, t["g_tasks"], 7, MUTED, True))
    for i, (lab, done, prog) in enumerate(((t["g_t1"], False, 0.6), (t["g_t2"], True, 1), (t["g_t3"], False, 0))):
        y = 250 + i * 22
        s.append(f'<rect x="200" y="{y}" width="260" height="18" rx="5" fill="#ffffff" fill-opacity="0.04"/>')
        s.append(f'<rect x="200" y="{y}" width="{260 * prog:.0f}" height="18" rx="5" fill="{GREEN if done else PURPLE}" fill-opacity="0.14"/>')
        s.append(text(208, y + 12, lab, 6.6, "#e6ecf5" if not done else GREEN, True))
        if done:
            s.append(f'<path d="M444 {y + 9}l3 3 6-6" fill="none" stroke="{GREEN}" stroke-width="1.6"/>')
        else:
            s.append(f'<circle cx="446" cy="{y + 9}" r="3.4" fill="url(#gold)"/>')
            s.append(text(438, y + 11.5, "+50", 5.6, GOLD, True, "end"))
    # 底部：赛季（免费）进度
    s.append('<rect x="16" y="318" width="448" height="28" rx="8" fill="#ffffff" fill-opacity="0.04" stroke="#263046" stroke-width="0.6"/>')
    s.append(text(26, 336, t["s_name"], 8, "#ffb020", True))
    sx = 26 + width(t["s_name"], 8, True) + 12
    right = t["s_free"] + " · " + t["s_left"]
    ex = 456 - width(right, 6) - 12
    s.append(f'<rect x="{sx:.1f}" y="329" width="{ex - sx:.1f}" height="6" rx="3" fill="#ffffff" fill-opacity="0.1"/>')
    s.append(f'<rect x="{sx:.1f}" y="329" width="{(ex - sx) * 0.42:.1f}" height="6" rx="3" fill="url(#season)"/>')
    s.append(text(456, 336, right, 6, MUTED, False, "end"))
    return B.svg(W, H, "".join(s), defs(), res=3)


# ---------- 4. 排行榜 ----------
def platform_badge(kind, x, y, s=12):
    """平台标识（示意，不是官方商标）"""
    bg, fg, lab = {"steam": ("#1b2838", "#c7d5e0", "S"), "gc": ("#ffffff", "#ff2d55", "G"), "wx": ("#07c160", "#ffffff", "W"),
                   "gp": ("#01875f", "#ffffff", "P"), "web": ("#3a4660", "#c8d2e3", "W")}[kind]
    return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * 0.25}" fill="{bg}"/>'
            + text(x + s / 2, y + s * 0.72, lab, s * 0.62, fg, True, "middle"))


RANK_ROWS = [
    (1, "Mika_88", "steam", ("pierce", "bounce", "double"), "18,450", False),
    (2, "lin.zhao", "steam", ("freeze", "rapid", "shield"), "16,900", False),
    (3, None, "steam", ("double", "shield", "engine"), "15,200", True),
    (4, "TankDad", "steam", ("bomb", "fortify", "rapid"), "12,050", False),
    (5, "ppx", "steam", ("stealth", "engine"), "9,800", False),
    (6, "Orbit", "steam", ("shield",), "7,400", False),
]


GLOBAL_ROWS = [
    (1, "Kaito", "gc", ("pierce", "bounce", "double", "magnet"), "31,200", False),
    (2, "lea.m", "web", ("pierce", "freeze", "double", "shield"), "30,850", False),
    (3, "RetroRex", "steam", ("bounce", "double", "rapid", "engine"), "29,900", False),
    (4, "ana_b", "gp", ("bomb", "pierce", "shield", "rapid"), "29,400", False),
    (5, "Nono", "steam", ("freeze", "fortify", "double", "engine"), "28,760", False),
    (1204, None, "steam", ("double", "shield", "engine"), "15,200", True),
]


def ranks(lang, tab=0):
    t = T[lang]
    rows = RANK_ROWS if tab == 0 else GLOBAL_ROWS
    s = [f'<rect width="{W}" height="{H}" fill="url(#bgH)"/>']
    s.append(text(16, 30, t["r_title"], 16, "#ffffff", True))
    s.append(toggle(428, 14, lang))
    # 选项卡
    x = 16
    for i, lab in enumerate(t["tabs"]):
        w = width(lab, 8, True) + 22
        sel = i == tab
        s.append(f'<rect x="{x:.1f}" y="42" width="{w:.1f}" height="20" rx="10" fill="{CYAN if sel else "#ffffff"}" fill-opacity="{1 if sel else 0.05}" stroke="{"none" if sel else "#2c3850"}" stroke-width="0.6"/>')
        s.append(text(x + w / 2, 55.6, lab, 8, "#06232b" if sel else "#c8d2e3", True, "middle"))
        x += w + 6
    # 平台范围
    if tab == 0:
        s.append(platform_badge("steam", 16, 72, 13))
        s.append(text(34, 82, t["scope"], 8, "#c7d5e0", True))
        s.append(text(34 + width(t["scope"], 8, True) + 8, 81.6, t["scope_note"], 5.8, MUTED))
    else:
        x = 16
        for k in ("steam", "gc", "gp", "web"):
            s.append(platform_badge(k, x, 72, 13))
            x += 16
        s.append(text(x + 4, 82, t["g_scope"], 8, "#ffffff", True))
        s.append(text(x + 4 + width(t["g_scope"], 8, True) + 8, 81.6, t["g_scope_note"], 5.8, MUTED))
        s.append(text(464, 81.6, t["g_season"], 6, MUTED, False, "end"))
    # 表头
    cols = t["r_cols"]
    y = 100
    s.append(text(28, y, cols[0], 6, MUTED, True, "middle"))
    s.append(text(48, y, cols[1], 6, MUTED, True))
    s.append(text(250, y, cols[2], 6, MUTED, True))
    s.append(text(456, y, cols[3], 6, MUTED, True, "end"))
    for i, (n, name, plat, build, score, me) in enumerate(rows):
        y = 106 + i * 32 + (14 if me and tab == 1 else 0)
        fill, op, stroke = (P1[0], 0.1, P1[0]) if me else ("#ffffff", 0.035, "#263046")
        s.append(f'<rect x="16" y="{y}" width="448" height="28" rx="7" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-opacity="{0.7 if me else 1}" stroke-width="0.7"/>')
        medal = {1: "#ffd23a", 2: "#c8d2e3", 3: "#e0915a"}.get(n)
        if medal:
            s.append(f'<circle cx="28" cy="{y + 14}" r="7" fill="{medal}" fill-opacity="0.9"/>')
            s.append(text(28, y + 17, str(n), 7.5, "#1a1205", True, "middle"))
        else:
            s.append(text(28, y + 17, f"{n:,}", 8 if n < 1000 else 6, "#c8d2e3", True, "middle"))
        s.append(tank_icon(P1 if me else [B.TANKS["player2"], ("#ff9a3a", "#8a3d00", "#ffe0b8"), ("#b0b8c8", "#4a5266", "#eef2f8"), B.TANKS["fast"], B.TANKS["heavy"], ELITE][i], 44, y + 4, 20))
        nm = t["you"] if me else name
        tx = 70
        if tab == 1:  # 全球榜：名字前面是玩家所在的平台
            s.append(platform_badge(plat, 70, y + 8, 12))
            tx = 87
        s.append(text(tx, y + 17.5, nm, 8.5, P1[0] if me else "#ffffff", True))
        lvl = ("Lv4", "Lv4", "Lv3", "Lv3", "Lv2", "Lv1")[i] if tab == 0 else ("Lv4", "Lv4", "Lv4", "Lv4", "Lv4", "Lv3")[i]
        nx = tx + width(nm, 8.5, True) + 6
        b, _ = pill(nx, y + 9, lvl, 5.4, "#2c3850", GOLD, pad=6, h=10)
        s.append(b)
        for j, k in enumerate(build):
            s.append(perk_badge(k, 250 + j * 22, y + 5, 18))
        s.append(text(456, y + 18, score, 10, GOLD if n <= 3 else "#ffffff", True, "end"))
    if tab == 1:
        s.append(text(240, 272, "· · ·", 8, "#5a6680", True, "middle"))
    s.append(text(240, 326 if tab == 1 else 312, t["r_foot"], 6.4, MUTED, False, "middle"))
    if tab == 1:
        return B.svg(W, H, "".join(s), defs(), res=3)
    # 底部：同一个榜在其他平台的样子
    x = 240 - 3 * 70 / 2
    for k, lab in (("gc", "Game Center"), ("wx", "微信好友" if lang == "zh" else "WeChat"), ("web", "Web")):
        s.append(platform_badge(k, x, 324, 11))
        s.append(text(x + 15, 332.5, lab, 6.2, "#7f8ba3", True))
        x += 70
    return B.svg(W, H, "".join(s), defs(), res=3)


# ---------- 5. 主页：每日挑战上线 ----------
def home(lang):
    t = T[lang]
    s = [f'<rect width="{W}" height="{H}" fill="url(#bgH)"/>',
         '<circle cx="340" cy="150" r="140" fill="#c46bff" fill-opacity="0.05"/><circle cx="340" cy="150" r="90" fill="#ffd23a" fill-opacity="0.05"/>']
    title = B.tr("title", lang)
    s.append(text(16, 42, title, 22, "#ffffff", True))
    s.append(text(16 + width(title, 22, True) + 6, 42, "2026", 22, "url(#gold)", True))
    s.append(text(16, 56, B.tr("subtitle", lang), 7.5, "#7f8ba3", True))
    # 开始战役
    s.append('<rect x="16" y="70" width="186" height="46" rx="10" fill="url(#cta)"/>')
    s.append(text(28, 91, t["h_start"], 13, "#ffffff", True))
    s.append(text(28, 106, t["h_start_d"], 6.4, "#fff2e0"))
    c, cw = B.chip(0, 0, "Enter", True)
    s.append(f'<g transform="translate({202 - 10 - cw:.2f},81)">{c}</g>')
    # 每日挑战（新）
    s.append(f'<rect x="16.4" y="124.4" width="185.2" height="62" rx="10" fill="{PURPLE}" fill-opacity="0.12" stroke="{PURPLE}" stroke-width="1"/>')
    s.append(text(28, 143, t["h_daily"], 11.5, "#ffffff", True))
    b, bw = pill(28 + width(t["h_daily"], 11.5, True) + 6, 134, "#301", 5.8, PURPLE, "#1a0b2b", pad=8, h=11)
    s.append(b)
    s.append(text(28, 156, t["h_daily_d"], 6.2, "#d9b8ff"))
    s.append(text(28, 175, t["h_daily_t"], 8, "#ffffff", True))
    s.append(text(192, 175, t["h_daily_rank"], 6.2, GOLD, True, "end"))
    c, cw = B.chip(0, 0, "D", True)
    s.append(f'<g transform="translate({192 - cw:.2f},134.5)">{c}</g>')
    # 双人、编辑器（小卡）
    for i, (k, key) in enumerate((("h_coop", "C"), ("h_maker", "E"))):
        x = 16 + i * 96
        s.append(f'<rect x="{x + 0.4}" y="194.4" width="89.2" height="30" rx="8" fill="{CYAN}" fill-opacity="0.07" stroke="{CYAN}" stroke-opacity="0.5" stroke-width="0.7"/>')
        s.append(text(x + 10, 213.5, t[k], 8.5, "#ffffff", True))
        c, cw = B.chip(0, 0, key, True)
        s.append(f'<g transform="translate({x + 90 - 8 - cw:.2f},204.5)">{c}</g>')
    # 车库、排行榜、赛季（图标按钮）
    for i, (k, ic) in enumerate((("h_garage", "garage"), ("h_rank", "rank"), ("h_season", "season"))):
        x = 16 + i * 64
        s.append(f'<rect x="{x + 0.4}" y="232.4" width="57.2" height="50" rx="8" fill="#ffffff" fill-opacity="0.04" stroke="#2c3850" stroke-width="0.7"/>')
        cx = x + 29
        if ic == "garage":
            s.append(tank_icon(P1, cx - 10, 238, 20))
        elif ic == "rank":
            for j, (hh, col) in enumerate(((10, "#c8d2e3"), (16, GOLD), (7, "#e0915a"))):
                s.append(f'<rect x="{cx - 10 + j * 7}" y="{258 - hh}" width="6" height="{hh}" rx="1" fill="{col}"/>')
        else:
            s.append(star(cx, 248, 8, "#ffb020"))
        s.append(text(cx, 270, t[k], 7, "#e6ecf5", True, "middle"))
        if ic == "season":
            b, _ = pill(x + 34, 228, t["h_hot"], 5, "#ff5a1a", "#ffffff", pad=6, h=9)
            s.append(b)
    s.append(text(16, 300, "S1 · " + t["s_left"], 6.4, "#ffb020", True))
    s.append('<rect x="16" y="304" width="186" height="4" rx="2" fill="#ffffff" fill-opacity="0.1"/>')
    s.append('<rect x="16" y="304" width="78" height="4" rx="2" fill="url(#season)"/>')
    # 展示台：Lv4 坦克 + 掉落的芯片
    s.append('<ellipse cx="340" cy="236" rx="96" ry="20" fill="#c46bff" fill-opacity="0.1" stroke="#c46bff" stroke-opacity="0.45" stroke-width="0.8"/>')
    s.append(tank_icon(("#ff9a3a", "#8a3d00", "#ffe0b8"), 296, 150, 88, rot=15))
    s.append(chip_drop(410, 150, 11))
    s.append(chip_drop(262, 186, 7))
    s.append(lv_stars(316, 132, 4, r=5, gap=13))
    s.append(toggle(428, 9, lang))
    s.append(img(B.banner(lang)[0], 16, 316, 448, 32))
    return B.svg(W, H, "".join(s), defs(), res=3)


# ---------- 6. 分享战报（微信 / 朋友圈 / 短视频） ----------
def share(lang):
    t = T[lang]
    s = [f'<rect width="{W}" height="{H}" fill="#05070c"/>']
    # 竖版战报卡
    x0, y0, cw, ch = 150, 14, 180, 300
    s.append(f'<rect x="{x0}" y="{y0}" width="{cw}" height="{ch}" rx="14" fill="url(#bgH)" stroke="{PURPLE}" stroke-width="1"/>')
    s.append(f'<rect x="{x0}" y="{y0}" width="{cw}" height="72" rx="14" fill="{PURPLE}" fill-opacity="0.16"/>')
    title = B.tr("title", lang)
    s.append(text(x0 + 14, y0 + 20, title + " 2026", 8, "#ffffff", True))
    ts = min(13, 112 / width(t["sh_title"], 1, True))  # 标题不能压到右边的坦克
    s.append(text(x0 + 14, y0 + 40, t["sh_title"], ts, "#f3dcff", True))
    s.append(text(x0 + 14, y0 + 56, t["sh_time"] + " · " + t["sh_score"], 7, "#d9b8ff", True))
    s.append(tank_icon(("#ff9a3a", "#8a3d00", "#ffe0b8"), x0 + 124, y0 + 18, 46, rot=20))
    # 迷你战场（每日挑战的地图缩略图）
    mx, my, ms = x0 + 14, y0 + 82, 7.0
    s.append(f'<rect x="{mx - 2}" y="{my - 2}" width="{13 * ms + 4}" height="{13 * ms + 4}" rx="3" fill="#0b0f18"/>')
    colmap = {"B": "#b5562e", "S": "#9aa6b8", "W": "#2f7fd6", "G": "#2e8a3a", "E": "#ffd23a"}
    for r, line in enumerate(JUNGLE):
        for c, chh in enumerate(line):
            if chh in colmap:
                s.append(f'<rect x="{mx + c * ms:.1f}" y="{my + r * ms:.1f}" width="{ms - 0.6:.1f}" height="{ms - 0.6:.1f}" rx="0.8" fill="{colmap[chh]}"/>')
    # 右边：排名
    rx = mx + 13 * ms + 10
    s.append(text(rx, my + 12, "TOP", 7, GOLD, True))
    s.append(text(rx, my + 34, "8%", 22, GOLD, True))
    s.append(text(rx, my + 50, t["sh_friend"], 6, "#e6ecf5", True))
    for i in range(7):  # 打卡格子（微信好友排名只能在开放数据域里画，不能放进分享图）
        s.append(f'<rect x="{rx + i * 8}" y="{my + 58}" width="6.4" height="6.4" rx="1.2" fill="{GREEN}"/>')
    s.append(text(x0 + cw / 2, my + 112, t["sh_rank"], 7, "#ffffff", True, "middle"))
    # 芯片组合
    s.append(text(x0 + 14, my + 132, t["sh_build"], 6.4, MUTED, True))
    for j, k in enumerate(("pierce", "bounce", "double", "shield")):
        s.append(perk_badge(k, x0 + 14 + j * 30, my + 138, 24))
    # 二维码占位 + 号召
    qx, qy = x0 + 14, y0 + ch - 54
    s.append(f'<rect x="{qx}" y="{qy}" width="40" height="40" rx="4" fill="#ffffff"/>')
    for i in range(36):
        if (i * 2654435761 >> 7) % 7 < 4 or i in (0, 5, 30):
            s.append(f'<rect x="{qx + 4 + (i % 6) * 5.4:.1f}" y="{qy + 4 + (i // 6) * 5.4:.1f}" width="4.4" height="4.4" fill="#111"/>')
    s.append(text(qx + 48, qy + 15, t["sh_chal"], 9, "#ffffff", True))
    s.append(text(qx + 48, qy + 27, t["sh_cta"], 6, "#d9b8ff"))
    # 卡片下方：按钮
    s.append(f'<rect x="{x0 - 30}" y="324" width="116" height="24" rx="12" fill="#07c160"/>')
    s.append(text(x0 + 28, 339.5, t["sh_btn"], 8.5, "#ffffff", True, "middle"))
    s.append(f'<rect x="{x0 + 94}" y="324" width="116" height="24" rx="12" fill="#ffffff" fill-opacity="0.06" stroke="#3a4660" stroke-width="0.7"/>')
    s.append(text(x0 + 152, 339.5, t["sh_btn2"], 8.5, "#c8d2e3", True, "middle"))
    # 左右两侧的说明
    s.append(text(16, 150, "1", 20, PURPLE, True))
    s.append(text(16, 166, "同图同芯片" if lang == "zh" else "Same seed", 7.5, "#ffffff", True))
    s.append(text(16, 178, "比的是操作和选择" if lang == "zh" else "Skill + choices", 6, MUTED))
    s.append(text(464, 150, "2", 20, PURPLE, True, "end"))
    s.append(text(464, 166, "好友助战" if lang == "zh" else "Friend assist", 7.5, "#ffffff", True, "end"))
    lines = ("好友点开链接，", "他的坦克来帮你打一关") if lang == "zh" else ("A friend opens the link,", "their tank joins your stage")
    s.append(text(464, 178, lines[0], 6, MUTED, False, "end"))
    s.append(text(464, 188, lines[1], 6, MUTED, False, "end"))
    return B.svg(W, H, "".join(s), defs(), res=3)


def main():
    out = {}
    for lang in ("zh", "en"):
        out[f"v6-battle-{lang}.svg"] = battle(lang)
        out[f"v6-pick-{lang}.svg"] = pick(lang)
        out[f"v6-garage-{lang}.svg"] = garage(lang)
        out[f"v6-ranks-{lang}.svg"] = ranks(lang)
        out[f"v6-ranks-global-{lang}.svg"] = ranks(lang, tab=1)
        out[f"v6-home-{lang}.svg"] = home(lang)
        out[f"v6-share-{lang}.svg"] = share(lang)
    for name, content in out.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
            f.write(content)
    print("wrote", ", ".join(out))


if __name__ == "__main__":
    main()
