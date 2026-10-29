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

产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`，以下是 **SOURCE** 依据：[ydental_supply/views/ydental_supply_views.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/views/ydental_supply_views.xml)、[ydental_supply/views/ydental_supply_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/views/ydental_supply_templates.xml)、[ydental_supply/controllers/supply.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/controllers/supply.py)、[ydental_supply/models/ydental_supply_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/models/ydental_supply_service.py)。源码存在不证明本环境已部署、实际操作成功或用户验收通过。环境、权限和历史证据由环境负责人单独确认。

截图目录：`../images/UAT-SCH-001/`。截图使用如 `03-用途.png` 的相对路径，不覆盖原图，私有副本保存；不要把真实患者、凭据、Session 或未授权信息上传公共仓库。

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-SCH-001-001`、`RUN-UAT-SCH-001-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-SCH-001/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-SCH-001/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
