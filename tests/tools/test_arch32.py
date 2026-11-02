"""Q11：游戏代码在 32 位设备上也能编译、算得一样（见 docs/v6/TEST_PLAN.md）

spx 打 Android 包时会编译 64 位（arm64-v8a）和 32 位（armeabi-v7a）两份库（APK 里只装 64 位那份），32 位上 Go 的 int 只有 32 位。
v6.0.1 的每日挑战随机数 lcg 写成 (s*1103515245 + 12345) % 2147483648：常量 2147483648 在 32 位上放不下，
Android 打包编译失败；就算能编译，乘法也会溢出（将来支持 32 位手机时，每日地图就会和别人不一样）。
依赖的 spx 离不开 cgo，本机做不了 32 位的类型检查，所以这里做静态检查，真正的把关是 Android 打包本身。
"""
import os
import re
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GAME = os.path.join(ROOT, "TankBattle")
INT32_MAX = 2**31 - 1
# 这些写法里的大数是 64 位的：int64(...) 里的运算、time.Duration（http.Client 的 Timeout）
SAFE = re.compile(r"int64\(|Timeout:")


def lcg(s):
    return (s * 1103515245 + 12345) % 2147483648


class Arch32(unittest.TestCase):
    def test_Q11_no_big_int_constants_outside_int64(self):
        bad = []
        for name in sorted(os.listdir(GAME)):
            if not name.endswith(".spx"):
                continue
            with open(os.path.join(GAME, name), encoding="utf-8") as f:
                for n, line in enumerate(f, 1):
                    code = line.split("//")[0]
                    for m in re.finditer(r"\b\d+\b", code):
                        if int(m.group()) > INT32_MAX and not SAFE.search(code):
                            bad.append(f"{name}:{n}: {m.group()}")
        self.assertEqual(bad, [], "超过 2^31-1 的整数常量要放在 int64 里算（32 位设备上 int 只有 32 位）")

    def test_Q11_lcg_computed_in_int64(self):
        with open(os.path.join(GAME, "main.spx"), encoding="utf-8") as f:
            src = f.read()
        body = re.search(r"func lcg\(s int\) int \{\n(.*?)\n\}", src, re.S).group(1)
        self.assertIn("int64(s)", body)
        # 结果小于 2^31，转回 32 位的 int 不会溢出；中间值小于 2^63
        for s in (0, 1, 7, 2**31 - 1, 650000 * 97 + 3):
            v = lcg(s)
            self.assertLess(v, 2**31)
            self.assertLess(s * 1103515245 + 12345, 2**63)


if __name__ == "__main__":
    unittest.main()
