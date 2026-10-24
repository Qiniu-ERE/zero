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
"""
import os
import re
import shutil
import sys

spx, app_id, title, version = sys.argv[1:5]
here = os.path.dirname(os.path.abspath(__file__))
tpl = os.path.join(spx, "cmd", "spx", "template", "project")

shutil.copyfile(os.path.join(here, "icon.png"), os.path.join(tpl, "engine", "icons", "logo.png"))

major, minor, patch = (version.split(".") + ["0", "0"])[:3]
code = int(major) * 10000 + int(minor) * 100 + int(patch)
ICON = "res://engine/icons/logo.png"
OPTIONS = {
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
        "application/short_version": version,
        "application/version": version,
        "application/export_project_only": "true",
    },
    "Mac": {
        "application/bundle_identifier": app_id,
        "application/short_version": version,
        "application/version": version,
    },
}


def quote(v):
    return v if v in ("true", "false") or re.fullmatch(r"-?\d+", v) else '"' + v.replace('"', '\\"') + '"'


def patch_presets(path):
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
            opts = OPTIONS.get(names.get(m.group(1)))
        elif line.startswith("["):
            opts = None
        if opts:
            key = line.split("=", 1)[0]
            if key in opts:
                line = f"{key}={quote(opts[key])}"
                done.add(key)
        out.append(line)
    missing = [k for o in OPTIONS.values() for k in o if k not in done]
    if missing:
        sys.exit(f"export_presets.cfg 里没有找到这些选项：{missing}")
    open(path, "w", encoding="utf-8").write("\n".join(out))


def patch_project(path):
    s = open(path, encoding="utf-8").read()
    if "config/icon=" not in s:
        s = s.replace("[application]\n", f'[application]\n\nconfig/icon="{ICON}"\n', 1)
    open(path, "w", encoding="utf-8").write(s)


patch_presets(os.path.join(tpl, "export_presets.cfg"))
patch_project(os.path.join(tpl, "project.godot"))
print(f"patched spx templates: {app_id} {title} {version} (versionCode {code})")
