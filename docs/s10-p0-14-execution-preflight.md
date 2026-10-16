[CODEX] S10-P0-14 原生DOM/登录审计修正及W5双只读单克隆确认完整执行预检

唯一授权6212000008、P0-13正式裁定6211928330。原分支codex/s10-settlement-finance-r1-20261013、唯一父HEAD 6c64403f9c015c669e50e750aff6e0e7a2eab3c0；origin和本地/远端GitHub REST ref同值；core f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb tracked干净。完整API读取#23当前正文/3评论、#34正文/224评论、#35 OPEN/0；预检发布前再查#34仍224末条本授权/远端HEAD未变，无已存在P0-14预检/交付/并行授权。本轮当前SQL/CREATE/HTTP/Firefox/login/switch/clinical GET/业务POST全部0。

第一优先离线门禁完成：19项确定性STATIC_REVIEW及18项执行器文件内检查PASS；后者在P0-13实际保存的完整login-only目标后验快照上证明新精确规则能接受合法字段而旧证据保持原FAIL，不模拟业务POST。静态入口没有PostgreSQL/Odoo/HTTP/Firefox导入或动作；静态Node只验证Number(undefined)/Number('0')表达式。旧clone p013_6a91d3c8/OID2100325完全不连接/不复用/不读写其运行目录；仅读取已保存的私有HTML、SQL快照、HTTP响应及固定公开证据。准备期一次冻结入口引用旧connector文件后缀发生FileNotFoundError，已在发布前纠正新脚本输入路径并保留失败日志；当时三项源码证明已PASS，执行预算一直0，无伪造预检。

三项真实源码及逐字段依据：
1. ydental_clinical/views/ydental_clinical_templates.xml 的t-att-data-execution="execution.id if execution else 0"；固定core odoo/addons/base/models/ir_qweb.py约2119行，输出条件if value or isinstance(value,str)，数值0不输出，文字0输出。保存真实HTML确实无属性。原生document.js约262行Number(root.dataset.execution)在缺失时NaN/falsy，字符串0也falsy；不把缺失伪造为0。新DOM条件仅在实时user7无serving/verify、doc1原execution1 handover、document1/revision1/version2/pending/heartbeat2/canHandover=no/完整原文全符时接受缺失或字符串0；非0/actor或版本漂移STOP。queue/models/ydental_queue_service.py _actor_execution明确仅查本人lease及serving/verify。没有DOM注入或QWeb/JS修改。
2. ydental_access/models/ydental_access_service.py _session_for_key约38—63行以当前env.uid创建session，_switch约325—338行原生选择店并write；core odoo/orm/models.py create约4291/4293行默认create_uid/write_uid=self.env.uid，_write约4010行同样write_uid=self.env.uid，sudo约5431行明确保持当前user。只有本次唯一新增session可相对历史row4允许write_uid不同且必须严格7/create_uid7；actor7/store1/revision1/key_hash绑定本人SID。其它模板字段仍相等，只保原有id/key_hash/create_date/write_date差异，全部旧session行原样。既存模板write_uid8不是新会话的操作者。
3. clinical/controllers/clinical.py workbench约35行非sudo pending文书search(store1,pending)→core odoo/orm/models.py BaseModel.search约1450行self.search_fetch→ydental_access/models/ydental_access_source.py search_fetch约88行，在非su时records._source_audit('source.view')→该文件约146行_scope和_audit_values，源码固定source_model、当前uid、当前scope店、来源model/id/category、accepted和空reason/before/after；_access_domain/_source_domain及clinical.document的medical _access保证原生合法读取。用实际纯dict构造函数AST逐字段比P0-13真实audit335相等，错user/store/doc/source/category静态拒绝。W5只有doc1 pending，首次GET仅source.view1；confirm后pending列表空，末次GET source.view0。本计划严格总1（授权绝对上限2且每GET至多1），不是任何额外审计通用放行；与真实GET、版本状态及subject逐步绑定。

