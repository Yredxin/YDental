# S10-UI1-R5 负向 Web：BLOCKED

授权为 #34 评论 6183901946；强制预检为 #34 评论 6184273529，API 逐字读回。固定起点 `3e2f863d089d1df4bf979eb99624a84abbfad292`、origin、分支、core、S10/S07/controller/QWeb 身份均匹配。产品源码、ACL、core、旧测试与旧库未修改。

## 已执行

- 离线：实际 `create()`/CLI 的 Fake SQL、非空文件复制、marker 尾部校验及失败门禁；实际 Playwright 请求函数的本人 access 页 CSRF/revision、跨角色和缺凭据拒绝、错误 CSRF 发出、响应分类、金融状态门禁。初版离线 `SIMULATED_PASS`；本次暴露的 `event()` 参数冲突修正后再次 `SIMULATED_PASS`。模拟不等于真实 Web 通过。
- R4 源库 `ydental_s10_test_20261015033000_a4c82d17` / OID2100265 只读核验；150 个 filestore 文件与附件指针完整，配置和 marker 与授权一致。一次 CREATE 得到新库 `ydental_s10_test_20261015043000_e7b04c13` / OID2100266 / cluster7694897083368259627。独立 marker/config/filestore，继承账务逐行一致。
- 唯一 Odoo HTTP PID3271725 启动就绪，受控停止 exit0、signal11=false、未超时。第一次浏览器启动包装器在导入 `s10_ui1_r2_contract` 前失败，没有 Playwright/Firefox。第二次包装器修正导入路径后启动了本批唯一 Firefox；manager、frontdesk、reader 各自重新登录，三个 store switch 为登录定位到 A 店的会话准备，非授权的 A→B→A 竞态步骤。只读 reader 页无 bill 写入表单，使用本人 `/ydental/access` 的 CSRF/revision 发出真实 `POST /ydental/settlement/action`，Odoo HTTP 日志记录 403，安全拒绝日志为 actor8/settlement.action。浏览器函数已解析到含 error 的 JSON403；但在落盘该请求结果时，`event('negative_request', label=label, ...)` 与 `event(label, ...)` 参数冲突抛出 TypeError，故此项为 **部分 HTTP 证据，未完成完整断言，不能称 Firefox PASS**。
- 失败后立即停止 Odoo，未重启浏览器。只读比对新库与 R4 源库的完整 account.move/account.move.line、原生 payment/partial、S10 payment/refund/close/receipt 行均相同；receipt8、account.move5、原生 payment2、partial2、mail.mail0、Bus30。S01 审计234→247，新增13条均为登录、会话、切店与只读 invoice_view；拒绝以安全日志保存，未出现新业务审计或 PDF export 审计。未知外发未发现。原生资金未变。

## 阻断与实际范围

本批 Firefox 额度已用尽，所有剩余真实场景 **NOT_RUN**：front JSON409、无效 CSRF 框架400、reader receipt/refund PDF 直链403、manager A→B→A stale revision409、一次撤权及其后当前 revision403、旧 HTML 表单303失败反馈、伪造 notice、>50 Web 分页。授权的三个业务状态变更实际0；新增资金/导出成功事务0。不能由 R4 旧 PASS、初版模拟通过或该次 HTTP403 推定其余结果。

测试夹具已离线修复冲突并强化 Fake 的真实 `event(label, **kwargs)` 签名。修正后的浏览器脚本未在真实 Firefox 中运行；新库 marker 锁定的是失败时原脚本 SHA `ed157d1d8af27601903b95b8920983d7100ee9466385a614e868bd0e9ababf6b`，原字节只保存在私有新库目录 `browser-executed.py`。不得改写 marker 或将修正后离线 PASS 冒称真实恢复。首个启动包装器导入失败和实际浏览器 TypeError 的原日志均保留。

资源实际：新库1/1、Odoo HTTP1/1、Firefox1/1、模块升级0、正向财务/PDF0、manager A→B→A 0、权限撤销0。全部历史数据库、PDF/PNG、filestore、marker/config、日志和事故证据保全。S10 完整技术与生产仍 BLOCKED；旧 Native SIGSEGV 根因 UNKNOWN；S11 NOT_STARTED。等待 GPT 独立复核及下一批明确裁定，不自行重试。

脱敏机器摘要见 [`verification.json`](evidence/s10-ui1-r5/verification.json)。
