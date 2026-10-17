[CODEX] S10-P0-17 已结清本店账单只读工作台与当前PDF入口CODE_ONLY预检

唯一有效授权6215375331；P0-16正式裁定6215317877直接引用，不重新审查或重跑。Yredxin/YDental，原分支codex/s10-settlement-finance-r1-20261013，唯一父HEAD 21dc2dc243200336959482fcfa9d3b5f5f5ad271；core f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb只读未改。开工API完整读取#23正文/3有效评论、#34正文/236有效评论、#35 OPEN/0及REST工作分支ref；origin/branch/本地与远端HEAD吻合，工作树没有未归属修改。本批唯一P0-17评论仍是正式授权，无既存Codex预检/交付；旧#34前232条全文与上批完整读取相同，新增4条含上批预检/交付/裁定与本授权，不是重复复核P0-16。

当前三份产品源码仍与父提交逐字相同，尚未修改；必须本评论REST GET body逐字读回，保存ID/URL/字符/UTF8字节/SHA后才能改动。

原源码SHA256：
ydental_settlement/models/ydental_settlement_service.py 1ea27012fd5500fc21891f9e652f4e694cb2e7cce844fa38d08b7f12beff8d2c
ydental_settlement/controllers/settlement.py bfa051971585369f1585d311cfc4553159d4a42ef23b3c54f35d77e53ab4caa2
ydental_settlement/views/ydental_settlement_templates.xml 8f74cffa93a3a24f1d4c4f95a2a006fd698050cda8d27a99924de58770feb329

冻结计划：docs/evidence/s10-p0-17/preflight-plan.json SHA256 6bf9510d061c3a342e0908fc8e3ed3f9480d56f6a045c632d7c4b08f23e02b59。它绑定原源码/实际core依赖SHA、最低diff、Domain规则、权限/分页反例矩阵、文件许可和全0预算。domain-api-static.json仅复制固定core相关源码段及路径/行号/SHA，不导入Odoo，不调用Domain SQL编译器。

真实API依据：core odoo/fields/__init__.py:20导出Domain；odoo/orm/domains.py:81–101、207–224、318–339支持any/not any、三参数构造、&和~；odoo/orm/fields_relational.py:847–889使用同一env的comodel存在/不存在量词，odoo/orm/models.py:1432–1447和4852–4890证明search使用模型环境且现有已鉴权su环境能看全量来源。新查询复用既有invoices的account.move环境，不加sudo，不用any!、原始SQL或动态模型兜底；来源模型无active字段隐藏混店行。合法来源字段及inverse关系取本仓真实模型，未确认API不臆造。

最低产品增量只限：
1. service::_workbench：原invoices仍严格未清余额>0，原域/顺序/支付/免单/勾选/其它列表均保持。新增settled页码/列表/count：posted、out_invoice、paid、residual=0、当前公司。要求EXISTS合格源且NOT EXISTS不合格源；合格源为当前店真实fee，fee和event属于当前店、event confirmed；筛选patient时沿原_patient/_current_relation/_patient_family_ids，只允许source/fee/event患者都在合法family。排除公司/门店/同公司混源及混患者来源，不靠“有一条本店源”放行。沿用_workbench_page每页50、invoice_date asc,id asc稳定排序；每条展示记录只调用既有S01 settlement.invoice_view审计，不写账款。
2. controller::workbench：只新增settled_page与raw_pages/context链；新页码必须decimal字符串1–5字符、整数1..10000，先验长度避免巨大数字int转换。原页码/付款反馈/权限行为保留。现有page_url自动保留patient_id及其它分页。can_export仅当前_member/_levels(member)['export']=='write'，无岗位/manager豁免；现有PDF服务端settlement read+export write、当前店和撤权再验完全不改。
3. QWeb：只追加name=settled-bills独立“已结清本店账单”只读段，ID/原生号/日期/总额/余额、空态、50条分页；下一页不超过10000，保留患者筛选。无form/勾选/付款操作，仅can_export为真显示现有/ydental/settlement/pdf/bill/<invoice.id>链接，准确用语“下载当前内部账单 PDF”。原未结清表和全部旧QWeb结构不动，不称历史原版重印或税票/渠道到账证明。

静态纯文件回归矩阵：Python AST及内存compile、XML解析和变量链；从实际新增域表达式提取到独立符号谓词，用纯合成字典反例核company/store/同公司混源/不存在或外店fee/未确认事件/患者与family混源；仅对纯标量guard和page_url作隔离fixture求值。不会执行Odoo模型、service/controller完整方法、原生Domain/ORM/HTTP/QWeb引擎。核缺settlement read、export缺失/只读、manager不豁免、错误session owner/store/revision、在职/患者关系缺失及撤权旧页的下一请求门禁；非法类型/0/负数/10001/巨长页码、50/50/5稳定分页/无重叠/重复页、筛选与其它页码保留、10000页nav上限。通过删除负量词的变异反例证明混源断言有辨别力。

原流程保全：所有service方法除_workbench、controller方法除workbench逐字不变，尤其_workbench_page、_invoice、_report_payload、_pdf、PDF controller、收退/日结/库存；将新增AST节点剥离后与旧_workbench全树比较，剥离新section后旧QWeb全结构比较；所有非许可旧tracked文件/core SHA原样。新增代码本身不增加sudo调用或业务write。

Git仅可改这3份既有产品文件，额外仅新增scripts/s10_p0_17_*.py、docs/s10-p0-17-*.md、docs/evidence/s10-p0-17/*；不改ACL/schema/其它产品/AGENTS/历史报告证据、Issue/Project正文状态。真实API、同源隔离或权限无法安全证明即BLOCKED，不放宽。

绝对执行预算及当前实际全部0：任何新旧数据库/maintenance连接、CREATE、Odoo HTTP/Firefox、业务GET/POST、PDF生成、直接ORM、Odoo shell/install/upgrade/init/test、执行者sudo、OS/PG/Docker/网络安全专项。W5及P0-13/14保护库不连接或复用；不重放500+240、退款14、日结9/负向、退款13分页、旧文书确认；不查看私有病历/凭据/HTTP/截图，不合并部署，不启P0-18/S11。

交付将固定源码位置、逐文件diff/SHA、实际静态检查与退出码、NOT_RUN清单、5–10步预期用户效果和未执行的安装/回滚边界。新已结清列表未来运行可新增invoice_view审计，但本批没有实际审计/账款写；代码未同步到任何已安装页面。未来若需安装QWeb，须新授权及新的独立合成数据库/metadata白名单，不碰W5或W4旧STOP。正常线性提交推送后发表正式交付或BLOCKED，REST逐字读回并保存立即STOP等GPT。

最高仅申请S10_P0_17_PAID_BILL_WORKBENCH_CODE_STATIC_TECH_ACCEPTED，不宣称已安装页面可点击、真实PDF/原版重印通过、T11/F4/T08/T12或整个S10 PASS。S10技术/生产和T12仍BLOCKED，R3 SIGSEGV UNKNOWN、W4 metadata STOP、W5旧browser exit1/final_audit NOT_RUN、历史原版/财税到账政策缺口保留。
