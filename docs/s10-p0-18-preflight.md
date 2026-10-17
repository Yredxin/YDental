[CODEX] S10-P0-18 新隔离副本原生账单UI与当前PDF有界实测预检

唯一授权6227951775；P0-17裁定6227904194已完成，不复核或重跑。仓库Yredxin/YDental，目录/home/redxin/code/odoo/odoo-sd/code/sd-addons，原分支codex/s10-settlement-finance-r1-20261013；唯一父/执行产品HEAD 68c9096246464f9ab1c3ec9c014fe7dc1be6d04b，core只读f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb。开工完整读取#23正文/3评论、#34正文/240评论、#35 OPEN/0；全部237条已读旧评论逐字相同，新增为P0-17交付/裁定与本授权，无P0-18预检/交付或并行任务。origin、远端ref、本地分支/HEAD和干净旧文件工作树匹配。再次完整获取#34仍240、远端HEAD不变。

本批仅新增 scripts/s10_p0_18_*.py、docs/s10-p0-18-*.md、docs/evidence/s10-p0-18/*，不改产品/ACL/core/旧报告证据/Issue或Project正文状态。本预检发表和REST逐字读回前，数据库连接/CREATE/Odoo加载/Firefox/HTTP/业务GET POST/PDF实际全部0。

一、纯文件门禁及冻结对象
已逐项核对P0-17索引全部18份SHA256/字节数/固定Git文件；索引SHA256 e1082ddc013e0708363791d6a88ecc8e19cab9e2c2db8c115e4783c8dd1f3598，固定blob 11becf8361bf8e38096e6c4e51398afd35838adb。未运行其3954项旧检查。
固定core convert.py:692–722明确convert_file(env,module,filename,idref,mode='update',...)，491–569为template转换，296–355为menu转换；ir_ui_view.py:262–275/656–681/2677–2697为arch inverse/历史arch/加载；ir_model.py:2446–2525为既有XMLID维护；orm/registry.py:1132–1150为原生cache信号；sql_db.py:659–715提供原生新连接backend PID日志。仅原生元数据环境uid1，禁止执行者sudo或业务ORM。
现有W5保存的主view结构严格等于固定产品去除P0-17 settled-bills；没有其他历史产品缺口需要顺带同步。真实语言键：tokens仅en_US，page_links和page均en_US+zh_CN；不扩语言。原始两次纯文件预检exit1（误假定helper语言、负向fixture写入原已存在write_uid值）均记录，修正纯文件断言后最终14检查exit0，含精确metadata正例及余额/授权/其它view/menu action/module/XMLID/旧主arch/语言越界反例；所有运行预算仍0。

最终执行冻结 docs/evidence/s10-p0-18/execution-freeze.json SHA256：
0887efa9ab7f009644e02e057a2f6fc9ec60841b709982c673da728c4ceea0a5
完整SQL/643表逐列及字面语句：docs/evidence/s10-p0-18/sql-contract.json，SHA256 723a27d87bf3a00c87544d98bb6b7de02d9ab530b3c73479a6c5c77ed1541c09。
五记录原始全部字段、XMLID及转换后结构：docs/evidence/s10-p0-18/metadata-contract.json，SHA256 4fd82604d0ccbc466042bde0b78eac6d12be039353d1a974cbf2393dbc92aa26。
脚本SHA256：
- s10_p0_18_contract.py dd1115ae12c60b2b98e98471418fc4d68d54e9860a9ca63ecaef89109aacb40f
- s10_p0_18_control.py b53e0e1e89937e623ad433ac98bb2a4b141165e800a17505228c94c361de2b8a
- s10_p0_18_metadata.py 5d05f69cbe338b7780932cd4af5e3849b2eb26ff7d833ccbf230c905fac90614
- s10_p0_18_browser.py 032333e1b9117b95bd7551decccd618280252d3fdae2315c4ccb1ad27092bd22
- s10_p0_18_preflight.py 1e2bd8eef65d7dda63c2b61d78854f1faf6fbd322ab39fa377e336c7d76297d6
冻结也含全部实际产品/core/私有既有工具及合成凭据来源文件SHA。脚本不再改变；私有原始行、密码、cookie不上传。

二、来源、SQL、复制及进程的准确合同
唯一源ydental_s10_test_20261015073500_e50f4a71/OID2100310/cluster7694897083368259627；config SHA867f761771ecc20931f69103388df699b094b748e6a9d392e15ebe3d406e43c7，marker SHA1a7f4a2a95e8aa0ea3d6da17abf6033976d2e39754185fa38e441a497351a5fa，152文件manifest bd0b0fbad15868bbabb836fa7016a91187bb31c6b9b6d934b2a7a0fe035c4283。
新唯一名称ydental_s10_p018_20261017020000_8e21bc49；独立目录.local/ydental_s10_p018_20261017020000_8e21bc49，HTTP127.0.0.1:18318，dbfilter精确此名、独立data_dir、workers0/max_cron_threads0/list_db=False/db_maxconn4。建库前名称和目录不存在、端口可绑定；一次CREATE结果新OID须不同于维护catalog全部旧OID，写一次不可变marker。filestore使用copy2复制，绝不硬链接/共享回写；旧152文件始终核对保留，新文件仅可对应下述技术assets。
连接端点固定127.0.0.1:5432/odoo，凭据仅原机既有私有配置。源前1连接先SHOW transaction_read_only/on、SHOW transaction_isolation/repeatable read，identity/其他活动连接/catalog/643表；与P0-16已封存来源签名严格全等，不重跑资格批次。ROLLBACK/CLOSE成功后才能维护连接/CREATE。源活动连接或漂移即STOP。
唯一维护连接autocommit/IDLE：SELECT oid,datname FROM pg_database ORDER BY oid；SELECT system_identifier::text FROM pg_control_system()；SELECT pid FROM pg_stat_activity WHERE datname=%s；仅一次CREATE DATABASE "ydental_s10_p018_20261017020000_8e21bc49" WITH TEMPLATE "ydental_s10_test_20261015073500_e50f4a71"；SELECT oid FROM pg_database WHERE datname=%s；CLOSE。
副本独立只读连接最多3：加载前、加载后且Web前、浏览器结束/服务停止后的尾审。每次READ ONLY/REPEATABLE READ/ROLLBACK/CLOSE；初始643表须与源完全相等。源最终后另1只读连接独立确认643表与本批前全等并重核文件封存。
冻结查询每表为SELECT to_jsonb(t)::text FROM public."<表名>" t ORDER BY "id"（无id时ORDER BY to_jsonb(t)::text）；完整643条及catalog列名单已冻结，不执行DML；源每次最多648条显式SQL，副本每次647条，每快照150秒/statement15秒/lock3秒。原生加载进程内部两次同事务643表检查单独计入native连接，不混为独立审计连接。
准确命令（前缀均/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python）：
scripts/s10_p0_18_control.py；其只启动一次scripts/s10_p0_18_metadata.py、一次../odoo-bin -c <新目录>/odoo.conf、一次scripts/s10_p0_18_browser.py。元数据进程120秒、Web就绪60秒、浏览器150秒。原生连接使用固定core的odoo.sql_db.connection:DEBUG计数新backend PID，metadata最多4、Web最多4，连接池4；不打驱动补丁、不做系统专项。仅可停止本批精确拥有的进程。

三、五XMLID/逐列白名单与导入提交前门禁
显式idref={}，原生调用且仅一次：
convert_file(env,'ydental_settlement','views/ydental_settlement_templates.xml',idref,mode='update',noupdate=False)
5个既有XMLID严格同module、model、res_id、noupdate=False：
- action：ir.model.data51384 → ir.actions.act_url571
- menu：51385 → ir.ui.menu320
- tokens：51386 → ir.ui.view1597
- page_links：51387 → ir.ui.view1598
- page：51388 → ir.ui.view1599
只准3个view的arch_db、arch_prev、arch_fs、arch_updated、write_uid、write_date变化；arch_db按各自原语言键逐一等于固定转换后结构，主view仅P0-17增量，辅助view业务结构不变；arch_prev严格旧en_US架构，arch_fs严格固定XML路径，arch_updated=False，actor=1。action571/menu320及相应上述5个ir.model.data仅write_uid/write_date技术字段许可，所有其他字段原值不变；XMLID映射、action URL、menu组关系、权限、模型/字段/schema、module state/version、report action/template均原样。允许原生metadata提交产生orm_signaling_default/templates各最多1条id/date，其他信号表不豁免。
先flush并比较全部643表精确差异，越界ROLLBACK/STOP，绝不先提交后放宽；成功唯一COMMIT后还须独立只读复核。禁止-u/update/install/init/test、手改arch SQL、业务ORM、QWeb/DOM注入或自定义猴子补丁。

四、真实Firefox/下载及精确非经济预算
一个Firefox上下文，既有合成user5本人一次原生登录。凭据已离线与保存的合成hash匹配，不改密码。按既有默认店hook得到store1/revision1；本次冻结手工switch POST=0，若默认店不符即STOP，不追加修复登录。原生切店审计仍允许其初始化时的store.switch一次。
请求白名单：GET /web/login?redirect=/ydental/settlement一次；POST /web/login一次（原生csrf/login/password/type/webauthn_response/redirect字段，秘密不记录公开）；登录303重定向后的GET /ydental/settlement一次必须计数；真实patient筛选表单GET /ydental/settlement?patient_id=1一次。工作台共2次，低于授权上限4。现有实际样本1条，不造51张账单，不声称真实多页PASS。
证明invoice1在新settled只读区、740/0、store1/company1，且不在旧未清invoice勾选；患者筛选仍该账单。新段真实可见“下载当前内部账单 PDF”链接且href为现有受控端点，然后仅点击该页面链接一次。PDF GET/渲染/下载各最多1；不得page.goto PDF、直接HTTP、插DOM或改余额。下载未知即STOP无重试。核对%PDF、<=10MB/20页、字节SHA=响应X-YDental-PDF-SHA256，中文文本、公司/门店/740实收/欠0及20+40+80+600费源，500+240只核既存核销不重收。用既有PyMuPDF解析并栅格化全部页，之后实际查看版面；内部演示/非税票/非自动到账声明必须存在，不称历史原版重印。
原生资源：仅源既有/web/assets/URL无query，最多100 GET；/website/translations?hash=&lang=zh_CN最多1；本PDF模板无外部资源，wkhtml业务/资源GET预算0。任何未知路由、错误状态、pageerror/crash或不确定请求STOP，不隐去重定向。
S01新增精确6审计：login1（user5无store/personnel/native_authenticated_login）、login.scope1（新session无store/personnel/authenticated_session）、store.switch1（新session/store1，before false→after1）、settlement.invoice_view2（account.move1/store1/settlement/confirmed_offline_transaction）、settlement.report_download1（同invoice/store/category/source，after kind=bill/pdf_sha256）。全部actor/create/write5、accepted、reason空、create/write时间同事务；旧audit行全等，source_view/pending_event_view/source.view或其他审计0。
登录非经济行：res_users_log新增1 uid5；res_device_log新增1，原生SID前缀/Firefox/127.0.0.1、无geo/revoked、原生SQL技术列null；ydental_access_session新增1 uid5/store1/revision1/create/write5，SID hash匹配device。只准res_users5/res_partner6/hr_employee1/resource_resource1的write_uid5/write_date；hr_version1再允许last_modified_uid5/date。旧身份/公司/员工/grant/会话行不改；Web orm_signaling_default最多1条id/date。
新增assets附件最多5，仅原生/web/assets/既有basename：frontend_minimal/lazy min.js(application/javascript)、frontend min.css(text/css)、odoo_ui_icons/material_symbols_outlined min.woff2(font/woff2)；ir.attachment仅新行、actor1/public/binary/res_model ir.ui.view/res_id0、<=5MB、store_fname/checksum真实匹配，res_field/access_token/original_id/description/db_datas空，其他字段由固定原生create生成；旧附件/旧152文件全等，无患者/报告附件。report_pdf_no_attachment=True不变。新URL不在既有请求白名单也STOP，不临时扩张。

五、不变量、停止和交付
费库款/临床/权限事实预算0，所有643表精确比较：account.move/line/payment/partial.reconcile，YDental source/fee/price/payment/refund/close、文书/version、stock move/quant/lot及授权/业务附件等没有经济列豁免。不得重放500+240、refund14、close9/负向、refund13分页或旧doc确认，不连接/复用P0-13/14；不做OS/PG/Docker/网络安全专项、不sudo、不改产品、不启P0-19/S11、不合并部署。
任何失败立即停止后续动作，不第二次CREATE/import/login/click；只可在余下预算做只读尾审、停止本批进程并封存失败副本。无末次核对不能以页面成功替代。
正常线性提交仅新增脚本/报告/脱敏证据，逐文件SHA、真实预算/metadata差异/页与PDF/经济核对和未运行项目如实报告。真实截图/PDF先核合成及秘密后才可入Git，原始行/凭据/cookie留私有。在#34发表正式交付或BLOCKED回执，REST逐字读回保存后立即STOP等GPT。本批最高仅申请S10_P0_18_PAID_BILL_NATIVE_UI_CURRENT_PDF_SCOPED_TECH_PASS；S10技术/生产/T12仍BLOCKED，R3 UNKNOWN/W4 STOP/旧W5失败和历史原版PDF及生产政策缺口保留。