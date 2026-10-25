#!/usr/bin/env python3
"""引擎内测试的覆盖率（见 docs/v4/TEST_PLAN.md 第四节）。spx 没有现成的覆盖率工具，这里自己插桩。

  spx_coverage.py instrument <工程副本目录>
      给副本里每个 .spx 的每个 func、每个事件处理的第一行插入 tCov("<文件>:<名字>")。
      tCov 在 main.spx 里，同一个名字只打印一次 "COV <名字>"（热点函数每帧都调用，不能每次都打印）。
      只加舞台变量和舞台函数，不给精灵加字段，不影响解释器的方法表。只改副本，不改仓库。

  spx_coverage.py report [--unittest-log 文件] <日志...>
      汇总所有日志里的 COV 行，输出 Markdown 报告：每个文件的函数 / 事件处理覆盖率、没覆盖到的列表、
      消息覆盖、TEST_PLAN 用例清单里每个用例 ID 有没有对应的测试。

  spx_coverage.py report --baseline tests/coverage-baseline.json ...
      再和基线比较：基线里覆盖到的函数 / 事件处理现在没覆盖到，或者新加的没有被任何测试执行，就失败（退出码 1）。

  spx_coverage.py baseline <输出.json> <第一次运行的目录> <第二次运行的目录> ...
      用几次完整运行的日志生成基线：每次都覆盖到的才算“覆盖到”；只有部分运行覆盖到的记为“不稳定”，不强制
      （例如子弹相撞抵消，受已知问题影响时有时无）。由 tools/test/update_baseline.sh 调用。

由 tools/test/run_spx.sh --coverage 调用。
"""
import glob
import json
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


def covered_in(logs):
    out = set()
    for p in logs:
        with open(p, encoding="utf-8", errors="replace") as f:
            out |= {line[4:].strip() for line in f if line.startswith("COV ")}
    return out


# 已知会时有时无的（不靠抽样判断，直接算不稳定）：原因写在后面
KNOWN_UNSTABLE = {
    'EBullet.spx:onMsg "clash"': "子弹迎面相撞经常不抵消（C17 已知问题），抵消没发生时这个处理不会执行",
}


