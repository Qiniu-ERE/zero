"""R31~R33：排行榜服务的部署文件（server/deploy/）、部署后的冒烟检查、本机模拟上线（见 server/README.md 的“部署”一节）

不需要 Docker：只检查部署文件里的参数和服务端对得上，冒烟检查脚本对本机临时起的服务跑一遍。
"""
import contextlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DEPLOY = os.path.join(ROOT, "server", "deploy")
sys.path.insert(0, os.path.join(ROOT, "server"))
import leaderboard as lb  # noqa: E402


def read(name):
    with open(os.path.join(DEPLOY, name), encoding="utf-8") as f:
        return f.read()


def parse_args(argv):
    """用服务端自己的参数解析检查一条启动命令（参数不对会 SystemExit）"""
    seen = {}
    real = lb.make_server
    lb.make_server = lambda host, port, db, trust_proxy=False: seen.update(host=host, port=port, db=db, trust=trust_proxy) or _Stub()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            lb.main(argv)
    finally:
        lb.make_server = real
    return seen


class _Stub:
    server_address = ("", 0)

    def serve_forever(self):
        pass

    def server_close(self):
        pass


class DeployFiles(unittest.TestCase):
    def test_R31_dockerfile_cmd(self):
        """R31 Dockerfile：复制 leaderboard.py，启动参数服务端都认识，监听 0.0.0.0，数据在卷 /data 里，SIGINT 正常关闭"""
        src = read("Dockerfile")
        self.assertIn("COPY leaderboard.py", src)
        cmd = re.search(r"^CMD (\[.*\])$", src, re.M)
        argv = json.loads(cmd.group(1))
        self.assertEqual(argv[:2], ["python3", "leaderboard.py"])
        seen = parse_args(argv[2:])
        self.assertEqual((seen["host"], seen["port"], seen["trust"]), ("0.0.0.0", 8787, True))
        self.assertTrue(seen["db"].startswith("/data/"))
        self.assertIn("VOLUME /data", src)
        self.assertIn("EXPOSE 8787", src)
        self.assertIn("STOPSIGNAL SIGINT", src)
        self.assertIn("USER lb", src)

    def test_R31_systemd_unit(self):
        """R31 systemd：只监听本机（前面接 HTTPS 反向代理），数据在 StateDirectory 里"""
        src = read("tankbattle-lb.service")
        line = re.search(r"^ExecStart=(.*)$", src, re.M).group(1)
        argv = shlex.split(line)
        self.assertTrue(argv[1].endswith("/leaderboard.py"))
        seen = parse_args(argv[2:])
        self.assertEqual((seen["host"], seen["trust"]), ("127.0.0.1", True))
        state = re.search(r"^StateDirectory=(.*)$", src, re.M).group(1)
        self.assertEqual(os.path.dirname(seen["db"]), "/var/lib/" + state)
        self.assertIn("KillSignal=SIGINT", src)

    def test_R31_compose_and_caddy(self):
        """R31 compose + Caddy：Caddy 反向代理到 lb 服务的 8787 端口，域名来自 LB_DOMAIN，请求体有上限"""
        compose = read("compose.yml")
        caddy = read("Caddyfile")
        self.assertIn("dockerfile: deploy/Dockerfile", compose)
        self.assertIn("context: ..", compose)
        self.assertRegex(compose, r"(?m)^  lb:$")
        self.assertIn('"8787"', compose)
        self.assertIn("LB_DOMAIN: ${LB_DOMAIN:?", compose)
        self.assertIn("{$LB_DOMAIN} {", caddy)
        self.assertIn("reverse_proxy lb:8787", caddy)
        limit = int(re.search(r"max_size (\d+)KB", caddy).group(1))
        self.assertGreaterEqual(limit * 1024, lb.MAX_BODY)


