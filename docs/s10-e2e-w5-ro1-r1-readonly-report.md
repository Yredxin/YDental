# S10-E2E-W5-RO1-R1：既有 W5 付款库只读账务收口

## 裁定申请与边界

本批申请 **`W5_RO1_R1_READONLY_ACCOUNTING_EVIDENCE_LIMITED_TECH_PASS`**，仅限既有合成库两笔已提交 Web 现金500/240的原生账务证据。S10整阶段技术及生产继续 BLOCKED；本批没有新交易、Web 回放或产品更改。唯一授权为 [#34 RO1-R1 6188802614](https://github.com/Yredxin/YDental/issues/34#issuecomment-6188802614)，固定起点 `877b94653e89234ba06c9086d0cb472458188ba1`，原分支 `codex/s10-settlement-finance-r1-20261013`，Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。开工时本地、远端、origin、工作树和核心身份一致，#35 OPEN/0，#34 最新为本次授权。

GitHub API 已读回 #23/#34 当前正文与全部有效评论、#35 状态，重点核 [RO1 阻断交付](https://github.com/Yredxin/YDental/issues/34#issuecomment-6188645630)及 [GPT 复核](https://github.com/Yredxin/YDental/issues/34#issuecomment-6188730055)。SQL 前 [#34 R1 预检 6189141033](https://github.com/Yredxin/YDental/issues/34#issuecomment-6189141033)已发表并 API **逐字相同**读回，检查点、脚本与预检 SHA 锁定。

## HISTORICAL_REAL_WEB_EVIDENCE

W5 原固定9份文件、RO1 原固定4份文件和 W5 私有27份证据再次逐件核哈希一致，W4/W5 marker/config 原 SHA 一致，原始文件未改。历史真实 Firefox 表单各一次 POST 现金500/240，均 HTTP303；旧快照依次为发票1 posted740、余额740→240→0。旧第二笔后两付款状态 `reconciled`，浏览器脚本 `validate_money()` 因只允许 `in_process/paid` 而 **exit1**；`browser-complete.json` NOT_WRITTEN，原 `final_audit` NOT_RUN。上述为旧证据，哈希见 [预检](evidence/s10-e2e-w5-ro1-r1/preflight.json)与[本批索引](evidence/s10-e2e-w5-ro1-r1/verification.json)，不得称原 W5 全流程 PASS。

固定 Odoo20 `addons/account/models/account_payment.py` 的 `state` 字段含 `paid/reconciled`；`_compute_state()` 按流动性行剩余额或已核销发票状态完成状态转换。`reconciled` 是可能的合法终态，但要结合已过账凭证、金额、应收行及核销关联判断。原 RO1 错查 `ydental_actual_utc`；产品模型 `ydental_settlement/models/ydental_settlement_payment.py:19` 声明 `ydental_actual_at`。本批新增独立脚本，RO1/W5 固定脚本不动。

## SIMULATED_PASS 与查询准入

R1 离线预检从新实际主流程和既有固定只读辅助函数提取 **28条 SHOW/SELECT 模板**，覆盖38表逐行签名查询；对 **42张表、102个必需列** 逐项关联模型源码或关系表声明。新 SQL 使用 `ydental_actual_at`，查询计划中不存在旧错误列；这是**源码合同检查**，不是数据库实际 schema 证据。真实连接后每库先在同一只读事务通过 `pg_catalog` SELECT 验证全部42表/102列，再做业务查询。

历史快照上的核销正例及15个账务负例、完整 W4→W5 断言正例及10个负例、catalog缺列/缺表、两库SQL中断和原件哈希漂移5个门禁场景均为 `SIMULATED_PASS`，不计真实交易。新脚本 SHA256 `7ef4eaabd0ffe27e889435686db1772c0c39be81551496d11382df91352b06c7`，预检 SHA256 `7935c06963017ec68980d4f036259d86e934b106926ade0681eba584bc46fcea`；预检评论读回后没有更改脚本。

## NEW_READONLY_SQL

**唯一窗口 exit0，`NEW_READONLY_SQL_PASS`。** 来源 W4 `ydental_s10_test_20261015064000_d41e7b62` / OID2100301 与已付款 W5 `ydental_s10_test_20261015073500_e50f4a71` / OID2100310 各只开1个连接；实际 `transaction_read_only=on`，事务隔离 `REPEATABLE READ`，语句超时30秒，窗口 **0.302秒**。两库同一 PG cluster `7694897083368259627`，实际 schema 各有合同所需42表/102列，投影哈希同为 `96902710b207c7d73cf7bea822ce56d5cc35c9a8e160b27c5aea2a3471d293b3`。全部查询及断言结果见 [固定只读SQL证据](evidence/s10-e2e-w5-ro1-r1/read-only-sql.json)，SHA256 `ca2a304fae2918ed91005552c65de21dacdc6a18707d01a16bcabe59a0c06c73`。

| 项目 | W4来源实读 | W5付款后实读 |
| --- | --- | --- |
| 发票1 | `out_invoice/posted`，740.00，余额740.00，`not_paid` | 同发票仍`posted`/740.00，余额0.00，`paid` |
| 原生资金 | `account.payment` 0、partial 0 | inbound/customer 付款ID1=500.00、ID2=240.00，均 `reconciled`；无第三笔 |
| 凭证 | 原发票 move1 posted | payment move2/3 分别 posted 500/240，法人1、现金journal8，各借贷相抵 |
| 核销 | 原发票应收line5、借方740 | partial ID1=500：发票line5→付款line7；ID2=240：line5→付款line9；付款行均为同一应收科目5，原发票line5余额0 |
| S10/S01 | 原 bill receipt1、无资金付款 | S10 payment1/2 均店1/患者1/现金/用户5/业务日2026-10-15且仅关联发票1；pay receipt2/3逐笔指向对应原生payment与partial；S01 `settlement.pay` accepted审计ID327/330，用户5/店1 |

S10 `ydental_actual_at` 实读分别为 `2026-10-15 07:52:02.559463` 与 `07:52:03.952418` UTC。receipt2记录500、该次后余额240；receipt3记录240、该次后余额0。来源 W4 的38表逐行签名仍与原 W5 CREATE 前固定签名相同；W5 的31张付款后应稳定表与付款前逐行签名相同；原322条 S01 审计前缀未覆盖，目标现330条。两库仍92个已安装模块、相同模块元数据和安装态结算 QWeb；filestore 各152文件/164附件指针、相同manifest SHA `bd0b0fbad15868bbabb836fa7016a91187bb31c6b9b6d934b2a7a0fe035c4283`。

两库费用ID1—4及价源快照仍分别为600/80/40/20，四个治疗事件与一个检查结果仍 confirmed，五条库存 move 均 done，其中实际发药数量仍1/4/2；退款0、日结0。原发票来源、原价和库存未因付款更改。W5 最终账务同时与旧 `pay-2-observed.json` 快照一致，但本批结论以**新只读 SQL**的逐ID读取和哈希比较为依据；旧快照只用于交叉验证。外部现实现金到账未验证。

## NOT_RUN、预算与交付

原 W5 `browser-complete`、`final_audit`、第二笔正式截图仍未执行/未生成。本批 Odoo HTTP/CLI/shell/install/upgrade0、Firefox/Playwright0、CREATE0、资金POST0、业务或SQL DDL/DML写0、sudo0；没有再次出账、付款、退款、日结或改变历史库。真实患者资金、生产会计政策、S10完整F1—F6/T01—T16、同一次Firefox 23步全链、用户最终效果验收、生产部署均 **NOT_RUN/BLOCKED**。#34应保持 OPEN，#35 S11不启动。

本批新文件仅在 RO1-R1 允许的脚本、报告和证据路径。请求 GPT 独立技术复核上述**限定只读账务证据**；交付后停止，不自动启动其它批次。
