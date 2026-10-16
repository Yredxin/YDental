# S10-P0-16 W5收费员5及内部账单来源严格只读准入报告

仅申请 `S10_P0_16_W5_USER5_SETTLEMENT_EXPORT_AND_BILL_SOURCE_READONLY_ELIGIBILITY_SCOPED_TECH_ACCEPTED`，由GPT独立复核决定。Codex本机结果 **READONLY_ELIGIBILITY_COMPLETE_PENDING_GPT**；不是PDF/Web业务PASS，不授权下一批。S10技术/生产及T12仍BLOCKED。

唯一授权 [6214616229](https://github.com/Yredxin/YDental/issues/34#issuecomment-6214616229)，上批裁定 [6214578731](https://github.com/Yredxin/YDental/issues/34#issuecomment-6214578731)作为生效历史引用，不重审或改GAP-03。原分支 `codex/s10-settlement-finance-r1-20261013`，固定父 `82a435e90b2aaba6437322700ad2ac0be4e7e328`，core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；最终子提交由交付评论固定。

开工API完整读取#23正文/3评论、#34正文/232有效评论、#35 OPEN/0，远端及本地HEAD一致。旧#34前228条全文与此前完整读取逐字相等，后四条含P0-15预检/交付/新裁定/本次授权；没有已有P0-16预检或并行授权。[逐条正文SHA索引](evidence/s10-p0-16/github-start.json)。正式预检在任何SQL前发表并REST body逐字相等，原文见[预检](s10-p0-16-preflight.md)、[读回/时间与冻结SHA](evidence/s10-p0-16/preflight-api-readback.json)。

本批离线冻结3份执行/分析脚本的SHA、全部643表/列白名单、所有字面SQL与参数、首SHOW顺序、数据身份、权限/报表规则及预算。[execution-freeze.json](evidence/s10-p0-16/execution-freeze.json)和[完整SQL合同](evidence/s10-p0-16/sql-contract.json)固定每一条将执行的SELECT/SHOW；脚本没有导入Odoo或调用旧批入口。仅调用一次psycopg2.connect；先READ ONLY/REPEATABLE READ，再SHOW on/repeatable read，首业务SELECT前门禁生效；无行锁/advisory/DML/DDL/ORM。只读连接实际 1，语句 674，耗时1.052秒，rollback=True、closed=True；[逐语句证据](evidence/s10-p0-16/statement-trace.json)。失败原因 `无`，无重试。

## 来源与643表

W5 `ydental_s10_test_20261015073500_e50f4a71` / OID2100310 / cluster7694897083368259627；config SHA `867f761771ecc20931f69103388df699b094b748e6a9d392e15ebe3d406e43c7`、marker SHA `1a7f4a2a95e8aa0ea3d6da17abf6033976d2e39754185fa38e441a497351a5fa`。文件封存152份manifest和164附件指针、92已安装模块与固定源后证据比较；具体检查成功/失败逐项见[只读结果](evidence/s10-p0-16/readonly-result.json)。全部643表本次同一只读快照与P0-14旧源后签名全等：**True**，保护47/稳定31有独立子集门禁，不只按OID认资格。

643表内容SHA在服务器用明确pg_catalog无副作用内置函数计算：按id排序（无id按JSONB文本排序）的PG `to_jsonb(t)::text`，行间LF并保留尾LF，空表也为一LF；与历史Python逐行算法相同。只返回计数/hash，病历或password等全行不出服务器。客户只读取冻结的user/company/employment/grant、单据/报表安装元数据；私有原投影只在新700目录，公开字段有固定白名单、模板arch只公布SHA，不公布附件路径、姓名、登录、密码、医疗原文。

这是**一条连接的一次只读快照**，没有新业务、没有源后第二SQL连接，不能称业务前后独立全表实测。未运行字段/门禁以缺失或NOT_RUN处理。P0-13/P0-14克隆未连接/未复用；永久W5仍pending2，P0-14 confirmed3仅在那座克隆成立。

## user5本店实际权限与经济来源

实际最小[投影](evidence/s10-p0-16/eligibility-projection.json)显示user.active/share/company_id、allowed cid、store/company active，唯一membership及employee/resource的active/user/company关联；原生internal和YDental基础组按实际group关系及传递implied闭包判断，而非岗位名或管理员豁免。grant逐行含membership/category/level，按固定RANK none0/read1/write2验证settlement>=read、export=write。缺失、错关联或不满足即STOP，未补grant、换账号或登录。实际levels：`{"capacity": "write", "exam": "write", "export": "write", "finance_approval": "write", "frontdesk": "write", "medical": "write", "patient": "write", "price": "write", "settlement": "write", "space": "write", "warehouse": "write"}`。既存medical权限仅作为原权限元数据保留，没有读取医疗全文或扩大授权；源643表相等亦约束权限未改，当前会话scope/revision尚未创建或实证。

invoice1需company1/store1、posted/paid740/residual0；source1→fee4/20、2→fee3/40、3→fee2/80、4→fee1/600，原qty1/1/4/2与S05价600/80/10/10快照、原生invoice line对应。原payment1/2为500/240、move posted/reconciled、两条partial回原invoice，总740；S10登记cashier5本店cash一致。患者仅校验canonical ID/partner/本店关系，不读取姓名病历。全部检查状态依`readonly-result.checks`，静态预期不冒称实际PASS。库存/价目/所有费源/款项表本次只有签名/必要只读投影，无新收款、退款、费用或退库。

## 报表安装态、真实入口与可执行边界

固定XML的report action XMLID是 **ydental_settlement.ydental_settlement_pdf_report**，其report_name与QWeb模板XMLID为 **ydental_settlement.ydental_settlement_pdf**；原生 `_get_report`允许按report_name查找。核实际ir_model_data、ir_act_report_xml、res_groups_report_rel、QWeb两个视图及paperformat、locale、92模块和base_report_wkhtmltox等依赖安装态；不把模板XMLID误认action XMLID。模型ydental.settlement.receipt、类型qweb-pdf-wkhtmltopdf、A4/96dpi/12-16-14-14边距、原YDental组和no attachment行为按固定源码逐字段比较。

`ydental_settlement/controllers/settlement.py:135` PDF GET端点及service `_report_payload:1077`/`_pdf:1159`、report abstract model与manifest引用均只读源码。report模板及workbench模板按Odoo core convert.py template→t/full t-name变换后逐结构比较，保留属性和文本，忽略XML格式缩进；zh_CN缺专属arch时按原生en_US回退，中文源文字本身仍须匹配。字段hash/实际视图ID与check结果公开，未动态编译或渲染QWeb，也未验证wkhtmltopdf可执行文件、字体或浏览器表现。

**新增的静态入口限制**：service `_workbench:1015–1019` 仅列amount_residual>0账单；`views/ydental_settlement_templates.xml:81`“下载中文 PDF”链接在该invoices循环内。所以paid/residual0的invoice1在当前工作台没有这个按钮。即使本批只读权限/action/template门禁成立，也只能支持受控端点的来源资格，不能宣称“现有页面能点击invoice1按钮”或直接启动下一批。后续若要求本人原生按钮，须GPT决定合法入口及必要最小产品差异；本批不改addon、不临时构造按钮、不借新收款/改余额显示旧单。服务 `_invoice:313`本身可读取已过账本店paid单，这是与页面列表不同的静态范围。

S10 `_pdf`为当前动态内部账单并写report_download审计，no attachment，不是历史字节重印。print_job历史0不等于所有PDF不存在，W5同源历史原版仍缺；R3外部PDF是不同来源。S12正式税务原件、生产科目/税/币种/银行渠道实际到账政策仍待批准。实际PDF生成、report_download、业务GET/POST均NOT_RUN/0。

## 离线验证、预算与交付

[离线检查](evidence/s10-p0-16/offline-checks.json)验证SQL字面/参数/表列、内置函数白名单、一处连接/受控execute、源SHA，及缺export、export只读、错membership、未知RANK、group传递闭包等确定性负例；没有模拟成功业务来替代现场证据。旧3838份tracked文件逐字节不变，core未改，[verification.json](evidence/s10-p0-16/verification.json)记录本批边界。

除W5最多一条严格只读连接外，其它数据库/maintenance/CREATE/Odoo HTTP/Firefox/业务GET或POST/PDF生成/文书价格资金库存附件写/Odoo CLI/直接ORM/sudo/OS-PG-Docker-防火墙-IPv6专项均0。不改旧库、证据、产品/ACL/core/AGENTS、Issue/Project状态，不合并部署或启S11。原GAP-03 22行及P0-14已接受事实不改写；W4元数据STOP、旧W5 browser exit1/final_audit NOT_RUN、R3 Native SIGSEGV UNKNOWN永久保留。

仅正常线性提交/推送许可新增文件，[SHA索引](evidence/s10-p0-16/sha256-index.json)覆盖全部新增文件（索引自身SHA由正式回执固定）。正式Codex回执REST逐字读回后立即STOP等待GPT；不自行授权P0-17、CREATE或执行下一批PDF。
