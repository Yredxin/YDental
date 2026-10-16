# YD-N1 R1 S10-P0-05：来源 config 授权哈希门禁 BLOCKED

本批在 CREATE/HTTP/Firefox/业务 POST 全部为 **0** 时停止，未进入 DOM 离线验证、完整来源 SQL 核验或真实 Web。唯一授权为 [#34/6206097763](https://github.com/Yredxin/YDental/issues/34#issuecomment-6206097763)，上批 GPT 复核为 [6206056107](https://github.com/Yredxin/YDental/issues/34#issuecomment-6206056107)。S10 整阶段技术与生产仍 BLOCKED；#34 OPEN，#35 OPEN/0 评论、S11 NOT_STARTED。

## 实际阻断

正式授权指定的 OID2100320 来源 `odoo.conf` SHA256 与实际文件不相等，而且授权值仅有 **62** 个十六进制字符：

|依据|config SHA256|
|---|---|
|本批 GitHub 正式授权原文（62位）|`578a1304e65dab36440c6e51374276903d7b9ba989e4b75697c1fb9ae62abc`|
|实际文件、原 marker、P0-04 固定机器索引（64位，三者一致）|`578a1304e65dab36440c6e51374276903f9d7b9ba989e4b75697c1fb9ae62abc`|

授权值在 `...74276903` 后缺少 `f9`。这是正式授权与现场/封存证据的哈希冲突，**不能据此断言来源配置被修改**，也不能自行用封存值替换授权值继续运行。本授权第二节规定来源 OID/marker/config 等无法对上时立即 `BLOCKED_PREFLIGHT`、CREATE/HTTP/Firefox/POST 全0，因此本次执行采用硬停止。

最初新建的 P0-05 snapshot/control/CLI 草稿，在首次 `authority()` 的来源 config 比较处抛出 `AssertionError`。该调用发生于 `capture()`、SQL、`source_gate()` 以及所有运行动作之前。三个草稿原字节和失败记录保存在权限700的 `.local/s10-p0-05/`，未改旧脚本，不把未完成草稿交付为可执行窗口。仓库仅新增一个只读预检回执脚本、本文档及脱敏 JSON。

## 实际核验与限制

origin 为 `https://github.com/Yredxin/YDental.git`；原分支 `codex/s10-settlement-finance-r1-20261013` 本地/远端起点均为 `8802bfee708bb854ac4ef1599796ee1f958db6d6`，Odoo20 core 为 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；开始时工作树干净。GitHub API 完整取回 #23 正文/3评论、#34 正文/190评论、#35 OPEN/0，私有保存完整响应；本次授权和上批授权/预检/补充/交付/GPT复核已核对。再次 GET 本次授权及末条评论确认没有后续并行授权；逐条 body SHA/ID 保存在脱敏索引。

实际来源 marker SHA 为 `8afd6122428c723fafa597536c64f146b5b5a339bbb866229d8660f648173f29`，匹配正式授权；marker 内来源身份为 OID2100320。P0-04 `blocked.json` SHA `1738cbd133eda97234ab621f4bc622e5301b8cbaa9330a958e94e9d97b463e1a`、`business-before-after.json` SHA `5b99aa655057a3e54c06aefbb17aa9d9e552cac4ea69940931412b96873c26a7` 均匹配正式授权。四个历史库的 config/marker 文件只读 SHA 和 marker OID 均记录于 JSON；没有连接这些数据库，没有在旧库启动 Web。**完整643表/265受管表/schema/QWeb/filestore及实时 PG OID/活动连接/经济签名核验 NOT_RUN**，不把文件匹配或旧证据冒称本批完整来源门禁 PASS。

静态查阅固定产品源码确认 `_workbench()` 每张本店 invoice 写 `invoice_view`，`_operate()` savepoint 包含 mutex、业务与 receipt，`_unlock()` 对非当前门店记录抛出 AccessError；没有改产品。稳定 form 引用和每次 GET 审计绑定均未完成验证，不能申请其通过。

## 结果及绝对预算

|分类|本批结果|
|---|---|
|HISTORICAL_REAL_WEB_REFUND14_REJECT|仅保留历史证据，绝未重发|
|HISTORICAL_P004_USER10_DENIAL|仅保留历史证据，绝未重发|
|NEW_READONLY_P004_SOURCE|PARTIAL：config/marker 文件核验；正式 config 哈希门禁 FAIL；完整 SQL/filestore NOT_RUN|
|NEW_USER14_CROSS_STORE_DENIAL|NOT_RUN，无 intent/POST|
|NEW_USER6_REAL_WEB_UNLOCK9|NOT_RUN，无 intent/POST|
|BOUND_INVOICE_VIEW_AUDIT|NOT_RUN|
|NATIVE_FINANCE_UNCHANGED|本批未重新 SQL 核验；未启动任何业务进程或写入|
|SIMULATED_PASS / DOM 正负例 / Odoo20 CLI parser|NOT_RUN，不挪用上批模拟|

CREATE **0/1**、HTTP **0/1**、Firefox **0/1**、user14 跨店 unlock9 POST **0/1**、user6 合法 unlock9 POST **0/1**。user10、任何 refund_reject、新收退款/贷项/出账/再日结/库存写、upgrade/init/install/prepare/shell、sudo 全 **0/0**。登录/切店 POST 也为0。未创建计划目标 `ydental_s10_test_20261016_p005_b7e42a91`，无新 OID/HTTP/Firefox PID；计划端口18288未使用。失败前置条件不成立，**未发表 CREATE 前检查点**。

## 验证与交付

执行 `../.venv/bin/python -B scripts/s10_p0_05_preflight.py`，exit0，仅运行文件读取、Git只读核对和生成不可覆盖的 `BLOCKED_PREFLIGHT` 回执；此 exit0 表示阻断记录成功，**不是业务或来源门禁 PASS**。脚本不含 SQL、CREATE、Odoo/Firefox 启动路径。脱敏机器证据为 [blocked.json](evidence/s10-p0-05/blocked.json)，包含正式/实际哈希、历史文件身份、完整评论哈希索引、未执行草稿 SHA、逐项 NOT_RUN 与预算。

只正常前进提交/推送原分支，并在 #34 发布 BLOCKED 复核申请、API 逐字读回后 STOP。须由 GPT 独立复核此正式授权哈希差异并明确修正后续授权；本批不自行纠正授权、续测、启动 P0-06/S11、修改产品/核心/Project/Issue状态、合并/强推或部署。