redirect GET修正：安装Playwright async_api/_generated.py Page.route文档约10580行明确redirect只回调首URL；_impl/_browser_context.py _on_request约723行独立emit所有Request，_on_response亦独立emit。原保存login303 Location=/ydental/clinical?document_id=1、Firefox临床response200及已保存服务器访问记录均1，旧route计数0保持。新执行器从BrowserContext request事件按真实Request身份计数，含redirected_from，response和最终原生Odoo log三方完全一致；route不重复增GET计数。所有POST仍必须经过真实route一次验证、响应校验、服务器勾稽，未知/重复/heartbeat转发前STOP；不修改/伪造网络响应。

唯一预定新库 ydental_s10_test_20261016_p014_7c42a9e1，HTTP127.0.0.1:18314，新私有目标目录目前不存在；独立maintenance实时查库名不存在/模板无连接，任一冲突即STOP。旧W5仅作只读模板：ydental_s10_test_20261015073500_e50f4a71/OID2100310/cluster7694897083368259627；configSHA867f761771ecc20931f69103388df699b094b748e6a9d392e15ebe3d406e43c7，markerSHA1a7f4a2a95e8aa0ea3d6da17abf6033976d2e39754185fa38e441a497351a5fa；父W4/OID2100301血缘与P0-10封存比。152filestore/manifest bd0b0fbad15868bbabb836fa7016a91187bb31c6b9b6d934b2a7a0fe035c4283，只读SQL后再核164指针。P0-13源后验全部643表是本批实时前验必须匹配的固定基准。

严格顺序与连接合同：
- 本预检新评论REST GET正文逐字读回，保存ID/URL/字符/UTF8字节/SHA后，才W5源前验连接#1。libpq default_transaction_read_only=on+psycopg BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY，第一条SHOW核只读/隔离级别，首次SELECT前确认；身份/无其他连接/canonical catalog643/全行SHA/P0-13源后643/P0-10保护47/稳定31/父血缘/152文件/164指针/92模块/QWeb/既存原全文及25资格，任一失败CREATE0。finally ROLLBACK/CLOSE。
- 25项当下权限/资格全部PASS、源前验确已关闭，独立postgres maintenance autocommit/IDLE，target名不存在、模板无连接、cluster正确才一次CREATE DATABASE新库WITH TEMPLATE W5；不杀连接、不改源、不重试。核唯一新OID、独立filestore152文件全等/configSHA/marker/dbfilter/data_dir/端点；目标前验只读连接#1全643表必须逐行等于源前验。
- 同一目标前验物理连接保留至Web结束，每步重新严格READ ONLY/RR事务/ROLLBACK，最小固定47表（doc/version/editor、审计/session/device/fence、全部25资格的人员/公司/授权/能力/患者关系/原execution/模块及少量原740来源依赖）；不在POST之间再扫描643表、不复用旧快照、不多开人工连接。每个阶段结果标为minimal47，绝不当全库经济证明；最终独立目标后验#2完成完整643表和全部627锁定表证明。最小表全名及字面SELECT已冻结机器计划。
- 原生HTTP一次/Firefox一次，本人user7 login一次，原生default store1/revision1（显式switch0，默认不符STOP），直接临床GET1含login redirect；现存Open按钮acquire1，立即Confirm text only按钮confirm1，JS自己release1、返回GET2。真实CSRF/Origin/cookie/SID scope及32—128位alnum connection、editor token、CAS expected_version2/完整原样TEXT_FIELDS+teeth/new native UUID逐项核对；不输入/补医学值、不save/correct/open新文书，不Python构造业务HTTP或直接ORM。
- 原生heartbeat2秒/timeout600秒不改；新context无holder/editor，acquire后立即Confirm，Confirm和自动Release期间native saving=true令timer原样return，release后token=null。各POST转发前47表小范围门禁及真实响应严格先通过，任何heartbeat/未知响应/403/409/超时/掉线/pageerror/额外POST/审计越界立即STOP，不换key、不重发、不自行补release、不回滚已成事实。保留原始异常栈/原evaluate和HTTP，原native SIGSEGV则立即停业务。
- 目标前验连接关闭、停止自有HTTP/Firefox后，目标后验#2新快照全643/filestore/逐字段白名单，比原版本及经济不变，ROLLBACK/CLOSE；随后W5源后验第二独立连接#2新READ ONLY/RR快照重读全部643/47/31/附件/filestore/config/marker，与真实源前验完全等，ROLLBACK/CLOSE。不用克隆SHA/旧事务代后验，无第3条源连接。异常STOP仍在安全可访问时做这一次后验，不继续业务。

