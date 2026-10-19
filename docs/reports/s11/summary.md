# [CODEX-STATUS] YD-S11-FOLLOWUP-LAB-V1 / 1.0

结论：**PARTIAL / IN_PROGRESS**
Issue #35：**OPEN**
同步：本次继续实施的代码和状态尚未推送；依用户要求只在 plan 结束时发布最终结果与说明。
计划范围：S11-A 复诊和通知可靠性 + S11-B 内部外加工，含补充输入 v1.1。真实外部通知、生产、合并、部署、S12/S13 均未启用。

## 当前候选与运行边界

- 分支 `codex/s11-followup-lab-r1`；当前已提交候选 `22ea0cd73b1a4f1458bf06675f9abf5a690f3d71`；分支比 origin 多56个已提交本地提交，未回退接管时 HEAD `b62cfe5d528f696e8ac8e8e4a266a5c661d0a39c`。该候选已提交但尚未获得匹配的新准入或 Odoo 实测；锁定 Odoo core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。
- 使用的目标为指定 scratch OID 2144130 / cluster `7694897083368259627`。S11 runtime、admission 与 launcher 位于本机忽略的 `.local/s11`，mode 0600；本机凭据不进入 Git、聊天、报告或请求日志。S10 main DB OID 2144129 未安装或写入；未知 8069/PID42433 未操作。
- launcher 在本候选启动过 owned Odoo 服务并执行过只读 HTTP/RPC 和浏览器工作台检查，随后正常停止。外部 SMTP、SMS、供应商、支付均未启用；本地受控 sink 只代表内部测试受理，不代表患者送达。
- 首次安装中的依赖和 Odoo 20 Registry 导入问题已在普通开发中修复；保留两次先前失败及只读保全记录，不覆写历史。当前候选成功完成带数据模块升级和测试，详见下文。

## 已取得的候选匹配证据

