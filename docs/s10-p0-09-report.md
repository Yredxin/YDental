# YD-N1 R1 S10-P0-09：旧退款13页2与门店3列表只读Web交付

**Codex限定自测通过，申请 `S10_P0_09_OLD_REFUND13_PAGE2_STORE3_LIST_SCOPED_TECH_PASS`，等待GPT独立复核。** 两账号均由原生机制自动选择本人的目标门店/revision1，跳过全部显式switch；同一Firefox完成三个真实GET，退款13第二页和门店3列表均与独立SQL一致。所有结算POST、资金和库存业务写0。S10整阶段及生产继续BLOCKED。

唯一正式授权 [6208086602](https://github.com/Yredxin/YDental/issues/34#issuecomment-6208086602)，前批GPT裁定 [6208060014](https://github.com/Yredxin/YDental/issues/34#issuecomment-6208060014)。原分支 `codex/s10-settlement-finance-r1-20261013` 从固定 `5c67b6ec8fcdcf138f79148316ab8f960b6077eb` 正常线性前进；core只读 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。最终固定commit见#34本批回执。

开工GitHub分页API完整取得#23当前正文/3评论、#34正文/205有效评论及#35 OPEN/0，逐条建立全文SHA、分节与指令索引，核P0-08授权/预检/交付/裁定及本授权；CREATE前复读正文、状态和#23/#34全部评论同值，无并行授权。起点、本地/远端分支、origin、核心HEAD匹配、tracked工作树干净。只新增P0-09脚本、报告和脱敏证据，产品/core/ACL/历史程序证据/Project/Issue状态0修改。

## HISTORICAL_REFUND14_REJECT_CLOSE9_UNLOCK

退款14 rejected/approver6、旧审计2661；日结9 unlocked/unlocked_by6、旧审计2689；mutex唯一XMLID行1 revision244；receipt242 refund_reject/243 unlock及全部receipt原行均为历史基线。没有重放旧退款驳回、解锁、user10/user14权限负向或W5收款。所有退款/日结/收据/互斥行全等。

## P008_NATIVE_LOGIN_AND_AUTO_SCOPE_REAL_WEB

P0-08真实user6登录303、自动session184/store1/revision1及S01 2690—2692已由GPT有限接受；P0-08整体BLOCKED，旧脚本仍错误要求None/0，全部旧失败和库保留。本批不修改或在旧库重跑。

新执行器将 `Browser.scope()` 与 `Browser.select_scope()` 直接用于真实及Fake主流程。先以本人cookie的SID前42字节hash严格绑定唯一**新**SQL session，再核actor、membership、门店/员工/账号有效性、执行空闲、真实DOM revision和身份审计链：A已选目标/rev1直接使用；B未选店/rev0仅凭本人表单当前revision/CSRF切一次至rev1；C仅在事前有user14默认4的真实依据时才可4/rev1→3/rev2，不能接受任意别店/版本。原生登录仍严格六字段/各1、Origin/referer/CSRF/actor/路径/Content-Type/一次性intent和POST账本，无放宽结算POST。

本批只读源码及SQL：两actor实际供给assignment均空；已安装S03默认钩子在无安排时回看合法历史session，user6最新184/store1、user14最新182/store3，均rev1；两人active lease、serving/verify execution和active/verify hold均0。user14对store4确有活跃membership和settlement write，但没有默认到4的证据，**现场C_enabled=false / NOT_APPLICABLE**。测试default字段未安装，按实际schema及已安装继承判断，不虚构该字段或store4场景。P0-07旧route事故的精确失败字段仍UNKNOWN，不能由本批成功反推。

## NEW_READONLY_P008_SOURCE

唯一来源 `ydental_s10_test_20261016_p008_8d43a1e5` / **OID2100323** / cluster7694897083368259627；config SHA `b97f715d104afdb89044ad753e15ff0115c393b51a85e35a062b0069374313c9`、marker SHA `40789a77746ae5582e678a401f3b930f710d19c948500893744a126fa1b8937f`。

开工、CREATE前及停机后独立只读核验与P0-08真正after及私有停止快照全等：643public完整行签名/265受管、schema `3e2c00487260472ad97ca84a68b7e4c1717364715df7e930ecba6ac766f70b1e`、702模块/92 installed、全部view/有效语言QWeb、权限、194文件逐SHA/manifest `27174fa6aa277611a62f4feaf8deb65701d5bbd0d38f91b7966a9b90f0901372`及1075附件指针。固定P0-08 verification SHA `c799d2e619579535c632da02c3fb76bf222070099d8a3861ea089cccdcfc2f29`，before-after SHA `046483672f70fcbb9b7d43b6f2ddb01ffe5a8821367c0a591ad3f5f059468ee4`。

P0-08已发生的session184和审计2690—2692完整保留，未使用更早before抹除身份元数据。R3/P002/P003/P004/P006/P007/P008七座历史库按原OID与封存表/schema/modules/views/逐文件前后核对相等，无活动连接。

[正式预检6208298195](https://github.com/Yredxin/YDental/issues/34#issuecomment-6208298195) 在任何CREATE/HTTP/Firefox前发表并API逐字读回，冻结预检SHA `9af9a957a23eae5b3a9236e565cc6376f921a9b17ac0ac905a0f05e14ad573d6`、九脚本SHA及精确argv。真实窗口后九脚本SHA完全相同，没有补白名单或修改门禁。

唯一新库 `ydental_s10_test_20261016_p009_9e51b7c2` / **OID2100324** / 127.0.0.1:**18292**：仅一次autocommit/IDLE CREATE从OID2100323只读模板克隆，新marker/config/data_dir/filestore/dbfilter/权限700；初始643/265、schema/module/view/194文件/1075指针全等才启动。新config SHA `743808ca70ebf1baff4b4fc0a8191c7bcd7b514ec74d6096dfb4ddd5da45e2a9`，marker SHA `59347fb41fb9a8593620fb94da4852a1bcaf0c7fc48f8379c6d7b68502212fdc`。

## NEW_AUTO_OR_EXPLICIT_STORE_SCOPE

| 本人 | 登录POST/后继GET | 新scope | 实际分支/显式switch |
|---|---|---|---|
|user6|/web/login 303 → /ydental/access 200|session185/store1/revision1|A；POST0|
|user14|/web/login 303 → /ydental/access 200|session186/store3/revision1|A；POST0|

每次登录提交前记录真实原生DOM form/action/method/enctype、六个控件结构，fsync intent后仅POST一次；随后保存响应及独立SQL快照再验证审计和字段。scope hash从本人cookie取得，未注入context、改角色或提升权限。三次结算GET之前再次运行相同scope验证。所有route/response/pageerror0，既有五资产响应长度和SHA精确匹配事前文件。

B只在离线通过，本次没有实际必要性而不消费switch预算。C没有真实默认4依据，现场禁用；其代码仅在“假设存在provider证据”的隔离Fake fixture中测合法4→3/rev2，不声称真实C通过。

## NEW_REFUND13_PAGE2_REAL_WEB

user6本人store1会话先GET `/ydental/settlement` HTTP200，真实退款第一页50条按降序为 `[66,64,63,62,60…15]`，无ID13；显示退款“共63条；第1页”和原生下一页href `/ydental/settlement?refunds_page=2`。实际点击该链接，第二个GET200，退款页2为 `[14,13,12,11,10,9,8,7,6,5,4,3,2]`，第2条**ID13/requested/金额1.00**，独立SQL再次全等。

实际原生画面显示金额 `1.0`，DOM按Number.toFixed(2)归一为 `1.00` 后与SQL Decimal `1.00`比较，未声称UI原文有两位小数。截图和DOM均确认退款区分页为“共63条；第2页”；日结区仍第1页属于独立分页，本批未操作其下一页或日结按钮。只查看退款13，不触发其业务状态动作。

## NEW_STORE3_LIST_REAL_WEB

user14本人合法store3/session186/rev1，仅一次GET `/ydental/settlement` HTTP200。退款记录节点严格为**61/done/20.00**、**1/done/100.00**，与本店独立SQL一致，**没有store1退款13**；退款区无第二页。页面付款列表自身的62条分页不作为退款分页，不以任意文字同号代替记录节点核对。

这是列表级门店过滤实证，不是直接ID、RPC、PDF或附件访问鉴权的完整证明；没有点击任何PDF、资金或其它业务按钮。

三份原始PNG已逐张实际查看，均与DOM结论一致，只公开SHA：

| 页面 | 尺寸 | screenshot SHA256 |
|---|---|---|
|user6退款第一页|1440×8347|`193288fb43c175f73a2a5dc812ef6106b1b57019f3a8ce6af131e475fb27fd04`|
|user6退款第二页|1440×5113|`d5aa0e78e56f8e7d5f7c3673448e5204a6300b3a63fa35922851e3142db8452c`|
|user14门店3列表|1440×6319|`0090403c9af4c259576f68a77b1d681d201937bd73c2669cdd181c339b36ed11`|

## S01_WEB_READ_AUDIT_BOUND

旧审计2692行全部原样。新增10条，严格依事前模板/actor/store/target/source/时间及session revision链核对：

| ID | actor/store | event/source | target |
|---|---|---|---|
|2693|6/null|login/native_authenticated_login|res.users 6|
|2694|6/null|login.scope/authenticated_session|session185|
|2695|6/1|store.switch/interactive|session185，False→1|
|2696|14/null|login/native_authenticated_login|res.users 14|
|2697|14/null|login.scope/authenticated_session|session186|
|2698|14/3|store.switch/interactive|session186，False→3|
|2699—2702|14/3|settlement.invoice_view/confirmed_offline_transaction|account.move 5/6/8/9，分别一条|

均accepted、create_uid/write_uid为真实actor。原生自动选店带来的store.switch审计不是显式switch POST。user6两次GET阅读审计0；user14一次GET的四条阅读审计由独立before/after快照逐行绑定该GET，只有audit2671模板允许的id/create_date/write_date/target_id变化；source_view/pending_event_view0。10/11总上限且身份6/7、阅读4/4，没有任意审计额度豁免。

新session185/186、device9/10、user_log9/10各2，旧行全等；其它元数据按原许可核验，mail/tracking/通知0。全部资产、附件、文件/checklist新增0，194文件及1075指针原样。

## NATIVE_FINANCE_BUSINESS_UNCHANGED

克隆初始→结束只有4张身份/阅读元数据表改变：res_device_log +2、res_users_log +2、ydental_access_session +2、ydental_access_audit +10；**639/643表完全不变**，变表旧行全部原样且新增行逐字段通过。停止快照→停机后独立只读再测 **643/643及受控逐行数据全等**。

全部159张account_*/stock_*原生表、14关键经济表、所有退款/close/receipt/mutex及其余YDental业务、ACL/schema/module/view完整签名全等。退款14仍rejected、日结9仍unlocked、mutex244、receipt242/243及全表保留。来源P0-08及七座历史库前后相等、无活动连接。全部结算/收退款/出账/贷项/日结/库存写0。

## SIMULATED_PASS

正式同execute_pipeline/source/clone/真实Browser.scope/select_scope/请求/DOM/审计/stop/final路径 **3正83负=86**：A跳过switch、B仅一次、C假设证据模拟；scope非法actor/store/revision、伪cookie/hash、历史/重复session、缺审计/无权4/忙、重复切店/旧revision等负例核确切失败码，其余未知响应/字段/POST和资金/库存/receipt/mutex/ACL/module/文件漂移全FAIL-CLOSED。Chromium安装态登录原生序列化/route/退款DOM **17**例通过。Odoo20真实CLI parser通过，仅-c独立配置，无-u/install/init/prepare/shell/test、cron0/workers0、SMTP禁发。

模拟只对应模拟层级；本批真实覆盖A/A，不将B/C模拟升级为现场PASS。构建阶段一次只读SQL误假定未安装测试default列、一次Fake隔离目录缺QWeb fixture缓存，失败程序/trace保留，CREATE前修正并完整重跑；没有改源库或隐去失败。真实窗口没有失败、重试或替代库。

## 资源、NOT_RUN与交付STOP

| 项目 | 实际/上限 |
|---|---:|
|CREATE/Odoo HTTP/Firefox launch|各1/1|
|本人login POST|2/2|
|必要显式switch POST|0/2|
|身份POST总数|2/4|
|结算工作台GET|3/3|
|结算业务POST/_operate路径/资金库存业务写|各0/0|
|upgrade/install/init/prepare/shell/sudo|各0/0|
|截图|3（未设额外额度）|
|PDF下载|0/0|

唯一HTTP **Python进程PID4127241**与Firefox **Python执行器PID4127341**（日志SHA见机器索引）；两者exit0，finally browser.close返回。原生Firefox子进程PID及独立exit未采集，不能把Python PID冒称原生Firefox PID。记录的两个PID停机后均不存在，全部本批/历史连接0。本次Odoo signal11=0，旧native SIGSEGV根因仍UNKNOWN。attempt/result文件时间近似HTTP61.137秒、浏览器56.860秒、HTTP就绪2.549秒，未超预算。

NOT_RUN：真实B/C、退款状态操作、日结/收款/贷项/库存、PDF/RPC/附件权限、其它F/T组合、S11、合并/部署/系统专项。生产财务与税/支付政策仍未批准，不把此限定成功提升为整个T05/T10/T14或S10阶段PASS。

[verification.json](evidence/s10-p0-09/verification.json)保存逐GET/DOM/截图SHA/SQL/审计/预算；[business-before-after.json](evidence/s10-p0-09/business-before-after.json)保存完整643表前后签名；[preflight.json](evidence/s10-p0-09/preflight.json)固定九脚本SHA与全部事前许可。原始HTTP日志、cookie所在会话、SQL/intent/PNG和全部旧失败均私有权限700保全；GitHub只发布脱敏结构、合成事实及SHA，无口令/CSRF/cookie/session原文。

正常快进提交推原分支，在#34发布 `[CODEX] S10-P0-09交付与GPT独立复核申请`，API逐字读回后立即STOP等待GPT独立复核，不自行启动P0-10。没有替用户最终统一验收、关闭Issue或解除S10/生产BLOCKED。
