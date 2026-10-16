# YD-N1 R1 S10-P0-07：登录请求字段门禁 STOP，历史退款 Web 补证 NOT_RUN

**本批 BLOCKED，不申请历史退款页或跨店列表技术 PASS。** 唯一新库已克隆并正常启动一次 Odoo HTTP；唯一 Firefox 在 user6 第一次登录时被执行器请求门禁拦截，未完成登录，未切店、未请求结算工作台。按停止条件保全，不修改冻结脚本、不重试、不另建库。S10 整阶段与生产仍 BLOCKED，历史 native SIGSEGV 根因 UNKNOWN，S11 NOT_STARTED。

唯一授权为 [6206799419](https://github.com/Yredxin/YDental/issues/34#issuecomment-6206799419)，前批正式复核为 [6206735953](https://github.com/Yredxin/YDental/issues/34#issuecomment-6206735953)。沿原分支 `codex/s10-settlement-finance-r1-20261013` 从 `da1f1547bf54044c3bb787ac1cfc382728f6b84d` 正常前进，core 固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。本次只新增七份 P0-07 脚本、本报告和三份脱敏 JSON；产品 addon、core、所有历史文件/数据库/filestore、Project 与 Issue 状态零修改。最终提交由 #34 BLOCKED 回执固定。

## 授权读取与真正的来源基线

GitHub API 完整取得 #23 正文/3评论、#34 正文/197评论、#35 OPEN/0，并完整处理每条正文、分节和 SHA；单独核 P0-06 授权/预检/交付/正式复核、P0-07 授权及 GAP-01 全22行矩阵和剩余候选。CREATE 前重取授权、#23/#34 当前正文与全部评论完全一致，无新增并行授权。#35 初次成功，随后 gh 两次只读复读 TLS 超时；改用现成 GitHub connector 的同一 API 读取，确认 OPEN/0 与原正文一致，没有修改网络或服务。

|来源项|本批新的实机只读结果|
|---|---|
|唯一来源|`ydental_s10_test_20261016_p006_4e8a91c7` / OID **2100321** / cluster7694897083368259627|
|config SHA256|`aa3d0cca39fc0fefe802812e587ffd53cc0884c5656ded545b536aca4b311439`|
|marker SHA256|`855ce4177af4e6e1b7574112278d9dfa00a74f58db53808af8e3843b95a9acd7`|
|数据库|643 public 表完整行签名、265受管表、schema、702模块/92 installed、全部 view 和有效语言 QWeb 与 P0-06 真正 **after** 全等|
|schema SHA256|`3e2c00487260472ad97ca84a68b7e4c1717364715df7e930ecba6ac766f70b1e`|
|filestore|194文件逐 SHA 相等、1075附件指针及每份文件 SHA1 对应；manifest `27174fa6aa277611a62f4feaf8deb65701d5bbd0d38f91b7966a9b90f0901372`|
|历史业务|退款14 rejected/approver6/audit2661；日结9 **unlocked**/unlocked_by6/audit2689；mutex唯一XMLID行ID1 revision **244**；旧receipt242 refund_reject、243 unlock和全receipt表保全|

P0-06 verification SHA `3a41643daef2283b4ba294ea790edd62ff9b2d77c5293257609c99b2bf7eed90`、business-before-after SHA `2c8c56a25e6972c8b16e71f2e28907cad10cfcf8c156ab0b8e5724444fd2841d` 均实测匹配；不用 P0-06 解锁前签名。R3 OID2056451、P0-02 OID2100311、P0-03 OID2100319、P0-04 OID2100320、P0-06 OID2100321分别与各自原封存的表/schema/module/view/filestore全等，开工与停机后均无活动连接。所有 SQL 连接显式只读 REPEATABLE READ，退出即关闭，没有 Odoo shell。

## CREATE 前选定的真实历史目标和字段许可

按产品 `_workbench_page(..., 'id desc')` 和退款所关联收款的真实门店域，只读固定 **退款13 / requested / store1 / 1.00 / 总排序52 / 第二页第2条**。它在第一页不存在，且不是已经驳回的退款14。门店1共63条、每页50，第二页为14(rejected)、13—3(requested)、2(cancelled)；门店3仅61(done)、1(done)两条，没有第二页。此处只有 SQL 选证通过，**没有真实 Web 可见性或操作通过**。

user6/store1、user14/store3实际有 settlement/finance_approval write，user14无store1授权。只读工作台数据域显示：store1无未付invoice，store3未付invoice5/6/8/9，两店未出账fee和pending event均空。冻结计划为user6第一页、真实点击退款下一页、user14本店列表，共3次GET（正式授权上限5，程序更严3）。user6读审计0；user14一次GET必须恰有4条actor14/store3/account.move/5/6/8/9的invoice_view，按旧audit2671字段模板仅允许id/create_date/write_date/target_id变化并绑定实际GET；source_view/pending_event_view新增0。

两人各login/login.scope/store.switch≤1，共6条，S01总新增≤10，旧行全部全等；session/device/user_log各≤2且每人≤1，已有user/partner/HR/resource只允许列明元数据；mail/tracking/通知新增0。资产仅固定来源/URL/mime/字段/大小/真实SHA与空checklist，默认其它643表全等，全部退款/日结/mutex/receipt、原生account/stock与YDental经济表强制全等。逐字段模板和值及上限全部写入事前 [preflight.json](evidence/s10-p0-07/preflight.json)，Web 后没有增补或放宽许可。

## 离线、正式检查点与资源窗口

同实际 `execute_pipeline/source_gate/clone_equal/validate_request/validate_page/web_diff/stop/readonly_final` 的 **1正例+53反例=54** 结果符合预期；错误源/OID/权限/页ID/状态/店/DOM/未知响应、偷偷付款/退款/解锁POST、PDF GET、业务/财务库存/ACL/module/schema/mail/asset、审计字段和GET错配均 FAIL_CLOSED。实际 Chromium 合成DOM **3正+5负=8**，Firefox/Odoo=0。真实 Odoo20 CLI parser确认仅 `odoo-bin -c <独立配置>`，无升级/安装/init/prepare/shell/test，cron0/workers0/loopback/SMTP禁发。这些只记 **SIMULATED_PASS / REAL_CLI_PARSER_PASS**，不能替代原生身份表单与实际业务页面实测。

构建阶段一次合成route回调参数误用、一次fixture缺UTF-8声明已在正式预检前纠正，失败原件保留；组装预检评论时另一次误用系统Python缺psycopg2，未生成API输入、未发表，随后用固定venv纠正。最终七份脚本重新全套离线验证并冻结。实际窗口后七份源码SHA与事前预检完全相同。

正式 [检查点6207010865](https://github.com/Yredxin/YDental/issues/34#issuecomment-6207010865) 在任何CREATE/HTTP/Firefox前发表；gh首次GET遇TLS超时，随后通过GitHub connector的**精确API评论URL**完整取得JSON。正文逐字相等、body SHA `6dd4f396e5060642bd8f3d1d8b6549051c5aeb0d49f91e1bfcd1c6367b887b31`、preflight SHA **`dfea99543c418fc47377dadc69ba4f9c28b898c9cf0d2d60e7fc7847095d830b`**、七份脚本SHA及精确argv均由checkpoint复核后才放行。

唯一新库 `ydental_s10_test_20261016_p007_7c92b4a6` / **OID2100322** / 127.0.0.1:**18290**，此前不存在且端口bind空闲；仅一次 autocommit/IDLE CREATE 从OID2100321克隆。新marker/config/data_dir/filestore/dbfilter独立，权限700目录；克隆初始643表、265受管/schema/module/view、194文件/1075指针与来源全等。唯一Odoo HTTP PID **4062517** 加载92模块并就绪，唯一Firefox Python执行器 PID **4062882** 启动一次。

## 真实失败与 STOP 边界

执行器用user6本人合成登录页GET200，加载现有原生资产和中文翻译；填入本人的合成身份后，先fsync登录intent，再点击原生登录提交按钮。**浏览器request事件记录一次 `/web/login` POST尝试，但request route在 `validate_request()` 内触发空信息 AssertionError，执行了 `route.abort()`，没有调用 `route.continue_()`，也没有把本次计入已放行POST集合。** 等待POST响应30秒超时，登录观察记录 HTTP=None、仍在原登录URL，严格门禁立即STOP。

原始route处理器只保存 `ROUTE_STOP AssertionError: `，没有具体断言行或原始字段集合；登录payload只有SHA `61d22075b1df2068af9b677049a774e6938b48f1499c6fadd5b26abd5ef73f61`。因此**确切失败字段 UNKNOWN**，不能凭推测称为产品权限拒绝、Odoo环境故障或已定位修复。离线模拟只构造了合成身份payload，没有证明真实原生登录payload与严格白名单相容，这是本次离线覆盖的实际限制；不在STOP后改白名单或补一次真实登录。

独立服务端日志 **POST=0、结算GET=0、settlement.action=0**；浏览器结算GET集合/已放行POST集合均空。user6切店、user14会话、第一页/第二页/跨店列表、截图与逐GET阅读审计绑定均 **NOT_RUN**。不能把只读SQL里存在ID13、离线DOM通过或登录页200说成历史退款Web验证通过。

Firefox执行器exit **1**，finally中的browser.close正常返回；Firefox原生子进程PID/独立exit未采集，不能把执行器PID冒称原生PID。Odoo HTTP正常停止exit **0**，无本次Odoo signal11；不代表历史native根因已修复。日志SHA分别为 `d1a7c7be3907a38e67e0234096111f3af8cf56292cb9178282819761dd689b2a` 和 `a9f62f01cf6df54b49d9fbe02b3392b82a8e39b0ef9b98bdab297d4e03409402`。停机后精确记录的两个执行器PID均不存在，新库无活动连接；未操作其它服务或进程。

## 停机后的独立只读保全与预算

克隆初始→失败停止快照→停机后再次只读实测：**643/643表完整行签名和受控逐行数据全等，变化表0**；265受管/schema/modules/views/filestore全等，194文件/1075指针原样。全部 **159张account_*/stock_*表**和14关键经济表相等；全退款/日结/receipt/S01旧审计原样、mutex244、日结9仍unlocked。新增S01/会话/device/user_log/mail/资产/文件/资金/库存全部0。来源P0-06与固定after再核对643/643相等，五座历史库再次全等并无连接。这里只是**保全PASS**，不是Web验收PASS。

|证据分项|实际结论|
|---|---|
|HISTORICAL_P003_REFUND14_REJECT|只读保留，没有重放|
|HISTORICAL_P006_CLOSE9_UNLOCK|只读保留，没有重放；旧user10/user14负向同样未重放|
|NEW_READONLY_P006_SOURCE / NEW_CLONE_EQUALITY|本批实机只读/克隆一致性PASS|
|NEW_REAL_WEB_OLD_REFUND_PAGE2 / NEW_CROSS_STORE_LIST_FILTER|**NOT_RUN**，登录门禁先停止|
|WEB_READ_AUDIT_FIELD_GATE|无结算GET、新审计0，全旧行相等；逐GET阅读审计实测未发生|
|NATIVE_FINANCE_AND_BUSINESS_UNCHANGED|643/643及全部原生财务库存保全PASS|
|SIMULATED_PASS|54主路径模拟、8合成DOM、真实CLI parser，不能替代真实Web|
|NOT_RUN|任何结算操作、PDF/RPC/附件权限、旧退款状态操作、其它GAP、S11、sudo/系统安全专项、合并/部署|

|预算|实际/上限|
|---|---:|
|CREATE / Odoo HTTP / Firefox launch|各1/1|
|工作台GET|0/5（程序更严0/3）|
|身份POST尝试|1/4，只有user6登录；已放行/服务端收到0|
|全部结算POST / _operate路径 / 业务资金库存写|各0/0|
|upgrade/install/init/prepare/shell / sudo|各0/0|

完整索引见 [verification.json](evidence/s10-p0-07/verification.json)；[643表前后签名](evidence/s10-p0-07/business-before-after.json)与事前预检可独立交叉核验。CSRF/凭据/cookie/私有原始日志和失败文件仅在权限700目录保留，GitHub只发布脱敏事实与SHA；本批没有生成截图或PDF。所有历史和本次失败原件保留。

正常提交推送原分支，在#34发布 `[CODEX] S10-P0-07 BLOCKED与复核申请`，API逐字读回后立即STOP等待GPT独立复核；不自行启动下一批。
