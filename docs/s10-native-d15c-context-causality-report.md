# S10 Native D1.5-C 会话选店与 `context_get` 因果审计

## 授权与边界

唯一授权为 [#34 评论 6161691305](https://github.com/Yredxin/YDental/issues/34#issuecomment-6161691305)。固定分支 `codex/s10-settlement-finance-r1-20261013`，开工 HEAD `daa905063108a18265eb23b894a1b643eec2393c`；S10 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`，test `255b48f54495eb99638af8ffc824771b9a5af3e7`，Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。本批仅静态源码、历史日志和经检查点放行后的必要 PostgreSQL 只读聚合；Odoo、GDB-Odoo、Firefox、CREATE DATABASE 和业务写入预算均为零。

本次通过明确的 GitHub API GET 取得 #23 正文及 3 条有效评论、#34 正文及 43 条有效评论，末条 [GPT-CHECK 6162127891](https://github.com/Yredxin/YDental/issues/34#issuecomment-6162127891)确认原授权不变且截至当时没有 D1.5-C 预检或交付；#35 OPEN、0 评论。旧会话 05:40 的评论 POST 返回 EOF、无读回，事故库新增会话聚合为零；**没有将它追写成事前检查点**。本次真实[只读查询预检评论 6162472787](https://github.com/Yredxin/YDental/issues/34#issuecomment-6162472787)在事故库新增查询之前发表，API GET 正文逐字相等，正文 SHA256 `54ff6d76d01b0803df4657f897b63e558f45399bc5107bf5182bf7ecdaf89de0`。

origin、分支、本地/远端 HEAD、干净工作树、core SHA、venv Python 3.12.15、PG `127.0.0.1:5432` 与 cluster `7694897083368259627` 均核对。原事故库 `ydental_s10_test_20261014020300_8b6c1d4e`/OID2056451，纯 92 模块源 OID2100080，最近 L1 库 OID2100086，及旧 OID2078375/2100078/2100079 在管理库的只读目录中仍为固定身份。事故配置、日志、crash marker SHA 分别为 `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`、`f7795b360a80afc8fdfff8cd9c7e389da25064c36480bdb98bceccd9a2c0eef6`、`d1785e5f111f0c2358fce04895092b81f1c4455f3e0774f82b1646a447e48d78`。

## 锁定源码的实际调用链

`../odoo/cli/shell.py:130-148` 先 `Registry(dbname)`，接着建立 registry cursor，固定 `uid=api.SUPERUSER_ID`（1），执行 `api.Environment(cr, uid, {})['res.users'].context_get()`，再以结果建立交互式 `env`；仅在这些步骤完成后才进入 `self.console(local_vars)`，读取 actor stdin。`../odoo/orm/environments.py:64-89,227-250` 说明空 context 的环境用户由 uid1 决定，默认公司从用户设置求得。

锁定 core 的唯一可见 `context_get` 实现在 `../odoo/addons/base/models/res_users.py:791-820`。它先读取 `self.env.user.read(['lang', 'tz'], load=False)`；若语言不在已安装语言中，依次参考请求语言、`self.env.user.company_id.partner_id.lang` 和默认语言；然后写入 `uid`。`../odoo/addons/base/models/res_users.py:234-249` 中 `lang/tz` 与 partner 关联。全树 `def context_get` 静态搜索未找到 YDental 覆盖。这个路径没有调用 S01 的登录会话服务，也没有读取 `ydental_access_session.ydental_store_id` 的显式语句。

S01 的独立链是：`ydental_access/models/ydental_access_service.py:38-59` 的 `_session_for_key` 由 HTTP 适配器提供 key，查找或创建 `ydental.access.session`，然后可由默认门店 hook 提议选店；`:215-240` 的 `_bind` 将 `Binding` 放在 `ydental_binding` context 中，`_scope` 从该绑定读取会话并验 revision；`:325-337` 的 `_switch` 校验 membership 后写 `ydental_store_id`/revision，并新增 `store.switch` 审计。基础 `_get_default_store_id`/`_get_execution_store_id` (`:284-290`) 都返回 False。S03 扩展 `ydental_supply/models/ydental_access_service.py:12-24` 可在 `_session_for_key` 被调用时查找以前已选店会话，S06 扩展 `ydental_queue/models/ydental_access_service.py:10-19` 可从执行 lease 提供门店，但两者都不是 core `context_get` 的已证调用点。会话模型的 `ydental_store_id` 是存储的 Many2one (`ydental_access/models/ydental_access_session.py:4-13`)。

`../odoo/orm/registry.py:600-609` 的 `field_computed` 延迟遍历 registry 模型/字段定义。因此 S01 模型定义可处在元数据遍历范围内；这**不等于**读取任一会话行的选店值，更不证明它导致 native SIGSEGV。

|路径或事实|源码存在|事故实际调用可证|关联会话行选店值可证|
|---|---|---|---|
|shell → uid1 空 context → `context_get`|是|是，faulthandler 可见|否|
|`context_get` → uid1 lang/tz read → ORM 字段计算|是|是，faulthandler 可见|否|
|`Registry.field_computed` → 所有 registry compute 字段定义遍历|是|是，最后可见 Python 帧|否，遍历定义不是读行值|
|S01 `_session_for_key` → `_get_default_store_id` → `_switch`|是|仅 prepare 脚本执行有证；崩溃 shell 中无证|prepare 的选店写入有证，崩溃 shell 读取无证|
|S01 `_bind`/`_scope` → 选店 session|是|actor stdin 前无证|否|

YDental 的 `res.users` 扩展只见 `ydental_access/models/res_users.py` 和 `ydental_supply/models/res_users.py` 的字段、`write`/登录后钩子；没有 `context_get` 覆盖。`ydental_access_test` 中另有测试字段，但它不在事故库已核实的安装模块集合里。静态调用图不证明所有动态副作用不存在；真正 C 栈仍缺失。

## 原事故顺序及证据界限

原 `scripts/s10_r3_race.py:47-100` 为两个独立 `odoo-bin shell` 目标提供 actor stdin。`scripts/s10_completion/concurrency_actor.py:18-36` 如果执行到 stdin 才会新建 cursor、以 uid1 准备 root，再绑定 fixture 指定的经理，启动 bill 操作。事故 B PID2383730 的私有日志在 UTC 2026-10-14 02:08:26.114 记录 registry loaded，紧接 `Fatal Python error: Segmentation fault`，faulthandler 可见链为 `shell.py:139` → `res_users.py:797` → ORM read/fetch/field compute → `registry.py:608`。没有 actor stdin 开始证据，故经理绑定和 bill 未执行。另一个 PID2383729 的 SIGINT/-2 来自守卫中止，不能算第二次 SIGSEGV。

最后两个 prepare 分别为 `concurrency_prepare.py`（PID2383521，02:08:16.674 UTC、exit0）和 `refund_race_prepare.py`（PID2383625，02:08:18.406 UTC、exit0），脚本在自有 cursor 内 `cr.commit()`。后者两次以经理创建 session 并 `_switch` 到门店。私有 fixture 的只读关系检查发现：**退款 prepare 与出账 actor 的经理和门店都不同**；这推翻了旧草稿可能暗示“最后两次选店就是 bill actor 会话”的关系。`concurrency_prepare.py:28` 本身调用测试 helper `bind`；`ydental_treatment_test/tests/common.py:12-17` 的 `bind` 会新建会话并 `_switch`。事故前已选店会话存在，但 actor B 崩溃时仍在 shell 初始化，尚未读取 stdin、没有调用 actor 自身的 `bind` 或 bill。

提交与 actor 启动的先后由原 `actions.jsonl`、fixture 文件时间及日志支持。`concurrency-fixture.json` 的文件时间 02:08:16.317，`refund-race-fixture.json` 为 02:08:18.077；actor B 的最后可见 registry 日志在 02:08:26.114。私有 ID 和 key 不公开。以上**不能**说明崩溃的 shell uid1 初始化读取了任一选店会话，也不能用当前行值重建事故瞬间完整 MVCC/WAL 状态。

L1 库的独立已复核证据说明有一个合成经理 session，未选店，且双 GDB 目标 registry 时间窗重叠、正常退出。已选店与未选店差异是 S01 门店授权流程中的实际业务差异；目前没有静态调用边证明它位于本次 `context_get` 失败路径。无 SIGSEGV 的 L1 窗口不代表 native 问题已修复。

## 检查点之后的实际只读聚合

独立 psycopg2 连接在任何 SQL 前设 `readonly=True`，连接时核对固定 OID/cluster，并验证 `transaction_read_only=on`。只读 schema 核对后，仅取 `count(*) FILTER` 和 uid1 的非识别布尔统计。SQL 没有读取或输出会话 key/hash、姓名、登录名、联系方式、病历、支付资料、审计 before/after JSON、单行 ID。私有 fixture 的 ID 仅作参数。完整脱敏结果在[机器索引](evidence/s10-native-d15c/diagnostic.json)。

|聚合|事故 OID2056451|L1 OID2100086|解释边界|
|---|---:|---:|---|
|会话总数 / 当前已选店 / 当前未选店|176 / 165 / 11|1 / 0 / 1|当前持久状态；L1 确为未选店|
|事故 actor 启动前创建 / 当前已选且最后写入早于 actor 启动|176 / 165|不适用|时间戳与事故前状态相容，不等于 MVCC 快照|
|`store.switch` 审计总数 / actor 启动前|194 / 194|0 / 不适用|ORM 禁止审计更新/删除；仍不能排除库外历史操作|
|出账 fixture 经理会话总数 / 当前已选店且最后写入早于 actor|6 / 5|不适用|仅用私有经理 ID 参数查询，未输出身份|
|最后退款 prepare 两会话找到 / 当前已选 / 早于 actor 的选店审计|2 / 2 / 2|不适用|这两会话属于**不同**经理和门店，不能归给出账 actor|
|uid1 默认公司、用户关联语言、默认公司关联语言存在|均是|均是|两库这些输入的存在性相同；未比较实际语言/公司值|
|uid1 关联时区存在|否|否|仅字段非空性，不能证明完整 context 内容相同|

事故库会话涉及 62 个不同用户；`res_users.share` 当前存储值对 176 会话均为 true，而经理组关联计数为 91，会话类别字段不可直接拿来推断业务岗位。该对照只表明事故库比纯 L1 的持久会话状态复杂得多。原执行脚本和 `store.switch` 审计给出事故前已选店的正面证据；事故 shell 读取它们的证据仍为零。原脚本首次因错误地假定两份 fixture 经理相同而在数据库业务查询前 exit1；保留原版 SHA 并修正为两类经理分别计数后 exit0，详见失败历史。

## 因果判断与未来方向

当前有较强证据支持 **B：暂缓重复 S01 选店实验**。可证的事故调用链是 uid1 的 shell 默认上下文，S01 session 的查找/选店只在另一个显式服务调用链中。已选店经理 session 在事故前存在的证据，尚未形成到 `context_get` 的调用边。单独增加一次选店，预计难以区分“选店值有关”与低频 native 竞态，信息增益低。

证据强弱排序：①“原事故发生在 uid1 `context_get`、actor stdin 前”由源码和原日志直接支持；②“事故前已有选店会话”由准备脚本、提交记录、时间戳和审计聚合共同支持，但事故瞬间的完整快照未知；③“已选店值影响此 `context_get` 或 native 崩溃”缺少调用边和 C 栈，仅是假设。原事故已选店较多并不自动说明选店是致因：业务数据规模、registry 缓存、进程时序也同时变化。

方向 A 只有在新证据找到可信调用边（例如真实 uid1 上下文初始化触发 S01 会话查询的代码或 trace）时才值得申请：全新纯合成库，准备进程一次仅添加选店状态，再以两个独立 GDB/Odoo 只读 shell 作一次并发窗口；准备 1、捕获 2，另有独立 CREATE 1；不复用旧库，不碰业务数据。本批不执行。

方向 B 建议先用锁定代码和只读记录比较原事故与 L1 的非会话差异：已安装模块相同但原事故有临床/库存/财务准备状态、更多用户及模型缓存；再针对 `Registry.field_computed` 所遍历字段和 CPython/native 扩展的真实栈设计一个单因素、固定预算的新窗口。需要真正 signal11 下完整 C 线程栈、共享库映射/Build ID 和两个目标的精确初始化时间，不能靠重复启动直到偶发崩溃。若未来只做符号/栈的离线核验，Odoo 预算仍为零；若另开受控捕获窗口，必须单独授权其新库、准备与两个目标的各自预算。本批不执行任何后续窗口。

## 实际命令、失败历史与原始证据

|实际动作/命令概要|退出码|结果|
|---|---:|---|
|`gh api --method GET` 读取 #23/#34/#35 正文及全部评论、两条指定 GPT 评论；`git ls-remote`、`git rev-parse`|0；第一次 #34 大响应文件不完整，独立重取 exit0|#34 开工时 43 条评论、无旧预检；远端 HEAD `daa9050`|
|独立 postgres 管理库 `SELECT pg_control_system()`、`pg_database`|0|cluster 与 6 个固定 OID 相符；未读取事故业务表|
|`gh api --method POST .../issues/34/comments --input checkpoint-request.json`|0|生成检查点 `6162472787`|
|`gh api --method GET .../issues/comments/6162472787`，逐字比较正文|0|post/readback/本地正文完全相同；**在新事故库查询之前**|
|只读 schema 探针，`information_schema.columns`|0|事故库身份、所需列存在；原始列名仅保留私有目录|
|`../.venv/bin/python -m py_compile read_aggregates.py`|0|静态语法通过|
|`../.venv/bin/python read_aggregates.py` 初版|1|错误假定出账和退款 prepare 经理相同；断言在会话聚合前失败，原脚本/错误保留|
|保留初版后，修正版 `read_aggregates.py`|0|两经理/门店分开计数，事故与 L1 只读聚合输出脱敏 JSON|
|只读脚本 AST SQL 检查|首两版检查器 exit1、修正后 exit0|检查器误把通用 `query(dbname, sql, ...)` 的变量参数当作未经验证 SQL；最终检查 8 个调用点均为固定 `SELECT`，其余执行点仅 `SELECT`/`SHOW`|
|`sha256sum` 锁定源码、原日志、私有诊断脚本|0|字节证据写入机器索引；原始文件不上传|

旧私有目录 `.local/s10-native-20261014-6161691305-d15c/` 保存前次 EOF/空响应、授权原文和静态草稿；本次私有目录 `.local/s10-native-20261014-6161691305-d15c-resume/` 权限700、文件600，保留检查点 POST/GET 原响应、SQL 列名、私有 fixture 参数、初版失败脚本和修正版聚合。原始 `actions.jsonl` SHA `d6a578b75fd9ba331372e8616bf7a18999694649ffe65f3e1002660bcf0800cf`，`race-actions.jsonl` SHA `380aa68c226a8fd2b4b904706d6856638c6bc9c0303a11c274a9909a3fb20ff0`，`race-bill-b.log` SHA 见上。修正版只读脚本 SHA `d933f7d7b0f2095323528a676f57cc2484690dfeb41f836086557a72d5c99b7a`，私有聚合结果 SHA `bb3769278ad85bf7f35a973a63908f894510f6c12f835979aeb523df555e5584`。公开索引不含原始日志、配置、密钥、行 ID 或患者/支付内容。

## KNOWN / UNKNOWN 与保护

|分类|事实|
|---|---|
|KNOWN|固定 Git/core/PG 身份；shell 在 uid1 空 context 调用 `context_get` 后才执行 stdin；原事故前已提交选店会话与审计；事故 B 的最后可见 Python 栈；L1 未选店且该有限窗口未复现。|
|SUPPORTED, NOT CAUSAL|事故前 176 会话与 194 条选店审计的时间戳、原 prepare exit0/commit 相互支持；并未观察到 core `context_get` 读取这些会话。|
|UNKNOWN|事故瞬间完整 MVCC/WAL 快照、uid1 实际 lang/tz/公司值在两库是否完全相同、动态扩展的全部副作用、Native C 根因、选店值的任何间接影响、低频竞态概率。|

Python faulthandler 的最后一帧不等于 C 根因。本轮没有新的 signal11 或 C 栈；不能把一次未复现或本次静态不见调用边称为原生问题已修复。

原始 GitHub API 响应、旧日志与私有 fixture 仅留在权限700/600的 `.local/` 目录。全部历史 S00-S10 数据库、filestore、volume、日志、core 与备份保留；Odoo20 core、odoo-12、产品、固定 runner 均未改。本批 Odoo 0、Firefox 0、CREATE 0、业务写 0、Project mutation 0；#34/#35 不关闭，不启 S11，不合并/强推或部署。S10 与生产持续 BLOCKED，Native 根因 UNKNOWN。
