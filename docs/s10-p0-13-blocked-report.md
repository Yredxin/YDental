# S10-P0-13：一次原生登录/文书读取后 STOP，确认未执行

**本批结果为 Codex `BLOCKED_NATIVE_DOM_AND_LOGIN_AUDIT_CONTRACT`，申请 GPT 独立复核。** 唯一新克隆已创建，本人 user7 完成原生 Firefox 登录并取得既存 doc1 的 HTTP200 页面，随后 DOM 合同断言失败；acquire/confirm/release 均0。doc1 仍为 **pending/version2**，没有 version3。源 W5 前后两条独立严格只读连接实际核验643表全部相等；新克隆639表完全不变，另外4表仅新增登录、scope与读取审计记录，全部旧行保留。经济、费用、价格和库存零变化并不等于文书确认成功或白名单通过。

## 1. 正式依据、Git 身份和范围

唯一授权 [6211098449](https://github.com/Yredxin/YDental/issues/34#issuecomment-6211098449)；固定父 HEAD `cf6692c27d48ebabf1b7d4f3ab1ef99ef4cfef74`，原分支 `codex/s10-settlement-finance-r1-20261013`、origin `https://github.com/Yredxin/YDental.git`。本地、`git ls-remote`和 GitHub REST ref 取得同一 HEAD；core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` tracked 干净。只新增本批许可脚本、报告和脱敏证据；不改 AGENTS、产品、ACL、core 或任何历史文件。

开工通过 API 完整取得 #23 当前正文/3评论、#34 当前正文/220评论和 #35 OPEN/0。交付前再次完整取得 #23/3、#34/221、#35 OPEN/0，原正文/原评论内容均不变，仅新增本批执行预检，无并行新授权或交付。[开工索引](evidence/s10-p0-13/github-start.json)、[交付前索引](evidence/s10-p0-13/github-delivery-read.json)保留逐条长度/SHA/ID；完整 API 原件只保私有目录。P0-12 的正式裁定6211057301保持，不重新复核，也未执行任何 P0-12/P0-11旧入口。

## 2. 唯一预检与冻结

正式预检 [6211482453](https://github.com/Yredxin/YDental/issues/34#issuecomment-6211482453) 已在任何 SQL/CREATE/HTTP/Firefox 之前发表，并通过 **GitHub REST GET 原始正文逐字比较**：9915字符、13721 UTF-8字节、SHA256 `a1606962a139ba92a42071c40e78194155ee1b740071f31307bf50c107f1c1de`。没有 POST 超时或重复发布。[预检正文](s10-p0-13-execution-preflight.md)、[读回凭证](evidence/s10-p0-13/preflight-api-readback.json)。

[机器计划](evidence/s10-p0-13/execution-preflight.json) SHA256 `f3d5a71344b214ff53cd96d0c2d35891f3ad6c285e2a425fa63d3ba96c6a224d`，包含5个执行脚本SHA、完整SQL字面值和643条展开SELECT、目标身份/argv、25资格、627锁定表和精确非经济逐字段白名单。执行前后及证据投影前核对5个脚本SHA全等；没有补充检查点或执行中修脚本/预算/白名单。新增 evidence.py 仅在 STOP 后处理既有文件，无数据库/HTTP/Firefox入口，不属于事后修改执行器。

17项离线检查通过，但覆盖的是初始快照比较器和请求形状，**没有覆盖真实登录后的模板差异、重定向请求计数和缺失 DOM 属性**，不能用17项通过解释为完整执行器合同已验证。准备期间 REST GET 有间歇TLS超时，首次离线检查在空 ref JSON 处失败，之后成功取得 ref；离线封存草稿和日志留私有。STOP 后首次 HTML 解析尝试缺 cssselect，改用现有 lxml XPath；未安装依赖、未再启动浏览器。没有 OS/PG/Docker/防火墙/IPv6安全专项或环境整改。

## 3. 实际执行与资格

|关口|实际结果|
|---|---|
|源前验连接 #1|2026-10-16 08:34:21 UTC，backend1127349；W5/OID2100310/cluster7694897083368259627；643表、47保护/31稳定、152文件/164指针与父血缘封存匹配；finally rollback/close|
|当下25资格|25/25通过：patient1/store1/company1/doc1 pending2/responsible7；execution1 handover/旧lease inactive；user7/member5/employee3/medical-write/capability/公司/患者关系、旧全文/版本和92模块/QWeb均成立|
|独立 maintenance|源前验连接已关闭；postgres autocommit/IDLE，目标不存在、模板无连接、cluster正确；一次CREATE，无重试|
|新克隆|`ydental_s10_test_20261016_p013_6a91d3c8` / **OID2100325** / 18313；独立filestore152文件全等；初始643表与刚才真实源快照全行相等|
|目标前验连接 #1|保持同一物理只读连接；初始一次、HTTP启动后一次、登录POST转发前一次，每次新READ ONLY/RR快照后ROLLBACK，共3个快照；Web结束后关闭|
|原生Firefox|一次启动/一个context；user7原生login POST303；重定向临床GET200一次，页面含原始完整文字、旧2个版本；在初始DOM断言处STOP|
|目标后验连接 #2|停止自有HTTP后独立只读取得全部643表，rollback/close；冻结login-view比较器离线复用结果FAIL，未放宽规则|
|源后验连接 #2|2026-10-16 08:34:39 UTC，独立backend1127441；全部643表、47/31、身份/指针/filestore/config/marker与源前验完全一致；rollback/close；无第三次连接|

当前source→fee外键实际为 **1→4/20、2→3/40、3→2/80、4→1/600**；invoice1 posted/paid740/residual0，历史payment500+240/partial1+2保全，没有重发收退款、日结解锁、权限负向或分页。材料：[源前验](evidence/s10-p0-13/source-before.json)、[25资格](evidence/s10-p0-13/eligibility.json)、[克隆](evidence/s10-p0-13/clone.json)、[源后验](evidence/s10-p0-13/source-after.json)。

## 4. 阻断、DOM/HTTP及审计字段

首个运行失败是 `BROWSER_FLOW_STOP`，底层 `AssertionError` 消息为空；冻结异常处理没有保存完整 traceback 或断言前 evaluate 对象。不能冒称事后恢复了原始运行栈。保存的真实临床HTTP200原文和未改JS足以定位一个确定的合同不兼容：原页面根节点没有 `data-execution` 属性，执行器初始 tuple 却要求 `dataset.execution == '0'`。其他已保存元数据为doc1/revision1/version2/pending/heartbeat2/canHandover no。该属性检查发生在首次截图和Acquire之前，故真实截图0、临床编辑POST0。原文只在本地700目录，[脱敏DOM/HTTP复核](evidence/s10-p0-13/native-dom-http-review.json)明确区分保存HTML证据与未保存的运行evaluate值。

另有**不能掩盖的计数器缺陷**：原 `browser-result.json` 的临床GET计数为0，因为该重定向目标没有进入此次route-handler观察列表；同一浏览器响应和Odoo真实访问日志均证明 **GET1/HTTP200**。原始文件及错误计数原样保留；[verification.json](evidence/s10-p0-13/verification.json)以两份独立原件校正实际预算为GET1，不把计数0当未访问临床。

STOP 后仅离线比较已取得的目标后验快照，发现冻结白名单还有两项不兼容：

- 唯一新增session16确属user7/store1/revision1/create_uid7/write_uid7，但冻结模板取旧user7的首行session，其write_uid为8。规则只许id/key_hash/create_date/write_date不同，故实际 `write_uid 8→7` 不被模板差异列表允许。冻结比较器在该断言失败。没有把模板或实际记录改成匹配。
- 新增5条审计331—335依次为login、login.scope、store.switch、clinical.view、**source.view**。最后一条是medical/source_model/doc1/store1/actor7的真实读取审计，未在冻结允许事件中。即便解决session模板断言，仍有独立审计越界。此次没有取消、删除或重新分类该事实，也没有事后加入白名单。

[逐字段复核](evidence/s10-p0-13/login-audit-field-review.json)固定实际模板差异、5条脱敏审计、全部旧行不变及冻结比较器FAIL。原生读取 `source.view` 的静态入口见 `ydental_access/models/ydental_access_source.py`；本批未改它。源当前资格正确不代表执行器事前模板/事件白名单正确。

## 5. 数据、预算与原生退出码

[全643表比较](evidence/s10-p0-13/all643-target-comparison.json)证明目标只有 `res_device_log` +1、`res_users_log` +1、`ydental_access_session` +1、`ydental_access_audit` +5；4表全部旧行不变，其余639表全行相同。冻结627张禁写表全部相等，文书本身、旧version1/2也完全相等。doc1 pending2、editor空；version3、acquire/confirm/release及其业务效果全部NOT_RUN。该比较不能升级为白名单PASS。

|预算项|实际|
|---|---:|
|W5前/后来源连接|1 / 1（合计2，独立backend）|
|目标前/后只读连接|1 / 1|
|maintenance连接 / CREATE|1 / 1|
|Odoo HTTP / Firefox启动|1 / 1|
|原生login / 显式switch POST|1 / 0|
|真实clinical GET / 原route计数|1 / 0（原缺陷保留）|
|acquire / confirm / release / heartbeat|0 / 0 / 0 / 0|
|其它业务POST / PDF / 资金费用库存写|0 / 0 / 0|
|历史重放 / shell/upgrade/install/init/test / 直接ORM / 执行者sudo|全0|

Odoo自有PID66211退出0；Firefox真实引擎PID66299退出0/signal null；控制器退出0是它捕获并记录了失败，不是业务通过。运行summary持续BLOCKED，目标后验原记录为CAPTURED而非PASS。Firefox pageerror0，但原生stderr有2条NS_ERROR_ABORT、1条NS_ERROR_FAILURE和1条协议dispose错误行，根因UNKNOWN，原件/SHA保留于[引擎诊断](evidence/s10-p0-13/browser-engine-diagnostics.json)，不称浏览器全程无错误。本窗口未记录新Odoo SIGSEGV，不证明历史根因修复。[原执行summary](evidence/s10-p0-13/execution-result.json)、[原浏览器结果](evidence/s10-p0-13/browser-result.json)。

## 6. 字段、动作、用户效果及未运行范围

原生入口为user7本人login→store1/revision1→既存doc1。原Controller按SID绑定scope、当前medical-write/公司/患者关系/原责任/资格，临床操作另校验connection/editor与CAS2。没有执行者提权或直接业务ORM；未改服务器既有受控fixed-model sudo实现。原native JS、heartbeat2秒/timeout600秒未修改；因尚未acquire，没有token和心跳。**不能声称本批实测完成了零heartbeat的确认/自动release路径。**

实际用户效果只有登录并查看pending2原文，随后停止，没有可验收的新确认版本。若用户日后由GPT正式授权另一个新窗口，预期步骤仍为本人登录、合法store1、打开既存doc1、确认原文及旧2版本、Open、Confirm text only、原生自动release、确认版本3和经济不变；本批后5步未运行，不能要求用户在保全旧库重演来补证。

F4/T08/T12完整链、数量更正/退药、同源原版PDF、收退款、日结和权限负向均未在本批重跑。最高限定成功结论没有达到；不申请S10整阶段PASS或自动下批。

## 7. 保全、隐私与回退

新旧数据库、filestore、失败日志、原始HTML/HTTP及冻结脚本都保留；新克隆只含合法登录/读取的既成事实，没有为恢复预期而删审计、回滚记录或再确认。业务回退没有必要的新资金/库存交易；源码只允许正常线性新增证据提交，无reset/clean/强推。源config/marker/父血缘/附件及152文件不变，目标独立filestore亦不变。

私有目录 `.local/s10-p0-13/` 权限700，原运行目录亦700；医疗全文、登录凭据、SID/CSRF/cookie/connection/editor/key、原生HTTP与真实HTML只留本地。GitHub仅发布ID、状态、金额、哈希、字段名及限定审计投影，[私有原件索引](evidence/s10-p0-13/private-artifact-index.json)只含名称/字节/SHA。没有生成真实截图或虚构截图。应用odoo-guidelines与odoo-web-guidelines静态阅读相关原生路径；没有其他执行者。

## 8. 独立复核申请及STOP

请GPT核对本固定提交中的：预检REST逐字读回和5脚本冻结、源连接先关闭再CREATE及独立源后验643表保全、单库/HTTP/Firefox预算、真实GET漏计纠正、DOM属性不兼容、session模板write_uid和source.view白名单失败、文书仍pending2与费用库存资金不变。**请求接受如实BLOCKED和保全证据，不请求把安装/登录/退出0解释为确认成功。** 原始运行完整断言栈缺失也作为证据限制保留。

正常推送原分支后在#34发布`[CODEX] S10-P0-13 BLOCKED与复核申请`，以真实最终SHA链接本报告和机器证据，REST GET正文逐字比较并私有记录ID/URL/字符/字节/SHA后立即STOP。任何未来执行器纠错、原生审计白名单变更或再次confirm均须新的GPT正式授权，本批不自行继续。

S10阶段技术/生产/T12持续BLOCKED；R3 Native SIGSEGV UNKNOWN、W4元数据STOP、W5历史browser exit1/final_audit NOT_RUN、同源原版PDF不足及生产财税/到账待授权全部保留；#34 OPEN、#35 S11 NOT_STARTED、Project0 mutation。最终用户效果验收仍在S13后统一，不合并、不部署、不启S11。
