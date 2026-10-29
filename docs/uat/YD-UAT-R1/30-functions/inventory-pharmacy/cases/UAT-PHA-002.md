# UAT-PHA-002｜药房报到与分次模拟发药

- 所属阶段：U04
- 参与岗位：前台、药房
- 真实权限要求：前台 frontdesk write 报到；药房 pharmacy write、有效药房工位及当前对应处方接诊；安装 ydental_queue 扩展后，pharmacy read 已可满足队列页面读取条件（pharmacy write 包含读取）；不要求额外 frontdesk、medical 或 exam 读取。工位还须匹配岗位能力、门店、营业与排班等实时条件。
- 对应需求／技术阶段及TC：R20、R21；S08-T08/13、S07-T05、S10-T08
- 验收层级：L3
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；前置不足为 BLOCKED，用户结果仍为 NOT_RUN。

## 业务作用与核心行为

以新合成处方完成一次部分发药与后续段，观察已发数量、剩余数量、库存及费用来源。这里为演示定价和合成用药，不是真实医嘱或实际用药。

### 页面与前置

使用 UAT-PHA-001 的已冻结新处方和本次 UAT-INV-001 新合成批次；环境负责人预先确认同门店、药品和单位匹配、批次可用未过期、库存足够、明确的药品 SKU 与费用目录关联及演示政策配置。总量须可按单位精度拆分为两个正数量。前台和药房账号、专用空闲工位与匹配能力准备完毕；不要使用历史患者或已发处方。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 前台打开 Workstation and explicit reporting（`/ydental/queue`）的 Pending explicit tasks，找到处方生成的准确任务编号，点击 Report this explicit task 一次。 | 对应任务进入已报到路径；不为其他任务报到。 |
| 2 | 药房人员在同一门店进入匹配药房工位，按 UAT-QUE-001 叫号；核对 Accepted tasks 中任务编号与处方段一致后，对该已叫号条目点击 Start actual execution 一次。 | 当前执行段显示约定任务编号并进入服务中；若叫到其他任务立即停止。 |
| 3 | 在同一浏览器同一标签页打开测试环境的 `/ydental/treatment` 路径进入 Treatment and pharmacy，找到对应处方和明细，记录 Approved、Remaining 和批次。 | 患者、药品、批准总量、待发量与计划一致，处方显示 Issued, frozen（已开立、冻结）。 |
| 4 | 选择 Verified batch，输入第一部分 Actual issue quantity 和模拟理由；不要勾选 Already physically performed。点击 Confirm actual dispensing 一次并确认。 | 当前行 Remaining 比之前减少第一部分数量；Immutable actual events 出现该次实际发药记录，状态为 Fee and stock confirmed，且可见费用来源和 native stock moves。若显示 Fact awaiting reconciliation、费用或移动缺失，停止，不结束段或重复发药。 |
| 5 | 在该处方输入 End this actual dispensing segment reason，点击 Finish segment and release workstation 一次。 | 当前段完成并释放工位；若仍有剩余，处方仍显示 Issued, frozen，产生新的待报到段及任务。 |
| 6 | 前台只对新段的任务按步骤1报到一次；药房在同一浏览器标签页回队列，按步骤2进入工位、叫取该新段并点击 Start actual execution 一次，再在同一标签页打开 `/ydental/treatment`。 | 队列中的任务编号与新处方段一致；治疗页再核对同一合成患者。 |
| 7 | 在相同处方行选择同一有效批次，输入剩余部分及理由，点击 Confirm actual dispensing 一次并确认。 | Remaining 为零；第二次实际发药记录显示 Fee and stock confirmed 且费用和 native stock moves 可见，分别保留两次数量与移动号。若状态待核对或来源缺失，停止，不结束段或重复发药。 |
| 8 | 输入结束理由，点击 Finish segment and release workstation 一次。 | 当前段完成，处方显示 All approved quantities dispensed（全部批准数量已发放）；不再产生新的发药段。 |

## 异常与权限负例

无可用批次、演示价格关联或药房对应工位时 BLOCKED；超额、跨店或无权限不应发药。请勿通过修改状态或补造已发生事实绕过拒绝。药房操作不代表付款；正式政策、真实临床和真实资金不在范围。

## 一次性提交和停止条件

每次报到、发药和结束段均为持久提交；发药可能创建费用和库存来源。响应未知、旧页或库存不足时停止，核当前订单、发药事件及库存后再由负责人决定，不换请求重发。

出现数据、资金或严重权限异常时停止受影响操作并记录，不在不明状态下重试。

## 结束条件及后续衔接

两段完成、剩余为零且两次来源可追踪；将本次新来源交 UAT-INV-002，结算另见 UAT-FIN-001。

## 源码依据与证据层级

固定产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不证明系统已部署、运行或用户验收通过。实际门店与账号准备后才可执行。

- [ydental_treatment/views/ydental_treatment_templates.xml](../../../../../../ydental_treatment/views/ydental_treatment_templates.xml)
- [ydental_treatment/controllers/treatment.py](../../../../../../ydental_treatment/controllers/treatment.py)
- [ydental_treatment/models/ydental_treatment_service.py](../../../../../../ydental_treatment/models/ydental_treatment_service.py)
- [ydental_treatment/models/ydental_queue_service.py](../../../../../../ydental_treatment/models/ydental_queue_service.py)
- [ydental_queue/views/ydental_queue_templates.xml](../../../../../../ydental_queue/views/ydental_queue_templates.xml)
- [ydental_queue/controllers/queue.py](../../../../../../ydental_queue/controllers/queue.py)
- [ydental_queue/models/ydental_intake_service.py](../../../../../../ydental_queue/models/ydental_intake_service.py)
- [ydental_inventory/models/ydental_inventory_service.py](../../../../../../ydental_inventory/models/ydental_inventory_service.py)

## 用户填写区

- 测试日期：
- 实际使用版本或测试环境：
- 实际岗位及门店：
- 浏览器、窗口宽度、缩放：
- 用户验收结果：NOT_RUN（可选 NOT_RUN / PASS / PARTIAL / FAIL / BLOCKED / N/A）
- 实际观察：
- 与预期是否一致：
- 失败步骤：
- 问题描述：
- 具体复现步骤：
- 复现次数／是否稳定：
- 问题等级：P0 / P1 / P2 / P3（留空待定）
- 是否阻断下一项验收：
- 截图相对路径：
- UI满意程度：满意 / 基本可用但需优化 / 需要重新设计 / 不适用（留空待定）
- 不满意的页面、位置和原因：
- 希望如何调整：
- 是否涉及需求变更：
- 用户最终意见：
- 修复后复测结果：

截图目录：[本用例截图目录](../images/UAT-PHA-002/)。例如 `![步骤3](../images/UAT-PHA-002/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
