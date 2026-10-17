# [CODEX-PLAN / NO-NEW-RUNTIME-AUTH] S10-LOG-AND-CLOSEOUT-v2｜PLAN_READY

- task_id: S10-LOG-AND-CLOSEOUT-v2
- message_id: YD-S10-LC2-PLAN-20261017-01
- revision: 1.0
- authority_source: 用户本轮直接指令；GPT规划接管6232520895；WORKFLOW-V2治理6232280969/6232284873。
- parent_commit: e7cd02689b92c0cc4f7343842268b21e56de9f80
- execution_status: PLAN_ONLY / NO_NEW_RUNTIME_AUTH；交付状态 PLAN_READY。
- supersedes: []（不替代既有6232155980技术裁定、不恢复旧窗口）。

本评论包含可独立审读的统一方案、全部12+22验收映射及19TC最小证据、四角色事实和独立评审。规划文档仅本地新增，未commit/push；本评论全文才是本轮远程交付，不伪造新文件的GitHub blob URL。所有新增应用运行NOT_RUN，S10/T12 BLOCKED，Native与当前编辑权UNKNOWN。

## 实际四角色与交接

|角色|真实agent/thread ID|开始UTC|规划交接/终审UTC|唯一写入/输出|
|---|---|---|---|---|
|controller|/root / thread UUID 01a1494f-2b74-7111-854f-ea64560ff09e|2026-10-17T10:01:33.798Z|2026-10-17T10:14:38.801919+00:00|plan-and-acceptance.md; acceptance-matrix.json; summary.md; run-manifest.json; agent-roster.json; github-comment.md; public-evidence-index.json; sync-state.json|
|developer|/root/developer（接口未公开UUID）|2026-10-17T10:02:02.906Z|2026-10-17T10:09:08Z|developer-handoff.md|
|tester|/root/tester（接口未公开UUID）|2026-10-17T10:02:09.967Z|2026-10-17T10:13:19.807745+00:00|tester-handoff.md|
|acceptance|/root/acceptance（接口未公开UUID）|2026-10-17T10:02:15.856Z|2026-10-17T10:13:20Z|acceptance-review.md|

