# UAT-FUP-002｜医生发起无时段跨店转诊并由目标门店接收

- 所属阶段：U06
- 参与岗位：治疗医生、目标门店前台
- 真实权限要求：源门店 medical write 且合法接诊、编辑租约；目标门店 frontdesk write、有效门店及公司范围。其他患者关系和供给资格由系统校验。
- 对应需求／技术阶段及适用 TC：R23；S11-T07–12
- 验收层级：L3
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；下述为源码依据，尚未实际部署或用户验收。

## 业务作用与核心行为

在源店发起转诊，由目标店取得现场接诊资格；发起不等于目标门店已接收或患者已到店。

## 页面与前置条件

医生从临床页面的 Actual treatment, orders and referrals 进入 `/ydental/treatment`；目标前台进入 Service intake（`/ydental/intake`）。须已在源店用新合成患者取得有效接诊和文书编辑权，事先准备另一合成门店的目标服务映射、合规可售测试供给、可用UTC时段及两岗位授权；源和目标不可为同一店。此例仅测 Untimed 模式。目标列表只显示服务名和截止时间，不显示源数值编号；负责人须事先确保此合成转诊在目标列表中能唯一辨识，无法确认时 BLOCKED。目标接收前合成场景中患者须实际到达目标门店；超时或无法确认政策／来源即 BLOCKED。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 源店医生打开工作台，核对患者、源门店和当前接诊。 | 患者及接诊与准备记录一致。 |
| 2 | 在 Cross-store referral 选择另一合成门店的 Target region and capability，选择 Untimed, no capacity held。 | 目标店及服务与准备数据一致；此模式不占用容量。 |
| 3 | 填未来 UTC valid until 和合成转诊原因；UTC slot start、end 留空。 | 仅无时段截止时间有值；时间位于允许范围。 |
| 4 | 点击 Initiate referral only 一次，记录显示的待接收来源编号。 | 页面显示 Untimed source awaiting target acceptance at initiation 和编号；这不是目标资格或到店。 |
| 5 | 目标前台切换到目标合成门店，打开 Service intake 的 Untimed referrals for this store。 | 依据负责人核定的唯一服务名和截止时间找到转诊；列表不显示源数值编号，不能仅凭编号匹配，不唯一则停止。 |
| 6 | 输入准备好的 UTC Slot start 和 Slot end，点击 Acquire target walk-in qualification 一次。 | 在目标店 Qualifications／Service tasks 检查新资格与任务的患者、服务和状态，并在 Actual arrivals 查看本次到店；目标接收同时取得资格并记录到店，未确认唯一结果则停止。 |

## 异常与权限负例

目标门店供给不可售、过期、权限不足或选择源店服务时不应取得新资格。没有专门合成负例及可读前后状态时标 BLOCKED；不通过伪造门店、时间或身份补齐。

## 一次性提交及停止条件

发起与目标接收是两次独立持久提交；任何一方结果不明先按编号由负责人核对，不重复点击或另开旧页重发。不得重新记录实际到店。 出现数据或严重权限异常，停止受影响操作并登记。

## 结束条件及后续衔接

目标资格、任务及到店被唯一确认后，源店旧接诊须先通过其合法结束或交还流程释放患者位置；若仍有 started 执行段，目标任务报到会被拒绝。由负责人核实源接诊及患者位置，未满足则 BLOCKED，不强制接管或反复重试。满足后在目标 Service tasks 对现有任务点击 Report this task 一次，再接续队列用例；不要执行 UAT-INT-003 的重复到店。取得资格和记录到店不等于任务已报到。

## 源码依据和证据层级

固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；并非运行证据或用户验收通过。

[医疗转诊控件](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_treatment/views/ydental_treatment_templates.xml) · [转诊校验](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_treatment/models/ydental_treatment_service.py) · [目标接收控件](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_intake/views/intake.xml) · [目标路由](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_intake/controllers/intake.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-FUP-002-001`、`RUN-UAT-FUP-002-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-FUP-002/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-FUP-002/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
