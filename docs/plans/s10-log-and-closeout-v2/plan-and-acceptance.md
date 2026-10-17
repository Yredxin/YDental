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
