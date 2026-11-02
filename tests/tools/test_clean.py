"""Q09：tools/dev/clean.sh 只删能确定是没用的临时文件（见 docs/v6/TEST_PLAN.md）

在临时目录里放一份脚本（当成一个假的仓库，免得删到真仓库的 .build/work），TMPDIR 也指向临时目录。
"""
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


class Clean(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)
        self.repo = os.path.join(self.d, "repo")
        os.makedirs(os.path.join(self.repo, "tools", "dev"))
        os.makedirs(os.path.join(self.repo, ".build", "work"))
        shutil.copy(os.path.join(ROOT, "tools", "dev", "clean.sh"), os.path.join(self.repo, "tools", "dev"))
        self.tmp = os.path.join(self.d, "tmp")
        os.makedirs(self.tmp)
        rid = subprocess.run(["sh", "-c", 'printf "%s" "$1" | cksum | cut -d" " -f1', "-", self.repo],
                             capture_output=True, text=True).stdout.strip()
        self.dirs = {
            "mine": f"tankbattle-test-{rid}",            # 这个仓库的：删
            "other": "tankbattle-test-123456",           # 别的 clone 的：不删
            "distboot": "tankbattle-distboot-123456.ab",  # 别的 clone 的安装包启动测试：不删
            "lblocal": "tankbattle-lb-local",            # 本机模拟上线正在用：不删
            "old": "tankbattle-record",                  # 旧脚本留下的：--legacy 才删
        }
        for name in self.dirs.values():
            os.makedirs(os.path.join(self.tmp, name))

    def run_clean(self, *args):
        return subprocess.run(["sh", os.path.join(self.repo, "tools", "dev", "clean.sh"), *args],
                              capture_output=True, text=True, env=dict(os.environ, TMPDIR=self.tmp))

    def left(self):
        return {k for k, v in self.dirs.items() if os.path.exists(os.path.join(self.tmp, v))}

    def test_Q09_default_only_lists(self):
        out = self.run_clean()
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.left(), set(self.dirs))
        self.assertTrue(os.path.isdir(os.path.join(self.repo, ".build", "work")))

    def test_Q09_yes_legacy_keeps_other_clones_and_local_sim(self):
        out = self.run_clean("--yes", "--legacy")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.left(), {"other", "distboot", "lblocal"})
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".build", "work")))


if __name__ == "__main__":
    unittest.main()
