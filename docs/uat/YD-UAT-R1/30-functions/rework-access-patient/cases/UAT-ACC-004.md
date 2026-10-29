# UAT-ACC-004｜撤销写权限后使用旧患者编辑页

- 所属阶段：U07；验收层级：L3。
- 参与岗位：授权管理者、独立合成受限账号。
- 真实权限：管理者须为有效成员店长，或有足够 personnel write 且不修改自身及不越权；合成账号初始仅 patient write，frontdesk 不可为 write；撤权后 patient read 保留读取。不同浏览器会话、同一门店、有效员工及门店绑定。其他类别不能为其提供患者写入能力。
- 需求／技术阶段及TC：R03、R04、R05；S01-T07/11/12/13、S04-T05/06。
- 准备状态：DATA_NOT_READY；SOURCE 已核，须负责人核两账号配置和合成对象，环境未就绪时 BLOCKED。

## 业务作用与核心行为

验证页面打开后权限被收紧，旧页面不能继续写患者资料。此例将原 UAT-ACC-003 的患者旧页负例具体化；同一合成对象只执行本例一次，不再重复执行该负例。

## 页面与前置条件

进入 YDental → Patients `/ydental/patients` 及 Store and staff `/ydental/access`。事先由负责人准备仅供此例使用的新合成患者、合成账号及门店。账号不能有尚未完成的文书、执行、库存或财务责任；记录初始患者姓名及版本，授权人员确认保留 patient read 后仍可读取患者。

## 操作步骤和预期结果

| 步骤 | 操作 | 预期结果 |
|---|---|---|
| 1 | 受限账号登录，切到指定门店，打开唯一合成患者档案，展开 Edit administrative information，保留该页面。 | 原姓名及 Content version 可见，编辑表单和 Save administrative information 可见。 |
| 2 | 管理者在另一会话的 Staff 表或由负责人取得唯一合成账号的 Account ID；在 Store and staff → Business permission 填入该数值 ID，选择 patient 和 Read only，点击 Save permission 一次。 | 页面返回；管理者按既有授权管理流程核实该账号 patient 为 read、frontdesk 不为 write；无法核实则停止。 |
| 3 | 保持受限账号原页，不刷新，在 Name 输入新的合成标记，仅点击旧表单 Save administrative information 一次。 | 服务拒绝旧页面的写入；页面可能显示拒绝或错误响应，记录原文。若成功或结果未知，停止并交负责人核实。 |
| 4 | 重新打开该合成患者档案。 | 原姓名和 Content version 保持撤权前的值，新的合成标记未保存；若无法读取则由有权负责人核实，不推断通过。 |
| 5 | 观察重新打开页面的编辑控件。 | 在此账号未有其他患者写入类别时，编辑表单不再可见；与步骤3的服务拒绝分开记录。 |

## 异常、一次性提交及停止

步骤2是真实权限变更，步骤3只提交一次可逆合成资料写入负例；不可对历史账号、正式用户或有责任账号操作。若权限变更、响应或患者前后状态不明，停止、不盲目重试。不要通过更高权限代受限账号操作。

## 结束条件及后续

独立记录拒绝和前后可见字段；有权管理者按环境负责人安排处置该合成账号，勿擅自停用。审计显示按 UAT-ACC-005 只读观察，不再次撤权。

## 源码依据及证据层级

SOURCE：患者写入需 patient 或 frontdesk write，动作捕获 AccessError；服务会实时重查授权。未动态验证本环境。
- [患者授权](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_patient/models/ydental_patient_service.py)
- [患者页面和控制器](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_patient/views/ydental_patient_templates.xml) · [控制器](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_patient/controllers/patient.py)
- [授权服务](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/models/ydental_access_service.py) · [授权页面](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/views/ydental_access_templates.xml)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-ACC-004-001`、`RUN-UAT-ACC-004-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-ACC-004/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-ACC-004/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
