"""R10~R29：自建排行榜服务 server/leaderboard.py（见 docs/v6/PLAN.md 第五、六节）

每个用例在系统分配的端口上起一个新服务，用临时 sqlite 文件和假时钟，互不影响。
"""
import http.client
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "server"))
import leaderboard as lb  # noqa: E402

# 2026-11-02（周一）北京时间 12:00
T0 = 1793592000
DAY = lb.day_of(T0)
WEEK = lb.week_of(T0)


class Clock:
    """假时钟：测试里手动拨"""

    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


def pid(n):
    """第 n 个玩家的 ID（16 位小写十六进制）"""
    return f"{n:016x}"


def entry(**kw):
    """一条合法的每日挑战成绩，kw 覆盖其中的字段"""
    b = {"player": pid(1), "region": "global", "board": "daily", "period": DAY, "score": 1200,
         "secs": 300, "stage": 10, "chips": ["rapid", "shield"], "level": 3, "version": "6.0.0"}
    b.update(kw)
    return b


class Base(unittest.TestCase):
    trust_proxy = False

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "lb.sqlite")
        self.clock = Clock(T0)
        self.start()

    def start(self):
        self.srv = lb.make_server("127.0.0.1", 0, self.db, now=self.clock,
                                  trust_proxy=self.trust_proxy, quiet=True)
        self.port = self.srv.server_address[1]
        self.th = threading.Thread(target=self.srv.serve_forever, args=(0.05,), daemon=True)
        self.th.start()

    def stop(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.th.join()

    def tearDown(self):
        self.stop()
        shutil.rmtree(self.tmp)

    def request(self, method, path, body=None, headers=None):
        """发一个请求，返回 (状态码, 响应头, 解析后的 JSON 或 None)"""
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            h = dict(headers or {})
            if body is not None and not isinstance(body, bytes):
                body = json.dumps(body).encode("utf-8")
                h.setdefault("Content-Type", "application/json")
            conn.request(method, path, body=body, headers=h)
            resp = conn.getresponse()
            data = resp.read()
            return resp.status, resp, json.loads(data) if data else None
        finally:
            conn.close()

    def post(self, body, headers=None):
        code, _, data = self.request("POST", "/v1/score", body, headers)
        return code, data

    def get(self, path):
        code, _, data = self.request("GET", path)
        return code, data

    def board(self, region="global", board="daily", period=DAY, limit=None):
        q = f"/v1/board?region={region}&board={board}&period={period}"
        if limit is not None:
            q += f"&limit={limit}"
        return self.get(q)

    def rank(self, player, region="global", board="daily", period=DAY):
        return self.get(f"/v1/rank?region={region}&board={board}&period={period}&player={player}")

    def assertRejected(self, body, words, code=400):
        # 校验用例会连着传很多条非法成绩，先清掉限频计数，免得被 429 挡住（限频由 R24 / R25 单独测）
        with self.srv.rate_lock:
            self.srv.ip_limit.hits.clear()
            self.srv.player_limit.hits.clear()
        got, data = self.post(body)
        self.assertEqual(got, code, f"应该被拒：{body}")
        self.assertFalse(data["ok"])
        self.assertIn(words, data["error"])


class Leaderboard(Base):
    def test_R10_health_cors_and_preflight(self):
        code, resp, data = self.request("GET", "/v1/health")
        self.assertEqual(code, 200)
        self.assertEqual(data, {"ok": True, "version": "1", "day": DAY, "week": WEEK})  # 网页版靠它拿到今天的日期
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        self.assertEqual(resp.getheader("Access-Control-Allow-Origin"), "*")
        # 浏览器跨域预检
        code, resp, data = self.request("OPTIONS", "/v1/score",
                                        headers={"Origin": "https://example.com",
                                                 "Access-Control-Request-Method": "POST",
                                                 "Access-Control-Request-Headers": "content-type"})
        self.assertEqual(code, 204)
        self.assertIsNone(data)
        self.assertEqual(resp.getheader("Access-Control-Allow-Origin"), "*")
        self.assertIn("POST", resp.getheader("Access-Control-Allow-Methods"))
        self.assertIn("Content-Type", resp.getheader("Access-Control-Allow-Headers"))
        # 出错的响应也要带跨域头，网页版才读得到错误原因
        code, resp, _ = self.request("POST", "/v1/score", {"player": "x"})
        self.assertEqual(code, 400)
        self.assertEqual(resp.getheader("Access-Control-Allow-Origin"), "*")

    def test_R11_unknown_path_404_json(self):
        for method, path in [("GET", "/"), ("GET", "/v2/board"), ("POST", "/v1/board"), ("POST", "/v1/health")]:
            with self.subTest(method=method, path=path):
                code, resp, data = self.request(method, path, {} if method == "POST" else None)
                self.assertEqual(code, 404)
                self.assertFalse(data["ok"])
                self.assertTrue(data["error"])
                self.assertEqual(resp.getheader("Access-Control-Allow-Origin"), "*")

    def test_R12_upload_and_read_board(self):
        code, data = self.post(entry())
        self.assertEqual(code, 200)
        self.assertEqual(data, {"ok": True, "rank": 1, "total": 1, "best": 1200})
        code, data = self.post(entry(player=pid(2), score=2000, chips=[], level=1))
        self.assertEqual(data, {"ok": True, "rank": 1, "total": 2, "best": 2000})
        code, data = self.board()
        self.assertEqual(code, 200)
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["rows"], [
            {"rank": 1, "player": pid(2), "tag": 0, "score": 2000, "chips": [], "level": 1},
            {"rank": 2, "player": pid(1), "tag": 0, "score": 1200, "chips": ["rapid", "shield"], "level": 3},
        ])
        # tag = 前 4 位十六进制 % 10000
        p = "ffff0123456789ab"
        self.post(entry(player=p, score=10))
        self.assertEqual(self.board()[1]["rows"][-1]["tag"], 0xFFFF % 10000)
        self.assertEqual(lb.tag_of("2710aaaaaaaaaaaa"), 0)   # 0x2710 = 10000
        self.assertEqual(lb.tag_of("0457aaaaaaaaaaaa"), 1111)

    def test_R13_keep_best_score_only(self):
        self.post(entry(player=pid(2), score=1500))
        self.post(entry(score=1000))
        code, data = self.post(entry(score=800, chips=[], level=1))   # 更低：不覆盖，但照样返回名次
        self.assertEqual(code, 200)
        self.assertEqual(data, {"ok": True, "rank": 2, "total": 2, "best": 1000})
        row = self.board()[1]["rows"][1]
        self.assertEqual((row["score"], row["chips"], row["level"]), (1000, ["rapid", "shield"], 3))
        code, data = self.post(entry(score=1600, chips=["magnet"], level=2))   # 更高：覆盖
        self.assertEqual(data, {"ok": True, "rank": 1, "total": 2, "best": 1600})
        row = self.board()[1]["rows"][0]
        self.assertEqual((row["player"], row["score"], row["chips"], row["level"]), (pid(1), 1600, ["magnet"], 2))
        self.assertEqual(self.board()[1]["total"], 2, "同一玩家只占一行")

    def test_R14_tie_ranked_by_earlier_submission(self):
        self.post(entry(player=pid(1), score=500))
        self.clock.t += 5
        self.post(entry(player=pid(2), score=500))
        self.post(entry(player=pid(3), score=500))     # 同一秒，按提交顺序
        self.clock.t += 5
        code, data = self.post(entry(player=pid(1), score=500))   # 同分重传不刷新时间，名次不变
        self.assertEqual(data["rank"], 1)
        rows = self.board()[1]["rows"]
        self.assertEqual([r["player"] for r in rows], [pid(1), pid(2), pid(3)])
        self.assertEqual([r["rank"] for r in rows], [1, 2, 3])
        self.assertEqual(self.rank(pid(3))[1]["rank"], 3)
        # 后来者刷出更高分，提交时间按刷新那次算
        self.post(entry(player=pid(2), score=600))
        self.post(entry(player=pid(1), score=600))
        self.assertEqual([r["player"] for r in self.board()[1]["rows"]], [pid(2), pid(1), pid(3)])

    def test_R15_player_region_board_validation(self):
        for p in ["", "0" * 15, "0" * 17, "ABCDEF0123456789", "g000000000000000", 12345, None]:
            with self.subTest(player=p):
                self.assertRejected(entry(player=p), "玩家 ID")
        for r in ["", "us", "CN", None]:
            with self.subTest(region=r):
                self.assertRejected(entry(region=r), "region")
        for b in ["", "monthly", "Daily", None]:
            with self.subTest(board=b):
                self.assertRejected(entry(board=b), "board")
        self.assertEqual(self.board()[1]["total"], 0, "被拒的成绩不能进榜")

    def test_R16_daily_period_and_late_upload(self):
        self.assertRejected(entry(period=DAY + 1), "期数")
        self.assertRejected(entry(period=DAY - 2), "期数")
        self.assertRejected(entry(period=str(DAY)), "period")
        self.assertRejected(entry(period=float(DAY)), "period")
        self.assertEqual(self.post(entry())[0], 200)
        # 离线补传：过了零点还能传昨天的，再过一天就不行了
        self.clock.t += 86400
        self.assertEqual(self.post(entry(player=pid(2), period=DAY))[0], 200)
        self.assertEqual(self.post(entry(player=pid(3), period=DAY + 1))[0], 200)
        self.clock.t += 86400
        self.assertRejected(entry(player=pid(4), period=DAY), "期数")
        self.assertEqual(self.board(period=DAY)[1]["total"], 2)
        self.assertEqual(self.board(period=DAY + 1)[1]["total"], 1)

    def test_R17_time_model_and_weekly_period(self):
        # 北京时间零点切天：UTC 16:00 是下一天
        self.assertEqual(lb.day_of(0), 0)
        self.assertEqual(lb.day_of(16 * 3600 - 1), 0)
        self.assertEqual(lb.day_of(16 * 3600), 1)
        # 周一开始：1970-01-05（周一）北京时间 00:00 是第 0 周的第一秒，前一秒还在第 -1 周
        monday = 4 * 86400 - 8 * 3600
        self.assertEqual(lb.week_of(monday), 0)
        self.assertEqual(lb.week_of(monday - 1), -1)
        self.assertEqual(lb.week_of(monday + 7 * 86400 - 1), 0)
        self.assertEqual(lb.week_of(monday + 7 * 86400), 1)
        # T0 是周一中午：本周第一天
        self.assertEqual((DAY - 4) % 7, 0)
        w = entry(board="weekly", period=WEEK, stage=4)
        self.assertEqual(self.post(w)[0], 200)
        self.assertEqual(self.post(dict(w, player=pid(2), period=WEEK - 1))[0], 200)
        self.assertRejected(dict(w, player=pid(3), period=WEEK + 1), "期数")
        self.assertRejected(dict(w, player=pid(3), period=WEEK - 2), "期数")
        self.assertRejected(dict(w, player=pid(3), period=DAY), "期数")   # 每日的期数不能用在周榜
        # 周榜和每日榜互不影响
        self.assertEqual(self.board(board="weekly", period=WEEK)[1]["total"], 1)
        self.assertEqual(self.board(period=WEEK)[1]["total"], 0)

    def test_R18_score_range(self):
        # 每日挑战只有一关：最多 11000 分
        for s in [0, 11000]:
            with self.subTest(score=s):
                self.assertEqual(self.post(entry(player=pid(s + 1), score=s))[0], 200)
        for s in [-1, 11001, 10 ** 9, 12.5, "100", True, None]:
            with self.subTest(score=s):
                self.assertRejected(entry(score=s), "分数")
        # 周榜是战役的累计分：打到第几关最多就是几关的分
        w = dict(entry(), board="weekly", period=WEEK)
        self.assertEqual(self.post(dict(w, player=pid(7), stage=3, score=33000))[0], 200)
        self.assertRejected(dict(w, player=pid(8), stage=3, score=33001), "分数")
        self.assertEqual(self.post(dict(w, player=pid(9), stage=8, score=88000))[0], 200)

    def test_R19_secs_range(self):
        for s in [20, 3600]:
            with self.subTest(secs=s):
                self.assertEqual(self.post(entry(player=pid(s), secs=s))[0], 200)
        for s in [0, 19, 3601, 30.5, "60", None]:
            with self.subTest(secs=s):
                self.assertRejected(entry(secs=s), "用时")

    def test_R20_stage_daily_is_10_weekly_is_campaign(self):
        for s in [0, 1, 9, 11, -1, "10", 10.0, None]:   # 每日挑战的关卡编号只能是 10
            with self.subTest(stage=s):
                self.assertRejected(entry(stage=s), "关卡")
        for s in [1, 8]:   # 周榜：战役打到第几关
            with self.subTest(stage=s):
                self.assertEqual(self.post(entry(player=pid(s), board="weekly", period=WEEK, stage=s, score=100))[0], 200)
        for s in [0, 9, 10, "3", None]:
            with self.subTest(stage=s):
                self.assertRejected(entry(board="weekly", period=WEEK, stage=s), "关卡")

    def test_R21_chips_and_level(self):
        ok = [([], 1), (["float"], 2), (["pierce", "bounce", "stealth"], 4), (["double", "engine"], 3)]
        for i, (chips, level) in enumerate(ok):
            with self.subTest(chips=chips):
                self.assertEqual(self.post(entry(player=pid(i + 1), chips=chips, level=level))[0], 200)
        self.assertRejected(entry(chips=["rapid", "shield", "magnet", "float"], level=5), "最多")
        self.assertRejected(entry(chips="rapid", level=2), "最多")
        self.assertRejected(entry(chips=None, level=1), "最多")
        self.assertRejected(entry(chips=["laser"], level=2), "不认识")
        self.assertRejected(entry(chips=["Rapid"], level=2), "不认识")
        self.assertRejected(entry(chips=[1], level=2), "不认识")
        self.assertRejected(entry(chips=["rapid", "rapid"], level=3), "重复")
        for chips, level in [([], 2), (["rapid"], 1), (["rapid"], 3), ([], 0), (["rapid", "shield"], 5),
                             ([], "1"), ([], True), ([], None)]:
            with self.subTest(chips=chips, level=level):
                self.assertRejected(entry(chips=chips, level=level), "等级")

    def test_R22_version(self):
        self.assertEqual(self.post(entry(version="v" * 16))[0], 200)
        for v in ["", "v" * 17, 6, None]:
            with self.subTest(version=v):
                self.assertRejected(entry(version=v), "版本")
        b = entry()
        del b["version"]
        self.assertRejected(b, "版本")

    def test_R23_malformed_body(self):
        for raw in [b"", b"{", b"not json", b"\xff\xfe", b'{"player":}']:
            with self.subTest(raw=raw):
                self.assertRejected(raw, "JSON")
        for body in [b"[]", b'"x"', b"1", b"null"]:
            with self.subTest(body=body):
                self.assertRejected(body, "JSON 对象")
        # 4 KB 以内可以（用超长的未知字段把请求体凑大），超过就拒
        b = entry(pad="")
        size = len(json.dumps(b).encode())
        self.assertEqual(self.post(entry(pad="x" * (4096 - size)))[0], 200)
        self.assertRejected(entry(player=pid(2), pad="x" * (4097 - size)), "4096")
        # 服务还活着
        self.assertEqual(self.get("/v1/health")[0], 200)

    def test_R24_rate_limit_per_player(self):
        for i in range(10):
            self.assertEqual(self.post(entry(score=i))[0], 200, f"第 {i + 1} 次应该放行")
        code, data = self.post(entry(score=999))
        self.assertEqual(code, 429)
        self.assertFalse(data["ok"])
        self.assertIn("频繁", data["error"])
        self.assertEqual(self.board()[1]["rows"][0]["score"], 9, "被限频的成绩不能写进去")
        # 别的玩家不受影响
        self.assertEqual(self.post(entry(player=pid(2)))[0], 200)
        # 非法成绩也算次数（防止拿乱数据刷）
        for _ in range(10):
            self.assertEqual(self.post(entry(player=pid(3), score=-1))[0], 400)
        self.assertEqual(self.post(entry(player=pid(3)))[0], 429)
        # 窗口过去后恢复
        self.clock.t += 61
        self.assertEqual(self.post(entry(score=999))[0], 200)
        self.assertEqual(self.rank(pid(1))[1]["score"], 999)

    def test_R25_rate_limit_per_ip(self):
        for i in range(30):
            self.assertEqual(self.post(entry(player=pid(i + 1)))[0], 200, f"第 {i + 1} 次应该放行")
        code, data = self.post(entry(player=pid(100)))
        self.assertEqual(code, 429)
        self.assertFalse(data["ok"])
        # 坏请求也算 IP 次数
        self.assertEqual(self.post(b"{")[0], 429)
        # 默认不信任 X-Forwarded-For，伪造也没用
        self.assertEqual(self.post(entry(player=pid(101)), {"X-Forwarded-For": "10.0.0.9"})[0], 429)
        self.assertEqual(self.board()[1]["total"], 30)
        self.clock.t += 61
        self.assertEqual(self.post(entry(player=pid(100)))[0], 200)

    def test_R26_regions_are_separate(self):
        self.post(entry(player=pid(1), region="cn", score=5000))
        self.post(entry(player=pid(2), region="global", score=100))
        code, data = self.post(entry(player=pid(1), region="global", score=50))
        self.assertEqual(data, {"ok": True, "rank": 2, "total": 2, "best": 50}, "国内的高分不能带到海外榜")
        cn = self.board(region="cn")[1]
        self.assertEqual((cn["total"], [r["player"] for r in cn["rows"]]), (1, [pid(1)]))
        self.assertEqual(cn["rows"][0]["score"], 5000)
        gl = self.board(region="global")[1]
        self.assertEqual([(r["player"], r["score"]) for r in gl["rows"]], [(pid(2), 100), (pid(1), 50)])
        self.assertEqual(self.rank(pid(2), region="cn")[1], {"ok": True, "rank": 0, "total": 1, "score": 0})
        self.assertEqual(self.rank(pid(1), region="cn")[1], {"ok": True, "rank": 1, "total": 1, "score": 5000})

    def test_R27_board_query(self):
        for i in range(60):
            self.srv.store.submit(entry(player=pid(i + 1), score=i * 10), T0)
        code, data = self.board()
        self.assertEqual(code, 200)
        self.assertEqual(data["total"], 60)
        self.assertEqual(len(data["rows"]), 10, "默认 10 条")
        self.assertEqual([r["score"] for r in data["rows"]], [590 - 10 * i for i in range(10)])
        self.assertEqual([r["rank"] for r in data["rows"]], list(range(1, 11)))
        self.assertEqual(len(self.board(limit=50)[1]["rows"]), 50)
        self.assertEqual(len(self.board(limit=1)[1]["rows"]), 1)
        # 没人上传过的期：空榜
        self.assertEqual(self.board(period=DAY - 100)[1], {"ok": True, "total": 0, "rows": []})
        bad = ["/v1/board", "/v1/board?board=daily&period=1", "/v1/board?region=global&period=1",
               "/v1/board?region=global&board=daily", "/v1/board?region=moon&board=daily&period=1",
               "/v1/board?region=global&board=hourly&period=1", "/v1/board?region=global&board=daily&period=x",
               "/v1/board?region=global&board=daily&period=-1"]
        bad += [f"/v1/board?region=global&board=daily&period={DAY}&limit={v}" for v in ["0", "51", "abc", "-1", "1000"]]
        for path in bad:
            with self.subTest(path=path):
                code, data = self.get(path)
                self.assertEqual(code, 400)
                self.assertFalse(data["ok"])

    def test_R28_rank_query(self):
        self.assertEqual(self.rank(pid(1)), (200, {"ok": True, "rank": 0, "total": 0, "score": 0}))
        self.post(entry(player=pid(1), score=300))
        self.post(entry(player=pid(2), score=700))
        self.post(entry(player=pid(3), score=500))
        self.assertEqual(self.rank(pid(1))[1], {"ok": True, "rank": 3, "total": 3, "score": 300})
        self.assertEqual(self.rank(pid(2))[1], {"ok": True, "rank": 1, "total": 3, "score": 700})
        self.assertEqual(self.rank(pid(9))[1], {"ok": True, "rank": 0, "total": 3, "score": 0})
        for path in ["/v1/rank?region=global&board=daily&period=1",
                     "/v1/rank?region=global&board=daily&period=1&player=ABCDEF0123456789",
                     "/v1/rank?region=global&board=daily&player=" + pid(1),
                     "/v1/rank?region=xx&board=daily&period=1&player=" + pid(1),
                     "/v1/rank?region=global&board=xx&period=1&player=" + pid(1)]:
            with self.subTest(path=path):
                self.assertEqual(self.get(path)[0], 400)

    def test_R29_data_survives_restart(self):
        self.post(entry(player=pid(1), score=900))
        self.post(entry(player=pid(2), score=400, region="cn"))
        self.stop()
        self.start()
        self.assertEqual(self.rank(pid(1))[1], {"ok": True, "rank": 1, "total": 1, "score": 900})
        self.assertEqual(self.rank(pid(2), region="cn")[1]["score"], 400)
        # 重启后同分的先后顺序也保留
        self.post(entry(player=pid(3), score=900))
        self.assertEqual([r["player"] for r in self.board()[1]["rows"]], [pid(1), pid(3)])
        # 库里不存 IP 等个人信息：只有随机玩家 ID 和成绩
        cols = [r[1] for r in self.srv.store.db.execute("PRAGMA table_info(scores)")]
        self.assertEqual(cols, ["region", "board", "period", "player", "score", "secs", "stage",
                                "chips", "level", "version", "at", "seq"])


