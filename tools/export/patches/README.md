# spx 源码补丁

这里放给 spx 源码打的补丁（例如 v5 的手柄支持），现在还是空的。

- `tools/export/setup_spx.sh` 每次都先把 `.build/cache/spx` 恢复成 `env.sh` 里 `SPX_COMMIT` 的干净源码，
  再按文件名顺序 `git apply` 这里的 `*.patch`，然后才打模板补丁（`patch_spx.py`）、编译安装 spx。
- 文件名用编号开头，决定顺序：`0001-gamepad-input.patch`、`0002-...patch`。只认 `.patch` 结尾的文件。
- 生成补丁：在 `.build/cache/spx` 里改好源码，`git -C .build/cache/spx diff -- <改过的文件> > tools/export/patches/0001-xxx.patch`
  （只包含源码改动，不要把 `patch_spx.py` 改的模板文件也带进来）。
- 补丁的文件名和内容算一个校验和，`setup_spx.sh` 装好 spx 后写进 `.build/cache/spx/.bin/tankbattle-patches.txt`；
  `build.sh` 打包前核对，补丁改过而 spx 没有重装时直接报错，提示重新运行 `setup_spx.sh`。
  `.github/workflows/test.yml` 的 spx 缓存键也包含这个目录。
- 升级 `SPX_COMMIT` 时补丁可能打不上，`setup_spx.sh` 会报错停下，要按新源码重新生成补丁。
