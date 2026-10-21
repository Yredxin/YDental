## 2026-10-21 09:32 UTC｜S11 clock addon init failure and read-only reconciliation

On candidate `a2a6f331a51bf533a9ddaa61a1d0725cea278f7a`, independent fresh admission passed (receipt SHA-256 `cda6eb8cf76b55dd70d7508d1a96769dc1e3272260083d92226eb9c1adc2ab13`; two independent offline reviews passed). The dedicated debug entry launched GDB-owned run `20261021T090930Z-924ad881e648` and attempted the first addon initialization. Locked Odoo 20 rejected the old `res.groups.category_id` XML field with `ValueError: Invalid field 'category_id' in 'res.groups'`, followed by a security XML parse error. No HTTP business request, browser, clinical or economic action ran. Console log SHA-256 `e51c9aee52db01f5c125b19cdad8e5de4f3809569dd883ebc95b5d65388e52f0`; Odoo server log SHA-256 `67752ad021090ba964b5c8f06325cc29e297513ac8cdac138a0af39b6a90abb5`; GDB exit receipt SHA-256 `2b2027449e46d03936f60bd96d679c6e5ca3fdc5955864462f0f315f3d74bc07`. The child exited 0 after an owner stop; inferior signal is null, core bytes 0, `native_crash_evidence=false`, and the owned process group is stopped. This was not a SIGSEGV.

The service was stopped through the owned launcher. A first post-failure read-only helper receipt is preserved as FAIL (`df122cb225bdaef3ce52f6dad1d88a0a066102075b3ea8ca215e1b4fe4eafbeb`) because it compared `172.18.0.2/32` to the same prior endpoint `172.18.0.2` as raw strings. After normalizing both addresses, the bounded RR READ ONLY reconciliation passed: `.local/s11/verification/clock-addon-failed-init-reconcile-20261021T093221Z.json`, SHA-256 `f02779f256813aba0d3775d4a4dced5ea171f889af9dddd2e860aef59bc60d8d`; independent offline receipt review passed. Exact scratch OID/cluster/role/endpoint and grants match; the clock addon is absent from the module catalog, with zero `ir_model`, physical table, and XMLID residue. Installed module set is unchanged. All 224 protected counts are nondecreasing, D/C projection matches its pinned hash, external counts remain zero; the transaction explicitly rolled back to idle and closed, and service/port checks passed before and after. The only business-row read was the fixed, explicitly protected D/C scalar projection; no patient/clinical rows were read.

The implementation correction follows the locked Odoo 20 source model: create an `ir.module.category`, a `res.groups.privilege` referencing its `category_id`, and a group referencing the privilege via `privilege_id`. Independent source review passed; XML parsing and `git diff --check` pass. Only `ydental_s11_clock_test/security/clock_security.xml` changed after the a2a6f33 commit; the fix and reconciliation note are not yet committed. A new exact-candidate fresh admission is required before another install attempt. No repeat of the old install run. The clock page/session control, and all remaining S11 synthetic workflow and regressions remain untested; keep #35 OPEN and S11 PARTIAL/IN_PROGRESS.

## 2026-10-21 08:36 UTC｜session-scoped synthetic business clock implementation

用户批准为日期触发测试提供debug入口，无需等待物理日历时间。该批准调整S11测试时间控制方式，不授权改主机、PostgreSQL或全局Python时钟。实现增加 `ydental_s11_clock_test` addon 和 `scripts/s11/debug_clock.py`；启动入口固定S11 scratch admission及OID/cluster、私有run manifest、GDB运行和localhost。登录用户需有专用 `S11 Synthetic Clock Operator` 组，路由使用认证、POST+CSRF、loopback校验，按服务端session hash、actor和当前store绑定；客户端RPC context不能自行启用clock。业务时间仅单调前进、与物理UTC差距不超过30日，并在8小时物理时间后过期；事件保留原因、操作者、门店、前后时间、run和物理记录时点。

`Clock` 通过HTTP dispatch对当前会话注入类型化context，并由service `_now()` seam消费，不patch系统/进程时钟。支持queue/intake/supply/patient/inventory/exam/treatment/lab/charge/settlement/followup service。Audit额外记录 `run_id`、`simulated_utc` 和 `physical_audit_utc`。合成clinical/lab action时间属于测试业务时间，不能声称物理执行。ORM create/write审计时点、资金/settlement物理校验、followup dispatch attempt、stale timeout、daily-cap窗口与host/PG时钟仍保持实际时间。Followup due及quiet-hour eligibility使用合成时间；transport仍只支持内部controlled test sink，未开启真实短信/邮件/provider。

入口通过 `.venv/bin/python scripts/s11/debug_clock.py`，随后登录本机 `http://127.0.0.1:18411/ydental/s11/debug-clock` 设置/推进或清除时间。模块首次安装为addon初始化副作用，因此仍必须以提交后的候选、fresh admission及专用S11运行检查执行。live guard会用当前受限数据库会话查询 `pg_control_system().system_identifier` 并同manifest cluster id核对；本轮没有运行数据库验证其实际函数权限。若受限角色被拒绝，则保持失败关闭并记录工具拒绝，不以更高权限绕过。

独立代码验收结果：`/root/gdb_core_runner_review` PASS；`/root/notification_feasibility` PASS。该审查未启动服务、连接数据库或修改业务数据。静态验证：改动Python文件 `py_compile` PASS；`git diff --check` PASS；`python3 scripts/s11/test_launcher.py` 30/30 PASS，日志 `.local/s11/verification/session-clock-launcher-tests.log` SHA-256 `c833f3f766b9a079801ccb20f1fedafd1db1c90f80d8bea5257782ffa08319e0`。Launcher测试里的“service started”是Mock子进程输出，不是实际服务启动。当前不宣称HTTP/browser/时钟路由或业务流程已实测。

仍待安装后验证：restricted-role live cluster probe；debug page和设置/前进/清除路径；合成临床来源；T08已确认PO的义齿收发/返工与采购费用；合成来源的postcommit到controlled sink；追加收费返工；适用并发及影响面回归、独立总验收。所有合成事件按业务来源保真、不触碰patient650/task720或PO147–149。旧SIGSEGV `ROOT_CAUSE_UNDETERMINED`与历史F2 loser/PID `EVIDENCE_GAP`仍保留；#35 OPEN，S11 PARTIAL/IN_PROGRESS；不push、merge、deploy或启动S12/S13。

## 2026-10-21 03:52 UTC｜窄HTTP后读回及T08 ACL边界

GDB owned run `20261021T031235Z-06f93a2c106d` 的独立post-run只读核验最终PASS：receipt `.local/s11/verification/post-http-readback-4f3798d-run-05c51e0-20261021T031235Z-06f93a2c106d-ro.json` SHA-256 `b8fe773cf0844c7b69bbc0213008c87687dbf3c86a3a42e31d06587d6b270991`。224项保护计数、D/C、模块/外发状态、副作用计数、准入与服务停止均匹配；READ ONLY事务rollback/close。客户端一次GET返回HTTP200，但server access log不完整，服务端请求状态仍UNKNOWN；不据此称SIGSEGV已修复或一般HTTP/browser稳定。

T08 current-candidate只读预检attempt2 `.local/s11/verification/t08-synthetic-workshop-scope-preflight-05c51e0-attempt2.json` SHA-256 `bd0857dd9b03d264f3b297d054393f6a2d54587fd6ab8859b2f701db01d439c1` 为BLOCKED：scratch/scope、产品可用性及buyer PO/line create权通过；partner create、直接cooperation ACL及产品/supplierinfo create权不通过。未读PO/line、无业务写入。receipt中的`rollback_idle=false`仍是取证限制，即使显式rollback和close均发生也不写为PASS。

独立静态审查确认vendor由group manager按正常资格流程审核，Store2合作用warehouse:write角色的bound session调用原生服务；旧vendor98 one-shot已消费，不能重跑。现阶段选择经新候选只读确认后复用合格的Odoo service产品，由独立buyer2666只创建一张新的USD125/一件PO行，计划日期按提交时实际UTC加5个日历日。该日期只代表合成测试假设。buyer的原生公司级权限包含受保护PO147–149，后续路径必须create-only，绝不检索/读取旧单。partner-create角色方案尚未实施，未授权任何广泛partner-manager或product-manager提权。细节与下一动作见根目录`CURRENT_TASK.md`顶部。

合成工坊user2670已创建、独立读回且不重复操作；未授采购/仓储/产品管理员权。当前无新vendor、qualif、合作、PO或义齿单写入。`ROOT_CAUSE_UNDETERMINED`、历史F2 `EVIDENCE_GAP`保持，S11 PARTIAL/IN_PROGRESS、#35 OPEN。

## 2026-10-21 02:16 UTC｜用户授权的合成义齿工坊与角色创建

用户明确表示不能提供真实义齿厂家，批准在S11 scratch中创建明确标记的合成义齿工坊和专用角色，由Codex定义测试价及工期，并要求保持真实物理时间推进、不改本地时钟。暂定测试价USD 125/单件、5个日历日，仅为合成场景假设；不代表真实市场价格、真实厂家承诺或现实监管资质。公司1/USD、Store2和产品/角色可用性由`.local/s11/verification/t08-synthetic-workshop-scope-preflight-3558a7b-v2.json`只读PASS确认（SHA `61d70a605ea52d5d79d304d16746c5cace9e507406d0fb9abf0be0fc81098fb4`）；没有查PO或PO line。

角色准备helper SHA `7333358a04d3c97a47d0c512e9e36588a0345c28f808243954327f6223d1c68c`与GDB wrapper SHA `e0a6eabcef4093ce60aee9155b619c75d52410034c9c7fd1ba8b751164295e07`经独立静态PASS。wrapper创建单次私有授权，校验GDB/inferior PID、start ticks、PGID/SID及空闲loopback；helper直接调用无法绕过该授权。一次性GDB run `.local/s11/operations/20261021T020308Z-synthetic-denture-workshop-role-gdb-3558a7b/` exit0、无崩溃/core，服务和process group均停止。result SHA `7fa6bd544422264158e99c68c9aab2b65440b25f125d7793a08044b9b5cc65b4`，日志SHA `11f7e00df0f73f2214728d5b07cb69097ac212fb64c0ecb21e1cef101f6a5260`，intent SHA `d97bc97263d7b380951784bef287c385cc59fd49e5744bc7fdb9eb2a3a759606`。

新角色user2670/membership4170，仅company1、Store2及`medical:write`；其他15类自定义权限none，无采购/仓库/管理员全局组。`purchase.order`四项有效模型权限均false。采购仍由已有独立user2666、仓储由既有user2043处理；旧PO147–149未读取/修改。独立RR READ ONLY读回PASS：`.local/s11/verification/synthetic-denture-workshop-role-3558a7b-independent-readback-attempt3.json` SHA `e8568222c38d57f0254fc97d0e80c00c1c5d85630921ee2ee7b111999e6a0529`，审核器SHA `b767c325223d2948a111fc9a71e816abbd398b54f4d0fe58edbb483d03387250`；access audit五类各一条，正常新账户流程新增五条仅关联新partner/user/employee/hr.version的内部chatter metadata，没有读正文。SMTP、SMS、payment provider、followup外发参数均为零/关闭。

修正记录：helper原始intent中的`session_id=false`是把access service model recordset写成session id的报告字段错误。独立按私有session key只读解析出真实Store2 session4247，session正常有效；原始intent/文件未覆盖，生成reconciled私有session副本SHA `7cc052baabbe729cc7741886e807464b9406eb90f34565f223cf91d027dd28d6`。readback曾有一个因关联chatter白名单过窄导致的FAIL receipt（保留，SHA `e951c73a2c2f323d6fc334f2e8f238075dc9875a2189498940f4d3eb097262f2`）；后续验收器改为读取目标限定的message metadata且正确核验hr.version与employee，独立审查PASS。另有scope过期和旧ACL API的只读核验失败，均无业务重试/写入；fresh admission新receipt SHA `b50b5b07e7c4131b3dfb2ef961679605c7eb9576e6a646473eedf9ef08a5510f`覆盖224保护表、200跨库catalog和不变D/C pin。

尚未创建合成vendor/qualification/cooperation/PO/采购行或义齿加工单；仍需在新提交候选fresh-admit后按正常业务流程逐项实施。patient683 slot1697窗口15:00–15:30 UTC，当前尚未开放；不调时、不提前做临床来源。`ROOT_CAUSE_UNDETERMINED`和旧F2 `EVIDENCE_GAP`保留；S11 PARTIAL/IN_PROGRESS、#35 OPEN。

## 2026-10-21 01:26 UTC｜patient683 合成预约提交与读回

当前候选 `dd5421a402a676910e3e425231609e0d3c4103e7`、原分支。patient683/slot1697 只读资格预检实跑并独立审计PASS；一次性helper经独立静态审查后，仅通过正常actor2466/Store2业务UI提交一次预约，HTTP303。预约后RR READ ONLY读回及离线独立审计PASS：唯一operation7191、entitlement778、task1184、held claim802；slot reservation容量1→0、walk-in=2、version2→3。读回核实审计和原生source/event链、保护表增量、D/C及财务不变、无到店/临床/队列/外发变化，GDB exit0无崩溃且服务停止。队列只检查aggregate count=2，未取身份；15:00 UTC前不做arrival/report。完整命令、receipt/verifier SHA、失败修正与遗留范围见仓库根 [CURRENT_TASK.md](../../../CURRENT_TASK.md) 顶部本节。此结果不声称SIGSEGV根因已修复；S11仍PARTIAL/IN_PROGRESS、#35 OPEN，无push/merge/deploy。

## 2026-10-21 00:30 UTC｜GDB run容量误计数修复与合成患者预检

candidate `5d606c25cab5de6a04d5df4c4a0a6fdb9acd57f9` 下，独立静态审查PASS的合成患者只读预检器SHA `b586ccdf2eb97dd0227e4ac525858085e64a0fef3b8c9ac31b202d7f3fdee125` 实跑PASS；receipt `.local/s11/verification/s11-synthetic-patient-5d606c2-preflight.json` SHA `77dbe72a7d2a4708e129017d66fcaa7f18819646d224b2b76a411a96760c3f18`。核验指定scratch/OID/cluster、actor2466及Store2非manager有效权限、禁用管理员/采购/仓库组、唯一synthetic姓名/幂等键、HTTP服务与端口停止。RR READ ONLY事务回滚关闭，无业务写入。

尝试以GDB启动新的S11 owned service时，launcher在创建run/启动服务前拒绝：64-run保留上限。检查发现runs目录有62个run目录与3个顶层普通日志文件（总普通文件1,252,679 bytes）；旧逻辑把普通日志误计入run数量。没有服务进程、HTTP请求或患者创建动作。本次保留所有原始run和日志。

修复 `ensure_run_capacity()`：仅目录计run，顶层与run内regular file仍计入512 MiB总字节，symlink/special仍拒绝。新增四个容量回归覆盖目录计数、保留旧文件内容、普通文件字节限额和symlink拒绝。`py_compile`及25项launcher测试全通过。最终测试日志SHA `5f74ad61db55760b902561432c6512df91f641260c96d34f31e99dce619290cc`。独立静态复审PASS。

实现和本段报告改变候选；提交后须在新HEAD刷新准入和独立审核。尚未重启服务或执行一次性患者创建。ROOT_CAUSE_UNDETERMINED与旧F2 loser/PID `EVIDENCE_GAP`保持；S11继续PARTIAL/IN_PROGRESS，临床FIFO后续、postcommit链、T08独立义齿/采购来源及收发返工、追加收费返工、适用并发、F1/F4和影响面回归/总验收未完成；#35 OPEN。

## 2026-10-20 17:16 UTC｜当前队列无备用叫号 lane 的只读核实

Candidate `7217b672bdec449ce7159cfb4255071314f9ec61` fresh admission PASS，receipt SHA `f12b571804839e1bae0bc770b7c670c3e13ba07039fc22879996e3517ab77033`，candidate admission SHA `49cef8d5a44801e8aa24e2c78e2756dd328e6a2afdfc1e9fc53853393095aa1c`；独立静态审查通过，覆盖scratch/OID2144130、224保护表、D/C、200个跨库catalog权限检查、停止服务和空端口。GDB/HTTP服务没有启动。

随后进行一项独立静态审查通过的Odoo ORM只读聚合检查（核验器SHA `897ebdc5bff15bd77b435130c70650c6dd336e4b94356cb6943e5269ceb8473c`；receipt `.local/s11/verification/queue-lane-feasibility-7217b67.json` SHA `5acac475fe63c64b3799a1c93f57c8f762c74e40682efa212125f75091f8c05d`）。Store2仅有1个active area与1个enabled/callable station，能力2；不存在已发布未来capacity。area2/capability2是唯一live lane，waiting=2，其余calling/serving/verify/reserved=0。事务RR READ ONLY、显式rollback/close；没有读取patient/task身份或业务写入。

因此clinical flow不能换用另一个现有callable lane，也不能新建同lane业务来越过现有FIFO。不能处理匿名旧等待项，不能skip或改写既有队列。依赖临床source的T05/T08及病人闭环保持未完成；需要经授权的额外测试lane，或业务确认最早等待项身份/合成属性并授权按原FIFO正常接诊。#35仍OPEN，ROOT_CAUSE_UNDETERMINED。

## 2026-10-20 17:05 UTC｜合成采购/义齿权限设置及独立读回

专用合成操作员以 user 2666、Store2 membership 4166、employee 2636在scratch上通过原生流程创建；唯一公司为1，Store2 `medical:write`且有原生`purchase.group_purchase_user`。purchase manager/system/Store2 manager均false。warehouse actor2043保留warehouse:write并按批准增加medical:write。整个权限变化保留原生 account.create、employment.join、authorization.change、login.scope及store.switch记录，写操作由GDB runner一次完成并正常退出；helper禁止重跑。

purchase user的原生公司规则使新账号对company1采购单有效，包含受保护PO147–149。设置与读回均未查询/修改这些订单，后续合成流程也必须避开。不得把“未查询”描述成角色无访问权限。

最终独立RO回读脚本SHA `cdca56907a47672c3fd19481bcc2c79039fbdd0a0f14708c8f3483f400db83b7`获独立静态PASS并实跑PASS。回执 `.local/s11/verification/s11-prosthesis-role-postsetup-readback-8dfaaee-v3.json` SHA `512285d099ee559ddb3ca4a3e1493feec359835b1201d444559ba482ef27f2cf`。核验目标数据库身份、有效组/公司/employee/membership、非管理员、精确审计、224张保护表及合理side effects（audit+6、grant+2、membership+1、session+1、mail_message+6、attachment+10、resource+1），无通知job/SMTP/SMS/provider外发，D/C不变、事务rollback/close、服务STOPPED/18411空闲。附件内容和消息正文未读取；没有任何PO查询。

同候选GDB下`ydental_access_test`单项MODEL测试通过（1/0/0；日志SHA `a19690d667e831a9d682c099fb867ca47df2de1e2f9fd41148e48775419be833`）。模块安装后的fresh admission PASS。早期回读尝试的只读核验器断言失败是适配/预期错误，未写业务数据；最终修正的准确脚本及静态复审结果取代早期失败，不覆盖其事实。当前plan仍PARTIAL，FIFO队列临床后续、postcommit/通知、T08新合成采购/义齿链、追加返工费用、适用并发/影响回归及总验收待完成；旧F2证据缺口不重放，ROOT_CAUSE_UNDETERMINED，#35 OPEN。

# [CODEX-STATUS] YD-S11-FOLLOWUP-LAB-V1 / 1.0

## 2026-10-20 15:01 UTC：预约浏览器自动化前置两次退出，GDB服务已停止

候选HEAD `993ee508cff5d5f4d4630d1217481d9ea258c1ee`，分支 `codex/s11-followup-lab-r1`，ahead origin 182。patient682针对slot1694的两次预约浏览器attempt均未发送`/ydental/intake/action` POST，receipt分别为`.local/s11/operations/patient682-slot1694-reservation-browser-993ee50.json`（SHA `c80ce77db30f0818ae9ad1957fb120b5cdc42d87dfe7414635cac031f2f75e6b`）及attempt2（SHA `4890265014b9b92a3881fd0ceae717ed81b2d74e33bffe7bb06efb0f206d3c79`）。均为PREPARED、`post_attempts=0`；独立RO读回确认patient682无arrival/entitlement/task/active position/treatment event，slot1694剩余reservation/walkin为1/2。attempt1做过正常Store2切换，attempt2验证已处于Store2后跳过；只存在该正常访问scope状态，不存在预约业务提交。原slot时间15:00–15:30 UTC已过，不可再用。

attempt2客户端退出原因是Playwright `fill()`作用于hidden幂等key字段并等待可见性超时；这不是产品拒绝或未知业务提交。下一版自动化应以DOM property设置hidden key、提交前核对字段，并保留单次POST闸门。旧attempt不重放。候选993ee50 fresh admission PASS（receipt SHA `6afe91029afc1c778b3161dab4404ad17e51d0ab4aeb8c4894c2057ff3a8a741`）。GDB run `20261020T145630Z-0ff86d87f167`由launcher正常stop，exit0、无signal/core（exit SHA `8dfbd2707bc2d1418e47b7c4353e578676dab290bb4be5dcd8bb2a3cffade948`）；前次run也正常bounded expiry。`ROOT_CAUSE_UNDETERMINED`不变，这些退出不构成崩溃修复。

独立审查已确认最新状态和可独立推进项（plan remaining audit）；预约下一步需新slot、更新候选fresh admission及只读核验slot/capacity/actor/policy，再单次正常操作。整个S11仍PARTIAL/IN_PROGRESS，#35 OPEN；不push/merge/deploy/S12/S13。

## 2026-10-20 14:30 UTC：GDB owner 参数识别修复

固定候选`cd85e4972728f7b21c0ebee0297c78166b9daecb`。用参数顺序`launcher.py --gdb start`启动的owned run `20261020T142835Z-107cde1bd9f5`曾被`own_process_matches`误报STALE_OWNER_RECORD；状态工具未发送信号。修复只接受三种明确合法参数序列（`start`、`start --gdb`、`--gdb start`），且仍精确核对launcher路径与PID birth ticks。新增回归用例；py_compile成功，launcher 20项测试通过，日志见CURRENT_TASK本节所列SHA。修复后原生status/stop确认owner并正常停止。GDB exit receipt SHA `03c3834cc724b8a0bd73f2e79b835c8e63c1630a740ebddbf9ee75db48458334`记录exit 0、无signal/core；此次没有HTTP/业务请求或写入。代码变更待独立review和提交；提交后须新HEAD fresh admission再继续，不将此结果表述为SIGSEGV根因修复。S11 `PARTIAL / IN_PROGRESS`、#35 OPEN。

## 2026-10-20 13:42 UTC：经用户授权收紧跨库PUBLIC schema权限

用户已明确授权在S11专用测试集群范围内实施需要的权限调整。目标库`odoo20_dev`，OID `16388`、cluster system_identifier `7694897083368259627`。管理员实际执行`REVOKE CREATE ON SCHEMA public FROM PUBLIC RESTRICT`。执行日志`.local/s11/operations/odoo20-public-create-revoke.log` SHA-256 `565b9dbb5aa0e414e79cab73e58f353ae2e761113ae7741f616b5c18504e1f7a`；后验日志`.local/s11/operations/odoo20-public-create-postverify.log` SHA-256 `e9d8bcecfc9c349bc97c00bb0dc17a40298a6e409ca5504daa82694fc4349558`；前置快照`.local/s11/operations/odoo20-public-create-preflight.txt` SHA-256 `2b4f77b11cd805ca594bd8956a0947b16922e7fe26504e884c918fdf18139721`。保存SQL `.local/s11/operations/odoo20-public-create-revoke.sql` SHA-256 `a9670f13b22130d6c150fd87d73bdb9e776035af5ff089124c3045af8e333b9c` 在执行后重构保存。独立审阅指出REVOKE日志本身不能证明`RESTRICT`子句；实际命令使用RESTRICT是执行者报告，不把它描述为日志独立证明的事实。

精确ACL差异是`{pg_database_owner=UC/pg_database_owner,=UC/pg_database_owner}`→`{pg_database_owner=UC/pg_database_owner,=U/pg_database_owner}`：只撤销`PUBLIC` CREATE，保留PUBLIC USAGE。后验确认目标库CONNECT仍有效；S11 restricted login对public的有效CREATE为false、USAGE为true。管理员/`pg_database_owner`权限保留。影响范围为`odoo20_dev.public`中依赖该PUBLIC授权的所有角色失去创建对象能力，不改变其它数据库或集群权限。

执行前曾尝试使用`postgres`角色；尝试失败且无数据库变化，退出码未捕获，未推断错误原因。无业务表或行写入，无runtime/admission变更，无服务或外发动作。准入状态仍pending fresh admission：必须用新文档HEAD和当前launcher SHA重新准入并独立复核后，才能恢复运行；S11 `PARTIAL / RUNTIME_BLOCKED`、#35 OPEN。`ROOT_CAUSE_UNDETERMINED`保持，fresh admission尚未证明通过。

## 2026-10-20 14:20 UTC：权限收紧后的fresh admission及只读HTTP探测

分支仍为`codex/s11-followup-lab-r1`，候选`80766954eb5c6301c8cfdfa4749aec44561de1d4`。在目标`odoo20_dev`（OID 16388、cluster system_identifier `7694897083368259627`）按用户授权撤销PUBLIC在`public` schema的CREATE、保留USAGE；DB CONNECT未撤销。受限S11登录的有效CREATE=false。ACL变更及执行证据见本报告13:42节和`CURRENT_TASK.md`；不触及其他数据库/集群权限或业务数据。

候选fresh admission PASS，receipt `.local/s11/receipts/s11-fresh-admission-8076695-20261020T140501Z-f3f0a82a887ecf36.json` SHA-256 `31ef8838efa95d287f679ec416f9dec9a6315b37cdfa8dfa39f14a9ed52406f9`。目标scratch/OID/cluster、受限角色/跨库权限、224保护表、D/C投影、模块集、外发关闭及受控run条件通过。随后使用S11 launcher `start --gdb`启动owned run `20261020T140705Z-a70d12d5c6d9`，只对loopback发起一次无认证`GET /ydental/queue/screen`。HTTP 200，响应1505 bytes、无重定向；client receipt SHA `ee29f19a062e44f313e368ce15d7ae85a898f0bdffab4085b2de24105cbbb040`。GDB child exit 0、无signal、无core；服务由launcher正常停止。server log保留一条Odoo test-framework import ERROR级诊断。

第一份独立读回因工具将`inet_server_addr()`返回的CIDR文本传给纯IP解析器失败，保留FAIL收据，不代表服务/业务拒绝。修复后的v2 verifier由独立审阅，双侧均用`ip_interface(...).ip`核验，SHA-256 `2c46899c42614dba602c6667a9b8cc411227dc7bd4aa0ba1213bb406ddb6be87`，mode 0600。v2独立RR读回PASS：`.local/s11/verification/post-http-readback-8076695-20261020T140705Z-a70d12d5c6d9-v2.json` SHA `4784921a14fc98de952bfd5f0b3d0c3c4e4f14778f397aecf40676887840e3f7`。确认224保护计数、D/C、97模块、领域副作用计数、外发状态不变，显式ROLLBACK/IDLE/close，服务STOPPED、ACTIVE absent、18411拒绝连接。没有把缺少HTTP access-log行解释为零请求；客户端和服务端请求计数均UNKNOWN。完整私有日志及原失败receipt保存在忽略目录`.local/s11/`。

该证据仅支持一个只读endpoint和该次服务启动/停止观察成功，不证明SIGSEGV已修复、其他HTTP/browser路径稳定或业务写路径安全。`ROOT_CAUSE_UNDETERMINED`保持，S11仍`PARTIAL / IN_PROGRESS`、#35 OPEN。下一项按正常流程推进合成patient682预约：先更新提交文档并对新HEAD做独立fresh admission，再只读核对actor2466的Store2权限、有效slot及容量；旧slot1693已过时，不复用。遵守area2/capability2当前waiting FIFO，不手动越序呼叫；预约和后续到店/报到各用唯一幂等键并做独立持久读回。不得触碰patient364/event417/task720、patient650或PO147–149。无push/merge/deploy/S12/S13。

## 2026-10-20 13:35 UTC：准入失败定位与跨库schema权限

对候选`6a7869eb080d25451f511118d403c42e929a36eb`的第一次fresh admission在跨库catalog扫描后因`connection_failures`非空退出，exit 1；失败收据`.local/s11/operations/fresh-admission-6a7869e-failure-20261020T133028Z.json` SHA-256 `f20c801bd54c538625738fbd83da16622aba3ee8084cbf6a1ef8f5a49c315c4e`未保留具体失败DB/异常，故不推断原因。

之后独立的一次有界定位以同一restricted role/cluster逐库检查所有200个effective CONNECT数据库，仅查询系统目录/权限函数，每库一次；全部200连接与目录查询成功，未复现SQLSTATE或权限拒绝。证据`.local/s11/verification/cross-db-admission-failure-locate-6a7869e-20261020.json` SHA-256 `2c83d3e6dc337bf46a58ad2f6ef05ee679beba1a623061774e233b4ebe3b2935`，脚本SHA `5c837557a9fa584b5a81a3bb3a7e8825a32e7a6f06ad511c6276056d3a0d2d61`。但快照发现`odoo20_dev`存在effective schema CREATE；所有其他数据库CREATE为false，relation/sequence读写及role拥有的relation/schema/routine均为0。故首次连接失败的因果仍UNKNOWN。

对`odoo20_dev`补做一次受限ACL provenance查询，只读`pg_namespace`：effective `public` schema CREATE来自PUBLIC ACL条目（另有`pg_database_owner`条目），无restricted login直接grant。receipt `.local/s11/verification/odoo20-dev-public-schema-acl-provenance-6a7869e.json` SHA `457c0c700eb6eba53d2fb711f7458864a56f9d5a143849a8b5a25b23dd86855a`。其中一个辅助`role_owns_schema`表达式有误，已由更正摘要 `.local/s11/verification/odoo20-dev-public-schema-acl-provenance-corrected-6a7869e.json` SHA `7f740c1e97f344a9315f8a3f7304babb60f621846e314ae7618098695627a20a`作废说明；使用独立新鲜目录扫描`owned_schemas=0`与原始ACL条目。PUBLIC CREATE使该role能够在此数据库创建对象并向新对象写入数据，违反当前受限跨库边界。所有连接均READ ONLY/REPEATABLE READ并显式ROLLBACK/关闭；未读应用行、未改ACL、未改runtime/admission、未写业务数据或启服务。

