#!/usr/bin/env python3
"""引擎内测试的覆盖率（见 docs/v4/TEST_PLAN.md 第四节）。spx 没有现成的覆盖率工具，这里自己插桩。

  spx_coverage.py instrument <工程副本目录>
      给副本里每个 .spx 的每个 func、每个事件处理的第一行插入 tCov("<文件>:<名字>")。
      tCov 在 main.spx 里，同一个名字只打印一次 "COV <名字>"（热点函数每帧都调用，不能每次都打印）。
      只加舞台变量和舞台函数，不给精灵加字段，不影响解释器的方法表。只改副本，不改仓库。

  spx_coverage.py report [--unittest-log 文件] <日志...>
      汇总所有日志里的 COV 行，输出 Markdown 报告：每个文件的函数 / 事件处理覆盖率、没覆盖到的列表、
      消息覆盖、TEST_PLAN 用例清单里每个用例 ID 有没有对应的测试。

由 tools/test/run_spx.sh --coverage 调用。
"""
import glob
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GAME = os.path.join(ROOT, "TankBattle")
TEST_PLAN = os.path.join(ROOT, "docs", "v4", "TEST_PLAN.md")

FUNC = re.compile(r"^func (\w+)\(.*\{\s*$")
HANDLER = re.compile(r"^(onStart|onCloned|onClick|onKey|onMsg)\b(.*?)=> \{\s*$")
INPUT = ("onKey", "onClick")  # 按键和点击：无界面测试里触发不了，单独统计（见 TEST_PLAN 第六节）
TARGETS = {"main.spx 函数": 85, "全部函数": 75, "事件处理（不含按键 / 点击）": 70, "消息": 100}


def points(path):
    """(行号, 名字, 类别) 列表。类别：func / handler / input"""
    out = []
    starts = 0
    base = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f):
            m = FUNC.match(line)
            if m:
                out.append((n, f"{base}:{m.group(1)}", "func"))
                continue
            m = HANDLER.match(line)
            if m:
                kind, arg = m.group(1), m.group(2).strip().rstrip(",").strip()
                if kind == "onStart":
                    starts += 1
                    arg = f"#{starts}"
                name = f"{base}:{kind} {arg}".rstrip()
                out.append((n, name, "input" if kind in INPUT else "handler"))
    return out


def all_points(game=GAME):
    return {name: kind for p in sorted(glob.glob(os.path.join(game, "*.spx"))) for _, name, kind in points(p)}


def instrument(proj):
    for path in sorted(glob.glob(os.path.join(proj, "*.spx"))):
        marks = {n: name for n, name, _ in points(path)}
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        out = []
        for n, line in enumerate(lines):
            out.append(line)
            if n in marks:
                out.append(f'\ttCov(`{marks[n]}`)\n')
        if os.path.basename(path) == "main.spx":
            # 舞台变量 covSeen 放进第一个 var 块；tCov 放在第一个 func 前面（func 必须写在事件处理之前）
            i = next(k for k, l in enumerate(out) if l.startswith("var ("))
            out.insert(i + 1, "\tcovSeen map[string]bool // 覆盖率插桩（tools/test/spx_coverage.py）\n")
            j = next(k for k, l in enumerate(out) if l.startswith("func "))
            out[j:j] = ["// 覆盖率插桩：同一个名字只打印一次\n", "func tCov(id string) {\n", "\tif covSeen == nil {\n",
                        "\t\tcovSeen = map[string]bool{}\n", "\t}\n", "\tif !covSeen[id] {\n", "\t\tcovSeen[id] = true\n",
                        '\t\tprintln("COV", id)\n', "\t}\n", "}\n", "\n"]
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(out)


def messages(game=GAME):
    sent = set()
    for p in glob.glob(os.path.join(game, "*.spx")):
        with open(p, encoding="utf-8") as f:
            sent |= set(re.findall(r'broadcast(?:AndWait)? "(\w+)"', f.read()))
    return sorted(sent)


