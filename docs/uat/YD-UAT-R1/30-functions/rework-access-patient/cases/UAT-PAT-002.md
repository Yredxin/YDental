# UAT-PAT-002｜两份合成身份的集团核验合并

- 所属阶段：U07；验收层级：L3。
- 参与岗位：门店患者管理人员与集团身份核验人员。
- 真实权限：提出人须当前门店 patient write 或 frontdesk write；决策人另须集团管理资格、当前门店 patient 或 frontdesk write，且有权覆盖所有涉及公司。岗位称谓不自动给权限。
- 需求／技术阶段及TC：R04、R22；S04-T05/06/07/08、S12-T12。
- 准备状态：DATA_NOT_READY；SOURCE 已核，须两份专用于本例、无业务冲突的独立合成身份；不使用其他场景患者。

## 业务作用与核心行为

通过申请与集团核验将两份合成身份合并，并保留原号码追溯；姓名相似或共用电话不能自行证明同一人。

## 页面与前置条件

打开 YDental → Patients `/ydental/patients`。环境负责人通过合法业务流程提供两个不同、当前有效的合成患者源和目标（逻辑标识 UAT-MERGE-SOURCE、UAT-MERGE-TARGET），至少一个与本店有关系，并私下提供目标实际内部 ID；页面合并表单要求 ID，患者编号不等于内部 ID。两者不得有未解决接诊、财务、库存、文书或其他业务冲突；无法确认则 BLOCKED。合成验证依据由负责人提供，不代表正式身份政策批准。

## 操作步骤和预期结果

| 步骤 | 操作 | 预期结果 |
|---|---|---|
| 1 | 门店人员打开源合成患者，核对姓名及患者号码，确认目标内部 ID 来自负责人。 | 两份身份不同、当前有效；任何编号或对象不确定则停止。 |
| 2 | 在源患者展开 Request group identity merge，输入目标内部 ID 和合成申请原因，点击 Submit for group verification 一次。 | 返回源患者详情；随后点击 Patients 回到列表，Merge requests 中出现源／目标患者号码组合及 Awaiting group verification。 |
| 3 | 集团核验人员使用自己的有权账号打开同一门店 Patients，查看对应 Merge requests 和冲突信息。 | 可辨认唯一申请及来源／目标；有 Active business conflicts 提示则停止，由负责人处理，不强制重试。 |
| 4 | 完成对合成验证依据的检查，在该申请输入明确合成核验理由并点击 Confirm verified merge 一次。 | 若版本和权限满足且无冲突，申请显示 Confirmed；冲突则显示 blocked 和冲突项，停止后续。 |
| 5 | 搜索源号码并打开追溯入口，核对目标患者的 Traceable patient numbers。 | 源身份显示 Merged, open canonical patient，目标下能看到原号码；不能看到或对象无法唯一匹配则记为未证实。 |

## 异常、一次性提交及停止

申请及确认均持久化；确认会合并身份关系并停用源身份，不可撤销为测试初态。响应未知、版本冲突、权限拒绝或业务冲突时停止，由负责人核状态，不重放，不对真实患者执行。只验证当前合成事实，不把相似信息当身份核验。

## 结束条件及后续

申请和确认状态及可见号码已记录，合并后的对象不得复用于其他场景；缺失前置记录 BLOCKED。

## 源码依据及证据层级

SOURCE；未进行本环境合并。
- [患者页面](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_patient/views/ydental_patient_templates.xml) · [控制器](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_patient/controllers/patient.py)
- [请求、版本、冲突和合并服务](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_patient/models/ydental_patient_service.py)
- [业务冲突扩展](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_intake/models/integration.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-PAT-002-001`、`RUN-UAT-PAT-002-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-PAT-002/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-PAT-002/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
