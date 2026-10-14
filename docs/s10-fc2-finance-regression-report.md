# S10-FC2 退款终态与反向日结定向回归

## 裁定范围

依 [#34 唯一正式授权 6171419484](https://github.com/Yredxin/YDental/issues/34#issuecomment-6171419484)执行，任何 CREATE/Odoo 前已发表并 API 逐字读回[强制预检 6171566556](https://github.com/Yredxin/YDental/issues/34#issuecomment-6171566556)。本批仅一个全新合成库、一个 Odoo shell 主进程、两组真实双 ORM/PostgreSQL backend 交错、11 次预列业务 COMMIT。PID2834590 exit0、signal11=false；原 Native 崩溃根因继续 UNKNOWN。本批无产品代码修改，也不重复 FC1 已通过且无新变量的先行分支。

**FC2-A/C 的指定事务先后竞争 = `CONCURRENT_PASS`（胜者提交、败者 SQLSTATE40001 整笔回滚）；FC2-B/D 的指定终态及实际渠道业务 = `ODOO_PASS_COMMITTED`/合法负向 `EXPECTED_REJECT`。** 这些仅是本批有界子项；S10 整体技术及生产仍 BLOCKED，完整 T01—T16 没有自动通过。

| 子项 | 真实 Odoo 结果 | 限定说明 |
|---|---|---|
| A 取消先行 | 前台不同于请求经理，以受控合成“人工核实未付款”证据取消20并提交；经理实际执行第二 backend 在未提交期间开始，首提交后收到 `SerializationFailure/40001`并 ROLLBACK。新cursor见唯一 `cancelled`、实际退0、outbound/贷项/partial 增量0；同款可用额度15→35仅释放20一次。之后新key execute `access_denied`，重复取消 `refund_state_invalid`。 | 40001不等于第二动作成功；外部银行/微信未接入，仅合成线下未付款证明。 |
| B 完成态与恢复 | 合成实际退款25一次，posted outbound25、posted credit25、partial25；同key同参数回执 `already_accepted`且资金/审计计数不增。不同key执行、完成后取消、`verified_not_paid=True`恢复及倒退unknown均服务端拒绝。另两笔20分别真实提交为 `unknown`/`failed`；无核实的recover/cancel四次均拒；独立财务审核角色在合成核实未付款后 recover→cancel，各释放20；最终该100元入款只保留已实退25，可用75。 | 只有现有服务要求的证据字段及原生账状态已测试；没有真实外部付款状态核验。 |
| C 实退先行、同执行人日结 | 前台为昨日 card 收款员、今日退款执行者和当日 card 日结人，两个不同真实会话/后台。实退30先持锁未提交，另一 backend 的同人同日同渠道 close 启动等待；实退提交后 close 得40001并 ROLLBACK，新cursor仍只有昨日 close，且退款付款/贷项 posted。新独立事务合法今日 close 为 gross0/refunded30/pending0/net−30；昨日 card close 保持 gross100/refunded0。 | 双 backend 重叠及40001已证，具体 `pg_locks` 等待链未采集；没有宣称所有锁序均通过。 |
| D 更正后同款微信实退 | 昨日真实微信合成来源误录 cash100，先确认 cash 历史 close。只有 `settlement:write` 而无 `finance_approval` 的医生 unlock 得 `access_denied`；有权前台在锁定时直接 reclassify 得 `day_closed`。前台依法解锁，真实调整凭证不同科目借100/贷100且 posted，经理旧日微信重结 gross100；原现金 inbound 仍在 cash journal、旧 cash close 数值保留并标 unlocked。错日实退尝试以 `refund_time_invalid` 拒绝。**同一笔**原付款在更正记录之后按真实微信凭据实际退款40，微信 outbound posted、现金 journal outbound0；今日经理微信 close gross0/refunded40/pending0/net−40，旧日 cash/微信 close 金额不回填。 | 只验证“原本真实微信而旧标签错误”的纠正与同渠道实退，不构成任意跨渠道退款政策批准。 |

## 版本、用量与保护

原分支固定起点 `7ee2c5e091fa1d29bd01e493b07902d2827f4a35`；Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；历史 S10 product/test `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`/`255b48f54495eb99638af8ffc824771b9a5af3e7`，实际 S10 服务 blob `d4d4363ab2dfdd982606f464e5b66c240744fac6`，S07 服务 SHA256 `df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b`。GitHub API 开工时 #23/#29/#31/#34 全部有效评论 3/7/8/105、#35 OPEN/0，最新 #34 评论为本授权。产品、固定测试、旧 runner、ACL/manifest/schema 与 core 均未修改。

纯模板 `ydental_s10_test_20261014044700_4f6a8d2c`/OID2100080 经只读复核：92 installed、70 系统附件/124 安全 filestore 文件逐 SHA、主要业务表0、活动连接0。唯一新库 `ydental_s10_test_20261014152000_fc2a7d31`/OID2100212/原 cluster7694897083368259627，专属配置SHA256 `f6ff53e139cca390fc2edec7ab600f5505b2e0cd166d246080d2510b9c07553d`、markerSHA256 `f9ee208c81856bf8a8f6769556790420786c4b3b4f16085cd8413e7323daad61`。CREATE1、安装0、升级0、Odoo shell1、同时独立 ORM backend最多2、业务 COMMIT11/上限12、Firefox0/GDB0/sudo0；独立 data_dir/filestore、严格 dbfilter、loopback、SMTP127.0.0.1:1、cron0。原事故OID2056451/33历史S10库、C1三代OID2100125/2100126/2100176、FC1 OID2100197及旧 filestore/log/core/volume/备份没有清理或写入。

11次 COMMIT 在私有 attempt ledger 事前列名：fixture；A取消；B实际完成；B unknown/failed；B受控恢复/释放；C实退；C同执行人日结；D旧cash日结；D解锁/更正/旧微信重结；D同款微信实际退款；D今日微信日结。第12笔授权余量未用。A/C 主后端与第二后端不同，第二 actor 在首事务未提交时已经启动且等待，提交后分别抛 SQLSTATE40001；没有自动重试、第二 Odoo shell 或继续碰运气。原日志SHA256 `7206b35182a19b8e364ec3a973b1a4233bb38413e1700d93cc0c1df9eaa6e85b`，私有日志/ledger目录700、文件600。

## 独立只读账、权限及副作用核对

新库只读 SQL 核对：3张 posted invoice共300，3笔 inbound共300，3笔 outbound共95（card25+30、**wechat40**），3张 posted refund credit共95；6条 `account.partial.reconcile` 为100/100/100/25/30/40（合计395，包含退款核销，**不是395实收**）。13张原生 `account.move`均 posted、逐张借贷平衡；现金 journal 无 outbound，D旧 cash inbound 仍在原 journal，独立 posted 调整分录借100/贷100。六笔申请最终为3 cancelled（20/20/20）、3 done（25/30/40），请求者与审批者不同，执行者/门店/法人按上述场景一致。历史及今日五张 close 的实际存储值与表中金额一致。更正记录时间早于 D 实际退款 UTC，D 40 元 outbound 日归今日。

S01审计：refund request6/approve6/cancel3/execute3/unknown1/failed1/recover2、close5/unlock1/reclassify1；同一合成门店。原生账户只有同一合成公司。经理与前台均有本店 `settlement:write`、`finance_approval:write`，医生只有 `settlement:write`，越权解锁真实拒绝且无额外审计/资金。新库集团多仓、多库位、价目三组由管理员显式开启，S05已发布价格100和3个快照仍在，仓库2座；**没有改生产集团组**。

合成人员/目录准备后 `mail.message=927`、`bus.bus=30`、`mail.mail=0`；后续原生资金/调整消息最终937，业务阶段 Bus 行数均30且 mail.mail 始终0。每次 COMMIT 前读取 `bus.bus.values` precommit slot，11个观察点均0；这只是该 slot 当时的意图计数，**不证明所有可能的 Bus 生成路径不存在**，也不将内部消息当外发。PG deadlocks0。

[脱敏机器证据](evidence/s10-fc2/verification.json)含两组后台时序、13条负向分类、分阶段资金/消息计数、只读原生账与审计摘要及私有原始 ledger/timeline/log SHA；不含患者姓名、密码、邮箱、通知正文、session token。静态 `py_compile` PASS、源模板/身份预检 PASS、离线 AST/额度模拟仅 `SIMULATED` exit0、真实 shell exit0、独立只读 SQL 核验 PASS。原旧 Native SIGSEGV未在此批发生，不等于根因已修复；FC2未运行完整S10 T01—T16、Firefox/PDF/翻译、S08/S09全回归或真实外部渠道。政策 `POLICY_BLOCKED` 只适用于未授权的任意跨渠道/生产财税方案，本批 D 纠错正例不受其阻断。

集团多仓/多库位政策仍为 `POLICY_APPROVED`，S05×S07候选仍为 `ACCEPTED_FOR_CONTROLLED_S10_INTEGRATION`；生产集团组尚未配置。S10技术及生产继续 `BLOCKED`，Native SIGSEGV根因 `UNKNOWN`，S11未启动。请 GPT 独立复核以上有限结果与剩余 S10 范围；本批不自行解除状态、修改产品、改 Project/Issue、清理旧库、合并或部署。