def plan_ids():
    with open(TEST_PLAN, encoding="utf-8") as f:
        return sorted(set(re.findall(r"^\| ([A-Z]\d\d) \|", f.read(), re.M)))


def pct(a, b):
    return 100.0 * a / b if b else 100.0


def report(logs, unittest_log=None):
    covered, tested = set(), set()
    for p in logs:
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("COV "):
                    covered.add(line[4:].strip())
                m = re.match(r"TEST (?:PASS|FAIL) ([A-Z]\d\d)\b", line)
                if m:
                    tested.add(m.group(1))
    if unittest_log and os.path.exists(unittest_log):
        with open(unittest_log, encoding="utf-8", errors="replace") as f:
            tested |= set(re.findall(r"test_([A-Z]\d\d)_", f.read()))

    pts = all_points()
    files = sorted({n.split(":")[0] for n in pts}, key=lambda s: (s != "main.spx", s))
    out = ["# 测试覆盖率报告", "", "## 函数和事件处理", "",
           "| 文件 | 函数 | 事件处理 | 按键 / 点击（只能手工测） |", "|---|---|---|---|"]
    tot = {"func": [0, 0], "handler": [0, 0], "input": [0, 0]}
    per = {}
    for fn in files:
        row = [fn]
        for kind in ("func", "handler", "input"):
            names = [n for n, k in pts.items() if k == kind and n.startswith(fn + ":")]
            hit = [n for n in names if n in covered]
            tot[kind][0] += len(hit)
            tot[kind][1] += len(names)
            per[(fn, kind)] = (len(hit), len(names))
            row.append(f"{len(hit)}/{len(names)}（{pct(len(hit), len(names)):.0f}%）" if names else "—")
        out.append("| " + " | ".join(row) + " |")
    out.append("| **合计** | " + " | ".join(f"**{a}/{b}（{pct(a, b):.0f}%）**" for a, b in tot.values()) + " |")

    sent = messages()
    got = {n.split('"')[1] for n in covered if ':onMsg "' in n}
    msg_hit = [m for m in sent if m in got]

    ids = plan_ids()
    id_hit = [i for i in ids if i in tested]

    values = {"main.spx 函数": pct(*per[("main.spx", "func")]), "全部函数": pct(*tot["func"]),
              "事件处理（不含按键 / 点击）": pct(*tot["handler"]), "消息": pct(len(msg_hit), len(sent))}
    out += ["", "## 目标", "", "| 指标 | 实际 | 目标 | |", "|---|---|---|---|"]
    for k, want in TARGETS.items():
        out.append(f"| {k} | {values[k]:.0f}% | ≥ {want}% | {'✅' if values[k] >= want else '❌'} |")
    out.append(f"| 用例清单（TEST_PLAN 第三节） | {len(id_hit)}/{len(ids)}（{pct(len(id_hit), len(ids)):.0f}%） | 参考 | |")

    miss = [n for n, k in pts.items() if k != "input" and n not in covered]
    out += ["", f"## 没覆盖到的函数和事件处理（{len(miss)} 个）", ""]
    out += [f"- `{n}`" for n in miss] or ["（没有）"]
    out += ["", f"## 没覆盖到的消息（{len(sent) - len(msg_hit)} / {len(sent)}）", ""]
    out += [f"- `{m}`" for m in sent if m not in got] or ["（没有）"]
    out += ["", f"## 还没有测试的用例 ID（{len(ids) - len(id_hit)} / {len(ids)}）", ""]
    out += [", ".join(i for i in ids if i not in tested) or "（没有）"]
    return "\n".join(out) + "\n"


def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "instrument":
        instrument(args[1])
    elif args and args[0] == "report":
        rest, ulog = args[1:], None
        if rest[:1] == ["--unittest-log"]:
            ulog, rest = rest[1], rest[2:]
        sys.stdout.write(report(rest, ulog))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