全部SQL字面模板（643条已完全展开并连同固定catalog/列名冻结在机器计划）：

```sql
CREATE DATABASE ;
CREATE DATABASE ";
CREATE DATABASE {} WITH TEMPLATE {};
SELECT ;
SELECT c.relname,a.attname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='public' AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum;
SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(SELECT system_identifier::text FROM pg_control_system()),CURRENT_TIMESTAMP;
SELECT oid,datname FROM pg_database WHERE datname=%s;
SELECT pid FROM pg_stat_activity WHERE datname=%s;
SELECT pid FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid();
SELECT system_identifier::text FROM pg_control_system();
SELECT to_jsonb(t)::text FROM public.";
SELECT to_jsonb(t)::text FROM public.{} t ORDER BY {};
SHOW ;
SHOW transaction_isolation;
SHOW transaction_read_only;
```
动态Identifier只来自严格等于冻结643表/列的catalog；id存在按Identifier(id)，无id按to_jsonb(t)::text。固定参数只目标名/W5名，唯一DDL为上述新库CREATE；只读事务不DML/DDL/FOR UPDATE/advisory。

25资格逐项当前NOT_RUN，源前验后全PASS才CREATE：
- active_person_company_store_employee
- complete_nonempty_original_content
- current_patient_relation
- current_snapshot_capability
- doc_source_identity
- existing_synthetic_doctor_credential_verified_offline
- explicit_timeout_configuration
- handover_not_active_reception
- installed_clinical_qweb_matches_source
- installed_module_seal
- internal_ydental_group
- invoice_posted740_residual0
- medical_write_now
- native_payments_partials_500_240
- no_document_editor_or_stale_metadata
- no_live_actor_execution_fence
- no_refund_close_print_job
- one_active_membership
- original_current_execution_identity
- original_versions1_2_same_content
- pending_v2_responsible7
- qualification_satisfied_without_provider
- qweb_dom_and_zh_CN_present
- same_source_fees_sources740
- source_station_capability_and_context

身份限定patient1/company1/store1/doc1 pending2 author/responsible7/execution1 handover/旧lease inactive/无残留editor/无本人serving或verify；user7 active/internal/公司1/member5/employee3/medical-write/capability1及原资格；QWeb与源码/zh_CN一致。当前source→fee必须1→4/20、2→3/40、3→2/80、4→1/600，invoice1 posted/paid740/residual0、payment500+240/partial1/2原SHA保全。凭据仅复用既存合成doctor离线核PBKDF2，不补权限、不更改账户；完整原文只从本次源前验私有快照取得，DOM及confirm全字段/teeth与原文等值。

