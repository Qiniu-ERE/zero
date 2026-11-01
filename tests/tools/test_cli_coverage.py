"""Q05~Q07：v6 工具的命令行入口和少见的分支（让 tools/test/py_coverage.py 的行覆盖率达到目标），见 docs/v6/TEST_PLAN.md

命令行入口都在进程里调用（子进程里执行的代码 trace 统计不到）。
"""
import _thread
import contextlib
import http.client
import io
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.request

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "levels"))
sys.path.insert(0, os.path.join(ROOT, "server"))

import check  # noqa: E402
import daily  # noqa: E402
import leaderboard as lb  # noqa: E402


def run_main(func, argv):
    """在进程里跑一个命令行入口，返回（退出码，输出）"""
    old = sys.argv
    sys.argv = argv
    out = io.StringIO()
    code = 0
    try:
        with contextlib.redirect_stdout(out):
            func()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    finally:
        sys.argv = old
    return code, out.getvalue()


class DailyCli(unittest.TestCase):
    def test_Q05_print_and_write(self):
        code, out = run_main(daily.main, ["daily.py", "20758"])
        self.assertEqual(code, 0)
        self.assertIn("每日挑战 #1", out)
        self.assertEqual(out.strip().splitlines()[1:], daily.daily_rows(20758))
        code, out = run_main(daily.main, ["daily.py"])
        self.assertIn(f"第 {daily.today()} 天", out)
        with tempfile.TemporaryDirectory() as d:
            old = daily.DATA
            daily.DATA = os.path.join(d, "maps.txt")
            try:
                daily.write_data.__defaults__ = (daily.DATA,)
                code, out = run_main(daily.main, ["daily.py", "--write"])
                with open(daily.DATA, encoding="utf-8") as f:
                    self.assertEqual(f.read().count("\n"), 1 + daily.DAYS * 14)
            finally:
                daily.DATA = old
                daily.write_data.__defaults__ = (old,)

    def test_Q05_map_problems_and_fallback(self):
        blank = [daily.locked_char(i) for i in range(daily.ROWS * daily.COLS)]
        self.assertEqual(daily.map_problem(blank), 0)
        walled = list(blank)
        for c in range(daily.COLS):
            walled[1 * daily.COLS + c] = "S"  # 第 1 行全是钢墙：敌人到不了基地
        self.assertEqual(daily.map_problem(walled), 1)
        boxed = list(blank)
        for i in (11 * daily.COLS + 4, 12 * daily.COLS + 3, 12 * daily.COLS + 5):
            boxed[i] = "S"  # 1P 出生点被钢墙围住（这张图没有锁定的护墙）：开不到敌人出生点
        self.assertEqual(daily.map_problem(boxed), 2)
        old = daily.map_problem
        daily.map_problem = lambda m: 1  # 80 次都不合格：用空白地图
        try:
            self.assertEqual("".join(daily.daily_rows(20800)), "".join(blank))
        finally:
            daily.map_problem = old


class CheckCli(unittest.TestCase):
    def test_Q06_main_with_file_and_default(self):
        with tempfile.TemporaryDirectory() as d:
            good = os.path.join(d, "good.txt")
            with open(good, "w", encoding="utf-8") as f:
                f.write("\n".join(daily.daily_rows(20758)) + "\n")
            code, out = run_main(check.main, ["check.py", good])
            self.assertEqual(code, 0)
            self.assertIn("✓", out)
            bad = os.path.join(d, "bad.txt")
            with open(bad, "w", encoding="utf-8") as f:
                f.write("....\n")
            code, out = run_main(check.main, ["check.py", bad])
            self.assertEqual(code, 1)
            self.assertIn("✗", out)
            empty = os.path.join(d, "main.spx")
            with open(empty, "w", encoding="utf-8") as f:
                f.write("// 没有 levelMap\n")
            with self.assertRaises(SystemExit):
                check.levels_from_spx(empty)
        code, out = run_main(check.main, ["check.py"])
        self.assertEqual(code, 0)
        self.assertEqual(out.count("✓"), 8)


class ServerCli(unittest.TestCase):
    def test_Q07_main_serves_until_interrupted(self):
        with tempfile.TemporaryDirectory() as d:
            srv = lb.make_server("127.0.0.1", 0, os.path.join(d, "probe.sqlite"), quiet=True)
            port = srv.server_address[1]
            srv.server_close()
            answered = []

            def poke():
                for _ in range(50):
                    try:
                        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/health", timeout=1) as r:
                            answered.append(json.loads(r.read())["ok"])
                        break
                    except OSError:
                        time.sleep(0.05)
                _thread.interrupt_main()  # 相当于按 Ctrl+C

            threading.Thread(target=poke, daemon=True).start()
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                lb.main(["--port", str(port), "--db", os.path.join(d, "lb.sqlite")])
            self.assertEqual(answered, [True])
            self.assertIn("已启动", out.getvalue())

    def test_Q07_rare_branches(self):
        limiter = lb.RateLimiter(2, window=10)
        self.assertTrue(limiter.allow("k", 0))
        self.assertTrue(limiter.allow("k", 1))
        self.assertFalse(limiter.allow("k", 2))
        self.assertTrue(limiter.allow("k", 10.5), "窗口过去以后，旧的记录要从队列里去掉")
        with tempfile.TemporaryDirectory() as d:
            srv = lb.make_server("127.0.0.1", 0, os.path.join(d, "lb.sqlite"), quiet=False)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            try:
                port = srv.server_address[1]
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    c = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                    c.putrequest("POST", "/v1/score")
                    c.putheader("Content-Length", "abc")  # 不是数字
                    c.endheaders()
                    r = c.getresponse()
                    self.assertEqual(r.status, 400)
                    r.read()
                    c.close()
                    time.sleep(0.1)
                self.assertIn("POST /v1/score", err.getvalue(), "quiet=False 时要打日志")
            finally:
                srv.shutdown()
                srv.server_close()


if __name__ == "__main__":
    unittest.main()
