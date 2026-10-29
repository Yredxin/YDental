# UAT-RPT-002｜导出合成报表并审阅审计边界

- 所属阶段：U06
- 参与岗位：经营报表使用者、授权导出人员
- 真实权限要求：所选每个门店 settlement read 或更高及 export write，且在账号允许公司范围；审计记录读取还需负责人确认其独立权限与入口，不能凭导出权限推定。
- 对应需求／技术阶段及 TC：R04、R24、R25；S12-T06、T09–11
- 验收层级：L2 / L4
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；步骤依据 SOURCE，环境、账号、数据准备后方可验收。

## 业务作用与核心行为

在已应用的授权筛选范围导出合成报表，并审阅对应审计证据是否存在；不将导出等同全局审计查看权限。

## 页面与前置条件

UAT-RPT-001 已确认合成门店、收款来源和过滤范围。使用该门店 settlement read 和 export write 的独立测试账号；本地私有副本有安全保存合成CSV的位置。负责人须从目标来源详情的 Technical trace and complete source facts 记录来源模型与来源 ID，并关联已知收款记录；无法对应时导出对照 BLOCKED。审计查看入口当前未固定，需负责人另提供专项证据，否则审计部分 BLOCKED。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 进入 `/ydental/reports`，选择与 UAT-RPT-001 一致的收款指标、营业日期和合成门店，点击 Query authorized sources。 | 页面显示已应用的日期、门店及币种，目标来源可辨识。 |
| 2 | 核对页内来源单号和金额，点击 View source and allocations，并展开 Technical trace and complete source facts；在负责人协助下记录对应的来源模型与来源 ID，再返回同一筛选。 | 模型与 ID 与负责人已确认的目标来源一致；无法对应或来源超出范围则停止并记 BLOCKED。 |
| 3 | 确认筛选条件与来源状态未变，点击 Export all matching sources (store export permission required) 一次。 | 浏览器下载 CSV；导出按已应用筛选重新查询全部匹配来源，而非固定的页面快照，也不限于当前页。 |
| 4 | 在私有副本打开 CSV，以 source_model 和 source_id 定位步骤2确认的目标来源，再比较 filters、totals_by_unit 与该行的 store_id、value、unit、event_date、state。 | 在相同筛选且来源未变化时，范围和目标来源信息与页面对应；CSV 不提供页面原生收款单号。多币种分开。若期间来源变化，保留原结果、重新对照并记录变化，不重发经济业务；无法建立对应则 BLOCKED。 |
| 5 | 请负责人按专项技术证据核对本次导出审计动作与门店范围；如没有合法读取入口或证据，记录审计部分 BLOCKED。 | 有证据时记录证据位置及版本；不能仅凭下载成功宣称审计已读回。 |

## 异常与权限负例

以独立无 export write 的账号进行相同筛选后，导出应被拒绝；不要以页面按钮是否显示代替实际拒绝。无独立账号或安全数据则 BLOCKED。

## 一次性提交及停止条件

导出会记录访问审计并产生包含来源数据的文件；仅保存合成数据于私有副本，不上传公共仓库。结果不明先核下载和审计，避免无必要重复请求。

## 结束条件及后续衔接

导出和审计证据分别记录结果；审计入口未准备则此用例记 PARTIAL 或 BLOCKED，不得写全部通过。

## 源码依据和证据层级

固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不是运行证据，也不代表用户验收通过。

- [源码：ydental_reporting_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_reporting/views/ydental_reporting_templates.xml)
- [源码：reporting.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_reporting/controllers/reporting.py)
- [源码：ydental_reporting_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_reporting/models/ydental_reporting_service.py)
- [源码：ydental_access_audit.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/models/ydental_access_audit.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-RPT-002-001`、`RUN-UAT-RPT-002-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-RPT-002/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-RPT-002/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
