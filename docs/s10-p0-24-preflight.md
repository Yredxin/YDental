# [CODEX] S10-P0-24 单字段双客户端只读采集预检

唯一授权6230858409 / READ_ONLY_DIAGNOSTIC，P023裁定6230830175保持；不是业务恢复。父HEAD ba536bc2203caee6f1681fd7aaac23a5b2a33704；原分支codex/s10-settlement-finance-r1-20261013、origin=https://github.com/Yredxin/YDental.git、唯一工作目录及core只读f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb匹配。初始本地/远端HEAD一致、工作树干净；#23/#34正文及全部3/270有效评论完整API读取，旧正文/264评论与P023存档逐字相同，四条P023流程评论与私有正文相同，仅再新增裁定/本授权。#35 OPEN/0；没有已有P024 CODEX预检/交付或并行记录。

固定执行提交 **c88f5606da4057d2fbae0997caeddeeb4e90af3c** 已正常线性推送；三个新脚本仅本批路径，旧产品/脚本/模板/证据/FAIL不改：

- scripts/s10_p0_24_collect.py SHA256 faeaf74b3be3a3720c63c66839883ca096acbd31e3254893e79f3d8fefcfebc6
- scripts/s10_p0_24_contract.py SHA256 59f16d63b27e74b5b1b8e9614fe2da6e3577598316b4ba6273e0e95043230a37
- scripts/s10_p0_24_offline.py SHA256 60a94c7af0ee98b0792aab7324e5c9e469ce23eb129ced7113386fa90912a3fd

