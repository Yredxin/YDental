[CODEX] S10-P0-13 W5两次严格只读前后全表与单新克隆原生文书确认执行预检

唯一正式授权6211098449。只在原分支codex/s10-settlement-finance-r1-20261013，从唯一父HEAD cf6692c27d48ebabf1b7d4f3ab1ef99ef4cfef74前进；core f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb tracked干净。GitHub API #23正文/3评论、#34正文/220评论（发布前重读末条仍本授权）、#35 OPEN/0已完整取得，origin/本地/远端HEAD一致，无并行P0-13交付。P0-12正式BLOCKED_PREFLIGHT裁定6211057301保留，不重审、不执行旧脚本。当前SQL/CREATE/HTTP/Firefox/login/switch/clinical GET及所有业务POST全部0。

本批新脚本独立命名，不导入任何P0-12/P0-11执行入口。17项文件内离线门禁检查通过，历史私有快照仅作比较器离线输入，不冒充当前SQL或25资格通过。前验后才重验当下资格。离线远端API读取出现间歇TLS超时；成功读回固定ref，未开展OS/PG/Docker/IPv6安全专项，无sudo、环境变更。

唯一目标 ydental_s10_test_20261016_p013_6a91d3c8；HTTP127.0.0.1:18313；离线目标私有目录不存在，maintenance再查库名不存在和W5无其他连接，冲突立即STOP。不复用p011_a730c9e4、不复用或写任何旧库。

旧W5永久不可写：ydental_s10_test_20261015073500_e50f4a71/OID2100310/cluster7694897083368259627；configSHA867f761771ecc20931f69103388df699b094b748e6a9d392e15ebe3d406e43c7；markerSHA1a7f4a2a95e8aa0ea3d6da17abf6033976d2e39754185fa38e441a497351a5fa；父W4/OID2100301/父封存与P0-10原件比对。离线152文件manifest bd0b0fbad15868bbabb836fa7016a91187bb31c6b9b6d934b2a7a0fe035c4283匹配，只能用SQL实时核164指针。

执行严格顺序：
1. 本唯一预检REST GET正文逐字比较成功并记录真实ID/URL/字符/字节/SHA后，W5前验来源连接#1。libpq默认只读+psycopg显式BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY，首条SHOW确认只读，首次SELECT前核isolation。源名/OID/cluster/0其它连接、public catalog严格643表与冻结列一致；全部逐行SHA、P0-10保护47表/P0-11全643/P0-RO1稳定31表独立比，原附件指针、152文件、92模块/QWeb、父血缘核对。finally ROLLBACK/CLOSE，私有记录关闭时间。
2. 该实时快照离线25资格全PASS后，独立postgres maintenance连接autocommit/IDLE，SELECT目标名/模板连接/cluster，通过后仅一次CREATE DATABASE新库WITH TEMPLATE W5；核新唯一OID，不杀连接、不改源、不重试。复制独立filestore152份/manifest全等，冻结新config/dbfilter/data_dir/marker，源连接已关闭。
3. 目标前验只读连接#1读取初始643表，必须与刚才源前验全行相等才启动HTTP。此同一物理目标连接保留到Web结束，用于每步HTTP门禁；每次快照完成即ROLLBACK，下一门禁重新BEGIN严格只读RR，不复用旧事务快照、不为每个action多开连接。
4. 一次原生Odoo HTTP + 一次原生Firefox，一个context本人user7登录，直接redirect既存doc1；原生Open按钮acquire一次，立即原生Confirm按钮confirm一次，原生JS自动release一次和返回GET。下一POST转发前，用同一目标只读连接比较前一步真实提交全643表、响应、scope/CSRF/Origin/cookie、editor/connection和白名单。原生HTTP来自真实Firefox，不用Python构造业务请求、不注入fetch、不改JS/计时器。
5. 关闭目标前验连接，精确停止自有HTTP PID并保退出码；目标后验连接#2新快照全643表/filestore和全部逐字段白名单、旧版本全行不变；ROLLBACK/CLOSE。之后才第二条独立W5源后验连接#2，严格READ ONLY/REPEATABLE READ新快照，源全部643表/47/31/附件/marker/config/filestore逐项与真实源前验全等；ROLLBACK/CLOSE。不以clone after或旧事务代源后验，不加第三条连接。Web失败/STOP也在安全可访问时做该一次源后验，失败如实BLOCKED。

