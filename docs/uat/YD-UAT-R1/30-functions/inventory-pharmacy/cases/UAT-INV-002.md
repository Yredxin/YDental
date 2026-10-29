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

- [ydental_inventory/views/ydental_inventory_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_inventory/views/ydental_inventory_templates.xml)
- [ydental_inventory/controllers/inventory.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_inventory/controllers/inventory.py)
- [ydental_inventory/models/ydental_inventory_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_inventory/models/ydental_inventory_service.py)
- [ydental_treatment/models/ydental_treatment_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_treatment/models/ydental_treatment_service.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-INV-002-001`、`RUN-UAT-INV-002-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

### 执行记录（复制本节以追加下一轮）

- RUN-ID：
- 测试日期：
- 实际产品版本：
- 测试环境标识：
- 实际岗位及门店：
- 合成业务对象逻辑标识：
- 浏览器及版本：
- CSS 视口宽度 × 高度：
- 浏览器缩放：
- 实际执行步骤及观察结果：
- 与预期是否一致：
- 用户验收结果：NOT_RUN（可选 NOT_RUN / PASS / PARTIAL / FAIL / BLOCKED / N/A）
- 失败步骤及阻断下一项的原因：
- 关联问题 ID（可填写多个，例如 UAT-ISS-0001、UAT-ISS-0002）：
- 截图相对路径：
- 用户最终意见：
- 若为修复后复验，原问题 ID、原 RUN-ID、修复版本及复验结果：

### 问题记录（一个问题复制一份，可关联多个问题）

- 问题 ID（格式 `UAT-ISS-0001`，全套材料中唯一）：
- 对应用例及 RUN-ID：
- 发生页面和位置：
- 前置条件及合成对象：
- 首次发生的实际步骤：
- 预期与实际差异：
- 具体复现步骤（仅记录已安全观察到的事实）：
- 复现次数／是否稳定：
- 问题等级：P0 / P1 / P2 / P3（留空待定）：
- 分类：功能 / UI / 需求 / 环境（可多选）：
- 截图相对路径：
- 是否阻断下一项验收：

### UI/UX 意见（可按 RUN-ID 重复）

- RUN-ID、页面及位置：
- 桌面 / 平板 / 手机及实际视口、缩放：
- 信息布局：
- 操作流程：
- 字号与可读性：
- 间距、颜色和按钮：
- 桌面／平板／手机差异：
- UI 满意度：满意 / 基本可用但需优化 / 需要重新设计 / 不适用（留空待定）：
- 不满意原因及希望如何调整：
- 优先意见：必须修改 / 希望优化 / 可接受（留空待定）：
- 是否涉及需求变更：
- 截图相对路径：

本用例截图放在私有副本的 [截图目录](../images/UAT-INV-002/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-INV-002/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
