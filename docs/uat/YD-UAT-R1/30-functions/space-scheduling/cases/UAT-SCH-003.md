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

产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`，以下是 **SOURCE** 依据：[ydental_supply/views/ydental_supply_templates.xml](../../../../../../ydental_supply/views/ydental_supply_templates.xml)、[ydental_supply/models/ydental_supply_service.py](../../../../../../ydental_supply/models/ydental_supply_service.py)、[ydental_queue/models/ydental_queue_day.py](../../../../../../ydental_queue/models/ydental_queue_day.py)、[ydental_queue/views/ydental_queue_templates.xml](../../../../../../ydental_queue/views/ydental_queue_templates.xml)。源码存在不证明本环境已部署、实际操作成功或用户验收通过。环境、权限和历史证据由环境负责人单独确认。

截图目录：`../images/UAT-SCH-003/`。截图使用如 `03-用途.png` 的相对路径，不覆盖原图，私有副本保存；不要把真实患者、凭据、Session 或未授权信息上传公共仓库。

## 用户填写区（可暂时留空）

- 测试日期：
- 实际使用版本或测试环境：
- 实际岗位及门店：
- 浏览器、窗口宽度、缩放：
- 用户验收结果：**NOT_RUN**（可改为 PASS / PARTIAL / FAIL / BLOCKED / N/A）
- 实际观察：
- 与预期是否一致：
- 失败步骤：
- 问题描述：
- 具体复现步骤：
- 复现次数／是否稳定：
- 问题等级（P0 / P1 / P2 / P3）：
- 是否阻断下一项验收：
- 截图相对路径：
- UI 满意程度（满意 / 基本可用但需优化 / 需要重新设计 / 不适用）：
- 不满意的页面、位置和原因：
- 希望如何调整：
- 是否涉及需求变更：
- 用户最终意见：
- 修复后复测结果：
