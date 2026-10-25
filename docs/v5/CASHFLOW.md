# 坦克大战 v5.0 · 各平台的盈利周期与现金流

> [v5.0 规划](PLAN.md)的一部分：每个平台**从开始投入到第一笔钱到账要多久**、钱怎么打回来、要扣哪些税、什么时候回本。收费方式见 [MONETIZATION.md](MONETIZATION.md)，推广时间线见 [MARKETING.md](MARKETING.md)。
>
> 依据：2026-10-25 查阅的平台官方文档（Steamworks、App Store Connect、Play Console、Microsoft Partner Center）和公开报道。可信度：**高** = 官方文档；**中** = 有日期的报道或多家一致；**低** = 第三方或个案。**销量和收入全部是推测**，三档情景的假设写在第三节。本文不是税务或法律意见，涉及税务的部分要请专业人士确认。

## 一、一句话结论

| 平台 | 最早上架 | 第一笔钱最早到账 | 打款规则 | 第一年收入（基准情景，推测） | 定位 |
|---|---|---|---|---|---|
| **Steam** | 2027-03 中旬（Next Fest 之后） | **2027-04-30 前** | 每月一次，次月 30 日前付上月销售额；满 $100 才付 | 约 $5900 | **主力**，占收入大头 |
| **Microsoft Store（PC）** | 和 Steam 同时 | 累计满 $50 后的次月 15 日前后；从销售到收款约 3 个月 | 每月一次，满 $50 | 约 $370 | 顺手上架 |
| **App Store** | 2027-05（决策点 2 之后） | 约 2027-07 | 苹果财务月结束后 45 天内；有最低金额（按币种约 $10~40，第三方数据） | 约 $1150 | 第二收入来源 |
| **Google Play** | 取决于 spx 升级引擎，**最早 2027 下半年** | 上架后次月 15 日前后 | 每月一次，次月 15 日前后付上月 | 第一年按 0 计 | 增量 |
| Xbox 主机 | v5 不上 | — | — | — | 只评估 |

**基准情景第一年合计约 $7400（约 ¥5.3 万），投入约 $1500，第一笔 Steam 打款到账（2027-04 底）时就能收回大部分投入。** 三档情景见第三节。

## 二、每个平台的周期

### 2.1 Steam

| 阶段 | 时间 | 要做的事 | 依据 |
|---|---|---|---|
| 注册 Steamworks、交 $100 上架费 | 2026-11 上旬 | 填税务表、银行信息；**有一段等待期**（新账号要等一段时间才能发布） | Steamworks（高） |
| 开 Coming Soon 页 | 2026-11 中旬 | 商店页要审核，留出几天 | Steamworks（高） |
| 积累愿望单 | 2026-11 ~ 2027-03 | Couch Co-Op Fest（02-08）、Next Fest（02-22） | MARKETING.md |
| 发售 | 2027-03 中旬 | Next Fest 结束（03-01）之后才能发售 | Steamworks（高） |
| **第一笔钱** | **2027-04-30 前** | 3 月的销售额在 4 月 30 日前付；到账还要几个工作日 | Steamworks 打款文档（高） |
| 上架费返还 | 收入达到 $1000 的那个月 | 在月报里单列一行返还 $100 | Steamworks（高） |

**打款规则**：每月一次，付上个月的销售额，次月 30 日前；**上月余额满 $100 才付**，不满就累计到下个月；海外银行走美元 SWIFT 电汇；银行信息要在每月 15 日前改好，否则顺延一个月（高）。从卖出到到账实际约 6~8 周（第三方，中）。

**税（中国个人开发者）**：

- Valve 只对**美国区**的收入代扣美国预扣税。填 W-8BEN 时选“非美国人”，**纳税人识别号填身份证号并申请中美税收协定优惠，税率是 10%**；不填就按 30% 扣（多家中文资料一致，中）。
- 结汇：个人每年有 5 万美元的结汇额度，基准情景远低于这个数；SWIFT 电汇可能被中间行扣手续费（个案：$120 扣了 $30），金额小的时候可以把 Steam 的打款门槛调高，攒几个月再付一次（中）。
- 国内个人所得税：境外所得要在次年 3~6 月的年度汇算里申报，在美国已扣的税一般可以抵免。按“特许权使用费”还是“经营所得”计税目前没有定论（低，**要请税务专业人士确认**）。如果团队以公司名义发行，处理方式不同。

### 2.2 Microsoft Store（PC）

| 阶段 | 时间 | 说明 | 依据 |
|---|---|---|---|
| 注册 | 2026-12 | 个人免费，身份验证（证件 + 自拍） | Microsoft（高） |
| 确认普通 Win32 游戏能否只用 MSIX 提交 | 2026-12 | 官方没写清楚，问 Partner Center | EXPERIENCE.md 第四节 |
| 上架 | 2027-03，和 Steam 同时 | 审核一般 1~7 天 | 公开资料（中） |
| 第一笔钱 | 累计满 $50 后 | 每月 15 日前后付；微软员工在问答区说从销售到收款约 3 个月 | Microsoft Learn / Q&A（中~高） |

