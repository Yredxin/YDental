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

[医疗转诊控件](../../../../../../ydental_treatment/views/ydental_treatment_templates.xml) · [转诊校验](../../../../../../ydental_treatment/models/ydental_treatment_service.py) · [目标接收控件](../../../../../../ydental_intake/views/intake.xml) · [目标路由](../../../../../../ydental_intake/controllers/intake.py)

## 用户填写区

- 测试日期：
- 实际使用版本或测试环境：
- 实际岗位及门店：
- 浏览器、窗口宽度、缩放：
- 用户验收结果：NOT_RUN（可选 NOT_RUN / PASS / PARTIAL / FAIL / BLOCKED / N/A）
- 实际观察：
- 与预期是否一致：
- 失败步骤：
- 问题描述：
- 具体复现步骤：
- 复现次数／是否稳定：
- 问题等级：P0 / P1 / P2 / P3（留空待定）
- 是否阻断下一项验收：
- 截图相对路径：
- UI满意程度：满意 / 基本可用但需优化 / 需要重新设计 / 不适用（留空待定）
- 不满意的页面、位置和原因：
- 希望如何调整：
- 是否涉及需求变更：
- 用户最终意见：
- 修复后复测结果：

截图目录：[本用例截图目录](../images/UAT-FUP-002/)。例如 `![步骤3](../images/UAT-FUP-002/03-用途.png)`；保留原图与失败截图，用户材料保存在私有副本。