SQL全部已冻结在机器计划（包括643条完全展开SELECT和固定列catalog）；允许模板字面值及参数范围如下：

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
SELECT to_jsonb(t)::text FROM public.{} t ORDER BY {}仅将冻结643表名作为sql.Identifier，id存在用Identifier(id)，否则to_jsonb(t)::text；运行时catalog必须与冻结列全等。动态参数仅目标库名/W5固定名；无SELECT FOR UPDATE/advisory/业务UPDATE/DELETE/INSERT。maintenance仅唯一上述CREATE，W5事务无DDL/DML。完整展开SELECT列表SHA256=6aa6284fc7f37b4332a4fd05fd79b076ddcd360a766d54b7c9a2ca945443f94c.

25项当前资格（尚NOT_RUN，逐项从第一源快照验证，任一失败CREATE前STOP）：
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

固定业务身份doc1/patient1/store1/company1、pending/v2、author/responsible7；existing execution1 handover/旧lease inactive，无残留editor、无本人serving/verify。user7 active/internal/allowed company1/member5/employee3 active/medical-write/当前caps含1及原snapshot资格；QWeb实际安装与源码/zh_CN/DOM一致。source→fee真实外键1→4/20、2→3/40、3→2/80、4→1/600，invoice1 posted/paid740/residual0、历史payment500/240和partial1/2签名全部锁定。完整TEXT_FIELDS+teeth只从当前源快照安全保存在权限700目录，真实DOM与confirm全量内容逐字等值，无填空/医学推断/文本input事件。凭据只复用既存合成doctor身份，离线PBKDF2核对当前hash，不改账号/授权。

原生合同：GET /web/login?redirect=/ydental/clinical%3Fdocument_id%3D1，POST /web/login≤1；直接GET /ydental/clinical?document_id=1（共≤2）；POST /ydental/clinical/action仅acquire/confirm/release各1，revision1、native sessionStorage connection 32—128字母数字、本人SID绑定、CSRF/Origin/cookie严格核；confirm expected_version2/new UUID/完整原文，响应accepted/confirmed/version3；唯一新增kind=confirm/version3/previous2/author7，原v1/v2及作者全行保留，释放后editor全空。默认store1/revision1不符就STOP，本实现显式switch0（较授权≤1更严格）。GET仅正常login、既存5个assets URL、两份原生clinical静态文件、zh_CN website.translations；无其它业务页/PDF/附件/新资产写。

逐表逐字段白名单（未列627表全部原行SHA不变，完整列表已在机器计划locked_tables冻结，含所有account move/line/payment/partial、settlement source/receipt/refund/close、全部price/snapshot/fee/event、S08/S09、stock move/quant/lot、mail、ir_attachment与模块/QWeb）：
- 本人res_users7/res_partner8/hr_employee3/resource_resource3仅write_uid/write_date；hr_version3另仅last_modified_uid/last_modified_date；actor均7，timezone/业务字段零变，其他旧行全等。
- res_users_log仅append1，除id/create_date/write_date外等于旧user7模板，create/write_uid7、create/write_date相等；res_device_log仅append1，除id/session_identifier/user_agent/first_activity/last_activity外等于旧user7模板，user7/IP127.0.0.1/Firefox/revokedFalse，旧行不动；ydental_access_session仅append1，除id/key_hash/create_date/write_date外等于旧user7模板，store1/revision1/create/write_uid7、key_hash绑定native SID前42位且等于新device session_identifier哈希，旧行不动。
- S01审计只append≤8：login1、login.scope1、store.switch1（原生默认scope选择，不是额外switch POST）、clinical.view≤2、edit_acquire/confirm/edit_release各1；actor/create/write7/result accepted/reason空/create_date=write_date/字段schema全等。clinical target doc1/store1/category medical/source clinical_document；confirm before{version2}/after{version3}；login target res.users7/no store/personnel/native_authenticated_login；scope/switch target唯一新session/personnel/authenticated_session或interactive；switch before{store_id:false}/after{store_id:1}；其它before/after空；无editor_invalidated/一切审计可变例外。
- doc1仅7 editor字段+write元数据+state/version/saved_at变化，原内容/author/responsible/execution/template等全等；editor绑定本人新session/revision1/同connection及acquire editor_token哈希/600秒有效期，confirm后仍持有，release清空。仅新增1个version3，字段及digest严格绑定原content/new UUID/kind confirm/previous2/author7/store1/patient1，旧v1/v2全行不变。
- patient/supply/intake/queue四mutex各仅既有单行ydental_revision，每个实际action恰+1、最多+3，其他字段不变；orm_signaling_default只append≤3且exact id/date字段，旧行全等；不放开其他表/附件/filestore/mail。