- **SOURCE/PURE：** addon、权限、XML、launcher 与依赖检查及本地 launcher 测试曾通过。候选 `22ea0cd` 新增代码的 Ruff、compileall 与 diff 检查通过；不计作实际业务 PASS。
- **MODEL / 安装升级：** `.local/s11/operations/20261019T102519Z-7f03f49-followup-lab-upgrade-test/result.json`：固定候选 `7f03f495db404a700361a156132873563a6bfef0`，退出码0；60个 Odoo post-tests、0 failed、0 errors。日志 SHA-256 `59cb704de7cfc824acfca2cea75d3b8d7485e1109f1c83b0acd41c0c7596617f`。该候选含完整S11产品及T11回归；其后 `43af67a` 只增加扫码竞争取证脚本，无产品或测试代码改动。模块集是 S11 两产品 addon、两 test addon、必要结算扩展及因已安装核心 SMS 功能新增的 `ydental_lab_sms_guard`；没有 `-u all` 或升级 core。
- **T11 / 独立升级后状态：** 新增 `ydental_lab_test.tests.test_t11_exam_continuation.TestS11NextDayExaminationContinuation.test_yesterday_completed_panorama_today_revalidates_cbct`，通过真实 S06/S08 检查、队列、临床、治疗服务，证明昨日全景完成后次日 CBCT 旧任务先拒绝，必须重新接诊并复核后才实际确认；不安装或绕过 `ydental_exam_test` 的 S09-only 门禁。独立读回 `.local/s11/receipts/s11-independent-post-upgrade-7f03f49-20261019T102809Z.json`，SHA `ac950a915ef7c78a991fad737f7f15280c88bf32812fa015ee34905a12acbc05`，确认60项0错、T11用例日志、96模块版本和旧对象投影保全。独立读回确认当前模块数96、旧224项保护计数未下降、S10 D/C 摘要一致、既有 S11 订单/库存/通知/费用来源投影未变。该证据注明旧行内容的限制，计数不等于逐行全库证明。
- **通知任务：** job450 的原稳定 request-id 在候选 6706 同 key 恢复；独立读回 `.local/s11/receipts/s11-independent-job450-same-key-recovery-readback-6706bc7-20261019T095200Z.json`，SHA `7211f9d83d06b1566cb7701bfbb0bbbcaa8a7d5ba3127167d8b5447844004e7f`。任务 accepted、delivered=false、attempt=1，新增一条指派给负责人的内部 vendor activity；`mail.mail` 不变；SMTP/外部 provider 仍关闭。另有先前候选的真实双连接领取结果，但在较早版本的 activity 写路径上失败，随后才以原 key 做恢复；不把较早 race 直接称为当前候选完整成功 dispatch race。
- **扫码并发：** 候选 `43af67a` 的真实普通用户模型动作 `ydental.lab.code.scan.action_scan` 由两个不同 PostgreSQL backend 同时调用同一码；均解析到合成订单181。私有收据 `.local/s11/operations/20261019T103146Z-lab-scan-race-43af67a.json`，独立读回 `.local/s11/receipts/s11-independent-scanner-race-readback-43af67a-20261019T103241Z.json`，SHA `ef4bc95f1f6db9a37d4e30239dbf7ac34d7a66a49c90e216c1843b6ab346ff36`；确认订单状态、实验室事件、原生库存、采购行和成本前后不变。该证据仅证明并发扫码只解析、不产生库存/成本副作用，不覆盖并发收货/入库。
- **T02 / T10 新增代码（尚未实跑）：** 已新增真实异店转诊/接诊/来源复诊完成的 rollback-only `TransactionCase`，覆盖源店跟进权限、异店就诊读取负例、显式未关联确认、异店预约不伪装源店预约及关闭原因。附件 HTTP 回归针对 `ir.attachment._can_return_content` 中遗漏字段级授权的风险：现在在返回受保护源附件前校验 `res_field` 对应字段的读取权限，未知字段拒绝；对普通仓库用户和管理用户访问厂商资质附件进行真实 HTTP/RPC 测试。发现并修正了 vendor 审计类别不能从 `ydental_category` 读取的问题。两项代码静态检查通过，但 Odoo 测试未运行，尚无新候选及新准入。
- **HTTP/RPC：** `.local/s11/operations/20261019T0954Z-6706-http-rpc.json`，普通合成用户539登录并切到门店1；复诊页、门店切换和 `ydental.lab.order.search_read` 均 HTTP 200，返回的订单只含本店合成加工记录。
- **真实浏览器：** `.local/s11/operations/20261019T0954Z-6706-browser.json`，同普通用户、真实 Chromium、只读打开复诊工作台并读到既有 `to_notify` 行；HTTP 200、无页面异常。此项没有在浏览器中完成复诊业务变更。
- **原生追加费用与核销：** 已提交的合成收费来源51绑定真实追加周期202，冻结演示 S05 价37.80，在实际服务确认后关联 S10 原生已过账发票97 / 来源79 / 行193。现有非费用源和供应商成本独立读回仍按旧候选路径复核；具体独立收费读回见 `.local/s11/receipts/s11-independent-charge-acceptance-b08d493-20261019T080200Z.json`，收费实现自该候选至6706未变。候选6706新增了真实 1.80 合成贷项143、不可变调整源116与部分核销54，将发票余额从37.80降到36.00；无付款或现金退款。独立当前候选读回 `.local/s11/receipts/s11-independent-charge-credit-acceptance-6706bc7-20261019T101200Z.json`，SHA `180e1d89cc409d166d27327b70ae2930e1612a214b7cb3fc666e44221cdf6b16`。
- **收费幂等竞争：** 两个真实 PostgreSQL backend 同时调用同一已提交收费修正键，经 Odoo 原生事务重试层后均返回 `already_accepted` 和同一贷项/调整ID，且只保留一条调整、发票余额不再变化。私有操作 `.local/s11/operations/20261019T1015Z-charge-credit-idempotent-race-result.json`；独立状态读回 `.local/s11/receipts/s11-independent-charge-credit-idempotent-replay-6706bc7-20261019T101052Z.json`，SHA `68f9cd70dceb6bf90460139f69ccc765c85ff177430151f1d19064fa215bc7e1`。另一次首次写竞争中直接调用 `_operate` 的一方遇到 serialization failure；未盲重试，独立只读核实最终仅一条贷项后，才对已知稳定键进行上述无副作用幂等重放。
- **S10保护：** 独立收费/通知读回均核了 D/C 财务链摘要及相关 S10 计数。旧D6收款、2退款、净4链没有重演；S10原文书、附件原件、旧日结与审计没有为 S11 重新操作。

## F1–F5 与 T01–T18 覆盖状态

候选 `7f03f49` 的一次测试命令实际通过60个post-tests，不是60个需求，也不能把下列部分证据升级成场景全PASS。候选及层级按独立审查与原始结果限定：