精确非经济逐字段白名单：
- res_users7/res_partner8/hr_employee3/resource_resource3仅write_uid/write_date，hr_version3另last_modified_uid/date，必须actor7；其它所有字段/旧行原样，timezone0变化。
- res_users_log append1（仅id/create_date/write_date差异、create/write_uid7且dates相等）；res_device_log append1（仅id/session_identifier/user_agent/first/last_activity差异，其余等旧user7模板，user7/loopback/Firefox/revokedFalse）；access_session append1按上节新增行规则，write_uid只该新行且严格7，create_uid7/store1/revision1/SID哈希匹配device。全部旧行不变。
- audit只append最多9，actor/create/write7、accepted、空reason、create_date=write_date、schema固定；login1(personnel/native_authenticated_login/user7/no store)，login.scope1(personnel/authenticated_session/newsession/no store)，自动store.switch1(personnel/interactive/newsession/store1/before storeFalse→1，不是显式POST)；clinical.view2/medical/clinical_document/doc1/store1；source.view严格首次GET1/medical/source_model/doc1/store1（最终GET0），空before/after；edit_acquire/confirm/edit_release各1/medical/clinical_document/doc1/store1，confirm before version2→3，其它空before/after。无editor_invalidated、source.query或其它事件例外。
- doc1仅7 editor字段、write元数据、state/version/saved_at；原content/author/responsible/execution/template全等，editor绑定本人新scope/revision1/同connection/hash/600秒，释放清空。只新增1 version3/confirm/author7/previous2/new UUID/digest严格绑定原content/CAS2；旧v1/v2全文/作者/整行全等。
- patient/supply/intake/queue各仅单行revision每真实action+1、总+3，其它字段原样；orm_signaling_default仅append≤3且exact id/date、旧行不变。未列627表全部原行SHA不变，含所有价格/快照/event/fee/source/receipt/account move/line/payment/partial/refund/close/stock move/quant/lot/ir_attachment/mail/模块/QWeb/PDF；filestore零变。任何不符STOP，不事后宽放通用元数据/审计。

全部脚本SHA256：
- scripts/s10_p0_14_audit.py: 03acd386777f2538b6015db04f8818a1a80c98996998eb6696b49c2cba9fae7d
- scripts/s10_p0_14_browser.py: a5570cfdfdd2283dac2395558eaeb53ac6c3fce2cedcf3f6cb6204c86486af64
- scripts/s10_p0_14_contract.py: 2df01350c9e2608833918f87bc3e5fecfda72438915ea7395434a00ff7b62752
- scripts/s10_p0_14_control.py: b4e0edf50168664c3767faa9b6a0c12c1abe31d026eb0733996d7d9baa585499
- scripts/s10_p0_14_eligibility.py: eb94bb2a4077b13a18e52510b87358c72baf7ce6f5001ec4b4b4d4fcfbbd0e1b
- scripts/s10_p0_14_preflight.py: f5c0521c4692f7e01f3e4e9796767b077520b0b549bf87cd1a98767fcbeec44a

