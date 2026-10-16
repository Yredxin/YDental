# S10-P0-14：既存文书一次原生确认与双源只读保全交付

**本批限定子路径 Codex 自测完成，等待 GPT 独立技术复核。** user7 在唯一新克隆中通过真实原生 Firefox 对既存 doc1 完成 acquire1、confirm1、原生自动 release1；最终独立 SQL 和真实页面均为 **confirmed/version3**，唯一新增 confirm 版本3，原完整内容、旧版本1/2及作者保留，编辑锁释放。旧 W5 两个独立只读快照的643表全等；新克隆633表完全不变，627禁写表全部相等，费用、资金、价格、库存及附件零变化。没有重放历史交易、触碰P0-13旧克隆或改写其失败证据。

本报告只申请 `S10_P0_14_W5_DOC1_NATIVE_CONFIRM_SOURCE_BEFORE_AFTER_AND_MONEY_STOCK_ZERO_SCOPED_TECH_PASS` 的 GPT 复核，**不是 GPT 已PASS，也不是 F4/T08/T12/S10整阶段或生产PASS**。原生引擎stderr仍有未归因诊断，见第7节；不以exit0声称浏览器或历史Native稳定性已根治。

## 1. 正式依据、固定身份及交付范围

唯一授权 [6212000008](https://github.com/Yredxin/YDental/issues/34#issuecomment-6212000008)，P0-13正式裁定 [6211928330](https://github.com/Yredxin/YDental/issues/34#issuecomment-6211928330)。只在原分支 `codex/s10-settlement-finance-r1-20261013` 从父 HEAD `6c64403f9c015c669e50e750aff6e0e7a2eab3c0` 线性新增；origin `https://github.com/Yredxin/YDental.git`，开工GitHub REST ref与本地相同。固定 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` tracked工作树干净。最终完整SHA由#34交付评论固定，文件SHA由本批索引固定。

开工API完整取得 #23正文/3评论、#34正文/224评论和 #35 OPEN/0；发布预检前再次确认 #34末条仍本授权、远端HEAD不变。交付前完整重读 #23/3、#34/225和 #35 OPEN/0：原正文和评论内容全等，仅新增本批预检，无并行授权或交付。[开工索引](evidence/s10-p0-14/github-start.json)、[交付前比较](evidence/s10-p0-14/github-delivery-read.json)。

仅新增本批允许的scripts/docs/evidence；产品addon、ACL、core、AGENTS、旧报告/执行器/证据、Issue正文/状态及Project全0修改。P0-13旧clone/OID2100325未连接、未复用、未读写其运行目录；只读取用户允许的既存私有HTML/HTTP/快照与固定公开证据，用于静态证明。P0-12/P0-13旧入口未执行，旧正式裁定未重新审查。

## 2. 优先离线证明和真实源码依据

[static-contract.json](evidence/s10-p0-14/static-contract.json)记录19项确定性 `STATIC_REVIEW_PASS`，不导入Odoo/PostgreSQL/HTTP/浏览器。旧原件先与P0-13固定原件索引SHA核对；当前权限验证仍标NOT_RUN，不能用历史静态数据替代当前SQL。

|问题|固定源码和确定性证明|本批精确规则|
|---|---|---|
|缺失data-execution|`ydental_clinical/views/ydental_clinical_templates.xml`表达式`execution.id if execution else 0`；core `odoo/addons/base/models/ir_qweb.py`约2119行仅在`value or isinstance(value,str)`时输出；静态执行该表达式和输出条件证明数值0省略、字符串0保留，旧真实HTML无属性；原生document.js的`Number(undefined)`为NaN/falsy、`Number('0')`为0/falsy，由纯Node表达式验证|只在实时actor7无serving/verify、doc1为handover及其它ID/版本/内容/权限全部成立时，接受缺失或字符串0；非0/actor/版本漂移拒绝；不写DOM属性|
|新session write_uid|`ydental_access/models/ydental_access_service.py` `_session_for_key`以当前uid创建、`_switch`写store/revision；core `odoo/orm/models.py` create约4291/4293、_write约4010使用env.uid，sudo约5431明确不换user|仅本次唯一新增行可与模板row4的write_uid8不同，且create_uid=write_uid=7；actor7/store1/revision1/SID绑定，其余仅原4差异；所有旧行全等|
|source.view合法来源|`ydental_clinical/controllers/clinical.py` workbench对本店pending文书非sudo search → core BaseModel.search约1450行调用search_fetch → `ydental_access/models/ydental_access_source.py`约88行非su的`records._source_audit('source.view')` → 约146行_scope和_audit_values；clinical.document的_source_domain与access source的_access_domain校验medical读取/本店范围|固定actor7/store1/medical/source_model/doc1/accepted，空reason/before/after；首次GET时唯一pending文书是doc1，恰1条；confirm后列表空，末次GET0条。冻结总1，比授权绝对≤2更严格|
|redirect漏计数|安装Playwright `async_api/_generated.py`约10580行说明route仅拦首URL；`_impl/_browser_context.py`约723行_on_request独立emit Request，_on_response亦独立emit；旧login303 Location、浏览器response与已保存服务器GET均1、旧route计数0|新计数按BrowserContext全部真实Request身份，包括redirected_from；响应和最终服务器日志三方一致，route不再重复计数；全部POST仍由route一次验证/防重|

source.view证明不仅匹配旧观察值，还把**实际纯字典构造函数AST**提取执行，与旧audit335逐字段相等；错user/store/doc/source/category和新session错write/create_uid/store都静态拒绝，没有模拟ORM或业务POST。原生pending查询、授权domain、su条件和空结果不造审计均有静态断言。最终实际9条审计严格匹配，未事后扩大白名单。

执行器另18项文件内检查PASS，包括用P0-13**真实已保存login-only结束快照**证明新精确规则可通过，同时原P0-13白名单FAIL永久保留。这不是复跑旧业务。准备期一次冻结入口误引用旧connector文件后缀发生FileNotFoundError，在发布前修正新输入路径，失败日志和未执行草稿保留；当时19项源码门禁已通过，SQL/CREATE/HTTP/Firefox/POST始终0。没有把该失败当可执行预检。

## 3. 正式预检、冻结及双源克隆

正式预检 [6212387399](https://github.com/Yredxin/YDental/issues/34#issuecomment-6212387399) **先发表、REST GET逐字读回后才执行**：16043字符、20477 UTF-8字节，bodySHA `b11a961e4b506418556fa0976c229dbaa2b3ec1cffb538f0fd78e73158e4cfd4`。[预检正文](s10-p0-14-execution-preflight.md)、[读回凭证](evidence/s10-p0-14/preflight-api-readback.json)。预检与机器计划冻结6个脚本SHA、所有静态/私有依赖、SQL字面值/643展开SELECT/catalog列名、47个最小门禁表、627锁定表、25资格及逐字段规则。机器计划SHA `f2769b28d5941527792fef9a11b6bf8911033ff7aa30e886df246307dbb5c282`。执行前后全部冻结SHA相等，无执行中修脚本/规则/预算或补充检查点。STOP后新增evidence.py仅处理现存文件，不含数据库/原生Web入口。

|顺序|实际事实|
|---|---|
|W5前验 #1|2026-10-16 09:24:51.979 UTC，backend1139508；READ ONLY/REPEATABLE READ，首次SELECT前SHOW确认；源名/OID2100310/cluster7694897083368259627、643表与P0-13源后验、47保护/31稳定、152文件/164指针、config/marker/父W4血缘/92模块/QWeb匹配；finally ROLLBACK/CLOSE|
|当下25资格|25/25；user7 active/internal/allowed company1/member5/employee3/medical-write/capability1及原资格；patient1/store1/company1/doc1 pending2/responsible7/execution1 handover/旧lease inactive/无editor或本人serving/verify；完整TEXT_FIELDS+teeth和旧版本保持|
|maintenance|前验已关闭且模板无其他连接、目标名不存在、cluster匹配，独立postgres autocommit/IDLE，一次CREATE；不杀连接、不改源、不重试|
|唯一新克隆|`ydental_s10_test_20261016_p014_7c42a9e1` / **OID2100326** / HTTP18314；独立filestore152文件全等、config/dbfilter/data_dir/marker封存；初始643表与刚才真实源前验全行相等|
|目标前验 #1|同一只读物理连接；初始643一次，随后7个新RR事务分别读取固定47表并ROLLBACK，检查startup/登录前/login-view/acquired/confirmed/released/final-view；共8个快照，无每POST新连接|
|目标后验 #2|关闭前验连接并停止自有HTTP后，独立新RR快照取得完整643表；严格冻结final-view比较器PASS，rollback/close|
|W5后验 #2|2026-10-16 09:25:18.845 UTC，另一个backend1139635；新READ ONLY/RR快照全643/47/31/身份/附件/filestore/config/marker与真实源前验完全相同；rollback/close；无第三条连接|

[源前验](evidence/s10-p0-14/source-before.json)、[25资格](evidence/s10-p0-14/eligibility.json)、[克隆](evidence/s10-p0-14/clone.json)、[源后验](evidence/s10-p0-14/source-after.json)。最小47表只证明其实际被读集合，不冒充643经济证明；[最终完整门禁](evidence/s10-p0-14/gate-stopped-target.json)与[全643表比较](evidence/s10-p0-14/all643-target-comparison.json)提供最终全库依据。

## 4. 真实原生流程、DOM、权限和审计

本人user7原生login POST303，默认合法store1/revision1，显式switch0；redirect临床GET1/200。初始真实DOM中data-execution仍缺失，执行器仅读取为缺失，不伪造0；其它doc1/revision1/version2/pending/heartbeat2/canHandover=no及完整原文全等，sessionStorage无holder/editor。本人原生生成64位alnum connection，CSRF/Origin/cookie/SID scope逐步绑定。

点击原生Open → acquire1/200 accepted、原版本2/内容不变 → 立即点击Confirm text only → confirm1/200 accepted、CAS2/独立新UUID/完整原样TEXT_FIELDS+teeth、saved_version3/confirmed → **未人工点击release**，JS自己release1/200 accepted → 返回GET2/200，最终confirmed3、三个作者版本、待完善列表空、editorStorage清除、release按钮禁用。

每个下一POST转发前只读47表核前一步真实提交、权限原行、scope、doc/editor/version/audit/fence，全部PASS；Confirm已在原生JS内置saving=true期间执行这些门禁，2秒timer原样跳过，自动release后token=null。真实heartbeat0，不改JS、不屏蔽timer、不构造HTTP、不换key、不重试。acquire intent到confirm intent1.810004秒、confirm到release1.699402秒，包含门禁延迟；这些时间不是零heartbeat的替代证据，真实HTTP记录才是依据。

[网络/响应/服务器勾稽](evidence/s10-p0-14/http-reconciliation.json)：clinical GET=2/2/2，计数器2，首条redirected_from=/web/login；全部POST路径顺序为login+3次clinical action，四方计数相等，原始请求operation/响应与事务门禁同序。原P0-13 GET漏计数不改写。

唯一新增session16属于本次新clone，create_uid/write_uid=7、store1/revision1，旧模板row4 write_uid8保留。新增审计331—339依次：login、login.scope、store.switch、clinical.view、source.view、clinical.edit_acquire、clinical.confirm、clinical.edit_release、clinical.view；**source.view仅首次GET1，最终GET0**。9条逐主体/category/source/target/before-after/reason/schema/actor/dates验证，旧审计和旧session行全等。[文书/审计字段证据](evidence/s10-p0-14/document-audit-fields.json)。这些ID与其它克隆可同号，但数据库OID不同，不能混淆成重放P0-13。

5张原生截图均逐张目视核验、只留本地700目录：[截图SHA/DOM元数据](evidence/s10-p0-14/native-dom-visual-review.json)。确认/释放后的**导航前**旧页面部分标题/旧历史仍显示pending/v2，而server-version已3，这是原生JS局部更新；最终GET后正确显示Text confirmed、版本3/旧2/旧1及空pending列表。不把过渡截图当最终状态，也不改产品消除此原生表现。实际UI为英文，不声称本批完成中文UI/正式临床签署验收。

## 5. 全表、副作用、金额与实际预算

目标643表完整比较：**633表完全相同**，只有以下10表发生预冻结允许变化：res_device_log+1、res_users_log+1、access_session+1、access_audit+9、clinical_document1状态/版本/保存与write元数据、clinical_version+1、四mutex各revision+3。其余字段及所有要求保留的旧行不变；orm_signaling实际新增0，未使用允许最多3的额度。旧文书内容、作者/责任/原execution/template、v1/v2全行保留；唯一新version3 kind=confirm/author7/previous2，内容与原doc全等，doc最终editor字段全部为空。

冻结627禁写表全行SHA全部相同，包含全部account.move/line/payment/partial、receipt/source/fee/refund/close、全部price/snapshot/event、stock.move/quant/lot、附件/mail/模块/QWeb。invoice1仍posted/paid740/residual0，历史payment500+240/partial1/2保全；source→fee实际外键 **1→4/20、2→3/40、3→2/80、4→1/600**。没有产生新资金、费用、库存或价格事件，filestore/164指针也不变。

|预算项|实际|
|---|---:|
|W5来源前/后连接|1 / 1（两个独立backend，总2）|
|目标人工前/后连接|1 / 1（前验同物理连接8个新只读快照）|
|maintenance / CREATE|1 / 1|
|Odoo HTTP / Firefox启动|1 / 1|
|原生login / 显式switch POST|1 / 0|
|clinical GET（含redirect）|2|
|acquire / confirm / 自动release / heartbeat|1 / 1 / 1 / 0|
|其它业务POST / PDF / 财务费用库存新写 / 历史重放|全0|
|shell/upgrade/install/init/test / 直接业务ORM / 执行者sudo|全0|

Odoo自有PID96043 exit0，Firefox真实engine PID96134 exit0/signal null；控制器exit0与真实HTTP/SQL/DOM证据共同支撑限定自测完成，不单以exit0判断通过。[原执行结果](evidence/s10-p0-14/execution-result.json)、[原浏览器结果](evidence/s10-p0-14/browser-result.json)、[综合核验](evidence/s10-p0-14/verification.json)。

## 6. 用户效果与边界

已实际完成的有限用户路径：本人登录 → 自动合法店1 → 查看既存doc1及旧全文/版本 → Open for editing → Confirm text only → 原生自动release → 页面显示confirmed/version3和3个作者版本 → 编辑锁释放且费库款不变。截图和原HTML保本地，GitHub只脱敏字段/哈希。用户最终效果验收仍在S13后；不要求用户在任何保全旧库自行重演来补证。

本次没有执行数量更正/退药、退款14、日结9/权限负向、退款13分页/store3、W5历史500/240收款或任何原版PDF重印；这些NOT_RUN/旧缺口不被新文书确认覆盖。文书文字确认不等于新的治疗/检查/药房实际执行，也不代表正式病历签署、财税政策或真实到账获批。

## 7. 保全、隐私、原生诊断和残余风险

P0-13及全部历史失败/证据、所有旧库/filestore/卷/备份保留；本批新库和已确认文书永久保留，没有为了测试回退删版本/审计、改回pending或重发confirm。若业务以后需要合法文字更正，必须由新正式授权走新关联版本，本批不执行。原W5 config/marker及父血缘封存不变。

本批没有pageerror/HTTP拒绝/未知动作/heartbeat/超时/业务重试，也没有记录新Odoo SIGSEGV；但**原生Firefox stderr仍有8条未归因诊断行**，标签出现次数NS_ERROR_ABORT3、NS_ERROR_FAILURE2（同一行可能重复标签）、error in channel4，含FaviconLoader、protocol/dispose和webprogress线索。原件及行SHA见[引擎诊断](evidence/s10-p0-14/browser-engine-diagnostics.json)。它们不同于页面pageerror，未被本次执行器当业务响应错误；不声称全程无浏览器错误或已证明其无影响，请GPT结合限定原生事务证据判断其是否影响本批最高子路径结论。没有为诊断这些引擎信息再启动浏览器/服务或做OS专项。

私有目录 `.local/s10-p0-14/` 与新运行目录均700，医疗全文、凭据/cookie/CSRF/session/connection/editor/key、完整HTML/HTTP/真实截图/原始日志仅保本地；GitHub只公开ID、事件、状态、金额、字段名及SHA。[私有原件索引](evidence/s10-p0-14/private-artifact-index.json)不包含原值。使用已读odoo-guidelines/odoo-web-guidelines静态核对源码，未修改产品，未使用其他执行者。

## 8. 复核请求、固定交付与STOP

请GPT独立核对：优先静态三问题来源/精确字段和redirect计数；预检REST逐字读回早于SQL；冻结6脚本全等；源前验关闭→单CREATE→唯一本人原生acquire/confirm/自动release→独立目标全643→独立源后验全643；9条精确审计、唯一version3/旧全文作者保留、627经济禁写表全等及全部预算。请另评估保留的原生引擎stderr诊断，不能据exit0或静态PASS自动授予GPT PASS。

正常线性提交推送后在#34发布`[CODEX] S10-P0-14 既存文书一次原生确认交付与GPT独立复核申请`，固定最终SHA及本报告/机器证据链接；GitHub REST GET正文逐字读回并私有记录comment ID/URL/字符/字节/SHA后立即STOP。交付后不继续数据库或原生Web、下一批/S11、合并、强推或部署。

**S10整阶段技术/生产及T12仍BLOCKED；R3 Native SIGSEGV UNKNOWN、W4元数据STOP、W5旧browser exit1/final_audit NOT_RUN、同源原版PDF重印缺口及生产科目/税/币种/到账政策待审批均保留。#34 OPEN、#35 S11 NOT_STARTED，Project0 mutation。**
