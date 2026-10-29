# UAT-SCH-001｜员工排班与我的今日

- 所属阶段：U02
- 参与岗位：排班人员、被安排员工
- 真实权限要求：排班工作台须当前门店 capacity=read；新建排班须 capacity=write。我的今日要求有效内部会话及员工门店成员关系，排班本身不授予业务权限。
- 对应需求／阶段／TC：R06、R07；S03-T01、T02、T04、T06、T11–14
- 验收层级：L2
- 当前可验收准备状态：**ENVIRONMENT_NOT_READY**；须由环境负责人核实固定候选、账号及数据后再执行。用户结果初始为 NOT_RUN。

## 业务作用与核心行为

给员工安排工作地点和时间，让员工查看建议位置而不自动切店或获得额外权限。

## 入口、前置条件

YDental → Schedule and capacity（/ydental/supply）；员工进入 My today（/ydental/supply/today）。

环境负责人准备同一测试门店的有效员工、可用工位及今天与工位和员工均不重叠且未请假的时间段，工位业务能力与员工资格匹配。排班在门店本地时间输入。

## 操作及逐步预期

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 排班人员进入 Schedule and capacity，查看页面显示的门店与时区。 | 页面显示当前选中门店和本地时区；Weekly plan 包含员工、地点、时间和状态。 |
| 2 | 在 New arrangement 选测试员工，选择一个工位，区域留空，输入约定的开始、结束和原因。 | 表单显示 Employee、Workstation、Area、Start、End、Reason；只能选工位或区域之一。 |
| 3 | 单击 Save arrangement 一次，回到相应周的 Weekly plan。 | 该员工一条新安排显示选择的地点和本地时间；若有警告，记录具体内容。 |
| 4 | 用该员工登录并打开 My today。 | 在测试日对应安排显示门店、时间、工位或区域；未命中当天时显示无有效安排提示。 |
| 5 | 查看门店选择，再点击 Enter suggested workbench 查看建议。 | 页面明确安排只是建议；当前会话门店在用户选择前保持原值，建议页面提供信息而不等同工位已接诊。 |

## 异常、权限负例和停止条件

使用只读账号观察不显示新建操作；另选新合成冲突时间可验证员工或工位重叠被拒，拒绝后不得改变既有安排。请假或无有效门店成员不能安排。

Save arrangement 写入排班及事件；My today 的门店选择和错误反馈也是操作，不为观察建议随意提交。未知结果先查周表，不盲目重试。

## 结束及衔接

排班记录和员工今日页面结果已记录；无当天安排不能冒充通过。

测试容量见 [UAT-SCH-002](UAT-SCH-002.md)。

## 源码依据及证据层级

产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`，以下是 **SOURCE** 依据：[ydental_supply/views/ydental_supply_views.xml](../../../../../../ydental_supply/views/ydental_supply_views.xml)、[ydental_supply/views/ydental_supply_templates.xml](../../../../../../ydental_supply/views/ydental_supply_templates.xml)、[ydental_supply/controllers/supply.py](../../../../../../ydental_supply/controllers/supply.py)、[ydental_supply/models/ydental_supply_service.py](../../../../../../ydental_supply/models/ydental_supply_service.py)。源码存在不证明本环境已部署、实际操作成功或用户验收通过。环境、权限和历史证据由环境负责人单独确认。

截图目录：`../images/UAT-SCH-001/`。截图使用如 `03-用途.png` 的相对路径，不覆盖原图，私有副本保存；不要把真实患者、凭据、Session 或未授权信息上传公共仓库。

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