机器计划 docs/evidence/s10-p0-14/execution-preflight.json SHA256=f2769b28d5941527792fef9a11b6bf8911033ff7aa30e886df246307dbb5c282；包含全部6脚本、静态依赖逐文件SHA、SQL/643与47展开SELECT/catalog列名、627锁定表和规则。static-contract.json SHA=540ff1cf2d042ada611cd4141206bfdbdfa9deecff70f7ff71183348f9d5ec34。
静态/原生依赖SHA：
- ../addons/web/controllers/home.py: f66bcf97503c4388c37b664fc4ca96a913a3166dc68d254b919bfe846587a482
- ../addons/web/views/webclient_templates.xml: 2e28e54d0819b34617aab70dcd1d55f024e588c2f4230013f1016e37e3762c3f
- ../odoo/addons/base/models/ir_qweb.py: f80ca78702c43017bb094d5f1b345cbf2a8f3c886cbe20f6f49a1f3581329a65
- ../odoo/addons/base/models/res_device.py: cfe76793b19cd15387a380f4d069263a72ccd42f6a672a575c9e7466817a6e44
- ../odoo/addons/base/models/res_users.py: 98a5c18d63069f19ce8eba95adb5809769e6e491630d4ed08b3a93e3097780cf
- ../odoo/orm/models.py: e84f13aeaf02b61f69a38f4e293400279334386fd7619e64f6a21a6b5a383668
- .local/s00-b-deps/verify-lib/playwright/_impl/_browser_context.py: 595800a63fa0b9901b46e30a5a8defca46f746b8c2a20bd7e8cb02193151e494
- .local/s00-b-deps/verify-lib/playwright/async_api/_generated.py: 4ce7017cc59fb0e5d84596cbbc5c614fd302716aa855ddeaaa21d9f8605f6178
- docs/evidence/s10-e2e-w5-ro1-r1/read-only-sql.json: ca2a304fae2918ed91005552c65de21dacdc6a18707d01a16bcabe59a0c06c73
- docs/evidence/s10-p0-10/read-only-sql.json: 3bbc7130ed4fa3575a1f4ee8e5ca527781c366bbddcaf6de0eb3d8853e0f65ea
- docs/evidence/s10-p0-11/eligibility-corrected.json: dcbcba1268358bcf00e30fa59b9dfa6cb2e73eff63aeedf1ea88bb5911d0e85b
- docs/evidence/s10-p0-11/execution-preflight.json: 73e0b1094877960bfac783547decfe2972c237348db9c44316139d11eaf9f6ec
- docs/evidence/s10-p0-11/read-only-sql.json: 3506708c4c88d10d555a4ca5d3074a52294db3e68a7dfa21a21d8711b50a93ee
- docs/evidence/s10-p0-13/source-after.json: 338472c2aa2308a8be0c3153abee1b962923f680b634afa5bc2a30d7cd86fcd5
- docs/evidence/s10-p0-13/source-before.json: 595d7f9de193f765ba398f05c7f30367c9e538cef4b89263e78f985c506bc50e
- scripts/s08c_network_policy.py: 4d9066d67a6dcc414169d801a9a0679c1635145ded9576f4c264c3ccf94daa41
- scripts/s10_e2e_w5_browser.py: a3db4471714888a142a47d0067572fe83d9ba92362e2384a26d4144d4509efbc
- ydental_access/controllers/access.py: f91e98407b133a22de78a2bd5c468eb4fff9b4f866e21a900f1afc60536d7627
- ydental_access/models/res_users.py: fd6079795cd8b5a5e79be358413fced4400683520a9cf0de3477466e2da31287
- ydental_access/models/ydental_access_audit.py: e07e56d2f4ed2ce489f516c4c902643919282976c02bc9278a68b3d73d8af317
- ydental_access/models/ydental_access_service.py: 9654000038903522213303fcd9cdc64612cdd335deac6a96afd993c4dfd61132
- ydental_access/models/ydental_access_session.py: 1d3d5ab9b30d7869c759697afee1bc623ba2ccf3832c9317ebb27bf3e59b9adf
- ydental_access/models/ydental_access_source.py: 2236034b969fed2a2ceabf15d368a94a081930b0850b8bb0deb6a86fc8d1c517
- ydental_clinical/controllers/clinical.py: 7b0f3a5f628de9cba389ea7ea8d261a6e999761dea8d645bde75dc5f9d6291bd
- ydental_clinical/models/ydental_access_service.py: 1e53d5c24d8d2d8b93754a6afd25dce54a0bd48497ca9a553bf89f863760f359
- ydental_clinical/models/ydental_clinical_document.py: 963354107c1e5eae7a33ecaf7757ff772bca0f15889365a5d0d9cb4d8632280a
- ydental_clinical/models/ydental_clinical_service.py: bb601a4d231585281cf569def652f78205993cf2d73f8273ae2cf50d620f6709
- ydental_clinical/models/ydental_clinical_version.py: a15652869e4d8c1b6d0ad70c1d5e0e744dad39b1f38fdae5ab10f7fc1f9e1717
- ydental_clinical/models/ydental_queue_service.py: 9ecb43c22963db4dd59ef451e6a5fae3443ca1194930baffdc771aa18d8eb606
- ydental_clinical/static/src/document/document.js: 98c862a13ca0586cf038e01139258bb2aca7edfd20dc8785ecf85812adb67a30
- ydental_clinical/views/ydental_clinical_templates.xml: f485aad62fb2b731358a94f86f9eeac41904df9a8564eb2bdb0dea2407ea8400
- ydental_exam/models/ydental_queue_service.py: a1943e857a0941bb2f2e7f9ea163ff475c45a73b09be91dbdea8eb942e2aa405
- ydental_intake/models/ydental_intake_service.py: fbcb3e9e8c1c46489d8d76c4aefbb4fabe56ef5b0f36bce7ed9b4b9de9c04a0b
- ydental_patient/models/ydental_patient_service.py: 2cc72f87a7dd7cf9bf541007bddb2c975458f564599400ae944b63f5ea4513e3
- ydental_queue/models/ydental_intake_service.py: a36e91c0558ed1cd7b5f68bbc5087a0f2425e2c80b95bb46934bd320f8c18c65
- ydental_queue/models/ydental_queue_return.py: 47edf4e34e5c2367bf23a380a731dea50af14ae53f2db4b94db0bc0565c61e99
- ydental_queue/models/ydental_queue_service.py: a5b3a037a2be9992edf5867b3d401b351e4a74820d36fcc8764d46e0cc1c2a6e
- ydental_queue_test/models/adapter.py: a45cbe79230d78f8e18463adb325c1dbbac59c13b0a00776bf3c6bc01072ea3c
- ydental_supply/models/ydental_access_service.py: f181b774d794bf78da00e7b183ca1cb46ce159addd2ca727a9c4ab83c1d5111d
- ydental_supply/models/ydental_supply_service.py: 3c043b19f1b14cd8f00f9dd141e35d6fff10cdad27c25a066341de4f34b124d0

