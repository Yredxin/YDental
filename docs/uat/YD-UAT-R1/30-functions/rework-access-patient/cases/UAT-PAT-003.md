# UAT-PAT-003｜记录合成联系人验证依据

- 所属阶段：U07；验收层级：L2。
- 参与岗位：患者资料维护者。
- 真实权限：当前有效门店的 patient write 或 frontdesk write；验证勾选及依据只记录人为声明，不代表系统外部验证。
- 需求／技术阶段及TC：R04、R22；S04-T04/05/06、S12-T12。
- 准备状态：DATA_NOT_READY；SOURCE 已核，须新合成患者及未验证合成联系人，真实政策不由此例批准。

## 业务作用与核心行为

核对已存在的合成联系人从待验证变为记录了验证，并填写明确合成依据；此功能不等同患者身份自动核验。

## 页面与前置条件

在 YDental → Patients `/ydental/patients` 打开专用合成患者；可用 UAT-PAT-001 已创建的同一合成联系人作为来源，不再次添加。联系人须在 Contacts and declared guardians 中显示 Pending verification，负责人提供虚构验证依据，禁止使用真实证件或号码。

## 操作步骤和预期结果

| 步骤 | 操作 | 预期结果 |
|---|---|---|
| 1 | 打开合成患者，确认本店、患者号码和唯一合成联系人。 | 联系人姓名、关系及 Pending verification 可见；匹配不唯一则停止。 |
| 2 | 展开该联系人 Maintain this contact。 | 姓名、关系、Verification recorded、Verification basis 及 Save contact relationship 可见。 |
| 3 | 勾选 Verification recorded，输入负责人给定的合成验证依据，确认其余字段不变，点击 Save contact relationship 一次。 | 返回患者详情或重新打开后该联系人显示 Verification recorded。 |
| 4 | 再展开联系人维护，只读核对 Verification basis。 | 显示本次合成依据；不把该标志理解为外部系统核验。 |

## 异常、一次性提交及停止

验证为持久修改，未知结果先只读核对，不重复保存或为重现清除状态。没有依据不勾选验证；无写权限页面不应提供维护控件或服务拒绝。真实身份证明、患者或临床政策不在本例范围。

## 结束条件及后续

记录状态和观察，保留同一联系人；不因此产生到店或合并。

## 源码依据及证据层级

SOURCE；未运行验证。
- [联系人控件](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_patient/views/ydental_patient_templates.xml)
- [必填验证依据及版本检查](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_patient/models/ydental_patient_service.py)
- [患者页面控制器](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_patient/controllers/patient.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-PAT-003-001`、`RUN-UAT-PAT-003-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-PAT-003/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-PAT-003/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
