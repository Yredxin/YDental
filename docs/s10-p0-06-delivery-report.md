# YD-N1 R1 S10-P0-06：两项真实 Web 限定交付，申请 GPT 独立复核

本批 Codex 自测完成 user14 跨店权限拒绝及 user6 旧日结9唯一合法解锁，申请 **`S10_P0_06_OLD_CLOSE9_CROSS_STORE_DENIAL_UNLOCK_SCOPED_TECH_PASS`**。这不是 GPT 独立通过、用户验收或 S10 整阶段通过；**S10 技术和生产仍 BLOCKED**，历史 native SIGSEGV 根因仍 UNKNOWN，S11/P0-07 未启动。

唯一授权为 [6206287878](https://github.com/Yredxin/YDental/issues/34#issuecomment-6206287878)，上批 GPT 独立复核为 [6206249428](https://github.com/Yredxin/YDental/issues/34#issuecomment-6206249428)。原分支 `codex/s10-settlement-finance-r1-20261013` 从唯一 HEAD `59c777bcb6579f8a320c4e5633cc050b329659a1` 正常前进；Odoo20 core 固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。固定交付 SHA 见 #34 最终回执。唯一 [CREATE 前检查点6206511470](https://github.com/Yredxin/YDental/issues/34#issuecomment-6206511470) 经 API GET 逐字读回，随后 `checkpoint()` 独立核验正文、预检 SHA、全部7份脚本 SHA 和实际 argv 才进入 CREATE。

## 本批自己的来源及门禁

API 完整取回 #23 当前正文/3评论、#34 当前正文/193评论及 #35 OPEN/0；保存全部正文、逐评论 ID/更新时间/body SHA 和全文分节索引。单独核本次授权及 P0-04/P0-05 授权、交付、复核；CREATE 前重新 GET 本授权相同，完整193评论重取相同，没有后续并行授权。未用 P0-05 的旧62位错误哈希或旧预算继续运行，未改任何旧授权、脚本、报告或原件。

本次只读实机验证唯一 P0-04 来源 `ydental_s10_test_20261016_p004_9a6e37f2` / OID **2100320** / cluster `7694897083368259627`：

|来源项|新一轮实测|
|---|---|
|完整64位 config SHA256|`578a1304e65dab36440c6e51374276903f9d7b9ba989e4b75697c1fb9ae62abc`，与新授权/原marker/固定JSON相等|
|marker SHA256|`8afd6122428c723fafa597536c64f146b5b5a339bbb866229d8660f648173f29`|
|filestore|194文件逐 SHA 相等，manifest `27174fa6aa277611a62f4feaf8deb65701d5bbd0d38f91b7966a9b90f0901372`；1075附件指针/文件SHA1核对|
|数据库|643 public 表完整行签名、265受管表、schema、702模块/92 installed、全部view及有效语言QWeb与P0-04停止后封存全等|
|schema SHA256|`3e2c00487260472ad97ca84a68b7e4c1717364715df7e930ecba6ac766f70b1e`|
|资金、权限、业务起点|退款14 rejected/approver6/审计2661、旧receipt242 refund_reject/无实退贷项、mutex XMLID唯一ID1 revision243；日结9 store1/cashier5/2026-07-15/card/latest cycle1 confirmed，gross/refunded/pending均0|
|真实角色|user6 store1及user14 store3各有 settlement+finance_approval write；user14无store1授权|

R3 OID2056451、P0-02 OID2100311、P0-03 OID2100319、P0-04 OID2100320 的表/schema/module/view/filestore分别与各自真正封存原件相等，marker/config只读保存SHA，来源均无活动连接。P0-04公开 `blocked.json` SHA `1738cbd133eda97234ab621f4bc622e5301b8cbaa9330a958e94e9d97b463e1a`、`business-before-after.json` SHA `5b99aa655057a3e54c06aefbb17aa9d9e552cac4ea69940931412b96873c26a7` 独立核对，采用其中 **after** 签名。本次 SQL 连接显式只读/REPEATABLE READ，退出即关闭，没有 Odoo shell。

来源实际 SQL 按 `_workbench()` 的 company/state/type/residual/source 域确认：门店3未付 invoice 仅 **5/6/8/9**，门店1无未付 invoice；两店未出账 fee、pending event 均为空。依据固定 `_workbench/_audit` 源码及旧审计2671—2674，在 CREATE 前冻结每次 actor14/store3 合法页面 GET 的4条 `settlement.invoice_view` 字段模板、最多2次GET/8条；user6最多3次GET、读取审计0条。每次原始 request 事件、GET状态和独立前后 SQL 将新增audit ID绑定目标，不豁免整表或事后补白名单。两账号已完成过首次登录，新 mail tracking 许可为0；登录、session、device、用户/HR写元数据、原生资产与checklist另按源码和既有对象字段/上限约束。

## 离线验证与正式冻结

最终正式预检 [preflight.json](evidence/s10-p0-06/preflight.json) SHA256 **`53318e2f73b0efce62dc8f7ebc43f9ca3716660db514198e42108c4eea7d88f4`** 固定7份脚本、来源643表/资金签名、权限、逐字段许可、唯一目标和预算。

- 同 `execute_pipeline()` 主控制路径的 Fake 2正例/58反例，共60项符合预期；涵盖来源/克隆、HTML/权限、旧退款与user10重放、重复POST/key、响应丢失、收据/fingerprint/mutex、金额/财务/库存、module/ACL/asset/mail、invoice_view的GET/actor/store/target/数量和旧审计不变。
- 同 `stable_cross_form()`、`Browser.submit()` 及 request 事件的 Playwright 模拟10项：Chromium+本机临时合成HTTP fixture，旧 `[value="63"]` 修改后失配负例、稳定节点63→9正例、303拒绝→GET200、重定向GET捕获及6个字段反例全部符合预期。**离线没有使用 Firefox 或 Odoo**。稳定引用用固定 `data-p006-form`，修改后再次比较同一 ElementHandle，CSRF/revision/key/output/operation逐项不变。
- 实际 Odoo20 CLI parser 解析与 HTTP 精确一致的参数结构，仅 `odoo-bin -c <独立配置>`；无 upgrade/init/install/prepare/shell/test，cron0/workers0/loopback/SMTP禁发。

构建阶段原失败保留在私有新目录：一次只读探索误用不存在的 `ydental_store`，随后由 information_schema/实际源码确认 `ydental_access_store`；初稿持久化JSON的list与内存tuple直接比较失败，改为相同JSON表示比较；route.fulfill的303不会再次触发route拦截，离线fixture改用本机合成HTTP，真实GET记录改用request事件。上述均在正式检查点和所有真实资源/业务动作之前完成，未放宽任何资金、权限或审计字段。未发布候选预检保留原SHA，最终版重新完成全部离线和来源门禁；真实窗口后运行脚本 **零修改**。

## 唯一新库、真实动作与逐GET审计

新库 `ydental_s10_test_20261016_p006_4e8a91c7` / **OID2100321** / loopback **18289**。CREATE前库/目录不存在、端口bind空闲；一次 autocommit/IDLE `CREATE DATABASE ... WITH TEMPLATE ...`，只复制P0-04来源。新config/marker/data_dir/filestore/dbfilter独立；克隆初始全部643表、265受管/schema/module/view、194文件/1075指针与来源全等。

|分项|证据级别及实际结果|
|---|---|
|HISTORICAL_REFUND14_REJECT|P0-03旧证据只读保留，任何退款14 POST=0|
|HISTORICAL_USER10_DENIAL|P0-04旧证据只读保留，user10 POST=0|
|P005_CONFIG_TYPO_CORRECTED_NEW_AUTH_ONLY|使用P0-06新64位授权，未修旧批或恢复旧预算|
|NEW_READONLY_P004_SOURCE|本批完整实机只读PASS，旧13条P0-04审计属于克隆基线|
|NEW_USER14_CROSS_STORE_DENIED|user14本人store3原生form63，稳定节点改目标9，独立验证本人cookie对应scope182/revision1、CSRF/新key/理由；先fsync intent后一次HTML POST **303**，跳转 **200**、可信拒绝反馈；服务端 actor14 settlement.action denied；close9/refund14/mutex243/receipt及财务库存不变|
|NEW_USER6_CLOSE9_UNLOCK|仅A完整门禁PASS后，user6本人store1/scope183/revision1，真实点击 `closes_page=2` GET **200**、旧confirmed9和原生form可见；先intent后一次HTML unlock9 POST **303**、跳转 **200**、可信accepted；confirmed→unlocked、unlocked_by6、非空实际理由/时间|
|COMMAND_RECEIPT_MUTEX_FIELD_GATE|mutex唯一ID1仅revision **243→244**；旧242收据全等，仅新增 **receipt243** actor6/store1/unlock；实际HTML key与独立SHA256公式一致、result精确 `{"close_id":9,"state":"unlocked"}`；S01 unlock accepted **2689**|
|NATIVE_FINANCE_UNCHANGED|全部原生account/stock表及14经济关键表完整行签名相等；退款14、所有其它日结/退款、来源/收款/更正/库存不变，无原生出款或贷项|
|SIMULATED_PASS|仅前述60主流程模拟、10项DOM/HTTP模拟与真实CLI parser，不冒称Odoo业务实测|
|NOT_RUN|新收退款/出账/贷项/再日结/库存；upgrade/install/init/prepare/shell；其它S10差距、sudo/系统安全专项、S11/P0-07/部署/合并|

日结9的 store/cashier/date/channel/cycle/currency/confirmed_at/gross/refunded/pending 全部不变，只有预先许可的6字段变化。receipt243 fingerprint 为 **`602cb7f0397662e80f1fd6a88a609c602ee50693997fd9cf1e49f21c172d3a0e`**。实际理由为 `P0-06 synthetic finance unlock review`，实际key仅私有保存，公开仅SHA。无权请求不产生receipt或推进mutex；该产品拒绝只写服务端日志，**没有S01 denied行**，不伪造补数。跨店拒绝判断同时依赖有效本人scope/CSRF/revision/key、来源确认证据、固定 `_unlock()` 的 store不等AccessError条件、303可信拒绝及独立资金/命令不变，未仅凭303判定。

|真实GET|actor/store|HTTP|新增invoice_view审计ID→account.move|
|---|---|---|---|
|第一次工作台|14/3|200|2678→5、2679→6、2680→8、2681→9|
|拒绝303后的实际GET|14/3|200|2682→5、2683→6、2684→8、2685→9|
|工作台第一页|6/1|200|0|
|点击closes_page=2|6/1|200|0|
|成功303后的实际GET|6/1|200|0|

S01新行合计 **15**：user14 login/login.scope/store.switch **2675—2677**，invoice_view **2678—2685**，user6 login/login.scope/store.switch **2686—2688**，唯一unlock **2689**。旧审计全部原样。新device/user log各2、新scope182/183；mail tracking、用户/HR、asset/attachment/filestore、ORM signaling均无新增变化。643表中 **636表完全相等，仅7表许可内变动**：res_device_log、res_users_log、ydental_access_audit、ydental_access_session、ydental_settlement_close、ydental_settlement_mutex、ydental_settlement_receipt。

## 停机、进程、保全及预算

唯一 Odoo HTTP PID **4034790** exit **0**；唯一 Firefox **Python执行器** PID **4035021** exit **0**，pageerror0、`browser.close()`正常返回。原生Firefox进程PID/单独退出码没有记录，不把执行器PID冒称Firefox子进程PID。本批无Odoo SIGSEGV，不意味着旧native根因已修复。HTTP日志SHA `eed06717438b6eef14562d14f91deee39c9adc3f66e17d44712ee0ea7db71985`；浏览器执行器日志为空文件SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

独立停机后读取目标与 `final-snapshot/stopped-readonly` 全等；四个历史来源再次与原封存完整核对，所有五库OID对应正确、无活动连接。两次登录和两次切店POST也各有不可覆盖intent、实际HTTP状态和独立SQL观察；请求拦截器只允许这4次及两笔目标unlock，记录器实际共 **6 POST / 5 workbench GET**。所有响应/提交没有未知或重试，没有换库重做。

|预算|实际/上限|
|---|---:|
|CREATE / Odoo HTTP / Firefox launch|各1/1|
|user14跨店unlock9 POST|1/1|
|user6合法unlock9 POST|1/1|
|user10 / refund_reject POST|各0/0|
|新资金/贷项/出账/再日结/库存|0/0|
|Odoo upgrade/init/install/prepare/shell / sudo|各0/0|

可审材料为 [脱敏机器索引](evidence/s10-p0-06/verification.json)、[643表/265受管表前后签名](evidence/s10-p0-06/business-before-after.json)、[最终事前预检](evidence/s10-p0-06/preflight.json) 和7份新脚本。原始CSRF/key/cookie/HTTP/session/截图/日志仅留权限700的 `.local/s10-p0-06/` 与独立目标目录；截图实际查看，公开仅SHA。无历史库/脚本/证据、产品addon/core/ACL、Project/Issue状态修改，没有合并、强推或部署。

正常提交并推原分支，在#34发布 `[CODEX] S10-P0-06交付与GPT独立复核申请`、API逐字读回后立即STOP。只申请本批两项限定技术复核，不自行启动下一批。
