#!/usr/bin/env python3
"""Python 工具的行覆盖率（v6，docs/v6/TEST_PLAN.md 第四节）。只用标准库的 trace 模块，不装第三方库。

用法：python3 tools/test/py_coverage.py            # 跑 tests/tools 里的全部测试，统计下面 TARGETS 里每个文件的行覆盖率
      python3 tools/test/py_coverage.py --check    # 再和目标比较：没达到就退出码 1（pr_check.sh --coverage 会调用）

做法：trace.Trace 记下每一行有没有执行（服务端在线程里处理请求，所以也给新线程装上跟踪）；
“可执行的行”用 trace 自带的分析（和 python -m trace --missing 一样）。命令行入口 main() 由测试在进程里调用。
"""
import os
import sys
import threading
import trace
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
# 文件 -> 行覆盖率目标（%）。v6 新增的工具要求 100%；旧工具 85%
TARGETS = {
    "tools/levels/daily.py": 100,
    "server/leaderboard.py": 100,
    "tools/levels/check.py": 85,
    "tools/assets/strings.py": 85,
}


def executable_lines(path):
    """可执行的行（标准库的 trace 就是这样算的），不算 if __name__ == "__main__": 下面的行（只在命令行直接运行时执行）"""
    lines = {n for n in trace._find_executable_linenos(path) if n}
    with open(path, encoding="utf-8") as f:
        src = f.read().splitlines()
    for i, line in enumerate(src, 1):
        if line.startswith('if __name__ == "__main__":'):
            lines -= set(range(i, len(src) + 1))
    return lines


def run():
    tracer = trace.Trace(count=1, trace=0)
    threading.settrace(tracer.globaltrace)
    sys.path.insert(0, os.path.join(ROOT, "tests", "tools"))
    def go():  # 找测试时会 import 被测的模块，模块顶层的代码也要算进去，所以找测试也在跟踪里做
        suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, "tests", "tools"))
        return unittest.TextTestRunner(stream=open(os.devnull, "w"), verbosity=0).run(suite)
    result = tracer.runfunc(go)
    threading.settrace(None)
    counts = tracer.results().counts
    hit = {}
    for (fn, line), n in counts.items():
        if n:
            hit.setdefault(os.path.realpath(fn), set()).add(line)
    rows = []
    for rel, want in TARGETS.items():
        path = os.path.realpath(os.path.join(ROOT, rel))
        lines = executable_lines(path)
        got = lines & hit.get(path, set())
        missing = sorted(lines - got)
        pct = 100.0 * len(got) / len(lines) if lines else 100.0
        rows.append((rel, pct, want, missing))
    return result, rows


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    result, rows = run()
    ok = result.wasSuccessful()
    print("| 文件 | 行覆盖率 | 目标 | 没覆盖到的行 |")
    print("|---|---|---|---|")
    for rel, pct, want, missing in rows:
        good = pct >= want
        ok = ok and good
        shown = ", ".join(map(str, missing[:20])) + (" …" if len(missing) > 20 else "")
        print(f"| {rel} | {pct:.0f}% | ≥ {want}% {'✅' if good else '❌'} | {shown or '—'} |")
    if not result.wasSuccessful():
        print("❌ 有构建工具测试失败")
    if "--check" in argv and not ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