执行argv=["/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python", "/home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s10_p0_14_control.py"]；HTTP argv=["/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python", "/home/redxin/code/odoo/odoo-sd/code/odoo-bin", "-c", "/home/redxin/code/odoo/odoo-sd/code/sd-addons/.local/ydental_s10_test_20261016_p014_7c42a9e1/odoo.conf"]；真实pw.firefox.launch(headless=True)一次/一个context/zh-CN/UTC/1440x1100，DEBUG engine PID/exit/signal原日志留私有。既有进程内network guard仅复制到本批新目录，不改系统网络/PG/Docker/依赖。
最高预算={"ACQUIRE": 1, "CLINICAL_GET": 2, "CONFIRM": 1, "CREATE": 1, "DIRECT_BUSINESS_ORM": 0, "FIREFOX_LAUNCH": 1, "FUNDS_STOCK_WRITE": 0, "HEARTBEAT": 0, "HISTORICAL_REPLAY": 0, "MAINTENANCE_CONNECTION": 1, "NATIVE_LOGIN_POST": 1, "ODOO_HTTP_LAUNCH": 1, "ODOO_SHELL_UPGRADE_INSTALL_INIT_TEST": 0, "OTHER_BUSINESS_POST": 0, "PDF": 0, "RELEASE": 1, "SOURCE_AFTER_CONNECTION": 1, "SOURCE_BEFORE_CONNECTION": 1, "STORE_SWITCH_POST": 0, "SUDO": 0, "TARGET_AFTER_CONNECTION": 1, "TARGET_BEFORE_CONNECTION": 1, "W5_CONNECTION_TOTAL": 2}。

P0-13及更早证据永久不改，其旧审计FAIL/GET漏计数原件保留；绝不重做refund14、close9、旧权限负向、refund13分页/store3、W5500/240或其它历史经济/临床动作。原始医疗内容/凭据/CSRF/cookie/editor/connection/session/key/HTML/HTTP/真实截图只在本地700目录；GitHub只ID/事件/状态/金额/hash。仅新增本批许可scripts/docs/evidence，AGENTS/产品/core/ACL/Issue/Project不改，无sudo/OS或PG或Docker或IPv6防火墙专项、不合并部署/S11。S10整阶段技术/生产/T12 BLOCKED，Native UNKNOWN/W4 STOP/W5旧browser exit1/final_audit NOT_RUN/同源原版PDF不足与正式财税到账缺口保留。本次成功或BLOCKED都正常线性固定提交推送，#34交付回执REST GET逐字读回后立即STOP等待GPT，不自评整阶段PASS。
