#!/usr/bin/env python3
"""给 spx 源码里的工程模板打补丁，然后再编译安装 spx。

spx 每次导出都会用内置模板覆盖工程里的 export_presets.cfg / project.godot，所以包名、版本号、
图标、iOS 签名方式只能改模板。改动：
- 图标：engine/icons/logo.png 换成坦克大战的图标（iOS、Android、桌面都引用它）
- Android：包名、应用名、版本号，启动图标
- iOS：Bundle ID、版本号；只导出 Xcode 工程（之后用 xcodebuild 编出不签名的 IPA，见 build.sh）。
  Godot 要求填 Team ID，这里填占位值，不签名时不会用到
- project.godot：应用图标

用法：python3 tools/export/patch_spx.py <spx 源码目录> <包名> <应用名> <版本号>
      python3 tools/export/patch_spx.py --version-info <版本号>   只打印“纯数字版本号 版本代码”，例如 4.0.1 40001
      （build.sh 打 Android / iOS 前用它核对 spx 里的模板版本号）
"""
import os
import re
import shutil
import sys

ICON = "res://engine/icons/logo.png"


def version_numbers(version):
    """版本号 → (纯数字版本号, 安卓版本代码)。

    开发版的版本号像 3.0.0-dev.12：版本代码和 iOS 版本号只能用纯数字部分。
    版本代码 = 主版本 × 10000 + 次版本 × 100 + 修订号，所以次版本和修订号都不能超过 99。
    """
    m = re.match(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+].*)?$", version or "")
    if not m:
        raise ValueError(f"版本号格式不对：{version!r}（应该像 4.0.1 或 4.0.1-rc.1）")
    major, minor, patch = (int(g or 0) for g in m.groups())
    if minor > 99 or patch > 99:
        raise ValueError(f"版本号 {version} 的次版本或修订号超过 99，安卓版本代码会和别的版本重复")
    return f"{major}.{minor}.{patch}", major * 10000 + minor * 100 + patch


def options(app_id, title, version):
    base, code = version_numbers(version)
    return {
        "Android": {
            "package/unique_name": app_id,
            "package/name": title,
            "version/code": str(code),
            "version/name": version,
            "launcher_icons/main_192x192": ICON,
            "launcher_icons/adaptive_foreground_432x432": ICON,
        },
        "iOS": {
            "application/app_store_team_id": "TANKBATTLE",
            "application/bundle_identifier": app_id,
            "application/short_version": base,
            "application/version": base,
            "application/export_project_only": "true",
        },
        "Mac": {
            "application/bundle_identifier": app_id,
            "application/short_version": base,
            "application/version": base,
        },
    }


def quote(v):
    return v if v in ("true", "false") or re.fullmatch(r"-?\d+", v) else '"' + v.replace('"', '\\"') + '"'


def patch_presets(path, opts_by_preset):
    lines = open(path, encoding="utf-8").read().split("\n")
    names, cur, done = {}, None, set()
    for line in lines:  # 先找出每个 preset 编号对应的名字
        m = re.match(r'\[preset\.(\d+)\]$', line)
        if m:
            cur = m.group(1)
        m = re.match(r'name="(.*)"$', line)
        if m and cur is not None and cur not in names:
            names[cur] = m.group(1)
    out, opts = [], None
    for line in lines:
        m = re.match(r'\[preset\.(\d+)\.options\]$', line)
        if m:
            name = names.get(m.group(1))
            opts = opts_by_preset.get(name)
        elif line.startswith("["):
            opts = None
        if opts:
            key = line.split("=", 1)[0]
            if key in opts:
                line = f"{key}={quote(opts[key])}"
                done.add((name, key))
        out.append(line)
    # 按“preset 名字 + 选项”记录：iOS 和 Mac 有同名选项，只改到一个也要报错
    missing = [f"{n}: {k}" for n, o in opts_by_preset.items() for k in o if (n, k) not in done]
    if missing:
        sys.exit(f"export_presets.cfg 里没有找到这些选项：{missing}")
    open(path, "w", encoding="utf-8").write("\n".join(out))


def patch_project(path):
    s = open(path, encoding="utf-8").read()
    if "config/icon=" not in s:
        s = s.replace("[application]\n", f'[application]\n\nconfig/icon="{ICON}"\n', 1)
    open(path, "w", encoding="utf-8").write(s)


def main(argv):
    if len(argv) == 2 and argv[0] == "--version-info":
        try:
            base, code = version_numbers(argv[1])
        except ValueError as e:
            sys.exit(str(e))
        print(base, code)
        return
    if len(argv) != 4:
        sys.exit(__doc__)
    spx, app_id, title, version = argv
    try:
        opts = options(app_id, title, version)
    except ValueError as e:
        sys.exit(str(e))
    here = os.path.dirname(os.path.abspath(__file__))
    tpl = os.path.join(spx, "cmd", "spx", "template", "project")
    shutil.copyfile(os.path.join(here, "icon.png"), os.path.join(tpl, "engine", "icons", "logo.png"))
    patch_presets(os.path.join(tpl, "export_presets.cfg"), opts)
    patch_project(os.path.join(tpl, "project.godot"))
    print(f"patched spx templates: {app_id} {title} {version} (versionCode {opts['Android']['version/code']})")


if __name__ == "__main__":
    main(sys.argv[1:])