准入保持FAIL/BLOCKED，当前旧private pair不适用于候选HEAD；S11 `PARTIAL / RUNTIME_BLOCKED`、#35 OPEN。需要用户决定是否接受该PUBLIC schema CREATE能力或授权主机级ACL策略调整；不擅自撤改全局ACL。没有push/merge/deploy/S12/S13。

## 2026-10-20 13:32 UTC：准入复核与启动前实时数据库身份保护

独立准入审核发现私有runtime/admission仍绑定旧候选`dedbc2b`，且准入超过30分钟、launcher SHA已失效；scope仍有效，但旧pair不可用于当前HEAD。审核还发现原`validate_connected_database`只由synthetic测试addon的`pre_init_hook`调用，并非launcher每次启动都会执行。

修复提交`2e187a5c693b84f26b21efb6f1cd0b4da53108ab`把实时只读目标探测接到`start_service`：在run目录、ACTIVE owner marker和Odoo进程创建前，以私有受限S11 role连接固定loopback scratch DB，使用只读REPEATABLE READ查询并核数据库名/OID、current role、server addr/port及实际cluster system_identifier。成功路径ROLLBACK并确认事务IDLE后关闭；连接拒绝、权限不足或任一身份不符时fail-closed。探测与Odoo后续连接之间仍有极短时间窗；它降低错库风险但不构成数据库集群锁。

独立审查通过、无阻断。定向验证：py_compile通过；`python3 scripts/s11/test_launcher.py` 19 tests全部通过/exit 0，摘要日志`.local/s11/operations/launcher-live-db-guard-tests-final.log` SHA-256 `0ad4707946a9b2e18148006bca8c55a27a4e20716040b39fea6a089c51ef07e1`。mock用例验证正确目标、system_identifier SQL、只读/RR、rollback/idle/close；cluster mismatch关闭连接；启动probe拒绝时不创建runs目录/ACTIVE且不调用Popen。一次首轮test harness因系统Python未装psycopg2而顶层导入失败(exit 1)；将测试改为隔离mock依赖后，19项重跑全过。未连接数据库、未启动Odoo或写业务数据。

文档提交后必须以最终HEAD重新fresh-admit，旧pair不可复用；新pair通过后才运行`start --gdb`和全新只读最小HTTP稳定性验证。S11仍`PARTIAL / IN_PROGRESS`、#35 OPEN；不push/merge/deploy/S12/S13。

## 2026-10-20 13:20 UTC：提交后续行状态

GDB/core launcher实现已提交于`68dec3724f326738722c439484796ccce21493d8`（`[S11] add bounded GDB crash capture`），位于`codex/s11-followup-lab-r1`；该提交后工作树干净，分支ahead origin 175、未push。对应16项launcher测试、合成SIGSEGV捕获及独立审查摘要见下节与`.local/s11/operations/`私有日志。此提交没有启动Odoo或连接数据库。

先前13:16、13:10段落中“未提交/HEAD仍80bdce4”是写入当时的状态，不能作为当前状态。当前只读准入独立复核针对精确提交进行；旧admission/runtime/receipt绑定旧候选，不能直接启动。状态文档提交后还需按最终HEAD和`launcher.py` SHA重新执行新鲜独立准入。通过后可执行先前获准的全新只读最小HTTP稳定性检查，并使用`start --gdb`；不重演旧失败请求、不做业务写入。

S11其他合成业务闭环、义齿采购来源、通知postcommit、并发及影响面回归尚未全部完成。计划保持`PARTIAL / IN_PROGRESS`、#35 OPEN；不push/merge/deploy/S12/S13。

## 2026-10-20 13:16 UTC：GDB双进程组与崩溃捕获验收

独立代码审阅提出并促成的修正已完成。GDB与inferior处于专用session，运行期间可分属两个process group。wrapper在exec Odoo前以0600写入inferior PID、start ticks、PGID、SID；debugger PID/start ticks来自Popen。任何正常退出、信号停止或GDB早退后，launcher都需确认两个私有组均无存活成员才删除ACTIVE。inferior身份缺失、非对象/JSON损坏、权限或session/group不符时fail-closed，保留owner marker，不猜测目标已退出。独立审查最终确认该marker移除语义无剩余阻断。

最终定向验证：`python3 -m py_compile scripts/s11/launcher.py scripts/s11/test_launcher.py`通过；`python3 scripts/s11/test_launcher.py`运行16 tests、全部通过/exit 0，日志SHA-256 `2ba37648822b74db262a6c734b84c815bbbc5f45f675a536c20c6ac0abebb98a`。覆盖identity missing/null、独立inferior PGID以及debugger提前退出后的owned group清理。GDB 17.1对独立`ctypes.string_at(0)`测试inferior捕获真实SIGSEGV：7项thread table/backtrace/mappings/shared-library/core/permission/bound检查通过，sidecar及core mode 0600，PID匹配，core 10,931,832 bytes、SHA-256 `c1eb4b08ce3d8330a4a28c1d06a15eeb07214b4dd8d25a9b7bfc7ef0b5ed49d5`；摘要 `.local/s11/operations/launcher-gdb-capture-final.log` SHA `59e4b0dba21c98b9150af88867a275911466b08ca2907ca93e9f05bf47d69fdd`。对长驻合成inferior只杀debugger后，清理器分别清除inferior PGID并确认session两组为空；摘要 `.local/s11/operations/launcher-gdb-orphan-stop-final.log` SHA `b0357248c57aa5ccff761dbaf7fe5bfbfa77a36b997c90c7e6e1308348a60830`。另有一次无效core目标证明部分采集会明确`capture_complete=false`，不冒充完整；原始core/日志留在ignored `.local/s11/tooling/`，未进入Git。

仅验证了GDB捕获组件及其进程归属，没有启动Odoo或连接数据库，不能据此宣布HTTP稳定、原SIGSEGV根因已知或已修复。该批代码/文档之后已提交于`68dec3724f326738722c439484796ccce21493d8`；13:20状态节记录了当前准入要求。S11其余业务闭环、采购义齿、通知postcommit、影响面回归仍未完成，保持`PARTIAL / IN_PROGRESS`、#35 OPEN；不push/merge/deploy/S12/S13。

## 2026-10-20 13:00 UTC：更正队列阻塞判断

独立源码审阅发现此前把area2/capability2的一个waiting推断为阻止slot发布、预约、实际到店和报到，范围过宽；12:51记录中的这部分阻断结论撤回。当前历史聚合只证明当时有一项waiting，不能代表现在状态。正常预约检查已发布slot、窗口、能力和容量，不检查队列是否为空；到店根据patient/store/date创建事实；报到在有效qualification及实际arrival后创建或恢复queue entry。队列呼叫再按area顺序排序并筛选当前station/actor可服务的项，选择首个合格项。排序还含未用返工/回访机会优先级，因此应遵守原生排序，不称为无条件FIFO。源码位置见`ydental_supply_service.py:524-552`、`ydental_intake_service.py:485-494,545-571`、`ydental_queue/models/ydental_intake_service.py:114-150`和`ydental_queue_service.py:244-247,312-329`。

实施路径是fresh admission后先只读确认现时slot/队列，再由正常capacity角色发布当前有效时段，正常预约；仅在合成患者实际到店后记录arrival并report入队。用独立读回来确认新task/entry和顺序，不读取旧waiting身份。绝不手动呼叫patient682或让其越序接诊；等原生队列服务正常到它时，才继续接诊、文书和治疗。slot1693历史读回为draft，只有fresh核实政策、日期窗口及容量后才可发布；若已失效，按正常流程创建合适时段。无需创建替代area。这个waiting约束的是合成任务何时可被正常服务，不构成预约、到店或入队的空队列前置。

因此Store2 waiting不直接阻止其他无关工作。仍独立未完成的业务包括通知commit→postcommit→claim→controlled sink完整链、T08义齿专属来源及原生采购/收发/返工、F4完整双店经济链、task720之外的独立合成T18实际戴用与后续复诊、F1适用生命周期、全量影响面回归和独立总验收；各项仍受自身来源/角色/运行条件约束。F2旧loser/PID保留`EVIDENCE_GAP`，#35保持OPEN。

## 2026-10-20 12:51 UTC：下次 SIGSEGV 取证与当前剩余阻塞

用户要求下一次受控测试开启 GDB 与 core 记录。该项是未来新测试的运行前置，本次不启服务、不改主机级 core 配置。开始前需对新鲜候选重新做准入，并验证精确解释器/BuildID、GDB版本、core limit与`core_pattern`实际生效、私有目录权限及空间；测试必须由S11 owned child运行。若发生崩溃，保留run和请求关联、PID/TGID/TID、原始退出信号、GDB全线程`bt full`、进程映射/已加载库和core文件，并先独立只读核实业务提交，不重放。core可能包含凭据或患者资料，只能放在权限受限的`.local/s11/`私有目录，不进入Git、Issue或聊天。该取证配置用于下一次新测试，不代表恢复一般HTTP/browser或自动重跑旧失败路径。

当前可确认的业务阻塞与S11剩余缺口：Store2 area2/capability2的同一FIFO队列仍有1个waiting、没有替代可调用区；slot1693仍是draft，patient682尚未arrival/queue/clinical，不能跳过等待项或伪造业务事实。依赖合法临床来源的真实闭环、postcommit通知、义齿流程及适用并发暂不能推进。其余未完成项包括合法联系方式/偏好下的通知策略端到端；独立合成义齿来源、确认采购行和收发/返工；F4完整双店采购/收货/成本/患者费链；task720受保护的T18实际戴用/后续followup；F1剩余生命周期、最终影响面回归及独立整体验收。F2历史loser/PID继续`EVIDENCE_GAP`，不重放；PO147–149及task720保护不变。S11保持`PARTIAL / IN_PROGRESS`、#35 OPEN。

## 2026-10-20 12:45 UTC：SIGSEGV 系统日志关联与指令定位

原S11 run `.local/s11/runs/20261020T055248Z-18909ba92aa6/` 的runner记录直接child PID3536662、start ticks95156031、return -11、结束时间05:55:45.911Z（exit receipt SHA `4949fb84277ac17f6354e42509e15cc90b1e4793223ad69160fe11a524d153f4`）。此负值表示child以信号11状态退出，但该run没有同PID的内核crash entry；`reason=normal_exit`字段与该child exit值不一致，应以实际return为准。server log SHA `0a3c75dc015872b417c7bc5c7877fc95993e0024fe836ae77f93defadba46854`的最后HTTP行为05:55:43.709 `GET /web/webclient/load_menus`→403。此前登录POST→303、`/odoo`和前端资源GET→200；session rotation、cache invalidation已记录。两条缺失filestore blob的`FileNotFoundError`在资源读取上下文出现，资源HTTP仍成功返回。认证路径的Python栈包括YDental `res.users.write`、registry relation-trigger解析，并有`ydental.space.station.ydental_capability_ids` dependency searchable warning；日志未显示该warning之后的Python exception，也没有native stack。

本次报告更新前HEAD为 `d007b057e0ce05d31886c0457b31aad49d6378c5`，原分支 `codex/s11-followup-lab-r1`、工作树干净、比origin ahead 171，未push。产品代码候选仍为 `9425d999aaeba7a0e8af12cf419acb4aa91a5194`。S11保持 `PARTIAL / IN_PROGRESS`、#35 OPEN；本节只增加日志证据，不提升业务验收层级。

本轮新增核查`/var/log/kern.log:65`与`/var/log/syslog:2070`：journald事件时间2026-10-20T05:55:44.780116Z，内核记录`python[3538542]` fault at `0x36f237ab66a8`、IP `0x1800744`、error 4。内核task ID 3538542与runner直接child PID 3536662不同，时间仅相差约1.13秒；该task ID可能是其他进程，也可能是同一线程组中的TID。现有材料没有TGID/PPID/进程树/请求ID可以关联或排除两者，不能断言它属于或不属于原Odoo进程。

