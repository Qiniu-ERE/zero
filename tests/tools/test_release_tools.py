"""打包和发布工具的测试：patch_spx.py（版本号换算、缺选项时失败）、env.sh（从 CHANGELOG 取版本号）、
release_local.sh（DRY_RUN 生成的发布说明和校验和、发布前的检查）。都用临时目录里的小样本，不联网、不打包。"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EXPORT = os.path.join(ROOT, "tools", "export")
sys.path.insert(0, EXPORT)
import patch_spx  # noqa: E402

BASH = shutil.which("bash")
need_bash = unittest.skipUnless(BASH and os.name != "nt", "需要 bash（macOS / Linux）")

# 一份最小的 export_presets.cfg：三个 preset，patch_spx.py 要改的选项都在
PRESETS = """[preset.0]

name="Android"
platform="Android"

[preset.0.options]

version/code=1
version/name="1.0"
package/unique_name="org.godotengine.$genname"
package/name=""
launcher_icons/main_192x192=""
launcher_icons/adaptive_foreground_432x432=""

[preset.1]

name="iOS"
platform="iOS"

[preset.1.options]

application/app_store_team_id=""
application/bundle_identifier=""
application/short_version="1.0"
application/version="1.0"
application/export_project_only=false

[preset.2]

name="Mac"
platform="macOS"

[preset.2.options]

