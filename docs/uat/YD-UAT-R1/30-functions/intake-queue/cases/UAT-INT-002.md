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
- [ydental_intake/views/intake.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_intake/views/intake.xml)
- [ydental_intake/controllers/intake.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_intake/controllers/intake.py)
- [ydental_intake/models/ydental_intake_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_intake/models/ydental_intake_service.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-INT-002-001`、`RUN-UAT-INT-002-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-INT-002/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-INT-002/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
