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

产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`，以下是 **SOURCE** 依据：[ydental_supply/views/ydental_supply_templates.xml](../../../../../../ydental_supply/views/ydental_supply_templates.xml)、[ydental_supply/controllers/supply.py](../../../../../../ydental_supply/controllers/supply.py)、[ydental_supply/models/ydental_supply_service.py](../../../../../../ydental_supply/models/ydental_supply_service.py)、[ydental_supply/models/ydental_supply_policy.py](../../../../../../ydental_supply/models/ydental_supply_policy.py)。源码存在不证明本环境已部署、实际操作成功或用户验收通过。环境、权限和历史证据由环境负责人单独确认。

截图目录：`../images/UAT-SCH-002/`。截图使用如 `03-用途.png` 的相对路径，不覆盖原图，私有副本保存；不要把真实患者、凭据、Session 或未授权信息上传公共仓库。

## 用户填写区（可暂时留空）

- 测试日期：
- 实际使用版本或测试环境：
- 实际岗位及门店：
- 浏览器、窗口宽度、缩放：
- 用户验收结果：**NOT_RUN**（可改为 PASS / PARTIAL / FAIL / BLOCKED / N/A）
- 实际观察：
- 与预期是否一致：
- 失败步骤：
- 问题描述：
- 具体复现步骤：
- 复现次数／是否稳定：
- 问题等级（P0 / P1 / P2 / P3）：
- 是否阻断下一项验收：
- 截图相对路径：
- UI 满意程度（满意 / 基本可用但需优化 / 需要重新设计 / 不适用）：
- 不满意的页面、位置和原因：
- 希望如何调整：
- 是否涉及需求变更：
- 用户最终意见：
- 修复后复测结果：