class BehindProxy(Base):
    trust_proxy = True

    def test_R25_rate_limit_uses_forwarded_ip_behind_proxy(self):
        for i in range(30):
            self.assertEqual(self.post(entry(player=pid(i + 1)), {"X-Forwarded-For": "1.1.1.1, 10.0.0.1"})[0], 200)
        self.assertEqual(self.post(entry(player=pid(31)), {"X-Forwarded-For": "1.1.1.1"})[0], 429)
        # 另一个真实 IP 不受影响
        self.assertEqual(self.post(entry(player=pid(32)), {"X-Forwarded-For": "2.2.2.2"})[0], 200)


class Cli(unittest.TestCase):
    def test_R10_cli_starts_and_answers(self):
        import subprocess
        import time
        import urllib.request
        tmp = tempfile.mkdtemp()
        try:
            srv = lb.make_server("127.0.0.1", 0, os.path.join(tmp, "probe.sqlite"), quiet=True)
            port = srv.server_address[1]
            srv.server_close()
            p = subprocess.Popen([sys.executable, os.path.join(ROOT, "server", "leaderboard.py"),
                                  "--host", "127.0.0.1", "--port", str(port), "--db", os.path.join(tmp, "lb.sqlite")],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            try:
                self.assertIn("已启动", p.stdout.readline())
                for _ in range(50):
                    try:
                        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/health", timeout=2) as r:
                            got = json.loads(r.read())
                            self.assertEqual((got["ok"], got["version"]), (True, "1"))
                            self.assertEqual(got["day"], lb.day_of(time.time()))
                        break
                    except OSError:
                        time.sleep(0.1)
                else:
                    self.fail("命令行启动的服务没有响应")
                self.assertTrue(os.path.exists(os.path.join(tmp, "lb.sqlite")))
            finally:
                p.terminate()
                p.wait(5)
                p.stdout.close()
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