| 项目 | 当前证据与缺口 |
|---|---|
| F1 / T01、T13 | 生命周期模型测试涵盖提醒、未接通、联系成功、超期、预约关联/改期和真实接诊关联；当前普通 HTTP/RPC、浏览器工作台可读。浏览器没有执行完整闭环。新增跨店闭环模型用例待在新候选实跑，尚不计 T02 PASS。 |
| F2 / T07、T18 | 免费返工、成本与患者收费分离、S05冻结价、实际服务后原生出账及版本贷项模型测试通过；旧候选真实供应商成本/收货读回、当前候选追加收费/部分核销/幂等并发读回可用。尚无当前候选两连接收费首次确认/首张发票并发证据，也未独立读回完整 unknown 通知→返工周期链。 |
| F3 / T08、T16 | 异常终止/遗失/报废模型场景通过；没有该异常完整持久状态独立读回。入库前取消与 putaway 的真实两连接竞争缺失。 |
| F4 / T15 | 资质审核、合作/开单约束、过期旧单与内部活动消息测试通过；双店端到端合作矩阵和厂商资质附件鉴权缺证。 |
| F5 / T06、T14、T17 | 包装码冲突、预约版本和未知码保护有模型/HTTP证据；当前候选43af真实双连接并发扫描同一码、两请求均限于同一合成订单，独立读回库存/成本/采购/事件均不变。收货/入库竞争或取消/入库竞争仍缺。成功码绑定竞争仍只在较早候选9a7记录，绑定逻辑后续未改。 |
| T03、T04 | unknown、受控回调签名/重复/乱序的模型测试通过；当前候选 job450 同 key恢复独立读回。HTTP回调拒绝仅有较早候选证据，无真实供应商通道。 |
| T05、T12 | 策略/退订/未配置及通知不阻断人工加工有模型测试和相关持久状态；没有端到端日上限/免打扰/失败派发完整浏览器链。安装/带数据升级通过。真实通道 NOT_RUN。 |
| T09 | 完成后关联返修单的模型测试通过；独立只读读回 `.local/s11/receipts/s11-independent-t09-post-fit-repair-43af67a-20261019T103711Z.json`（SHA `8b052154098557d4e43eec8eb1c58f88f7449f8f5e336f8315bd43eea4a99e09`）确认父订单200仍完成、治疗与义齿出库事件保留，恰有一个独立返修子单249并有自身收货/采购成本/复诊待办。此为持久状态读回，不是新操作或并发测试，也未证明每条历史记录内容不变。 |
| T10 | 无权来源/未知码与病历边界已有模型/HTTP覆盖。新增附件字段授权修复和 HTTP 回归已静态通过，尚未实跑；若通过，将覆盖普通仓库用户不能读取管理组限定的资质附件，管理者可读。 |
| T11 | 新的 S11 专用 TransactionCase 已在候选7f03随完整带数据升级执行通过（计入60 post-tests），独立读回确认；通过实际检查/续诊/CBCT复核服务链测试昨日全景已完成、次日未复核拒绝旧CBCT、续诊并验证后才完成。S09-only `ydental_exam_test` 门禁保持未绕过。证据为上方升级日志与独立读回。 |

独立覆盖矩阵完整结果以本段为准；不将未执行/旧候选验证写 PASS。外部通知测试 sink 与真实 SMS 分列：真实供应商 **NOT_RUN / OUT_OF_CURRENT_ACTIVATION**。

## 独立验收、状态与下一步

独立代码/证据审查（实现者未给自己签收）确认：追加收费来源、供应商成本分离和 S10 原生出账/贷项代码契约通过；候选6706的升级、私有状态、通知恢复、收费核销与幂等竞争读回通过。T09 完成后返修的持久源状态已另行独立只读核验。T02与T10刚加入的回归仍待新候选实测；T06/T16、通知策略端到端及其他异常场景仍有证据缺口。故当前结论保持 **PARTIAL**，#35 不关闭。

已知差错与修复保留：早期安装缺 Python `phonenumbers`；Odoo20 registry import路径已修；ruff排序曾破坏模型依赖import顺序并导致模块注册失败，已恢复依赖顺序；Odoo mail.activity默认消息可能触发邮件，现通过 quick-update 抑制活动邮件并限制 vendor message API；通用 composer/template及可选 SMS模块存在外发路径，新增 vendor guard 与 `ydental_lab_sms_guard`，普通 reader 负测确认不会增加短信/邮件。各失败、候选、日志与保全读回仍在本地 ignored `.local/s11/operations`/`receipts`，最终交付前需生成不含秘密的可发布证据索引。

剩余工作只在 S11 范围继续：对新增 T02/T10 代码建立固定候选并在新准入下执行；完成 T06/T16真实收货/入库/取消竞争，补候选匹配的通知/资质/异常链和浏览器业务操作证据，再运行必要回归及独立最终验收。任何需改业务语义或放宽安全门禁的事项不自行处理。S11结束时按最终适用证据更新本文件与同一 `CURRENT_TASK.md`，再按用户要求统一推送最终报告并处理 #35；在此之前不发布中间 Issue 评论。

当前 owned Odoo 已停止；正式效果入口仍需在最终报告列出正常 launcher、普通角色及可复现步骤。无生产批准，不合并、不部署，不启动 S12/S13。
