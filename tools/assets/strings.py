"""v2.0 文案表：key -> (中文, English)。效果图和游戏共用，字体子集也从这里生成。"""

STRINGS = {
    # 通用
    "title": ("坦克大战", "BATTLE CITY"),
    "lang.zh": ("中", "中"),
    "lang.en": ("EN", "EN"),
    "hint.style": ("切换画风", "Art style"),
    "hint.lang": ("中 / EN", "中 / EN"),
    "go": ("去挑战", "Play"),
    # 对局 HUD
    "stage": ("第 3 关 · 钢铁峡谷", "Stage 3 · Steel Canyon"),
    "enemies": ("敌军", "Enemies"),
    "score": ("得分", "SCORE"),
    "combo": ("连击", "COMBO"),
    "lives": ("生命", "LIVES"),
    "perks": ("本局强化", "PERKS"),
    "rank": ("今日排名", "Today's rank"),
    "p2": ("2P 小明", "2P Ming"),
    # 广告（Google 原生广告样式）
    "ad.badge": ("广告", "Ad"),
    "ad.brand": ("示例品牌", "Sample Brand"),
    "ad.head": ("云存储新用户免费 10GB", "10 GB free cloud storage"),
    "ad.cta": ("了解更多", "Learn more"),
    "ad.banner": ("示例品牌 · 云存储，新用户免费 10GB", "Sample Brand · 10 GB free cloud storage"),
    # 通关
    "clear": ("第 3 关 完成", "STAGE 3 CLEAR"),
    "st.kills": ("击毁", "Kills"),
    "st.time": ("用时", "Time"),
    "st.combo": ("最高连击", "Best combo"),
    "st.base": ("基地", "Base"),
    "coins": ("金币", "Coins"),
    "ad.double": ("看视频 金币×2", "Watch ad · 2× coins"),
    "choose": ("选择一项强化", "Choose a perk"),
    "r.rare": ("稀有", "RARE"),
    "r.epic": ("史诗", "EPIC"),
    "r.common": ("普通", "COMMON"),
    "pk.ricochet": ("弹射弹", "Ricochet"),
    "pk.ricochet.d": ("子弹可反弹一次", "Bullets bounce once"),
    "pk.drone": ("无人机僚机", "Wingman Drone"),
    "pk.drone.d": ("自动射击的僚机", "Fires on its own"),
    "pk.iron": ("钢铁之心", "Iron Base"),
    "pk.iron.d": ("基地护甲 +2", "Base armor +2"),
    "continue": ("继续", "Continue"),
    # 复活
    "lost": ("基地失守", "BASE LOST"),
    "lost.sub": ("只差 3 辆敌人就通关了", "Only 3 enemies to go"),
    "revive.ad": ("看视频复活", "Watch ad to revive"),
    "revive.ad.sub": ("基地修复 + 5 秒护盾", "Base repaired + 5s shield"),
    "revive.ad.len": ("广告 · 15 秒", "Ad · 15s"),
    "revive.gem": ("50 钻石复活", "Revive for 50 gems"),
    "giveup": ("放弃", "Give up"),
    # 主页
    "m.campaign": ("开始战役", "Campaign"),
    "m.campaign.d": ("35 关剧情模式", "35 story stages"),
    "m.daily": ("每日挑战", "Daily Challenge"),
    "m.daily.d": ("AI 每日一图，全服同图", "New AI map every day"),
    "m.coop": ("双人合作", "Co-op"),
    "m.coop.d": ("本地双人", "Local 2 players"),
    "m.ai": ("AI 造关", "AI Level Maker"),
    "m.ai.d": ("一句话生成地图", "Describe it, play it"),
    "new": ("新", "NEW"),
    "language": ("语言", "Language"),
    "subtitle": ("经典重铸", "REFORGED"),
}


def tr(key, lang):
    zh, en = STRINGS[key]
    return zh if lang == "zh" else en
