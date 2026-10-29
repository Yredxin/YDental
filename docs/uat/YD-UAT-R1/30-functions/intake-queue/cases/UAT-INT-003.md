# UAT-INT-003｜实际到店与任务报到

- 所属阶段：U02
- 参与岗位：前台
- 真实权限要求：当前门店 frontdesk write，且合成患者存在本店关系和有效可报到任务。
- 对应需求／技术阶段及TC：R10、R11；S05-T03/04/08/12、S06-T03/04/05/09
- 验收层级：L3
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；以下为源码支持的预定操作，待独立环境和数据准备后由用户执行。

## 业务作用与核心行为

将实际到店与任务报到分开登记，建立队列入口。

## 页面与前置条件

YDental → Service intake；Record actual arrival 和 Service tasks 的 Report this task。

UAT-INT-002 已生成未报到的新合成任务；预约对应当前门店营业日，原时段已发布、覆盖有效且尚未到结束时间；事先明确模拟到店并开放对应区域。环境负责人须先确认合法可售供给及其测试身份条件；不满足时 BLOCKED，不使用既有历史任务或更改身份与政策。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 打开 Service intake，核对当前门店及目标合成患者。 | 门店与测试记录一致。 |
| 2 | 在 Record actual arrival 选择该患者，点击 Confirm actual arrival 一次。 | Actual arrivals 显示该患者与到店时间。 |
| 3 | 找到 Service tasks 中同一患者和服务的待处理任务。 | 患者号码、服务和任务状态与资格相符。 |
| 4 | 点击该行 Report this task 一次。 | Accepted positions 出现相应位置，任务进入已接收路径。 |
| 5 | 查看该行状态及队列入口。 | 有接受位置并可交接工位队列；到店和报到是两项独立事实。 |
| 6 | 把任务对应资料交给有权工位人员进行 UAT-QUE-001。 | 不再对同一任务重复报到。 |

## 异常与权限负例

无 frontdesk write 不应执行动作；存在跨店有效位置、已开始执行或不满足资格时应拒绝，查明状态后停止，不用另一门店强行报到。

## 一次性提交和停止条件

实际到店和任务报到均持久提交；不明结果先检查 Actual arrivals、任务及位置，禁止盲点或换页重发。同一到店不在患者详情页重记。

出现数据、资金或严重权限异常时停止受影响操作并记录，不在不明状态下重试。

## 结束条件及后续衔接

任务已有位置，交 UAT-QUE-001。

## 源码依据与证据层级

源码依据为固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不证明环境已部署或用户验收通过。
- [ydental_intake/views/intake.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_intake/views/intake.xml)
- [ydental_intake/controllers/intake.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_intake/controllers/intake.py)
- [ydental_intake/models/ydental_intake_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_intake/models/ydental_intake_service.py)
- [ydental_queue/models/ydental_queue_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_queue/models/ydental_queue_service.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-INT-003-001`、`RUN-UAT-INT-003-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-INT-003/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-INT-003/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
