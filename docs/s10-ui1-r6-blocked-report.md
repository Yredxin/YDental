# S10-UI1-R6 剩余负向 Web：测试执行器阻断

## 依据与身份

唯一授权为 [#34 评论 6184420329](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184420329)，R5 独立复核为 [评论 6184367704](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184367704)。已通过 GitHub API GET 读取 #23/#29/#31/#34 当前正文及全部有效评论，#35 OPEN/0；开工前 #34 最后评论为本批授权。固定起点和远端均为 `fc04662455528d6906370dbf15a3445faf6a9813`，原分支及工作树符合授权。core、S10/S07 service、controller/QWeb 哈希均与授权相符；产品文件未改。

强制[预检 6184494471](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184494471)在 CREATE/Odoo/Firefox 前发表并经 API 逐字读回。预检中的实际 `run()` 全流程 Fake 模拟和 create/CLI Fake PG 路径均 `SIMULATED_PASS`。模拟写入 15 条真实事件文件，覆盖 7 个负向场景、2 次经理切店、一次撤权、HTML 反馈和伪造 notice；事件写入失败、意外成功、错误状态、缺字段、资金变化、缺控件均阻断模拟完成标记。模拟 DOM **未模拟原生 `<input type="date" required>` 的浏览器提交约束**，因此不能替代真实 Firefox 验收。

## 单次真实运行

唯一只读克隆源为 R4 合成库 `ydental_s10_test_20261015033000_a4c82d17` / OID2100265。CREATE 一次成功，目标 `ydental_s10_test_20261015052000_b6d2a94f` / OID2100267 / 端口18275；新 marker、config、filestore、strict dbfilter 及继承财务基线均校验通过。唯一 Odoo HTTP PID3282173 正常停止 exit0、无 signal11/超时。Firefox/Playwright 仅启动一次；浏览器执行退出码1。

| 场景 | 本批结果 | 证据边界 |
|---|---|---|
| reader 自己的 CSRF/revision，无写表单但真正 POST | 真实 HTTP PASS（403） | JSON `access_denied`；资金前后相等 |
| front 未知 operation | 真实 HTTP PASS（409） | JSON 未知操作错误；资金前后相等 |
| 无效 CSRF | 真实 HTTP PASS（400） | Odoo 框架拒绝，`text/html`；资金前后相等 |
| reader receipt/refund 直链 | 真实 HTTP PASS（403/403） | 无 export grant；没有 PDF 导出审计增加 |
| manager A→B→A，旧 revision | 真实 HTTP PASS（200/200，旧请求409） | `version_conflict`；资金不变 |
| front 本店结算 write→read 后当前 revision | 真实 HTTP PASS（grant200，POST403） | 实际授权行 read，`access_denied`；资金不变 |
| 撤权前旧 HTML 表单 | `BLOCKED_TEST_HARNESS` | `expect_response` 等待 POST 30 秒超时；Odoo 日志没有该次 POST |
| 旧 HTML 303/失败反馈、伪造 notice | `NOT_RUN` | 上述超时触发 STOP |
| >50 条真实分页 | `NOT_RUN` | 无合法数据且不伪造财务记录 |

HTML 阻断的**静态归因**：脚本取到 `close` 表单后只点击提交按钮，未填写该表单 `required` 的 `business_date`。浏览器可在表单校验阶段拦截提交；实际 Odoo 日志最后一个结算 POST 是撤权后的403，没有旧表单 POST。这是当前证据支持的测试夹具解释，未取得页面原生校验截图，因此不把解释写成已实测根因，更不宣称产品缺陷。按“测试进程异常即 STOP”条件未修改脚本并重试。

## 资金、权限与审计

失败后只读核对源/目标：原生 `account_move` 5、line10、`account_payment`2、partial2；S10 receipt8、payment1、refund1、close1，全部逐行一致。PDF 导出审计均3；mail.mail 均0、Bus 均30。front A settlement 授权从 write 合法变为 read；这是唯一 grant 变更。S01 audit 234→262：`authorization.change`+1、`login`+3、`login.scope`+3、`store.switch`+5（含三角色初始切店及经理另两次）、`settlement.invoice_view`+16。拒绝日志未冒充持久 S01 拒绝审计。没有成功资金动作、PDF 导出、模块升级、业务准备或产品代码变更。

## 保全与结论

R4 OID2100265、R5 OID2100266、本批 OID2100267 及更早历史库、filestore、marker/config、原始私有日志和浏览器事件均保留。机器脱敏索引见 [verification.json](evidence/s10-ui1-r6/verification.json)；私有原件哈希在索引内。R6 是 `BLOCKED_TEST_HARNESS`，已完成的前述负向仅为本批有限真实 HTTP PASS；旧 HTML/伪造 notice 和分页仍 NOT_RUN。S10 完整技术及生产继续 BLOCKED，旧 Native SIGSEGV 根因 UNKNOWN，S11 NOT_STARTED。等待 GPT 独立复核后决定是否另批授权；本批不自行重试、修改产品、改 Project/Issue 状态、合并或部署。
