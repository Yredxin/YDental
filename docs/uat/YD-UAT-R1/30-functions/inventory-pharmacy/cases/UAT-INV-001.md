# UAT-INV-001｜门店仓库、批次与入库

- 所属阶段：U01
- 参与岗位：仓库、环境负责人
- 真实权限要求：当前门店 warehouse write；集团产品目录由集团管理权限维护，不能仅用岗位名推断。
- 对应需求／技术阶段及TC：R19；S07-T01–09；S08-T04
- 验收层级：L2
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；前置不足为 BLOCKED，用户结果仍为 NOT_RUN。

## 业务作用与核心行为

记录一个新合成批次的实际模拟收货；原生库存移动才是库存来源。

### 页面与前置

YDental → Inventory workbench（`/ydental/inventory`）；选择经批准的隔离测试门店。环境负责人预先准备本店仓库配置、集团已存在的合成产品、单位及全新批次标签、未来有效期、唯一收货来源和模拟数量；对应库存类别与该门店匹配。若仓库未配置，不自行改全局设置，交负责人处理。此处不创建或修改集团产品，也不使用历史批次。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 打开 Inventory workbench，查看标题下当前门店。 | 显示的是约定的隔离测试门店。 |
| 2 | 在 Find products, lots and consumption 输入合成产品名并点击 Search。 | Lots and alerts 显示当前授权门店的匹配产品／批次；若已有同名待建批次则停止。 |
| 3 | 展开 Create manufacturer lot，选择约定产品，填写全新批次标签与 UTC 有效期，点击 Confirm 一次。 | 返回工作台后查询该产品可见新批次；记录批次名称。 |
| 4 | 展开 Actual receipt，选择刚建批次及匹配的库存单位，输入约定正数量、唯一来源和合成理由。 | 提交前产品、批次、单位和数量与测试计划一致。 |
| 5 | 点击 Confirm 一次。 | 搜索相同产品：Lots and alerts 显示该批次及库存；Inventory sources and recovery 显示 Receipt 来源和 Stock confirmed 状态。 |
| 6 | 对照步骤4记录的输入，核对页面显示的 Receipt、数量、批次、责任人、Native movement 及当前批次可用量；保留输入的来源标识，但不假设列表回显该标识。 | 新批次起始库存为零且无并发操作时，入库后 On hand／Available 与入库数量一致；存在保留时记录差异并停止后续发药。 |

## 异常与权限负例

无 warehouse write 的账号不得执行创建或收货；超期、禁用、单位不符或来源重复应停止并记录具体拒绝。不要为了测试异常更改正式策略。

## 一次性提交和停止条件

创建批次和收货各为持久提交；超时或结果不明时停止并请负责人查批次与来源，禁止换来源或重发。

出现数据、资金或严重权限异常时停止受影响操作并记录，不在不明状态下重试。

## 结束条件及后续衔接

记录新批次及一次入库结果；将批次交 UAT-PHA-002 或后续库存核查。

## 源码依据与证据层级

固定产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不证明系统已部署、运行或用户验收通过。实际门店与账号准备后才可执行。

- [ydental_inventory/views/ydental_inventory_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_inventory/views/ydental_inventory_templates.xml)
- [ydental_inventory/controllers/inventory.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_inventory/controllers/inventory.py)
- [ydental_inventory/models/ydental_inventory_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_inventory/models/ydental_inventory_service.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-INV-001-001`、`RUN-UAT-INV-001-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-INV-001/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-INV-001/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
