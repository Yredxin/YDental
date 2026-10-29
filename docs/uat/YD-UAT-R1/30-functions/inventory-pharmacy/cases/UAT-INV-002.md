# UAT-INV-002｜库存来源与隔离退回

- 所属阶段：U04
- 参与岗位：仓库
- 真实权限要求：当前门店 warehouse read 查看、warehouse write 登记退回；关联事件须本店实际已完成的发出或处方发药。
- 对应需求／技术阶段及TC：R19、R20；S07-T01–09、S08-T04/08/13
- 验收层级：L3
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；前置不足为 BLOCKED，用户结果仍为 NOT_RUN。

## 业务作用与核心行为

追踪已发生的库存来源，把独立的模拟实物退回隔离区；退回不恢复处方可发额度。

### 页面与前置

YDental → Inventory workbench（`/ydental/inventory`）。仅使用本次隔离验收中已实际完成的 UAT-PHA-002 新处方发药来源，或负责人准备的本次新合成 replenishment 来源；必须有明确模拟实物退回数量及未使用的唯一来源标识，不能从历史数据补造退回事实。库存列表不显示患者、处方或来源标识；负责人事先凭 UAT-PHA-002 的可见 native stock moves 移动号与对应事件私下标定唯一来源和退回数量。两段共用同批次时不能仅凭产品及批次选来源；无法唯一识别则 BLOCKED。该用例不再次执行治疗耗用或发药。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 搜索约定产品或批次，在 Inventory sources and recovery 比对 Native movement 移动号与负责人预先标定的唯一来源。 | 显示处方或补货来源、产品、批次、数量、责任人、Native movement 及 Stock confirmed，且移动号与事先记录完全相符；否则停止。 |
| 2 | 查看该来源及 Lots and alerts 中本批次当前 On hand、Available、Quarantine。 | 记录三个独立数值及该移动对应的原发出数量，来源属于当前门店。 |
| 3 | 在该来源展开 Enter stock action → Register physical return。 | 可见 Confirmed unit、Actual quantity、Unique source reference、Evidence and reason。 |
| 4 | 选择原单位，填入不超过未退实际发出量的模拟实物退回数量、全新来源和理由，点击 Confirm 一次。 | 新的 Physical return 来源出现；该数量进入 Quarantine，而不是直接成为 Available。 |
| 5 | 查询同一批次并比较隔离量。 | 在无并发变更时 Quarantine 增加本次退回数量；原发药来源仍保留。 |
| 6 | 停在隔离状态并记录退回来源；将结果交负责人。 | 不自动选择 Verify physical destination、放行或报损；处方额度不因退回恢复。 |

## 异常与权限负例

没有已完成的本店来源或真实模拟退回事实时 BLOCKED。超额退回、跨店来源、无 warehouse write 应拒绝；出现任何不明差异停止并保留记录。

## 一次性提交和停止条件

退回是库存持久提交。无响应、重复或来源不明时停止核查，不能换来源重做；核实放行或报损是另一独立提交，本用例不执行。

出现数据、资金或严重权限异常时停止受影响操作并记录，不在不明状态下重试。

## 结束条件及后续衔接

记录来源和隔离数量，后续交仓库负责人；不将隔离品当作可发库存。

## 源码依据与证据层级

固定产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不证明系统已部署、运行或用户验收通过。实际门店与账号准备后才可执行。

- [ydental_inventory/views/ydental_inventory_templates.xml](../../../../../../ydental_inventory/views/ydental_inventory_templates.xml)
- [ydental_inventory/controllers/inventory.py](../../../../../../ydental_inventory/controllers/inventory.py)
- [ydental_inventory/models/ydental_inventory_service.py](../../../../../../ydental_inventory/models/ydental_inventory_service.py)
- [ydental_treatment/models/ydental_treatment_service.py](../../../../../../ydental_treatment/models/ydental_treatment_service.py)

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

截图目录：[本用例截图目录](../images/UAT-INV-002/)。例如 `![步骤3](../images/UAT-INV-002/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
