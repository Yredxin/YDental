# S10-E2E-W2-G0 只读恢复可行性审查

授权：[#34 / 6185093001](https://github.com/Yredxin/YDental/issues/34#issuecomment-6185093001)。本批仅审查 W1 已提交现场；未创建数据库、启动 Odoo/Firefox、调用业务服务或写入业务数据。机器快照见 [verification.json](evidence/s10-e2e-w2-g0/verification.json)，由固定目标且显式 `transaction_read_only=on` 的 [审计脚本](../scripts/s10_e2e_w2_g0_audit.py)生成。`OBSERVED_READONLY` 是数据库事实；以下源码判断均为 `STATIC_INFERENCE`，没有 Web 复现。

## 版本与来源

- 原分支本批起点、本地及远端 HEAD：`7039ed65204b0f23b40e438fd69aa962daa4caa7`；开工工作树干净，origin 为 `Yredxin/YDental`。Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。S10 service blob、S07 service SHA256、S10 controller/QWeb SHA256 均与授权全文相同。
- 唯一业务库 `ydental_s10_test_20261015051000_e2e1a7b4`，OID `2100269`，cluster `7694897083368259627`。独立 config SHA256 `f0a8ad4d715e4a6f316d7c1117e39ce9f743953284af2fa7088ce3eb66feed86`；marker/OID/严格 dbfilter 相符。150 个 filestore 文件形成清单哈希；164 个数据库附件指针均匹配实物 SHA1。同一附件文件可被多条指针引用，不以指针数充当文件数。15 张业务/审计表的完整行内容仅记录 SHA256，不公开患者文本、token 或 session hash。
- GitHub API GET 完整取得 #23/#29—#34 正文和全部有效评论：#34 本批开工时 145 条，最后评论仍为本批唯一授权，未见后续交付或并行执行；#35 OPEN、0 评论。W1 独立复核 [6185046690](https://github.com/Yredxin/YDental/issues/34#issuecomment-6185046690) 已核对。

## 已提交事实 `OBSERVED_READONLY`

- 同一合成患者 ID1：治疗 event1 `confirmed`，fee1 = 600.00，冻结 snapshot1 数量1、单价600.00、金额600.00；event、fee 均指向 snapshot1。原生 stock.move3 `done` 数量1，对应 inventory.event3 `treatment/done`。inventory.event1/2 各20入库是 W1 准备动作。`treatment.actual_execution`、`inventory.movement` 与 `clinical.save` 均有 accepted S01 审计。
- 检查 order1 `exam/issued`、line1 `issued`，均关联原 execution1、当前 document1/version1；line1 指向 task2，task2 `pending`，与 task1 为同一患者。`treatment.order_issued` 审计存在。task2 无 queue entry、无 active position、无 examination result；未报到、未叫号、未接诊。
- 原 task1 `started`，execution1 `serving`、entry1 `serving`；没有 queue hold。唯一 lease1 对应医生7/工位9，数据库原值 `active=true`、到期 `2026-10-15 05:24:33 UTC`，审计快照数据库 `now()=2026-10-15 05:29:01 UTC`，已超时。lease 的 session ID11 对应同一用户/门店，revision 1 对1；只能说明数据库修订一致，**不能证明旧浏览器 cookie、连接 key 与 lease token 可供新会话使用**。没有其他 active lease/execution/hold。task1 旧 position1 已 inactive，task2 没有队列位置。
- document1 仍 `draft`、current_execution1、version1；当前内容与 immutable clinical_version1 内容数据库逐值相等。编辑锁的数据库到期 `05:24:03 UTC`，同样早于快照时间。原草稿已保存，但状态不是已确认病历。原生 `account.move`、`account.payment`、`account.partial.reconcile`，S10 source/receipt/payment/refund/close 和检查结果均为0。既有600/库存/价源不可重做或重价。

## S06 业务动作图 `STATIC_INFERENCE`

1. `ydental_queue_service._held` 要求当前登录用户、同一门店 session/revision、同一 browser connection hash、原 lease token 与 active lease 同时满足（[源码](../ydental_queue/models/ydental_queue_service.py:116)）。`_operate` 对过期 lease 先调用 `_expire`，把 `serving` execution/entry 变成 `verify`，并使 lease inactive；这是**未来真实业务动作的预期效果**，不是本批数据库已发生的事实（[源码](../ydental_queue/models/ydental_queue_service.py:136)，[分发](../ydental_queue/models/ydental_queue_service.py:174)）。即便旧浏览器仍有凭据，已过期连接不能直接 reserve/handover。
2. `ydental_intake_service._queue_assert_idle/_queue_accept` 在同一患者存在 `serving/verify` execution 时拒绝 task2 报到；前台不能靠直接报到越过旧执行（[源码](../ydental_queue/models/ydental_intake_service.py:85)）。`_reserve` 仅能由仍持有原 lease/token 的实际执行人对已签发医嘱关联的外部任务操作（[源码](../ydental_queue/models/ydental_queue_return.py:199)，[检查来源钩子](../ydental_treatment/models/ydental_queue_service.py:32)）；当前 lease 已过期，不具备此通道。
3. `_onsite_source/_takeover_verify` 要求有本店写权、合格原工位、**真实物理在场确认**及原因。合法 Web 表单把 `confirmed`、`reason` 设为必填（[服务](../ydental_queue/models/ydental_queue_return.py:111)，[页面](../ydental_queue/views/ydental_queue_templates.xml:74)）。服务器会核冻结服务快照与实际可接管资格。临床钩子只在旧连接无效、编辑锁无效且已保存草稿与 immutable version 一致时允许服务器校验保存（[源码](../ydental_clinical/models/ydental_queue_service.py:21)）；W1 只读数据满足版本一致/超时两项，但实际角色资格与现场确认均未 Web 验证。
4. **恢复后的接续还存在静态限制**：`takeover_verify` 中断原 execution1 并新建 resumed execution；当前 clinical document1 仍指向旧 execution1，源码中只有 reserved hold 的 `_restore` 明确重新绑定 document；直接对新 execution 调用 queue `handover` 会因找不到它的临床文书而触发 `save_required`（[新执行](../ydental_queue/models/ydental_queue_return.py:143)，[文书匹配](../ydental_clinical/models/ydental_queue_service.py:21)，[仅 hold 恢复重绑](../ydental_clinical/models/ydental_queue_service.py:54)）。临床 `_open` 可给新执行创建独立文书，但需要真实医生审核并保存实际内容，不能复制旧文本冒充现场记录（[源码](../ydental_clinical/models/ydental_clinical_service.py:123)）。此后 handover 是否完整成功为 `UNKNOWN`，本批未运行。新 execution 的 ID 不等于原检查 order1 的 `ydental_execution_id`，因此不得假设它还能用 `_reserve` 把原 task2 保留到旧工位；必须按实际后续 Web 反馈判断。
5. 队列页将待办 task2 渲染在 `[data-pending-task="2"]`，其中合法前台报到表单是 `form[data-queue-form="report"]`，隐藏字段 task_id、version 来自服务器（[源码](../ydental_queue/views/ydental_queue_templates.xml:86)）。未来浏览器应先从检查 order1 的 `tr[data-line="1"]` 与业务 line1→task2 关联，再在队列页以 `data-pending-task=2` 交叉核对表单字段与患者/门店/能力；不能从检查卡片读取 `.task-id`。后者只属于药房 segment 列表（[源码](../ydental_treatment/views/ydental_treatment_templates.xml:87)）。不得根据 DOM 文本单独推断患者身份或伪造 task ID。

## 决策表

| 场景 | 事实/推论 | 判定与出口 |
|---|---|---|
| 原浏览器凭据继续 reserve/handover | `OBSERVED_READONLY` 到期；`UNKNOWN` cookie/token 当前可用性；`STATIC_INFERENCE` 下次受控动作先过期 | 当前无可证明的合法接续。不能复用 W1 cookie 标记或重置租约。 |
| 到期后原 execution 进入 verify | DB 仍是 `serving/active`；源码说明受控请求会转换 | **ONSITE_CONFIRMATION_REQUIRED**：只有真实合格人员在原工位核实后，经 Web `takeover_verify` 接管；Codex 不能自动勾选、伪称在场。 |
| 已交还/已被其他真实执行占用 | `OBSERVED_READONLY` 无 handover/hold、无其他执行；task2 pending | 本快照不适用。后续须重读状态，不能把 task2 当已报到。 |
| 合法核实后继续检查 | 版本一致是事实；接管后的新文书、handover 与 task2 报到是静态条件 | `UNKNOWN`，需要新的明确业务授权和真实 Web 证据。当前不能启动 W2-R1。 |

**本批结论：`ONSITE_CONFIRMATION_REQUIRED / RECOVERY_BLOCKED`。** 前者是 S06 现场业务门槛；后者是当前 Codex 无法以获授权方式独立完成恢复，且接管后的文书/交还链尚未真实验证。此结论不等于已发现已复现产品故障，也不等于740全链可恢复。GPT需先决定真人现场核实的责任与后续授权；若没有，停止在此快照。

## 如获后续单独授权的最小顺序（本批 `NOT_RUN`）

1. 保留 W1 库只读，另按新授权核新库/预算；重读 OID、价快照、fee600、move3、order1/line1/task2、lease/文书/审计与 idempotency receipt，防二次治疗/耗材扣减。
2. 真正有权人员在原工位现场核实，按队列真实 `takeover_verify` 及病历工作台检查原保存版本；新接诊文书仅凭真实医生内容保存。若有任何 `save_required`、版本或权限拒绝，保全并停止，不能直接 SQL 改状态。成功结束原段后，前台仅用 task2 的服务器 version 报到检查，按本店能力真实叫号/接诊。
3. 检查工作台对 line1 实际执行、独立结果文书及费源80逐 ID 核对；医生真正开具并签发处方，药房同处方先按真实批次发4、结束段、再次报到后发2，核每次原生库存 move/费用40+20。每一成功动作使用页面自身 revision/CSRF/稳定幂等 key，重放先核 receipt；不得重开治疗600或检查单。
4. 财务工作台只选择真实费用 600+80+40+20 出账740；核 posted 原生 invoice、来源唯一、价格快照与审计，再分别实际收500和240，核原生付款/核销/余额0。此步骤不因 G0 静态推论而获准执行。

本批 Odoo/Firefox/新库/业务 COMMIT/模块升级均为 **0**；没有 PDF、检查、药房、740/500/240 的真实 Web 验收。历史库、filestore、日志与 W1 现场未修改。S10 完整技术与生产继续 BLOCKED；旧 Native SIGSEGV 根因 UNKNOWN；S11 未启动。