冻结docs/evidence/s10-p0-24/freeze.json SHA256 **fdaa8b0e0b943489ac4c5d2f7a0522ba4f17a78e6ff5ec18103124e0538ccf2b**，13项SHA含代码、SQL/输出合同、纯文件测试、工具版本记录、既存解释器/psql/psycopg2扩展、本地私有凭据引用及唯一旧字段基准。SQL字面完整保存于[SQL-contract.json](https://github.com/Yredxin/YDental/blob/c88f5606da4057d2fbae0997caeddeeb4e90af3c/docs/evidence/s10-p0-24/SQL-contract.json)，SHA256 bb19b69039fc1b2c67e1430ac93afa4d2683c929a0f24ad81980abd9f2a68dcd。不重新核P02347份大文件或旧业务；基准仅GPT已独立复算的2022字节arch_prev-tail.txt，SHA776c4257a3567c92aa3e46aa5dc2c4e5a714989be88ab59714452dfeb4042664。

唯一连接目标：host127.0.0.1/5432、既存私有凭据角色odoo，**ydental_s10_test_20261017060000_22b0cafe / OID2144126 / cluster7694897083368259627**。本批新私有目录.local/s10-p0-24模式0700；凭据只私有读取../odoo.conf，引用哈希私有冻结，缺失/漂移STOP，不改密码/权限。psql用新私有0600 PGPASSFILE；密码不入argv、公开日志或Git。禁P021源、W5及其他旧库，维护连接0/CREATE0。

既有工具文件/版本已核，无DB能力探测或安装：实际psql为/usr/lib/postgresql/18/bin/psql 18.6（/usr/bin/psql原包装器亦指向既有18）；../.venv/bin/python为3.12.15，psycopg2 2.9.9，compiled/runtime libpq180006。二客户端可能共用libpq/主机，不称完全独立硬件路径。选择既有内置pg_catalog.sha256(bytea)/convert_to/encode，原固定P016合同也使用此无扩展形式；当前服务器版本由正式身份SELECT记录，若函数/权限不符则STOP，不安装扩展、换算法或补查询。

**预算与SQL顺序**：最多2连接，psql一次→Python/psycopg2一次，严格顺序、不重连/不循环重试。每条连接的显式SQL最多6条：BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY；SHOW transaction_read_only；SHOW transaction_isolation；身份SELECT；目标SELECT；ROLLBACK。两条SHOW必须on/repeatable read。连接建立即用PGOPTIONS default_transaction_read_only=on、statement_timeout5000、lock_timeout5000、UTC/UTF8，连接超时5秒、每语句5秒、每客户端总30秒（25秒主体、余量仅ROLLBACK/CLOSE）。启动参数不是SET语句。Python autocommit=True后显式BEGIN，避免隐式BEGIN；psql -X -w -q -A -t -P pager=off -v ON_ERROR_STOP=0 -v ON_ERROR_ROLLBACK=off -v FETCH_COUNT=0 -v AUTOCOMMIT=on -h127.0.0.1 -p5432 -Uodoo -d精确库 -f-，不读rc/交互口令、不自动savepoint/cursor。sslmode=disable只限该loopback连接参数，不改服务配置。

psql由控制器每次仅派发一条冻结SQL及ERROR/SQLSTATE原生echo分隔标记；原stdout/stderr流先写新文件、flush/fsync，再判定。身份或任何SQL错误后只尝试ROLLBACK并关闭，不派发后续目标/第二客户端。Python同样原字节/返回类型先保存，再解析身份；最终原ROLLBACK必须返回，conn.close记录。超时/断连则保留实际可得输出、明确不能证明的清理状态，停止，无第三入口。每次intent/派发/返回/错误/PID/时刻及实际语句均保存；一次性run-intent和目录独占创建阻止重放。

身份SELECT仅必要current_database/OID/cluster、backend、server_time/transaction_start/snapshot、RO/isolation、服务器/客户端编码/版本；准确身份通过才目标SELECT。目标只FROM public.ir_ui_view WHERE id=929 AND key='account.portal_my_journal_mail_notifications'，不加LIMIT掩盖重复，不扫描替代记录。预期实际物理tableoid2122563、表ir_ui_view（或带public限定）、arch_prev类型text且非NULL；一次目标SELECT返回id/key/tableoid/表名、NULL/类型、arch_prev原文本、字符数、UTF8字节数、**同语句服务器**convert_to→encode hex及sha256摘要；active arch_db只返回其::text的UTF8服务器SHA及类型/NULL，另write_uid/write_date，不返回active正文/其他行。预期字段2022字节，完整目标JSON返回上限65536字节、字段上限8192字节；不存在/重复/超限保留实际已得证据并停止，不换记录。

保存层合同：psql保留原stdout/stderr及单语句stdout；Python目标SQL返回类型为text，先保存驱动返回Python str类型、即时UTF8字节及描述OID/摘要，再JSON解析。这些不是网络抓包或驱动解码前协议字节。服务器摘要始终来自本条目标SELECT，客户端sha另列比较，不冒充服务器。严格JSON拒重复键、字面控制字符和非有限数；显式UTF8、allow_nan=False序列化，exclusive x、flush/fsync、关闭后重开保存读回bytes/sha及语义比较。每层完整值/差异先私有保存再判断；多个落盘副本不是独立观测。

纯文件预检已实际exit0，9项涵盖正常、v→6、字面0x1F、正常转义、重复键、截断、模拟写后读回不一致、非有限解析/序列化。模拟读回故障和合成server字段清楚标STATIC_FIXTURE，不是服务端实测、物理故障或业务MODEL测试；没有导入旧native/capture主程序。三个当前脚本compile通过，DB连接仍0。

跨两客户端逐项比较文本、长度、UTF8 hex、服务器摘要、真实类型/对象、active摘要及write元数据；各自backend/时间/snapshot原样保留。与P023基准字段SHA另列，只能给“当前有限观测一致”“采集层间不一致”或“无法完成”。psql层已不一致/身份SQL失败则第二入口NOT_RUN；psql内部一致但字段不同历史基准时，只按计划的第二入口核当前差异，不推断历史修复。结果不能说明长期稳定、数据库整体完整或过去故障层。

仅当当前字段全文等于GPT已复算的P023正常模板或已公开v→6那个一字符变体，才公开完整字段/hex/服务器JSON及原接收文本；否则完整返回只留私有，公开长度/摘要/差异状态，不上传患者、会话、配置、口令/token或其他行。原0x1F所在其他行不查询。公开新增结果仅docs/evidence/s10-p0-24/*，报告docs/s10-p0-24-*.md；凭据材料及完整异常返回不入Git。

本条REST GET全文逐字相等保存后才执行：`PYTHONDONTWRITEBYTECODE=1 ../.venv/bin/python scripts/s10_p0_24_collect.py`，仅此一次控制运行；随后`PYTHONDONTWRITEBYTECODE=1 ../.venv/bin/python scripts/s10_p0_24_offline.py seal`只做本批文件封存。业务DML/COMMIT、CREATE/DROP、Odoo/Registry/shell、业务HTTP/RPC/浏览器、scope、文书、收退款、日结、PDF生成/下载、权限变更、安装升级、产品/core修改及sudo/OS-PG运维/Docker/网络/硬件专项全部0。GitHub流程API/本批纯文件/Git操作除外，Issue/Project状态0写。

完成或无法完成均正常线性提交推送新增材料，给精确SQL/连接/退出码/未运行和数据层边界；旧失败/快照/manifest/字节不改。正式交付REST逐字读回后立即STOP，等待GPT独立复核；S10/T12及五组状态不变，不自动恢复五组/P025/S11、合并或部署。
