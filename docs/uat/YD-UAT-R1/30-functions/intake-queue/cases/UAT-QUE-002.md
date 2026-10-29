# UAT-QUE-002｜过号与连接异常观察

- 所属阶段：U03
- 参与岗位：工位人员、前台
- 真实权限要求：过号需持有对应工位且该类 medical、exam 或 pharmacy write；队列页面读取需当前门店 frontdesk、medical、exam 或 pharmacy 至少 read；追加权限另需 frontdesk write 和专门追加组，本用例不做追加。
- 对应需求／技术阶段及TC：R11、R15、R16；S06-T09/10/11/12/20、S13-T14
- 验收层级：L2
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；以下为源码支持的预定操作，待独立环境和数据准备后由用户执行。

## 业务作用与核心行为

用独立合成队列理解实际过号和连接异常，避免误将未确认操作重发。

## 页面与前置条件

Workstation queue 的 Accepted tasks；仅该工位拥有的 calling 项显示 Record real missed call。

专门新建、已报到且被当前工位叫号的合成任务；正数过号位移、心跳和超时已配置。不得对 UAT-QUE-001 已开始执行的任务重复过号。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 查看 Current store、工位持有人及合成任务行。 | 当前人员确实持有对应工位，任务状态为 calling。 |
| 2 | 模拟该合成对象确实未响应，点击该行 Record real missed call 一次。 | 该行 Missed 数相对操作前增加 1，状态变为 waiting；记录实际排序。 |
| 3 | 观察 Accepted tasks 和显示的区域、能力。 | 过号计数为原值加 1，状态为 waiting；位移按测试环境明确配置，不凭岗位名称推断。 |
| 4 | 若页面提示连接不可用或过期，停止提交并刷新查看。 | 显示连接状态或现场核验提示；未确认成功不能作为已完成。 |
| 5 | 将观察交给环境负责人核实后续责任。 | 无需通过重复提交制造第二次过号。 |

## 异常与权限负例

未经授权人员不可持工位或修改过号；无正数位移配置时叫号控件不可用。超时、撤权、跨店等需独立合成状态及专门准备，不假定此用例已覆盖。

## 一次性提交和停止条件

真实过号会改变队列；提交结果不明先查任务与过号数，不重新点击。断连时不自动重新开始执行，不自动释放现场责任。

出现数据、资金或严重权限异常时停止受影响操作并记录，不在不明状态下重试。

## 结束条件及后续衔接

记录过号及异常实际状态；进一步交接或超时另用经准备的场景。

## 源码依据与证据层级

源码依据为固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不证明环境已部署或用户验收通过。
- [ydental_queue/views/ydental_queue_templates.xml](../../../../../../ydental_queue/views/ydental_queue_templates.xml)
- [ydental_queue/controllers/queue.py](../../../../../../ydental_queue/controllers/queue.py)
- [ydental_queue/models/ydental_intake_service.py](../../../../../../ydental_queue/models/ydental_intake_service.py)
- [ydental_queue/models/ydental_queue_service.py](../../../../../../ydental_queue/models/ydental_queue_service.py)
- [ydental_queue/models/ydental_queue_return.py](../../../../../../ydental_queue/models/ydental_queue_return.py)

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

截图目录：[本用例截图目录](../images/UAT-QUE-002/)。例如 `![步骤3](../images/UAT-QUE-002/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