抽成 12%（PC 游戏）。销量小的话，可能要好几个月才攒满 $50。

### 2.3 App Store

| 阶段 | 时间 | 说明 | 依据 |
|---|---|---|---|
| 投递 Apple Arcade（可选） | 2027-04 前 | 只收还没发布的游戏 | Apple（高） |
| 加入开发者计划、申请小型企业计划（15%） | 2027-04 | $99 / 年；小型企业计划要手动申请，获批后的下个财务月起生效 | Apple（高） |
| 签名、Xcode 26 编译、TestFlight | 2027-04 ~ 05 | 需要一台装 Xcode 26 的 Mac | TECH.md |
| 上架 | 2027-05 | 审核一般几天 | — |
| **第一笔钱** | **约 2027-07** | 5 月财务月结束后 45 天内付；实际付款日大约在财务月结束后 33 天左右；每个国家 / 地区都要满最低金额，不满就累计 | App Store Connect 帮助（高）；门槛数字来自第三方（低） |

注意：苹果用自己的**财务日历**，财务月在每个自然月最后一个星期六前后结束，不是自然月（中）。

### 2.4 Google Play

| 阶段 | 时间 | 说明 | 依据 |
|---|---|---|---|
| 等 spx 升级引擎（AAB、目标 API 36、16 KB 页） | 不确定 | 不升级就上不了架 | PLATFORMS.md 第六节 |
| 注册、封闭测试 | 引擎就绪后 | $25；个人账号要 **12 人连续 14 天**封闭测试，之后申请正式发布，Google 一般 7 天内答复 | Play Console 帮助（高） |
| 上架 | 引擎就绪后约 3~4 周 | — | — |
| 第一笔钱 | 上架次月的 15 日前后 | 每月 1 日到月底的订单，次月 15 日前后付；电汇到账再等几天 | Play Console 帮助（高） |

最低打款金额官方页面的数字这次没有核实到（第三方说法不一）。抽成：美国 / 欧洲 / 英国首 $100 万 10% + 结算费 5%，其他地区 15%（高）。

## 三、第一年的盈利预期（推测）

### 3.1 假设

| 假设 | 数值 | 依据 |
|---|---|---|
| Steam 售价 | $4.99 | MONETIZATION.md |
| Steam 每份到手 | 约 $2.6 | 扣 Valve 30%，再扣区域折扣、美国预扣税、退款约 25% |
| 首周销量 / 发售时愿望单 | 0.15 | GameDiscoverCo 中位数 0.10~0.15、定价低于 $10 的游戏偏高（中） |
| 第一年销量 / 首周销量 | 3 倍 | **推测**：首周之后靠季节特卖、主题节和长尾 |
| iOS 售价 / 每份到手 | $2.99 / 约 $2.3 | 扣 15%，再扣税和地区差价 |
| Microsoft Store 每份到手 | 约 $3.7 | $4.99 扣 12%，再扣税约 15% |

### 3.2 三档情景

| 情景 | 发售时愿望单 | Steam 第一年 | Microsoft Store | App Store | **第一年合计** |
|---|---|---|---|---|---|
| 保守（推广不力） | 2000 | 900 份 ≈ $2300 | 20 份 ≈ $75 | 100 份 ≈ $230 | **≈ $2600（约 ¥1.9 万）** |
| **基准（达到铜档）** | **5000** | **2250 份 ≈ $5900** | **100 份 ≈ $370** | **500 份 ≈ $1150** | **≈ $7400（约 ¥5.3 万）** |
| 乐观（主播带动 / 苹果推荐） | 15000 | 6750 份 ≈ $17600 | 300 份 ≈ $1100 | 2000 份 ≈ $4600 | **≈ $23300（约 ¥16.8 万）** |

（汇率按 1 美元 ≈ 7.2 元人民币估算。）

参照系：2025 年 Steam 上 65.9% 的游戏收入不到 $1000，收入超过 $10 万的约 8%（Gamalytic，中）。**基准情景已经好于大多数 Steam 游戏，前提是推广做到 5000 个愿望单**；做不到就推迟发售（MARKETING.md 第三节的决策点）。

### 3.3 投入

| 项目 | 金额 | 时间 | 说明 |
|---|---|---|---|
| Steam 上架费 | $100 | 2026-11 | 收入满 $1000 后返还 |
| 商店胶囊图外包 | 约 $800 | 2026-11 | 推测；像素风游戏也要插画风胶囊图 |
| 付费广告测试 | $500 | 2027-01 | 单个愿望单超过 $2~3 就停 |
| Apple 开发者计划 | $99 / 年 | 2027-04 | — |
| Google Play 注册 | $25 | 引擎就绪后 | 一次性 |
| Microsoft Store | $0 | 2026-12 | 个人免费 |
| Steam Deck 测试 | $0 | — | Valve 自己做兼容性测试；有条件再借实机 |
| **合计** | **约 $1500（约 ¥1.1 万）** | | 不含人力 |

### 3.4 现金流（基准情景，按月）

