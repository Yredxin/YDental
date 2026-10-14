# S10-FC1 单进程双事务财务并发定向回归

## 结论与边界

按 [#34 正式授权 6170892559](https://github.com/Yredxin/YDental/issues/34#issuecomment-6170892559)执行。已于任何新库/Odoo启动前发布并 API 逐字读回[强制预检 6171084143](https://github.com/Yredxin/YDental/issues/34#issuecomment-6171084143)。一个新合成库、一个 Odoo shell 主进程、四组两个独立 ORM/PostgreSQL 后端的真实重叠，七次预列业务提交。Odoo PID2820768 exit0、signal11=false；旧 Native SIGSEGV 原因仍 UNKNOWN。

**有限技术子项：A 双审批竞争、B 已确认线下实退先行与取消竞争、C 两个 close 先行交错及后续合法解锁/更正，均有本批真实 Odoo 证据。S10 整体技术与生产继续 BLOCKED。** 现有 S10 产品未修改。本批没有发现足以在此授权内改产品的已证缺陷。

| 场景 | 本批真实结果 | 覆盖边界 |
|---|---|---|
| FC1-A / T04 | `ODOO_PASS_COMMITTED`：前台批准一次；医生独立后端 SQLSTATE40001 并 `ODOO_PASS_ROLLBACK`；请求经理自批 `EXPECTED_REJECT`；相同操作 key 返回 `already_accepted`；无贷项、outbound 或资金出账，审批审计仅增加一条。 | 第二批准者的受控业务拒绝路径未在本次新事务重试；40001 未冒称成功。 |
| FC1-B / T05 | `ODOO_PASS_COMMITTED`：经理合成线下实退 25，独立前台取消事务在首事务未提交期间等待后 40001 回滚。新事务读回一条 `done`、25 posted outbound、25 posted credit、25 原生 partial；本场景收款100，另有待退20，未超原实收。 | 完成后再次 cancel/execute、同 key 丢失响应重放及 `unknown` 恢复竞争 **NOT_RUN**；不能据此称 T05 全闭合。 |
| FC1-C1 / T07/T16 | `ODOO_PASS_COMMITTED`：前台今日 card close 先行，经理今日退款竞争事务 40001 回滚；读回快照 gross0/refunded0/pending30，无半付款。经理随后真实执行30，原入款日 10月13日、实际退款日 10月14日，card posted outbound，已确认前台快照数值不回填。 | 未在本批再建经理退款日 close；反向“退款先提交、close 等待” **NOT_RUN**。 |
| FC1-C2 / T07/T16 | `ODOO_PASS_COMMITTED`：经理 10月13日 cash close 先行，前台重分类竞争事务 40001 回滚；读回 cash gross100、无调整凭证。前台财务授权解锁后生成同公司 100 借/100 贷的 posted 调整凭证，经理以 WeChat 重结 gross100；旧 cash 周期保留 gross100、状态 unlocked。 | 更正后的原现金入款再实际微信退款、日期绕锁/未授权改已确认金额负向及反向交错 **NOT_RUN**。 |

`ODOO_PASS_ROLLBACK`仅指预期的并发失败事务已回滚，未创建第二笔业务；不能将它计为第二个成功动作。真正重叠的主后端 PID547513，第二后端 PID547555（A/B）及547558（C）；每组第二 actor 在第一 actor 未提交时已开始并仍在等待，第一提交后第二于互斥行更新处得到 SQLSTATE40001。Odoo 日志保留四条原生序列化错误。没有重试至偶然成功，也没有第二次 Odoo shell。

## 固定身份、隔离与预算

分支及固定起点 `ce21976f4bc448ff1aa3c2380ce6f959aed9dbde`；Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；历史 S10 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、fixed test `255b48f54495eb99638af8ffc824771b9a5af3e7`；实际 S10 服务 blob `d4d4363ab2dfdd982606f464e5b66c240744fac6`、S07 服务 SHA256 `df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b`。#23/#29/#31/#34 当前正文及全部有效评论经 API 取得，开工时数目 3/7/8/100；#35 OPEN/0。未重复 C1-R1/R2 无新变量的价格/建仓试验；本次仅在财务合成夹具前明确开启已获批的三个原生组。

只读核验的纯模板 `ydental_s10_test_20261014044700_4f6a8d2c`/OID2100080：92 installed（含 S10 服务与合成适配器）、70 系统附件、124 安装 filestore 文件逐 SHA、主要业务表 0、活动连接 0。克隆唯一新库 `ydental_s10_test_20261014145000_fc1a84d7`/OID2100197/同 PG cluster7694897083368259627，专属端口18267、700/600 目录与文件、严格 dbfilter/独立 filestore、loopback Python 网络 guard、SMTP127.0.0.1:1、cron0。新库 CREATE1，安装0，升级0，Odoo shell1，最多同时两个独立 ORM backend，Firefox0，GDB0，sudo0；业务 COMMIT7/授权8，其用途依次为 fixture、A批准、B实退、C1日结、C1后续实退、C2日结、C2解锁/更正/重结。旧事故 OID2056451、原33座 S10 历史库、C1 OID2100125/R1 OID2100126/R2 OID2100176及原 filestore/log/core/volume/备份均未清理或写入。

## 账、款、日结和权限回源

新库只读 SQL：原生 `account.move` 11 条全部 posted 且每张借贷余额0，其中3张 100 发票、2张退款贷项合计55、6张原生付款/调整分录；`account.payment` 3笔 inbound 共300（10月13日两笔、10月14日一笔），2笔 outbound 共55（10月14日、同一 card journal），原生付款所连 move 均 posted；`account.partial.reconcile` 5条为100/100/100/25/30，总355。退款最终状态一笔 approved20（实际0），两笔 done25/30。10月13日旧现金日结 gross100/refunded0/pending0，财务解锁但原金额未改；同日微信重结 gross100；10月14日前台 card close gross0/refunded0/pending30，后续经理实际退款不回填这份已确认快照。重分类调整分录为不同科目的借100/贷100，原现金付款未覆写、亦没有错误的 cash outbound。本批 S05 发布价 100 一条仍 published、三个价格快照共300；新库双仓、全局多仓/多库位/价目功能组仍开启，但没有对生产数据库配置。

S01 `settlement.refund.approve` 审计共3条，分别为夹具 B/C 两笔预批及 A 真实竞态唯一批准；`settlement.refund.execute` 2条、`settlement.close` 3条、`settlement.reclassify` 1条、`settlement.unlock` 1条。审计属同一合成门店且资金业务由经理/前台两个真实用户操作；第三名医生作为 A 的第二批准者发生40001回滚，无第二笔审批审计。请求人自批确实被拒。更广跨法人/跨门店权限负向本批 **NOT_RUN**，保留既有 C1 证据边界。

合成用户与目录准备阶段 `mail.message` 增至927、`bus.bus`增至30；A 阶段均不增，B 原生收退款消息增3、C1后续退款增3、C2调整增1（新增记录模型为 `account.move`/`account.payment` notification）；`mail.mail`始终0，四组竞争业务 Bus 行数始终30。内部消息不认定为外发。Bus precommit intent 的类型级记录本批未捕获，标 **NOT_CAPTURED**；不能声称消息/Bus 的所有底层成因已归因。PG deadlocks0。

## 证据与后续

[脱敏机器证据](evidence/s10-fc1/verification.json)由只读 SQL 审计脚本生成；包含阶段计数、真实两 backend/时间、资金与原生凭证摘要及原始私有 ledger/timeline/log SHA，不含患者、密码、通知正文、邮件地址或 session token。原始日志、完整 actor ledger 及数据库仅保留在700/600私有新库目录。静态 `py_compile` PASS、源模板/身份预检 PASS；只读 SQL 审计 PASS。仅这些真实提交场景可称本批 Odoo 子路径通过，完整 S10-T01—T16、旧 Native 根因、生产财税/渠道政策、Firefox/PDF/全 S08/S09 联调均未因本批解除阻断。

集团多仓/多库位政策已 `POLICY_APPROVED`，S05×S07候选为 `ACCEPTED_FOR_CONTROLLED_S10_INTEGRATION`；**正式生产集团组未配置**。S10 技术及生产继续 BLOCKED，Native 旧 SIGSEGV 根因 UNKNOWN，S11 未启动。请 GPT 独立复核本批有限结果和明确 NOT_RUN 项后裁定后续边界；本批不自行再开第二 shell、改产品、改 Project/Issue 状态、合并或部署。