application/bundle_identifier=""
application/short_version="1.0"
application/version="1.0"
"""


class PatchSpxVersion(unittest.TestCase):
    def test_version_numbers(self):
        cases = {
            "4.0.1": ("4.0.1", 40001),
            "3.0.0-dev.12": ("3.0.0", 30000),
            "4.0.1-rc.1": ("4.0.1", 40001),
            "5.12.3": ("5.12.3", 51203),
            "4": ("4.0.0", 40000),
            "4.1": ("4.1.0", 40100),
        }
        for v, want in cases.items():
            with self.subTest(version=v):
                self.assertEqual(patch_spx.version_numbers(v), want)

    def test_bad_versions_fail(self):
        for v in ("", "v4.0.1", "abc", "4.0.1x", "4.100.0", "4.0.100", None):
            with self.subTest(version=v), self.assertRaises(ValueError):
                patch_spx.version_numbers(v)

    def test_version_info_cli(self):
        out = subprocess.run([sys.executable, os.path.join(EXPORT, "patch_spx.py"), "--version-info", "4.0.1-rc.1"],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "4.0.1 40001")
        bad = subprocess.run([sys.executable, os.path.join(EXPORT, "patch_spx.py"), "--version-info", ""],
                             capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)


class PatchSpxPresets(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.cfg = os.path.join(self.dir, "export_presets.cfg")

    def write(self, text):
        with open(self.cfg, "w", encoding="utf-8") as f:
            f.write(text)

    def read(self):
        with open(self.cfg, encoding="utf-8") as f:
            return f.read()

    def test_patches_all_presets(self):
        self.write(PRESETS)
        patch_spx.patch_presets(self.cfg, patch_spx.options("com.x.tank", '坦克 "2026"', "4.0.1-rc.1"))
        s = self.read()
        self.assertIn("version/code=40001\n", s)
        self.assertIn('version/name="4.0.1-rc.1"\n', s)
        self.assertIn('package/unique_name="com.x.tank"\n', s)
        self.assertIn('package/name="坦克 \\"2026\\""\n', s)          # 引号要转义
        self.assertIn("application/export_project_only=true\n", s)     # true / false 不加引号
        self.assertEqual(s.count('application/short_version="4.0.1"'), 2)  # iOS 和 Mac 都只用纯数字部分
        self.assertEqual(s.count('application/version="4.0.1"'), 2)

    def test_missing_option_fails(self):
        self.write(PRESETS.replace('version/name="1.0"\n', ""))
        with self.assertRaises(SystemExit) as e:
            patch_spx.patch_presets(self.cfg, patch_spx.options("com.x", "t", "4.0.1"))
        self.assertIn("Android: version/name", str(e.exception.code))

    def test_option_only_in_one_of_ios_and_mac_fails(self):
        # Mac 没有 short_version、iOS 有：以前只按选项名检查，会漏掉
        mac = PRESETS.index("[preset.2.options]")
        self.write(PRESETS[:mac] + PRESETS[mac:].replace('application/short_version="1.0"\n', ""))
        with self.assertRaises(SystemExit) as e:
            patch_spx.patch_presets(self.cfg, patch_spx.options("com.x", "t", "4.0.1"))
        self.assertIn("Mac: application/short_version", str(e.exception.code))

    def test_cli_patches_template(self):
        """命令行：图标、export_presets.cfg、project.godot 都改到；缺参数时失败"""
        tpl = os.path.join(self.dir, "spx", "cmd", "spx", "template", "project")
        os.makedirs(os.path.join(tpl, "engine", "icons"))
        with open(os.path.join(tpl, "export_presets.cfg"), "w", encoding="utf-8") as f:
            f.write(PRESETS)
        with open(os.path.join(tpl, "project.godot"), "w", encoding="utf-8") as f:
            f.write('[application]\n\nconfig/name="x"\n')
        script = os.path.join(EXPORT, "patch_spx.py")
        out = subprocess.run([sys.executable, script, os.path.join(self.dir, "spx"), "com.x", "坦克", "4.2.3"],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("versionCode 40203", out.stdout)
        self.assertTrue(os.path.isfile(os.path.join(tpl, "engine", "icons", "logo.png")))
        with open(os.path.join(tpl, "project.godot"), encoding="utf-8") as f:
            self.assertIn('config/icon="res://engine/icons/logo.png"', f.read())
        self.assertNotEqual(subprocess.run([sys.executable, script, self.dir, "com.x"], capture_output=True).returncode, 0)

    def test_option_in_other_section_is_not_patched(self):
        # [preset.0] 里（不是 options 段）的同名行不能改
        self.write(PRESETS.replace('platform="Android"\n', 'platform="Android"\nversion/code=7\n', 1))
        patch_spx.patch_presets(self.cfg, patch_spx.options("com.x", "t", "4.0.1"))
        self.assertIn("version/code=7\n", self.read())


@need_bash
class EnvVersion(unittest.TestCase):
    """env.sh 从 CHANGELOG.md 取默认版本号"""

    def version(self, changelog, env_version=None):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        os.makedirs(os.path.join(d, "tools", "export"))
        shutil.copy(os.path.join(EXPORT, "env.sh"), os.path.join(d, "tools", "export", "env.sh"))
        with open(os.path.join(d, "CHANGELOG.md"), "w", encoding="utf-8") as f:
            f.write(changelog)
        env = {k: v for k, v in os.environ.items() if k != "APP_VERSION"}
        if env_version:
            env["APP_VERSION"] = env_version
        out = subprocess.run([BASH, "-c", 'source "$1/tools/export/env.sh" 2>/dev/null; printf %s "$APP_VERSION"', "-", d],
                             capture_output=True, text=True, env=env)
        return out.stdout

    def test_plain(self):
        self.assertEqual(self.version("# 更新记录\n\n## v4.0.1\n\n- x\n\n## v4.0.0\n"), "4.0.1")

    def test_prerelease(self):
        self.assertEqual(self.version("## v4.0.1-rc.1\n\n## v4.0.0\n"), "4.0.1-rc.1")

    def test_heading_with_text(self):
        self.assertEqual(self.version("## v5.0.0（2026-11-01）\n"), "5.0.0")
        self.assertEqual(self.version("## v5.0.0 正式版\n"), "5.0.0")

    def test_first_section_wins(self):
        self.assertEqual(self.version("说明\n### v9.9.9 不是二级标题\n## v3.0.2\n## v3.0.1\n"), "3.0.2")

    def test_env_overrides(self):
        self.assertEqual(self.version("## v4.0.1\n", env_version="4.0.2-dev.3"), "4.0.2-dev.3")

    def test_real_changelog_not_empty(self):
        with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
            self.assertRegex(self.version(f.read()), r"^\d+\.\d+")


@need_bash
class ReleaseNotes(unittest.TestCase):
    """release_local.sh 的 DRY_RUN：缺的平台指向以前的版本、校验和、发布前检查（用 RELEASE_ASSETS_FILE 代替 gh）"""

    V = "4.0.1"

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.dist = os.path.join(self.dir, "dist")
        os.makedirs(self.dist)

    def put(self, name, text="x"):
        with open(os.path.join(self.dist, name), "w") as f:
            f.write(text)

    def assets(self, lines, name="assets.txt"):
        p = os.path.join(self.dir, name)
        with open(p, "w") as f:
            f.write("\n".join(lines) + "\n")
        return p

    def run_release(self, assets, *args, **env_extra):
        env = dict(os.environ, DRY_RUN="1", APP_VERSION=self.V, DIST_DIR=self.dist, RELEASE_ASSETS_FILE=assets,
                   REPO="owner/repo", SKIP_BUILD_CHECK="1", TMPDIR=self.dir)
        env.update(env_extra)
        return subprocess.run([BASH, os.path.join(EXPORT, "release_local.sh"), *args],
                              capture_output=True, text=True, env=env, cwd=ROOT)

    def notes(self, out):
        return out.stdout.split("---- 发布说明", 1)[1]

    def test_missing_platforms_link_to_latest_older_version(self):
        for s in ("macos-arm64.zip", "web.zip", "android.apk"):
            self.put(f"TankBattle-{self.V}-{s}")
        self.put(f"TankBattle-{self.V}-rc.1-linux-x64.tar.gz")  # 预发布的包不能当成 4.0.1 的
        a = self.assets([
            "v3.0.2 TankBattle-3.0.2-web.zip",
            "v3.0.10 TankBattle-3.0.10-ios-unsigned.ipa",   # 按版本号 3.0.10 比 3.0.2 新（按创建时间排会错）
            "v3.0.1 TankBattle-3.0.1-ios-unsigned.ipa",
            "v3.0.1 TankBattle-3.0.1-windows-x64.zip",
            "v5.0.0 TankBattle-5.0.0-linux-x64.tar.gz",       # 比本版新的不用
            "v4.0.0 TankBattle-4.0.0-linux-x64.tar.gz",
        ])
        out = self.run_release(a)
        self.assertEqual(out.returncode, 0, out.stderr)
        n = self.notes(out)
        base = "https://github.com/owner/repo/releases/download"
        self.assertIn(f"[`TankBattle-3.0.1-windows-x64.zip`]({base}/v3.0.1/TankBattle-3.0.1-windows-x64.zip)（本版没有打包，沿用 v3.0.1）", n)
        self.assertIn(f"{base}/v3.0.10/TankBattle-3.0.10-ios-unsigned.ipa", n)
        self.assertIn(f"{base}/v4.0.0/TankBattle-4.0.0-linux-x64.tar.gz", n)
        self.assertNotIn("v5.0.0", n)
        for s in ("macos-arm64.zip", "web.zip", "android.apk"):
            self.assertIn(f"`TankBattle-{self.V}-{s}`", n)
        self.assertNotIn("@VERSION@", n)
        self.assertIn(f"## 坦克大战 2026 v{self.V}", n)
        sums = out.stdout.split("---- SHA256SUMS.txt", 1)[1].split("---- 发布说明", 1)[0]
        self.assertEqual(len(sums.strip().splitlines()), 3)
        self.assertNotIn("rc.1", sums)

    def test_platform_never_released(self):
        self.put(f"TankBattle-{self.V}-web.zip")
        out = self.run_release(self.assets(["v3.0.2 TankBattle-3.0.2-web.zip"]))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("| （本版没有打包） |", self.notes(out))

    def test_append_merges_checksums(self):
        self.put(f"TankBattle-{self.V}-windows-x64.zip", "new")
        self.put(f"TankBattle-{self.V}-macos-arm64.zip", "local copy")   # Release 里已经有了：跳过
        a = self.assets([f"v{self.V} TankBattle-{self.V}-macos-arm64.zip", f"v{self.V} SHA256SUMS.txt",
                         "v3.0.1 TankBattle-3.0.1-ios-unsigned.ipa"])
        old = os.path.join(self.dir, "old-sums.txt")
        with open(old, "w") as f:
            f.write(f"aaaa  TankBattle-{self.V}-macos-arm64.zip\n")
        out = self.run_release(a, "--append", RELEASE_SUMS_FILE=old)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn(f"要上传：TankBattle-{self.V}-windows-x64.zip SHA256SUMS.txt", out.stdout)
        self.assertIn("已经有了，跳过", out.stdout)
        sums = out.stdout.split("---- SHA256SUMS.txt", 1)[1].split("---- 发布说明", 1)[0].strip().splitlines()
        self.assertEqual(len(sums), 2)
        self.assertIn(f"aaaa  TankBattle-{self.V}-macos-arm64.zip", sums)   # 原有的那一行保留
        n = self.notes(out)
        self.assertIn(f"`TankBattle-{self.V}-windows-x64.zip`", n)
        self.assertIn(f"`TankBattle-{self.V}-macos-arm64.zip`", n)
        self.assertIn("v3.0.1/TankBattle-3.0.1-ios-unsigned.ipa", n)

    def test_append_needs_existing_release(self):
        self.put(f"TankBattle-{self.V}-web.zip")
        out = self.run_release(self.assets(["v3.0.2 TankBattle-3.0.2-web.zip"]), "--append")
        self.assertNotEqual(out.returncode, 0)

    def test_create_refuses_existing_release(self):
        self.put(f"TankBattle-{self.V}-web.zip")
        out = self.run_release(self.assets([f"v{self.V} TankBattle-{self.V}-web.zip"]), DRY_RUN="")
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("--append", out.stderr)

    def test_build_check(self):
        """BUILD_LOCAL.md：提交不等于标签、表里有 ❌、工作区不干净都要停（DRY_RUN 时只列出来）"""
        self.put(f"TankBattle-{self.V}-web.zip")
        a = self.assets(["v3.0.2 TankBattle-3.0.2-web.zip"])
        with open(os.path.join(self.dist, "BUILD_LOCAL.md"), "w") as f:
            f.write(f"| web | ✅ | TankBattle-{self.V}-web.zip | |\n| android | ❌ | — | 打包失败 |\n\n"
                    f"<!-- build_local version={self.V} commit=0000000000000000000000000000000000000000 dirty=1 -->\n")
        out = self.run_release(a, SKIP_BUILD_CHECK="")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("有失败的平台：android", out.stderr)
        self.assertIn("未提交的改动", out.stderr)
        tagged = subprocess.run(["git", "-C", ROOT, "rev-parse", "-q", "--verify", f"refs/tags/v{self.V}"],
                                capture_output=True).returncode == 0
        if tagged:  # 浅克隆里可能没有标签
            self.assertIn("打的，标签", out.stderr)


class PinnedVersions(unittest.TestCase):
    """env.sh 锁定的版本和 .github/workflows 里写的一致，sha256 格式正确"""

    def env_value(self, name):
        import re
        with open(os.path.join(EXPORT, "env.sh"), encoding="utf-8") as f:
            m = re.search(rf'^{name}="([^"]*)"', f.read(), re.M)
        self.assertIsNotNone(m, name)
        return m.group(1)

    def test_workflows_match_env(self):
        import re
        go, xgo = self.env_value("GO_VERSION"), self.env_value("XGO_VERSION")
        wf = os.path.join(ROOT, ".github", "workflows")
        for name in ("release.yml", "test.yml"):
            with open(os.path.join(wf, name), encoding="utf-8") as f:
                text = f.read()
            with self.subTest(workflow=name):
                self.assertEqual(re.search(r"GO_VERSION: '([^']*)'", text).group(1), go)
                self.assertEqual(re.search(r"XGO_VERSION: '([^']*)'", text).group(1), xgo)

    def test_sha256_format(self):
        for name in ("MOLTENVK_SHA256", "GO_LINUX_AMD64_SHA256"):
            with self.subTest(name=name):
                self.assertRegex(self.env_value(name), r"^[0-9a-f]{64}$")


@need_bash
class BuildArgs(unittest.TestCase):
    """build.sh 的参数（只测解析和检查，不真的打包）、--store / --demo 改常量、spx 源码补丁的校验和"""

    def build(self, *args, **env_extra):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        env = dict(os.environ, BUILD_DIR=os.path.join(d, "work"), DIST_DIR=os.path.join(d, "dist"),
                   CACHE_DIR=os.path.join(d, "cache"), TMPDIR=d)
        env.update(env_extra)
        return subprocess.run([BASH, os.path.join(EXPORT, "build.sh"), *args], capture_output=True, text=True, env=env)

    def test_bad_arguments(self):
        for args, words in [((), "用法"), (("desktop", "web"), "只能打一个平台"), (("desktop", "--bogus"), "不认识的选项"),
                            (("phone",), "未知平台")]:
            with self.subTest(args=args):
                out = self.build(*args)
                self.assertNotEqual(out.returncode, 0)
                self.assertIn(words, out.stderr)

    def flags(self, main_spx, store, demo):
        """把 build.sh 里的 enable_flag / build_flags 拿出来，对一份临时的 main.spx 运行"""
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        with open(os.path.join(d, "main.spx"), "w", encoding="utf-8") as f:
            f.write(main_spx)
        script = (
            'eval "$(awk \'/^enable_flag\\(\\) \\{/,/^\\}/\' "$1")"\n'
            'eval "$(awk \'/^build_flags\\(\\) \\{/,/^\\}/\' "$1")"\n'
            'set -euo pipefail; G="$2"; STORE_BUILD="$3"; DEMO_BUILD="$4"; build_flags\n')
        out = subprocess.run([BASH, "-c", script, "-", os.path.join(EXPORT, "build.sh"), d, store, demo],
                             capture_output=True, text=True)
        with open(os.path.join(d, "main.spx"), encoding="utf-8") as f:
            return out, f.read()

    def test_store_flag(self):
        src = "const (\n\ttouchUI    = false\n\tstoreBuild = false // 商店版\n\tdemoBuild  = false\n)\n\nfunc f() {\n\tif storeBuild == false {\n\t}\n}\n"
        out, main = self.flags(src, "1", "0")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("\tstoreBuild = true // 商店版\n", main)
        self.assertIn("\tdemoBuild  = false\n", main)
        self.assertIn("if storeBuild == false", main)     # 只改常量定义
        out, main = self.flags(src, "1", "1")
        self.assertIn("\tdemoBuild  = true\n", main)

    def test_store_flag_missing_fails_demo_only_warns(self):
        src = "const (\n\ttouchUI = false\n)\n"
        out, _ = self.flags(src, "1", "0")
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("storeBuild", out.stderr)
        out, main = self.flags(src, "0", "1")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("demoBuild", out.stderr)
        self.assertEqual(main, src)

    def test_patches_digest(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        shutil.copytree(EXPORT, os.path.join(d, "tools", "export"), ignore=shutil.ignore_patterns("web", "*.png"))
        patches = os.path.join(d, "tools", "export", "patches")
        spx = os.path.join(d, "spx")
        os.makedirs(os.path.join(spx, ".bin"))
        run = lambda: subprocess.run(  # noqa: E731
            [BASH, "-c", 'source "$1/tools/export/env.sh" 2>/dev/null; patches_digest; check_spx_patches && echo OK',
             "-", d], capture_output=True, text=True, env=dict(os.environ, SPX_DIR=spx, TMPDIR=d))
        out = run()
        self.assertEqual(out.stdout.split(), ["none", "OK"])   # 没有补丁、也没有记录：一致
        with open(os.path.join(patches, "0001-x.patch"), "w") as f:
            f.write("--- a/x\n+++ b/x\n")
        out = run()
        digest = out.stdout.split()[0]
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertNotIn("OK", out.stdout)                    # 补丁加了、spx 没重装
        self.assertIn("setup_spx.sh", out.stderr)
        with open(os.path.join(spx, ".bin", "tankbattle-patches.txt"), "w") as f:
            f.write(digest + "\n")
        self.assertEqual(run().stdout.split(), [digest, "OK"])


if __name__ == "__main__":
    unittest.main()
