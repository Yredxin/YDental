# S10-E2E-W5-RO1：只读 SQL 查询合同阻断

## 结论与范围

**`BLOCKED_READONLY_SQL_QUERY_CONTRACT`。** 本批没有完成授权要求的 W5 目标库独立只读账务核验，故不申请 `W5_RO1_READONLY_ACCOUNTING_EVIDENCE_LIMITED_TECH_PASS`。原 W5 浏览器 exit1、`browser-complete.json` 未写、`final_audit` NOT_RUN 均保持原结论。S10 技术及生产继续 BLOCKED，#35 S11 未启动。

唯一授权为 [#34 RO1 6187934504](https://github.com/Yredxin/YDental/issues/34#issuecomment-6187934504)。通过 GitHub 连接读取 #23/#34 当前正文及所有有效评论、#35 OPEN/0，并重点核 [W5 Codex 交付](https://github.com/Yredxin/YDental/issues/34#issuecomment-6187504862)与 [GPT 复核](https://github.com/Yredxin/YDental/issues/34#issuecomment-6187844624)。原分支、本地与远端 HEAD 均为 `287881a824e9a18dd637522c570f74df139078f9`，起点工作树干净、无冲突；Odoo20 core 固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。只新增 RO1 脚本、报告和证据，未改 W5 原交付、产品或 Odoo core。

## HISTORICAL_REAL_WEB_EVIDENCE

W5 原 9 文件和其中 6 脚本 SHA256 与 [W5 固定机器证据](evidence/s10-e2e-w5/verification.json)及 GPT 的 9/9 复核一致；私有 27 份原始证据逐一与固定索引匹配，清单和 SHA256 收于 [RO1 预检](evidence/s10-e2e-w5-ro1/preflight.json)。W4 来源 `ydental_s10_test_20261015064000_d41e7b62` / OID2100301 和 W5 已付款目标 `ydental_s10_test_20261015073500_e50f4a71` / OID2100310 的 marker/config 哈希均与 W5 交付一致。原 intent→sent→HTTP303 response→observed 顺序为现金500、240各一次；原快照为 invoice1 posted740、余额740→240→0，付款1/2为500/240，第二笔后状态均 `reconciled`。这些是**旧 W5 证据**，本批没有重新执行 Web 动作或收款。

固定 Odoo20 `account.payment` 状态字段在 `addons/account/models/account_payment.py:37` 列出 `paid` 与 `reconciled`；其 `_compute_state` 在约第495行按付款分录流动性行剩余额，及已核销发票的付款状态，使 `paid` 转为 `reconciled`。发票 `_compute_payment_state` 在 `addons/account/models/account_move.py:1265` 结合应收核销与付款匹配判定。故 `reconciled` 可以是合法终态，但单看状态字符串不能证明金额、凭证、partial、AR 链接正确。原 `scripts/s10_e2e_w5_browser.py:69` 只允许 `in_process` 或 `paid`，在第二笔资金已经提交且快照落盘后拒绝 `reconciled`；原离线 Fake 在 `scripts/s10_e2e_w5_offline.py:90` 固定 `in_process`，遗漏真实终态。这说明旧判据为何失败，不修饰旧失败，也不将旧 post-stop 快照当成未执行的 final_audit。

## SIMULATED_PASS 与预检

新增 `scripts/s10_e2e_w5_ro1_verify.py` 对固定旧快照做离线正例，并以 12 个内存负例检验未过账、错现金日记账、错 partial 金额或目标 AR、重复付款、错金额、错发票、分录不平、缺凭据和缺审计等情况。结果为 `SIMULATED_PASS`，不代表数据库实测。脚本 SHA256 `e1326cf1e24b5ff712281ebe398ace447e58b8873dad88203a331201b972062d`；离线预检 SHA256 `6142e41d421025e83a40cb19de8d0da2c8f9f841edd48926199d00a8b010ff45`。SQL 前已在 [#34 预检 6188488655](https://github.com/Yredxin/YDental/issues/34#issuecomment-6188488655)发表查询合同和预算，并通过 GitHub API 读回。

## NEW_READONLY_SQL：原样失败与停止

唯一 SQL 窗口在 W4 来源库建立 **1 个**显式 `REPEATABLE READ READ ONLY` 连接，`SHOW transaction_read_only` 返回 `on`，进程内 OID/cluster 断言已继续通过。随后执行模块元数据及 S01 审计 SELECT；在读取 S10 cashier 行时，脚本查询了不存在的 `ydental_actual_utc`：

```text
psycopg2.errors.UndefinedColumn: column "ydental_actual_utc" does not exist
HINT: Perhaps you meant ... "ydental_actual_at".
```

产品模型静态字段确为 `ydental_settlement/models/ydental_settlement_payment.py:19` 的 `ydental_actual_at`。这是**新增 RO1 脚本的查询合同错误**，不是已证实的产品账务缺陷。异常发生在任何 W5 目标连接前；来源连接经 `finally` 关闭。先前成功 SELECT 的值未写入新证据，不能当成完整来源复核。按照授权“异常即 STOP”，未修改检查点后的脚本、未补充检查点、未重试 SQL；`read-only-sql.json` 未生成。

因此本批 `NEW_READONLY_SQL` 对 W5 invoice/payment/posted move/partial/S10 receipt/S01 审计的逐 ID 验证均 **NOT_RUN**；W4 38 表最终签名与 filestore 复核亦 **NOT_RUN**。旧 W5 对来源和稳定31表的检查仅保留为 HISTORICAL_REAL_WEB_EVIDENCE，不能升级为 RO1 独立结论。原始异常、资源账本和未执行项见 [脱敏阻断证据](evidence/s10-e2e-w5-ro1/blocked.json)。

## 资源及交付边界

本批 CREATE0、业务写0、SQL DDL/DML0、付款 POST0、Odoo HTTP/CLI/shell/install/upgrade0、Firefox0、sudo0；新 SQL 来源连接1、W5 目标连接0。未修改 Issue/Project 状态、历史库/filestore/marker/原始HTTP、旧脚本和旧证据。需 GPT 独立复核本次查询合同阻断和后续只读边界；本批交付后停止，不自行继续。