class LocalServer(unittest.TestCase):
    """每个用例在本机临时起一个排行榜服务"""

    def setUp(self):
        if not shutil.which("curl"):
            self.skipTest("没有 curl")
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.srv = lb.make_server("127.0.0.1", 0, os.path.join(self.tmp, "lb.sqlite"), quiet=True)
        th = threading.Thread(target=self.srv.serve_forever, args=(0.05,), daemon=True)
        th.start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"


class Smoke(LocalServer):
    """R32 冒烟检查：对本机临时起的服务跑 smoke.sh"""

    def smoke(self, *args):
        return subprocess.run(["sh", os.path.join(DEPLOY, "smoke.sh"), *args], capture_output=True, text=True, timeout=60)

    def test_R32_smoke_passes(self):
        for region in ("global", "cn"):
            with self.subTest(region=region):
                out = self.smoke(self.url + "/", region)
                self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
                self.assertIn("冒烟检查通过", out.stdout)

    def test_R32_smoke_fails(self):
        out = self.smoke(self.url, "eu")             # 服务端不认识的区域：上传被拒
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("上传失败", out.stderr)
        out = self.smoke(self.url + "/nope")         # 路径不对：健康检查 404
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("GET /v1/health 失败", out.stderr)
        out = self.smoke()
        self.assertNotEqual(out.returncode, 0)


class LocalSim(LocalServer):
    """R33 本机模拟上线（local.sh）：只开在本机的端口，模拟玩家合法、编号各不相同，游戏副本连本机服务"""

    def local(self, *args, **env):
        e = dict(os.environ, LB_LOCAL=self.url, TMPDIR=self.tmp, **env)
        return subprocess.run(["sh", os.path.join(DEPLOY, "local.sh"), *args], capture_output=True, text=True, timeout=60, env=e)

    def test_R33_compose_local_only_binds_localhost(self):
        src = read("compose.local.yml")
        self.assertIn('"127.0.0.1:8787:8787"', src)
        self.assertNotRegex(src, r'"(0\.0\.0\.0:)?8787:8787"')

    def test_R33_seed(self):
        out = self.local("seed")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("10 个模拟玩家", out.stdout)
        day, week = lb.day_of(time.time()), lb.week_of(time.time())
        for board, period in (("daily", day), ("weekly", week)):
            with self.subTest(board=board):
                with urllib.request.urlopen(f"{self.url}/v1/board?region=global&board={board}&period={period}&limit=50") as r:
                    rows = json.load(r)["rows"]
                self.assertEqual(len(rows), 10)
                self.assertEqual(len({row["tag"] for row in rows}), 10)          # 游戏里显示的编号各不相同
                self.assertTrue(all(row["player"][4:8] == "5eed" for row in rows))
                self.assertEqual([row["score"] for row in rows], sorted((row["score"] for row in rows), reverse=True))
        out = self.local("seed")                                             # 60 秒内再填：同一 IP 被限频
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("上传失败", out.stderr)

    def test_R33_status_and_errors(self):
        out = self.local("status")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn('"ok": true', out.stdout)
        out = self.local()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("用法", out.stdout)
        bad = dict(LB_LOCAL="http://127.0.0.1:9")
        e = dict(os.environ, TMPDIR=self.tmp, **bad)
        out = subprocess.run(["sh", os.path.join(DEPLOY, "local.sh"), "seed"], capture_output=True, text=True, timeout=60, env=e)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("连不上", out.stderr)

    def test_R33_game_copy_points_at_local_server(self):
        out = self.local("game", LB_GAME_DRY="1")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        with open(os.path.join(self.tmp, "tankbattle-lb-local", "game", "main.spx"), encoding="utf-8") as f:
            main = f.read()
        self.assertIn(f'lbURL       = "{self.url}"', main)
        with open(os.path.join(ROOT, "TankBattle", "main.spx"), encoding="utf-8") as f:
            self.assertIn('lbURL       = ""', f.read())                   # 仓库里的游戏不改


if __name__ == "__main__":
    unittest.main()
