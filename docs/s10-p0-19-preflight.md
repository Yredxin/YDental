[CODEX] S10-P0-19 继承投影与失败取证修正、原生账单UI及当前PDF有界实测预检

唯一授权6228355422；P0-18裁定6228320925维持既成BLOCKED，不重判、不重跑旧窗口。唯一仓库Yredxin/YDental，目录/home/redxin/code/odoo/odoo-sd/code/sd-addons，原分支codex/s10-settlement-finance-r1-20261013。唯一父/执行HEAD 432c06f1b3529eafd7f7610475cb11c9ea834b3c，core只读f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb。产品仍为P0-17版本，本批只新增scripts/s10_p0_19_*.py、docs/s10-p0-19-*.md和docs/evidence/s10-p0-19/*。

开工完整读取#23正文/3评论、#34正文/244评论、#35 OPEN/0，保存所有完整正文及逐评论SHA。旧241条#34评论逐字相同，仅新增P0-18交付/裁定及本授权；本批只有唯一授权，没有已有预检/交付或并行任务。origin、branch、本地/远端HEAD及旧文件工作树核验一致。发表前再次完整读取#34仍244、远端HEAD不变。P0-18全部23项SHA/字节数/固定Git内容及索引自身已核对；索引SHA e9f33c2fdc54d8fb3ae265fcf05a0c5023075fe1fe53f02746dc0bfa79c8fbc4、固定blob9430b1ed99a75dc2ce48472155ad93c294501fb0。没有运行P0-18或P0-17旧测试/业务。

本预检REST逐字读回前，所有数据库/CREATE/Odoo/Firefox/HTTP/登录/PDF实际预算均0。下述冻结门禁成功后，按本授权同批继续；实际失败或未知即STOP，绝不修改冻结合同重试。

一、两个验证修正及实际纯文件正反例
固定core base_data.sql:5–13、ir_actions.py:54–60/90–103/424–435证明ir_act_url继承ir_actions。原643表查询及签名完整保留，包括不带ONLY的ir_actions；没有删除父表检查。
新增完整继承族的tableoid→pg_class/namespace物理来源映射，稳定键(schema,physical_table,id)，来源OID和共享字段也保存。仅ID的dict不用于父表；普通非继承表的ID映射也显式拒绝重复键。允许同号异表存在而各自不变，重复物理键拒绝，不覆盖。原父表逻辑行多重集必须与完整物理投影一致，所有child与parent全部共享字段一致，ONLY父表自身行另核但不替代族核验。
新增许可仅public/ir_act_url/571在ir_actions的同一物理投影：child先通过原字段门禁，parent全部共享字段与child一致后，只能同一write_uid/write_date技术变化。其他action/子表、ONLY自身、URL/name/type/path/binding/target等全部不放宽。

使用新实际metadata_gate及guarded_import完成33项纯文件检查exit0，包含合法child+parent技术变化、parent/child不一致、同ID异表保留及其变化拒绝、重复物理键/普通表重复ID、其他action、URL/name/type、额外view/XMLID/语言/模块/权限/金额、ONLY自身、提交后精确信号与超额拒绝。实际共享事务函数用纯文件ledger测试成功、门禁拒绝、load/capture失败、证据落盘失败、commit未知：先保存证据，只有PASS才允许唯一commit；异常rollback/close，无成功marker。fixture含完整571条历史action继承族、父/子及选定真实metadata，fixture tableoid101..105明确为静态身份，不冒称实测SQL。假cursor.commit计数不是原生commit，所有运行预算0。
docs/evidence/s10-p0-19/offline-result.json及transaction-fixture-results.json保留结果，后者SHA 9525f09e0203ee44053128c7b3c9e06e3c8ed1178f56c3b806253141d91a25e8。

加载器在门禁之前fsync保存完整私有before/after、全行/列diff和精确来源映射，再fsync脱敏全变化索引并读回。索引保留所有变化行、列、前后SHA及同号/重复分组；不会因重复键导致取证先失败。只有证据已保存并PASS才写唯一commit intent并commit。捕获/保存失败如实不可得，不猜字段、不commit。异常保存错误状态并rollback/close；不再导入补证。独立提交后门禁使用同一比较器，另仅准default/templates各1条id/date信号。

二、冻结对象、脚本与SQL
执行冻结 docs/evidence/s10-p0-19/execution-freeze.json SHA256：
b916b620023321b7b74dcddd176d71a14e25f7a44d7a69e1ea5ec82e60300be0
SQL/643表逐列及继承族三语句：docs/evidence/s10-p0-19/sql-contract.json SHA256 78969e6a876dfa575db767676776f0b6eaa021bc0e955c08cde1a770829d6304。
五记录原值/预期转换结构、物理表/父投影/关系表影响清单：docs/evidence/s10-p0-19/metadata-contract.json SHA256 a123eb53bcc5e2b193b4560638a977ffbc699480e3d04d297124a35950817f0d。
脚本SHA256：
- s10_p0_19_contract.py dac2bd4c72b2ad5779b794c488674444d8b1f01de12c6668329eaa6196dac55e
- s10_p0_19_metadata.py 966c97841f9b7011a59670b5fb6c8596b38fc37c7d232f59e3ca014bbcfb13db
- s10_p0_19_control.py 9fb6c0b40841034e661d4b5051172afc5afacddd92053b6f36ad93f6487ab0b4
- s10_p0_19_browser.py 08426ffd6f5281c7bd26c5eee3d7652c124fbc9c88907667a6f97bc942353577
- s10_p0_19_preflight.py eaba0b482f08a223ab527f9e04131a54ee052205d0e3001f537df4200122421c
冻结含实际产品/core/依赖和历史源快照SHA；旧P0-18字节不改。

每次保留原643条SELECT to_jsonb(t)::text FROM public."<table>" t ORDER BY "id"（无ID时ORDER BY to_jsonb(t)::text）；原catalog逐列相同。新加仅以下3条只读SQL：
1. WITH RECURSIVE edges AS (SELECT inhparent,inhrelid,1 AS depth FROM pg_inherits WHERE inhparent='public.ir_actions'::regclass UNION ALL SELECT i.inhparent,i.inhrelid,e.depth+1 FROM pg_inherits i JOIN edges e ON i.inhparent=e.inhrelid) SELECT pn.nspname,p.relname,cn.nspname,ch.relname,e.depth FROM edges e JOIN pg_class p ON p.oid=e.inhparent JOIN pg_namespace pn ON pn.oid=p.relnamespace JOIN pg_class ch ON ch.oid=e.inhrelid JOIN pg_namespace cn ON cn.oid=ch.relnamespace ORDER BY pn.nspname,p.relname,cn.nspname,ch.relname,e.depth
2. SELECT n.nspname,c.relname,c.oid,p.id,to_jsonb(p)::text FROM public.ir_actions p JOIN pg_class c ON c.oid=p.tableoid JOIN pg_namespace n ON n.oid=c.relnamespace ORDER BY n.nspname,c.relname,p.id,to_jsonb(p)::text
3. SELECT n.nspname,c.relname,c.oid,p.id,to_jsonb(p)::text FROM ONLY public.ir_actions p JOIN pg_class c ON c.oid=p.tableoid JOIN pg_namespace n ON n.oid=c.relnamespace ORDER BY n.nspname,c.relname,p.id,to_jsonb(p)::text
预期5个public直接继承边：ir_actions→ir_act_client/ir_act_report_xml/ir_act_server/ir_act_url/ir_act_window，depth1、无其他后代；历史完整family571行、ONLY自身0行，在本批实时源快照核实。历史源仅为比较依据，不冒称新测量。
源每连接显式SQL最多651，副本每连接650；native显式快照SELECT648，原生加载/ORM内部语句另计native连接。只读连接首两条SHOW确认READ ONLY/on和REPEATABLE READ，rollback/close；快照150秒/statement15秒/lock3秒。原生连接同时用PGOPTIONS限定statement15秒/lock3秒/idle15秒/UTC，不改PG系统配置或驱动。

三、身份、复制、进程与五对象字段门禁
唯一源ydental_s10_test_20261015073500_e50f4a71/OID2100310/cluster7694897083368259627；源config SHA867f761771ecc20931f69103388df699b094b748e6a9d392e15ebe3d406e43c7，marker SHA1a7f4a2a95e8aa0ea3d6da17abf6033976d2e39754185fa38e441a497351a5fa，152文件manifest bd0b0fbad15868bbabb836fa7016a91187bb31c6b9b6d934b2a7a0fe035c4283。源前/最终后各1独立READ ONLY/RR，首测与P0-18 source-after的643签名核对、末测与本批前643及完整action来源映射核对；活动连接/身份/漂移即STOP，不强断、不改grant。源前必须rollback/close后才可CREATE。

新唯一名ydental_s10_p019_20261017021844_64f8a46b，独立目录.local/ydental_s10_p019_20261017021844_64f8a46b，HTTP127.0.0.1:18319；名称为本批冻结UTC标签，实际创建时间另记。建库前目录/名称不存在，端口可绑定。维护连接1、autocommit/IDLE，catalog完整旧OID、cluster和源活动连接核验，唯一CREATE：
CREATE DATABASE "ydental_s10_p019_20261017021844_64f8a46b" WITH TEMPLATE "ydental_s10_test_20261015073500_e50f4a71"
取得新OID须不在全部旧catalog，绑定一次性marker；仅copy2复制到独立filestore，不硬链接/共享回写，不DROP/覆盖。P0-13/OID2100325、P0-14/OID2100326、P0-18/OID2100327不连接/复用/清理。

副本独立只读连接最多3：加载前、提交后且Web前、最终或停止尾审。初始643表+完整action映射须与本批源全等，保存完整差异后裁决。所有原经济/临床/授权/旧附件及152文件前后不变。
准确命令前缀为/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python：
scripts/s10_p0_19_control.py；其只启动一次scripts/s10_p0_19_metadata.py、一次../odoo-bin -c <新目录>/odoo.conf、一次scripts/s10_p0_19_browser.py。加载120秒、Web就绪60秒、browser150秒。config精确db_name/dbfilter新名、独立data_dir、workers0/max_cron_threads0/list_db=False/db_maxconn4。原生metadata/Web各最多4物理连接，原生odoo.sql_db.connection backend-create日志计数；仅停止本批精确进程，不做系统专项。

固定core convert.py:692–722真实API；显式idref={}，仅一次convert_file(env,'ydental_settlement','views/ydental_settlement_templates.xml',idref,mode='update',noupdate=False)。专用元数据env uid1仅用于授权导入；无执行者sudo、业务ORM、shell、-u/full upgrade/install/init/test、SQL写arch、DOM注入或自定义猴子补丁。
5个原XMLID严格module ydental_settlement、noupdateFalse、映射不变：action51384→ir.actions.act_url571；menu51385→ir.ui.menu320；tokens51386→view1597；page_links51387→view1598；page51388→view1599。
view仅arch_db/arch_prev/arch_fs/arch_updated/write_uid/write_date；tokens原语言en_US，page_links/page原en_US+zh_CN，严格保留键；新arch逐语言等固定XML转换结构，主view仅P0-17增量、helper结构不变；arch_prev=旧en_US架构，arch_fs=固定XML路径，arch_updated=False，actor1。action/menu/5 XMLID只准write_uid/write_date；ir_act_url571父投影按第一节独立核验，不豁免其他行。ir_ui_menu_group_rel、ir_ui_view_group_rel及其它关系/字段/业务含义、schema/module state/version、report action570/template1596、ACL/grant全等。postcommit仅orm_signaling_default/templates各≤1 id/date。

四、原生UI、当前PDF及非经济副作用
已重新核当前服务/controller/QWeb/report/auth/session/device/assets固定源码，保留settlement read+export write最终鉴权和当前membership can_export；不是盲抄旧窗口执行结论。
一个Firefox上下文，原生login GET1/POST1，使用既有user5私有合成凭据（已离线与历史hash核对，不改密码）；默认store1/revision1，否则STOP，手工切店POST0。工作台GET2：计入登录303 redirect后的默认页1，真实patient1筛选表单1；请求事件、响应及server日志独立完整计数核对，不漏redirect。只看现有1条账单，不造51张，不称实际多页PASS。
验证invoice1不在未结清勾选表，确在settled只读区、store1/company1、总740/余额0、患者来源合法；真实可见链接标签“下载当前内部账单 PDF”，href现有/ydental/settlement/pdf/bill/1。仅从页面点击一次，PDF GET/render/download各1；未知或失败不点击第二次，不能goto PDF/直接HTTP/注入按钮/改余额。
保存真实截图、请求/状态、下载字节/SHA，必须%PDF≤10MB/20页、字节SHA=响应X-YDental-PDF-SHA256=report_download审计SHA；既有PyMuPDF解析中文并栅格全部页，再逐页实际查看。公司/门店/740实收/余额0及20+40+80+600费源、内部演示/非税票/非自动到账声明必须核对；500+240仅原记录核销，不重收；不是历史原版重印。
原资源仅既有源/web/assets/URL无query最多100 GET，translations?hash=&lang=zh_CN最多1；wkhtml资源GET0，未知路由/网络失败/状态/pageerror/crash立即STOP。除此以外的业务GET/POST预算0。
新增S01精确6条：login1（user5/no-store/personnel/native_authenticated_login）、login.scope1（新session/no-store/personnel/authenticated_session）、store.switch1（新session/store1/personnel/interactive，false→1）、settlement.invoice_view2（account.move1/store1/settlement/confirmed_offline_transaction）、settlement.report_download1（同目标，after kind=bill/pdf_sha256）。actor/create/write5，accepted、reason空、事务时间匹配；旧审计行全等，其他新审计0。
原生登录日志append1 uid5，device append1（SID前缀/Firefox/127.0.0.1、无geo/revoked、原生SQL技术列null），session append1 uid5/store1/revision1/create/write5，SID hash一致。仅res_users5/res_partner6/hr_employee1/resource_resource1的write_uid5/write_date，hr_version1另last_modified_uid5/date；旧身份/公司/员工/授权/会话不改；Web orm_signaling_default最多1 id/date。
技术assets附件append≤5，仅源既有basename frontend_minimal/lazy min.js(application/javascript)、frontend min.css(text/css)、odoo_ui_icons/material_symbols_outlined min.woff2(font/woff2)；URL/web/assets/、ir.attachment actor1/public/binary/res_model ir.ui.view/res_id0、≤5MB、store_fname/checksum真实，res_field/access_token/original_id/description/db_datas空；旧附件/152文件全等，新增文件仅对应允许技术asset，不含患者或报告附件。report_pdf_no_attachment=True保持，不临时扩请求白名单。

五、停止、保全与交付
经济/临床/库存/权限业务写、旧业务重放全部0。643表与实际继承族继续核验：原生account.move/line/payment/partial.reconcile、source/fee/price/payment/refund/close、文书/version、stock move/quant/lot、权限/旧附件全部原事实不变。禁止旧500+240、refund14、close9及权限负向、refund13专门分页、旧doc确认，不连接保护副本，不改产品/core/旧证据，不sudo，不做OS/PG/Docker/防火墙/IPv6专项，不合并部署或启P0-20/S11。
实际门禁失败或未知立即停止，先保留完整before/after/私有全差异及脱敏全索引/拒绝原因；捕获或落盘失败如实不可得，不猜字段，不commit，不第二次CREATE/import/login/click，不换库绕过。只在剩余预算只读尾审并停本批进程，封存副本，不清理或复用。
正常原分支线性提交新增脚本/报告/证据，全部SHA、继承正反例、原生全差异、预算、UI/PDF/经济核对与NOT_RUN如实交付；检查.log实际入Git，密码/cookie/原始快照不上传，截图/PDF先核合成与脱敏。在#34正式交付或BLOCKED回执REST GET逐字读回保存后立即STOP等GPT。最高仅申请S10_P0_19_PAID_BILL_NATIVE_UI_CURRENT_PDF_SCOPED_TECH_PASS；P0-18旧裁定不变，S10技术/生产/T12持续BLOCKED，#34 OPEN/#35未启，原Native UNKNOWN/W4 STOP/旧W5失败、历史原版PDF及生产政策缺口保留。