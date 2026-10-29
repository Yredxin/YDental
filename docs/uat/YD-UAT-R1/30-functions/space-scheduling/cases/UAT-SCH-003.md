# UAT-SCH-003｜报到区域营业日开接和停接

- 所属阶段：U02
- 参与岗位：容量配置人员、前台观察人员
- 真实权限要求：Schedule and capacity 页面需当前门店 capacity=read；变更需 capacity=write。队列页面的其他可见性另由相关业务读取权限决定。
- 对应需求／阶段／TC：R15、R16；S05-T05、S06-T09–12、T20、S09-T08、S13-T14
- 验收层级：L2
- 当前可验收准备状态：**ENVIRONMENT_NOT_READY**；须由环境负责人核实固定候选、账号及数据后再执行。用户结果初始为 NOT_RUN。

## 业务作用与核心行为

按报到区域开接、停止普通报到并在候叫清空后停止普通叫号。

## 入口、前置条件

YDental → Schedule and capacity → Area business day（/ydental/supply）；队列页 Local business day and area reception 提供另一入口。

环境负责人提供未用于真实业务的独立测试报到区域、准确本地日期和可写账号，确认该区域当天没有营业日记录、当前无等待或叫号对象，且已连接队列集成；若当天已有记录，停止并由环境负责人提供新的合成区域，不要操作历史区域或受保护任务。

## 操作及逐步预期

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 在 Area business day 查看区域及当天状态。 | 已存在的当天区域显示名称、状态和本地日期；未开接的区域可在 Open a reporting area today 下选择。 |
| 2 | 选择测试报到区域，填写原因并单击 Open local business day 一次。 | 当天该区域显示 open；这是区域开接，不代表整个门店全部区域开接。 |
| 3 | 在同一行选择 Stop ordinary reporting，填写原因并保存一次。 | 状态显示停止普通报到（draining）；不要将其解释为已停止所有叫号。 |
| 4 | 确认测试区域等待与叫号均为空，再选择 Stop ordinary calling，填写原因并保存一次。 | 状态变为 closed；如仍有待叫或正在叫号，系统应拒绝关闭并保留当前状态。 |
| 5 | 需要衔接后续测试时，从已关闭行选择 Reopen with reason，填写原因并保存一次。 | 该区域回到 open；不开启其他区域，也不恢复旧日队列。 |

## 异常、权限负例和停止条件

只读账号没有写控件；未开接前不能先停普通报到，必须先开接。跨日本地清理由服务处理，需专项受控环境和技术证据，不让用户改时钟或触发历史清理。

开接、停接及重开每次均持久记录并影响新业务入口，逐步仅执行一次。结果未知先刷新查看状态并由负责人确认，绝不对历史业务重放。

## 结束及衔接

测试区域状态及每次变更结果已记录，必要时按约定重开。

进入预约、报到与叫号场景；容量配置见 [UAT-SCH-002](UAT-SCH-002.md)。

## 源码依据及证据层级

产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`，以下是 **SOURCE** 依据：[ydental_supply/views/ydental_supply_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/views/ydental_supply_templates.xml)、[ydental_supply/models/ydental_supply_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/models/ydental_supply_service.py)、[ydental_queue/models/ydental_queue_day.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_queue/models/ydental_queue_day.py)、[ydental_queue/views/ydental_queue_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_queue/views/ydental_queue_templates.xml)。源码存在不证明本环境已部署、实际操作成功或用户验收通过。环境、权限和历史证据由环境负责人单独确认。

截图目录：`../images/UAT-SCH-003/`。截图使用如 `03-用途.png` 的相对路径，不覆盖原图，私有副本保存；不要把真实患者、凭据、Session 或未授权信息上传公共仓库。

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-SCH-003-001`、`RUN-UAT-SCH-003-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-SCH-003/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-SCH-003/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
