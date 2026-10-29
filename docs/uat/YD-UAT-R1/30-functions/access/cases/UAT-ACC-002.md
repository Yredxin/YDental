# UAT-ACC-002｜单项权限和模板预览

- 所属阶段：U00 组织与权限准备；层级 L2。
- 参与岗位：集团管理者、获准店长或人员授权者；模板定义由集团管理员管理。
- 真实权限：有效门店成员的店长或 `personnel=write`，或允许公司范围内集团管理员可处理授权；普通 `personnel=write` 不得改自己，也不能授予超过自身等级的类别。模板菜单和定义操作要求集团管理员组，应用仍须目标门店人员授权。系统管理员是另一组，不能用其名称推导业务权限。
- 需求与技术阶段：R03、R04、R05；S01-T01/02/03/04/07/08/09/10/11/12/13、S03-T12。这里的 TC 是需求追溯，并非用户 PASS。
- 业务作用：为合成员工授予可核对的门店内能力，并在替换前检查模板影响。
- 核心行为：设置单一类别；预览模板的全部类别及前后等级，只在授权后替换。
- 页面：YDental 的 **Store and staff**（`/ydental/access`）中的 Business permission、Apply template；集团管理员另可从 **Permission templates** 查看模板。类别是 frontdesk、patient、medical、exam、pharmacy、warehouse、followup、outsourcing、settlement、finance_approval、personnel、space、capacity、price、supplier、export；等级为 none、read、write。Common capabilities 是员工资料字段，不等于上述业务授权。
- 前置：未来合成测试环境、目标活动员工及门店已准备；预先列出该账号的所有目标等级和可用活动模板，模板由有权负责人配置。仅使用专为本次测试准备的目标账户，勿使用历史人员或真实账号。模板缺失类别会变为 none。
- 当前可验收准备状态：**ENVIRONMENT_NOT_READY**；界面标签及权限以实际环境核对，源码并不证明部署。

| 步骤 | 操作 | 预期结果 |
|---|---|---|
| 1 | 打开 Store and staff，确认 Current store 与准备清单一致，找到目标合成人员 Account ID。 | 当前门店和目标账号相符；若管理表单不见或对象不符，停止。 |
| 2 | 在 Business permission 填目标 Account ID，选择清单中指定的一个 Business category 和 Permission level。 | 类别和等级与事前授权清单一致，尚未提交。 |
| 3 | 点 Save permission 一次。 | 请求返回门店员工页。源码规定单项设置只提交所选类别；仅凭返回页面不能观察或证明其他类别未改变。需要事前和事后的完整预览才能验证。 |
| 4 | 在 Apply template 填同一目标 Account ID，选择事先批准的活动模板，点 Preview all changes。 | 出现 Confirm template changes 表格，逐类别列出 Account、Store、Business category、Before、After；如事先记录了 Before，可与本次 Before 比较未选类别。 |
| 5 | 对照授权清单逐项检查表格，尤其核对变为 None 的类别。 | 可观察到目标账户、门店及全部类别的前后等级；与清单有任何差异时点 Cancel，不确认替换。 |
| 6 | 仅在全部等级与授权清单一致且测试负责人允许持久替换时，点 Confirm replacement 一次。 | 返回员工页；模板对该目标是全部类别替换，不是合并；缺失类别成为 None。 |
| 7 | 再次点 Preview all changes，只读核对 Before 与预定等级；然后点 Cancel。 | Before 列反映已提交的等级；取消不应用第二次替换。 |

异常与权限负例：普通人员授权者尝试超出自己级别或修改自己时应拒绝；无活动目标成员不可授权；模板或权限在预览后变化时确认会提示版本冲突，应停止并重新核查后再预览，不盲目重发。集团管理与系统管理分别控制不同菜单，不能以职称取代条件。

一次性提交：第3、6步持久改授权并产生审计；替换影响所有类别。响应不明、对象不符或预览过期时停止，由负责人核实提交与责任后决定后续，不自动重试。模板定义与正式安全策略不在本例中修改。

结束条件：授权清单与预览前后相符，或已记录拒绝、差异及阻断；接续 [UAT-ACC-003](UAT-ACC-003.md) 的专用撤权测试。

源码依据和证据层级：SOURCE，[权限常量](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/models/constants.py)、[菜单](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/views/ydental_access_menus.xml)、[权限页面](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/views/ydental_access_templates.xml)、[授权服务](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/models/ydental_access_service.py)、[模板模型](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/models/ydental_access_template.py)、[ACL](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/security/ir.access.csv)。无用户环境实测结论。

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-ACC-002-001`、`RUN-UAT-ACC-002-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-ACC-002/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-ACC-002/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
