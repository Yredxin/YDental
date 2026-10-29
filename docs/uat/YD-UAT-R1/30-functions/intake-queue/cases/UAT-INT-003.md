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
- [ydental_intake/views/intake.xml](../../../../../../ydental_intake/views/intake.xml)
- [ydental_intake/controllers/intake.py](../../../../../../ydental_intake/controllers/intake.py)
- [ydental_intake/models/ydental_intake_service.py](../../../../../../ydental_intake/models/ydental_intake_service.py)
- [ydental_queue/models/ydental_queue_service.py](../../../../../../ydental_queue/models/ydental_queue_service.py)

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

截图目录：[本用例截图目录](../images/UAT-INT-003/)。例如 `![步骤3](../images/UAT-INT-003/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
