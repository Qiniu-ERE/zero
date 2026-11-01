#!/usr/bin/env python3
"""坦克大战 v6 自建排行榜服务：上传成绩、读榜单、查排名（见 docs/v6/PLAN.md 第五节）。

用法：python3 server/leaderboard.py --host 127.0.0.1 --port 8787 --db lb.sqlite
      python3 server/leaderboard.py --trust-proxy   # 部署在反向代理 / 无服务器容器后面时，按 X-Forwarded-For 限频

只用 Python 标准库（http.server、sqlite3、json、threading），不依赖第三方库。
海外榜（global）和国内榜（cn）是两张完全分开的榜；正式上线时两个区各部署一份，国内数据存境内。
接口和校验规则见 server/README.md。
"""
import argparse
import json
import re
import sqlite3
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

API_VERSION = "1"
MAX_BODY = 4096                 # 请求体上限 4 KB
TZ_OFFSET = 8 * 3600            # 按北京时间（UTC+8）切天
PLAYER_RE = re.compile(r"^[0-9a-f]{16}$")
REGIONS = {"global", "cn"}
BOARDS = {"weekly", "daily"}
CHIPS = {"rapid", "double", "pierce", "bounce", "shield", "engine", "float", "stealth", "magnet"}
MAX_SCORE = 30000
SECS = (20, 3600)               # 一局用时的合理范围（秒）
STAGES = 10                     # 一共 10 关；每日挑战必须打通
MAX_CHIPS = 3                   # 最多 3 块芯片，等级 = 芯片数 + 1（Lv1~Lv4）
MAX_VERSION = 16
LIMIT_DEFAULT, LIMIT_MAX = 10, 50
RATE_WINDOW = 60                # 限频窗口（秒）
RATE_PLAYER = 10                # 同一玩家每个窗口最多上传次数
RATE_IP = 30                    # 同一 IP 每个窗口最多上传次数


def day_of(t):
    """unix 秒 → 第几天（UTC+8）"""
    return (int(t) + TZ_OFFSET) // 86400


def week_of(t):
    """unix 秒 → 第几周（周一开始；第 0 天 1970-01-01 是周四，所以减 4）"""
    return (day_of(t) - 4) // 7


def tag_of(player):
    """玩家在游戏里显示成“指挥官 #tag”"""
    return int(player[:4], 16) % 10000


def is_int(v):
    """JSON 里的整数（排除 true / false）"""
    return isinstance(v, int) and not isinstance(v, bool)


def check_score(body, t):
    """检查一条上传成绩，合法返回 None，否则返回中文原因"""
    if not isinstance(body, dict):
        return "请求体应该是 JSON 对象"
    player = body.get("player")
    if not isinstance(player, str) or not PLAYER_RE.match(player):
        return "玩家 ID 应该是 16 位小写十六进制"
    if body.get("region") not in REGIONS:
        return "region 只能是 global 或 cn"
    board = body.get("board")
    if board not in BOARDS:
        return "board 只能是 weekly 或 daily"
    period = body.get("period")
    if not is_int(period):
        return "period 应该是整数"
    now = day_of(t) if board == "daily" else week_of(t)
    if period not in (now, now - 1):
        return "期数不对：只能上传本期或上一期"
    score = body.get("score")
    if not is_int(score) or not 0 <= score <= MAX_SCORE:
        return f"分数应该是 0~{MAX_SCORE} 的整数"
    secs = body.get("secs")
    if not is_int(secs) or not SECS[0] <= secs <= SECS[1]:
        return f"用时应该是 {SECS[0]}~{SECS[1]} 秒"
    stage = body.get("stage")
    if not is_int(stage) or not 1 <= stage <= STAGES:
        return f"关卡应该是 1~{STAGES}"
    if board == "daily" and stage != STAGES:
        return "每日挑战要打通全部关卡才能上榜"
    chips = body.get("chips")
    if not isinstance(chips, list) or len(chips) > MAX_CHIPS:
        return f"芯片最多 {MAX_CHIPS} 块"
    if not all(isinstance(c, str) and c in CHIPS for c in chips):
        return "有不认识的芯片"
    if len(set(chips)) != len(chips):
        return "芯片不能重复"
    level = body.get("level")
    if not is_int(level) or level != len(chips) + 1:
        return "等级应该等于芯片数 + 1"
    version = body.get("version")
    if not isinstance(version, str) or not 1 <= len(version) <= MAX_VERSION:
        return f"版本号应该是 1~{MAX_VERSION} 个字符"
    return None


