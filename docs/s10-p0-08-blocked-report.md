# YD-N1 R1 S10-P0-08：原生登录通过，默认门店会话判据阻断

**本批 BLOCKED，不申请退款13页2或跨店列表限定技术PASS。** user6唯一原生登录POST通过六字段门禁，服务器303、后继访问入口GET200；执行器随后错误预期“无已选门店、revision0”，实际新会话已由原生机制选店1、revision1，触发scope断言并停止。全部结算GET/POST、显式切店POST、资金库存业务写0。未修改冻结执行器重试，唯一新库及原始失败保留。

唯一正式授权 [6207347281](https://github.com/Yredxin/YDental/issues/34#issuecomment-6207347281)；前批GPT裁定 [6207285901](https://github.com/Yredxin/YDental/issues/34#issuecomment-6207285901)；CREATE前正式预检 [6207559984](https://github.com/Yredxin/YDental/issues/34#issuecomment-6207559984) 已通过API逐字读回。原分支 `codex/s10-settlement-finance-r1-20261013` 从固定起点 `4f40f11f51ca4f73070c117b88770e31d1354e9c` 线性前进；core只读 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。最终提交由#34本批交付回执固定。

## 任务来源与固定环境

开工分页API完整取得#23当前正文/3条评论、#34正文/201条评论及#35 OPEN/0，逐条建立完整正文SHA、分节/指令索引；与P0-07开工归档逐条比对，#23三条同值，#34前197条同值，四条新增预检/交付/复核/本授权完整核对。正式预检前再次读取正文/状态和#34全部201条评论，无并行新授权。现行合同仅6207347281，旧批次授权不累计为本批资源或业务许可。

本地/远端HEAD、分支、origin与核心HEAD匹配，tracked工作树初始干净。仅新增P0-08脚本、报告、脱敏证据；产品addon/core、ACL、所有历史程序/证据/库和文件未修改。GitHub Project及Issue状态0写，不sudo、不做系统专项，不合并/部署/启动S11。

## HISTORICAL_REFUND14_REJECT_CLOSE9_UNLOCK

退款14 rejected/approver6、旧审计2661；日结9 unlocked/unlocked_by6、旧审计2689；receipt242 refund_reject、243 unlock；mutex唯一XMLID行1 revision244全部属于初始克隆基线。未再次驳回、解锁、执行旧user10/user14负向或W5付款。全部历史退款、日结、receipt及mutex整行/签名严格全等。

## P007_LOGIN_GATE_CAUSE_EVIDENCE

P0-07精确失败字段依然 **UNKNOWN_NOT_CAPTURED**。其旧执行器白名单与安装态模板存在可证差异：本机 `web.login` view195含csrf/login/password/type/redirect；已安装 `auth_passkey.auth_passkey_login` view320继承195，在redirect前插入空hidden `webauthn_response`。原生passkey控制器将字段加入CREDENTIAL_PARAMS；password模式只消耗非空credential。auth_signup.login506只加链接。

本批六字段各1的合同已由固定源码、安装态各语言SHA、Chromium原生表单序列化和实际Firefox DOM共同证实；原生user6提交实际包含 `webauthn_response` 空字段、type=password，redirect精确为 `/ydental/access`。这不能反推P0-07当时唯一失败断言，也不能称P0-07事故已根治。

新测试程序严格校验loopback origin和POST Origin/referer、方法/路径/query、Content-Type、CSRF/账号/既有合成口令哈希、字段名和单值计数、门店/revision、事前fsync intent及防重账本。未知字段、业务POST、外域、未知GET/PDF均FAIL-CLOSED。route失败具有固定N1—N9码、字段名计数/脱敏未知字段名/payload SHA和断言文件行，abort前落盘。实际route/response失败0。所有敏感值只在进程内使用，公开材料没有口令、CSRF、cookie或session原文。

## NEW_READONLY_P007_SOURCE

唯一来源 `ydental_s10_test_20261016_p007_7c92b4a6` / **OID2100322** / cluster7694897083368259627：

| 固定项 | 核验 |
|---|---|
| config SHA256 | `9ab06779590e31bd372e6880cc406ffd6fe08ed78b41f1786700530fb7bb3db7` |
| marker SHA256 | `065e25e24b5786a60963330943f1b4db2c8a983101e0ab5fab9d3bf4e81522d8` |
| filestore | 194文件逐SHA全等，manifest `27174fa6aa277611a62f4feaf8deb65701d5bbd0d38f91b7966a9b90f0901372`；1075附件指针 |
| 表/schema | 643public/265受管完整行签名全等；schema `3e2c00487260472ad97ca84a68b7e4c1717364715df7e930ecba6ac766f70b1e` |
| 模块/模板 | 702模块/92 installed、全部view/有效语言QWeb、权限全等 |
| P0-07 verification | SHA `5118bb12bc712bc9a326b335066a2c057ae9e83936c43b7855adafcf00e45a1d` |
| P0-07 before-after | SHA `63de2e86f97daf6ded2c9fb33e60135adb1e8431b7ccef727ab59b9bcefda4b9`；严格对真正after和私有停止快照 |

来源在开工、CREATE前、停止后独立只读重验均全等；R3/P002/P003/P004/P006/P007六座历史库OID及原封存表/schema/module/view/filestore前后均一致、无活动连接。没有使用更早P0-06 before代替P0-07停止态。

只读SQL确认：退款13 requested/store1/1.00，总序52、第二页第2条；门店1共63条，第一页 `[66,64,63,62,60…15]`，第二页 `[14,13…2]`。门店3仅退款61及1，均done。user6/store1和user14/store3有本身settlement write，user14无store1授权。门店1无未付invoice/未出账fee/pending，门店3未付invoice5/6/8/9、无未出账fee/pending。此为SQL事实，不是退款页面可见性实证。

## 实际执行与新的STOP

唯一新库 `ydental_s10_test_20261016_p008_8d43a1e5` / **OID2100323** / 127.0.0.1:**18291**，一次autocommit/IDLE CREATE从OID2100322克隆；独立marker/config/data_dir/filestore/dbfilter，权限700。克隆初始643/265、schema/modules/views、194文件和1075指针全等才启动。

唯一HTTP PID **4088027**加载92模块并就绪；唯一Firefox **Python执行器** PID **4088170** 启动。先检查新库渲染的真实form.action/method/enctype与控件name/type/hidden/required/disabled，六字段结构符合预检；保存fsync intent后，user6本人唯一POST `/web/login`，原生服务器返回303、后继 `/ydental/access` GET200。五份现有资产HTTP响应长度/SHA与事前固定文件相等，翻译GET200，route/response错误0。

随后 `Browser.login()` 调用 `scope(page,6,None)`；`scripts/s10_p0_08_browser.py:239` 断言预期store=None/revision0，但实际本人新session184为 **user6/store1/revision1**。原始异常是空消息 `AssertionError`，其文件/行由私有完整trace保全；交付分类码 **`P008_POST_LOGIN_SCOPE_EXPECTATION_MISMATCH`** 为停止后根据trace及独立SQL分类，**不是运行时已经输出的failure_code**。

源码 `ydental_access._session_for_key()` 会在创建会话后消费 `_get_default_store_id()` 的合法建议并调用 `_switch()`；S03供应模块及既有测试模块有该钩子实现。实际原生选店事实由审计2692和session184明确证实，具体默认门店provider未埋点，不冒称已有动态调用栈。新增审计仅：

| ID | actor/store | event/source | target/result |
|---|---|---|---|
|2690|6/null|login/native_authenticated_login|res.users 6/accepted|
|2691|6/null|login.scope/authenticated_session|ydental.access.session 184/accepted|
|2692|6/1|store.switch/interactive|session184；before store=False/after store=1；accepted|

原生自动选店不是第二个HTTP POST。显式switch POST0，user14登录0。登录后逐字段Web元数据门禁已经通过；本次停止是执行器scope判据与原生行为不匹配，不能称产品权限拒绝或资金越界。

**测试覆盖缺陷：** FakeOps虽然复用execute_pipeline和request/audit/DOM门禁，但人工生成“未选店/revision0→显式切店”的会话，没有调用真实 `Browser.scope()` 或覆盖原生默认选店分支。因此69项模拟不能证明完整本人登录/切店路径。route错误码改进也没有覆盖所有非route断言；本次scope异常仍是空消息，不能宣称“所有运行时错误均已带明确码”。以上缺陷在STOP后只报告，未修改执行器、补白名单、再登录或换库。

Firefox执行器exit1，finally关闭browser返回；原生Firefox子进程PID/独立exit未采集，不将Python PID冒称原生PID。HTTP正常停止exit0，本次Odoo signal11=0，历史native根因仍UNKNOWN。两个记录的执行器PID停止后均不存在，来源/新库无活动连接。

## NEW_REAL_WEB_REFUND13_PAGE2 / NEW_REAL_WEB_STORE3_LIST

**均 NOT_RUN。** user6退款第一页、真实“下一页”及ID13页2DOM/截图均未发生；user14合法独立登录/本店退款节点隔离同样未运行。结算请求账本为空，服务器结算GET0/POST0，截图0/PDF0。实际成功登录和SQL选证均不能替代这两个业务断言，不申请原T05/T10/T14或S10阶段技术PASS。

## WEB_READ_AUDIT_GATE

事前冻结user6两个GET读审计0；user14单GET必须恰4条actor14/store3/account.move/5,6,8,9的invoice_view，旧audit2671模板及实际GET逐条绑定。source_view/pending_event_view0，总S01≤10；session/device/user_log各≤2且每actor≤1，按旧行模板逐字段限制；mail/通知/tracking0；全部旧行全等。

实际无结算GET，新invoice/source/pending阅读审计0；新增S01仅上述3条身份审计，新session184/device8/user_log8各1。全部符合事前许可，但不能称逐GET阅读审计已完成。资产沿用五个固定文件，附件/文件/checklist新增0，194文件/1075指针全等，无Web后许可扩张。

## NATIVE_FINANCE_AND_BUSINESS_UNCHANGED

克隆初始→失败停止快照：**639/643张表全等，仅四张身份元数据表变化**：res_device_log +1、res_users_log +1、ydental_access_session +1、ydental_access_audit +3，旧行全部原样。逐字段门禁PASS。停止快照→停机后独立只读再次实测 **643/643及受控逐行数据全等**。

全部159张account_*/stock_*、14关键经济表、所有refund/close/receipt/mutex及其余YDental业务/权限/schema/module/view/filestore原样；mutex244、receipt242/243、退款14 rejected、日结9 unlocked保持不变。全部原生资金、库存及结算业务写0。这里只是保全PASS。

## SIMULATED_PASS 与真实验证边界

| 检查 | 实际结果 | 局限 |
|---|---|---|
|同控制路径FakeOps|1正68负=69符合预期|原生默认门店和真实scope未覆盖|
|Chromium安装态表单/真实route与退款DOM|17例符合预期|模拟HTML，非Odoo Web；Firefox0|
|同note_response五资产响应＋损坏反例|6例符合预期|拦截的合成响应，非现场资产结果|
|真实Odoo20 CLI parser|PASS|只解析配置，无registry/服务；无升级/安装/init/prepare/shell/test|
|新库真实user6登录|POST303/后继入口GET200|只user6，不是两个账号完整会话流程|
|真实退款页/跨店列表|NOT_RUN|scope断言先停止|

构建期离线route回调参数默认值误用已纠正；补充响应模拟曾直接导航字体触发合成下载、一次未等待回调结束即断言；原失败文件保留，改用fetch并等待回调后通过。均在CREATE前完成，不隐藏失败、不记为真实Web。正式预检冻结后八份脚本SHA完全未变。

## 资源、交付与STOP

| 预算 | 实际/上限 |
|---|---:|
|CREATE/Odoo HTTP/Firefox launch|各1/1|
|身份POST尝试/放行/服务器收到|各1/4，只有user6登录|
|显式切店POST/user14登录POST|各0|
|结算工作台GET|0/3|
|结算POST/_operate路径/业务资金库存写|各0/0|
|upgrade/install/init/prepare/shell/sudo|各0/0|
|截图/PDF|各0|

正式预检JSON SHA `b17a7f2da9349eeb1c38092dff44e57feee921836161b113e497a77f68b3609e`；机器索引见 [verification.json](evidence/s10-p0-08/verification.json)，完整前后签名见 [business-before-after.json](evidence/s10-p0-08/business-before-after.json)。原始快照、trace、请求/响应、intent和日志仅保留于权限700私有目录，公开仅脱敏结构/事实与SHA。

正常快进提交并推送原分支，在#34发表 `[CODEX] S10-P0-08 BLOCKED与复核申请`，API逐字读回后立即STOP等待GPT。最高申请BLOCKED、原生user6登录和保全事实独立复核；不自行启P0-09。S10整阶段技术/生产继续BLOCKED，#34 OPEN、#35 S11 NOT_STARTED，旧native SIGSEGV根因UNKNOWN。没有用户最终统一验收或生产批准。
