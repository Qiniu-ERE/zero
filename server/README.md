# 坦克大战排行榜服务

v6 自建的**全球榜（周榜）**和**每日挑战榜**的后端（规划见 [v6.0 规划第五节](../docs/v6/PLAN.md#五排行榜)）。好友榜用各平台自己的接口，不走这里。

- 一个文件 `leaderboard.py`，只用 Python 3 标准库（`http.server`、`sqlite3`、`json`、`threading`），不装任何第三方包。
- 数据存在一个 sqlite 文件里。
- **还没有部署**，游戏里的服务地址上线前再填。

## 本地运行

```bash
python3 server/leaderboard.py --host 127.0.0.1 --port 8787 --db lb.sqlite
curl http://127.0.0.1:8787/v1/health        # {"ok": true, "version": "1", "day": 20758, "week": 2964}
```

| 参数 | 默认 | 说明 |
|---|---|---|
| `--host` | `127.0.0.1` | 监听地址；部署到容器里用 `0.0.0.0` |
| `--port` | `8787` | 端口 |
| `--db` | `lb.sqlite` | sqlite 文件，不存在就自动建 |
| `--trust-proxy` | 关 | 按 `X-Forwarded-For` 的第一个地址做 IP 限频；只在可信的反向代理 / 无服务器平台后面打开，否则客户端能伪造 |

测试：`python3 -m unittest discover -s tests/tools -p 'test_leaderboard.py' -v`（用例 R10~R29，见 [test_leaderboard.py](../tests/tools/test_leaderboard.py)）。

## 时间怎么算

都是整数，按北京时间（UTC+8）切天，周一开始一周：

- `day = (unix 秒 + 8*3600) // 86400`
- `week = (day - 4) // 7`

每日挑战榜的期数 `period` 就是 `day`，周榜是 `week`。

## 接口

请求和响应都是 JSON（`Content-Type: application/json`）；所有响应带 `Access-Control-Allow-Origin: *`，`OPTIONS` 预检返回 204，网页版能直接从浏览器调用。出错统一返回 `{"ok": false, "error": "<中文原因>"}`。

| 接口 | 说明 | 成功返回 |
|---|---|---|
| `GET /v1/health` | 健康检查，顺便返回服务器的日期（网页版拿不到本机时间，每日挑战靠它） | `{"ok":true,"version":"1","day":20758,"week":2964}` |
| `POST /v1/score` | 上传一局成绩 | `{"ok":true,"rank":名次,"total":本榜人数,"best":这个玩家的最好成绩}` |
| `GET /v1/board?region=&board=&period=&limit=` | 读榜单前几名；`limit` 默认 10，最多 50 | `{"ok":true,"total":N,"rows":[{"rank","player","tag","score","chips","level"}]}` |
| `GET /v1/rank?region=&board=&period=&player=` | 查某个玩家的名次 | `{"ok":true,"rank":名次（不在榜上是 0）,"total":N,"score":分数（没有是 0）}` |
| 其他路径 | — | 404 |

上传的请求体：

```json
{"player": "0123456789abcdef", "region": "global", "board": "daily", "period": 20759,
 "score": 1200, "secs": 300, "stage": 10, "chips": ["rapid", "shield"], "level": 3, "version": "6.0.0"}
```

`tag = int(player[:4], 16) % 10000`，游戏里把玩家显示成“指挥官 #tag”。

### 校验规则（不合格返回 400）

| 字段 | 规则 |
|---|---|
| `player` | 16 位小写十六进制 |
| `region` | `global`（海外）或 `cn`（国内） |
| `board` | `weekly`（周榜）或 `daily`（每日挑战） |
| `period` | 整数；只能是本期或上一期（过了零点 / 周一还能补传上一期，离线成绩联网后补传靠这个） |
| `score` | 整数，合理性检查：每日挑战 0~11000（一关）；周榜是战役累计分，0~11000 × 打到的关数 |
| `secs` | 20~3600 秒 |
| `stage` | 每日挑战是 10（游戏里每日挑战的关卡编号）；周榜是战役打到第几关，1~8 |
| `chips` | 最多 3 块、不重复，只能是 `rapid` `double` `pierce` `bounce` `shield` `engine` `float` `stealth` `magnet` |
| `level` | 1~4，并且等于芯片数 + 1 |
| `version` | 1~16 个字符的字符串 |
| 请求体 | 不超过 4 KB，必须是合法的 JSON 对象；多出来的字段忽略 |

读接口（`board` / `rank`）缺参数或参数不对也返回 400；`period` 只要是非负整数，查往期没有限制。

### 限频（超了返回 429）

- 同一个 IP 60 秒内最多 30 次上传（每次 `POST /v1/score` 都算，包括坏请求）；
- 同一个玩家 60 秒内最多 10 次上传（玩家 ID 格式对了就算，成绩不合格也算）；
- 被拒的那次不计数；计数在内存里，重启清零。

### 存储和排名

- 每个（区、榜、期、玩家）只留**最好成绩**：分数更低或相同不覆盖，但照样返回当前名次。
- 同分时**先提交的排前面**（以刷出这个分数的那次提交为准）。
- **海外榜和国内榜完全分开**：国内的成绩不会出现在海外榜，反过来也一样。

## 存了哪些数据

每条成绩只存：区、榜、期、玩家 ID、分数、用时、关卡、芯片、等级、版本、提交时间。

- 玩家 ID 是游戏首次打开时生成的**随机设备 ID**（以后可以换成平台玩家 ID 的摘要），不是手机号、昵称或账号。
- **不存 IP**：IP 只在内存里做限频，60 秒后就清掉。
- 不收集任何其他个人信息。

## 部署（还没做）

- 随便一台小虚拟机，或者无服务器容器（能跑 Python 3、能挂一块持久盘放 sqlite 就行）；玩家量级下用免费额度即可（推测）。
- 放在反向代理 / 平台网关后面时打开 `--trust-proxy`，否则所有请求看起来都来自同一个代理 IP，会一起被限频。
- **海外榜和国内榜是两份独立部署**，各在自己的地区：海外（Steam、App Store、Google Play、网页）用 `region=global` 部署在海外；国内（微信小游戏）用 `region=cn`。
- **国内数据必须存在境内**，例如用微信云开发（CloudBase）的云函数 + 数据库按同样的接口和规则实现一份；这里没有实现。
- sqlite 适合单实例；要多实例横向扩展就得换成共享数据库，限频也要挪到共享存储里。
