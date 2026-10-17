# S10-P0-17 已结清本店账单工作台 CODE_ONLY 交付

仅申请 **S10_P0_17_PAID_BILL_WORKBENCH_CODE_STATIC_TECH_ACCEPTED**，等待GPT独立复核。新增代码为已结清本店账单提供只读列表和受控当前内部PDF链接；本批未安装、未升级、未访问数据库或页面、未生成PDF。S10技术/生产及T12仍BLOCKED。

唯一授权 [6215375331](https://github.com/Yredxin/YDental/issues/34#issuecomment-6215375331)，P0-16正式裁定 [6215317877](https://github.com/Yredxin/YDental/issues/34#issuecomment-6215317877)直接作为历史事实引用，没有重复复核或重跑。原分支 `codex/s10-settlement-finance-r1-20261013`，固定父 `21dc2dc243200336959482fcfa9d3b5f5f5ad271`，core只读固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；固定子提交由正式交付回执记录。

## 事前授权与产品修改门禁

开工GitHub API完整读取#23正文/3有效评论、#34正文/236有效评论、#35 OPEN/0及远端ref。origin、本地/远端HEAD、工作分支与干净产品工作树匹配。旧#34前232条正文与此前完整读取逐字相同，后四条为P0-16预检/交付/正式裁定和本次授权；没有已有P0-17预检/交付或并行任务。[正文及评论SHA索引](evidence/s10-p0-17/github-start.json)仅用于完整性与任务归属核验，不重判上批结论。

产品修改前已完成固定core/三份产品盘点和反例方案，冻结[计划](evidence/s10-p0-17/preflight-plan.json)，SHA256 `6bf9510d061c3a342e0908fc8e3ed3f9480d56f6a045c632d7c4b08f23e02b59`。

唯一正式[预检6227632581](https://github.com/Yredxin/YDental/issues/34#issuecomment-6227632581)创建于2026-10-17 00:54:59 UTC，REST GET逐字读回于00:55:09.878310 UTC，3901字符/6741 UTF-8字节，body SHA256 `a7f656ef86e9599239cb03496e0e01a9243cf6f803ab5ee65641f452c78160fb`；读回时三份产品改动0、所有运行预算0。读回成功后才应用产品补丁。[原文](s10-p0-17-preflight.md)/[API读回](evidence/s10-p0-17/preflight-api-readback.json)/[最终字段及源码位置合同](evidence/s10-p0-17/action-contract.json)记录时序和原/新SHA。

## 最小产品变化

仅修改允许的三份旧文件，产品diff为45行新增、7行删除，完整[补丁](evidence/s10-p0-17/product-diff.patch) SHA256 `755f5423a27ed9349ba35d0268532dec134e12afd335436ab024d101000b7372`。

| 文件及本批位置 | 增量与边界 |
|---|---|
| `ydental_settlement/models/ydental_settlement_service.py:983` `_workbench` | 在原未结清列表之外添加独立settled查询/数量/页码。原invoices域、排序、付款与免单数据源及其它列表不变；所有其它方法字节不变。 |
| `ydental_settlement/controllers/settlement.py:31` `workbench` | 新增settled_page、页码长度门禁及can_export；沿用原page_url传递筛选与分页。其它controller方法、routes及PDF入口字节不变。 |
| `ydental_settlement/views/ydental_settlement_templates.xml:107` | 只追加`section name="settled-bills"`；旧表格/所有表单/共享分页完整保留，无新form、勾选或资金操作。 |

新列表显示账单ID、原生号、业务日、总额和已结清余额；无记录时明确“本页无已结清本店账单。”。仅具当前会员export=write时出现**“下载当前内部账单 PDF”**，地址仍为 `/ydental/settlement/pdf/bill/<invoice.id>`；无导出权显示“仅供查阅”。这是当前动态内部演示账单的入口，不能称历史原版重印、税务开票或银行/平台到账证明。

## Domain来源、隔离与权限合同

[domain-api-static.json](evidence/s10-p0-17/domain-api-static.json)保存固定core实际路径、行号、文件SHA和有关源码段：

- `odoo/fields/__init__.py:20`真实导出Domain；`odoo/orm/domains.py:81–101/207–224/318–339`定义any/not any、三参数构造、AND及取反。
- `odoo/orm/fields_relational.py:847–889`的x2many量词在同一模型env取comodel、生成存在/不存在条件；`odoo/orm/models.py:1432–1447/4852–4890`证明search使用模型环境而非已有记录ID集合，现有su环境不因comodel规则隐藏混店来源。
- 本仓真实source inverse关联为`account.move.ydental_settlement_source_ids→ydental.settlement.source.ydental_invoice_id`；fee/event、继承的store/patient字段均从真实模型AST核对。来源/费用/事件模型没有active字段隐藏不合格行。

新域必须同时满足：当前store.company、posted、out_invoice、paid、residual=0；**存在合格来源，并且不存在任何不合格来源**。合格来源必须属于当前店、有真实fee，fee及其confirmed event属于当前店；选择患者时，source/fee/event患者全部处于原合法patient-family内。存在一条本店源不足以放行混店发票；同公司其他店、混店、混患者、外店费用/事件及缺费源都被排除。

patient仍通过原 `_patient`、`_current_relation` 后再求 `_patient_family_ids`；没有将任意URL patient_id直接当作授权family。无patient筛选时允许当前店原有结算读取范围内的患者账单，不授予他店财务或医疗全文权限。

新查询复用原invoices记录集已经由 `_access()` 鉴权的account.move环境。原`search`不以该记录集的未结清IDs限制新搜索，故即使invoices为空也能查询settled；新代码没有增加sudo调用或any!量词。正、反量词在这个已有环境中约束**所有**来源，避免把不可见的外店源漏算。它没有为缺失页面字段额外sudo读取患者全文，也不改变现有权限/ACL。

`can_export`只取controller当前 `access._membership(service.env.uid, context['store'].id)` 的 `_levels(member)['export']=='write'`，无岗位、manager或历史user5资格豁免。工作台初始settlement read、员工、公司与session binding校验完全保留；缺导出权不阻断获准的账单摘要。旧页上的链接不等于永久授权：现有PDF `_report_payload`仍先 `_access()`，再检查export write，`_invoice`再核来源店/公司。撤权、错误店或会话下一请求仍受这些服务端门禁约束；本批没有真实撤权/HTTP测试。

## 分页、变量与未来副作用

| 字段 | 合同 |
|---|---|
| `settled_page` | GET参数，默认字符串1；decimal字符串1–5字符，整数1..10000。先验长度，5000字符数字也在int转换前拒绝。保持原isdecimal语义，合法前导零/Unicode decimal输入解析成整数；没有放宽其它原页码或患者校验。 |
| `pages['settled']` | 模型仅接受真正int，bool/字符串/浮点/0/负数/10001拒绝；原七类分页及上限保持。 |
| `settled` / `page_counts['settled']` | 现有 `_workbench_page`搜索与计数，limit50、offset=(page-1)*50，按invoice_date asc,id asc稳定排序；不合并入原invoices付款集合。 |
| `page_url` | 原实现不改，新pages字段自然进入链接；保留patient_id及其它已选分页，第一页省略默认参数，重复求值不改原pages。 |
| 新导航 | 独立prev/next，无共享旧模板改动；next同时要求还有记录和当前页<10000。页码超出实际结果但在合法上限内时显示本页空态。 |
| `can_export` | 当前本店实际会员的export=write；模板仅对新settled段应用此可见性，旧未结清区块保留。所有PDF实际下载仍由原服务端鉴权。 |

新列表未来真实运行会为**每条实际展示的settled记录**调用既有 `settlement.invoice_view` 审计（最多50/页），原audits亦仍照原路径执行；不会直接调用会计write、收款、退款或库存服务。只读列表允许该S01非经济审计，不能宣称将来整个请求零写。本批没有运行此请求，实际审计和经济写均为0。

## 实际静态结果与证据边界

命令 `PYTHONDONTWRITEBYTECODE=1 python3 scripts/s10_p0_17_static_checks.py --test` 最终exit0：**102项功能/契约静态检查＋3852份非许可旧tracked文件字节保全，共3954项通过**。[完整结果](evidence/s10-p0-17/static-results.json)逐项标注STATIC_FILE_FIXTURE，计数不等于Odoo业务测试数。另用目标venv **Python3.12.15**作两产品Python文件及检查器的内存AST/compile，exit0、无模块导入或执行，见[兼容检查](evidence/s10-p0-17/python-compatibility.json)。XML只解析，不调用QWeb。

覆盖公司/门店/同公司混源/缺失及异常fee/event/患者family；原生RANK读权限、导出none/read/write、manager不豁免、缺员工或会员、错误session owner/revision、当前店及患者关系、撤权后服务端先验；新页码非法值/类型/溢出、105条50/50/5、稳定排序无重叠、重复页/空页/上限、URL保留筛选；返回的settled/count/pages/can_export与模板变量链和真实字段链一致。

删除否定量词的变异反例会把同公司混店发票错误放行，因此静态断言能检出该放宽。剥除新增节点后，**旧 `_workbench` 整棵AST逐结构相同**；剥除新section后，**旧QWeb整棵结构相同**。服务除_workbench、controller除workbench的所有源码字节相同，包含_workbench_page、_invoice、_report_payload、_pdf、PDF controller及业务POST等。产品补丁也明确只有三文件增量。

首次静态运行exit1，原PDF方法的文本片段断言因ast.unparse为generator增加括号而失败；这不是产品PDF失败或动态测试。已保存[首次失败](evidence/s10-p0-17/static-attempt-01.json)，改为AST结构及原方法全树比较后exit0，[第二次结果](evidence/s10-p0-17/static-attempt-02.json)保留；随后补齐变量/字段链及读取撤权门禁的必要检查，最终上述102项通过。没有数据库或原生业务重试。

Domain案例使用从实际产品表达式抽取的**独立符号谓词**，权限/页码仅隔离求值纯标量guard及page_url。没有导入Odoo、执行service/controller完整方法、原生Domain优化/SQL生成、ORM查询、HTTP或QWeb引擎。由源码固定可审查性支持代码层结论，不充当已安装行为实证。

## 未运行、未来用户效果及撤回

所有新旧数据库/maintenance连接、CREATE、Odoo HTTP启动/Firefox、业务GET/POST、PDF生成、直接ORM、Odoo shell/install/upgrade/init/test、执行者sudo、OS/PG/Docker/网络专项**预算及实际全0**。W5、P0-13/P0-14均未连接或复用；没有查看其凭据、原始病历、HTTP或截图。历史500+240、退款14、日结9及负向、退款13分页、旧文书确认均未重放。

以下仅是**后续独立授权后**的预期用户效果，本批全部NOT_RUN：

1. 在新的独立合成来源、明确安装及metadata白名单的新授权窗口中同步本模块代码/QWeb；先核来源/角色/公司/门店，不碰W5或旧事故/已确认克隆。
2. 本店具有settlement read的本人进入工作台，原未结清区和付款勾选保持，新段只显示本店posted/out_invoice/paid/residual0账单。
3. export缺失/只读时新段仅供查阅；真实export write的当前会员刷新后看到“下载当前内部账单 PDF”。
4. 筛选已合法建本店关系的患者/别名，已结清列表仅包含其family的合格来源，跨公司/店或混源单据不出现。
5. 独立合成105条匹配账单按50/50/5分页；患者与其它页码保留，重复页内容稳定，空态清楚，不跳到10001页。
6. 原未结清账单仍只在原付款选择集合；新列表无支付/免单控件，不为验入口重发旧收款。
7. 权限/会话变更后的下一请求按当前授权重新判断；旧链接仍须服务端当前店settlement read和export write。本批仅静态反例，不执行历史负向测试。
8. 只有后续新授权明确包含PDF时才可本人点击验证动态PDF/中文字体/审计与经济不变量；当前不承诺按钮已安装可点或下载字节成功。

安装动作本批未执行。若未来需要模块升级、同步QWeb或原生回归，必须另获授权，限定新的独立合成数据库、合法源/角色、模块及metadata差异/审计白名单、命令/连接预算和预检读回；不得直接使用旧W4升级脚本或永久W5、P0-13/14克隆。

回滚说明仅为未执行方案：若独立复核要求撤回，后续经明确授权在原分支追加逆向产品补丁提交，只撤本批三份产品文件的增量，核对后续修改以免覆盖；**保留本批全部报告/脚本/证据与旧历史**，不reset/clean/force-push、不修改数据库或余额。固定原文件SHA和完整product-diff供逐字段核对，无数据迁移需回退。本批回滚执行次数0。

## 固定交付及STOP

[逐文件SHA索引](evidence/s10-p0-17/sha256-index.json)覆盖三份修改文件及全部新增脚本/报告/证据，索引自身SHA由正式交付评论固定；[源码合同](evidence/s10-p0-17/action-contract.json)列原/新SHA、实际方法行与时序。仅正常线性提交推送，Issue/Project正文或状态、ACL、core、AGENTS、旧报告证据不修改；不合并部署、不启P0-18/S11。

正式Codex交付回执REST GET逐字读回并保存后立即STOP，等待GPT。本批不能升级为T11/F4/T08/T12或S10整阶段PASS；R3 Native SIGSEGV UNKNOWN、W4 metadata STOP、旧W5 browser exit1/final_audit NOT_RUN、同源历史原版PDF缺失及生产财税/渠道到账政策待审继续保留，最终S13统一用户效果验收边界不变。