def make_baseline(path, run_dirs):
    runs = [covered_in(glob.glob(os.path.join(d, "*", "run.log"))) for d in run_dirs]
    always, sometimes = set.intersection(*runs), set.union(*runs)
    always -= set(KNOWN_UNSTABLE)
    sometimes |= set(KNOWN_UNSTABLE)
    pts = all_points()
    data = {
        "说明": "tools/test/update_baseline.sh 生成，不要手改。covered：每次运行都覆盖到；unstable：只有部分运行覆盖到，不强制",
        "runs": len(runs),
        "points": sorted(pts),
        "covered": sorted(n for n in always if n in pts),
        "unstable": sorted(n for n in sometimes - always if n in pts),
        "unstable_why": {n: KNOWN_UNSTABLE.get(n, "抽样的几次运行里只有部分覆盖到") for n in sorted(sometimes - always) if n in pts},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return data


def compare(covered, baseline_path):
    """和基线比较：返回（Markdown 行列表，是否通过）"""
    with open(baseline_path, encoding="utf-8") as f:
        base = json.load(f)
    pts = all_points()
    lost = [n for n in base["covered"] if n in pts and n not in covered]
    new = [n for n, k in pts.items() if n not in base["points"] and k != "input" and n not in covered]
    unstable = [n for n in base.get("unstable", []) if n not in covered]
    out = ["", "## 和基线比较（tests/coverage-baseline.json）", ""]
    if not lost and not new:
        out.append(f"✅ 没有退步：基线覆盖到的 {len(base['covered'])} 个都还覆盖到，新加的函数 / 事件处理都有测试执行。")
    if lost:
        out += [f"❌ **原来覆盖到、现在没覆盖到（{len(lost)} 个）**：给它们补测试，或者在 PR 里说明为什么删掉了", ""] + [f"- `{n}`" for n in lost]
    if new:
        out += ["", f"❌ **新加的、没有任何测试执行（{len(new)} 个）**：同一个 PR 里加上测试", ""] + [f"- `{n}`" for n in new]
    if unstable:
        out += ["", "这次没覆盖到、但基线里标为不稳定的（不算退步）：" + "、".join(f"`{n}`" for n in unstable)]
    more = [n for n in covered if n in pts and n not in base["covered"] and n not in base.get("unstable", [])]
    if more:
        out += ["", f"覆盖率提高了（{len(more)} 个新覆盖到）：运行 `tools/test/update_baseline.sh` 更新基线，一起提交。"]
    return out, not lost and not new


def report(logs, unittest_log=None, baseline=None):
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
            text = f.read()
            tested |= set(re.findall(r"test_([A-Z]\d\d)_", text))
            tested |= set(re.findall(r"^ok \d+ - ([A-Z]\d\d)\b", text, re.M))  # node --test 的输出

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

    # 只由“已知不稳定”的事件处理接收的消息不计入目标（例如 clash，受 C17 已知问题影响时有时无），单独列出
    unstable_msgs = {n.split('"')[1] for n in KNOWN_UNSTABLE if ':onMsg "' in n}
    receivers = {}
    for n in pts:
        if ':onMsg "' in n:
            receivers.setdefault(n.split('"')[1], []).append(n)
    skip = {m for m in unstable_msgs if all(r in KNOWN_UNSTABLE for r in receivers.get(m, []))}
    sent = [m for m in messages() if m not in skip]
    got = {n.split('"')[1] for n in covered if ':onMsg "' in n}
    msg_hit = [m for m in sent if m in got]

    ids = plan_ids()
    id_hit = [i for i in ids if i in tested]

    values = {"main.spx 函数": pct(*per[("main.spx", "func")]), "全部函数": pct(*tot["func"]),
              "事件处理（不含按键 / 点击）": pct(*tot["handler"]), "消息": pct(len(msg_hit), len(sent))}
    out += ["", "## 目标", "", "| 指标 | 实际 | 目标 | |", "|---|---|---|---|"]
    for k, want in TARGETS.items():
        out.append(f"| {k} | {values[k]:.0f}% | ≥ {want}% | {'✅' if values[k] >= want else '❌'} |")
    if skip:
        out.append(f"| 不计入的不稳定消息 | {'、'.join(sorted(skip))} | — | 原因见 KNOWN_UNSTABLE |")
    out.append(f"| 用例清单（TEST_PLAN 第三节） | {len(id_hit)}/{len(ids)}（{pct(len(id_hit), len(ids)):.0f}%） | 参考 | |")

    miss = [n for n, k in pts.items() if k != "input" and n not in covered]
    out += ["", f"## 没覆盖到的函数和事件处理（{len(miss)} 个）", ""]
    out += [f"- `{n}`" for n in miss] or ["（没有）"]
    out += ["", f"## 没覆盖到的消息（{len(sent) - len(msg_hit)} / {len(sent)}）", ""]
    out += [f"- `{m}`" for m in sent if m not in got] or ["（没有）"]
    out += ["", f"## 还没有测试的用例 ID（{len(ids) - len(id_hit)} / {len(ids)}）", ""]
    out += [", ".join(i for i in ids if i not in tested) or "（没有）"]
    ok = True
    if baseline and os.path.exists(baseline):
        lines, ok = compare(covered, baseline)
        out += lines
    return "\n".join(out) + "\n", ok


def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "instrument":
        instrument(args[1])
    elif args and args[0] == "report":
        rest, ulog, base = args[1:], None, None
        while rest[:1] in (["--unittest-log"], ["--baseline"]):
            if rest[0] == "--unittest-log":
                ulog = rest[1]
            else:
                base = rest[1]
            rest = rest[2:]
        text, ok = report(rest, ulog, base)
        sys.stdout.write(text)
        sys.exit(0 if ok else 1)
    elif len(args) >= 3 and args[0] == "baseline":
        d = make_baseline(args[1], args[2:])
        print(f"基线：{len(d['covered'])} 个覆盖到，{len(d['unstable'])} 个不稳定（{d['runs']} 次运行）→ {args[1]}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