class RateLimiter:
    """滑动窗口限频：同一个键在 window 秒内最多 limit 次（被拒的那次不算）"""

    def __init__(self, limit, window=RATE_WINDOW):
        self.limit, self.window = limit, window
        self.hits = {}

    def allow(self, key, t):
        q = self.hits.setdefault(key, deque())
        while q and q[0] <= t - self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(t)
        return True

    def sweep(self, t):
        """清掉已经过期的键，免得内存一直涨"""
        for key in [k for k, q in self.hits.items() if not q or q[-1] <= t - self.window]:
            del self.hits[key]


class Store:
    """sqlite 存储：每个（区、榜、期、玩家）只留最好成绩；同分按先提交的排前面"""

    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        with self.lock, self.db:
            self.db.execute("""CREATE TABLE IF NOT EXISTS scores (
                region TEXT NOT NULL, board TEXT NOT NULL, period INTEGER NOT NULL,
                player TEXT NOT NULL, score INTEGER NOT NULL, secs INTEGER NOT NULL,
                stage INTEGER NOT NULL, chips TEXT NOT NULL, level INTEGER NOT NULL,
                version TEXT NOT NULL, at REAL NOT NULL, seq INTEGER NOT NULL,
                PRIMARY KEY (region, board, period, player))""")
            self.db.execute("""CREATE INDEX IF NOT EXISTS scores_rank
                ON scores (region, board, period, score DESC, at, seq)""")

    def submit(self, b, t):
        """写入一条成绩（比原来的高才覆盖），返回 (名次, 总人数, 最好成绩)"""
        key = (b["region"], b["board"], b["period"], b["player"])
        with self.lock, self.db:
            row = self.db.execute(
                "SELECT score FROM scores WHERE region=? AND board=? AND period=? AND player=?", key).fetchone()
            if row is None or b["score"] > row[0]:
                # seq 全局递增：同一秒内同分时，先提交的排前面
                seq = self.db.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM scores").fetchone()[0]
                self.db.execute("INSERT OR REPLACE INTO scores VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                key + (b["score"], b["secs"], b["stage"], json.dumps(b["chips"]),
                                       b["level"], b["version"], t, seq))
            return self._rank(*key)

    def rank(self, region, board, period, player):
        with self.lock:
            return self._rank(region, board, period, player)

    def _total(self, region, board, period):
        return self.db.execute("SELECT COUNT(*) FROM scores WHERE region=? AND board=? AND period=?",
                               (region, board, period)).fetchone()[0]

    def _rank(self, region, board, period, player):
        """返回 (名次, 总人数, 分数)；不在榜上时名次和分数都是 0"""
        total = self._total(region, board, period)
        row = self.db.execute(
            "SELECT score, at, seq FROM scores WHERE region=? AND board=? AND period=? AND player=?",
            (region, board, period, player)).fetchone()
        if row is None:
            return 0, total, 0
        score, at, seq = row
        ahead = self.db.execute("""SELECT COUNT(*) FROM scores WHERE region=? AND board=? AND period=?
            AND (score > ? OR (score = ? AND (at < ? OR (at = ? AND seq < ?))))""",
                                (region, board, period, score, score, at, at, seq)).fetchone()[0]
        return ahead + 1, total, score

    def top(self, region, board, period, limit):
        """返回 (总人数, 前 limit 名)"""
        with self.lock:
            total = self._total(region, board, period)
            rows = self.db.execute("""SELECT player, score, chips, level FROM scores
                WHERE region=? AND board=? AND period=? ORDER BY score DESC, at, seq LIMIT ?""",
                                   (region, board, period, limit)).fetchall()
        return total, [{"rank": i + 1, "player": p, "tag": tag_of(p), "score": s,
                        "chips": json.loads(c), "level": lv} for i, (p, s, c, lv) in enumerate(rows)]

    def close(self):
        with self.lock:
            self.db.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "TankBattleLeaderboard/" + API_VERSION
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if not self.server.quiet:
            super().log_message(fmt, *args)

    def send_json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        if self.close_connection:
            self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def fail(self, code, error):
        self.send_json(code, {"ok": False, "error": error})

    def client_ip(self):
        if self.server.trust_proxy:
            fwd = self.headers.get("X-Forwarded-For", "")
            if fwd.strip():
                return fwd.split(",")[0].strip()
        return self.client_address[0]

    def do_OPTIONS(self):
        """浏览器跨域预检（网页版从浏览器直接调用）"""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[-1] for k, v in parse_qs(url.query).items()}
        if url.path == "/v1/health":
            return self.send_json(200, {"ok": True, "version": API_VERSION})
        if url.path not in ("/v1/board", "/v1/rank"):
            return self.fail(404, "没有这个接口")
        region, board = q.get("region"), q.get("board")
        if region not in REGIONS:
            return self.fail(400, "region 只能是 global 或 cn")
        if board not in BOARDS:
            return self.fail(400, "board 只能是 weekly 或 daily")
        period = q.get("period", "")
        if not re.fullmatch(r"\d{1,9}", period):
            return self.fail(400, "period 应该是非负整数")
        period = int(period)
        store = self.server.store
        if url.path == "/v1/board":
            limit = q.get("limit", str(LIMIT_DEFAULT))
            if not re.fullmatch(r"\d{1,3}", limit) or not 1 <= int(limit) <= LIMIT_MAX:
                return self.fail(400, f"limit 应该是 1~{LIMIT_MAX}")
            total, rows = store.top(region, board, period, int(limit))
            return self.send_json(200, {"ok": True, "total": total, "rows": rows})
        player = q.get("player", "")
        if not PLAYER_RE.match(player):
            return self.fail(400, "玩家 ID 应该是 16 位小写十六进制")
        rank, total, score = store.rank(region, board, period, player)
        return self.send_json(200, {"ok": True, "rank": rank, "total": total, "score": score})

    def do_POST(self):
        if urlparse(self.path).path != "/v1/score":
            self.close_connection = True   # 没读请求体，这条连接不能再复用
            return self.fail(404, "没有这个接口")
        try:
            size = int(self.headers.get("Content-Length", ""))
        except ValueError:
            size = -1
        if not 0 <= size <= MAX_BODY:
            self.close_connection = True
            return self.fail(400, f"请求体不能超过 {MAX_BODY} 字节")
        raw = self.rfile.read(size)
        srv = self.server
        t = srv.now()
        # 先按 IP 限频（每次上传都算），再按玩家限频（玩家 ID 格式对了才算）
        with srv.rate_lock:
            srv.ip_limit.sweep(t)
            srv.player_limit.sweep(t)
            if not srv.ip_limit.allow(self.client_ip(), t):
                return self.fail(429, "上传太频繁，请稍后再试")
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return self.fail(400, "请求体不是合法的 JSON")
        player = body.get("player") if isinstance(body, dict) else None
        if isinstance(player, str) and PLAYER_RE.match(player):
            with srv.rate_lock:
                if not srv.player_limit.allow(player, t):
                    return self.fail(429, "上传太频繁，请稍后再试")
        err = check_score(body, t)
        if err:
            return self.fail(400, err)
        rank, total, best = srv.store.submit(body, t)
        return self.send_json(200, {"ok": True, "rank": rank, "total": total, "best": best})


class LeaderboardServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, addr, db_path, now=time.time, trust_proxy=False, quiet=False):
        self.store = Store(db_path)
        self.now = now
        self.trust_proxy = trust_proxy
        self.quiet = quiet
        self.rate_lock = threading.Lock()
        self.ip_limit = RateLimiter(RATE_IP)
        self.player_limit = RateLimiter(RATE_PLAYER)
        super().__init__(addr, Handler)

    def server_close(self):
        super().server_close()
        self.store.close()


def make_server(host, port, db_path, now=time.time, trust_proxy=False, quiet=False):
    """建一个服务对象（还没开始 serve_forever）；port=0 时由系统分配端口，用 server.server_address 取"""
    return LeaderboardServer((host, port), db_path, now=now, trust_proxy=trust_proxy, quiet=quiet)


def main(argv=None):
    ap = argparse.ArgumentParser(description="坦克大战排行榜服务")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--db", default="lb.sqlite", help="sqlite 文件路径")
    ap.add_argument("--trust-proxy", action="store_true",
                    help="按 X-Forwarded-For 的第一个地址限频（只在可信的反向代理后面打开）")
    args = ap.parse_args(argv)
    srv = make_server(args.host, args.port, args.db, trust_proxy=args.trust_proxy)
    print(f"排行榜服务已启动：http://{args.host}:{srv.server_address[1]}/v1/health", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
