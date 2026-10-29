# UAT-SCH-002｜工位容量及资格覆盖

- 所属阶段：U02
- 参与岗位：容量配置人员、合成测试员工
- 真实权限要求：当前门店 capacity=read 查看；capacity=write 创建和发布。发布还需真实有效门店员工的业务能力覆盖、工位可用和测试策略合法。
- 对应需求／阶段／TC：R06、R07、R09；S03-T03、T07、T10–13；S05-T02、T06
- 验收层级：L2
- 当前可验收准备状态：**ENVIRONMENT_NOT_READY**；须由环境负责人核实固定候选、账号及数据后再执行。用户结果初始为 NOT_RUN。

## 业务作用与核心行为

为工位时间段设置共享容量，核对预约与现场分配及人员能力覆盖。

## 入口、前置条件

YDental → Schedule and capacity → Capacity policy / Shared capacity（/ydental/supply）。

预备可叫号的测试工位、其报到区域、能力和覆盖该能力的有效测试员工；环境负责人确认隔离合成策略已按该环境授权配置。演示策略不可售；正式生产策略不在本次授权。使用没有现有时段的同一当地营业日时间。

## 操作及逐步预期

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 进入工作台并查看 Capacity policy 的范围、比例、模式及截点。 | 能辨认适用策略；工位优先于最近区域，再到门店；已有时段保留原策略版本。 |
| 2 | 在 Shared capacity 展开 Temporary opening or new capacity slot，选择测试工位及其有效能力。 | 所选能力属于该工位；安排区域本身不增加容量。 |
| 3 | 填写本地同一天内、不与工位已有时段重叠的开始和结束时间、正数 Total、原因，单击 Create capacity slot 一次。 | 该工位的 Shared capacity 表出现新时段、总数、预约与现场剩余及状态；零预约分配时显示警告。 |
| 4 | 在该新行展开 Verify and publish supply，选择可覆盖所列全部能力的有效测试员工，填写原因并单击 Publish verified supply 一次。 | 该行状态显示已发布；这是资格覆盖确认，仍取决于策略和营业日，不能直接推断可以预约。 |
| 5 | 比较工位行和区域汇总。 | 同一时段工位的共享总量只计一次，不按每个能力重复相加；记下实际数值。 |

## 异常、权限负例和停止条件

未覆盖全部能力、无有效门店员工或重叠时段应被拒；只在新隔离测试对象上执行。只读账号不显示写入控件。demo 即使发布也不代表可售。

创建时段及发布均为持久提交，不创建正式政策或勾选正式生产批准。任何失败或响应未知先核页面状态、原因和环境，不重发或另建同一时段。

## 结束及衔接

新时段、策略模式、人员覆盖及汇总可记录；策略或环境未配置则 BLOCKED。

开接见 [UAT-SCH-003](UAT-SCH-003.md)；预约由独立预约用例负责。

## 源码依据及证据层级

产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`，以下是 **SOURCE** 依据：[ydental_supply/views/ydental_supply_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/views/ydental_supply_templates.xml)、[ydental_supply/controllers/supply.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/controllers/supply.py)、[ydental_supply/models/ydental_supply_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/models/ydental_supply_service.py)、[ydental_supply/models/ydental_supply_policy.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/models/ydental_supply_policy.py)。源码存在不证明本环境已部署、实际操作成功或用户验收通过。环境、权限和历史证据由环境负责人单独确认。

截图目录：`../images/UAT-SCH-002/`。截图使用如 `03-用途.png` 的相对路径，不覆盖原图，私有副本保存；不要把真实患者、凭据、Session 或未授权信息上传公共仓库。

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-SCH-002-001`、`RUN-UAT-SCH-002-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-SCH-002/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-SCH-002/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