本机Odoo项目解释器`../.python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12` BuildID `7713d416ece8f53a2b37e61dd06defd7bf795954`、SHA-256 `0886fb76ceec8ff568d23079b5da6342bb41675e216e11525d4d6a9e65988d10`。对该二进制在记录IP `0x1800744`执行离线`addr2line`与objdump得到符号`visit_decref`和指令`mov 0x8(%rdi),%rax`。若崩溃task使用该二进制，故障指令与CPython cyclic-GC traversal visitor读取对象字段相符；无core及调用栈，无法判断对象为何不可读，也无法区分扩展`tp_traverse`错误、先前内存破坏、解释器缺陷或与S11/Odoo进程无关。CPython中`visit_decref`用于循环垃圾回收的引用遍历，见[CPython GC源码](https://github.com/python/cpython/blob/main/Python/gc.c)。由于task尚未关联到原run，该指令线索不能当作原run的根因证明或代码修复依据。

有限系统取证结果：`journalctl _PID=3536662`无记录；针对3536662及3538542的COREDUMP_PID日志查询均空；系统无`coredumpctl`命令，`/var/lib/systemd/coredump`与`/var/crash`当前无保存文件。原run目录只含exit.json/server.log，无parent PID和request-side raw receipt。既存独立crash-log review `.local/s11/verification/run-20261020T055248Z-18909ba92aa6-crash-log-review.json` SHA `dd0eeb3f44e5872a18d3c95208432ff4e97c29b954453df7bbbe57c0d49c0d43`范围仅覆盖runner receipt与bounded server log，确认提交状态未核实。后续faulthandler run在另一候选上exit0，没有native stack、未复现本故障。

结论仍为`ROOT_CAUSE_UNDETERMINED`。本轮没有修改产品代码；特别是不把searchable warning当作SIGSEGV修复目标。可形成决定性关联的下一证据是目标PID的进程树/PPID与映射库清单、崩溃core和native backtrace。按用户约束，不启动受影响服务、不重放旧请求；没有新增证据支持安全代码修复。

## 2026-10-20 12:36 UTC：capability队列读回及依赖业务阻断

固定分支 `codex/s11-followup-lab-r1`、候选HEAD `dedbc2bbe0945e5b302b9167630fa75485850c0b`，当次准入前工作树clean、origin ahead167；当前product source candidate仍为`9425d999aaeba7a0e8af12cf419acb4aa91a5194`。此提交与`b9f75517`间是报告/状态变更；queue代码和测试tree与产品候选一致。未push。

对先前area/state聚合所见的Store2 area2一个active waiting位置，用户范围内执行一次修正后的能力维度只读聚合。独立fresh admission `.local/s11/verification/admission-dedbc2-independent-ro-queue-aggregate.json` PASS，SHA `38b3d85966986a60ae8a3e69d02fab3fce542d29b54b1a52b9c2b9f5bc6a241c`；精确scratch/OID2144130/cluster/受限role、scope、D/C pin、保护计数、模块、外发和service STOPPED均通过，`launcher.validate_pair()` PASS。唯一最终查询receipt `.local/s11/verification/store2-queue-capability2-aggregate-final-dedbc2.json` PASS SHA `44dfbaa484b0babd60f354ad4e0c457dbe1caa736cec3dbcbd2947b351c8e3ac`；所执行runner `.local/s11/verification/store2-queue-capability2-aggregate-final-dedbc2.py` SHA `c7270a5b08cc3ae03558640ea67a704cc21796ab3884bb5a6fddab3dbdc4b9e1`。SQL仅针对Store2当前business date的`ydental_queue_entry`选取并group by `area_id, capability_id, state`与`count(*)`，不选取或关联patient/task/姓名/联系/文书字段。实际结果area2/capability2：`waiting=1`、`handover=3`、`void=1`。RR READ ONLY事务显式rollback、连接关闭；service STOPPED、18411 free。先前三次本地适配器NameError/KeyError回执保持INDETERMINATE；一次脏工作树导致的准入拒绝在数据库连接前停止，没有读数。此次锁定项目venv的执行唯一成功；较早system Python因缺psycopg2在数据库连接前退出。

该聚合确认当前待处理位置与唯一callable station的capability2一致；Store2没有替代可调用区域。严格按正常FIFO，禁止让合成patient682越过未知现有队列位置。slot1693保持draft，不发布、不预约、不到店/不入队；不操作或查明等待项身份。由此依赖真实临床来源的postcommit通知、义齿采购/收发/供应商退回返工及新并发场景均不能在当前合法队列条件下完成。不得把历史generic-care event417、protected task720或旧PO147–149拿来补源。

这不是运行恢复失败：已批准的限定GET及patient read-only browser访问通过，然而原SIGSEGV仍`ROOT_CAUSE_UNDETERMINED`，未修复声明。42项MODEL、限定带数据升级与保护验收不重跑；F2旧竞争仍为`EVIDENCE_GAP`、不重放。S11最后状态PARTIAL/IN_PROGRESS、#35 OPEN；不push/merge/deploy/S12/S13。

## 2026-10-20 12:31 UTC：有界恢复后续及Store2合成流程状态

当前固定branch `codex/s11-followup-lab-r1`、HEAD `b9f75517c612b71b4073012545545b3dea7df460`；运行时代码候选仍是 `9425d999aaeba7a0e8af12cf419acb4aa91a5194`，之后HEAD变化为状态/报告和已记录测试变更。工作树续行前干净，branch比origin ahead166，尚未push。

依用户的SIGSEGV处置决定，终止无新增证据的精确根因循环并记录 `ROOT_CAUSE_UNDETERMINED`。原child PID3536662退出-11、父PID未捕获；日志无native fatal stack/core，不能证明旧请求提交为零，不重放。此前独立有界恢复gate只授权限定新验证；loopback `GET /ydental/queue/screen` 返回200，owned服务正常停止并通过独立保护读回（gate SHA `e0b0668f…8200c`，probe SHA `39335ddd…81850a`，post-readback SHA `cd0baef7…ab912d`）。本轮在候选b9上，actor2466正常浏览器访问合成patient682：access GET 200、store switch POST 303、patient GET 200；无page errors/blocked requests，独立持久读回PASS SHA `160004793227af864ceb4a7aaa5b0956587b4315b6f904c8fbdbaeb71ad180a8`。这是窄范围静态页/只读访问成功，不是根因修复或全部运行路径安全证明。

为给合成预约准备正常资源，group manager按原授权只为既有合成actor2466增加Store2 `capacity:write`；独立读回确认仅该grant新增，audit 56043、source为`S11 user-authorized synthetic Store2 capacity scheduling role`，receipt `.local/s11/verification/store2-capacity-grant-2466-independent-postgrant-ro.json` SHA `fa53aae4407246b808d06c99ecb250e8ab3e54ea716340960f7d331f4de17528`。窗口预检为Store2/station2/capability2、policy305、12:30–13:00 UTC，未发现重叠slot（receipt SHA `70804eb3439f219b9022fae9d1916cc7001c26d0886306c99554b43b1af80585`）。slot表单浏览器attempt1客户端在GET后timeout，没有POST；独立读回确认无slot/operation/event变化。修正本地语言文本选择器后attempt2唯一POST得到303，随后GET200，创建的是未发布draft slot1693，容量1；无预约、入队或临床动作。operation receipt `.local/s11/operations/s11-store2-capacity-slot-2466-b9-attempt2.json` SHA `afa56f1c8e27b83416dc818b3ac6579ef4213c65692137910e348a40157d9c1f`，run `20261020T122015Z-33ff25d1be1b`；服务正常停止。独立RR READ ONLY readback事务rollback/close；修正capability关联适配后PASS，operation7013/key唯一，slot1693/capability[2]/event/audit唯一；fresh admission SHA `ef5e77806fcbdf1521c3a5e6f6aa98a08f1385cdf21b4588ad3f5deee666e98d`，reconciliation SHA `f4b787b5a4d04a18976ab58580c3074b8a85bfb4e41353a92d50de23944edd90`。首个只读适配器失败收据保留；同一已取得读回和admission中精确的capability关系+1，经静态修正allowlist后reconciliation PASS，不代表slot业务提交回滚。没有重放业务操作、不发布slot。

队列可用性方面，既有area/state聚合显示当前Store2唯一可调用area2当天有1个waiting位置，未读patient/task身份；无替代service area。源码只读审查显示合法预约必须使用已发布且有reservation capacity的slot，预约之后仍须按原生FIFO/能力顺序到店；draft slot1693不可预约。三次更细的capability2聚合尝试回执 `.local/s11/verification/store2-queue-capability2-aggregate-fresh-ro.json` SHA `03c9e1019f9354a6247596269ac954425ab3c1dc60e4f15ce3664fcdd027deec`、`...attempt2.json` SHA `82e466bfe9186a96fdd6f46eb97088830c27c5e4acb11bb6db683b50c65512b2`、`...attempt3.json` SHA `c71e976c6052eb3026c1c133f487f96a739b2aa942db6c48b35642837b25ec26` 均因本地adapter NameError/KeyError成为INDETERMINATE，但只使用RR READ ONLY并rollback/close，未读取身份列。另一次因tracked `CURRENT_TASK.md` dirty而在DB连接前被launcher安全拒绝，无新业务读取。没有证据证明area2现存waiting不兼容capability2，因此不发布slot、不预约或推进patient arrival/queue动作，保守维护原队列顺序。patient650/task720、event417及PO147–149均未用于本次续行。

已有42项MODEL、限定模块带数据升级和保护检查继续接受，不重跑。F2旧loser/PID保持`EVIDENCE_GAP`，不重放。T05/T12完整commit-postcommit-claim-sink、T08有效义齿来源/原生采购与收发返工、相关浏览器/真实并发及影响面回归仍未闭环；当前结果为PARTIAL/IN_PROGRESS、#35 OPEN。最终报告同步前不push；不merge/deploy或启动S12/S13。

## 2026-10-20 11:07 UTC：结算来源约束元数据只读核验

为精确区分升级日志的schema warning与费用去重约束，在新固定docs candidate `23e23bd0484e1d32a6ad5005b23ee099aedc1f93`及fresh admission下，只读查询 `pg_attribute`、`pg_constraint`、`pg_index` 和目标身份。receipt `.local/s11/verification/settlement-source-constraint-catalog-23e23bd.json` PASS，SHA-256 `3b7fef148c37aaf693ef10cf677944199b16cdfae34dcf406d285966b806ae87`；独立review PASS。结果为 `ydental_settlement_source.ydental_fee_id.attnotnull=false`，`ydental_settlement_source_fee_once` 的唯一约束定义 `UNIQUE (ydental_fee_id)` 存在，对应unique btree index存在。事务为RR READ ONLY、显式rollback并close。未查询settlement source业务行、fee/invoice记录或计数；nullable列状态不能说明现有记录内容。

结合Odoo `fields.Many2one(required=True)`与schema代码，upgrade warning是NOT NULL标记未能加上；不能把它解释成unique去重约束缺失。保留数据库现有内容，不清理历史null行；新S11业务操作仍须通过正常ORM要求该字段。该元数据核验不代表任何实际账务或lab业务链完成。

## 2026-10-20 11:04 UTC：最终候选带数据升级与升级后影响回归

候选固定为 `bed99cfe9fae52c6584c5424eb128b2d5bd9fa88`，与前序模型测试候选相比只有状态/报告文档提交。Upgrade前独立fresh admission `.local/s11/verification/admission-bed99cfe-independent-ro-recheck.json` SHA-256 `7f0a438f07f22bf5e700c23dd62eb96159aeac9b990313d32cb4b2a69b2120fd` PASS；目标scratch OID2144130、受限角色、其他DB权限、224保护计数、D/C pin、模块集、外发和停止服务均通过。升级后另行fresh admission receipt `.local/s11/verification/admission-bed99cfe-post-upgrade-independent-ro-recheck.json` SHA-256 `94d08876fc68b192faf6b5f1dd8a07aea3e553fe501f5f12e6f6371b9f55cf16` PASS；scope与DB secret保真，原pre-upgrade receipt未覆盖。

在数据已存在的scratch上，对 `ydental_base`、`ydental_followup`、`ydental_followup_test`、`ydental_lab`、`ydental_lab_test`、`ydental_settlement` 和 `ydental_lab_sms_guard` 执行精确模块升级；命令参数为 `--stop-after-init --no-http -u ydental_base,ydental_followup,ydental_followup_test,ydental_lab,ydental_lab_test,ydental_settlement,ydental_lab_sms_guard`，不含 `--test-enable`、`-u all`或HTTP服务。operation `.local/s11/operations/20261020T110013Z-final-s11-data-upgrade-bed99cf/` exit 0；日志SHA-256 `50f36a3e40a291906cb1006f265407a24796b8f6ba65d51f67b34797a1608e46`，result SHA-256 `05b6b25681fd20baddd92d1cb8e1c41bec88608e9247233cb3ac75cc4945b16b`。日志确认 `Modules loaded.`，最终已安装模块数97、与准入列表一致，没有新增模块或pending模块动作。操作记录保存模块与开关；确切runner保存在私有 `.local/s11/run_final_s11_upgrade_bed99cf.py`，但operation.json未复制argv字段。

独立upgrade后RR只读读回 `.local/s11/verification/final-s11-data-upgrade-bed99cf-readback.json` PASS，SHA-256 `30af497d18e3bcb6e32f18e43ec376f5d2b127f06e921f96b49da52b141813ff`。224保护计数零差异、D/C pin `33f8730…202ae8`、97模块一致且无待处理模块动作；16张S11领域表中有create_date的表在upgrade时间窗均无新行，通知/邮件/活动/job/outbox/SMS侧窗新增为0，外发关闭，RR事务explicit rollback/close，owned service STOPPED/18411空闲。首轮RO adapter因psycopg2 LIKE `%`转义错误失败，已显式ROLLBACK/close；修正后第二次读回PASS，没有重复upgrade。首轮stdout/stderr还在 `.local/s11/verification/final-s11-data-upgrade-bed99cf-readback.stdout/.stderr`；其部分JSON回执与第二轮共用路径，已由第二轮PASS覆盖，未保留首轮完整JSON。

upgrade日志有一个既有Odoo测试框架导入的ERROR级诊断（无Traceback，服务模块最终加载成功）、一个因`ydental_settlement_source.ydental_fee_id`现有NULL行而未能施加NOT NULL的schema warning、以及既存manifest/field warnings。相同诊断在较早S11 upgrade logs中出现；本次没有清理/迁移历史null行，也不宣称约束已生效。退出码0和Modules loaded不代表这些诊断不存在。

upgrade之后按当前固定候选、新fresh admission，更新仅两个已安装test addons并运行 `TestFollowupNotification`、`TestLaboratoryGuards`、`TestFreeReworkLifecycle`、`TestLabChargeNativeChain`：`--stop-after-init --no-http -u ydental_followup_test,ydental_lab_test --test-enable --test-tags <四个类>`，42 post-tests，exit 0、0 failed、0 errors；operation `.local/s11/operations/20261020T110240Z-post-upgrade-followup-lab-model-regression-bed99cf/`，日志SHA-256 `88475174e69b0ca7ded5b5de7c4fb20463936971dfda8a38cdc4696bc71d91ef`，result SHA由operation目录保存。独立测后RR回执 `.local/s11/verification/post-upgrade-model-regression-bed99cf-readback.json` SHA-256 `166892b3c65d83583f33dd3e64e7094f1f28b496f2e19bfb1c047fb98cb9fdb4` PASS；独立review PASS。224保护计数、D/C pin、模块集、测试时段受查副作用行、外发、事务rollback/close、服务停止与端口均通过。`mail_notification`无create_date，只记录当前数量。

这提供S11当前最终candidate的限定模块带数据升级和升级后MODEL影响回归证据；不证明HTTP/RPC、浏览器或normal identity/source业务流程，也不补足真实并发、F2历史loser响应、T05/T12 commit-postcommit-claim-sink、T08 supplier_return与完整F1/F3/F4/T18。以上业务依赖正常运行路径，但原HTTP child SIGSEGV根因仍未知，按用户决定HTTP/browser保持STOP，不重启/重放。S11 PARTIAL/IN_PROGRESS、#35 OPEN。

## 2026-10-20 10:57 UTC：义齿/返工/采购模型回归

在固定候选 `b3402c3bc0084266d6bc8c5e18f74fdae59514aa`、指定scratch数据库和`--no-http`条件下，运行 `ydental_lab_test` 的 `TestLaboratoryGuards`、`TestFreeReworkLifecycle` 与 `TestLabChargeNativeChain`。26 post-tests，退出码0、0 failed、0 errors。完整operation/result/log目录 `.local/s11/operations/20261020T105627Z-lab-guards-rework-purchase-models-b3402c3/`；result SHA-256 `51c4326eac6dd795bc8e788e77ba28f7972118717c80985051a4f17282db4499`，Odoo日志SHA-256 `227d33414c8bb6bafb9403bc89de3ed18373823e31312fc8f376ec54c576fd31`。operation绑定fresh admission `.local/s11/verification/admission-b3402c3-independent-ro-recheck.json`，SHA-256 `125521a36cba4d30c9ba6f24c37b37876c64fbe3de4babf6233659ed0b153348`。

独立RR只读测后读回 `.local/s11/verification/lab-model-regression-b3402c3-readback.json` PASS，SHA-256 `0567b16775a75573229c288c758ba94db5e4612ea557d5d3994803f29cb4afa3`；独立review PASS。224项保护计数无变化、D/C pin匹配、受查测试窗口side rows为0、外发关闭、模块集不变、事务显式ROLLBACK并关闭连接，owned service STOPPED且18411空闲。`mail_notification`没有`create_date`，只记录当前计数而不归因测试时段。初次系统Python调用在导入psycopg2前退出，未连接数据库；使用仓库venv仅完成只读测后检查，没有重跑测试。

本证据是MODEL/ORM回归，`--no-http`。它不证明正常用户工作流产生临床治疗源、已确认原生采购服务行、义齿收发/退货/返工的持久业务结果，也不证明HTTP/RPC、浏览器、真实并发、postcommit通知或患者送达。用户已批准的合成业务对象还需等SIGSEGV对应运行STOP解除并经过独立安全恢复审查；不使用patient650/task720，不读取/修改PO147–149。S11保持PARTIAL/IN_PROGRESS，#35 OPEN。

## 2026-10-20 10:54 UTC：通知模型类回归

在candidate b6845bbd25170b208579966a7685505d4939da9f运行整个TestFollowupNotification TransactionCase类一次，使用--no-http。结果16 post-tests、exit 0、0 failed/0 error；operation目录为.local/s11/operations/20261020T105304Z-followup-notification-models-b6845bb，完整日志SHA-256 eb2cdd522128ccadeebcc4d388e6ca21d4dbebd5796c9e8c3601b8983f9972cb。fresh admission SHA 4470ed85c5e72418c6dd5850d839eaefb089533d3b2dc3f969108f0f9d22f89b，独立review及launcher pair PASS。

独立RR READ ONLY/ROLLBACK/close测后读回PASS .local/s11/verification/followup-notification-models-b6845bb-readback-attempt2.json，SHA 7c50f0ad5fd9b81ead3d23ec471e1e3fa0038d7b012558042bf764f9401d3d84。224保护计数无差异，D/C pin匹配，测试时段受查mail/activity/followup/job/outbox/SMS行零新增，外发关闭、模块集不变，服务停止且18411空闲。mail_notification无create_date，只记录当前count。两次readback adapter错误原件见.local/s11/verification/followup-notification-models-b6845bb-readback-attempts.log；没有重跑测试。

这是MODEL/ORM且HTTP disabled，不证明真实postcommit、claim、transport或患者送达。该项不关闭T05/T12；SIGSEGV和F2只读复核见10:51节，S11仍PARTIAL/IN_PROGRESS、#35 OPEN。

## 2026-10-20 10:51 UTC：用户补充决定及SIGSEGV/F2只读复核

用户明确批准独立标记的合成患者及必要业务对象，通过正常身份、登记、到店、报到、排队、接诊、文书、治疗流程形成来源；批准正常义齿临床来源和原生已确认采购服务行建立独立lab/收发/返工流程。此业务数据授权不解除SIGSEGV运行STOP。patient650与task720不重用，PO147–149和旧财务/库存/审计原件保留。F2按用户决定只审既有证据；找不到原loser响应/PID时记EVIDENCE_GAP，未来并发使用独立标记合成场景并完整记录双请求及终态。

只读SIGSEGV核验：原run `.local/s11/runs/20261020T055248Z-18909ba92aa6/` candidate `81daa65…`，child PID3536662，exit -11；exit receipt SHA `4949fb84277ac17f6354e42509e15cc90b1e4793223ad69160fe11a524d153f4`，bounded server log SHA `0a3c75dc015872b417c7bc5c7877fc95993e0024fe836ae77f93defadba46854`，独立日志review SHA `dd0eeb3f44e5872a18d3c95208432ff4e97c29b954453df7bbbe57c0d49c0d43`。既有日志记录login POST303、`/odoo`及assets 200、`load_menus` 403和两条filestore `FileNotFoundError`；没有业务POST、native fatal stack或可确认提交。未找到匹配core/OS dump。之后有界faulthandler诊断exit0、未复现且无native stack；独立读回 SHA `6011d2c19ca04ea9892c10c1315c85230f8533e2fa9da56655ab652aef713c76`。其中“Stack”是普通Odoo stack_info。`13be108` launcher变化仅提升child signal/exit归因，不是崩溃修复。独立source/evidence审查没有支持具体产品修复，故保持HTTP/browser STOP，直到取得根因证据和独立审核的恢复条件。

新病例源码路径静态审查确认了normal session/Store2身份→patient registration/arrival→intake report→queue station/lease→execution→clinical document confirmation→confirmed treatment→follow-up source的顺序。义齿lab需要有效同患者治疗文书、义齿产品、approved/cooperating vendor和同公司已确认的原生采购服务行；采购行链接需purchase角色；lab接收/返工动作需要当前操作人同时有medical与warehouse写权。它们是代码前置，尚未核实当前DB合格资源/actor。此项授权不允许裸ORM、伪造session或跳过原生流程。

原F2 loser response与backend PID不在历史索引或artifact中；later same-key reconciliation及终态读回只能证明已存在invoice179，不能重建竞争响应。明确保留历史EVIDENCE_GAP，不重放。剩余无HTTP工作继续推进；不宣布运行恢复。

## 2026-10-20 10:34 UTC：通知入队回滚语义补测

在候选 `35608b53450797b349aa49d2881c8d117f117e66` 增加 `TestFollowupNotification.test_enqueue_rollback_discards_postcommit_dispatch`：通过测试自行开启的registry cursor/TestCursor savepoint创建合成store并调用`_enqueue`，确认一个postcommit hook被注册；回滚该savepoint后hook被清空且mock dispatcher未调用。独立代码review PASS；项目venv `ruff check`、compileall、`git diff --check`通过。候选fresh admission receipt `.local/s11/verification/admission-35608b5-independent-ro-recheck.json` SHA-256 `74cd0b793a77697d9c36056db52a8319e3b5777c9a0f94e9a83a9382e1c0dc7e` 经独立复核PASS，scratch/OID/角色/保护投影/外发关闭/service状态均通过。

只运行该单测一次，使用`--no-http --stop-after-init -u ydental_followup_test --test-enable --test-tags /ydental_followup_test:TestFollowupNotification.test_enqueue_rollback_discards_postcommit_dispatch`：1 post-test、exit 0、0 failed/0 error。operation/result/log位于 `.local/s11/operations/20261020T103242Z-followup-enqueue-rollback-35608b5/`，完整日志SHA-256 `f9b103d79f48b1017724bb43f1345461b71d412fd0201bfe3f2977713e94338a`，result SHA `d0c04045fb8fa1e975fe242212accb1224dfee8720d4c92cfbde0c115984ed67`。独立RR READ ONLY/ROLLBACK/close测后读回PASS `.local/s11/verification/followup-enqueue-rollback-posttest-readback.json` SHA `a885e33965fd67d1c43e8166bb7854a10e10e1678b6a38a8b9b91ede0e343c3e`，独立审查PASS：224保护计数无差异、D/C pin与模块集匹配、测试窗口受查通知/mail/activity/followup/outbox/SMS表无新增、外发关闭、service STOPPED/18411空闲。`mail_notification`无`create_date`，只记录当前count，不做测试时间归因。读回脚本的三次失败分别为语法错误、假设该表有`create_date`、operation元数据缺admission hash；均未重跑测试，最终适配器显式RR rollback/close并PASS，失败说明在`.local/s11/verification/followup-enqueue-rollback-readback-attempts.log`。

准入复核工具曾意外回显私有runtime行，故将S11 scratch LOGIN角色密码轮换为本机新随机值并验证新登录；仅更新ignored private runtime，未扩大权限或触碰业务表，之后按同一候选重新准入。秘密值没有写入Git或本报告。

该测试仅补充MODEL/ORM回滚不会派发的证据；不证明真实提交→postcommit→独立claim→controlled sink、HTTP/RPC、浏览器或送达。T05/T12仍有原完整链缺口，S11继续PARTIAL/IN_PROGRESS，#35 OPEN。

## 2026-10-20 10:26 UTC：#35 Python 中文翻译增量

按Issue #35 10-20 P2 定向复核，`ydental_base/i18n/zh_CN.po` 中 `Dental | YDental` 与 `YDental application access is required.` 两条 Python 文案缺少 Odoo 导出标记。候选 `9425d999aaeba7a0e8af12cf419acb4aa91a5194`（`[S11] mark Python entry translations`）仅为两个条目补 `#. odoo-python`，不改变源字符串、译文或访问判断。

纯Odoo `CodeTranslations._read_code_translations_file` 验证两项均通过 `PYTHON_TRANSLATION_COMMENT` 过滤，结果日志 `.local/s11/operations/20261020T1022Z-ydental-base-translation-loader-check/result.log` SHA-256 `5efd5532559bd6dac52080e6fbe558ce2b5df86a13a15aef002befe22c6b5bcf`。Odoo `get_translation` 对zh_CN返回完整中文译文、对en_US返回原字符串，脚本 `.local/s11/operations/20261020T1025Z-ydental-base-runtime-translation-lookup/check_translation.py` SHA `a6c015869c03f11b6de4f084154d3cfd9e944e1cdf9c358600619152fe9b7520`，结果日志SHA `111df72fc5f062a5a5b170f26385d25907a589cd999ff697a1849a8a8ea3ddcf`。首次纯查找未注册workspace addon路径而失败，未访问数据库或服务；attempt1说明保留在同目录，修正查找路径后的纯翻译调用通过。独立代码审查结论PASS（范围限PO过滤和解析）。

fresh RO准入 `.local/s11/verification/admission-9425d999-independent-ro-recheck.json` SHA `a75ebd79af3e5e302e4edb6eb2d4f67e5e1264d834ab30a65caff3b35ffe51d3` 经独立审查PASS后，仅升级已安装 `ydental_base` 一次：`--no-http --stop-after-init -u ydental_base`，exit 0。operation `.local/s11/operations/20261020T102403Z-ydental-base-translation-upgrade/`，完整日志SHA `49d0dc09abe4e29f8cdb90dc42b93481dc9067052d60b182244abb58a111f762`，其中明确记录加载`ydental_base/i18n/zh_CN.po`，97模块加载并registry正常结束。升级日志仍包含已安装test addon在非test mode导入`odoo.tests.common`产生的ERROR级诊断和字段依赖/schema警告；完整日志保留，升级exit 0，本次没有将该既存诊断归因于PO改动。

独立RR READ ONLY/ROLLBACK/close测后读回PASS `.local/s11/verification/ydental-base-translation-upgrade-postreadback-9425d999.json` SHA `1abd0e366bab12f9f08217f94407358b6beb467129837341dc3c1ede5033754c`：数据库/OID、224保护计数、D/C pin、97模块集一致，外发关闭，服务STOPPED且18411空闲。数据库没有`ir_translation`表，故没有声称存在持久翻译行读回；没有启动HTTP/browser或验证实际页面标题/403渲染。该运行时页面验证仍受已记录Native SIGSEGV STOP约束。没有新增角色/权限，没有触及受保护患者或PO，没有Issue过程评论、push、merge或deploy。plan仍PARTIAL/IN_PROGRESS、#35 OPEN。

## 2026-10-20 10:16 UTC：follow-up addon完整回归复核

在当前文档HEAD `a1e35b7c8eb529ec7456836f2eef47ab0871a49c` fresh RO admission receipt `.local/s11/verification/admission-a1e35b7-independent-ro-recheck.json` SHA-256 `f766c72053bc1cb526dd542ad829b162e3750a12381cdbfdca9bcee725a9c7e7` 经独立审查PASS后，完整运行 `--stop-after-init -u ydental_followup_test --test-enable --test-tags /ydental_followup_test` 一次：26 post-tests，exit 0，0 failed/0 error。operation/result/log在`.local/s11/operations/20261020T101527Z-followup-full-addon-7576985/`，完整日志SHA-256 `c627cb075b35285296a45ce9b26462e1353a91c067d0eb0641b8df65a52bfa8b`。这是Odoo addon suite，包含HttpCase测试客户端覆盖；不等于真实浏览器/provider/患者送达。

独立RR READ ONLY/ROLLBACK/close读回最终PASS `.local/s11/verification/followup-full-addon-posttest-readback-7576985-attempt2.json` SHA-256 `0c0cd1e70a4c7fe72a0a7d96e1d16f4a4abc3a2b5d995852e8ee4d1c81e4ad59`，独立review PASS：224保护计数与准入基线一致；D/C projection SHA `33f8730aa39cc869e749827e66f10505a0fe9e5aedd5677c9cb1b17718202ae8`、97模块集匹配；测试窗口activity/contact/preference/job/mail/message/notification/outbox/SMS零持久新增；SMTP/provider关闭，RR显式rollback/close，service STOPPED、18411空闲。首次测后读回使用了上轮admission引用，候选校验失败，其余只读项已通过；receipt `.local/s11/verification/followup-full-addon-posttest-readback-7576985.json` SHA `9bceb7e6bd785ca471e01e6d49a31967f42db436010430d139c6db6f5ec0baea`保留。修正准入引用后只重做读回，没有重跑测试。

## 2026-10-20 10:13 UTC：enqueue至postcommit callback接线测试
## 2026-10-20 10:13 UTC：enqueue至postcommit callback接线测试

固定候选 `75769854a75b0944b66f66f3b1dfba56450f42b5`新增MODEL测试 `TestFollowupNotification.test_enqueue_registers_deferred_postcommit_dispatch`。测试在隔离`TransactionCase`内通过`_enqueue`创建唯一pending job，捕获当前cursor注册的postcommit callback，确认dispatcher在callback执行前未调用；随后只调用捕获闭包，并mock `_dispatch_after_commit`验证数据库名及job ID参数。独立代码审阅PASS。

此断言仅验证`enqueue → callback registration/wiring`，callback由测试直接调用；不验证真实事务提交/回滚后回调生命周期、`_claim_dispatch`独立事务、`_dispatch_claimed`、controlled sink transport、HTTP/RPC或患者送达。原生完整自动链仍未验证。

新鲜RO admission receipt `.local/s11/verification/admission-7576985-independent-ro-recheck.json` SHA-256 `40fbe366464140736069530a9106d16eb66e9ef686684843f40387aeaa3edcdd`，launcher pair及独立准入review PASS。指定scratch/OID2144130/cluster/受限角色、224保护计数、D/C pin、97安装模块、外发禁用和service stopped状态通过。

精确定向命令仅运行一次，test tag `/ydental_followup_test:TestFollowupNotification.test_enqueue_registers_deferred_postcommit_dispatch`，1 post-test，exit 0，0 failed/0 error。operation/result/log `.local/s11/operations/20261020T101323Z-followup-postcommit-hook-7576985/`，完整日志SHA-256 `c3e56fdca2e76a2c7827f5067c95faa7c1a91ac8b13cee4a0288bfd7ea724cc1`。独立RR READ ONLY/ROLLBACK/close测后读回 `.local/s11/verification/followup-postcommit-hook-posttest-readback-7576985.json` SHA-256 `b21b4e003091ae4adbc1f880b0c42cd58d4fada677ef2e916660562caba059e5`，独立验收PASS：224保护计数、D/C pin、97模块集无差异；测试窗口notification/contact/preference/mail/activity/message/outbox/SMS无持久新增；事务回滚关闭，service STOPPED、18411空闲。

当前逐项层级及不完整证据的索引见[独立证据索引](evidence-index.md)。S11仍PARTIAL/IN_PROGRESS、#35 OPEN；此小测不把T05/T12升级为PASS。无push/merge/deploy。

## 2026-10-20 10:08 UTC：postcommit自动派发测试覆盖审计

只读测试/源码审计（未查DB、启停服务、运行测试或改代码）确认当前测试尚未连通来源提交与真实dispatch：`TestFollowupNotification.test_after_commit_dispatch_does_not_hold_an_extra_registry_cursor` mock了`_claim_dispatch`及`_dispatch_claimed`；`TestFollowupLifecycle.test_controlled_sink_records_internal_acceptance_without_delivery` 手动将job置为`dispatching`后直接调用`_send_transport`；生命周期另一测试只确认pending job创建、未派发。因此既有证据分别覆盖回调顺序和sink handler内部行为，但不证明source transaction commit后触发postcommit callback、独立claim和sink处理。

完整证明需正常HTTP/RPC业务请求形成真实提交，postcommit回调另开事务claim并dispatch，再独立RR读回job/contact/activity与零外发。TransactionCase/TestCursor的测试提交不能冒充此实证。现有HTTP/browser Native SIGSEGV STOP仍约束正常请求路径；不得重启该通道、伪造arrival/binding或用裸ORM绕过。T05/T12自动controlled-sink E2E因此保持未验证。后续仅推进不依赖此STOP且不造假业务事实/访问保护对象的计划工作；S11 PARTIAL/IN_PROGRESS、#35 OPEN，无push/merge/deploy。

## 2026-10-20 10:06 UTC：预约后通知来源的只读源码审查

恢复核验确认仍在原分支 `codex/s11-followup-lab-r1`、HEAD `f2aa841404c07c6fff553d0077f6b899d1cc9964`、工作区干净。既有25项follow-up addon回归与patient650预约及独立读回均保留，不重放。

子Agent对原生来源路径作只读源码审查，未查DB、未启动服务、未跑测试、未改文件。预约本身不能当作到店；原生业务需按arrival、report/queue FIFO、station capability和临床权限完成真实临床文书及治疗，再由confirmed treatment event支持显式followup创建。actor2466目前缺medical:read；clinical执行人还需medical:write及对应station能力。没有contact时followup走人工联系兜底；存在contact时才排入postcommit dispatcher路径。建job或controlled sink内部accepted均不代表已送达；`.invalid`地址不表示所有权或同意。

因此patient650的arrival不得为测试方便而伪造；既有area2活动queue entry身份不读取且顺序不绕过。已有HTTP/browser Native SIGSEGV STOP不重启，亦不以伪造binding或裸ORM替代正常认证。下一步只审查测试代码是否能用隔离用例补足source commit至dispatcher的覆盖；其结论不改变本轮已完成业务事实。S11仍PARTIAL/IN_PROGRESS、#35 OPEN，未push/merge/deploy。

## 2026-10-20 10:04 UTC：follow-up addon全套回归

候选 `ea1928c410697d8e68e533d9630a82efd5e879b7` 的新鲜admission receipt哈希链初审被独立验收指出错误：私有receipt自带自引用`receipt_sha256`，且`admission.json`尚绑定旧receipt hash。没有启动服务或进行业务动作。按无循环方式移除receipt内的self/admission哈希字段，将最终receipt SHA-256 `ffe0dfc9c7b3652e33137ca36fe76c96b37c86a8d6629528a7dd54ef418a947f`写在私有admission绑定中；`launcher.validate_pair()`通过，独立review复核PASS。receipt `.local/s11/verification/admission-ea1928c-independent-ro-recheck.json`。

使用Odoo项目venv，在指定scratch仅升级/测试已安装 `ydental_followup_test`：`--stop-after-init -u ydental_followup_test --test-enable --test-tags /ydental_followup_test`。全套25 post-tests、exit 0、0 failed/0 error。operation `.local/s11/operations/20261020T100258Z-followup-full-addon-suite-ea1928c/operation.json`，result SHA-256 `7f3b14c2138819dee033dd28489689353b2e921993cbace12730f94896ad0cce`，完整日志SHA-256 `ee026c69198e3814444821b85f107382f6bf6d3f1ed727c5fa7fc60b1e3b8cc1`。套件包含Odoo `HttpCase`测试客户端（包括原生signed callback HTTP路由），未使用真实浏览器/provider，不代表真实外部回调或患者送达。

独立RR READ ONLY/ROLLBACK/close测后读回PASS `.local/s11/verification/followup-full-addon-posttest-readback-ea1928c-attempt4.json` SHA-256 `c397312df1f5c42ab97851f3ec107719537dbf4f198831d4d83e78a30378cc31`；独立验收PASS。核对exact candidate/admission/test log、全部224项保护计数与测试前一致、D/C pin、97个已安装模块不变；测试时间窗中followup/contact/preference/mail/activity/message/notification/queue_outbox/SMS均无持久新增，外发关闭，service STOPPED/18411空闲，RR事务rollback/close。测后读回三次脚本错误（时间戳列假设、基线取值来源）仅影响本地核验，均保留错误证据，未重跑测试；第四次读回通过。

这填补follow-up addon测试回归证据，但不等于完整M5影响面或独立S11总验收。S11维持PARTIAL/IN_PROGRESS、#35 OPEN；下一业务动作前对状态文档新候选重新准入。slot1594预约流程仍未到店/排队/治疗，维持原活动队列顺序；无push/merge/deploy。

## 2026-10-20 10:00 UTC：patient650原生预约来源与独立读回

在候选 `59f0ceee26881c475759972f2e3fb2742612a3b0` 上，slot1594/patient650新鲜RR READ ONLY预检PASS：`.local/s11/verification/patient650-slot1594-fresh-preflight-59f0cee.json` SHA-256 `29e01ac982818e169e28ac2b62865246d2675e84551fa2c4c1659619f37cc9f3`。scratch identity/OID2144130及受限角色匹配；patient650为当前Store2合成关系且无arrival/entitlement/task；mapping2/catalog2与发布价455有效（$7 care）；slot1594发布、预约余量1、无既往claim或active lease。Store2 area2有1条活动队列entry；没有查询其patient/task身份。

沿actor2466既有原生Store2 session row3976/revision1，仅POST一次正常 `/ydental/intake/action` `reserve`，使用patient650、mapping2、slot1594及 `reservation` channel，HTTP200，operation receipt `.local/s11/operations/patient650-reservation-slot1594-59f0cee.json`。结果为entitlement740/task1128。没有重试、没有 arrival/check-in/queue-position/call 或临床业务事实。

独立RR READ ONLY/ROLLBACK/close读回PASS：`.local/s11/verification/patient650-reservation-independent-readback-59f0cee-attempt5.json` SHA-256 `e7eafc284c357d8f4417660c1fc1c29b6fb0298546af34bd175ce2b2007a792c`；独立review PASS。确认 task1128 pending→entitlement740 held→claim760 held→slot1594，原生capacity event/operation各唯一，预约余量1减为0、walk-in余量保持2。共3条accepted业务审计（frontdesk reserve、patient relation intake、capacity acquire）；224个S10保护表的其余217项为零差异，七个变更表恰为3条业务审计及上述6个intake/supply实体/操作/事件，无其它差异。D/C projection SHA仍为 `33f8730aa39cc869e749827e66f10505a0fe9e5aedd5677c9cb1b17718202ae8`。area2活动队列计数仍1，身份不明且未访问；patient650无arrival/active position/event/treatment/followup。SMTP、SMS、payment provider、mail、notification、outbox均未增加；服务STOPPED、18411空闲。

读回脚本的前两次未能形成收据：一次用错followup SQL表名，一次引用了错误的outbox基线键；随后一次脚本断言将这次正确的三条业务审计误按一条计，修正后attempt5通过。失败均属RR只读核验脚本问题，没有再次发送业务POST；原件和修正版本均留在私有verification目录。预约流程证实的是合成的资格/容量来源，不等于实际到店、候诊完成、治疗或复诊，不给予患者越过活动队列的优先级。

下一步仅在新文档候选fresh admission及独立复核后继续slot1594时段的原生到店/队列流程，严格保留现有队列顺序；不查认队列中既有对象。此候选仍仅是S11范围内的患者预约。S11仍PARTIAL/IN_PROGRESS、#35 OPEN，尚缺计划要求的来源及自动通知闭环、supplier_return、完整F4、T18后续、最终回归及独立总验收；无push/merge/deploy。

## 2026-10-20 09:53 UTC：controlled sink handler MODEL/ORM 覆盖结果

候选 `60d1bad343b3f9cb0f59ab1aa246dc4655c36410`，新增用例已提交为`[S11] cover controlled follow-up sink handler`。fresh admission `.local/s11/verification/admission-60d1bad-independent-ro-recheck.json` SHA-256 `7be1f07434c293c8d5739d30fb02d63e9f5ba13ac59db89e4443206082faa6d7`；receipt哈希与私有admission一致，独立准入review PASS。

仅运行新增定向测试 `/ydental_followup_test:TestFollowupLifecycle.test_controlled_sink_records_internal_acceptance_without_delivery`，模型/ORM层1 post-test、exit 0、0 failures/errors。operation `.local/s11/operations/20261020T095020Z-followup-notification-model-tests/operation.json` SHA-256 `a3310fd0a830c91103b5507e51fc875a2e13e0c0ed5150d20ffb1e605e4343ac`，result `a0347842f3ec52f9680f6e2029f5f52ec93ff89da9f82172980feb17fca25e0e`，完整私有日志SHA-256 `9b5fc11a43db20fedcba0dfe9f618ac23f8cc14c7fdce95aea86264bd7b274ab`。新增用例经正常合成 intake→queue→clinical→treatment链生成confirmed事件，在事务测试中验证controlled sink内部accepted、唯一联系记录、activity、followup状态/request推进及mail.mail无新增。

独立RR READ ONLY测后读回PASS：`.local/s11/verification/controlled-sink-model-posttest-readback-60d1bad-attempt2.json` SHA-256 `5c8436f9f8db2d7d287314dcec0a47e8aa5f605f833fe471bf279ae21c1c3cd4`。224项保全计数全零变化、D/C pin一致；测试窗口和持久状态均无本测试患者/偏好/followup/job/contact/mail/activity/SMS记录，外发相关计数均为0；只读RR事务rollback/close、服务STOPPED、18411空闲。独立测后验收PASS。第一次测后读回因本地检查脚本把多列结果按标量读取而失败；该工具失败原件 `.local/s11/verification/controlled-sink-model-posttest-readback-60d1bad.json` SHA-256 `66da36f7e97883c711b7d0085063ed3fe2a656ba36d38d6bce349b5a209646b8`保留，修正的attempt2通过，测试没有重跑。

测试仅补足controlled sink内部handler的MODEL/ORM证据，不验证post-commit/claim事务、来源事务提交后的自动触发、HTTP/provider或患者送达；controlled sink `accepted`仍不是delivery。S11仍PARTIAL/IN_PROGRESS、#35 OPEN；无push/merge/deploy。

## 2026-10-20 09:49 UTC：controlled sink handler模型覆盖（待运行）

只读计划/源码审计发现现有14项通知模型回归没有直接调用患者follow-up的controlled test sink handler。已新增 `ydental_followup_test/tests/test_followup_lifecycle.py::TestFollowupLifecycle.test_controlled_sink_records_internal_acceptance_without_delivery`。用例在TransactionCase事务中经正常合成intake→queue→clinical→treatment路径产生confirmed source，再用`.invalid`地址和合成email偏好创建followup/job，直接执行transport handler并断言内部accepted、唯一contact、activity、followup状态与request绑定，以及`mail.mail`无增量。独立只读源码审阅通过；没有数据库访问、服务启动或业务提交。测试尚未执行，固定候选和准入待提交后建立。

此用例仅填MODEL/ORM内部handler覆盖，不包含post-commit dispatcher/claim、源事务提交后的触发、HTTP/provider或患者送达；真实M1/T05/T12闭环仍缺patient650自己的confirmed source、followup和自动任务端到端实证。不得把受控sink accepted表述为送达。后续仅在精确候选fresh admission及独立审查通过后运行一次定向用例；S11保持PARTIAL/IN_PROGRESS、#35 OPEN，无push/merge/deploy。

## 2026-10-20 S11续行：合成患者联系偏好

候选HEAD `cf516304d086eb231e0bee5ebcb9ea1f094680b3`；写入前fresh admission及独立复核PASS：`.local/s11/verification/admission-cf51630-post-session-preference.json` SHA-256 `7716d388922f2703e0ccd1983ea64e071d1fd0bb92445c3c7b68b3e2015bf8ef`。沿已有actor2466/Store2原生HTTP身份，使用access服务为membership仅增加`followup:write`；保留`patient:write`和`frontdesk:write`，其它自定义权限none、无manager/system/purchase组。独立RR读回PASS `.local/s11/verification/grant-store2-followup-actor2466-independent-readback-attempt2.json` SHA-256 `0e1c07003f8513e0389c5f5912905b5e28e75a83774cbe082811afea09bbf797`；授权grant与accepted审计各1，无mail/activity/job/SMS/outbox副作用。

新正常认证产生Store2 session3976/revision1，native `store.switch` accepted。第一次followup workbench GET为403，没有偏好POST；独立读回 `.local/s11/verification/store2-session-pref-no-post-independent-readback-attempt2.json` SHA-256 `1b2a791e0f6a60f2f606e214918ab4ba1b8fa0f47abcd7dd16732f3a9b7f498b`确认无偏好及通知副作用。源码检查指出该workbench GET还搜索/读取同店医疗治疗事件，missing `medical:read`是403最可能原因；这是源码推断，未据此扩大授权。服务停止后复用同一个session3976与Store2 binding，不重复认证或switch；只GET access页面取得CSRF并向原生followup action提交一次`set_preference`。HTTP POST返回303。

patient650/Store2偏好当前唯一记录为`opt_out=false`、`preferred_channel=email`、actor2466；独立RR READ ONLY读回PASS `.local/s11/verification/patient650-email-preference-independent-readback-attempt2.json` SHA-256 `e536163a1b05aa4d4a09f4de2b7d7bbadc096eb81dd458f5f1a63ab402644f25`。操作回执 `.local/s11/operations/set_patient650_email_preference_existing_session_cf51630.json` SHA-256 `061451ea988f50e18588a14b77f2ddef02e9c537f933684d8108913ac1fa60ae`。`.invalid`值仅用于机制测试，不代表真实邮箱所有权或患者同意；没有创建notification job、mail、activity、SMS或outbox，外部发送关闭。该事实不等于T05/T12自动通知端到端完成；patient650尚无confirmed treatment source或followup。

此前`/ydental/followups`的403与直接原生`set_preference`成功分开记录；本轮未授予medical读权限、未改变产品代码。protected counts未下降，D/C匹配；service STOPPED、18411空闲。S11继续PARTIAL/IN_PROGRESS、#35 OPEN；无push/merge/deploy。

## 2026-10-20 S11续行：创建全新合成患者

写入前fresh admission固定候选 `ef6607840d531ddda12f625202d79b1e6b6f3152`，独立核对通过；receipt `.local/s11/verification/admission-ef66078-patient-create-preflight.json` SHA-256 `3db72d31eea78d03833a9d23cb4116e63912b4d2a06d07f46f25b05c2c50764b`。沿正常Store2 actor2466/session row3975/revision1访问患者表单GET 200；原生create POST仅一次，303重定向到patient650。HTTP receipt `.local/s11/operations/s11-synthetic-patient-create-ef66078-20261020T092846Z.json`。显式synthetic名称 `S11 synthetic followup patient 20261020 A` 和 `s11-followup-20261020-a@synthetic.invalid`；电话、出生日期空。邮箱只是机制测试值，不是所有权验证或患者同意。未创建联系偏好，未记录预约、实际到店、签署或临床事实。

独立RR READ ONLY/ROLLBACK/close复核PASS：`.local/s11/verification/synthetic-patient650-independent-readback-final.json` SHA-256 `b06685569e0fff93cd45e4dd3f63117b4944fd7d291c18bab92aed468c2950bd`。确认patient650仅属Store2，partner/号码/关系一致，operation763唯一，accepted `patient.create` audit恰1。无预约、arrival、clinical document/event、treatment、fee、followup/task/lab order、purchase/stock、notification/mail/SMS/outbox新增。保护计数增量仅access audit+9和patient/number/relation/operation各+1，D/C匹配；服务STOPPED、18411空闲。此建档不代表M1或T05闭环。

## 2026-10-20 S11续行：患者原生HTTP入口

在最终准入HEAD `0c864ae063bb31c05c4dcde9e492880cabfa11d8`（纯状态/报告文档变更，产品候选未变）下，受限正常Store2 session访问 `/ydental/patients` 一次，只读GET返回HTTP 200。准入 `.local/s11/verification/admission-0c864ae-current-http-preflight.json` SHA-256 `b3cbe009ff4de349c834ea075bb4ba683fc1da71a3aa6e7264b301158b46fcf7`，由独立review核对最终收据/配置哈希、目标、保护、角色、外发和service状态。

HTTP operation receipt `.local/s11/operations/patient-route-readonly-0c864ae-20261020T092254Z.json` 记录actor2466、Store2、已绑定access session row3975/revision1、请求状态和响应字节数，不保存返回页面、cookie或session key。独立RR READ ONLY/ROLLBACK/close读回 `.local/s11/verification/patient-route-readonly-0c864ae-independent-readback.json` SHA-256 `fafc17b31f5f2812ef1509cc5175f82ef72e9e5322caff8ca8b8c2e7da00344d`：仅增加8条该用户/Store2的accepted `patient/source.view`审计；224保护表无其他变化，D/C pin匹配、外发关闭、service STOPPED/18411空闲。没有保存患者页面数据，未运行业务POST。

这证明患者工作台在server-bound Store2 session和patient write权限下可HTTP访问；菜单API403由“需要相应业务权限”的菜单保护产生，不代表患者路由失败。下一步仍需新HEAD准入后仅通过正常患者表单创建明确合成的S11新记录，并核其持久状态；这一步尚未开始。

## 2026-10-20 S11续行：正常Store2测试session与原生门店绑定

修复提交 `13be1084d1cc9915c3ffe428872909b7e87f596c` 补充launcher对子进程信号/非零退出的准确归因及单测。`python3 scripts/s11/test_launcher.py` 12项通过，日志 `.local/s11/operations/20261020T0914Z-launcher-child-exit-diagnostics-test.log` SHA-256 `00c0b6fa9c2e40d2f67fc4d1fdf0c91039ea872eb2740f9dadb830fce3e4d5f0`。此前HTTP child SIGSEGV根因仍未定位；此修复不声称解决Native根因。

用户明确授权的受限诊断/正常Store2 session建立已继续。第一次普通认证作为诊断仅成功登录user2466 (`/web/session/authenticate` HTTP 200、`/odoo` 200)，未选Store时 `load_menus` 403；独立RR读回 `.local/s11/verification/http-session-diagnostic-13be108-independent-readback-final.json` SHA-256 `81e688c1570d598cde8b1c696a5507fd203c13de92c4a00a0ad57067d487454f` 确认server session未绑定Store (`NULL/revision 0`)。仅有session +1、认证审计 +2和内部chatter +1；无患者/临床/复诊/采购/库存/通知业务写入，无mail发送/SMS/outbox增量；S10保护计数与D/C pin匹配。未重用旧会话key或重放业务动作。

基于更新后scratch状态、同一候选 `13be108…` 的再次fresh admission通过，并由独立审阅确认文件SHA正确绑定：`.local/s11/verification/admission-13be108-store-scope-preflight.json` SHA-256 `4e0fc6ac2f2125d2d1d57c57ffbedf1fe662de1d08c088b126c8f366fee721d4`。第二次正常认证后通过原生access dashboard读取并提交一次Store2 switch（`GET /ydental/access` 200、`POST /ydental/access/action` 303、dashboard刷新200）。独立RR只读回执 `.local/s11/verification/store2-session-select-13be108-independent-readback-finalized.json` SHA-256 `de844f9f03dd66840872f6b4c807f47fe2a3c0bb8e39db37201d056a38edc690` 确认本轮新会话绑定 `store_id=2/revision=1`，`login.scope` 与 `store.switch` 审计accepted；无业务对象写入或外发，D/C与保护计数匹配，服务停止且18411空闲。该次认证cookie不写入回执；原始session key没有输出。

Store2绑定后 `/web/webclient/load_menus` 返回403，日志为“需要相应业务权限”；同轮认证、access dashboard与门店切换均正常，服务child退出码0且reason为`stop_requested`，无faulthandler崩溃栈。此结果证明正常Store2 server-bound scope建立，不证明菜单/浏览器业务测试通过；继续前需确认user2466具备计划所需业务入口/权限，并维持每次实际业务写入前的fresh admission和独立状态读回。task720、PO147–149及其他保留事实继续禁止触碰。

## 2026-10-20 S11续行：SIGSEGV退出诊断修复

用户明确授权对既有 HTTP child SIGSEGV 做只读诊断和必要修复，并在新鲜准入后建立新的正常 Store2 测试 session。原始崩溃 run 保持只读、不重放；授权不覆盖 task720、PO147–149、业务POST、外部通道、生产、合并或部署。

已修复 `scripts/s11/launcher.py` 的退出归因：子进程非零退出标为 `child_nonzero_exit`，意外信号标为 `child_signaled` 并记录 signal number；监督器主动停止记录 `stop_requested`，更具体的超时/强杀原因不被覆盖。测试 `scripts/s11/test_launcher.py` 覆盖这些分支。`python3 scripts/s11/test_launcher.py`：退出码0，12项通过；日志 `.local/s11/operations/20261020T0914Z-launcher-child-exit-diagnostics-test.log` SHA-256 `00c0b6fa9c2e40d2f67fc4d1fdf0c91039ea872eb2740f9dadb830fce3e4d5f0`。`git diff --check`通过。独立审阅通过。该修复提升未来诊断记录准确性，不构成既有Native崩溃根因修复；此前启用Python faulthandler的认证链未复现SIGSEGV且无native stack。

本次状态更新时新 session 尚未启动。下一步固定文档与代码候选、提交本地变更，再执行精确HEAD的只读fresh admission和独立复核；准入通过后才进行有界登录与只读HTTP路由诊断。S11原有业务缺口、task720 verify边界及#35 OPEN均保持。

## 2026-10-20 09:04 UTC：剩余闭环认证路径复核与停止边界

本次为本地只读源码/证据调查；没有数据库连接、业务写入、服务启动、测试重跑或产品代码修改。核验基线为原分支 `codex/s11-followup-lab-r1`、HEAD `698220d06c533257c1d4c0a3fe67d37d9532e79d`，产品测试候选 `789619fa76674caa1f8eab6db2eaf559847f16bf`。既有2项T18选择用例、14项followup notification模型测试及独立读回仍是最近测试结果，见08:58节。

独立认证可行性审查确认：新用户2466只完成Odoo原生密码校验，尚无 `ydental.access.session` 与Store2 server-bound scope；user10有medical权限但没有patient写权限。直接从裸ORM用 `with_user`、构造binding或复用已回显session key会绕过服务身份边界，不采用。新角色的正常业务调用要求HTTP adapter建立session；此前owned HTTP child以SIGSEGV退出的STOP仍有效，因此不重启服务、不重跑浏览器登录。task720已timeout进入verify，不重开、不takeover、不重放。

独立通知可行性审查确认，完整T05/T12 controlled sink需要新合成患者自己的confirmed treatment event、Store2联系字段及偏好、medical读权限和followup责任角色。用户已授权的合成测试联系方式/偏好可用明确标记的`.invalid`字段检验路径，但不能报告成真实邮箱所有权已验证或真实患者同意；controlled sink状态`accepted`仅说明内部测试sink接收，不等于患者送达。patient364的event417不能复用于其他患者，受保护event/task继续保全。当前14项通知回归没有直接覆盖controlled sink send handler，因此不将这14项扩大解释为受控sink端到端通过。

独立原生runner复核确认Queue→Clinical→Treatment可以通过Registry/model runner、不启动HTTP/browser来生成一条全新的合成治疗事件；前提是相关普通角色已有正常、server-bound Store2登录scope。禁止从裸ORM直接赋UID、手造binding或借旧session绕过认证。既有 `run_task941_native_clinical_once.py` 绑定patient364/task941/旧arrival与slot，只能作为序列参考、不可重跑或复用。旧只读资源证据中的slot1594为2026-10-20 10:24–10:54Z未来时段，mapping/catalog2 + published price455仅为$7 care；执行前必须刷新资格、容量和状态，该价不能作为义齿来源。独立复核未读数据库、凭据或PO，也未执行操作/测试。

独立源码路径复核确认T08初始lab order派单要求关联confirmed purchase line；purchase group原生company ACL会使独立合成采购用户可见PO147–149。历史用户授权允许在S11 Store2合成采购用户授予 `purchase.group_purchase_user`，但仍严格禁止查询、读取、使用或修改PO147–149；未以该授权访问这些记录。目前没有可安全复用的义齿confirmed treatment source，也没有新角色正常服务scope。新合成前置对象授权本身不构成临床适应证或已确认采购链，不能把generic event417或task720改作义齿来源。

结论：现有证据与授权下可继续准备明确标记的合成患者、联系方式/偏好以及价目/合作/仓库前置，但没有已验证的HTTP-free普通用户session路径来完成患者、临床和自动通知闭环；Native crash STOP禁止启动新HTTP/browser会话，T08还受confirmed采购行流程约束。当前无法满足S11 M1–M5技术关闭条件，保持 **PARTIAL / IN_PROGRESS**、#35 **OPEN**。需要用户决定是否单独批准对既有HTTP child Native SIGSEGV做只读诊断及修复，并在新鲜准入后建立新的正常Store2测试session；未获决定前不触发HTTP/browser链。未启用真实供应商、短信、生产、push/merge/deploy；没有读取PO147–149。

## 2026-10-20 08:58 UTC：T18与通知模型回归、独立测后读回

续行核验：分支 `codex/s11-followup-lab-r1`，HEAD `81fe5cd2f836696a0e16898d973838e294579103`，产品/测试候选 `789619fa76674caa1f8eab6db2eaf559847f16bf`；开始核验时跟踪工作区干净。前序用户授权创建的Store2有限权限合成操作员仍为唯一新建角色，本轮不重复创建、不创建患者、不重放已完成的业务动作。无产品代码变更。

在目标scratch OID2144130、固定候选81fe5cd上运行两个隔离 `--stop-after-init` MODEL/ORM批次，未启动HTTP服务：

- T18免费返工/返修关联所选测试2项通过，exit 0、0 failures/errors。operation `.local/s11/operations/20261020T085331Z-t18-free-rework-isolated-tests/operation.json` SHA-256 `d383a28a4b6393ecadeb855ce13d994194901b0985aacc5e02b0e1abd8701491`；result SHA-256 `6c098df107f622ff8aa765ec417a7fbee83bd8c10c49cb0a5c1f1bc76394c267`；log SHA-256 `a920b706ade9480b182b132b099a99bc01bae8a549825f299ff4dfc563a6b3d4`。
- `ydental_followup_test:TestFollowupNotification` 14项通过，exit 0、0 failures/errors。operation `.local/s11/operations/20261020T085502Z-followup-notification-model-tests/operation.json` SHA-256 `c1bc21e17839d429bd8dda383b18af0aa890c485991d58bbab747c0c578f53ec`；result SHA-256 `91f5276519d3d2ee61c0e360bd02bd47965a9eafa8dee0d0f6a121556da35205`；log SHA-256 `fddca7529fa885372f989f7b0113ef8ed1ad31c85dc0f84be25b5887954fa9b2`。

独立测后只读读回 `.local/s11/verification/s11-model-test-suites-postrun-readback-81fe5cd.json` SHA-256 `8e53ccfc0d06296fc98c05ee10a771b413ea4c7709cae8b819fa7a662704c742` PASS；独立审阅者核对六项operation/result/log哈希。读回确认测试前后mail.mail、mail.message、mail.activity、mail.notification、SMS、notification job、queue outbox七项计数零增量，D/C pin和保护计数一致，只读RR事务显式rollback/close，服务停止。准入 `.local/s11/verification/admission-81fe5cd-post-followup-model-independent-ro-recheck.json` SHA-256 `f3f67253b43225309c9473a15e60d85b4e4cc1ac5e4b1a4732ef14ae01c16958` PASS，确认scratch身份、受限角色和外发关闭。

证据范围限于所选合成MODEL/ORM测试，不证明task720完整T18临床续行，不证明HTTP/RPC、浏览器或controlled-sink/provider端到端。此前task720的Native crash STOP仍生效，不重启或takeover。S11仍PARTIAL/IN_PROGRESS，#35 OPEN；F1剩余闭环、supplier_return适用场景、合法联系方式下的通知策略端到端、T18实际戴用/独立followup、最终影响面回归及独立总验收均未完成。不得虚构义齿来源、联系方式或患者偏好，不读PO147–149。无push/merge/deploy。

本次独立计划覆盖复核仅检查现有计划、状态文档和固定证据，不访问数据库、不运行操作或测试。确认已有有限证据包括：F1 followup265浏览器完成及followup272无contact人工兜底、T03/T04 signed callback HTTP、F4/T15部分ORM、T06/T16/T17真实竞争、T08 discard、T18返工前段；F2首次收费竞争中一方提交、另一方遇SerializationFailure，先独立确认无第二经济事实，再对同一幂等键作有界恢复并读回唯一invoice。F2证据不等于两路并发均直接成功。依据 [S11实施计划](../../execution/S11_IMPLEMENTATION_PLAN.md) M1–M5及技术结束条件，独立验收结论为 **NOT ACCEPTED / PARTIAL**：仍缺T08 supplier_return及合格来源/入库链、有效联系与偏好下自动通知策略端到端、受Native crash STOP约束的task720后续临床戴用/followup、F1其余生命周期、F4完整双店采购/收货/成本/患者费链、最终影响面回归及涵盖完整计划范围的独立最终验收。不得把历史分项PASS叠加成计划整体完成。保持#35 OPEN。

## 2026-10-20 08:52 UTC：合成Store2患者/前台授权角色

用户授权在开发/测试阶段自行认证，并在缺少可用角色时创建并授予权限。保持分支`codex/s11-followup-lab-r1`、HEAD `d02a2363269aed29d7abde419d461890326f7d56`，产品测试候选`789619fa76674caa1f8eab6db2eaf559847f16bf`。针对HEAD的scratch admission PASS：`.local/s11/verification/admission-d02a236-independent-ro-recheck.json` SHA-256 `d3d17a92a6e779ffd98ed0983462d439569c56bd42a10ddcd13b981ed6ed8cd4`；覆盖分支/候选、DB/OID2144130/cluster、受限数据库角色、保护计数/D-C、外发关闭、服务停止与18411空闲。

经原生`ydental.access.service._create_account()`、`_grant()`创建普通合成用户2466，Store2 membership3871 / employee2434 / company1。仅有`ydental_base.ydental_base_group_user`原生组，仅授予Store2 `patient:write`与`frontdesk:write`，其余本店自定义授权均为none；无manager/system/purchase组、无其他门店membership。随机密码只写入ignored私有文件；通过Odoo原生`res.users.authenticate()`凭据校验，返回uid2466。没有建立HTTP浏览器session或创建患者/临床数据。

操作回执`.local/s11/operations/create_store2_synthetic_patient_frontdesk_operator_d02a236.json` SHA-256 `e74b1ce4e8bb23c64448932157da770758a5a675e8106fad00c532af8a838156`；独立RO/RR提交状态读回`.local/s11/verification/store2-patient-frontdesk-role-d02a236-independent-readback-attempt5.json` SHA-256 `afbeef401b11671c365fa41e6d76705492eeba94b31b92b070cc821968fcf7db`，14项权限、身份、审计、认证、渠道和回滚检查PASS，独立agent交叉核对通过。

实际副作用须保留：`mail.mail`+1，新行2461状态`exception`；`mail.message`+6。该邮件未发送/未排队，SMTP为0，未重试或删除；SMS、mail.notification、activity、notification job、queue outbox无新增。因先前HTTP子进程SIGSEGV后已有Native crash STOP，未重启服务或执行浏览器登录；当前只有模型层正常凭据校验。受此边界影响的HTTP/browser测试保持未验证。S11仍PARTIAL/OPEN、#35 OPEN；无push/merge/deploy。

结论：**PARTIAL / IN_PROGRESS**
Issue #35：**OPEN**
同步：本次继续实施的代码和状态尚未推送；依用户要求只在 plan 结束时发布最终结果与说明。
计划范围：S11-A 复诊和通知可靠性 + S11-B 内部外加工，含补充输入 v1.1。真实外部通知、生产、合并、部署、S12/S13 均未启用。

## 2026-10-20 授权后续行：合成路径准入与登录阻断

用户授权继续调查并使用S11 scratch内的明确合成测试场景。针对HEAD `284984004f3527d823fd25efe036560af33782e7` 的fresh admission通过：`.local/s11/verification/admission-2849840-independent-ro-recheck.json` SHA-256 `20b37c69b2a38195f8b4a41f4c8950dc238922ea5836ad75272b844c4d13a7a9`。独立复核确认检查通过且为RR只读/rollback/close；无业务数据库写入。角色和资源预检只读确认Store2 user9可建患者/处理前台/医疗，user10医疗，user2318医疗/复诊；当前发布映射2/价源455是$7 care，不能充当义齿来源。slot1594仍有余量但不重用已完成操作。

本次没有创建合成业务对象。原因是patient-write/前台actor9只有曾用于既有本机服务session；该session key先前曾在工具输出中回显，依保全约束不可复用。user10/2318现有正常scope没有patient-write；不以代码直接构造新认证身份或superuser绕过。fresh admission与role/resource检查无生产或业务写入。首次只读检查因脚本使用不存在的slot状态字段失败并自动关闭只读游标；修正后结果通过。后续需要通过获准私有provider建立actor9新scope，或确认另一名真实认证的Store2普通用户具patient/frontdesk write。T08还需另有合格义齿临床场景、义齿价源/有效采购行和相应操作员授权；purchase group的company级ACL可能使受保护PO147–149可见，既有明确限制仍禁止读取、使用或修改这些PO。S11保持PARTIAL/OPEN。

更新到HEAD `e08e3a527f708c5caf34d755f408017eea7eb9a3`后重新准入PASS：`.local/s11/verification/admission-e08e3a5-independent-ro-recheck.json` SHA-256 `28b4df9812cb214b175327eca5fb3aabe801bca00aef4fc8881450bb08ee1f00`；新鲜角色/资源RR只读读回PASS `.local/s11/verification/store2-role-resource-preflight-2849840.json` SHA-256 `9da69b68a867d6d1a9f1f513d21b0f9880a9b08d47d1a8d1dc9009246edd4d7c`。两证据确认S11 scratch/OID和受限角色、保护计数/D-C、外发关闭、服务停止；当前Store2 patient/frontdesk写权限仅在actor9，但缺安全可用的新鲜认证scope。user10/2318的现存scope不具patient write。映射2/价源455为care而不是义齿，slot1594仍发布且有capacity；本轮没有业务写入或已完成测试。

独立审阅复核了上述两份证据的SHA、候选/分支、权限/资源及只读事务标记，确认准入和资源检查PASS；没有查询数据库或凭据。

## 最新续行状态（2026-10-20 08:33 UTC）

分支仍为`codex/s11-followup-lab-r1`；本节证据核验时HEAD为`210a2ca275caf6cff4e5256f186fbdebe210b814`，本次文档更新不改产品代码；已测代码/测试候选为`789619fa76674caa1f8eab6db2eaf559847f16bf`。789到210只有报告/状态文档变化；7bd到789增加报告和F4测试，没有产品源码变化。HEAD210独立fresh admission PASS：`.local/s11/verification/admission-210a2ca-independent-ro-recheck.json` SHA-256 `3d4a5d0921d7d9b3fc2c22d2bf450cfd87568053a2c801d7d4172929942a119d`。

经普通Store2供给服务一次发布slot1594：station2，2026-10-20 10:24–10:54Z，容量3、user10覆盖。独立RR只读读回PASS `.local/s11/verification/store2-slot1594-independent-readback.json` SHA `b398104f27bb8e4ffe06a43b59dd6efab4b7d5f7bc12a025e1872a7f4fb55f11`：policy305、容量和覆盖匹配，两条原生供给操作/event/audit唯一，224保护计数与D/C通过，无临床、采购、库存或通知副作用；没有读取PO。首次脚本启动误用系统Python，在数据库连接前导入失败；改用项目`.venv`后唯一业务操作exit0。

Store2 source preflight证实event417是已提交、有效且未被复诊使用的confirmed treatment，actor2318具本店medical/followup权限；独立证据 `.local/s11/verification/event417-followup-source-preflight-210a2ca.json` SHA `f5695bf7514da4dd0e60180570702e7f716fdd9bf6b51f4a309ff6441336632a`。patient364无已验证联系方式/偏好，因此按原生规则不会排自动通知job。为验无联系路径，actor2318从正常浏览器工作台对event417只提交一次post_visit，创建followup272；POST303、刷新GET200。receipt SHA `0e43dd055e67f8a561956c44b7ac9adf6def435b0e4807332f57591dcb6ec245`，stdout SHA `8ea2f76f08cdf7e563d1bb7b4dc28936b6b7794a1133466d5f4be9799fc15fa3`。独立RR读回PASS `.local/s11/verification/followup272-event417-browser-independent-readback-finalized.json` SHA `a23f9cfd1075933ea19b44f4be72052475fc78506895da0622621b0ee0cd0bd2`：状态`to_notify`、内部activity恰1、contact/job=0；followup265/event416未变；增加1条内部chatter `mail.message`，没有邮件/SMS/outbox或外部送达。

执行期间的一次本机私有session文件核对发生了未脱敏工具输出，短暂回显一个scope key值；该值未进入仓库或业务操作收据，后续不会复述或复用。私有运行配置保持原状，此事项列为本地会话凭据处理风险，未推送GitHub。T05/T12的无contact人工兜底分支现有浏览器/持久状态证据；policy controlled sink的自动派发、免打扰/退订/日上限完整端到端仍未完成，因为没有已验证患者联系渠道，不能伪造联系方式或同意偏好。合格义齿来源、supplier_return、F4完整采购/接收、T18返工/返库与最终影响回归/独立计划验收仍未完成；#35 OPEN，无push/merge/deploy。下方按时间记录的历史进度保留当时事实；如与本节或覆盖矩阵冲突，以本节及矩阵当前候选为准。

### 本次只读覆盖调查

独立覆盖审阅未运行测试、未查询数据库、未读取PO147–149。F4/T15候选789619f的真实ORM资质审批/双店隔离测试已有通过记录及独立post-test读回，因此不重复执行。代码和测试中没有supplier_return实际业务链；现有event417是generic care，不能转作义齿临床来源。T18有隔离事务合成闭环用例，但task720已超时进入verify，不能重开/重放；隔离用例不能替代task720实际后续。T05/T12已有无联系路径的浏览器持久状态证据，不能据此声称controlled-sink自动派发通过；自动路径仍需合法联系/偏好。此次没有发现可安全推进以上真实闭环的新来源，因此这些范围仍保持NOT_RUN/PARTIAL。

## 2026-10-20 followup265 attempt12：浏览器完成与独立状态读回通过

候选/HEAD `f2e159e0093f2cde0af29c7117ab6780b8a13fa5` 的fresh admission、followup265/event416专用preflight和独立静态审查均PASS。preflight `.local/s11/verification/followup265-preflight-f2e159e-attempt12.json` SHA-256 `a591ff56e3697b5c9a6f8e167044a2fca2ba7ab1654c902d43b7655bd7e3dbe6`；attempt12 receipt `.local/s11/operations/followup265-completion-browser-attempt12.json` SHA `b97b653da9764264fedc3bd05f6f3ba37a77b29ab0caf2c0a1443f6ab44bf9d8`。actor2318在Store2展开“Complete from actual treatment”表单，选定event416并只提交一次；HTTP返回303，workbench刷新GET=200且followup265不再出现在开放列表。页面无JS错误。此前attempt7–11的不可重放收据/失败与只读读回均保留。

独立RR只读/显式rollback/close持久状态验收PASS `.local/s11/verification/followup265-attempt12-independent-readback.json` SHA-256 `f2c5587b6b504c832855a8f93ceae14de02cb89302452d2355c102f59da661f7`：followup265=`done/seen`，唯一关联event416/execution536；event为同Store2/患者364的confirmed treatment，执行为handover；恰一条actor2318/store2的accepted `followup.complete` audit；contacts和notification jobs为空。已有activity232未改变。页面读取审计38条及正常session/device记录保留。保护计数增加仅包含访问审计/session与1条`mail_message`；独立检查确认这条message为本次followup状态变更生成的内部tracking message，mail_outbox仍10，SMTP/SMS关闭、无外发。D/C pin匹配；service STOPPED/18411空闲；未查询PO147–149，也未重试。

此结果完成F1中followup265从人工联系至实际接诊关联的浏览器操作及已提交状态验收。S11仍PARTIAL/IN_PROGRESS，#35 OPEN；通知HTTP回调/策略端到端、适用supplier_return、F4双店E2E、T18后续、最终影响回归和独立总验收仍待完成。无push/merge/deploy。

## 2026-10-20 T03/T04：signed provider callback HTTP

在 `7bd9f0d09173288ee748c56227501f10be9329fe` 新增 `HttpCase`，针对`/ydental/followups/provider-callback`经真实Odoo test HTTP处理器提交raw JSON和HMAC header。单项定向HTTP测试 exit 0、1 post-test、0 failed/error：合法签名返回accepted/delivered；相同event第二次返回duplicate且只留一条receipt；错误签名返回403；无transport/dispatch调用。operation/result/log `.local/s11/operations/20261020T080614Z-followup-callback-http/`，log SHA-256 `9ed5d5b101babf5f23975b81d66e044f2e85ae6c465ce620a861db2d09921f0c`。独立静态审查、compileall和ruff均通过；fresh admission见`.local/s11/receipts/s11-admission-7bd9f0d-20261020T080601Z.json`，SHA `d67e422953b5fb63fe4c0467ae581133930596a24671247852752ac9867b8322`。

独立post-test RR只读/rollback/close读回PASS `.local/s11/verification/followup-callback-http-7bd9f0d-posttest-readback.json` SHA-256 `2a78569c12f53579ad3ec6610b0c7c76bf399ea733fc7710855056a8e337ffd3`：224保护计数零增量，D/C和模块集匹配，测试合成store/job/callback/audit及测试secret均无持久残留，mail_message/mail_outbox仍1080/10，SMTP/SMS关闭，service STOPPED/18411空闲。此仅是callback HTTP路由/鉴别/幂等验收，真实供应商仍NOT_RUN，策略端到端仍未完成。

## 2026-10-20 F4/T15：真实ORM资质与双店合作隔离回归

候选 `789619fa76674caa1f8eab6db2eaf559847f16bf` 新增 `TestLaboratoryGuards.test_vendor_qualification_and_cooperation_use_real_store_scoped_records`。测试在隔离事务内创建同公司两个门店、两名普通仓库用户和一个带合成资质附件的供应商；用原生审核动作批准资质，再由各店scope内的用户分别创建合作。断言两名用户的`_access(write=True)`只解析到各自门店、跨店缺少合作时拒绝、两条合作均建立后记录仍按门店隔离且第二店供应商校验通过。定向测试exit0，1 post-test、0 failed/error；operation/result/log `.local/s11/operations/20261020T081641Z-f4-real-cooperation-matrix/`，log SHA-256 `d7052e73305485959ab978ab2e22459108a8abe5bcc0aa42e9c178c37477ce8e`。Fresh admission `.local/s11/verification/admission-789619f-independent-ro-recheck.json` SHA `c4bcca927a630ee0dfa5bb2078718bb6b5239ef9498cf000856ac036b38a0fa8`。

独立post-test RR只读/rollback/close验收PASS `.local/s11/verification/f4-real-cooperation-789619f-posttest-readback.json` SHA-256 `16c47dca90f2888aa1f4621d6c294dbfede9c4f1d126cf408677060cd78fe67f`：保护计数未降、D/C与模块集匹配；测试store/users/vendor/cooperations/audit/internal expiry jobs及mail/activity/outbox无残留，外发provider关闭，service STOPPED/18411空闲。没有读取PO或创建采购/临床对象。此用例将F4/T15资质和合作证明从mock模型断言提升到真实ORM/原生审核与用户store scope，但仍不覆盖开单、收货、成本/患者费闭环。

测试日志记录3条auth_signup “Signup email sent”提示及一次Odoo测试filestore GC `3 checked, 3 removed`。独立数据库读回确认无新增mail/message/outbox，SMTP/SMS/provider均关闭；没有证据证明邮件外部送达。Odoo test cleanup仅处理filestore checklist中未被`ir.attachment`引用的文件，但operation没有保留被删路径或hash，因此最终交付列为测试清理限制，不推断文件逐项来源。

## 2026-10-20 候选2afd515验证进度

当前仍在原分支 `codex/s11-followup-lab-r1`，修正测试payload后的HEAD为 `353e0fa3f99bfc6e7c02fe952a724d0dbc0ea8bd`，实现候选仍为 `2afd5156c9b9b4e9a3a778df9b04d6f001f309f4`。353 fresh admission PASS，证据 `.local/s11/verification/admission-353e0fa-readonly.json` SHA-256 `3598bfe0c9acb35e5eb7dec107252a1cafea825910209bf5b4484c7885527534`；包含scratch身份/受限角色、224保护计数、D/C、模块集、外发关闭及服务STOPPED/18411空闲核验，未读取PO147–149。

三组定向回归均exit 0：32项临床/队列回归 `.local/s11/operations/20261020T073544Z-clinical-queue-expiry-handover-regression/`（日志SHA-256 `a808911cd9a3b1018a5c3ad9989034af64a0a97e2608913c5a39d7b043e7ed5e`）、followup生命周期1项 `.local/s11/operations/20261020T073625Z-followup-completion-regression/`（`31e7550a5b39fbb109da4508f44d7b4faba6e53aeb292807e7fa949ec707a82d`）、无frontdesk医疗角色HTTP工作台1项 `.local/s11/operations/20261020T073639Z-followup-http-medical-without-frontdesk/`（`155f81268665033a52526b75aa6cfb8891085d680f992765b52f1b2eec28619f`）。HTTP日志记录`GET /ydental/followups`=200；生命周期用例执行原生reservation reschedule并验证新slot DTO。独立post-test只读/rollback/close读回PASS `.local/s11/verification/posttest-353e0fa-readback.json` SHA-256 `b086cfccc26741735facb61b42b2655bcc027bea3e05978095ae38144945ef3d`：224保护计数、D/C、模块、SMTP/SMS及mail/outbox与测试前一致，owned服务STOPPED/18411空闲。之前2afd运行因测试调用参数错误报1 error的失败记录及独立读回保留；修复已在353e0fa提交，不计为PASS。

候选e373上followup265/event416 fresh只读资格预检PASS `.local/s11/verification/followup265-preflight-e3732fd.json` SHA-256 `380544dc4331f68394055bbbbbf4e15ea8e8b3772f5be3705cbca451b7f4ba7b`：followup265仍to_notify且未关联预约/完成事件/执行，没有contact/job；event416仍是同Store2患者治疗事件，execution536已handover结束、文书507关联一致；actor2318仍为active internal user且有medical/followup写权；无已有链接或外发，预约来源校验正常，服务STOPPED/18411空闲。该只读预检在状态提交前，后续需对新HEAD重新admit并fresh preflight。确认后可使用新attempt ID做一次真实浏览器完成；attempt6仍`do_not_retry`且不重放。#35仍OPEN、无push/merge/deploy。

## 2026-10-20 followup265 attempt11：折叠表单中的选择器不可见

attempt11通过认证并打开Store2 access/workbench；唯一complete marker定位至正确表单，但表单位于`details`中且尚未展开，选择event416时Playwright报不可见超时。未发生业务action POST；attempt11 receipt为`OUTCOME_REQUIRES_READBACK`/`do_not_retry=true`。独立RR只读/rollback/close读回PASS `.local/s11/verification/followup265-attempt11-independent-readback.json` SHA-256 `b34316e6c38df7ddc6cc15f57f903dfd92e6045756d3ab9e5cc7724ac17f3d95`：保留login/store及16条accepted source.view审计、两条设备记录；保护计数仅access_session+1/access_audit+19。followup265/event416、contacts/jobs/完成链接、D/C和外发/mail计数不变；服务STOPPED/18411空闲。后续全新attempt应点击对应details summary展开，再进行一次性表单提交。

## 2026-10-20 followup265 attempt10：工作台GET通过、表单定位停止

attempt10使用新准入和资格预检，HTTP认证后Playwright成功GET Store2 access和followup workbench（均200）；由于`form.filter(has=...)`没有唯一匹配完成表单，在任何业务action POST前停止。receipt为`OUTCOME_REQUIRES_READBACK`/`do_not_retry=true`，attempt10和锁不重用。独立RR只读/rollback/close读回PASS `.local/s11/verification/followup265-attempt10-independent-readback.json` SHA-256 `62cb4bc31607c3aa2fce8fb06e17367aedc9a237bfb2266f81683e23485ad775`：followup265/event416、contacts/jobs/completion link、D/C和outbound/mail计数不变；保留登录/范围切换、两条设备记录及16条accepted source.view审计；服务STOPPED/18411空闲。接下来修正为唯一操作input locator并用其ancestor form精确定位，验证followup_id=265及event416选项，随后全新attempt ID/准入/预检。

## 2026-10-20 followup265 attempt9：access页面文本断言停止

attempt9经HTTP认证成功（uid2318）并读取`/ydental/access`=200；脚本因用英文响应正文查找“Store 2”未匹配，在Playwright打开前安全停止，无followup workbench GET或completion POST。receipt `.local/s11/operations/followup265-completion-browser-attempt9.json` 为`OUTCOME_REQUIRES_READBACK`/`do_not_retry=true`，owned service `20261020T075100Z-be97da6ffcdc`已正常停止。独立RR只读/rollback/close读回PASS `.local/s11/verification/followup265-attempt9-independent-readback.json` SHA-256 `531bfc03b3672b3d55d264dcd81a6fb0ba0cf252c8d5bdfe9d495f0c40b68b8d`：保留session3925、device82及三条accepted登录/范围审计；保护计数仅access_session+1/access_audit+3。followup265/event416、contact/job/完成链接、D/C、外发计数不变，18411空闲。错误是普通本地化断言，不是业务拒绝；后续新attempt应删除该文本断言，交由浏览器检查Store2选择器。

## 2026-10-20 followup265 attempt8：认证后等待超时

候选1ad7a1f上的attempt8使用正确的CPython3.12 Playwright/greenlet导入顺序，普通用户登录成功，但Playwright等待`/web` URL匹配超时，尚未访问Store2业务工作台，更未提交followup完成POST。receipt `.local/s11/operations/followup265-completion-browser-attempt8.json` 标记`OUTCOME_REQUIRES_READBACK`/`do_not_retry=true`，attempt8不重放；owned service `20261020T074613Z-4ed754dd6c47`已正常停止。独立只读读回PASS `.local/s11/verification/followup265-attempt8-independent-readback.json` SHA-256 `39bebe854a4e128730bf5d01f5e5cc316c56599201c0f779fc22cd2dbeb871fc`：登录成功产生session3924、device81和三条正常认证/范围审计；除这些认证副作用外保护数据未变。followup265仍to_notify/unlinked，event416未变，无contact/job/完成链接，D/C及SMTP/SMS/mail/outbox计数不变；运行日志无access或followup应用路由，服务STOPPED/18411空闲。

下一attempt需使用独立新ID及fresh admission/preflight；可沿用已验证的普通登录HTTP/RPC认证，核实其uid严格为2318并将该session cookie交给Playwright，然后直接访问已授权Store2 access/workbench页和提交一次表单。此前attempt7导入失败原件保留且不重用。

## 2026-10-20 followup265 attempt7：浏览器运行时导入失败

候选506b019上的一次性attempt7在Playwright导入`greenlet._greenlet`时失败；浏览器未登录，没有followup workbench GET或completion POST。运行 receipt `.local/s11/operations/followup265-completion-browser-attempt7.json` 标记`OUTCOME_REQUIRES_READBACK`，attempt7和锁均不重用。owned service `20261020T074259Z-aa6268eeb9c2`已停止。独立RR只读/rollback/close读回PASS `.local/s11/verification/followup265-attempt7-independent-readback.json` SHA-256 `af4ace34f0ee301968d0625eb94e7da9b2c21e69a508a873ecb1e14b02ed9446`：仅有预期未认证`/web/login` GET；无认证session、访问审计、设备记录、复诊动作；followup265/event416和contact/job/完成链接未变；保护计数、D/C、外发及mail/outbox未变，服务STOPPED/18411空闲。

根因是运行脚本把私有browser_runtime放在site-packages前，导致CPython3.14的greenlet扩展覆盖`.venv`内兼容CPython3.12的greenlet。后续独立纯导入核验应采用先加载venv site-packages、再加载browser_runtime的顺序；对attempt7不重试，后续只能使用fresh admission/preflight和全新attempt ID。

## 2026-10-20 followup265 attempt6：已定位并保全的GET拒绝

候选 `2d87dba95b90c3601b558bbcda3f37975e514842` 的fresh admission与followup265/event416前置读回曾通过，但新的单次browser attempt6在唯一工作台GET遇到403，完成POST未发送。receipt `.local/s11/operations/followup265-completion-browser-attempt6.json` 为`OUTCOME_REQUIRES_READBACK`、`do_not_retry=true`；owned run `20261020T072753Z-f01909785bf8`已正常停止。独立RO回读 `.local/s11/verification/followup265-attempt6-independent-readback.json` SHA-256 `76182b60ff97cb951ba4effdc858952d7af94927b3f09d3b7ba42e6794f22f0a`确认followup265/event416没有业务变化；仅有本次预期认证session、设备记录和3条认证/门店审计，外发0，保护表与D/C保全通过。

日志显示工作台403原因不是ACL而是attempt5修复中错误假设claim source key始终等于task ID。独立RO核实同店entitlement475/claim493在合法重排后source key为`475-v1`，所关联task758为cancelled；另一有效entitlement485/claim503/task799使用task ID `799`。该 source key格式来自原生 `_reschedule()`（`entitlement.id-v<prior version>`）。当前dirty修订改为按entitlement精确关联任务，校验初始ID或精确重排key；任何其他不匹配capacity选项只被省略，不放宽权限或中断整个工作台。S11生命周期测试现以原生服务执行reservation reschedule并核对新的slot DTO；该修订尚待候选冻结、fresh admission、测试和独立post-test读回。attempt6不重放；F1后续新尝试必须使用新ID。

## 2026-10-20 续行：followup265 完成前置核验

fc0测试及独立post-test读回之后，状态/报告提交为 `e73bcd72535d651e9662db2f08cb6438472ec8cd`（工作台实现候选不变）。e73 fresh admission与followup265/event416同一只读事务预检PASS：`.local/s11/verification/admission-e73bcd-readonly.json` SHA-256 `eb2cddd966829cfcba5c521ee7113a5d96cc8a89d6e7315c060a1673d148a37d`。RR READ ONLY显式rollback并关闭；目标、受限角色、模块/外发、224项保护计数和D/C pin、服务停止均通过。

读回确认followup265仍`to_notify`、无预约/完成事件/执行、无联系记录或通知job；actor2318仍为active store2内部用户并具followup与medical写权，patient364当前store2关系存在。event416为confirmed treatment，执行536于2026-10-20 05:50:14 UTC handover结束，document507、patient364和store2链匹配；原生`_complete`允许该事件，但要求明确勾选无预约关联并填写非空原因，不要求文书状态confirmed。该次只读预检未触碰PO147–149、未写数据库。attempt5只有workbench GET 403、无completion POST，不能重放；在状态/准入按新HEAD刷新后，新的浏览器attempt6才可使用该前置事实。

## 2026-10-20 最新续行：工作台权限修复候选 fc0f614

分支 `codex/s11-followup-lab-r1`，候选 `fc0f614f2af90c4e0714ed6c9db5ae0bb5918175`，core仍锁定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。`ydental.intake.service._followup_reservation_options()` 限定当前store、授权patient relation、reservation entitlement和精确引用的claim/slot；校验reservation pool、来源task/source_key、store/patient/entitlement关联及held→held、started→consumed状态，只返回最少展示DTO。followup controller/template不再直接读取受保护capacity记录，未扩大ACL。患者canonical关系批量解析保留旧ID→合并链最终患者当前门店关系，并检查循环和缺失记录。

候选fc0 fresh admission PASS（`.local/s11/verification/admission-fc0f614-readonly.json` SHA `73f5e0f0fee0e8608990155468a0b4a1d394e2f2244584941ad9bb781b4dae68`）。测试结果：32项临床/队列回归、1项含原生A→B→C合并链和held/started预约DTO的followup生命周期测试、1项无frontdesk能力医疗角色的HTTP工作台测试均exit 0，0 failures/errors。私有运行目录和日志SHA见 `CURRENT_TASK.md` 当前快照。曾对S04专用`ydental_patient_test`选择器跑出0 tests，未计PASS且未在S11安装/绕过其pre_init约束；最终A→B→C覆盖已迁至已安装的S11 followup生命周期测试并在fc0通过。

独立测试后读回PASS：`.local/s11/verification/fc0f614-post-test-readback-attempt2.json` SHA `b988064fd4c4c869295a7ff28e8474c8975e114b838f8b665b2266239a8010f5`。RR只读/rollback/close确认224保护计数不变，D/C pin和安装模块集一致，SMTP/SMS为零，服务停止且18411空闲。首次post-test读回FAIL原件 `.local/s11/verification/fc0f614-post-test-readback.json`（SHA `282890ebbb7a64cbbe6e22fda812b91488e65a05db6714fb90046c328c0beac2`）因预期4条而本次真实3条；保留后由第二独立读回对三条日志/退出码和保护事实完整复核。

attempt5验证了followup265在未修候选下的页面403；独立读回确认没有completion POST，attempt5不可重放。fc0覆盖该权限路径的HTTP测试已通过。下一步需在同步当前状态文档并对新HEAD重新准入后，为followup265执行新的只读资格核验，再决定是否开展全新浏览器attempt6。计划仍PARTIAL/OPEN；task942固定care映射和event417/doc508不支持义齿临床场景，不能当作T08义齿来源，也不查询PO147–149。通知回调/策略端到端、适用supplier_return、F4双店E2E、T18后续、F1完成、影响回归和最终独立验收仍待完成。

## 2026-10-20 续行：followup 工作台容量权限修复（实现待测）

当前分支仍为 `codex/s11-followup-lab-r1`，HEAD `f2e320b78cf11e912f6ea129f6ddb3754dc02090`；下述实现/测试增量尚未提交，工作树有7个tracked文件改动。候选未冻结，也未运行该增量的数据库测试。`git diff --check` 与Python 3.12 `compileall`通过；独立代码审查未发现确定安全、数据流或ORM缺陷。

attempt5实际登录成功，但 `/ydental/followups` 返回403：工作台模板读取当前预约所关联的受保护capacity claim/slot，触发原生ACL拒绝。独立只读/显式回滚读回证据 `.local/s11/verification/followup265-attempt5-independent-readback-v2.json`（SHA-256 `8def40fc69a105579ee32e0ee7c3a2ee347f08a8e50471ae90d4748b24f9421c`）确认没有提交followup完成动作，followup265仍`to_notify`、event416未变，也没有contact、notification job/outbox、邮件或SMS副作用。登录的用户日志、设备日志、session及三条认证审计真实存在并予以保留。原attempt receipt与锁不重用。

本次改动在intake服务中以当前授权关系和同店reservation entitlement为边界，只沿精确claim/slot引用做受限读取并校验来源、任务、门店与状态，controller/template只传递患者ID、entitlement ID和slot start DTO；未扩大访问组。另将患者current relation lookup批处理，避免workbench每个patient重复查canonical chain。新增模型层held及started/consumed预约选项断言、合并别名A/B→C解析断言，以及无frontdesk能力但有医疗只读/复诊写能力的HTTP工作台测试。尚未证明带真实预约选项的HTTP渲染；需后续实测和独立状态读回。

task942的当前T08只读评估显示固定mapping2/catalog2属于care、event417/doc508没有义齿临床语义，且entry431/task759先排队；因此不把现有来源改作义齿采购，不访问PO147–149。S11仍PARTIAL/OPEN，通知HTTP/策略、T08适用外加工分支、F4双店端到端、T18后续、F1完成动作、影响回归及最终独立验收仍待推进。

当前续行快照（2026-10-20 06:50 UTC）：保持原分支 `codex/s11-followup-lab-r1`，HEAD `e65c078a4807b3ef6842a7df8d991c9aa861cd23`，产品addon候选 `2df07373fa5257589115d39f4354dcd4c25c2997`；分支ahead 110，未push/merge/deploy。e65为状态/报告文档提交。最新HEAD准入 `.local/s11/receipts/s11-fresh-admission-e65c078-20261020T064816Z.json` SHA `9c86da547cfd573ca5b744aabf1add91d17c1d6a3403b1ac27ec585df016e420` 经独立review PASS；receipt SHA亦绑定在当前 admission。

用户明确授权给专用S11 Store2合成采购测试用户加入`purchase.group_purchase_user`，接受原生ACL可见PO147–149；仍禁止查询、读取、使用或修改这些PO。采购组尚未授予。T08来源event417/doc508/fee415的当前只读适用性证据 `.local/s11/verification/t08-source-417-preflight-5e961f7.json` SHA `2f7898802139626724125eed4c1cd0a9d806a31a124b8bc35768a66449d36a79` 确认关系正确、无既有lab order，但原记录只有generic synthetic continuation；无义齿产品/订单行/材料语义，不能作为义齿外加工临床来源，禁止据此直接建单。

只读路由评估发现task942为pending/store2/patient364，固定mapping2/catalog2是`S10 independent C synthetic care`、kind=care。原生continuation可以创建独立新文书/治疗event且保留event417/doc508，但必须新鲜核对task/到店/资格/价格并确认该固定映射适用；不能编辑task快照。若不适用，应从另一个正常合格的合成临床任务开始。临床文字需明确标记为合成测试，并清楚记录义齿适应场景；不得由系统代码的宽松校验推导临床依据。未查询PO147–149、未写DB。

当前续行快照（2026-10-20 06:45 UTC）：原分支 `codex/s11-followup-lab-r1`、HEAD `5e961f7a36dac100351ef6b4d3e2d1c6a56ef758`，产品addon候选 `2df07373fa5257589115d39f4354dcd4c25c2997`。用户已明确授权给独立S11 Store2合成采购测试用户加入 `purchase.group_purchase_user`，接受原生ACL使PO147–149可见；仍禁止查询、读取、使用或修改这些PO。该组尚未实际授予，执行计划将采购用户与医疗/仓库操作用户分开。当前候选新鲜准入 `.local/s11/receipts/s11-fresh-admission-5e961f7-20261020T064523Z.json` SHA `e915cd4f522300734144a1b37149ebc2232f2a4fd7ae663d7ba5769b4ac66ea6`，经独立review PASS；范围包括受限scratch身份、97个已安装模块、外发关闭、S10保护计数及D/C pin。SMS guard模块已安装，代码仅阻断厂商记录SMS composer发送/排程。

获准的单次HTTP调查 run `20261020T064355Z-8dcdb386fe49` 只完成actor2318登录、`GET /odoo`与`GET /web/webclient/load_menus`：200、200、403；owned child正常exit0，服务STOPPED/18411空闲，未复现SIGSEGV。faulthandler没有fatal crash栈；日志中的`Stack`是Odoo导入测试框架路径触发的`stack_info`。请求记录 `.local/s11/operations/http-faulthandler-diagnostic-5e961f7.json` SHA `29eb324ac74bc2626f6bfa2757c8490e81bf495b9a6a5b10b1200b30f216cf45`；server log SHA `f63aeaa9b6b374f45293a1e7a7c1ccbfc2444cebfed8ef159e9ab414a62cd17d`；exit receipt SHA `d5320f258815c9c29c9ed3d32ae5aaef03678edef345f753da8628279a7539a3`。独立RR只读、显式rollback/close结果 `.local/s11/verification/http-faulthandler-diagnostic-5e961f7-independent-readback-reconciled.json` SHA `6011d2c19ca04ea9892c10c1315c85230f8533e2fa9da56655ab652aef713c76`确认只有正常登录device log、session和3条认证/门店切换审计，业务followup/lab/purchase/财务无变化。403不是HTTP E2E PASS；SIGSEGV根因未定，不再复现。

当前续行快照（2026-10-20 06:38 UTC）：分支 `codex/s11-followup-lab-r1`，报告修改前文档HEAD `24f9b63664db01f4137813f923340d9d51ae8cc8`，最近实现/测试候选 `57a3fcbc5d093de92f5f2aa13423ca3bfcff238d`，产品addon候选 `2df07373fa5257589115d39f4354dcd4c25c2997`。候选既有32项临床/队列post-tests、1项followup regression及新增F4单项MODEL regression通过；F4独立post-test保护状态读回PASS（范围有限）。当前F4资质/合作/任务只读快照见 `.local/s11/verification/f4-vendor-current-readonly-08a1050-attempt2.json`。HEAD08a及24f9为文档增量；私有runtime/admission仍绑定57a，未为只读文档HEAD重绑准入。#35仍OPEN；无push、merge、deploy。

## 当前候选与运行边界

- 分支 `codex/s11-followup-lab-r1`；最新实现/测试 HEAD `57a3fcbc5d093de92f5f2aa13423ca3bfcff238d`，本轮报告和状态文档待提交；产品 addon候选为 `2df07373fa5257589115d39f4354dcd4c25c2997`。产品候选已通过32项临床/队列 post-tests、1项followup regression；固定HEAD另通过F4 store-scoped合作MODEL回归1项，并fresh admission PASS：`.local/s11/verification/admission-57a3fcb-independent-ro-recheck.json` SHA `76813c58c3c2c86cd29c241325630682c7415fc93a24fe01e738c568552622cf`。锁定 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。较早候选 `caabf67` 的62 post-tests、旧 `98412e7` admission及前述报告内容保留作历史证据，不代表当前 HEAD 的运行态准入。分支未推送；无merge/deploy。
- 使用的目标为指定 scratch OID 2144130 / cluster `7694897083368259627`。S11 runtime、admission 与 launcher 位于本机忽略的 `.local/s11`，mode 0600；本机凭据不进入 Git、聊天、报告或请求日志。S10 main DB OID 2144129 未安装或写入；未知 8069/PID42433 未操作。
- launcher 在本候选启动过 owned Odoo 服务并执行过只读 HTTP/RPC 和浏览器工作台检查，随后正常停止。外部 SMTP、SMS、供应商、支付均未启用；本地受控 sink 只代表内部测试受理，不代表患者送达。
- 首次安装中的依赖和 Odoo 20 Registry 导入问题已在普通开发中修复；保留两次先前失败及只读保全记录，不覆写历史。当前候选成功完成带数据模块升级和测试，详见下文。

## 已取得的候选匹配证据

- **SOURCE/PURE：** addon、权限、XML、launcher 与依赖检查及本地 launcher 测试曾通过。候选 `caabf67` 新增代码的 Ruff、compileall 与 diff 检查通过；不计作实际业务 PASS。
- **MODEL / 安装升级：** `.local/s11/operations/20261019T104659Z-caabf67-followup-lab-upgrade-test/result.json`：候选 `caabf67cb0b5f50d098081dc5c6d72124f8f35e2`，退出码0；62个 Odoo post-tests、0 failed、0 errors。日志 SHA-256 `4b5810ce679579d169726724dd5292c4eedbe7a2a6c0ed9166fd890d7f28b8c9`。模块集是 S11 两产品 addon、两 test addon、必要结算扩展及因已安装核心 SMS 功能新增的 `ydental_lab_sms_guard`；没有 `-u all` 或升级 core。较早候选 `cb02075` 有一次失败升级尝试，具体错误和独立失败后保护读回见下方，保留其原始日志。
- **T11 / 独立升级后状态：** 新增 `ydental_lab_test.tests.test_t11_exam_continuation.TestS11NextDayExaminationContinuation.test_yesterday_completed_panorama_today_revalidates_cbct`，通过真实 S06/S08 检查、队列、临床、治疗服务，证明昨日全景完成后次日 CBCT 旧任务先拒绝，必须重新接诊并复核后才实际确认；不安装或绕过 `ydental_exam_test` 的 S09-only 门禁。独立读回 `.local/s11/receipts/s11-independent-post-upgrade-7f03f49-20261019T102809Z.json`，SHA `ac950a915ef7c78a991fad737f7f15280c88bf32812fa015ee34905a12acbc05`，确认60项0错、T11用例日志、96模块版本和旧对象投影保全。独立读回确认当前模块数96、旧224项保护计数未下降、S10 D/C 摘要一致、既有 S11 订单/库存/通知/费用来源投影未变。该证据注明旧行内容的限制，计数不等于逐行全库证明。
- **通知任务：** job450 的原稳定 request-id 在候选 6706 同 key 恢复；独立读回 `.local/s11/receipts/s11-independent-job450-same-key-recovery-readback-6706bc7-20261019T095200Z.json`，SHA `7211f9d83d06b1566cb7701bfbb0bbbcaa8a7d5ba3127167d8b5447844004e7f`。任务 accepted、delivered=false、attempt=1，新增一条指派给负责人的内部 vendor activity；`mail.mail` 不变；SMTP/外部 provider 仍关闭。另有先前候选的真实双连接领取结果，但在较早版本的 activity 写路径上失败，随后才以原 key 做恢复；不把较早 race 直接称为当前候选完整成功 dispatch race。
- **扫码并发：** 候选 `43af67a` 的真实普通用户模型动作 `ydental.lab.code.scan.action_scan` 由两个不同 PostgreSQL backend 同时调用同一码；均解析到合成订单181。私有收据 `.local/s11/operations/20261019T103146Z-lab-scan-race-43af67a.json`，独立读回 `.local/s11/receipts/s11-independent-scanner-race-readback-43af67a-20261019T103241Z.json`，SHA `ef4bc95f1f6db9a37d4e30239dbf7ac34d7a66a49c90e216c1843b6ab346ff36`；确认订单状态、实验室事件、原生库存、采购行和成本前后不变。该证据仅证明并发扫码只解析、不产生库存/成本副作用，不覆盖并发收货/入库。
- **T02 / T10 新增代码与实测：** `TestFollowupCrossStore.test_cross_store_referral_completes_followup_and_close_requires_reason` 在候选 `caabf67` 带数据升级中运行通过，真实使用转诊/接受/异店治疗/来源复诊服务，覆盖跨店授权拒绝、显式未关联关联、不得伪造源店预约和关闭原因。附件修复在 `ydental_access.models.ir_attachment` 内容返回路径校验受限 `res_field` 字段授权，未知字段拒绝；`TestLaboratoryAttachmentFieldHTTP.test_manager_only_vendor_evidence_denied_by_field_and_direct_attachment_url` 通过真实普通 HTTP/RPC 验证管理者可取文件、普通仓库用户可读普通元数据但字段读取和猜测附件直链均拒绝且不泄露测试标记。原首轮发现 vendor 审计类别字段错误也已修正。两个新用例均计入62 post-tests。
- **首轮新回归失败及保全：** 较早候选 `cb02075` 带数据升级运行 `.local/s11/operations/20261019T104242Z-cb02075-followup-lab-upgrade-test/result.json`，61项中2错误、退出码1。跨店用例仓库编码超五字符；附件 HTTP 用例初始化时普通经理无权创建 `res.partner`，因此安全断言未执行。独立只读失败后读回 `.local/s11/receipts/s11-independent-post-failure-cb02075-20261019T104441Z.json`，SHA `d0cd98755a821d7f76406f92befafd2462956c64fe070ffaeaa7a76679b6247a`，确认96模块、224项保护计数、S10 D/C及S11费用/通知投影未变化，服务停止且18411空闲。夹具修复后候选 `caabf67` 实测通过。失败后模块状态保全不等于失败安装升级整体回滚。
- **候选匹配独立升级后读回：** `.local/s11/receipts/s11-independent-post-upgrade-caabf67-20261019T104848Z.json`，SHA `7cc2b3e7bcff888be05dc221ce959fea44ebe4a340d07855b6eaba2faf82da58`。独立核实确切候选与日志、62项0错、96个已安装模块、原91模块哈希、224项保护计数、D/C及S11费用/通知/订单/采购/库存/复诊投影保全；运行身份、角色和scope吻合，服务已停止，18411空闲。计数及指定投影不能证明全部历史行内容逐行相同。
- **HTTP/RPC：** `.local/s11/operations/20261019T0954Z-6706-http-rpc.json`，普通合成用户539登录并切到门店1；复诊页、门店切换和 `ydental.lab.order.search_read` 均 HTTP 200，返回的订单只含本店合成加工记录。
- **真实浏览器：** `.local/s11/operations/20261019T0954Z-6706-browser.json`，同普通用户、真实 Chromium、只读打开复诊工作台并读到既有 `to_notify` 行；HTTP 200、无页面异常。此项没有在浏览器中完成复诊业务变更。
- **原生追加费用与核销：** 已提交的合成收费来源51绑定真实追加周期202，冻结演示 S05 价37.80，在实际服务确认后关联 S10 原生已过账发票97 / 来源79 / 行193。现有非费用源和供应商成本独立读回仍按旧候选路径复核；具体独立收费读回见 `.local/s11/receipts/s11-independent-charge-acceptance-b08d493-20261019T080200Z.json`，收费实现自该候选至6706未变。候选6706新增了真实 1.80 合成贷项143、不可变调整源116与部分核销54，将发票余额从37.80降到36.00；无付款或现金退款。独立当前候选读回 `.local/s11/receipts/s11-independent-charge-credit-acceptance-6706bc7-20261019T101200Z.json`，SHA `180e1d89cc409d166d27327b70ae2930e1612a214b7cb3fc666e44221cdf6b16`。
- **收费幂等竞争：** 两个真实 PostgreSQL backend 同时调用同一已提交收费修正键，经 Odoo 原生事务重试层后均返回 `already_accepted` 和同一贷项/调整ID，且只保留一条调整、发票余额不再变化。私有操作 `.local/s11/operations/20261019T1015Z-charge-credit-idempotent-race-result.json`；独立状态读回 `.local/s11/receipts/s11-independent-charge-credit-idempotent-replay-6706bc7-20261019T101052Z.json`，SHA `68f9cd70dceb6bf90460139f69ccc765c85ff177430151f1d19064fa215bc7e1`。另一次首次写竞争中直接调用 `_operate` 的一方遇到 serialization failure；未盲重试，独立只读核实最终仅一条贷项后，才对已知稳定键进行上述无副作用幂等重放。
- **真实多连接竞争：** T06 收货同键与收货后入库同键 races 在候选 `03949443` 分别使用 order432 执行，独立读回确认各自唯一持久结果；具体收据和此前准入留在 ignored `.local/s11/races`、`.local/s11/verification`。取消限于 `draft/sent/processing`、入库要求 `received`，因此合法竞争组合为取消/收货与收货后入库，不能把取消/入库伪造成同一初态竞态。 续行在候选 `73ec1c7` 用 order434 完成 T06 duplicate putaway race，runner 与独立只读读回均通过；操作事实见下方。
- **T16/T17 新证据与独立验收：** T16 order433 首轮 runner exit3 原样保留，不重放；T16 order434 在 `377ae373` 运行 PASS，receipt `.local/s11/races/20261020T014807Z-a173a69b-lab-cancel-receive.json` SHA `c8e28791a3f90400fa58a9dc0ee20e2ed2c08e901765dd0f236ec6d75bfd069f`。T17 package-code race receipt `.local/s11/races/20261020T014504Z-51ef7495.json` SHA `73163f282ae0dd0bd64554b2807a9a20d258d326b4b259792ec28a06e688511b`。两项均为数据库服务层真实不同 backend；独立验收为 RR READ ONLY 并显式 ROLLBACK。T16 event1069 赛前/赛后均读得 `draft→sent`，新收货 event1071 唯一；T17 只为433追加一个 code-bound event，434保留 sent/unbound。后续 T06 putaway race 用 order434，receipt `.local/s11/races/20261020T015223Z-2e41fc22-lab-putaway-duplicate.json` SHA `58c8f70b01d584833a20605362a3e79215a240a5f75b0dd13b54d9fc2e694cb0`；独立验收 `.local/s11/verification/race-putaway-order434-independent-readback-73ec1c7.log` SHA `78af20984e6d3aa80be91c716f72c14bb28a96376bbd568dc7044c0097b226c8`。两 backend 为 accepted/already_accepted，唯一event/move/幂等操作/audit/followup；库存目标/来源精确+1/-1，成本$42.75、患者费$137.25、order433绑定及D/C保持。 T08 discard 分支使用 order432 在 `5c69855` 上执行一次，ordinary model runner exit0、`_operate(exception, discard)` 返回 accepted；独立 RR READ ONLY + 显式 rollback 读回 order v5 exception、唯一 event1074/inventory event+move904/audit40296/operation1021。实物由义齿库移至损耗库，数量−1/+1且 reserved 不变；followup239关闭并保留内部resolution activity，既有 accepted job1012仍 accepted、delivered_at空；原收货/入库902、PO147 $42.75、fee384 $137.25保留，没有新增fee/charge/credit/refund/fit，D/C摘要一致。证据 `.local/s11/verification/t08-discard-order432-independent-readback-final.log` SHA `dc2f2403d06e041ebfc54ad06aa532fa62698f507bc3b19551fb7b78b562ed7e`；receipt `.local/s11/races/20261020T020257Z-t08-discard-order432-committed.json` SHA `0e65d9374140660dd250e589155628bced4fd8fa1d08dcfb49d0e87f974b8e15`。第一次/第二次 harness 分别因关系类型断言/无效 inventory domain 字段在业务调用前退出1，未建session、未写业务；保留日志SHA `370909d6245bf609113b250468406061a555d08f2fd9a2efab65c8c4e04637f1` 与 `291947bb3a81708a8ab8b7311c4af3c3983b9dd74bb701babe7b4bdc19cd4292`；修正后第三次执行退出0，日志SHA `9c4eaf9a97f248f28a50cda66261a81e4fa43c0496e22dc617e3046106d3f5b3`。supplier_return处置分支仍未实测。
- **T17 夹具与保护：** 为取得第二张合格活动订单，按正常 S06/S08 与采购流程新建 event388/doc388/fee386（$137.25）和 PO149/line149/order434（$42.75）。source 独立读回 `.local/s11/verification/source388-independent-readback.log` SHA `a0db668353629134c2a018a854d90bb9a208c26cab95fbd7cf24acb416aca9a`；fixture 独立读回 `.local/s11/verification/fixture-source388-independent-readback.log` SHA `b9bf933f4956e68c1f171df982be1cd2767f773f9bcca28820c2db29a3cd6f6f`。两阶段均无库存/外加工/复诊/通知副作用；D/C 标量投影保持 `33f8730aa39cc869e749827e66f10505a0fe9e5aedd5677c9cb1b17718202ae8`。
- **S10保护：** 独立收费/通知读回均核了 D/C 财务链摘要及相关 S10 计数。旧D6收款、2退款、净4链没有重演；S10原文书、附件原件、旧日结与审计没有为 S11 重新操作。

## 2026-10-20 continuation checkpoint

本轮在候选 `1b8f5b6` 上将task720正常报告至queue position408/entry408；queue enter/call/start已提交为execution400/lease400。resume runner因clinical service参数签名错误在clinical.open之前停止，未创建clinical document、treatment event、fee或material consumption。原token不在receipt中且不能从hash恢复；expired lease经固定原生`ydental.queue.service._timeout()`按唯一expired active ID 400回收。timeout receipt `.local/s11/races/20261020T-native-timeout-lease400.json` SHA `f20a744923d68aa4676f2cfc5f3843f32178c1484a350bc18dafe4e911a44e4f`；独立RR READ ONLY回读 `.local/s11/verification/t18-native-timeout-expiry400-independent-readback.log` SHA `5e00d0ff195b0f8bd0b459c34291ce925a514a478b29c223b0ca42d9f70cc22`确认lease400 timeout释放、execution400/entry408为verify、task720仍started v6、position408 inactive、唯一自动审计40339；lot144 qty1/reserved0、area1294 open v10。临床模块的takeover要求先有已保存真实文书；这次失败发生于open前，故不takeover、不重报、不重开task720，station1继续被verify execution保护。

当前candidate `98412e7` fresh admission PASS，服务停止且scope有效；receipt见上。独立RO资源核验：store1只有station1，user8的execution400仍verify；user6具station capability但不能越过站点fence，users539/952没有该capability。store2有station2和合格普通clinicians users9/10，但其mapping/catalog对应的published prices 2–5均已于2026-10-19过期，vendor98没有store2 cooperation，且未发现普通warehouse-write actor。候选S11 synthetic confirmed treatment event扫描没有安全可复用记录：13条S11合成治疗事件属于patient150/orders432–435/source388保护链；其他无followup事件属于S10保护链。扫描证据 `.local/s11/verification/f1-followup-candidate-search-15a6624.json` SHA `fb4c5ecc3354c280b4d6629494acf4a77ca95a18a706431c3c9ef89022a1143c`。因此F1、T08 supplier_return、通知端到端、F4双店合作、T18戴用/followup及F2首次收费并发仍未完成；这些下一步都需要建立真实的新合成治疗来源并有合格服务站/价源/普通操作权限。未改业务语义、未触及S10保留对象、未运行外部通道。`#35`保持OPEN，状态 **PARTIAL / IN_PROGRESS**。

## F1–F5 与 T01–T18 覆盖状态

候选 `caabf67` 的一次测试命令实际通过62个post-tests，不是62个需求，也不能把下列部分证据升级成场景全PASS。候选及层级按独立审查与原始结果限定：

| 项目 | 当前证据与缺口 |
|---|---|
| F1 / T01、T13 | 生命周期模型测试涵盖提醒、未接通、联系成功、超期、预约关联/改期和真实接诊关联；actor2318对confirmed event414创建followup265，并在attempt12通过真实浏览器关联后续合格event416。POST返回303、工作台刷新200/条目消失，独立已提交状态读回确认done/seen、唯一event416/execution536及唯一完成审计；attempt12详情见本报告顶部。跨店接诊 T02 新模型闭环在 `caabf67` 运行通过。 |
| F2 / T07、T18 | 免费返工、成本与患者收费分离、S05冻结价、实际服务后原生出账及版本贷项模型测试通过；task941首次收费两连接竞争中一方提交invoice179，另一方收到mutex更新SerializationFailure。独立读回先确认无loser receipt且无第二经济事实，再对未提交的同一幂等key单次恢复，最终两个receipt key指向唯一posted unpaid $7 invoice179；payment=0、库存/材料与D/C不变。runner未保存原始backend PID及loser响应，故限称数据库竞争加核实后的幂等恢复，不称两路并发直接成功。完整 unknown 通知→返工周期链仍缺。 |
| F3 / T08、T16 | T08 discard/报废分支有模型覆盖并已有真实持久状态独立读回，验证实物损耗去向、成本与患者费用未变、待办关闭且无假戴牙/退款；supplier_return分支尚未实测。T16 首次在 order433 执行时 runner 退出3；根因为 before/after 事件字典使用了不对称字段投影。独立读回确认当次恰一收货业务结果，但赛前两列不可证明。提交 `377ae373` 统一补读并新增纯测试后，order434 的 T16 race runner 与独立读回均 PASS：两 backend，收货一胜；取消在明确 SerializationFailure 后有界重试并观察状态冲突；旧 event1069 的 before/after 原始值两侧一致，新 event1071、audit40283、operation1019 唯一，无库存/复诊/成本/费用副作用。独立证据 `.local/s11/verification/race-cancel-receive-order434-independent-readback.log` SHA `dba6892be4087d13d3acac8bf4339120ebf73387e264e08a51d094fc1d5064d4`。|
| F4 / T15 | 资质审核、合作/开单约束、过期旧单与内部活动消息测试通过；T10 HTTP回归验证普通仓库用户不能下载管理组限定厂商资质附件。当前候选新增模型用例 `TestLaboratoryGuards.test_vendor_cooperation_is_store_scoped_within_shared_company` 通过1项post-test、0错，检查同公司门店不能复用对方的合作；operation/result/log在 `.local/s11/operations/20261020T063019Z-f4-store-scoped-model-test/`，log SHA `129dd9c2f0c0b4975e384bb5da6e7c5205ccfde6ad893dc2cd21758a71494384`。 最新候选`789619f`另以真实ORM/原生审批和两名店内warehouse actor运行`test_vendor_qualification_and_cooperation_use_real_store_scoped_records`，通过1项post-test并独立读回PASS（详见顶部F4/T15段落）。独立post-test RR读回PASS（限定范围）：`.local/s11/verification/f4-posttest-independent-readback-facts.json` SHA `f9632b35fc463bf18746ded9bbca7e4e5eb1ceeecf44b9a97099cccb5318672a`，核对224保护计数无下降、D/C pin、测试窗口业务表零增量、T08/T18相关投影、PO成本和job语义、service stopped/18411空闲；explicit rollback/close。原自动读回FAIL `.local/s11/verification/f4-posttest-independent-readback.json` SHA `d172ef5e8def3537081488e8d10ee69d86ba5d582d5cd57469e73980da4e4ec2`保留；原脚本将旧投影字段名硬匹配且要求工作树clean，而主控同步中的两处仅文档变更导致其总判定FAIL，候选与测试/运行/准入绑定本身一致，补充事实读回修正该解释。这仍非双店端到端合作矩阵。最新当前数据只读快照 `.local/s11/verification/f4-vendor-current-readonly-08a1050-attempt2.json` SHA `63b6df0a7215490e8a1cd8aced69888ebbf64f8b45fab9985638171d85e330a8`（HEAD08a、RR READ ONLY/ROLLBACK/close）：vendor98为approved/company1、有效至2026-11-18，cooperation98(store1)、235(store2)均active；vendor249为approved/company1、valid_until 2026-10-20，cooperation236(store2) active。job450(store1/vendor98) accepted/attempt1/no delivery timestamp；job1050(store2/vendor98) pending/attempt0/due 2026-11-18；job1051(store2/vendor249) accepted/attempt1/no delivery timestamp。均无外部送达事实。该快照早于当前HEAD，但当前HEAD08a仅增加报告/状态文档；不把快照当E2E验收。T08可行性快照仍缺store2 lab order及同actor的medical+warehouse权限；新增purchase组会扩大company级可见范围到受保护PO147–149。无权限扩张或PO写入。 |
| F5 / T06、T14、T17 | T06 order432 收货及入库 duplicate races 在候选 `03949443` 已实测并独立读回；order434 在 `73ec1c7` 的入库 duplicate race 也完成 runner 与独立持久读回，详见前述 SHA。T17 在 `377ae373` 对 order433/434 执行两个 backend 同码竞争：433 唯一绑定，434 收到 `code_conflict`；event1070/audit40278/operation1018 各唯一，数据库 unique constraint 报错经产品冲突映射对应 loser 结果；库存、成本、费用与 D/C 未变。独立读回 `.local/s11/verification/race-package-code-433-434-independent-readback.log` SHA `b467643311661cf57a7e087c64101abcdacb04b102a78be122f096ee7716c0f4`。T14预约版本仍只有模型证据。|
| T03、T04 | 模型覆盖unknown、签名、重复/乱序、冲突和取消后不复活；候选`7bd9f0d`新增HTTP `HttpCase`真实路由定向验收：有效HMAC accepted/delivered、重复event duplicate且唯一receipt、invalid HMAC 403，独立post-test回读PASS（详见顶部T03/T04段落）。回调HTTP路径不调用transport；真实供应商通道仍NOT_RUN，T05/T12策略端到端未完成。 |
| T05、T12 | 免打扰/退订/日上限/未配置及通知失败不阻断人工加工有模型覆盖。event417新建followup272的真实Store2浏览器链验证无已验证联系时进入`to_notify`、仅留内部activity且不建job/contact；独立持久读回PASS（见本节上方）。完整controlled-sink自动派发、静默窗口/退订/日上限端到端仍未完成，因为没有合法可用联系偏好/联系方式；真实通道NOT_RUN。 |
| T09 | 完成后关联返修单的模型测试通过；独立只读读回 `.local/s11/receipts/s11-independent-t09-post-fit-repair-43af67a-20261019T103711Z.json`（SHA `8b052154098557d4e43eec8eb1c58f88f7449f8f5e336f8315bd43eea4a99e09`）确认父订单200仍完成、治疗与义齿出库事件保留，恰有一个独立返修子单249并有自身收货/采购成本/复诊待办。此为持久状态读回，不是新操作或并发测试，也未证明每条历史记录内容不变。 |
| T10 | 无权来源/未知码与病历边界有模型/HTTP覆盖。候选 `caabf67` 新增真实 HTTP/RPC 附件回归通过：普通仓库用户的直接附件 URL 被拒绝，管理用户下载成功；失败负载不含合成标记。 |
| T11 | 新的 S11 专用 TransactionCase 已在候选7f03随完整带数据升级执行通过（计入60 post-tests），独立读回确认；通过实际检查/续诊/CBCT复核服务链测试昨日全景已完成、次日未复核拒绝旧CBCT、续诊并验证后才完成。S09-only `ydental_exam_test` 门禁保持未绕过。证据为上方升级日志与独立读回。 |

独立覆盖矩阵完整结果以本段为准；不将未执行/旧候选验证写 PASS。外部通知测试 sink 与真实 SMS 分列：真实供应商 **NOT_RUN / OUT_OF_CURRENT_ACTIVATION**。

## 独立验收、状态与下一步

独立审查（实现者未给自己签收）确认：S11收费来源/费用成本分离与S10原生出账、贷项契约；T09持久状态、T02/T10 HTTP/RPC、升级保全读回；T06/T16/T17真实多连接动作和独立状态读回；T08 discard处置、task941首次收费竞争后状态；F1 followup265真实浏览器完成和followup272无contact人工兜底；T03/T04 signed callback HTTP；F4/T15真实ORM资质审批及双店scope隔离。当前`PARTIAL / IN_PROGRESS`：自动通知策略端到端因缺已验证联系渠道未运行；supplier_return及完整F4采购/收货链缺合格义齿临床来源；T18后续返工/返库链未完成（task720失败后按原事实保持verify、不takeover）；最终综合影响回归及独立总验收仍缺。旧SIGSEGV日志与后续HTTP浏览器成功尝试均保留，不重试旧run；#35保持OPEN。

已知差错与修复保留：早期安装缺 Python `phonenumbers`；Odoo20 registry import路径已修；ruff排序曾破坏模型依赖import顺序并导致模块注册失败，已恢复依赖顺序；Odoo mail.activity默认消息可能触发邮件，现通过 quick-update 抑制活动邮件并限制 vendor message API；通用 composer/template及可选 SMS模块存在外发路径，新增 vendor guard 与 `ydental_lab_sms_guard`，普通 reader 负测确认不会增加短信/邮件。各失败、候选、日志与保全读回仍在本地 ignored `.local/s11/operations`/`receipts`，最终交付前需生成不含秘密的可发布证据索引。

剩余工作继续限于 S11：补齐适用异常、通知、资质/合作与返工闭环，并完成浏览器业务步骤、必要影响面回归及独立最终验收。任何需改业务语义或放宽安全门禁的事项不自行处理。plan结束时更新本文件与同一 `CURRENT_TASK.md`，然后统一同步 GitHub 最终结果并按证据处理 #35；此前不发布 Issue 中间评论。

当前 owned Odoo 已停止；正式效果入口仍需在最终报告列出正常 launcher、普通角色及可复现步骤。无生产批准，不合并、不部署，不启动 S12/S13。


## 2026-10-20 S11续行：过期预约队列守卫与实际到店报告

固定候选 `2df07373fa5257589115d39f4354dcd4c25c2997`，分支 `codex/s11-followup-lab-r1`。新增只读预约资格检查：预约结束、资质/发布价失效或预约业务日期不符时，未开始的保留任务不进入 queue call 候选，queue start 再次核验并拒绝已过期资格；已开始、暂停、交接、完成的任务保留已消费预约容量语义，避免过期原时段阻断当前执行或后续流程。队列返回服务资格复用同一检查。修改涉及 `ydental_queue/models/ydental_intake_service.py`、`ydental_queue/models/ydental_queue_return.py`、中文翻译和 `ydental_clinical_test/tests/test_document.py`。

本候选的 S11 兼容临床/队列升级回归为 32 post-tests、0 failed、0 error；完整私有日志 `.local/s11/operations/20261020T043731Z-clinical-queue-expiry-handover-regression/odoo.log`，摘要 `result.json`，日志 SHA-256 `131ad44f558fd0fe56300aa1d21792e07225ec9bc98dc70bfb0597d2013ecf16`。followup 生命周期精确回归 1 post-test、0 failed、0 error；证据 `.local/s11/operations/20261020T043813Z-followup-completion-regression/result.json`，日志 SHA-256 `a171d64a18fcbd1ce2a6f64718ae24d2c0fe150aa0d64e068249c879ec4d1927`。更早的错误测试选择（0 tests）不计通过；32测套件发现的 suspended 任务错误已通过同一容量语义修复解决。此前 started 状态错误及后续修复细节不覆盖，原始日志留在 `.local/s11/operations`。

独立 post-suite RR READ ONLY/ROLLBACK 读回通过：候选/DB身份匹配；task758 recovery→execution421/entry430/lease421→task799/ent485/claim503链保全；task759/entry431、slot1297/1299、protected counts与D/C摘要未变；无新增治疗、费用、库存或通知外发事实。一个 inventory mutex 内部时间戳触碰（revision0/write_uid1）被准确记录，不伪称完全无DB写痕。证据 `.local/s11/verification/queue-clinical-followup-postsuite-readback.json`，SHA-256 `faf3d15caf24cdad930e2d3d784f6341af5a5e82ee5e84f41219bcef62e7abba`。独立准入复核确认候选/受限角色/DB与运行时绑定有效，无ACL更改；其他数据库上仅继承PUBLIC CONNECT，`odoo20_dev.public`另有继承PUBLIC USAGE/CREATE且已记录，未撤销全局权限。见 `.local/s11/verification/admission-2df0737-ro-recheck.json`，SHA-256 `ab2c17485d825c348e800356b29248d6560ef1442aaa3c9d4c4d8ebc43fef61a`。

本轮 RO 前置核实后，以actor9本店普通前台身份，通过原生 `ydental.intake.service._operate('report', ...)` 对patient364/task799 version2登记排队，复用已存在的当天arrival359，没有重复arrive。动作发生于 `2026-10-20T04:41:51.779672Z`，返回position544、task v4、waiting。受限于待排 slot1297在05:09 UTC开始，后续接诊不得提前调用或跳过原生队列。执行receipt `.local/s11/operations/store2-patient364-task799-report.json`。独立RR提交状态读回待本节续记；本次report不构成治疗、戴用、followup完成或计划完成证明。

当前仍未完成：T08 supplier_return；F1完整浏览器生命周期（followup265已建但未由后续合格事件完成，浏览器POST后投影未确认）；通知 unknown/策略端到端；F4双店资质合作矩阵；T18 continuation/followup后续及最终影响回归；F2首次收费并发；以及独立最终验收与计划收尾。原task720在clinical.open前失败后已timeout转verify，不takeover/不重报/不重用。真实供应商/短信仍NOT_RUN / OUT_OF_CURRENT_ACTIVATION。#35保持OPEN，未向GitHub发布中间更新；无push、合并或部署。

## 2026-10-20 S11续行：task799原生治疗与handover

固定产品候选 `f423cc7363b399e0e1713f5674e33d62eb94e590`，原分支不变。预约1297真实开放后（DB UTC 05:09:25），普通store2医疗角色actor10在单一原生事务中接诊已等待的task799/entry544，建立execution534、打开并保存临床文书505，执行一次合成catalog2治疗并按 `demo_confirmation` 形成event414、price snapshot511（price455，USD 7.00）及fee412（$7）；无材料、库存、invoice/payment。handover创建/复用 continuation task940 并退出lease541。操作回执 `.local/s11/operations/task799-native-clinical-handover.json`；运行摘要 `.local/s11/operations/task799-native-clinical-handover-run.log`。文书handover后为pending v2；治疗事件固定关联handover前保存的v1，immutable versions 1/2各一条。task799进入handed_over v7、continuation940仍pending，因此不冒充后续continuation完成。

独立RR READ ONLY/ROLLBACK读回最终PASS；attempt4证据 `.local/s11/verification/task799-clinical-handover-independent-readback-attempt4.json` SHA-256 `7dd2c6515b06d32a2768558a2141db13b5e08ee614f7bc1654039f13077cd04b`。核实DB/OID/cluster/受限角色与候选匹配；task799/entry544/execution534 handover，lease541 inactive，position inactive；entitlement485已started、claim503 consumed、slot1297 reservation_free仍0；event414 confirmed关联doc505 v1和snapshot511/price455，fee412 $7；continuation940 pending且来源为execution534/parent task799。无消费、库存事件或stock move；224张保全表相对checkpoint无计数下降；D/C pin匹配；提交后mail/activity/message/SMS/notification/outbox均0；owned service stopped、18411空闲。早期两次核验查询错误及attempt3断言投影形状错误保留原FAIL证据，attempt4通过，不把验证器错误升级为业务失败。

T08 supplier_return前置仍有实际权限缺口：采购组ACL对purchase.order与purchase.order.line为CRUD，规则仅限制company，store1受保护单147–149也在company1。新授予store2合成用户 `purchase.group_purchase_user` 会让其获得这些记录读写范围；未创建该角色、未扩大跨店权限。继续处理不依赖该权限的范围；是否接受该company级访问须由用户在具体事实基础上决定。

## 2026-10-20 S11续行：store2 followup浏览器操作员

当时store2无followup writer。使用现有actor9 group-manager经原生访问服务创建合成user2318，company1范围、store2 membership3600/employee2287、session3589；仅授权store2 `followup:write` 和 `medical:write`，仅base internal group，无采购/manager/system组。账号回执 `.local/s11/operations/create_store2_followup_operator_attempt2.json`；独立RR READ ONLY读回 `.local/s11/verification/followup-operator-attempt2-independent-readback.json` SHA-256 `9112f562bd7dfd4254273c19d60b28689fbae044cba5849f0cfbfb96a68541d5`。224项保护计数无下降、D/C pin匹配，权限和session符合预期。

账号创建同时产生1条 `mail.mail`（state=`exception`）及6条mail.message；mail记录没有已发送状态，外发SMTP server为0，未见短信、notification job或queue outbox增量。该失败投递记录按原样保留，不删除或重试邮件；独立读回按“无外发副作用”严格检查标记FAIL，报告按事实区分“邮件失败记录存在”和“无投递”。第一次账号尝试由新用户自身执行 `_join` 而被拒，事务回滚；独立RR读回确认无账号、membership、grant、session或通知计数残留，证据 `.local/s11/verification/followup-operator-attempt1-rollback-readback.json` SHA-256 `6b1b2fc278d71e1b6f8f9c34a40c256f2143ff44258bf200a7383dba1b9bd8f7`。该工具/脚本错误已修正为管理员actor9授权加入，不重放已提交操作。


## 2026-10-20 S11续行：event414 followup创建

候选HEAD `64d841f357b66dbe76e5de91b1a5cf51271ffd47`（纯文档变更，产品代码仍为 `2df07373fa5257589115d39f4354dcd4c25c2997`）。owned launcher准入刷新后启动局部S11服务，actor2318以真实浏览器表单仅提交一次patient364 / confirmed event414的post_visit计划，计划时间2026-10-27 09:00。首次Playwright启动缺少libatk私有动态库时在表单前退出；使用仓库私有依赖路径后执行。POST后客户端投影断言未能确认结果，未重放。独立RR READ ONLY/ROLLBACK核实followup265恰一条，store2、patient364、source event414、created/responsible actor2318、state `to_notify`，证据 `.local/s11/verification/followup-265-browser-independent-readback.json` SHA-256 `9a69d9eed29eb2bab99aacf0ea2aeb4bee3313dd85ae1d838061f9d38fdf4dc3`；本地核对记录 `.local/s11/verification/followup-event414-browser-ambiguous-readback.json` SHA-256 `77ce401907712ffab9f2a45c0aa26af260b795981c826575125ec4b15aa5dd5b`。

创建仅新增1条内部activity及1条内部notification message；无notification job、outbox、email或SMS增量，外发渠道仍禁用。随后浏览器只读UI核验未找到预期workbench heading，故不报浏览器UI读回PASS；数据库独立已提交状态确认创建成功。该followup没有新的合格治疗事件，禁止用source event414自行完成。owned Odoo服务已由launcher正常停止，18411端口空闲。保护计数224项无下降、D/C pin匹配。


## 2026-10-20 S11续行：task940 continuation与HTTP崩溃边界

固定候选为当前docs HEAD `81daa65be1f158dea930a3dd76b4559015176c62`；产品代码候选仍为 `2df07373fa5257589115d39f4354dcd4c25c2997`。沿此前真实到店report task940/entry545，actor10通过普通store2医疗会话一次运行原生队列与临床链：call/start、execution536、clinical document507、一次独立synthetic `demo_confirmation` event416、price snapshot513（price455/$7）、fee414/$7；handover到pending continuation task941，lease543通过holder_exit释放。前序task799的event414/fee412保持不变；无材料/库存消耗。queue report唯一scope-version outbox id5621为store2/area2内部队列版本通知，不是患者通知或外发。

事务收据 `.local/s11/operations/task940-continuation-native-clinical-attempt2.json` SHA-256 `a24c72e91b121b08f89a9db5da84fc5e52ffed15935478bd92a219a82a1d6c60` 在commit后保持`COMMIT_PENDING_READBACK_REQUIRED`：原生DB commit已执行，脚本随后在cursor关闭后访问延迟ORM fee字段，没能写最终投影。不得重放。独立RR READ ONLY/ROLLBACK读回PASS：`.local/s11/verification/task940-clinical-attempt2-independent-readback.json` SHA-256 `62ce4fcd59bcd8db068fd5e03a47d58c8cccf2d651befd08bd2eeda45b3da152`，核实唯一execution536/event416/doc507/fee414及task941，来源、费用快照和handover一致；旧event414/fee412保留、无材料、无外发、224保护计数未下降、D/C pin匹配。补充closeout `.local/s11/operations/task940-continuation-native-clinical-attempt2-independent-closeout.json` 记录原receipt哈希和独立读回，原receipt未覆盖。第一次事务断言在commit前失败并rollback；独立读回SHA `36b729914936eb890b42bf8cc2f05ef00789397634fa2a6b602033ac45debe12` 确认无持久副作用。

followup265仍`to_notify`，源event414/doc505、无预约关联；不得用event414自行完成。后续浏览器运行仅通过actor2318认证并到达`/odoo`，没有进入followup workbench或提交complete POST。导航等待错误及SIGSEGV后的独立RR读回 `.local/s11/verification/browser-timeout-followup-final-independent-readback.json` SHA-256 `a2d3b8b3425ca2ab8a1eccb7d13adfd1f8f2731c1c6aa0e67b83a9a0d64302c1` 确认followup与event416关联未变，无contact/job/outgoing mail/SMS/outbox增量。认证产生1条无outgoing recipient的discuss.channel comment、3条accepted access audit及1个access session；因此mail_message/access_audit/access_session分别+1/+3/+1，按严格零计数变化标准不报全PASS。

owned launcher run `20261020T055248Z-18909ba92aa6` Odoo child退出码`-11`。owned service已停止且18411无监听。日志审查 `.local/s11/verification/run-20261020T055248Z-18909ba92aa6-crash-log-review.json` SHA-256 `dd0eeb3f44e5872a18d3c95208432ff4e97c29b954453df7bbbe57c0d49c0d43`：登录POST 303和`/odoo`页面后出现session rotation/registry cache invalidation，随后load_menus 403；两个missing-filestore FileNotFoundError附近静态asset后续200。日志未定位native crash原因，也没有业务action POST。依停止规则不重启HTTP/browser链路。HTTP后续失败证据与差错保留，不把导航错误当业务失败，也不重试followup。

本段对应task941首次收费竞争及其最终读回之前的状态快照；其后的续行已补做F2有限竞争与恢复验证，故本句不代表当前F2状态。T03/T04/T05/T12通知端到端、T08 supplier_return、F4完整双店业务矩阵及计划整体独立最终验收仍待处理；真实供应商/短信仍NOT_RUN。无push/merge/deploy，未向#35发过程评论。

## 2026-10-20 S11续行：task941完成与首次收费竞争

当前固定产品候选 `2df07373fa5257589115d39f4354dcd4c25c2997`，活动HEAD `1776c4e3520b742ac47ba874c5616bfe3240991f`。fresh task941资格核验通过：actor10具store2医疗权限/capability，task941仍pending且来源、到店、活动区域/站点和有效价源匹配；过期entry431/task759按原生规则排除。actor9有普通store2 settlement写权限及有效演示会计配置。一次report提交将task941更新至v3并生成position/entry546，arrival359复用；report回执 `.local/s11/operations/task941-native-report.json` SHA-256 `0435f67f3ed4af45f1495c3ceb35ec8069bbcbc8859f92b6bfab9912369de358`，独立readback `.local/s11/verification/task941-report-committed-independent-readback-1776c4e.json` SHA-256 `8110c9aa0a794bf39cdec5c5f7efa85e400a4bcdf9539aac46facfc43b9e21b7`。

actor10随后沿原生队列/临床/治疗路径一次完成task941，生成execution537、document508、event417、fee415（$7）、price snapshot514（锁定price455）；handover生成pending task942，lease544按`holder_exit`释放，没有材料消耗。操作receipt `.local/s11/operations/task941-native-clinical.json` SHA-256 `340b5c831219f5d2b7ae0926e33ac40ef408640b686d7082a5418eaaec046de5`。最终独立RR只读复核 `.local/s11/verification/task941-final-independent-ro-recheck2.json` SHA-256 `785da3fb188c5511aacb66cbf6e77fdc74f4f89f9a55b6c1fe1af345d37f17ae` PASS，显式ROLLBACK并关闭连接；核实新链唯一、旧event416/fee414及task940保留、task942待办和lease状态正确，保护库存/材料/财务计数与D/C pin符合预期，无fee415结算来源或外发副作用。早期独立读回FAIL因错误假设handover投影和receipt数量，保留原件并以复核解释，不覆盖历史；首次收费runner两个前置脚本错误均发生在数据库业务调用前，已修正后仅运行一次。

fee415首次发票竞争以两个同步barrier的独立数据库连接调用原生settlement。一次操作提交invoice179；另一操作在更新原生结算mutex时收到PostgreSQL `SerializationFailure`。runner随后在cursor关闭后延迟访问ORM字段，导致结果组装失败，未持久保存backend PID和loser原始返回值，因此没有重跑竞争。独立RR状态核验先确认fee415仅关联一张posted `out_invoice` invoice179（$7、residual $7、`not_paid`、payment_count 0），仅一条settlement source；loser key没有receipt，也没有第二张票、退款、贷项、付款或外发。基于该独立事实，仅对缺失的同一幂等key调用一次原生bill，得到既有invoice179并新增该key receipt，没有新增经济事实。最终独立只读读回 `.local/s11/verification/task941-first-invoice-race-final-independent-readback-1776c4e.json` SHA-256 `a345374fccf743834506374beeed59fdbf99402bfd6d0aa6e7288a8f43c55af2` PASS：两receipt key映射同一invoice179；move +1、line +2、source +1、settlement receipt +2、payment不变；库存/材料/D/C及邮件、短信、job、outbox无非预期变化。该证据代表真实数据库竞争和基于核实的幂等恢复；不代表两路并发调用均直接成功。首轮失败审计 `.local/s11/verification/task941-first-invoice-race-independent-status-audit-1776c4e.json` 保留为不完整的历史观察，不覆盖。

T08 supplier_return仍未运行。只读评估 `.local/s11/verification/t08-supplier-return-feasibility-1776c4e-final.json` SHA-256 `169b8b38070e6909757e15866ff1572bba3fc8bb45c66af45e148b14c88b0552` 显示store2有vendor98/cooperation235但无lab order；warehouse actor2043权限与medical actor不重合。supplier_return需要同时具store2 warehouse/medical权限的同一actor和已入库订单；完整PO成本来源还需要`purchase.group_purchase_user`，其ACL为CRUD、规则按company过滤，会覆盖company1受保护的store1 PO147–149。未授予该组、未触碰这些PO。此前用户的“授权”未指明是否接受这一company级访问扩展，因此不作为扩大访问权限的决定；其余不依赖该范围的计划项继续独立推进。

为补足F4当前候选可安全验证的门店隔离行为，新增 `ydental_lab_test.tests.test_lab_guards.TestLaboratoryGuards.test_vendor_cooperation_is_store_scoped_within_shared_company`：同一company范围下，合作查询对store1命中、store2无合作则拒绝。固定候选 `57a3fcbc5d093de92f5f2aa13423ca3bfcff238d` fresh admission由独立RR只读核验PASS，证据 `.local/s11/verification/admission-57a3fcb-independent-ro-recheck.json` SHA-256 `76813c58c3c2c86cd29c241325630682c7415fc93a24fe01e738c568552622cf`。精确MODEL运行退出码0、1 post-test、0 failed、0 error，`--no-http`；result `.local/s11/operations/20261020T063019Z-f4-store-scoped-model-test/result.json`，完整私有日志SHA-256 `129dd9c2f0c0b4975e384bb5da6e7c5205ccfde6ad893dc2cd21758a71494384`。同时修正该测试文件原有的Ruff告警（UTC别名及嵌套定义空行）。独立RR post-test事实核对 `.local/s11/verification/f4-posttest-independent-readback-facts.json` SHA-256 `f9632b35fc463bf18746ded9bbca7e4e5eb1ceeecf44b9a97099cccb5318672a` PASS：候选/运行/准入绑定一致、224保护计数无下降、D/C及订单/PO/job语义投影匹配、测试窗口相关业务表无写入、服务停止、事务显式rollback/close。首次自动汇总FAIL保留于 `.local/s11/verification/f4-posttest-independent-readback.json` SHA `d172ef5e8def3537081488e8d10ee69d86ba5d582d5cd57469e73980da4e4ec2`，其字段映射与dirty-doc检查问题已在补充事实读回中解释。该用例是模型层隔离断言，不能证明真实双店审批/开单/收货端到端。

HTTP/browser owned run `20261020T055248Z-18909ba92aa6`在followup真实完成POST之前以SIGSEGV停止，launcher已停、18411空闲。只读检查的run记录与server log没有native栈；`coredumpctl`无对应条目，`/var/crash`、`/var/lib/apport/coredump`、`/var/lib/systemd/coredump`也没有可用dump。现有日志审查 `.local/s11/verification/run-20261020T055248Z-18909ba92aa6-crash-log-review.json` SHA `dd0eeb3f44e5872a18d3c95208432ff4e97c29b954453df7bbbe57c0d49c0d43`只确认登录后到`/odoo`、load_menus 403及child exit -11，未定位native原因。故followup265真实完成、T03/T04回调HTTP、T05/T12端到端策略链、SIGSEGV后影响回归均仍缺；不重启或复现。F4双店合作矩阵仍未完成端到端部分。真实外部短信/供应商未启用；#35保持OPEN，无Issue中间更新或push/merge/deploy。
## 2026-10-20｜SIGSEGV 有界恢复评估处置

用户调整了 S11 的项目自定恢复标准：不再要求定位 SIGSEGV 精确根因作为继续的唯一条件，但原始崩溃、未知提交/数据风险和实际工具安全停止条件仍有效。阶段一停止无新增证据的重复调查，正式状态为 **`ROOT_CAUSE_UNDETERMINED`**。这不是根因修复，也不表示运行已恢复。

原始证据来自 `.local/s11/runs/20261020T055248Z-18909ba92aa6/`，候选 `81daa65be1f158dea930a3dd76b4559015176c62`。`exit.json` SHA-256 `4949fb84277ac17f6354e42509e15cc90b1e4793223ad69160fe11a524d153f4`：子 PID `3536662`、Linux start ticks `95156031`、exit `-11`、时间 `2026-10-20T05:55:45.911374Z`。`server.log` SHA-256 `0a3c75dc015872b417c7bc5c7877fc95993e0024fe836ae77f93defadba46854`；既有有界日志审阅收据 `.local/s11/verification/run-20261020T055248Z-18909ba92aa6-crash-log-review.json` SHA-256 `dd0eeb3f44e5872a18d3c95208432ff4e97c29b954453df7bbbe57c0d49c0d43`。日志观察到登录 POST 303、认证后 `/odoo` 与资源 GET 200、菜单 GET 403，以及两条 filestore `FileNotFoundError`；没有业务变更 POST、native crash stack 或可确认的业务数据库提交。日志审阅明确指出数据库提交状态未核实，不能由日志推断为零。run 目录只有 exit 和 server log，父进程 PID 是 `NOT_CAPTURED`。无可用 core/OS dump；此前 faulthandler 诊断 exit 0 且未复现，`13be108`仅改进 launcher 的 signal/exit 归因，不是产品根因修复。**不重放旧请求、不重启旧服务、不作根因推测。**

当前按阶段二提交独立恢复门槛审查，须判断固定候选、旧业务提交状态、指定 scratch/OID2144130、已有数据保护、进程归属与权限是否充分可信。若审查发现工具实际拒绝、未知提交或数据完整性异常，相关路径不得恢复。只有独立审查通过且常规运行许可有效，才可执行新建的、loopback、只读、最小范围 HTTP 稳定性请求；不复现原 POST/`/odoo`/菜单请求，不做临床或经济写入，遇崩溃或数据变化即停止。通过单个只读 endpoint 也只证明该 endpoint 的本次有限观测，不证明崩溃已修复或所有路径稳定。

此前 `bed99cf` 上42项 post-upgrade MODEL 回归、限定带数据升级与保护读回均保持已完成，不重复执行。返工来源 catalog 只读结果仍显示 `ydental_fee_id` 可空且唯一约束/index 存在；不清理历史 NULL 或为补 NOT NULL 破坏合法费用来源。F2 原始 loser/PID 缺口保留，不重放。当前状态文档候选为本地 `f5c64a8`，本追加记录待提交；未 push。plan 未完成，#35 保持 OPEN。
## 2026-10-20 11:22 UTC｜有界只读 HTTP 稳定性探测

独立恢复门槛收据 `.local/s11/verification/sigsegv-recovery-gate-e6b60e6-v2.json` PASS（SHA-256 `e0b0668faca7a67fcd255de610c9f17aa26124083c36d1e5bf79576fb8d8200c`），范围仅允许对S11自有loopback服务执行一次未认证raw-client GET。fresh exact-e6准入 `.local/s11/verification/admission-e6b60e6-independent-ro-recheck.json` PASS（SHA `eba4b698db35d3330206cf1e11cef311ea5c0ba3999f804bca13cb28445404e2`）；核验scratch/OID2144130、受限角色、224保护计数、D/C pin、97模块、外发禁用及服务停止。原崩溃父PID缺失、全DB提交不为零的证明缺失仍明确保留；独立审查只认定没有证据显示相关follow-up业务提交。

在候选`e6b60e6ca8da112d42609e6f1d9c2995cd56afa1`上启动自有run `20261020T112044Z-fc4811c5b7a9`（child PID3763917/start ticks97123683），以无cookie、无认证、无redirect、无JS的`http.client`恰发一次 `GET http://127.0.0.1:18411/ydental/queue/screen`。返回HTTP200，1505 bytes，body SHA-256 `f17ee1d5e161ada80313ce7fb00cc7f62d1020e0160342ecff4adf5fad8afec8`，client exit0。probe收据 `.local/s11/operations/http-probe-e6b60e6-20261020T112044Z-once.json` SHA `39335ddd8585cea1890f7f264c7cea34705bf62f5dee5d55683fe5413781850a`。服务由正常S11 launcher owner验证后停止，exit0/`stop_requested`，exit receipt SHA `9cfbd0708adbef24f4162bdc0f715f541f1c5d2149532f8b1ec0ceff0d8de424`，server log SHA `b3efb594bdb604466328c11ec12cce8c1bdffb8d821bff6f0230bbd3a81164d9`；日志中恰一条请求，无SIGSEGV标记。启动仍记录既有test-framework import ERROR级诊断，未隐去。

独立post-probe RO读回 `.local/s11/verification/postprobe-e6b60e6-20261020T112044Z-readback.json` PASS，SHA `cd0baef793cccdbbe645b848181cc8cc2afc9ee3f23d12cbb2d77bfa4bab912d`：224保护计数、D/C、模块、15张S11副作用表、外发及runtime hash均未变化；服务停止、18411空闲；只读事务显式rollback/close。此结果证明本次单个静态screen GET与服务观察成功，**不证明SIGSEGV已修复、不解除一般HTTP/browser STOP、不证明临床/经济写路径稳定**。根因继续为`ROOT_CAUSE_UNDETERMINED`。接下来只按用户批准逐步做独立合成业务；每阶段须 fresh admission、真实业务身份、逐项幂等与独立提交读回。#35仍OPEN，不push/merge/deploy/S12/S13。
## 2026-10-20 11:32 UTC｜合成前台身份预备操作

针对精确候选`b22e88d3cea18b970ac650b95ae20c64e2455638`的fresh RO准入和actor2466 Store2写权限复核均通过（receipt SHA分别为`9b7fd973…f0386d27906`、`643ff69f…c2474c74`）。正常JSON-RPC认证返回actor2466；访问`/ydental/access`后，登录scope自动绑定Store2并记录正常审计；一次`POST /ydental/access/action`返回HTTP200。

客户端在处理该原生JSON revision响应时错误地期待mapping/object，提前退出，患者创建请求未发送。不得把这次客户端错误算作业务拒绝或患者业务失败。唯一运行`20261020T113011Z-07c127de8445`的子进程正常退出0/`stop_requested`。原请求收据SHA `22bcf2e0…df50670`，exit SHA `22717a17…b38`，server log SHA `2f252fd9…fe0c`。

独立RR只读回执 `.local/s11/verification/synthetic-patient-create-b22-postattempt-ro-corrected.json` PASS，SHA `b30ac502…14b3d3`：确认仅创建一条新的actor2466 Store2 session/revision1，login、login.scope、store.switch三条成功审计及设备/登录记录；本次拟用patient create key没有操作记录，patient.create审计为0；224保护业务计数无变化。事务显式rollback/close。初次只读回执因本地断言字段写错被保留；校正回执使用同次查询结果及原始run receipt，没有重查或重新发HTTP。

完整Odoo log还记录4条actor2466 `source.read`权限拒绝信息；真实目标未记录，故不推断。它们不是该次登录或Store2切换的HTTP拒绝（认证、页面、切换都返回200）。保持权限缺口事实。下一步需修正仅客户端revision解码，使用新session与唯一患者key；未创建患者，patient650/task720保护保持。该预备操作不是临床闭环通过。
## 2026-10-20 11:42 UTC｜新合成患者HTTP创建及独立提交读回

当前仍在原分支 `codex/s11-followup-lab-r1`；本记录对应业务候选 `4d126a69fd702462a3d33d5d8d0d7fd27a8f7561`。患者创建前fresh RO准入 `.local/s11/verification/admission-4d126a69-pre-create-independent-ro-recheck.json` PASS，SHA-256 `93c21c58a4856eb509bd693f22b7474590ef12f5baa7c187155bae7d4ca50792`；目标scratch/OID/cluster/受限role、保护计数、D/C、模块、外发关闭、actor2466 Store2权限和credential file mode均匹配。

attempt1在客户端active run marker校验处停止，未发HTTP。attempt2仅进行了正常JSON-RPC认证、`GET /ydental/access`和一次Store2切换，三条HTTP请求均200；客户端误把`/ydental/access/action`的JSON `{revision: ...}`响应用另一结构解析，因此没有发`/ydental/patients/action`。该正常登录/switch提交独立读回 `.local/s11/verification/patient-create-4d126a6-attempt2-independent-readback-attempt2.json` PASS，SHA-256 `e4e23a6751ea4605e2f82a1a466100960169d59714b6aceb5470b7cd5c49f887`：一个actor2466 Store2/revision1 session、login/login.scope/store.switch各一审计；患者key、patient.create audit与新患者均为0，224保护计数仅session+1/audit+3。两个脚本端错误没有触发业务拒绝或患者创建，已保留原receipt且没有重放。

attempt3使用新的私有cookie session和独立幂等key；run `20261020T114138Z-43b54bcd8be4`，candidate `4d126a6`，四个HTTP请求依序为JSON-RPC authentication、access GET、Store2 switch POST、patients/action create POST，均HTTP200。actor2466创建新的合成patient ID 682、Store2、version1，result accepted。客户端receipt `.local/s11/operations/s11-synthetic-patient-create-4d126a6-attempt3-once.json` SHA-256 `ab87af0dac3d113f1fb6aac655b3f876ba59ff42a4ca3f3a857de9957a0bb425`。owned launcher服务正常停止；stop log SHA-256 `3893e17a6c4860fe906e93a114627c721c8489260741b9993627186fb3e059a7`。

独立RR postcreate readback `.local/s11/verification/synthetic-patient-create-4d126a69-independent-postcreate-ro.json` PASS，SHA-256 `38d238de6283a3808bf153575d6c79692fefe25db592269fb107925716e0b337`：唯一patient/number/partner ownership/Store2 current relation/version1、精确operation key和accepted patient.create audit都匹配。对fresh admission baseline的224表delta为session+1、audit+4、patient/number/relation/operation各+1，其余0；D/C/module一致，RR rollback/close。该适配器的第一次汇总因external-channel数组索引错误、audit窗口边界被截到整秒而暂报INDETERMINATE；单独缺项读回 `.local/s11/verification/audit-external-reconcile-4d126a69-run-20261020T114138Z.json` PASS，SHA-256 `d33aa0a21ee0fd28854b0b8fa6775af68d6dc8db1f75fe3b9ced509307455c49`：schema确认四条记录同属`ydental_access_audit`，精确微秒窗口为login/login.scope/store.switch/patient.create四条；旧边界止于`11:41:44.000`漏掉`patient.create`（`11:41:44.319031`），总delta+4正确。SMTP/SMS/live-published payment providers及非秘密followup参数为0；事务显式rollback/close，服务STOPPED、18411空闲。

这只证明一次合成患者HTTP写路径和独立提交状态，不证明浏览器稳定、患者实际到店、预约/指定任务排队、接诊/治疗、postcommit通知claim/transport/delivery或义齿/采购流程；`ROOT_CAUSE_UNDETERMINED`继续有效，不声称根因修复。下一步固定本状态文档后为新精确HEAD fresh admission，再按原计划逐阶段执行并读回真实预约/登记、实际到店和任务报到；如服务或数据出现异常立即停止受影响路径。42项MODEL回归、限定带数据升级及保护检查保留且不重跑；#35保持OPEN。无push/merge/deploy/S12/S13。


## S11 状态续行（2026-10-20 16:17 UTC）：slot1696预约已提交并通过独立读回

- 保持原分支 `codex/s11-followup-lab-r1`，业务候选 `b3f551a8120e364df1e91b440ed8629917430e74`，本节文档变更尚待提交。S11授权范围内新建并发布slot1696（Store2/station2/capability2，16:30–17:00 UTC），随后由actor2466正常认证和浏览器提交，为独立合成patient682仅提交一次reservation；未使用patient650/task720。预约请求的GDB run `20261020T160125Z-8f8f1bb827ca`正常退出0、无信号/core并停止；exit收据SHA-256 `6dbac7319570d61caede8924f6ff089919426173e215e052758630c014f2bb22`。浏览器收据SHA-256 `708c10eee192faaeb112802c87707ad012b3c2ab63e03a1aa7d2911584410c37`；reservation intent SHA-256 `d0eacd8ecd9559c599dde806f34fa3cb598119fc6fb555acd9195699d4c0f09f`；preflight SHA-256 `d87ca1c86400050590fc01e014ad33b7aa39b275f23d8feff79b937e6761b2fa`。
- 新鲜独立准入因旧pair超过30分钟而阻止了只读读回；没有数据库连接。更新准入脚本静态独审发现并修正跨库有效写权限扫描遗漏TRUNCATE后，fresh admission通过：`.local/s11/receipts/s11-fresh-admission-b3f551a-20261020T161431Z-f39084683763a002.json` SHA-256 `40fdca72f01d180a4ff5ef7eb679693a18937c423e2c6458e01f64808f22acce`。覆盖目标scratch OID2144130/cluster、受限角色、224保护表、D/C projection，以及继承PUBLIC CONNECT的200库catalog扫描；服务停止、18411空闲。跨库PUBLIC CONNECT仅记录；无其他库关系读写权限。
- 独立RR只读读回最终PASS：`.local/s11/verification/patient682-slot1696-reservation-independent-readback-attempt4.json` SHA-256 `05dea813932bf93883a6507d8de72940f6c3ee306730ecc66b988660428e14f9`；独立收据审查PASS。确认唯一accepted操作7188、held entitlement777/claim801、pending task1183、Store2当前patient relation698、slot1696容量reservation 1→0/walk-in仍2、版本3；审计匹配、D/C pin相同、外发渠道为0。保护增量为audit+110（publish 4条+预约窗口106条）、session+2、intake operation/task/entitlement/claim各+1、supply operation/event各+2；无arrival/queue/lease、治疗、临床文书、费用、库存或followup。认证日志有3条记录早于浏览器计时0.42秒，独立窄窗只读查询已保存于`.local/s11/operations/patient682-audit-gap-investigation.log`，并纳入最终保护计数。
- 读回attempt1–3失败均为核验器/范围问题，证据保留，预约POST未重放：attempt1脚本误用Path.get并误判正常空source_task；attempt2遗漏患者预检不含D/C字段及预认证的3条audit；attempt3遗漏预约正常创建的`supply_operation`。attempt4修正后18项检查全部PASS，事务READ ONLY/REPEATABLE READ显式ROLLBACK并关闭。普通系统Python两次缺psycopg2，和一次旧准入过期均发生在数据库连接前，运行日志留存。
- 预约时段为16:30 UTC开始；在时段前不做arrival/report/queue或临床操作。下一业务动作仍需在当前状态文档形成的新HEAD上fresh admission及独立准入复核。`ROOT_CAUSE_UNDETERMINED`保持；只读HTTP探测不构成SIGSEGV修复。S11其余缺口包括实际到店及按原生FIFO排队/临床闭环、T05/T12真实postcommit dispatch/claim/sink及策略端到端、T08义齿专属临床来源/已确认原生采购服务行/收发与supplier_return、F1/F4剩余矩阵、F2历史loser/PID保留EVIDENCE_GAP及新并发、最终影响面回归和独立总验收。用户已明确授权S11相关测试权限；新角色实际grant与独立读回尚未完成，PO147–149仍受保护且不操作。S11保持`PARTIAL / IN_PROGRESS`、#35 OPEN；不push/merge/deploy/S12/S13。


## S11 状态续行（2026-10-20 16:38 UTC）：patient682真实到店与原生FIFO报到通过

- 保持原分支 `codex/s11-followup-lab-r1`。当前代码候选 `ce46e5cb5bd562519a6417a16a1a4f1525891006`；本节为后续文档候选记录。patient682/slot1696在16:30 UTC开窗后，由actor2466通过正常Store2前台浏览器执行一次actual arrival。GDB run `20261020T163156Z-0a60a7795cb6`，PID3991465，exit0、无signal/core，owned process group已停止；退出回执SHA-256 `a89c2a8b09902e54c4c633ffeb84e1bdefa27a952b038619f9b43e94ec36dc07`。浏览器receipt SHA-256 `d71f071fc48460cbc56fdf4f9ede486685a72532cb533a63b51d5b9723f81c25`；intent SHA-256 `f5db6f0702aa82a1f65a09da01b9616cd4e62470390fe6b5382d6f071f6fba1b`；arrival preflight SHA-256 `535d5e2f7b96d982251508ea791c28d1d1ac51d1f440684d745debe7a2fe2973`。唯一到店POST获HTTP303。
- Arrival独立RR只读读回最终PASS：`.local/s11/verification/patient682-slot1696-arrival-independent-readback-attempt2.json` SHA-256 `d787c9beb2c0ea8f8677660c45c74b91ff7bb12a3a00edeb89de1caf165ce7c8`；独立验收PASS。唯一accepted arrive operation7189对应persisted arrival638（Store2/patient682/actor2466/UTC）；task1183保持pending v2，没有position/queue、治疗、文书、followup或费用；匿名FIFO aggregate仍1，无lease。累计protected counts精确，D/C/财务不变，SMTP/mail/SMS/jobs/providers/outbox均0。
- 随后一次GET-only报到脚本运行在PREPARED、post_attempts0、无attempt marker，未发出任何report POST；该浏览器辅助动作仅产生正常session和audit，独立纳入下一预检的55 audits+1 session增量。原尝试保留，不作为业务动作重放。
- 修正表单定位后，actor2466通过正常Store2页面对task1183/version2仅提交一次report，HTTP303。GDB run `20261020T163727Z-556c1360aaf6` PID3995443，exit0、无signal/core并停止；回执SHA-256 `aec42354c870519a4e2131090e0b71527a2a9169c9cef186d46a4788266955f4`。browser receipt SHA-256 `4866e5fc0a5ad66e6e6666f1ad597fd3bb2dec189db7ca630809ef0f2541908b`；intent SHA-256 `a97cfe865fda1f3612f338626cd4c790bc46a14365e29e9c5246af29dbc85829`；preflight SHA-256 `d45d41c68737d92f5c707923640661a9e276e321d14cd2af512316aea38097a7`。
- 报到独立RR只读读回最终PASS：`.local/s11/verification/patient682-task1183-report-independent-readback-attempt2.json` SHA-256 `a6c96034112fbb405be1dcb55c3f8c36684aa7c73fd7397aca65b2806da5a3d0`；独立验收PASS。唯一operation7190对应active position716、task1183 state accepted/version4、queue entry716 waiting；area2 waiting由1增至2且无lease。匿名queue-order聚合count2、min431000、max716000，新条目716000在末尾，保留已有FIFO，不读取既有排队患者身份。仅增加一个store2/area2内部queue outbox版本通知；邮件、短信、notification jobs/provider均0。protected count精确delta含access.audit+384、session+5、intake operation+3、arrival/entitlement/task/position/claim及queue entry/outbox各按实际递增；财务与D/C保持原pin，治疗/文书/followup/lab/settlement均0。
- 早期核验器失败均保留：arrival attempt1因将正常login/login.scope审计错误要求非空store而FAIL，attempt2修正后PASS；report attempt1仅认证并GET页面，DOM检查停止于POST前，GDB正常退出且无marker/POST，未产生业务写入；其审计/session纳入后续准入。report读回attempt1误期望task version3、误将本地queue outbox归为外发，attempt2依据真实version4及内部queue outbox语义修正后PASS。浏览器原始响应体/凭据未持久化。
- 当前只完成患者到店、任务报到与原生FIFO入队；尚无叫号、execution/lease、临床文书、治疗event、postcommit通知、followup、义齿/采购来源、supplier_return或返工。后续按fresh candidate admission和独立核验逐步继续；不将本次无SIGSEGV写成根因修复。ROOT_CAUSE_UNDETERMINED保持；S11仍PARTIAL/IN_PROGRESS，#35 OPEN；不push/merge/deploy/S12/S13。
## 2026-10-21 00:42 UTC｜GDB下合成患者683身份登记完成

在候选 `2dbfa5c67f511d501bf7bb028222210a19cf3b01` fresh admission PASS、独立准入读回PASS后，使用GDB 17.1 owned service和actor2466正常Store2权限，仅执行一次合成患者登记。患者683/version1；operation receipt SHA-256 `7d59493e8aff9c1873b3d5ffc5feb4c56b623045dcb6c94d19bb20c9d686aadf`。独立RR READ ONLY postcreate回读16项全PASS，receipt SHA-256 `41bbbc3f6b02c55997912ab009797b8f8e284f72345f4874cd8213a0dc606b53`；224张保护表仅出现登记及正常认证审计/会话增量，D/C、模块和外发参数不变。GDB退出0、无signal/core，服务停止；exit receipt SHA-256 `c9ad718c4fd60d15de757cd09be4cc311a366d805fab5d1cd8a4e1ab91554dbd`。

该患者只完成登记，未预约、到店、报到、排队或接受临床/治疗/费用/通知操作。辅助只读核验器attempt1–5的断言/时间窗口适配失败均保留；业务POST未重放，attempt6通过。独立验收提示操作源SHA未嵌入运行回执，来源依赖run ID与执行前mtime关联。新文档提交会改变候选，下一次运行前重新fresh admission。S11仍PARTIAL/IN_PROGRESS，#35 OPEN；ROOT_CAUSE_UNDETERMINED与历史F2 loser/PID EVIDENCE_GAP不变。

## 2026-10-21 01:36 UTC：T08义齿供应商与原生服务价源资格预检

- 对固定候选 `0f03ef910c46688f56e51afed93a5cbdf76479f4` 执行只读资格预检。脚本 `.local/s11/verification/t08_prosthesis_supplier_service_feasibility_0f03ef9.py` SHA-256 `32db11bfc23487f90214faff54ef377373ae0b47151caf1ba41ee3de2eb8df10`；独立静态审核该精确SHA PASS。静态范围确认未读取PO/PO line，company/store admission allowlist在目标ORM读取前校验，supplierinfo按通用记录或具体变体匹配。
- 首次运行因脚本常量名错误在DB连接前退出，stderr保留于 `.local/s11/verification/t08-prosthesis-supplier-service-feasibility-run-0f03ef9.stderr`；改正并复核后的一次只读执行结果为BLOCKED，收据 `.local/s11/verification/t08-prosthesis-supplier-service-feasibility-0f03ef9.json` SHA-256 `53fc28c03fa82326a93eecec48112e236cc4fb3fa8253157610fe058d603fce4`。受限目标库身份、准入scope、采购/医疗角色和服务停止检查通过；没有有效已审核义齿厂商，合法的同公司服务价源组合为0。尚不能新建正常采购服务行或义齿加工单；旧PO147–149不访问。
- 此核验是MODEL/ORM只读数据调查，不是HTTP、浏览器或采购业务实测。READ ONLY和REPEATABLE READ显示通过，显式rollback调用、cursor关闭；但`rollback_idle=false`，该项保留为未通过证据且整体不标PASS。没有业务写入；不为此重复查询。具体执行错误、范围和待解条件记录于根目录`CURRENT_TASK.md`同名状态续行。

## 当前剩余任务与推进条件（固定候选：文档HEAD `4a106f3e94e7de89259fb057d28822b4df3a1d9e`；最近业务候选 `0f03ef910c46688f56e51afed93a5cbdf76479f4`）

| 计划项 | 已实证层级 | 尚缺内容 | 真实推进条件 |
|---|---|---|---|
| M1 合成患者临床闭环 | MODEL、预约HTTP/浏览器、到店与原生报到/FIFO已分别实证 | patient683到店、接诊、文书和治疗确认；patient682仍排在原生FIFO中 | patient683预约窗开放后按正常前台流程；只处理原生FIFO允许的下一条，不能跳过未知前序项 |
| T05/T12 followup通知 | MODEL callback/dispatch/claim/sink组件有覆盖 | 真实来源提交→postcommit→独立claim→controlled sink，及HTTP/browser来源事务 | 需要合法确认的合成临床来源和当前HEAD fresh admission；内部sink不等于真实患者送达 |
| T08/F3/F4 义齿、采购、收发与返工 | 现阶段仅完成只读资格调查 | 无审核有效的义齿厂商及同公司合法服务价源；因此无义齿加工单、采购确认、收发/返工/供应商退回 | 需有可验证的真实厂商资格及价目来源；然后由适当采购/仓库/医疗角色走正常流程。PO147–149永久保持受保护 |
| F2 原竞争 | 新测试前置/产品不变量和既有部分证据 | 历史 loser response/backend PID不存在，标记 `EVIDENCE_GAP`；新的独立真实竞争尚未完成 | 不重放旧竞争；在有合法独立来源和运行条件时只运行新标记场景并保存双请求及独立终态 |
| M5 最终影响面回归 | 42项MODEL、限定带数据升级及保护核验已完成 | 业务闭环后的固定候选升级/影响面、适用并发及独立总验收 | 先完成适用产品业务链，再对最终候选做一次完整而不重复的验收 |
| SIGSEGV恢复状态 | 有界恢复评估与少量只读HTTP/GDB观察 | 精确根因未确定；历史错误不作为已修复 | 保持 `ROOT_CAUSE_UNDETERMINED`；下一次受影响运行按已授权GDB/core方式记录，异常即停 |

静态复核确认现有 followup 测试分别覆盖 callback 注册、去重/领取和受控sink行为，但不能合并推断为完整端到端证据。尝试构造供应商到期的测试源也必须建立真实有效资格事实；不能用合成“已批准”数据替代缺失的业务凭证。已有升级与42项模型结果不重复运行。以上缺项意味着S11仍 `PARTIAL / IN_PROGRESS`、#35保持OPEN。
## 2026-10-21 03:30 UTC：GDB 下窄只读 HTTP 检查

当前分支 `codex/s11-followup-lab-r1`，候选 `4f3798dfbd413d2201105bf1b7bda7ffcaf87bb1`，工作区干净、ahead 198、未push。候选 fresh-admission 脚本经独立静态复核，SHA-256 `21fc26d0fc21d748c0bef0ef7d765ce103b01e5b5086eaf0a5d03db9a73a4544`。两次候选专用脚本早期尝试各因一个私有脚本绑定错误在DB连接前断言失败（旧/新候选初始pair绑定；恢复allowlist误把历史`0f03ef9`别名改指向`3558a7b`），未访问DB/未做业务写入；保留stdout/stderr原件。修正及静态复核后fresh admission PASS，receipt `.local/s11/receipts/s11-fresh-admission-4f3798d-20261021T025205Z-597ad045e2e7a887.json` SHA `e4f70bcc8a4126f79cb33cea159c9f3bd5354f565c4ad755448d96bce4b8f620`。核实目标scratch OID2144130、有效scope、224保护表、D/C projection SHA `33f8730aa39cc869e749827e66f10505a0fe9e5aedd5677c9cb1b17718202ae8`、200个跨库目录检查、跨库关系读/写/建schema均无权限、外发关闭、服务停止及18411空闲；runtime/admission原子pair更新manifest为COMPLETED。

独立恢复评估者 `/root/gdb_core_runner_review` 核准的范围仅为一次新的匿名raw HTTP GET `/ydental/queue/screen`，不解除一般HTTP/browser STOP。历史窄GET和当前准确候选admission、scratch身份、进程归属、数据保护与权限均过审。PID42433只读身份为PID1所属Odoo server，配置 `db_name=odoo20_dev` / `dbfilter=^odoo20_dev$` / `db_user=odoo`，监听127.0.0.1:8069；未接管、停止或更改此进程。

在该批准范围内通过 `start --gdb` 运行 `20261021T031235Z-06f93a2c106d`，发出一次`GET /ydental/queue/screen`。客户端原始回执 `.local/s11/operations/http-probe-4f3798d-20261021T031235Z-once.json` SHA `6f199b8a425c89ae850a9af61d5246442c7abfffec2fff5ed6e246f7f38fd68f` 报HTTP 200、body 1505 bytes、无认证/cookie/redirect/JS。第一次客户端owner文件路径预检错误，发生在建连前，未发请求；无重试。launcher exit receipt `.local/s11/runs/20261021T031235Z-06f93a2c106d/exit.json` SHA `cd25c5a03cbd5a52cabe6818ab59208019d59523d000fdf3eea9ec00b20df529` 显示child exit0、无signal/native crash/core、inferior/GDB组停止；run下server log SHA `7107acdfed3ea8ccb917934c250499779bad6d1739906adbf0ce4ed3d6a3ee74` 包含模块加载完成和一条已有test-framework导入ERROR诊断。访问日志行不完整，故server端request count/status为UNKNOWN；客户端回执只证明一次客户端GET的200。launcher stop返回成功，owned service STOPPED、active marker无、18411无监听。

独立post-run readback曾尝试调用既有只读校验器 `.local/s11/verification/post-http-readback-4f3798d-20261021T031235Z-06f93a2c106d-ro.py`（SHA `30ce3a0b641fd746d55bd4743c6dc6ccefddc0dd453af75a1c469e5630887b18`），但admission在30分钟freshness期限外，launcher在DB连接前拒绝；失败回执 `.local/s11/verification/post-http-readback-4f3798d-20261021T031235Z-06f93a2c106d-ro.json` SHA `8277a1e0f835c597d0304665ceeb182263d37f1c56247e10dcad3b95864969d8`。当时runtime/admission SHA分别 `2c9e99dc…15956b5` / `11749b4d…b5304fe`。此次未做DB查询、未修改runtime/admission、未重启/重复HTTP。需基于当前候选重新fresh-admit后，由独立验收比较224保护表、D/C、modules、通知/外发与post-run状态。未完成此读回前不进行新的业务写入。

这只是窄范围HTTP运行证据，不能证明SIGSEGV根因已修、旧失败请求无提交或一般HTTP/browser路径恢复。`ROOT_CAUSE_UNDETERMINED`、历史F2 loser/PID `EVIDENCE_GAP`、#35 OPEN均不变。T05/T12真实commit→postcommit→claim→sink、T08 synthetic vendor采购/义齿临床来源与收发返工、费用来源互斥与追加收费返工、patient683预约时段后按原生FIFO到店/临床、适用并发、F1/F4/T18余项、最终影响面回归和独立总验收仍缺；不push/merge/deploy/S12/S13。
## 2026-10-21 04:09 UTC｜T08预检聚合断言缺陷

在候选5891e17的只读T08预检attempt3中，scratch/OID/cluster、角色、产品来源、READ ONLY rollback/close及service STOPPED核实通过；没有PO读取或业务写入。BLOCKED聚合中发现本地预检器使用了错误的XML ID `ydental_access.ydental_base_group_user`，源码实际ID为`ydental_base.ydental_base_group_user`，导致user2670已有基础组时仍判定合成marker唯一检查失败。这是验证器错误，不是业务权限或数据缺失。直接cooperation create ACL确实不存在，后续须使用已授权warehouse:write绑定会话的原生服务。partner联系人只用字段白名单的一次性初始化方案，不授宽泛管理组；详见`CURRENT_TASK.md`顶部。原回执保留，不重跑写入。
## 2026-10-21 04:17 UTC｜T08 one-shot脚本缺陷及无提交读回

合成工坊partner/vendor/cooperation的GDB helper因`Environment.sudo()`调用错误而中止；没有对象ID，runner为`RECONCILE_REQUIRED`，GDB正常退出、服务停止、无native crash。独立复核的RR READ ONLY读回确认精确partner、义齿资格、Store2合作及对应partner sudo审计均不存在，回执`NO_TARGET_BUSINESS_COMMIT_OBSERVED`。原attempt与intent保持不可重放；修正脚本后必须新建独立路径及当前候选fresh admission。证据SHA和路径见`CURRENT_TASK.md`顶部。
# 2026-10-21 04:24 UTC：合成义齿工坊语义核验

用户确认测试阶段无法提供真实义齿厂家，并授权在既有S11 scratch范围内使用明确标记的独立合成工坊与测试角色，由实施方定义价格/工期；不得改本地、操作系统或数据库时钟。沿用测试假设 USD 125/件、5个日历日。该授权不把合成资质描述为真实厂家资质，不解除真实业务来源、权限、数据库保护或SIGSEGV相关停止条件。

在HEAD `bc963b2097ea88d602a2f5c614be57a4435b6317` 上，一次性T08设置已提交partner 3634、义齿qualification 267、Store2合作257。原始读回 `.local/s11/verification/t08-synthetic-workshop-setup-readback-bc963b2-attempt2-retry1.json` SHA-256 `09757bde229a55c0d61afd3a99c6add1183e0d2135e0023f436cafa9bfb17188` 因 `is_company=false` 及review reason未含synthetic而落为 `FAIL_REQUIRES_RECONCILIATION`。保留原始回执和所有业务字段，不对对象做修补。

独立静态验收者 `/root/plan_remaining_audit` 对源码和回执核对PASS：Odoo `res.partner.is_company`依赖有效VAT与commercial entity；helper未提供VAT，而合成场景不得编造VAT，所以false为原生计算结果。`ydental.lab.vendor.create`只要求外部非患者partner，不要求is_company。`action_approve()`在未提供理由时以 `Qualification reviewed` 调用原生审核动作，审核服务按真实manager执行状态迁移、版本递增、审计和到期通知排队。故FAIL来自过度严格的验证器断言，不是已提交业务对象异常。

纯本地离线语义对账回执 `.local/s11/verification/t08-synthetic-workshop-setup-semantic-reconciliation-bc963b2.json` SHA-256 `661e2005283dace2c33bc1c042def60a44e872b9b4f0c4639a9c176e9c11d320`，结果 `PASS_WITH_EXPECTATION_CORRECTION`，9项检查PASS。它固定原始读回和intent哈希、辅助源码语义、合成partner非患者/公司归属、vendor审核状态及审核人、合作负责角色、审计标记和通知边界；没有连接Odoo/数据库、没有触发请求、没有改写历史收据。原notification job是未来到期的单条internal pending job（attempt 0，无request/activity id）；没有 claim 或交付。外部邮件服务器与live/published payment provider均为0。

因此本次解释无需真实义齿厂商：合成工坊与合成资格已被正常工作流创建/审核，且仍清楚标记为非真实凭证。下一步必须在文档提交后的新候选重新fresh-admit，随后才可继续采购/义齿流程。PO147–149未读取或更改。历史 `ROOT_CAUSE_UNDETERMINED` 与F2 `EVIDENCE_GAP`保留；S11 PARTIAL/IN_PROGRESS、#35 OPEN。不推送、不合并、不部署、不启动S12/S13。

## 2026-10-21 05:43 UTC｜T08采购 attempt6 无提交对账

- 固定HEAD `204a0c209c8f61bd485e069d3075a63f70185224`，当前分支 `codex/s11-followup-lab-r1`，无tracked代码改动。原计划不变。
- PO attempt6 使用新幂等尝试标识，在GDB受管运行中调用正常采购路径一次；因helper错误提供不存在的`purchase.order.line.product_uom`字段，Odoo原生字段应为`uom_id`，在草稿行缓存更新时报`ValueError`。没有SIGSEGV；GDB退出0、owned process group停止、服务STOPPED、授权撤销。结果SHA `7faa032e41986071dafbcee0ba7cb8e2bb29be12be81ccab771dc50b7b724f7b`，GDB日志SHA `10b342c6cebbb48c4e76e68d3419c57a28b3bde724e840ccc205aa4b17d7b90e`。
- 原intent SHA `bf666e15cc494a0a5b0696bce2aaa07958aca8ed1ff3b9ca03b07345af05db1b`保留COMMIT_RESULT_REQUIRES_READBACK。经静态独立审查后的精确origin只读RR对账PASS_NO_SUBMISSION，receipt SHA `acad28f41ccc3b5c30e03f4718a3dd88d454f41513cb5372bc91b6bfc30a008d`：目标PO为空；Store2 native config仍有效；指定DB/OID/cluster正确；显式ROLLBACK/idle/close。只查询目标origin，不读PO lines；没有重试attempt6。第二独立验收`/root/gdb_core_runner_review` PASS_NO_SUBMISSION；复核所有证据哈希并另核旧GDB/runner进程退出、ACTIVE absent、18411无监听。
- 后续将更正为原生`uom_id`，先独立静态审查，再按文档提交后的新HEAD fresh-admit才可尝试一次新幂等attempt。Store2原生库存setup的先前独立读回见本报告前节，0库存和库存事件。
- 当前S11仍PARTIAL/IN_PROGRESS、#35 OPEN；SIGSEGV `ROOT_CAUSE_UNDETERMINED`、历史F2 `EVIDENCE_GAP`。未提交采购服务费或义齿收货等后续状态；S11其他缺口按当前任务状态保留。

## 2026-10-21 06:07 UTC｜返工收费来源三类约束核验与postcommit路径复核

当前branch保持`codex/s11-followup-lab-r1`，核验候选`102e50f2d9857bd7b8aaed01c6259e165e233007`，tracked工作区在本节记录前干净，未push/merge/deploy。对候选做fresh admission后，receipt `.local/s11/receipts/s11-fresh-admission-102e50f-20261021T055926Z-2eb0fb14c9a6c148.json` SHA-256 `ba1cbabf0c1547cab25ecacafeb313c75b91dfbf85d273dad5d1e72b89049506` PASS；独立离线收据审核PASS。目标scratch/OID2144130及真实cluster、受限角色、224 protected counts、D/C projection、200数据库扫描、服务STOPPED/端口空闲及外发关闭均通过。

用户计划要求确认返工费用三类来源的真实数据库互斥约束。已执行一次只读catalog审计，脚本 `.local/s11/verification/fee_source_constraint_audit_102e50f.py` SHA-256 `6aff13f2d79daa63b16c9f59996c8976566a4ab9782071d6f0f2856d9c24d42c`，exit0；实际receipt `.local/s11/verification/fee-source-constraint-audit-102e50f.json` SHA-256 `70f9470507e1d7293375475f5095008505599629b88091ad8806ccdb8d9a578d` PASS，`/root/plan_remaining_audit`独立离线验收PASS。连接前核目标和服务状态；实际PostgreSQL身份与admission匹配。目标库中已验证validated CHECK精确要求`ydental_fee_id`、`ydental_lab_charge_id`、`ydental_lab_charge_adjustment_id`三列恰一非NULL，并且三列各有validated UNIQUE；三列数据库标记仍nullable。RR READ ONLY事务显式ROLLBACK、IDLE、关闭。脚本的一处摘要字段`database.cluster_ref`取自runtime配置而为空；实际查询的`database_identity.cluster_ref`为`7694897083368259627`并与admission一致。此记录不将摘要空值误称实际cluster缺失。无需添加重复约束；不得为消除既有NOT NULL升级警告而改变合法费用来源/历史NULL。

独立postcommit代码审查：现有代码分别测试callback注册/回滚、dispatcher claim、controlled sink，但没有测试真实提交触发的完整`source commit → cursor postcommit → committed claim → controlled sink`。普通Odoo`TransactionCase`主事务在测试框架中回滚，不应对其外层cursor执行commit来伪造此覆盖。最小可信业务路径应使用一个新的合成患者实际治疗事件/复诊来源，正常创建对应job，在独立边界的已提交事务中触发现有postcommit，sink固定为内部`controlled_test_sink`；在sink dispatch期间核claim提交状态，结束后读回job终态、唯一内部activity以及无SMTP/email/SMS/provider/outbox副作用。现有受保护patient364/event417等不复用；不建未授权独立数据库、不留下无业务来源的孤儿job。具体运行等待patient682原生队列正常推进或其他合法合成临床来源。

S11仍`PARTIAL / IN_PROGRESS`、#35 OPEN。T08 P00169的物理收货不得早于实际UTC `2026-10-26 05:51:53`；旧F2 loser/PID为`EVIDENCE_GAP`不重放，SIGSEGV为`ROOT_CAUSE_UNDETERMINED`。剩余仍包括真实临床来源、义齿收发/返工、真实postcommit受控sink、追加费用返工、适用并发、剩余影响面回归与独立最终验收。不得合并、部署或启动S12/S13。

## 2026-10-21 06:46 UTC｜当前状态与原生队列诊断

当前branch `codex/s11-followup-lab-r1`、HEAD `1cf5c6c06aae72629d1766d687de07203721269d`、tracked工作区干净，领先远端208提交；未push。fee-source catalog审计与代码核对已独立通过：三类来源列为nullable，数据库有“恰一来源”validated CHECK及各列独立validated UNIQUE；不应改NOT NULL或增加重复约束。回执和摘要字段缺失限制详见 evidence-index；真实数据库身份匹配准入，事务回滚后关闭。

原生队列只读诊断针对patient682/task1183/entry716：目标任务与队列项匹配，但原生eligibility为 `day_closed`、eligible count为0，所以不得call。attempt3诊断证据已由独立离线检查核实目标、限输出和事务回滚/关闭；审查同时发现脚本文件mode为0664且receipt未绑定verifier SHA，receipt只保留服务连接前STOPPED。结论限定为“只读阻断诊断通过，业务readiness未通过”，不把低层代码/证据限制隐去。旧队列项不能通过改时间或直接重开复用；后续使用真实开放业务日中的新合成预约及实际到店，遵循原生FIFO。

T08现有独立合成工坊已通过原生资质/合作流程创建，且已由正常采购角色确认初始加工服务PO `P00169`（PO164），USD125，五实际日历天交期。PO提交时数据库时间为 `2026-10-21 05:51:53.939916 UTC`，允许最早的物理到货时间是 `2026-10-26 05:51:53.939916 UTC`；不得调系统或数据库时钟。采购单并不生成临床来源或物理义齿，也不能单独支持lab order。供应商、workshop、价格及工期定义为明确的S11合成测试实体，不宣称为真实外部厂商服务承诺。

尚未取得有效合成临床event/文书，因此不能安全创建初始lab order、治疗收费、真实来源postcommit job或返工。patient682旧entry已day_closed；patient683仍只能在实际预约时段和FIFO条件满足后推进。继续推进不依赖物理交期的源代码/离线影响审阅及适用测试，不重复既有42项MODEL或upgrade。最终条件仍缺：有效临床闭环、真实postcommit链、物理收货/入库及适用返工、适用新并发、其余回归和独立总验收。SIGSEGV `ROOT_CAUSE_UNDETERMINED`及F2历史 `EVIDENCE_GAP`保留，#35 OPEN；不push、合并、部署或启动S12/S13。

## 2026-10-21 07:37 UTC｜HTTP运行后的迟到只读累计对账

在文档候选 `322a50091655f48f40cfc6313e5bf8d798154aaa` 上重新fresh admission一次并通过独立收据核对。目标scratch/OID/cluster、受限数据库身份、224表、D/C pin、200库目录权限扫描及受控服务停止均通过。执行前静态review发现private recovery脚本先逐个验证并立即写回备份；将新副本改成先验证两份备份，再写任一pair成员并再次独立审查PASS。系统Python缺psycopg2导致的第一次命令在连接前退出；使用README指定的项目venv完成实际审计。

对03:12 UTC窄HTTP GDB GET的第一次迟到回读未通过，receipt仅为通用AssertionError，未出具业务影响结论。原因是原验证器要求当前计数仍与03:12运行前完全相同；当时之后S11已按授权创建合成工坊、库存配置并确认P00169，所以该前提错误。固定前中后准入receipt离线比较出实际受保护表差异：4f→6c为已独立读回的合成工坊/库存前置11表增量；6c→322为PO确认阶段`mail_message +1`。因此没有即时post-HTTP快照，不能证明在那个时间点没有状态变化或将后来变化归因于GET；本次只核对当前数据库与当前准入快照，并验证两段已记录中间增量。

全新attempt2静态复核PASS后，一次RR/READ ONLY、显式ROLLBACK的迟到对账通过16项：目标数据库身份正确，当前224保护表和D/C/modules/external状态匹配fresh admission，已知历史增量符合固定snapshot receipts，连接idle并关闭、pair不变、owned service停、ACTIVE不存在且port空闲。它同时核验原HTTP客户端receipt为单个GET HTTP200及原GDB exit0/no signal/no core。server access log不完整，服务端请求数仍为UNKNOWN；记录中已有一个test-framework导入ERROR，所以不称日志无错误。独立离线receipt review PASS，重算7项输入hash并确认所有checks为true；回执未嵌入自身verifier SHA，故来源链依赖已静态审查的script SHA及固定输入。此结果不等于即时HTTP后状态证明、一般HTTP/browser恢复或SIGSEGV根因修复，`ROOT_CAUSE_UNDETERMINED`不变。

本节之后候选仍为`322a500`直到本报告提交；S11剩余临床/F1/F4/T05/T08/F2/F3和影响面任务如06:46节所列，保持`PARTIAL / IN_PROGRESS`、#35 OPEN；不push/merge/deploy/S12/S13。

## 2026-10-21 05:55 UTC｜T08 合成采购确认及独立读回

- fixed candidate `6c86964a1adb5c899c6ea4d26aa3bd29a2c49a13`; fresh admission PASS，receipt SHA-256 `1f965d2c2dcc8f4789e688848beab57e881ca6f85689e6324a4abdc0b25310d1`; offline independent receipt review PASS. 224 protected tables, D/C projection, 200-database permission/catalog sweep, modules/external channels and service STOP/port-free facts match.
- Once under bounded GDB after independent static reviews, normal buyer 2666 created and confirmed a new Store2 synthetic denture processing PO, `P00169` / id 164, exact unique origin `S11-SYNTH-DENTURE-INITIAL-01`, company1, vendor partner3634 / qualified vendor267 / Store2 cooperation257, one product564 service line, qty1/UOM1, USD125, incoming type1529 tied to Store2 config182→warehouse192/S2D. The synthetic workshop is not a real supplier commitment.
- GDB result `.local/s11/operations/20261021T055152Z-s11-t08-synthetic-initial-po-6c86964-attempt7-gdb/result.json` SHA `6144a16ee219533a3a959efe64e74bd66f52bd12526f15c2c91461001c54416f`; log SHA `58054d8b52636a33d9fe7d5b1711690d45b23e9fc1d904a70b35b00290c662cf`, exit0, `COMMIT_RETURNED_READBACK_REQUIRED`, no SIGSEGV; owned group/service stopped, port free, auth revoked. Intent SHA `9ee8277f467fb9ab56578f972a5b954ed5b1af596b063a3b8e996fbaa834e135`; actual UTC order time `2026-10-21T05:51:53.939916Z`, planned date `2026-10-26T05:51:53.939916Z` (5 actual calendar days).
- The first independent raw SQL readback `.local/s11/verification/t08-attempt7-purchase-confirmed-independent-ro.json` SHA `23909b1e544ab3fbc068dcb17b0d9b12c3d0b3d038ab85109cdffb42bda25360` is retained as FAIL_REQUIRES_RECONCILIATION: only the intent-vs-DB order timestamp comparison failed because Odoo persisted datetimes at second precision; all other source/order/line/Store2/five-day and transaction checks passed. No business action was repeated. A statically reviewed corrected verifier aligned to Odoo second precision while requiring exact committed `po.date_order + 5d == line.date_planned`; attempt2 receipt `.local/s11/verification/t08-attempt7-purchase-confirmed-independent-ro-attempt2.json` PASS, SHA `248b4f31423d2894a88053f08188fb4a7174296f78a3a0ca4a994309b7db0ff8`. It checked only the unique target origin/order and Store2 mapping, with RR READ ONLY rollback/idle/close. `/root/gdb_core_runner_review` independently accepted actual evidence; `/root/plan_remaining_audit` independently reviewed verifier.
- No physical receipt or stock update is claimed; no denture receipt may be recorded before actual UTC `2026-10-26 05:51:53`. Physical workflow, supplier return/rework and financial source remain incomplete. PO147–149 and prior finance/stock/audit remain protected. Patient682 remains behind pre-existing FIFO entry; patient683 appointment begins at 15:00 UTC and must not be serviced early.
- S11 is still PARTIAL/IN_PROGRESS and #35 OPEN; SIGSEGV remains `ROOT_CAUSE_UNDETERMINED`, historical F2 loser/PID remains `EVIDENCE_GAP`. This result is not root cause remediation, delivery, or final acceptance.

## 2026-10-21 08:00 UTC｜patient683 预约时段只读预检

在固定候选 `364b53ca190a5c7e39489043fd44921f495b1d4a` 上，对 patient683/task1184/slot1697执行单次RR/READ ONLY快照。验证器 `.local/s11/verification/patient683-price-and-appointment-364b53c-readonly.py` SHA-256 `0e880ae402cc5c0faacdbb1925101075956c98f7676ca4a2446bf257cf260438` 经独立静态审查PASS；S11 venv执行exit0。回执 `.local/s11/verification/patient683-price-and-appointment-364b53c-readonly.json` SHA-256 `2d61c7c6b740a422430d392eb898566d4b8a841ae030a073f01793f547d0ae9c`，mode0600；独立离线审查PASS并重新核验脚本/runtime/admission绑定及11项断言。采集时间08:00:19 UTC，预约真实时段15:00–15:30 UTC尚未来到。

读取确认任务资格、预约claim指向slot1697；Store2和业务日开放，mapping为care catalog2/product3，预约时点有唯一原生价455/USD7，Store2 medical/frontdesk写权限均有效。read-only事务rollback/idle/close。脚本前后检查service STOPPED及端口拒连；receipt本身未嵌入这两项，受限运行日志 `.local/s11/verification/patient683-price-and-appointment-364b53c-readonly.log` SHA-256 `0888dec1f597d26d33a1a6c5e32f532613c49739f8c327d7c077681fda8772de`有STOPPED输出。队列只暴露aggregate（2 waiting、0 in service），所以此证据**不证明FIFO/叫号优先级，不允许提前到店或接诊**；到实际时段后须先按原生队列顺序核查。

T08已存在经正常审核的synthetic workshop/vendor partner3634及Store2 cooperation257，采购角色2666正常确认PO164/P00169（USD125，五实际日历日）。S11合成验收不要求真实厂商对接；这是独立合成业务参与方，并非现实厂家身份或外部接口。原始PO intent `.local/s11/operations/s11-t08-synthetic-initial-po-6c86964-attempt7.json` SHA-256 `9ee8277f467fb9ab56578f972a5b954ed5b1af596b063a3b8e996fbaa834e135`记载精确计划交期 `2026-10-26 05:51:53.939916 UTC`；DB读回为秒精度且验证五日交期，因此不得在该精确intent时间前记录实物到货。义齿有效临床来源、收货/入库、退回/返工、追加收费和后续验收仍未完成。S11仍PARTIAL/IN_PROGRESS，#35 OPEN，SIGSEGV根因未知，历史F2缺口保留。
## 2026-10-21 11:50 UTC｜session clock operator授权前置失败记录

用户要求的快速触发日期功能已实现为受控S11浏览器session业务时钟；目前该用户界面/动作仍未端到端测试，因为UID539还没有 `ydental_s11_clock_test.group_operator`。尝试为其授予专用测试组时，发现Odoo 20的 `Registry.cursor(readonly=True)`只是尝试副本，可能回退为主库读写cursor；attempt8在写用户组之前按 `cr.readonly` 门禁失败（NO_COMMIT），正确连接模式应显式 `sql_db.db_connect(DB, readonly=True)`并核验数据库只读状态。

新的诊断attempt1 helper与runner共用了marker路径，触发防重放拒绝；GDB目录 `20261021T114421Z-rodb-diagnostic-8aa3ea8-attempt1-11f414f83c79`，日志SHA-256 `0bcddc4877f5bd41229cff3d8c3d2ece0930e07d78dbbb7c74e2ac27243e369b`，runner/exit SHA-256 `6617fcfbf53459b2639fcc6d2a17d666648e05560f7fe239b2a2a5602c21b136`。attempt2将marker分离后，helper在DB连接前因证据字段名校验不匹配退出；GDB目录 `20261021T114842Z-rodb-diagnostic-8aa3ea8-attempt2-63d5ff8adbd1`，日志SHA-256 `ebff1f57f7335e86cf6fa8ec5c8a8b4df590701694d3db75d314d0121d2edf5e`，runner/exit SHA-256 `8521572864a95b69dcd16a3975d5081f66d6523c1386b8e49a22035d264c39b0`。独立复核确认二者都没有诊断SQL、业务SQL写入或commit；Odoo shell启动阶段加载了Registry/context，故不能写成“无数据库访问”。两次GDB进程组及S11服务均停止，无SIGSEGV、core或native-crash收据；全部日志及receipt保留在忽略的私有 `.local/s11/operations/`。

两次操作工具均已消费且不得重放，固定候选代码不变。当前用于准入的11:18 UTC fresh pair已过30分钟时效，下一次数据库动作之前必须生成并独立验收新的只读准入。专用operator组尚未授予；未做时钟快进，未进行任何临床/经济流程；#35仍OPEN、S11仍PARTIAL。完整实时状态见根目录 `CURRENT_TASK.md`。
## 2026-10-21 14:59 UTC｜debug clock UI readback mismatch and template correction

Attempt20’s one-shot authenticated browser sequence performed exactly one normal clear and one normal set through `/ydental/s11/debug-clock/action`, then a GET. Both POSTs returned HTTP 200; set returned the requested synthetic UTC. The final page returned HTTP 200 but displayed neither `Run` nor `Session business UTC`. No clinical/economic action or unexpected HTTP request occurred. The operation receipt is `.local/s11/verification/attempt20-clock-clear-set.json` (SHA-256 `970f814acd2a72bbd6c5ea501482d85a62a509c0d19d34363b58936b69e2e960`); its exclusive intent latch is preserved and the sequence must not be replayed.

The independent read-only reconciliation `.local/s11/verification/attempt20-clock-readback-ro.json` (SHA-256 `e48ee593d1cdeae250e89c0a528f91d8111590bb2f4f5f0c56467f013bfbb754`) confirms the original UID539/Store1/browser-session binding has one active row for run `20261021T144049Z-d1cac1ccdc8a`, simulated time `2026-10-27 05:51:53 UTC`, and one clear plus one start event in the same physical window. All 224 protected table counts match attempt18; the database transaction was READ ONLY / repeatable-read, rolled back and closed. Thus the defect is in dynamic page rendering rather than failed persistence. No business data was changed by this readback.

Independent source review found that pinned Odoo 20 QWeb implements `t-out` but has no `t-esc` directive handler; the Odoo upgrade migration explicitly converts `t-esc` to `t-out`. The controller passes both values correctly. The page’s two dynamic output directives are changed to `t-out` in `ydental_s11_clock_test/views/clock_templates.xml`, committed as `57633cf61eacac194a4865661dde281f75abf481`. During fresh-admission preparation, a second issue was found: the controller’s page GET selected an unexpired session row without requiring its run ID to match the active GDB clock run. Also, action handling applied monotonicity across runs and labeled a new run’s first set as `advance`. The controller now considers a clock active only when session, actor, store and run match and physical expiry is in the future; a clear still records the prior stored value, while a new run’s first set is a `start`. Independent review passed. Python compilation, XML parsing and `git diff --check` passed. Runtime testing is pending. Require a fresh exact-candidate admission before upgrading the addon and performing a minimal browser verification of display plus set/readback; do not repeat attempt20 clear/set.

Service remains STOPPED. The synthetic clock row/events are retained. S11 remains PARTIAL/IN_PROGRESS, #35 OPEN; `ROOT_CAUSE_UNDETERMINED` and historical F2 `EVIDENCE_GAP` remain. No merge, deployment or S12/S13 start.
## 2026-10-21 15:07 UTC｜new-run clock lifecycle corrections committed; fresh admission pending

The final committed debug-clock candidate is `b1947ec6dd0482979f56e25e67f0f317772b55bc` on `codex/s11-followup-lab-r1`. It includes the two QWeb `t-out` corrections plus controller behavior that binds visible/active time to the current actor, store, GDB run and physical expiry. A prior-run row no longer appears active, and a new run’s first `set` is treated as `start` without inheriting the prior run’s monotonic floor. `clear` still records the value removed. Independent source reviews passed; Python compile, XML parse and `git diff --check` passed.

No database/runtime action has been run against this candidate. The bounded fresh-admission helper is being prepared to pin the exact commit transition and separately reconcile attempt20’s one session row and two clock events while keeping all 224 protected counts unchanged. After its independent review and successful admission, update only the S11 clock addon and run a minimal GDB-captured localhost page/time verification. Attempt20 clear/set is never replayed. Keep #35 OPEN and S11 PARTIAL until all plan criteria pass; no merge/deploy/S12/S13.
## 2026-10-21 15:12 UTC｜attempt21 admission helper pre-connect assertion failure

Attempt21’s once-reviewed helper `.local/s11/verification/fresh_admission_32ecd9a_attempt21_readonly.py` (SHA-256 `77b22469b54987fb66835cef69b2f4d4e8af65594b4015f2bfb432a9059b630c`) exited 1 before any database connection. It compared the current corrected addon source tree with the historical source aggregate from the old candidate. The traceback ended in `verify_clock_postrun_evidence()` before the later `connect(db)` statement; no SQL, service start, or business write occurred. Preserve its O_EXCL runlock and do not rerun attempt21. Captured stdout/stderr SHA-256: `0908e207f68d83ed06cbf69e8886400e924490d1aa8e385959ee7196f2c59ed0` / `676ef0474a0cc9623f4238333b6f785462653cc8e8bd606e00d155edbeb68f43`.

The pinned historical candidate `8aa3ea880ea0844682000e87f7938714132fb16d` has a 10-file `.py`/`.xml` addon source aggregate of `007a3b5d011e5b501a6feca9bb98ab7afa0dccd6b7386ca83eaed8ed6451ec74`, independently recomputed from its Git tree. The current source aggregate is separately pinned as `b5514f24af338c93bf92656b914777c560bea874faee2979dd54ffac4cb21109`. A new attempt22 helper will verify the historical hash from Git objects and retain current-tree verification separately; it must pin attempt21’s pre-connect failure evidence and receive independent review before any DB action. Service remains STOPPED.