派生工具实际返回 /root/developer、/root/tester、/root/acceptance，list_agents确认三个真实独立任务；子UUID未暴露则不编造。开始时间来自本会话JSONL的session_meta/spawn_agent调用元数据；验收最终签署真实时钟见报告。父会话实际UUID取自环境。子线程继承父权限，角色约束不等于独立只读OS沙箱。[官方Subagents权限说明](https://learn.chatgpt.com/docs/agent-configuration/subagents)。developer/tester实际完成交接，主控据acceptance五条缺口修订后由其逐项重核；主控不替自己签独立验收。

# S10-LOG-AND-CLOSEOUT-v2 统一实施包（待一次批准）

- task_id: S10-LOG-AND-CLOSEOUT-v2
- message_id: YD-S10-LC2-PLAN-20261017-01
- revision: 1.0
- 当前 execution_status: PLAN_ONLY / NO_NEW_RUNTIME_AUTH；材料完成后 PLAN_READY。
- 父HEAD: e7cd02689b92c0cc4f7343842268b21e56de9f80；固定core: f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb。
- 来源：用户本轮直接指令；#34 6232520895；#23 6232280969；#34 6232284873。本文件的未来资源建议不是本轮运行许可。

## 1. 实际状态和可信边界

本地/远端分支均 codex/s10-settlement-finance-r1-20261013，origin=https://github.com/Yredxin/YDental.git，HEAD一致，开始时工作树干净。core实际Git根为上级code，文件为 ../odoo/netsvc.py，core SHA匹配且tracked diff为空；其既有untracked AGENTS.md/sd-addons不清理。codex-cli 0.163.0，gh 2.102.0。未读出本地含凭据配置，不将 config/odoo.conf.example 当成生效配置；本地实际logging/PG参数均未核。

主控实时API全分页取回#23四评论、#34 280评论、#35零评论；读取当前正文与有效治理/技术链6110178328、6125774169、6232280969、6229289071、6230102263、6231120531、6232080385、6232155980、6232284873、6232520895。280条是分页取回数量，未声称重新审判全部历史批次。消息ID只有GPT接管记录，无Codex执行回执。#34/#35均OPEN，Project未查询/未修改，不能宣称其当前字段已核。

进程名清单仅见既有codex服务链34893→3886514→3975817，cwd均上级code；未见odoo/firefox/gdb。该观察不证明远端或全部会话无人执行。当前无发现并发写入/HEAD漂移；实施前必须重做所有权锁与HEAD核验，发现其他写者不争抢。四角色真实接口见agent-roster.json，canonical task ID是接口实际提供的标识，不虚构子线程UUID；权限继承父会话，无独立只读沙箱。

6232155980已完成技术裁定，本轮只承接：S10/T12 BLOCKED，S11未启动。最后有效独立检查点r2-A-correct-committed：同源patient1/execution1/doc1 confirmed/v4、writer7；version9=confirm/v3/author7/previous2，version10=correct/v4/author7/previous9。曾经editor7/session109，不等于现在。release已派发但无已验证提交，当前编辑权及release结局UNKNOWN。r2-final-tail-RO保存不一致，不能作基线；同次副本不是独立测量。

Native PID965603/backend1483029/exit-11，Python栈在persist/save/read/JSON解析路径。该路径是故障时观测，不是Native C根因。根因UNKNOWN；新取证方式只可称MITIGATION。保留P020/P021财务、原件及同源v3/v4正式采纳，不拼接不同患者为一条链，不重做confirm/correct，不重放W5旧500+240、退款14/13、日结9、旧治疗发药资金。

受保护来源：ydental_s10_test_20261017050000_21b0cafe/OID2122140；事故副本ydental_s10_test_20261017080710_2494c102/OID2144127；cluster7694897083368259627。本轮连接0，全部旧预算封存。odoo-12、core、历史文件/库/卷/附件不变。04文件36066 UTF-8 bytes，SHA256=0c869bbaf8a06210a46aaf04702207fa1ff54d619209928b67c0b1031edae439，已完整读395行（包括03全文）。

## 2. 推荐的最小实现与文件所有者

推荐“一包批准，先离线日志和框架测试，再新准入，最后A→B/C→D→E”。开发改产品，测试独占runner/fixture/测试，主控串行调度DB与收敛，acceptance独立判据。此处是未来所有权分配，本轮仅写新规划文件。

| 文件/函数（现有或拟新增） | 实施决定与兼容边界 | 未来所有者 |
|---|---|---|
| ../odoo/netsvc.py::LogRecord/init_logger | 只读固定实现；保留factory、dbname/test字段和原生人类日志。复用log_config JSON/TOML、keep_odoo_default=True；不basicConfig、不改root/factory、不启log_db | 无人修改 |
| ydental_access/diagnostics.py（新增）::bind_context/current_context/emit_event/classify_error | 纯Python primitive接口与ContextVar token；configure_once/JsonlFormatter/PidFileHandler只在access addon已由原生加载时单次初始化ydental.events专属handler，不在每请求安装；server生成trace/request/event ID；上下文finally reset，不接受客户端ID作鉴权。每个适用场景显式run/task/case/attempt；缺字段null且context_missing。模型调用不依赖http.request，不从recordset读取字段、不查业务/flush/改uid/锁/事务 | developer |
| ydental_access/diagnostic_errors.py（新增）::DiagnosticAccessError/DiagnosticUserError/DiagnosticValidationError | 原Odoo异常的子类携带稳定diagnostic_code；保留原英文/翻译消息与HTTP行为。关键DAY_CLOSED/VERSION_CONFLICT/AUTHZ_DENIED/INPUT_PARSE_ERROR有稳定码，未细分UserError用BUSINESS_RULE_REJECTED，绝不解析中文message | developer |
| ydental_access/models/ydental_access_service.py::_denial/_audit | _denial补安全事件。_audit原create成功后用新audit.id发audit.created（transaction-local），将audit_ref与trace连接；create失败原样传播，不吞强制审计。不新增S01字段/schema，不独立COMMIT；独立RO能按audit_ref核持久性，回滚仅日志有attempt，不伪造审计已落库 | developer |
| ydental_settlement/controllers/settlement.py::action/workbench/pdf/other_stores；bill_original.py::bill_original/create_bill_original | HTTP适配器进入/返回/异常/finally。单独输入解析catch-site与服务调用catch-site；缺key/格式错为输入，服务内TypeError/KeyError为APPLICATION_ERROR。现有JSON403/409、HTML303 notice和安全输出契约保持；notice不是trace；异常栈只进受控内部文件，公开不打印str(error) | developer |
| ydental_settlement/models/ydental_settlement_service.py::_operate及日结/版本拒绝点 | 只补primitive关联和必要typed code；不变金额、锁顺序、savepoint、审计、防重。新增拒绝码用原异常子类；具体关键raise及翻译影响见developer交接 | developer |
| ydental_clinical/models/ydental_clinical_service.py::_valid_editor/_acquire/_held/_release | 业务源码保持，测试按实际分支。不得加logger清锁、忽略writer或改default_env。若仅需临床请求关联，HTTP适配器传已知primitive，不做全仓改造 | developer仅必要边界适配；锁规则不改 |
| config/odoo.conf.example + config/logging-s10.example.json（新示例） | 文档化log_config、原生logfile、ydental.events专用JSON消息logger、INFO、propagate=False；log_config配置类仅stdlib，不用class-path在框架logger启动时导入addon；access已正常加载后configure_once安装专属formatter/按launch或PID独占handler。实际仅新run私有配置由launcher生成，workers=0，每launch独占文件，不改共享odoo.conf | developer |
| scripts/s10_lc2_logging.py（新增）::validate_jsonl/query_timeline/summarize_failure | 严格UTF-8/JSONL逐行校验：重复键、NaN、字段类型、截断/空洞、重复event检测；按run/case/trace/operation检索四层索引，坏行标INVALID，不修旧文件；summary先首异常再secondary、进程与最后验证提交 | tester |
| scripts/s10_lc2_supervisor.py（新增）::launch/record_exit/save_primary | 不import Odoo；父进程独立追加短文本退出记录(pid/start/end/returncode/signal/timeout/attempt/last_checkpoint)。faulthandler专用FD子进程全程打开；primary最简write路径，secondary写独立fallback，禁止重用失败serializer递归 | tester |
| scripts/s10_lc2_evidence.py（新增）::collect_selection/seal/verify_checkpoint | 业务进程只发简短事件/返回对象引用。RO/RR新连接独立查证并ROLLBACK/CLOSE，原始数据先流式落盘；大差异/JSON重读/hash/PDF在连接关闭后外部进程完成。独立观察是新测量；复制/重序列化只是同次数据处理 | tester |
| scripts/s10_lc2_cases.py / scripts/s10_lc2_browser.py；ydental_settlement_test/tests/test_log_closeout.py（新增） | framework TransactionCase.uid/HttpCase身份；MODEL回滚隔离，提交链用真实HTTP与正常框架事务。禁止复用R3 default_env补丁/导入旧运行脚本。每次固定product/test SHA，普通修复形成新attempt且保留失败 | tester |

实际文件名和精确调用点由developer-handoff.md补足；不得以新增工具为由加载旧脚本。S01仅Python观测桥接，无schema变更，因此E仍-u ydental_settlement；若实现发现必须升级其他产品模块，先判为包外依赖缺口，不静默扩成-u all。

## 3. 日志协议、四层与失效隔离

schema_version=1.0。每条白名单字段：event_id/run_id/task_id/case_id/attempt；trace_id/request_id/operation_ref/idempotency_ref；component/operation/stage/event/outcome/severity；actor_id/effective_uid/su_flag/company_id/store_id/scope_revision；product_commit/test_commit/core_commit/runtime_version；ts_utc/monotonic_ns/pid/thread_id/process_seq/duration_ms；error_code/error_class/exception_type/root_event_id/stack_ref；transaction_phase/commit_observation/checkpoint_ref/evidence_refs；经授权object_ref/version_before/version_after/diff_ref。适用必填，不适用null；版本/配置全量在manifest，事件引用版本。

真实actor与effective_uid/su分别记录，只有入口本已取得的primitive；unknown不为补日志查询env.user/store.company。外部ID若格式合法也只作untrusted_client_ref，服务端重新绑定，不参与权限。operation_ref跨同一业务重试稳定，request/attempt每次不同，idempotency_ref为受控不可逆非授权引用，secret/key不公开。HTTP/CLI/测试各自适配；ContextVar token进入/退出恢复，线程及gevent并行必须分别测后才声称兼容。

1. 应用事件：ydental.events JSON消息使用标准logging；原生odoo.log不变。
2. S01审计：原事务创建不可改删，audit_ref桥接，未提交不能叫永久审计。
3. 测试：intent在派发前封存；case/attempt/真实身份/固定版本/请求引用/断言/返回或断开/独立查证分别列。
4. 进程：父进程短文本出口不依赖JSON链，原stdout/stderr和faulthandler各文件。SIGSEGV不能try/except兜底；模拟信号只叫SYNTHETIC_FIXTURE。

阶段独立：request.received→validation/authorization→business.start→business.returned→response.observed或disconnected→independent_verification。框架返回accepted/HTTP200不是COMMIT证据；本方案不在业务方法手动commit或用after-return日志冒充post-commit。commit_observation初始NOT_OBSERVED，独立连接见到预期唯一账款/版本/审计才VERIFIED_COMMITTED；事务内回滚测试写ROLLED_BACK_OBSERVED，无法证实写UNKNOWN。查证连接也是新run事件，有自己的backend/time而非复制旧marker。

分诊：BUSINESS_REJECTION / APPLICATION_ERROR / TEST_HARNESS_ERROR / EVIDENCE_ERROR / OUTCOME_UNKNOWN / NATIVE_CRASH / REQUIREMENT_OR_RESOURCE_BLOCKER / SYNC_ERROR。INFO常态事实及预期拒绝，WARNING可恢复异常，ERROR未预期，CRITICAL未知资金/完整性/致命进程。严重度不替代TC断言。

primary先写exception type、固定safe code、stack文件/行/函数（不采locals，不原样str(error)），secondary以root_event_id指向第一异常；后续取证失败不替换首异常。可选诊断handler坏了只stderr固定标记并暂停后续相关写入，绝不触发重收/重退；强制业务审计失败依原契约阻断，不能套诊断降级绕过。

JSONL单行上限16KiB，默认INFO；每launch独立文件，10MiB段/每进程最多5段（新run内），总新原始证据上限1GiB（PDF/外部快照另列索引但计入总额）；80%告警、90%暂停新写，达到上限停。轮转只封存、绝不删除旧历史证据；封存索引标段序号/bytes/SHA、缺失/截断可发现。指定logger DEBUG最多15分钟或case结束即关，不开SQL/debug_http/请求体。评估日志开关前后每请求时延/事件数/文件大小，不虚报长期运行。公开只白名单摘要；合成password/cookie/token/病例/换行注入测试+扫描+acceptance人工复核，异常字符串同样受控。

## 4. 新实施包运行准入与资源申请（现在不执行）

推荐只批准以下应用内范围，不引用旧事故余量，不改OS/PG服务/Docker/网络/硬件/依赖，不升级Codex。解释器使用上级既有.venv/bin/python（版本和二进制SHA在实施准入只读核定），固定core+父分支。所有新名称/端口在实施manifest生成并核无冲突；不假造当前空闲或已获连接许可。

| 资源 | 请求的完整上限/用途 | 所有权/准入 |
|---|---|---|
| 受保护两库的新RO权限 | P021来源0条新连接（不作复制源，也不重复旧终审）；仅事故副本至多2条新RO（新状态/复制后保全），READ ONLY REPEATABLE READ，每条≤60秒、lock_timeout≤3秒、statement_timeout≤30秒；不发DML/COMMIT/锁表 | 主控调度tester唯一执行；核host/port/dbname/OID/cluster/user/backend/只读隔离；与旧3/3无关，必须本整包明确批准 |
| 新测试目标 | 最多2个唯一库：主目标从事故副本只复制一次，继承v3/v4；独立scratch从空template0创建供框架夹具/rollback/故障注入，不复用旧库。两次CREATE上限，维护连接最多1条、≤180秒；建库边界使用autocommit/IDLE、identifier安全引用，每次CREATE失败即停该准入，不重试/重建；新filestore独立目录，原文件只读拷贝 | 新库名严格ydental_s10_test_YYYYmmddHHMMSS_hex8；私有run_dir/database.json和odoo.conf满足现有pre_init_hook的OID/cluster/core/config SHA guard；升级不触发安装hook，launcher需每次自行再核marker；若原库有活连接不杀连接/不改allowconn/template标志；CREATE失败停止该准入，不偷偷换源/重建 |
| 应用实例 | 仅目标库，workers=0/max_cron_threads=0；两个新本地端口预留范围18410—18419，串行一台服务。最多12个Odoo启动总额（scratch install/test、S10-only upgrade、主目标pre/post服务及普通修复）；安装/升级≤1200秒、短测试≤600秒、服务窗口≤1800秒 | tester独占DB执行，主控校验SHA/config/hash/PID；不得碰既有服务；每台db_maxconn≤4，总活跃应用连接≤4，独立RO额外≤1，不改服务器上限 |
| 目标RO/网络样例 | 目标独立RO最多48条、每条≤60秒（准入/提交核实/权限负向/升级前后/最终）；两条真实HTTP并行仅LOG-02串号测试，业务写仍串行 | 应用HTTP用现有本机链路，不新外部服务；鉴权信息私有，不能把RO预算当业务重试许可 |
| 浏览器/文档 | 单个Firefox，最多pre/post两完整会话加1个定向修复会话，各≤1200秒；所有HTTP请求含登录/重定向/静态资源累计≤600、旧原件GET≤12；仅目标库工作台/权限/原件样例。PDF全部已下载页目视；不接打印机/税票/真实支付 | tester执行，acceptance独立读图/页与证据；不读取旧浏览器会话token冒当前授权 |
| 空间/时间/配置 | 新run .local/s10-lc2/<run_id>/<database>/0700（YDENTAL_S10_RUN_DIR basename必须等于库名）、文件0600，专属配置/日志；总工作窗最多8小时运行时间，耗尽保留成果结束，不继承其他包；不装新包、不改共享配置 | root owns manifest/locks；developer owns product；tester owns fixture/evidence；acceptance owns review。磁盘与内存余量先只读查够现有资源，欠缺就资源阻塞，不申请系统调优作为暗含范围 |

CREATE是新应用测试库复制/初始化，不是PG运维专项；只有明确整包批准后可用原已有建库身份。若既有账号不具所需权限，报告缺口，不扩大sudo/PG角色。受保护库永远不作本包业务写目标；事故库自身editor也不直接release。A在新主目标处理继承状态，原事故库完整保留UNKNOWN的原终点。

准入顺序：

1. 重读GitHub/HEAD/dirty和其他执行者；独占新run marker，现有凭据不打印；记录core/interpreter/配置摘要、allowlist、新端点。离线日志与supervisor工具测试先完成；不能未有可用首异常/退出链就派发资金。
2. 经新RO核事故当前doc/version9→10/作者、scope/连接有效性、经济表及原件关系。只有v4真实保留、经济等于正式有效检查点、无未知新增经济结果、源身份正确且采集严格读回一致，才形成准入候选。若不符，不从P021的pending/v2重建v3/v4，不修坏JSON/字段，冻结A主目标；安全scratch开发仍可继续。
3. 正常复制目标后，再由独立新连接核目标与受保护基线关键存储一致。复制过程非新测量；验收必须来自新目标RO。原filestore仅一次复制和离线hash索引，不能认定历史198必为当前数量。所有原件记录/附件/实际bytes/SHA与有效checkpoint核对。父过程封存新baseline，来源/时间/字段/选择集可审。
4. scratch框架测试用TransactionCase.uid/HttpCase正常身份，MODEL可回滚；真实提交路径使用目标HTTP/auth session/CSRF/已有门店绑定，业务方法不自制default_env，不手写write_uid。任何系统API安全拒绝不换工具规避。
5. 主目标每次写前intent封存；收到响应也先核必要的独立关系和S01 audit再标验证提交；丢响应只查不重做。事务独立后才分析/封存大文件。可选证据坏了业务结局单列UNKNOWN，暂停相关重放。

精简证据选择集不是删不变量：准入/E节点一次全schema/模块版本/依赖与业务关系清单；所有历史及本包新增经济账款/库存存储行、权限/公司/会话、临床文书版本、原件/附件索引及实际文件完整签名在节点比较。每个小动作只读：受影响patient/execution/doc+全部versions、其event/price/fee/source/invoice/payment/allocation/refund/close+native account_move/line/payment/partial+stock move/line/quant/lot、权限scope/membership/company、该动作审计与原件/附件。金额/关联/数量用存储字段精确值，排除name_get/展示串；原存储字段不随便排除。

A要求旧经济全部不变：用准入后目标的独立经济基线和A后完整经济域检查，不每个heartbeat抓316表；四mutex修订按真实调用白名单+审计事实，不把所有变动一概允许。B/C拒绝对目标对象及整个旧经济域无改动，鉴权阅读审计允许受控追加。E对经济/历史版本/权限/附件/原件全域前后保存逐行差异；技术视图/模块元数据有明确升级白名单，不把全库所有差异通配排除。全量内容仅在准入/E若关系清单无法证明完整时在独立采集节点追加，超预算即报缺口，不把大文件带回业务进程。

## 5. A—E具体退出设计（全部新运行NOT_RUN）

A：A-STATE取得上述可信基线。按clinical._valid_editor/_acquire/_held/_release：若确无editor无需假装release；有效且当前真实connection/session/token均合法持有才正常release；新会话不能拿旧token，若旧锁仍有效等待其自然失效，不改时钟/过期字段、不主动撤权造失效。失效后责任人7在来源店真实HTTP acquire，再release，服务自产editor_invalidated/edit_acquire/edit_release审计。若execution仍serving/reserved需先满足原lease持有前提，不能走responsible分支硬绕。自然失效等待最长120秒；若按现有到期仍超过120秒或状态未合法失效，记录具体到期/条件并停A，不延长窗口或改时钟。有效他人持锁或无法证明资格则冻结A。doc始终v4，版本9/10不得重写或新增confirm/correct。A-ORIGINAL从真实settled工作台点击旧v1已保存链接下载，核SHA256 05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4、对象链/权限/旧附件字节不变，渲染调用计数0，逐页目视；费库款全域不变。截图不含患者全文/secret。

B：普通有来源读取资格但无底层write权的真实账号，先确认旧source/payment/audit目标来自已提交marker（金额350，不假设500）。ydental.settlement.source的ydental_original_amount、ydental.settlement.payment的ydental_amount、ydental.access.audit的ydental_reason分别非空write及各unlink，共6项MODEL，及同6项真实/web/dataset/call_kw RPC，分别12份结果。实际调用/web/dataset/call_kw/<model>.<method>（或无suffix的同路由），JSONRPC params中的model/method/args才是实际调用。每个RPC记录身份/route/model/method/arguments白名单/HTTP+RPC错误体/独立查证；HTTP200里的error不算成功。拒绝后原对象存储+审计旧行/关系不变，不把缺记录造成异常当权限PASS。不伪造sudo测试普通权限；若源码公共RPC guard先拒也记录实际层。

C：角色=有源read+export、有read无export、有export无read、无两权、已撤权旧登录/旧页面、另一店同公司、另一公司、患者family与混源（同family允许医疗历史不自动财务全文）。对象=主链invoice/original/attachment及异店/公司/患者对应独立合成对象；不混拼主链。入口=GET /ydental/settlement?patient_id=…、/ydental/settlement/bill-original/<id>、/ydental/settlement/pdf/{bill,receipt,refund}/<id>、/ydental/settlement/other-stores/<patient_id>；普通model read/search_read/web_read/export_data（适用公开guard）；/web/content/<attachment_id>?download=true、/web/image/<attachment_id>及download变体与fixed core适用model/id/field路由；真实call_kw包括bill.original.read、ir.attachment.read(raw)/export_data和私有方法guard拒绝（不算服务执行）。source read+export允许只通过受控原件endpoint取回；即使有源权限，普通native binary/RPC直接获取受保护附件也应拒绝。每个cell列适用原因/预期/实际证据，不存在入口用STATIC说明而不叫PASS。原件read与导出分别校验；旧页面撤权后下一请求拒绝，恢复仅新夹具授权按原值并独立核对。token分无/随机无效/合法受控有效签名路径；没有合法签发路径不可伪造通过或为测试加旁路，列NOT_APPLICABLE及源码理由。图片200必须保存body/MIME/bytes/SHA，与固定core占位图字节或解码像素/尺寸语义核对、排除PDF/原件内容；合法图片比较源内容，非法返回真正原件即安全硬停。旧缺body200保持证据缺失。

D：推荐保留“6单位收款/2单位退款”为新合成参数，取消继承其旧执行资格/额度。只在新目标新patient/source/invoice/request_key、当日真实本店操作者、非自批者和有效线下测试证明下执行，不碰旧支付。先核用户active/公司/店/权限/scope/坐诊、store timezone、actual_utc/recorded time及收款员所有相关支付渠道/日期的日结锁；锁住则另用本包新合成配置，不解锁旧锁。允许新夹具发生必要上游治疗/执行/出账产生独立6费用，此动作属于新来源而非重放历史。

D-FAILED/D-LOST采用唯一新6/2来源、确定动作数：新patient→原生上游费6→新invoice→HTTP收6一次并独立核回→新refund申请2→异人审批→refund_uncertain(outcome=failed)登记“合成线下核实未付”→finance经refund_recover(verified_not_paid)回到approved→仅一次refund_execute 2。测试客户端在该refund_execute派发后丢弃响应（本机测试适配，不改防火墙/代理），先记OUTCOME_UNKNOWN；独立查receipt/idempotency/refund.state、原生outbound payment/credit/partial和S01审计，只有已证实done/实退2且唯一提交，才对同refund同key同payload发一次验证性重试，返回原结果、出款仍一笔，净收4。若查证不能证实，冻结该退款，不重退、不声称failed。这是同一新来源的6入/2出，不另开第二2来源，不在scratch提交资金。failed是显式登记的合成状态，绝不叫真实支付网关失败/真实资金转账；HTTP请求和原生提交证据仍按实际层级标HTTP/RPC、MODEL_NATIVE_COMMITTED并另标SYNTHETIC_FIXTURE。正常、failed、recover各操作有独立operation_ref；execute与其同key重试共享operation_ref，分开TC/request_id/attempt，不能用只有MODEL的故障注入代替真实refund HTTP丢响应。

E：仅新目标带已提交A/B/C/D数据，固定候选执行-u ydental_settlement（非-u all，不升级临床等历史模块）。升级前停自己的HTTP精确PID，独立前基线；升级exit0与原生日志/模块状态/独立后读分别核；S01诊断桥接为Python无schema，验证导入/API兼容。前后所有旧及新业务账款、原生凭证/库存、权限、文书v3/v4、审计旧行、原件/附件/文件完整不变；明确允许模块/view/ir.model.data等技术元数据变化并逐项审查。升级失败禁止把候选库重建/重克隆或git revert当DB回滚：保留库、文件、日志和升级退出；仅按已批RO核实际模块/schema及业务不变量。若未知事务/完整性则硬停，若仅普通可解释且业务完整的应用升级错误，修代码后先经tester+acceptance确认重入条件再用同一目标/新candidate重试，受整体预算约束，不丢v3/v4/新D提交。升级后真实A旧原件同SHA、B RPC只读负向/C关键matrix、D只读旧receipt防重状态、LOG最小正常/拒绝/程序错误（后者scratch注入）和受影响S01/结算/原件测试回归。重新渲染当前动态票据仅限已批准样例，不覆盖旧原件；必要中文PDF逐页目视。不能靠普通安装代替带数据升级，E不补跑旧整条740资金。

LOG-11在实施时派生一个fresh acceptance_locator（不继承开发/注入答案），仅给标准入口index/manifest/AC，验收其实际首异常定位和UNKNOWN判断/耗时；当前方案评审agent不冒称已完成该运行测试。

12 LOG+22 S10逐行完整映射见acceptance-matrix.json及summary.md；本轮所有新增运行项NOT_RUN，历史正式采纳分列。方案评审不是运行PASS，LOG通过不代表A—E通过。

## 6. 收敛、停止和最小规则建议

普通代码/夹具/断言问题：tester先保存首异常/最后可靠提交，developer最小修改，锁新candidate，重跑原失败+影响面；acceptance独立退回/接受。包内最多初次+2个修复循环（并受12进程/48RO/8小时总体上限），同一签名连续2轮无新证据就换假设/最小化；不能只改断言放行。编译/lint错误可直接修，不机械造业务失败。已提交经济操作不因修复循环重放，只用新来源或合法只读查证。预算不足交已完成范围、缺口和推荐，不续借旧额度。

硬停止受影响运行：身份/cluster/OID/config/SHA漂移；未知资金/提交；Native SIGSEGV/SIGABRT；证据严格读回不一致或关键链不可用；越权真实内容泄露；金额/库存/权限/版本/原件完整性异常；新来源不明；活跃他人编辑权；工具安全拒绝；需要未批准依赖/权限/系统资源。立即禁止受影响下一写/重试；父进程保存退出，保留旧失败与新文件，不伪称清理或ROLLBACK已完成。仅按获批RO核状态，无足够安全核实条件就UNKNOWN。独立scratch/安全源码工作可继续，主控最终交付而非空泛BLOCKED。

本轮不改AGENTS。最小未来建议：仅在最前追加WORKFLOW-V2当前入口，引用本包批准消息/父SHA/范围/owner/停止条件；明确原D1.2、旧R0/R1/R2和旧commit/push/逐错等待只为历史，不恢复其额度；旧材料全部保留。保留不动core/odoo12/生产/资金/权限保护；不删旧事故证据、不全量重写AGENTS、不据6125774169展开环境调优。普通包内修复自治与硬风险停止同时成立。当前无commit/push；未来实现交付正常线性product→test→evidence提交/push需纳入整包批准，不合并/force/deploy，不改Issue正文/状态/Project。

## 7. 一次待批准范围与明确推荐

推荐批准本文件第2—6节作为新的完整实施包：最小日志Python/控制器适配和示例配置；新runner/测试/验收材料；上述最多2条事故副本新RO（P021新连接0）、1维护连接/2新库、48目标RO、12 Odoo启动和指定端口/单浏览器/私有配置/8小时窗口；A合法编辑权与同SHA原件、B12层结果、C权限矩阵、D独立6/2合成、E S10-only升级；一处AGENTS新入口；正常线性提交/push和#34脱敏进度/最终技术复核申请。授权后普通修复包内自治，最终独立验收agent审核后交GPT技术复核。

不授生产、真实患者/支付、S11、旧事故业务续跑、系统/PG运维/网络硬件专项、sudo扩张、core/odoo12修改、删旧证据、合并/强推。若新RO基线无法成立，A/E主目标准入阻塞，保留v3/v4历史采纳和UNKNOWN，报告具体差异；不能为了满足退出表重做旧文书或资金。

本轮到PLAN_READY结束。所有运行范围仍待明确批准；不是本文件生成即获许可。


## LOG-01—LOG-12完整映射

共同前提：完整实施包明确批准，product/test/core冻结，指定新环境/工具准入成立；tester执行、acceptance独立复核。以下都是拟测定义，当前一律NOT_RUN，不是12条PASS。每项证据包括固定版本/真实角色、case intent/result、适用四层索引与独立状态；原生配置当前未核。资源按主计划统一上限。

|AC|需求/实现位置|具体TC|必需层级|资源/最小证据补充|当前|
|---|---|---|---|---|---|
|LOG-01|原生配置兼容；diagnostics.configure_once / netsvc.init_logger只读 / logging-s10.example.json|L01:正常/异常启动和重复初始化；原生factory/handler字段兼容、无重复|STATIC/SYNTHETIC_FIXTURE/HTTP/RPC|scratch日志配置+单次启动|NOT_RUN|
|LOG-02|端到端关联；bind_context/reset_context; _audit audit_ref; query_timeline|L02:正常/拒绝链；两真实并行请求不同actor/trace不串；缺上下文显式null|STATIC/MODEL/HTTP/RPC|单服务两请求+独立audit查证|NOT_RUN|
|LOG-03|拒绝/异常分类；diagnostic_errors.py / action parse-vs-service catch-sites|L03:缺权限/日结/版本冲突固定码；合成NameError/TypeError程序异常；403/409/303不变|STATIC/MODEL/HTTP/RPC/SYNTHETIC_FIXTURE|新夹具拒绝与scratch故障注入|NOT_RUN|
|LOG-04|首异常与secondary；supervisor.save_primary / evidence.seal / diagnostics.safe_exception_frames|L04:合成业务异常+保存异常+fallback异常；首异常不覆盖、不递归serializer|SYNTHETIC_FIXTURE|非Odoo安全工具用例|NOT_RUN|
|LOG-05|真实事务结果；intent/dispatch/independent_verify; D-FAILED/D-LOST|L05:回滚、accepted/returned与commit分列；真实新refund丢响应先UNKNOWN再独立核实；不盲重退|MODEL/HTTP/RPC/MODEL_NATIVE_COMMITTED/SYNTHETIC_FIXTURE|新主目标唯一6/2+D observer|NOT_RUN|
|LOG-06|日志无业务副作用；diagnostics纯primitive / access._audit原失败规则|L06:静态禁ORM/flush/uid/default_env/锁/事务；开关同夹具经济差异0；强制审计失败回滚|STATIC/MODEL/HTTP/RPC/MODEL_NATIVE_COMMITTED|scratch等价夹具+主目标A不变量|NOT_RUN|
|LOG-07|独立进程退出；supervisor.launch/record_exit; faulthandler独立FD|L07:正常/异常/timeout/安全非Odoo信号子进程；历史965603退出解析|STATIC/SYNTHETIC_FIXTURE|非Odoo工具测试；不诱发新Native|NOT_RUN|
|LOG-08|严格JSONL完整性；logging.validate_jsonl|L08:重复键/NaN/UTF8/截断/oversize/缺run-end/重复event；标INVALID不修旧证据|SYNTHETIC_FIXTURE|离线短坏行夹具|NOT_RUN|
|LOG-09|隐私与注入；diagnostics白名单 / public export scanner|L09:合成password/cookie/token/病例/换行/含秘异常；关联非secret；公开自动扫描+人工复核|STATIC/SYNTHETIC_FIXTURE|本包合成秘密与公开材料|NOT_RUN|
|LOG-10|保存并发/开销有界；PidFileHandler / supervisor单进程独占段/索引|L10:两写者分文件；上限/轮转/空间/权限失败；测开关时延、大小和事件数；不删历史|SYNTHETIC_FIXTURE/HTTP/RPC|新run文件，16KiB行/10MiB段/5段/1GiB包|NOT_RUN|
|LOG-11|独立验收定位；query_timeline / summary / failure package|L11:未来fresh acceptance_locator独立线程仅拿标准入口index/manifest/AC，不继承开发/注入答案；定位首异常/最后可靠提交/UNKNOWN，记录实际耗时，无预设SLA|SYNTHETIC_FIXTURE|新失败夹具包；验收未参与写实现|NOT_RUN|
|LOG-12|S10最小样例；A合法只读或D正常 / B-C拒绝 / scratch程序异常|L12:正常+拒绝+程序异常三样例联四层、明确真实HTTP与模拟/MODEL边界|MODEL/HTTP/RPC/MODEL_NATIVE_COMMITTED/BROWSER/SYNTHETIC_FIXTURE|获批新主目标与scratch；LOG不代替A-E|NOT_RUN|

## F1—F6、T01—T16共22行退出映射

H1=[P021正式限定采纳6230102263](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230102263)；H2=[文书子证据限定采纳6232155980](https://github.com/Yredxin/YDental/issues/34#issuecomment-6232155980)。完整未改历史对象保留在父HEAD的 [exit-table-reviewed-terminal.json](https://github.com/Yredxin/YDental/blob/e7cd02689b92c0cc4f7343842268b21e56de9f80/docs/evidence/s10-closeout-v1/exit-table-reviewed-terminal.json)，按下表行序/rows/0—21可定位；本轮只引用，不重判或修旧证据。表中历史层级只描述限定采纳，不能升级MODEL为真实网络。所有行共同前提是新准入成立、A继承v3/v4、无未知提交/完整性/Native停止；tester执行、acceptance验收。新TC引用下表后的19项精确证据要求。

共同受影响回归：E前后全历史及本包经济/权限/文书/审计/附件/原件存储不变量；日志/typed catch影响路径的身份、UI错误/翻译/API兼容；只有直接涉及业务并发语义时用新scratch独立backend回归，不用LOG关联并行替代资金竞态。新资源按主计划上限，已提交旧经济不重放。

|行/原需求|历史正式采纳范围|来源/历史层级/限制|本轮新TC与退出缺口|新增状态|
|---|---|---|---|---|
|F1：S10-F1（独立合成数据）：治疗600+检查80+发药6×10=740，出账740→实收500欠240→补240结清。重复请求不再收款/出账。|同一患者/执行/四费600+80+40+20=740；发布620后仍旧600；350+390原生核销、COMMIT及独立恢复读回。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED；保留740/350+390；原500+240只按原历史来源，禁止重收|E：E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|F2：S10-F2：已收740→申请退100→他人批准，在途100/实退0→确认真实退100，累计已退100/净收640。拒绝另一申请须原因且不产生退款。|新申请100异人批准/实际退100，收740净640；拒50无贷项/付款；unknown80核实未付取消、容量回390。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED；100/50/unknown80等独立历史不拼主链；D新failed/退款丢响应另证|D/E：D-ADMIT、D-NORMAL-6、D-FAILED-2、D-RECOVER-2、D-LOST-REFUND-2、D-VERIFY-RETRY、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|F3：S10-F3：实际微信录成现金且已日结→财务审批解锁留原因→更正登记→再日结，没有真实资金往返；实物退药另进待核查。|新现金日结550锁、异人解锁、更正300到微信、原生重分类move15、重结300；无现金往返。药品退回另记录。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED；旧日结/重分类与实物事实保持；新拒绝夹具测DAY_CLOSED，不解旧锁|E：E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|F4：S10-F4：真实诊疗/检查/发药、批次扣减→结算→补旧文书/重印票据，费库款不再变化，调价也不改原已确认费用。|同源治疗/检查/药房4+2/批次/四费/账款已提交，原件1留存；acquire完整经济差异为0，但患者mutex修订被冻结门禁拒绝并回滚。 产品未变，来源独立，限P021正式裁定采纳范围。；6232155980追加同源confirmed/v3和correct/v4已验证提交，release当前UNKNOWN。|H1+H2；MODEL_NATIVE_COMMITTED/BROWSER；6232155980仅采v3/v4子证据；A仍尾段未完成|A/E：A-STATE、A-EDITOR、A-ORIGINAL、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|F5：S10-F5（另一个独立场景）：旧账270、新账200，均选中，实收300→先核旧270，再核新30→旧账0、新账欠170，保留两张账单和一笔300收款。仅选新账时不得擅自核旧账。|新多账仅新200不动旧账；选300按270+30；同日稳定ID；真实前台Web只选invoice9收3，余额200→197。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED/HTTP/RPC/BROWSER；保留270+30及仅选新账，不再收旧款|E：E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|F6：S10-F6：前台小李有A结算权可从前台收款，无结算权者只能看到获准摘要。B看到A欠270仅只读；不能在B收A款，A权限且上下文合法时到A处理。|前台有权真实Web收3；六类无结算岗位board/pdf/pay拒绝；原件错店及撤权服务拒绝。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL/HTTP/RPC/BROWSER；普通前台真Web与六角色拒绝、旧模型原件负向层级分开|C/E：C-SCOPE、C-ATTACHMENT、C-TOKEN、C-REVOKED-PAGE、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T01：740重复/并发出账；来源有效出账一次|新源bill重试仍invoice1/四来源；财务方法与旧并发证据AST相同，历史两事务结论只按原范围引用。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL/MODEL_NATIVE_COMMITTED；历史双事务仅原断言兼容；LOG双请求不等于出账并发PASS|E：E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T02：740收500补240及重试；应收240→0，原生核销和实收一致|新350+390形成partial1/2、余额0；新5同key重试仅一笔，变更payload拒绝。旧500/240只历史引用。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED；保留350+390、原500+240历史及原5同key；不重收|E：E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T03：负/超额折扣、明确免单；非法拒绝，原因齐，零账无假收款|负/超额折扣拒绝；明确理由全额折扣产生posted零账，患者原生付款0。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL/MODEL_NATIVE_COMMITTED；新scratch折扣/零额回归，不记真收款|E：E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T04：退款自批与并发批准；自批拒绝，在途+已退不超允许额|新退款自批拒绝/异人批准、额度检查；旧审批/额度两事务子证据仅在未变财务方法范围兼容引用。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL/MODEL_NATIVE_COMMITTED；旧双事务额度仅原范围；如typed路径影响则新scratch真双backend回归，不用LOG并行代替|E：E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T05：退款失败/未知/实际完成/重试；不伪已退、不重复资金记录|真实unknown80核实未付撤销、done100原生出款与贷项、rejected50无资金。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED；旧unknown/done/rejected保留；failed和refund真实HTTP丢响应/核实/防重新增|D/E：D-ADMIT、D-NORMAL-6、D-FAILED-2、D-RECOVER-2、D-LOST-REFUND-2、D-VERIFY-RETRY、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T06：未收款减免；只调应收，不记实退|未收80减免产生贷项17、余额0，实际退款0、患者原生付款0。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED；保留未收80减免/实际退款0|E：E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T07：日结后改支付方式；财务解锁/原因/再确认，无伪退款|日结锁拒绝改支付方式；解锁原因/异人审批、现金→微信重分类、再结；无伪退款。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED；保留旧改方式/日结；只新夹具拒绝回归|E：E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T08：已出账数量更正、文字更正和实物退回；反向来源正确，文字不动费库，未退不回库|独立患者数量更正关联原费13→反向费14/贷项20，旧600不取620；主链药event3退1到quarantine，处方余量仍0、不增费退款。 产品未变，来源独立，限P021正式裁定采纳范围。；6232155980追加同源confirmed/v3和correct/v4已验证提交，release当前UNKNOWN。|H1+H2；MODEL_NATIVE_COMMITTED；旧数量/实物独立事实与同源文字v3/v4分列|A/E：A-STATE、A-EDITOR、A-ORIGINAL、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T09：同法人调拨与跨法人交易；实际收发/凭证对应、公司店铺隔离|新同法人调拨move24/qty5；新跨法人sale/purchase、库存及posted双方法人凭证，普通前台请求拒绝。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED/MODEL；旧跨法人真实原生凭证保留，新C测权限不重交易|C/E：C-SCOPE、C-ATTACHMENT、C-TOKEN、C-REVOKED-PAGE、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T10：他店代收/无权医疗全文或票据；越权拒绝，摘要与全文分离|六角色拒绝、原件19项MODEL/service断言；真实content404；image200因未存body维持证据缺失。不得称19真实RPC。|H1；MODEL/HTTP/RPC；19项仅MODEL/service；旧RPC-read=with_user().read；invalid token不是有效token；旧image200缺body仍证据缺失|C/E：C-SCOPE、C-ATTACHMENT、C-TOKEN、C-REVOKED-PAGE、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T11：中文票据及部分收退款；实收/欠款/在途/已退准确，法人门店正确|新bill/receipt/refund三份中文原生PDF各1页已逐页目视；740/0、实收350/退100/净250、done100状态准确。旧原件UI实际下载另1页同SHA。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED/PDF_VISUAL/BROWSER；旧三PDF/原件Codex目视是历史署名证据非本轮重测；新退款状态PDF逐页看|A/C/D/E：A-STATE、A-EDITOR、A-ORIGINAL、C-SCOPE、C-ATTACHMENT、C-TOKEN、C-REVOKED-PAGE、D-ADMIT、D-NORMAL-6、D-FAILED-2、D-RECOVER-2、D-LOST-REFUND-2、D-VERIFY-RETRY、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T12：安装升级及F4真实全链；事件、价格、批次、费账款一一对应|唯一新B正常安装，真实同源S08/S09/药房/价费账款已提交；全部645物理表独立尾审。 产品未变，来源独立，限P021正式裁定采纳范围。；6232155980追加同源confirmed/v3和correct/v4已验证提交，release当前UNKNOWN。|H1+H2；MODEL_NATIVE_COMMITTED；安装不代替带数据升级；同源全链尾段与升级仍BLOCKED|A/E：A-STATE、A-EDITOR、A-ORIGINAL、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T13：F5旧270新200收300及仅选新账；核销270+30、欠170，未合并账单；未选不核|选中旧270+新200、300只核270+30；仅选新账及同日ID序；普通前台额外新3只核指定invoice9。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED/HTTP/RPC/BROWSER；保留日期/ID分摊、仅选新和前台3，禁旧资金重试|E：E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T14：F6前台有/无billing权及跨店摘要；同一结算服务鉴权，无按岗位默认放开，无跨店代收|普通前台真工作台/收款；六角色无权拒；新原件read/export分别缺失及撤权旧绑定服务下次拒绝。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL/HTTP/RPC/BROWSER；旧服务撤权不代替新真实RPC/撤权旧页|C/E：C-SCOPE、C-ATTACHMENT、C-TOKEN、C-REVOKED-PAGE、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T15：已确认600调价620后结算/重印；退款驳回；仍取600快照；驳回原因和审计齐、不生贷项/退款|主链确认费用600→发布620→仍600出账；新退款拒50原因/审计/无贷项；原件v1真实UI重取同SHA，v2另存且v1未覆盖。 产品未变，来源独立，限P021正式裁定采纳范围。；6232155980追加同源confirmed/v3和correct/v4已验证提交，release当前UNKNOWN。|H1+H2；MODEL_NATIVE_COMMITTED/BROWSER；保留600/620价源及驳回50；A同SHA重取不重生成|A/E：A-STATE、A-EDITOR、A-ORIGINAL、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|
|T16：日结锁后补录、解锁更正、删除/篡改审计；锁覆盖新增/更正，合法补录双时间可查，单据日志不可普通删改|新实际前日/今日录入双时间、锁后补录拒绝、异人解锁再收1重结11均提交读回。 产品未变，来源独立，限P021正式裁定采纳范围。|H1；MODEL_NATIVE_COMMITTED；旧双时间/锁/再结保留；新增六动作各MODEL和RPC12结果|B/E：B-MODEL-6、B-RPC-6、E-PREBASELINE、E-UPGRADE-S10-ONLY、E-PRESERVE、E-AFFECTED-REGRESSION|NOT_RUN；阶段BLOCKED|

## TC→确切层级→最小证据

所有TC执行/验收仍tester/acceptance；当前NOT_RUN。MODEL_NATIVE_COMMITTED仅指独立连接观察真实Odoo持久事实；数据来源合成与HTTP/原生事实可以同时标注，绝不叫真实患者资金或真实网关测试。

|TC|必需证据层级|最小材料|当前|
|---|---|---|---|
|A-STATE|MODEL_NATIVE_COMMITTED|新准入RO身份/隔离/退出；doc v4及versions9→10/author/经济/原件独立基线|NOT_RUN|
|A-EDITOR|HTTP/RPC/MODEL_NATIVE_COMMITTED|真实actor7正常acquire/release或已无editor的独立状态；合法失效分支/审计/四mutex精确diff；v4/旧费库款不变|NOT_RUN|
|A-ORIGINAL|BROWSER/HTTP/RPC/PDF_VISUAL/MODEL_NATIVE_COMMITTED|真实工作台link/click/download；旧v1字节SHA同059287…；逐页目视及原件不重渲染计数0/经济不变|NOT_RUN|
|B-MODEL-6|MODEL|source/payment/audit各write/unlink六项framework普通用户拒绝；非空实际字段/目标前后存储/actor/su/回滚隔离|NOT_RUN|
|B-RPC-6|HTTP/RPC/MODEL_NATIVE_COMMITTED|六项真实JSONRPC请求/响应体/实际params；各错误层与独立旧对象/审计旧行不变|NOT_RUN|
|C-SCOPE|HTTP/RPC/MODEL_NATIVE_COMMITTED/SYNTHETIC_FIXTURE|每权限/店/公司/family/混源cell预期与真实响应；新合成fixture标识与old对象只读不变|NOT_RUN|
|C-ATTACHMENT|HTTP/RPC/MODEL_NATIVE_COMMITTED|content/image/download各实际body MIME bytes SHA；合法safe placeholder解码像素/尺寸/内容对照及无原件泄露；独立附件/原件行和审计变化|NOT_RUN|
|C-TOKEN|STATIC/HTTP/RPC|无/随机无效/合法受控有效token各实际请求或N/A源码不可签发理由；原件native binary前置拒绝；token不进入公开材料|NOT_RUN|
|C-REVOKED-PAGE|BROWSER/HTTP/RPC/MODEL_NATIVE_COMMITTED/SYNTHETIC_FIXTURE|新合成用户授权前页面/撤权后旧页下一请求拒绝；同源read/export分离及正常恢复原fixture权限的独立核实|NOT_RUN|
|D-ADMIT|STATIC/HTTP/RPC/MODEL_NATIVE_COMMITTED/SYNTHETIC_FIXTURE|新独立来源及真实账号/店/公司/scope/日期/全相关渠道日结锁准入；无旧钱款/锁/权限改动|NOT_RUN|
|D-NORMAL-6|HTTP/RPC/MODEL_NATIVE_COMMITTED/SYNTHETIC_FIXTURE|唯一新patient/source/invoice费用6与一次收6；native inbound/partial/receipt/audit独立核回|NOT_RUN|
|D-FAILED-2|HTTP/RPC/MODEL_NATIVE_COMMITTED/SYNTHETIC_FIXTURE|新refund2申请/异人批准；refund_uncertain failed合成线下未付事实/状态/额度/audit；非真实网关故障标识|NOT_RUN|
|D-RECOVER-2|HTTP/RPC/MODEL_NATIVE_COMMITTED/SYNTHETIC_FIXTURE|合法finance verified_not_paid→approved；额度/审计独立状态，不增加出款|NOT_RUN|
|D-LOST-REFUND-2|HTTP/RPC/MODEL_NATIVE_COMMITTED/SYNTHETIC_FIXTURE|refund_execute唯一派发+客户端故意丢响应的独立dispatch记录；OUTCOME_UNKNOWN→新RO核done/唯一outbound/credit/partial/receipt/audit；未知不重放|NOT_RUN|
|D-VERIFY-RETRY|HTTP/RPC/MODEL_NATIVE_COMMITTED/SYNTHETIC_FIXTURE|前置已核done后同actor/store/key/payload/operation_ref一次retry；返回already_accepted/native出款仍1笔2/净收4；退款PDF实际字节/目视由T11另列|NOT_RUN|
|E-PREBASELINE|STATIC/MODEL_NATIVE_COMMITTED|目标SHA/config/marker/模块/schema/关系全清单；旧及新增经济权限临床审计原件附件全域前存储签名|NOT_RUN|
|E-UPGRADE-S10-ONLY|STATIC/MODEL_NATIVE_COMMITTED|精确-u ydental_settlement命令与独立父进程exit/signal；原生日志/模块版本/事务后RO状态；失败保全不重克隆/不伪回滚|NOT_RUN|
|E-PRESERVE|MODEL_NATIVE_COMMITTED|逐行存储全域前后diff/附件与filestore逐文件bytes SHA；升级技术元数据逐字段白名单及原因；所有历史与本包提交保全|NOT_RUN|
|E-AFFECTED-REGRESSION|MODEL/HTTP/RPC/BROWSER/PDF_VISUAL/SYNTHETIC_FIXTURE|受影响S01/clinical/settlement/original方法与typed异常API翻译回归；B真实RPC/C关键cells/旧原件UI同SHA和PDF逐页；D只读唯一提交，不重执行资金；新合成并发仅直接影响需要时|NOT_RUN|

## acceptance独立方案评审全文

# 独立验收角色方案评审

任务 `S10-LOG-AND-CLOSEOUT-v2`；消息 `YD-S10-LC2-PLAN-20261017-01`；revision `1.0`。

评审角色为实际子线程 `/root/acceptance`，父线程 `/root`，父 HEAD `e7cd02689b92c0cc4f7343842268b21e56de9f80`。工具公开的真实线程标识为此 canonical task name；未推测内部 UUID。主控从本会话 rollout metadata 提取的实际派发开始为 `2026-10-17T10:02:15.856Z`（见 agent-roster.json）；本角色首次独立时钟记录为 `2026-10-17T10:03:05Z`，终审时钟为 `2026-10-17T10:12:57Z`。唯一可写文件为本报告。角色共享父会话实际权限，角色约束不构成独立 OS 沙箱。

当前评审结论：`PLAN_REVIEW_READY`。本文件不表示 LOG、A—E 或 S10 运行验收通过；应用测试、HTTP/RPC、浏览器、PDF、数据库连接均未执行。

## 独立读取与事实边界

完整读取用户 04 提示词及所附 03 全文，直接通过 GitHub API 读取正式裁定 `6232155980`、`6230102263` 与 #34 当前正文；只读了 `terminal-verified-partial-facts.json`、`r2-A-correct-checkpoint.json`、`r2-window-tail-primary-exception-index.json` 等现有材料，以及实际 checkout 的 `ydental_clinical_service.py` 编辑权路径、结算控制器和 S01 审计不可变方法。大表退出材料出现嵌套历史后只提取22行的顶层 ID/remaining，没有重算旧大快照，也未把同次保存副本当独立测量。

采用 `odoo-security` 的权限与公开 RPC 边界进行定向方案审核；读取 `odoo-review` 流程仅用于确定审查层级，本轮没有产品 diff，也不声称完成全 addon 安全审计。

独立确认以下边界必须保留：

- 正式裁定已限定采纳 acquire、confirm/v3、correct/v4 与独立核回子证据，不能重新审判或重放。
- 最后有效检查点是 confirmed/v4、writer7/editor7/session109；这是历史检查点，不是崩溃后当前状态。
- release 只有已派发事实，没有已验证提交；不能凭无成功 marker 断言回滚或当前编辑者。
- `r2-final-tail-RO` 无效，不能修补成新的基线。Native 根因继续 `UNKNOWN`。
- T10 历史“19项服务/RPC”混写不能提升证据层级；原 MODEL 证据保留为 MODEL。
- P021 所用 `not-a-token` 不是有效签名 token 旁路验证；下一 C 矩阵必须区分无 token、随机无效 token 和合法受控有效 token。旧图片200缺 body 不能被本轮“推断占位图”补成成功。
- LOG 是新增验收要求；所有本轮运行状态应为 `NOT_RUN`。`PLAN_REVIEW` 不能写作产品 PASS。

## 进入完整方案复核的必要条件

1. 12 条 LOG 和 22 行 S10 必须逐行包含历史采纳范围及出处、新需求与缺口、具体 TC、前提、资源、证据层级与验收者，不能只按主题概括。
2. 资源包明确新只读核实连接、来源/目标环境身份、filestore、端口、进程与预算；所有旧额度封存，同一库唯一串行执行者，候选运行时源码冻结。
3. 编辑权按实际 `_valid_editor`、`_acquire`、`_held`、`_release` 分支处置。只有真实有效原持有者才释放；合法失效后重新 acquire/release 应保留审计；未知或他人有效锁停在门禁，不手工改字段。
4. B 的 source/payment/audit × write/unlink 六项，MODEL 与真实 RPC 必须各六项单列；C 的允许/拒绝矩阵必须同时含正例、撤权旧页及图片实际内容语义。
5. D 只用独立新合成资金来源，先核查真实账号/当地日期/支付方式/全部相关日结锁；未知提交先查证，绝不重退旧钱。
6. E 只升级 S10 模块及明确依赖，保全历史与新增提交，覆盖公共日志适配影响；模型测试不能替代真实 HTTP、浏览器或 PDF。
7. 日志适配没有 ORM 查询/flush/commit/uid/锁副作用；首异常走最小独立路径；强制 S01 审计失败不能被 optional 诊断降级吞掉；控制器 UI 响应契约保持独立评估。

## AGENTS/旧流程冲突的最小建议

仓库 AGENTS 首节停留于旧 D1.2 窗口，其旧“正常提交/推送后停”等要求与用户本轮 `PLAN_ONLY`、禁止 commit/push 冲突；本轮按用户最新直接指令执行，只创建规划材料，不改 AGENTS。未来获批实施包可在 AGENTS 顶部追加简短当前入口，列本包唯一授权、父 HEAD、只读来源/新目标、历史成果和硬停止保护，并将下方旧窗口明确标历史；不能清空保护或把剩余额度复活。

包内普通代码/夹具/断言错误由主控内部闭环；Native、未知资金/提交、越权泄露、数据完整性异常与越界资源须冻结受影响运行。同步失败只补同步，不重跑业务。

## 最终独立方案评审

已独立读取 developer、tester 两份交接及统一 `plan-and-acceptance.md` 初稿，并向主控提出以下具体闭环项；当前不预授予运行批准。

|发现|初稿问题及风险|要求的闭环|
|---|---|---|
|AR-01 / 高|D 把收款丢响应、scratch 退款执行、可选第二合成退款来源分散，经济来源数量及 T05 真实退款丢响应覆盖不明确。|采用唯一新6/2来源：收6、申请2、异人批准、支持 API 标 failed、核未付、recover、只执行一次退款并受控丢弃响应、独立核实唯一实退、最后同key重试；既定旧钱不重退。若选其他方案，必须同样精确声明资源和覆盖缺口。|
|AR-02 / 中|统一初稿把 Odoo typed 异常放入声称纯 stdlib 的 diagnostics.py，接口与依赖描述互相冲突。|typed 异常单独 diagnostic_errors.py；primitive helper 不依赖 Odoo，或明确撤销纯 stdlib 边界并评估影响。推荐前者。|
|AR-03 / 中|A 自然失效等待和 HTTP 总额未具体收敛；新DB名称/marker规则没有列全。|明确等待上限、HTTP 请求总上限；新库匹配既有 `ydental_s10_test_YYYYmmddHHMMSS_hex8` guard，run_dir/marker/config SHA/core/cluster全部一致，升级前运行器也重核，不能仅依赖 pre_init_hook。|
|AR-04 / 中|tester T10 历史行仍混用19项service/RPC描述。|按正式裁定改回19项 MODEL/service，真实网络层始终 NEW_NOT_RUN。|

初稿结论为 `PLAN_REVIEW_CHANGES_REQUESTED`。随后主控完成 AR-01—03 的主计划修订：D 定为唯一6/2来源、pay6正常返回核回、refund2唯一execute受控丢弃响应后先独立核实再同key一次重试；typed 异常拆为独立文件；A 自然等待120秒、HTTP总请求600/原件GET12、新库guard和升级marker重核全部明确。developer 已独立交接确认对齐最终方案。tester 已纠正 AR-04 的 T10 历史证据层级。验收角色重新读取了对应实改位置，未以口头“已修复”代替文件核对。

最终又提出并闭环 AR-05：22行最初重复列全7层词汇，没有真正给 TC 分层；主控补入19个 `tc_evidence_requirements`，逐个列确切 `required_layers`、最小材料和 NOT_RUN，22行改为引用对应 TC。LOG-11 补为未来 fresh `acceptance_locator` 独立线程仅拿 index/manifest/AC，不继承开发注入答案。主控还明确 execute 与其重试共享 operation_ref；CREATE 采用 autocommit/IDLE、安全 identifier 且一次失败即停；E 失败保全同库，不把重克隆或 git revert 冒充数据库回滚。

### 终审范围与结果

独立逐行审查了 LOG-01—12 共12行，以及 F1—F6/T01—T16 共22行，合计34行；核对每行现有采纳范围/正式来源、新TC/缺口、受影响回归、前提、资源、验收者和新执行状态。对19个 A—E TC 的最小证据和层级也逐个阅读，文档解析检查确认34个 AC ID 唯一齐全，22行引用全部可解析，所有新增执行均为 NOT_RUN。该检查只读取规划 JSON，不加载应用、不连接数据库，也不是应用测试。

|审查面|方案层面结论|
|---|---|
|历史保全|保留6230102263与6232155980限定成果；v3/v4不重做；release与当前编辑权UNKNOWN；T10的19项MODEL不提升为RPC。|
|日志12项|具体helper/typed错误/入口/审计桥接/父进程/校验与检索位置、TC、资源及层级齐全；强制审计失败原样传播；首异常与secondary分开。|
|运行准入|P021来源0条新连接，仅事故副本最多2条新RO；维护连接1/CREATE2、两个新目标、目标RO48、Odoo启动12、单Firefox最多3会话、HTTP600/原件GET12、8小时和1GiB上限明确；这些都是待批准的未来上限。|
|A|新可信基线、真实编辑权分支、120秒等待、旧v1真实工作台重取同SHA、经济与版本不变已形成具体退出路径。|
|B/C|6 MODEL+6真实RPC分列；源read/export、旧页撤权、公司/店/family/混源、附件与合法token路径明确；图片200以实际内容语义裁定。|
|D|唯一新6/2来源覆盖failed恢复及真实HTTP退款丢响应；唯一execute后先独立核实，再同key一次防重验证；不操作旧钱。|
|E|新主目标带数据S10-only升级、持久事实保全与受影响回归明确；失败保全和安全重入条件不会丢已提交v3/v4或新资金。|
|协作与停止|一个文件一个所有者、一个库一个串行执行者、冻结候选、普通错误内部闭环；Native/未知资金/泄露/完整性/越界/工具拒绝硬停。|

结论为 **PLAN_REVIEW_READY**：建议将统一主计划第2—6节及其明确资源上限作为一次完整实施包请求批准；方案审查发现的 AR-01—05 已闭环，未发现剩余需要用户决定的技术选择。本结论没有授予实施或运行许可，也没有授予S10阶段PASS。

仍无法证明的事实保留为未知：Native C根因、事故后真实编辑权/release提交、当前数据库状态与可复制性、Ubuntu实际日志配置、未来候选SHA和新目标OID/可用端口、真实运行验收结果。它们通过已提出准入/实施/独立验收取得，不以方案文档代替观测。若准入不成立，按具体差异停受影响工作，不重做旧文书或资金；安全工具开发/静态工作可以继续。

签署：`/root/acceptance`，终审 `2026-10-17T10:12:57Z`；输出已交主控。GitHub发表/全文读回由主控所有，本角色未发表任何外部消息。

最小资源补充复核 `2026-10-17T10:13:20Z`：主控将保护库新RO总额从4降为2，P021来源不作为复制源且新连接为0，仅事故副本允许新基线/复制后保全各一次。已重新读取主计划资源表和一次批准范围，确认实改；该缩减不影响继承v3/v4的准入路径，维持 `PLAN_REVIEW_READY`。P021零连接不能称其现状已实时核实或新终审保全通过。


## 本轮新材料校验索引

以下仅是本地规划文件的UTF-8字节身份，不证明运行事实，不声称文件已推送。远程完整方案/映射/独立评审已在本评论正文提供；developer/tester详细交接在本地，主方案已纳入具体决定。sync-state和comment/self不纳入下表，避免自引用及同步后变化。

|规划材料|bytes|SHA256|
|---|---:|---|
|plan-and-acceptance.md|29151|84bd69296d19a06d1daf3a937b5ca7c46c95712c62f6d81f9f525c53ef0162ce|
|run-manifest.json|3772|04edb4d7f81b2fed3a97959f0a3aacd04c4a0e2c8f3c5593ac831fefe5f5cb3a|
|agent-roster.json|4900|a26fd31668661c38199d4f7388edc976a9bf3f307081bdebfb975602f6895fb2|
|acceptance-matrix.json|82004|5d5d2109af42eecd9fdba19bd2cc219290e908bbe273d43c18153ae7c75c81ff|
|summary.md|3108|89055ded917c1523398718ed8ed42e11c6ccb62b3b14a82bf19d03d5bd1defc3|
|developer-handoff.md|29063|356d08dd1e31a356b4eef2b95e36f2d4a984232839a33e88a8f0a06dd73c2951|
|tester-handoff.md|36139|1473a208c451fc2fcedc1913e9d890315ffc6cefc515353f7fc16b1f6a36318e|
|acceptance-review.md|10671|89f326a7561d255b9cf4f4672b8cd6efee14715f3d9e2fb738e19d92a68990b8|

本轮只读代码/GitHub/有限旧日志和版本，新增规划文档及本评论；没有修改产品/AGENTS/配置/旧证据，没有commit/push，没有连接数据库、启动Odoo或业务浏览器/应用测试，没有改Issue正文/状态/Project。本评论发布后用REST GET完整body程序化UTF-8字节比较并保存SHA与sync-state；此句是将执行的步骤，尚不提前声称读回已完成。

明确推荐：一次批准主方案第2—6节及第7节资源/实施交付范围后，再开始编码与新准入；普通修复包内自治，独立验收后交GPT技术复核。当前PLAN_READY即止，不恢复R2/R3、启S11、合并/强推或生产部署。若同步失败，保存完整USER_RELAY正文和UTF-8 SHA，补同步不重跑业务。
