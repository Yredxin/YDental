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
- [ydental_queue/views/ydental_queue_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_queue/views/ydental_queue_templates.xml)
- [ydental_queue/controllers/queue.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_queue/controllers/queue.py)
- [ydental_queue/models/ydental_intake_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_queue/models/ydental_intake_service.py)
- [ydental_queue/models/ydental_queue_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_queue/models/ydental_queue_service.py)
- [ydental_queue/models/ydental_queue_return.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_queue/models/ydental_queue_return.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-QUE-002-001`、`RUN-UAT-QUE-002-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-QUE-002/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-QUE-002/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
