# UAT-INT-002｜预约或现场登记资格

- 所属阶段：U02
- 参与岗位：前台
- 真实权限要求：当前门店 frontdesk write；患者与服务必须在当前门店可用，供给及区域须事先配置。
- 对应需求／技术阶段及TC：R08、R09、R10；S05-T01/02/03/04/06/08/11/12、S06-T02/03
- 验收层级：L2
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；以下为源码支持的预定操作，待独立环境和数据准备后由用户执行。

## 业务作用与核心行为

取得预约或现场登记资格，区分资格、到店与报到。

## 页面与前置条件

YDental → Service intake（`/ydental/intake`）；New qualification 有 Reception type、Patient、Service and reporting area、UTC 时段与 Acquire qualification。

新合成患者、合成服务映射、开放区域及该时段可用容量；环境负责人须先准备合法隔离测试环境和可售供给：demo 不可售，isolated_test 有身份门禁，published 须另获正式政策批准。未满足则结果 BLOCKED；用户不要更改身份、守卫或政策。接续报到需当前门店营业日内、未过期且有效覆盖的时段。选择尚未使用的合成资格，不使用历史数据。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 进入 Service intake 并核对当前门店。 | 门店与患者测试计划一致。 |
| 2 | 在 New qualification 的 Reception type 选择 Reservation。 | 选项保持 Reservation；不要选择含 reporting 的组合动作。 |
| 3 | 选择 UAT-PAT-001 的合成患者和 UAT-INT-001 配好的服务区域。 | 所选患者和服务与测试计划一致。 |
| 4 | 填写有可用供给的 Slot start/end (UTC)，核对开始早于结束。 | 两个时刻及日期与准备的时段一致。 |
| 5 | 点击 Acquire qualification 一次。 | Qualifications 出现该患者和服务的有效资格，Service tasks 可见相关任务；记录其状态。 |
| 6 | 查看 Actual arrivals 与 Accepted positions。 | 预约本身不是实际到店；不能仅凭预约声称已报到或叫号。 |

## 异常与权限负例

无 frontdesk write 不应可创建资格；容量不足或关闭区域应拒绝取得新资格。若需现场登记，使用另一个新合成资格并选 Walk-in registration only，不复用已有资格。

## 一次性提交和停止条件

取得资格会占用容量并持久创建记录；响应不明先查资格、任务与容量，不重试。组合 Walk-in registration and reporting 不在此执行。

出现数据、资金或严重权限异常时停止受影响操作并记录，不在不明状态下重试。

## 结束条件及后续衔接

保存资格和任务对应的合成患者；下一项 UAT-INT-003。

## 源码依据与证据层级

源码依据为固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不证明环境已部署或用户验收通过。
- [ydental_intake/views/intake.xml](../../../../../../ydental_intake/views/intake.xml)
- [ydental_intake/controllers/intake.py](../../../../../../ydental_intake/controllers/intake.py)
- [ydental_intake/models/ydental_intake_service.py](../../../../../../ydental_intake/models/ydental_intake_service.py)

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

截图目录：[本用例截图目录](../images/UAT-INT-002/)。例如 `![步骤3](../images/UAT-INT-002/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
