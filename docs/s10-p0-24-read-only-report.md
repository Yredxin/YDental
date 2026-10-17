# YD-N1 R1 S10-P0-24：单字段双客户端只读采集链

结果为 **当前有限观测一致**。两条预先固定的只读连接均完成：服务器同语句生成的字段文本/UTF-8编码/摘要、psql与psycopg2接收、严格解析、显式UTF-8序列化及落盘重开读回一致；字段SHA与P023已采precommit/tail基准相同。结论仅限2026-10-17这两次当前观测，不是历史根因已修、数据库整体完好、长期稳定或业务可恢复。S10/T12及原五组状态仍BLOCKED/NOT_RUN。

依据为 [唯一授权6230858409 / READ_ONLY_DIAGNOSTIC](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230858409)，P023正式裁定 [6230830175](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230830175)不改。父HEAD `ba536bc2203caee6f1681fd7aaac23a5b2a33704`；原分支 `codex/s10-settlement-finance-r1-20261013`、origin、唯一工作目录及core只读 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`核对匹配。初始工作树干净，无本批已有CODEX预检/交付或并行。#23/#34当前正文及全部3/270有效评论API完整保存，与P023旧存档及四条流程正文逐字对照；#35 OPEN/0，Issue/Project状态0修改。

唯一正式预检 [6230985005](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230985005)在任何本批连接前发布，2026-10-17T07:02:42.894620+00:00 REST GET正文逐字相同落盘。正文SHA256 `7318792ddd531aee925f942d5fff9d5dcdd059344fc54d7df51d8c60ea0fbc5c`；`freeze.json` SHA256 `fdaa8b0e0b943489ac4c5d2f7a0522ba4f17a78e6ff5ec18103124e0538ccf2b`。执行提交 **c88f5606da4057d2fbae0997caeddeeb4e90af3c**，13项代码/工具/SQL/输出/基准输入SHA在运行门禁核同，没有冻结后修脚本、改合同或重试。

仅新增三份脚本：

|脚本|执行版SHA256|
|---|---|
|scripts/s10_p0_24_contract.py|`59f16d63b27e74b5b1b8e9614fe2da6e3577598316b4ba6273e0e95043230a37`|
|scripts/s10_p0_24_collect.py|`faeaf74b3be3a3720c63c66839883ca096acbd31e3254893e79f3d8fefcfebc6`|
|scripts/s10_p0_24_offline.py|`60a94c7af0ee98b0792aab7324e5c9e469ce23eb129ced7113386fa90912a3fd`|

既有实际psql `/usr/lib/postgresql/18/bin/psql` 18.6，Python既有3.12.15、psycopg2 2.9.9，compiled/runtime libpq180006；未安装任何工具、扩展或修改配置。/usr/bin/psql是已有pg_wrapper，因此冻结实际18二进制而非运行时另选版本。工具版本核验不连接PG。两个观察客户端可能共享libpq与主机，不能称独立硬件路径。控制器/纯文件工具本身不连接数据库。

唯一数据库为 `ydental_s10_test_20261017060000_22b0cafe`，OID **2144126**，cluster **7694897083368259627**。只查 `public.ir_ui_view` 的 id929、key=`account.portal_my_journal_mail_notifications`；真实tableoid **2122563**、表名 `ir_ui_view`。身份SELECT只读必要的当前DB/OID/cluster、backend、事务时刻/snapshot、编码和版本。目标SELECT无LIMIT隐藏重复，没有扫其他记录或查原0x1F所在行，也没有连接P021源、W5、postgres维护库或其他旧库。

|客户端实际观测|psql|Python/psycopg2|
|---|---|---|
|客户端PID|891514|891516|
|PG backend PID|1454084|1454085|
|事务开始UTC|07:02:43.056292|07:02:43.240855|
|目标SELECT服务器时刻UTC|07:02:43.110259|07:02:43.265921|
|事务snapshot|516783:516783:|516783:516783:|
|SHOW及身份RO/isolation|on / repeatable read|on / repeatable read|
|server/client encoding|UTF8 / UTF8|UTF8 / UTF8|
|服务器版本|18.6 (Debian 18.6-1.pgdg13+2)|同版本|
|显式SQL数|6|6|
|ROLLBACK|原回复成功，SQLSTATE00000|原回复成功，status ROLLBACK|
|客户端关闭|psql进程exit0|conn.closed=True，外层进程exit0|
|客户端完整进程时长|0.085858497秒|0.164798877秒（内部主体0.049137274秒）|

两次相同snapshot字符串只表示可见事务快照相同，不把它当作同一个客户端/同一个采集对象；两个backend与各自transaction_start实际分别记录。没有额外pg_stat_activity尾查；关闭结论采用ROLLBACK原回复、psql退出和Python conn.close证据，不冒称又查询了服务器活动连接。

每客户端六条显式语句准确为 BEGIN READ ONLY/REPEATABLE READ、SHOW transaction_read_only、SHOW transaction_isolation、身份SELECT、目标SELECT、ROLLBACK。合计2 BEGIN、4 SHOW、2身份SELECT、2目标SELECT、2 ROLLBACK，无COMMIT。完整SQL字面及所有intent/returned时刻在 `SQL-contract.json`、各client的process-result及私有events。psql关闭rc/交互口令/自动savepoint/FETCH_COUNT cursor，按一条SQL一条原生ERROR/SQLSTATE分隔符顺序派发；Python autocommit=True后显式BEGIN。没有自动重连、循环重试、第三入口或失败候选。

连接建立即default_transaction_read_only=on；超时设置连接5秒、statement_timeout5000毫秒、每客户端30秒（主体25秒，预留ROLLBACK/CLOSE）。这些由固定启动参数/控制器保证，没有增加额外SHOW语句。两次实际时长均远低于上限，未触发超时。凭据仅来自私有已有文件，psql新PGPASSFILE0600、本批私有根目录0700；没有把密码写入argv或公开文件，没有变更密码/角色/权限。

服务器目标SELECT对同一 `arch_prev` 同语句返回：原文本、char_length、octet_length(convert_to(...,'UTF8'))、encode(convert_to(...),'hex')和encode(sha256(convert_to(...)),'hex')。这些实际服务器值均保存在返回对象里；客户端另外计算摘要比较，不能以客户端摘要冒充服务器摘要。仅选内置函数，没有CREATE EXTENSION或自定义函数。active `arch_db`只选其`::text`转换UTF8后的SHA256、类型与NULL标志，没有把active正文返回客户端。

|字段/元数据|两次当前结果|
|---|---|
|arch_prev类型/NULL|text / False；客户端解析str|
|字符数 / UTF8字节数|2022 / 2022|
|服务器同语句SHA256|`776c4257a3567c92aa3e46aa5dc2c4e5a714989be88ab59714452dfeb4042664`|
|客户端字段SHA256|同上|
|服务器UTF8 hex / 客户端UTF8 hex|完整4044个hex字符逐值相同|
|P023正常precommit/tail基准|字段全文/SHA相同；本次为v，未观测到旧6变体|
|active arch_db类型/NULL|jsonb / False|
|active arch_db服务器SHA256|`39bad19dad71ac0b68be0150c75ac213bb9a0560a46fde8bf91f495a5cec8a92`|
|write_uid / write_date|1 / 2026-10-17T04:24:39.404667，两次相同|

active摘要的输入是JSONB的服务器`::text`字节，不是arch_prev，也没有客户端active全文可重算。未重新核历史active字段或财务/库存状态；本批没有业务写入，不把这一点扩张成全库经济保全验证。

每层的原始输入先独占新文件保存，flush/fsync，再做判断：

|层|证据与范围|
|---|---|
|服务器表达|`server-generated-envelope.json`包含上述SELECT的文本/hex/摘要/类型/时刻；该文件本身是客户端对服务器对象的重序列化，不是网络原字节。|
|psql接收|私有stdout.raw/stderr.raw原字节及流入内存SHA与落盘SHA核同，6条单语句stdout/分隔符保留；公开client-received-target.utf8原目标stdout为6986字节，含行尾LF。|
|Python驱动返回|先存目标column的原Python str、即时UTF8字节/摘要和description type OID25，再JSON解析；公开client-received-target.utf8为6985字节，无psql行尾LF。不是驱动解码前的协议字节/抓包。|
|解析字段|strict JSON拒重复键、未转义C0与非有限数，完整解析对象和2022字节字段留存。身份/目标原数据均先落盘再判定。|
|序列化|每客户端显式UTF8/allow_nan=False、sort_keys、indent生成7034字节serialized.json；flush/fsync关闭再重新打开，保存serialized-reopened.bin及字节/语义结果。|
|差异判定|每客户端13项层间/事务对应核同，跨客户端18项字段/元数据核同；所有实际值及比较结果先保存，最后才给分类。|

两客户端完整envelope里的server_time/backend/transaction_start等本就不同，不能要求整包SHA相同；psql stdout末尾LF也与Python返回文本边界不同。真正比较的是同一字段的全文/长度/hex/服务器摘要及明确稳定元数据。每个客户端自身序列化和重开读回逐字节相同、重新解析语义相同。raw返回副本、解析对象、重序列化及读回是同一次观察的不同层，不算多次数据库测量。见 `capture-layer-map.json`、`diagnostic-result.json`及两客户端layer-analysis。

公开门禁仅接受全文等于P023已由GPT独立复算的正常模板/旧一字符变体。本次两份均等于正常模板，故公开两份完整arch_prev.utf8（SHA即上述字段SHA）、原接收目标JSON、服务器字段对象、序列化及重开bytes。末尾空行和4空格原样保留，不strip、不加换行；模板中的email/CSRF仅字面表达式，没有实际患者、会话、口令或token。Git默认空白检查仅对两份原样字段文本的末尾空行/4空格报exit2；仅排除这两份必须保真的文本后，其余格式检查exit0（format-check.json），未改变字段字节或门禁。原stderr两份均0字节，原stdout完整流仍私有、公开其SHA/字节数。凭据文件及其他行/整库数据不进Git。

纯文件预检实际exit0、9项：正常，v→6与未同步合成服务器摘要，字面0x1F拒绝，正常转义，重复键，截断，模拟读回字节变化，非有限数字解析/序列化。模拟读回与server字段均标STATIC_FIXTURE，未导入旧native/capture或执行旧业务测试。三个冻结脚本compile通过；收集控制器exit0、psql exit0、Python客户端exit0、纯文件seal exit0，无运行修复轮或重试。

|实际预算及未运行|结果|
|---|---|
|连接/显式SQL|2/2，各6/6，总12；两次ROLLBACK/CLOSE|
|目标SELECT/行|2次，各唯一1行|
|其他库/维护/CREATE/DROP/COMMIT/业务DML|0|
|Odoo/Registry/shell、业务HTTP/RPC/浏览器|0|
|scope/文书/收退款/日结/PDF生成下载|0|
|授撤权/安装升级/产品core模板修改|0|
|sudo/OS-PG运维/Docker/网络/硬件专项|0|
|旧快照、异常字节、旧脚本/FAIL/manifest修改|0|
|原47大文件重核、645表扫描、原0x1F其它行查询|NOT_RUN，0|
|P022五组与S11/P025|NOT_RUN；不恢复/启动|
|Issue/Project状态写、合并、部署|0|

结果仅说明这两个当前只读窗口：服务器选定表达、两个客户端可见值与各自解析/序列化/存储读回一致，关闭前确认只读和RR。没有复原P022当时未保存的返回文本，不能定位旧v→6或另一个0x1F的故障层；不能从这约0.16秒间隔的一致推出过去故障已修、长期稳定、全数据库无损、产品安装验证、任何五组业务或S10阶段PASS。

文件效果入口：

1. freeze.json、SQL-contract.json、预检读回：核版本、完整SQL、目标和预算。
2. actual-budget.json：核两个客户端/backend、语句数、ROLLBACK/CLOSE及退出码。
3. psql/process-result.json、python/process-result.json：逐条intent/返回与身份时刻。
4. 两份client-received-target.utf8：看客户端真正接收的目标JSON文本，区别边界LF。
5. 两份server-generated-envelope.json：核服务器同语句hex/SHA来源及active仅摘要。
6. 两份arch_prev.utf8：按原字节重算2022字节SHA，与P023基准对照。
7. serialized.json/reopened.bin及layer-analysis：核写入/重开bytes和解析语义。
8. diagnostic-result.json：核18项跨客户端结果与明确的当前有限结论。

以上仅是固定证据阅读入口，不是恢复Odoo/数据库或点击业务的步骤。无产品、schema、权限或业务数据更改，无需数据回滚。所有旧库/快照/失败及本批原数据保留，不修旧字节、不清理、不reset/clean/force-push。线性提交推送新增材料、#34正式交付REST全文逐字读回后立即STOP；后续DB/业务操作必须另有正式授权，不自动续五组/P025/S11、合并或部署。
