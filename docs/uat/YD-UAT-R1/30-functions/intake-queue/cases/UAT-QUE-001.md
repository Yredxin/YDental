# UAT-QUE-001｜工位进入、叫号与开始执行

- 所属阶段：U03
- 参与岗位：治疗医生／检查医生／药房人员
- 真实权限要求：对应工位类别分别需 medical、exam 或 pharmacy write；队列页面读取需当前门店 frontdesk、medical、exam 或 pharmacy 至少 read；write 满足该类别的读取等级。员工必须具备该工位全部启用业务能力，工位启用、可叫号且无人占用。
- 对应需求／技术阶段及TC：R05、R10、R11、R12；S06-T01/03/04/05/17/18/19
- 验收层级：L3
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；以下为源码支持的预定操作，待独立环境和数据准备后由用户执行。

## 业务作用与核心行为

让具备对应能力的工作人员从匹配队列叫号，避免把报到误认作实际执行。

## 页面与前置条件

YDental → Workstation queue（`/ydental/queue`）；Workstations、Accepted tasks、Enter workstation 和 Call next matching task。

UAT-INT-003 的新合成预约任务已报到，或 UAT-EXM-002 中的派生检查任务已由前台在队列 Pending explicit tasks 中单独报到；派生检查须同一门店营业日已有实际到店、医嘱及项目为 issued 且当日有效，若保留原工位则目标须匹配该派生任务；除合法保留状态外不能存在其他未解决执行。沿用已有实际到店记录，不重复 Record actual arrival。匹配工位、区域营业状态、正数过号位移及连接参数已按测试环境准备，且无未解决占用；该合成任务须是此工位下一条匹配任务，若还有其他匹配任务，停止并请负责人准备独立队列。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 打开 Workstation queue，核对 Current store 与目标工位行的区域、Exact capabilities。 | 工位与合成任务能力匹配且显示可进入。 |
| 2 | 在该工位点击 Enter workstation 一次。 | 页面显示当前持有人、工位位置及连接到期时间。 |
| 3 | 查看 Accepted tasks 中合成任务的区域、能力和状态。 | 该任务位于对应区域且等待；若没有合格工位，页面给出人员／工位提示。 |
| 4 | 点击 Call next matching task 一次。 | 下一条匹配任务进入 calling；核对确为本次合成任务，若不是则停止并请负责人处理，不执行下一步。不能指定其他不匹配能力。 |
| 5 | 确认是本次合成对象后，点击该行 Start actual execution 一次。 | 任务进入实际执行阶段；本步骤不等同治疗、检查或发药完成。 |
| 6 | 将任务交给相应治疗／检查用例。 | 记录执行交接，后续实际医疗动作由对应功能用例完成。 |

## 异常与权限负例

无对应 write、能力不匹配、工位被占或存在未解决执行时不得进入；这些条件下不能凭页面可见就假定有权。

## 一次性提交和停止条件

进入、叫号、开始均是状态提交；连接断开或响应未知先刷新查状态，由负责人核查，不再点叫号或开始。服务中断开需现场核验，不冒称已释放。

出现数据、资金或严重权限异常时停止受影响操作并记录，不在不明状态下重试。

## 结束条件及后续衔接

实际执行已开始，按任务类别进入治疗、检查或药房案例。

## 源码依据与证据层级

源码依据为固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不证明环境已部署或用户验收通过。
- [ydental_queue/views/ydental_queue_templates.xml](../../../../../../ydental_queue/views/ydental_queue_templates.xml)
- [ydental_queue/controllers/queue.py](../../../../../../ydental_queue/controllers/queue.py)
- [ydental_queue/models/ydental_intake_service.py](../../../../../../ydental_queue/models/ydental_intake_service.py)
- [ydental_exam/models/ydental_queue_service.py](../../../../../../ydental_exam/models/ydental_queue_service.py)
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

截图目录：[本用例截图目录](../images/UAT-QUE-001/)。例如 `![步骤3](../images/UAT-QUE-001/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