真实JS heartbeat2秒/timeout600秒保持。原生新context无holder/editor，acquire后立即Confirm，Confirm设置saving=true期间原生timer自己return，自动release后token=null。路由门禁只验证并continue，任何观察到heartbeat先阻止转发并STOP/记录，绝不屏蔽计时器或伪造响应；禁heartbeat能否实际满足仍由唯一有界Web实证决定。每个403/409/未知/超时/掉线/pageerror/异常额外请求/版本或副作用不符立即STOP，不换key重试、不回滚已发生事实、不执行额外业务。旧原生SIGSEGV若再现立即停止业务并保全。

全部脚本冻结SHA256：
- scripts/s10_p0_13_audit.py: 5a9d3c0869a0d53f5883561ebcaf28d79234a9db42ea16c3bdd12b8b03837f15
- scripts/s10_p0_13_browser.py: ffaee0487aee5650703f8dec5c37a3cbd02238f84b77815194ce265ddf11a597
- scripts/s10_p0_13_control.py: c6e3f631cf3084ae94aca4626c99d2382d4af5809f71f3c195e8c81c1f65a1e5
- scripts/s10_p0_13_eligibility.py: 21cb4f21786e6f00a9b331aa184091fc612b3adf018a902cc2741ade6f623c25
- scripts/s10_p0_13_preflight.py: 313942575cbeb82e82c3d90aebffd282e4dfde2a9686ab67d5dbdcf63a7d8559

完整机器计划 docs/evidence/s10-p0-13/execution-preflight.json SHA256=f3d5a71344b214ff53cd96d0c2d35891f3ad6c285e2a425fa63d3ba96c6a224d，包含逐SQL、643展开SELECT、627锁定表、逐字段规则、全部静态/历史/凭据输入依赖SHA与真实argv。
HTTP argv=["/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python", "/home/redxin/code/odoo/odoo-sd/code/odoo-bin", "-c", "/home/redxin/code/odoo/odoo-sd/code/sd-addons/.local/ydental_s10_test_20261016_p013_6a91d3c8/odoo.conf"]；执行argv=["/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python", "/home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s10_p0_13_control.py"]。Firefox由同一控制器进程调用现有Playwright pw.firefox.launch(headless=True)，单context/zh-CN/UTC/1440x1100，DEBUG原始launch PID及engine exit/signal日志保留；不另起Odoo shell/upgrade/install/init/test。既有进程内network guard仅复制到新运行目录，不修改系统/PG/Docker/防火墙。执行者sudo/直接ORM0；既有未改的原生服务内部受控fixed-model sudo不是执行者提权。

最高预算={"ACQUIRE": 1, "CLINICAL_GET": 2, "CONFIRM": 1, "CREATE": 1, "DIRECT_BUSINESS_ORM": 0, "FIREFOX_LAUNCH": 1, "FUNDS_STOCK_WRITE": 0, "HEARTBEAT": 0, "HISTORICAL_REPLAY": 0, "MAINTENANCE_CONNECTION": 1, "NATIVE_LOGIN_POST": 1, "ODOO_HTTP_LAUNCH": 1, "ODOO_SHELL_UPGRADE_INSTALL_INIT_TEST": 0, "OTHER_BUSINESS_POST": 0, "PDF": 0, "RELEASE": 1, "SOURCE_AFTER_CONNECTION": 1, "SOURCE_BEFORE_CONNECTION": 1, "STORE_SWITCH_POST": 0, "SUDO": 0, "TARGET_AFTER_CONNECTION": 1, "TARGET_BEFORE_CONNECTION": 1, "W5_CONNECTION_TOTAL": 2}。
旧refund14/close9/权限负向/refund13分页与店3/W5收500+240/任何历史临床动作全部不重放，原版PDF备选未授权。原始医疗全文/凭据/cookie/CSRF/session/connection/editor/key/真实截图/HTTP只保私有700，GitHub只ID/状态/金额/哈希/白名单结果。只新增本批允许scripts/docs/evidence，不改AGENTS/旧证据/产品/ACL/core/Issue/Project，无合并强推部署/S11。S10整阶段技术/生产/T12 BLOCKED，Native SIGSEGV UNKNOWN/W4 STOP/W5旧browser exit1/final_audit NOT_RUN/同源原版PDF不足保留。成功或BLOCKED均正常线性固定提交推送，在#34唯一交付回执REST GET逐字读回后立即STOP等待GPT；不自评GPT PASS。