| 月份 | 支出 | 到账 | 累计 | 发生了什么 |
|---|---|---|---|---|
| 2026-11 | −$900 | — | −$900 | 注册 Steamworks、胶囊图、开 Coming Soon 页 |
| 2026-12 | — | — | −$900 | 试玩版、Microsoft Store 注册 |
| 2027-01 | −$500 | — | −$1400 | 付费广告测试、主播发 Key |
| 2027-02 | — | — | −$1400 | Couch Co-Op Fest、Next Fest |
| 2027-03 | — | — | −$1400 | Steam、Microsoft Store 发售（3 月中旬） |
| 2027-04 | −$99 | **+约 $1900**（3 月半个月的销售，含首周） | +约 $400 | **回本**；Apple 开发者计划 |
| 2027-05 | — | +约 $450 | +约 $850 | iOS 上架（$100 上架费已随 4 月的 Steam 打款返还，含在到账里） |
| 2027-06 | — | +约 $300 | +约 $1150 | Steam 夏季特卖（6 月下旬）的收入 7 月底到账 |
| 2027-07 | — | +约 $500（Steam 夏促 + 首笔苹果打款） | +约 $1650 | — |
| 2027-08 ~ 2028-02 | — | 每月约 $250~600 | 到 2028-03 累计约 +$5900 | 秋季、冬季特卖带来小高峰 |

（第一年 Steam 收入的分布按“首周约占三分之一、其余在特卖和长尾里”估算，只用来说明节奏。）

**关键时间点**：

- **回本**：基准情景在 **2027-04 底**第一笔 Steam 打款到账时回本；保守情景大约在 2027-08 回本。
- **第一年结束**（2028-03）：基准情景累计净收入约 $5900（约 ¥4.2 万）。
- 人力成本没有算进去：两个人业余开发，从首次提交到 v4.0.1 约 44 小时。

## 四、风险和对策

| 风险 | 影响 | 对策 |
|---|---|---|
| 愿望单攒不到 5000 | 落到保守情景 | 推迟发售，参加 2027-06 的 Next Fest（每款游戏只能参加一次，所以 2 月那届要准备充分） |
| 改名后被认为“太像原作”，审核被拒 | 上架延期 | 改名、换基地造型，强调编辑器和双人合作（PLATFORMS.md 第七节） |
| 手柄补丁做不通 | Steam Deck 只能评“可玩”，远程同乐体验差 | 先用 Steam Input 键盘模拟上架，同时给 spx 提 PR（TECH.md 第一节） |
| 退款率高（流程短，2 小时内可退） | 收入打折 | 定价低（$4.99）；加强重玩性：编辑器、双人、两种画风 |
| spx 迟迟不升级引擎 | Google Play 上不了 | 不影响 Steam 和 iOS；Google Play 本来就按 0 计 |
| 税务和结汇处理不当 | 多扣税、到账慢 | 填好 W-8BEN（10%）；金额小时调高打款门槛；请专业人士确认国内申报 |

## 来源

- Steam：[打款与报表](https://partner.steamgames.com/doc/finance/payments_salesreporting)、[打款常见问题](https://partner.steamgames.com/doc/finance/payments_salesreporting/faq)、[Steam Direct 费用](https://partner.steamgames.com/doc/gettingstarted/appfee)、[Steam 抽成说明（Immutable）](https://www.immutable.com/guides/how-much-does-steam-take)
- Apple：[App Store Connect：收款概述](https://www.developer.apple.com/help/app-store-connect/getting-paid/overview-of-receiving-payments)、[查看付款和收益](https://www.developer.apple.com/help/app-store-connect/getting-paid/view-payments-and-proceeds)、[苹果打款时间（Leus Capital，2026）](https://leus.capital/blog/apple-payout-guide-2026-how-to-accelerate-your-studios-cash-flow)、[小型企业计划](https://developer.apple.com/app-store/small-business-program/)
- Google Play：[订单处理与打款](https://support.google.com/googleplay/android-developer/answer/137997?hl=en)、[Play 开发者打款时间（Nami ML）](https://www.nami.ml/blog/play-store-developer-payout-schedule/)
- Microsoft：[Partner Center 收款](https://learn.microsoft.com/en-us/partner-center/marketplace-offers/marketplace-get-paid)、[各地区打款门槛与方式](https://learn.microsoft.com/en-us/partner-center/marketplace-offers/payment-thresholds-methods-timeframes)、[开发者打款门槛（Microsoft Q&A，2024）](https://learn.microsoft.com/en-us/answers/questions/1500214/microsoft-partner-center-earnings-payments-default)、[Windows 应用账户常见问题](https://learn.microsoft.com/en-us/windows/apps/publish/faq/manage-your-account)
- 税务与结汇：[Steam 收益提现到国内（CSDN，2026-04）](https://www.csdn.net/article/2026-04-30/160664183)、[Steam 收入怎么汇款、超过五万限额怎么办（知乎）](https://zhuanlan.zhihu.com/p/711767873)、[开发者海外收款指南（万里汇，2026）](https://www.worldfirst.com.cn/static/contenthub/blog/2026-developer-overseas-payment-guide)
- 销量基准：见 [MARKETING.md](MARKETING.md) 和 [MONETIZATION.md](MONETIZATION.md) 的来源
