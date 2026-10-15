# S10-E2E-W1：真实工作台费库款全链 BLOCKED

## 执行边界

- 授权：[GitHub #34 comment 6184776579](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184776579)。固定起点 `7efa4e25583b667cc0de22d115b54d67d0d10a3b`，原分支、Odoo20 core、S10/S07 服务及结算 controller/QWeb 哈希全部相符。#23、#29—#34 的正文和有效评论、#35 状态已 API 读取；执行前无更新授权或并行交付。
- [主预检](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184932354)及[最终脚本哈希补充](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184949645)均在 CREATE 前发表并 API 逐字读回。真实 Odoo20 参数解析通过；完整浏览器 Fake 流程和异常门禁为 `SIMULATED_PASS`，不算真实业务验收。
- 唯一只读源 `ydental_s10_test_20261014044700_4f6a8d2c` / OID2100080，精确92模块、业务空、0活动连接、124个文件及附件哈希匹配。仅新建 `ydental_s10_test_20261015051000_e2e1a7b4` / **OID2100269** / 18277；独立 config、marker、filestore 校验通过。

## 实际结果

准备 shell 1/1，exit0、signal11=false；仅建立合成角色、门店、患者、工位/容量、发布价格、两批次入库及演示日记账。准备后治疗事件、fee、发票、收款、核销均为0。HTTP进程1/1，启动成功，精确停止后exit0、signal11=false。Firefox 1/2，进程exit1；第二次因首轮已成功提交治疗600，**按授权禁止运行**。模块升级0，新建库1/1。

真实 Firefox 成功的前六步：前台预约303、到店303、报到200；医生接诊200、独立文书保存200、治疗工作台表单提交200。只读终态证实治疗 event **1** 为 `confirmed`，fee **1** 为600.00、价格快照 **1** 单价600.00；S07物料出库 event **3** 数量1、原生 stock.move **3** 为 `done`。两条前置合成入库 event 1/2 各20为准备阶段，未算本批网页发药。S01审计含 `treatment.actual_execution` 与 `inventory.movement` 的 accepted 行。

**停止位置：**医生在治疗页通过真实表单保存并签发一张检查医嘱，HTTP动作成功；只读终态显示医嘱 **1** `issued`、行 **1** 对应待报到任务 **2**。随后执行器等待该医嘱卡片内的 `.task-id` 30秒超时。当前 QWeb 的 `.task-id` 只出现在药房 `segment` 列表；检查医嘱没有该元素。该失败是本批浏览器夹具错误，不能归因于检查产品功能缺失，也不能把检查结果称作 PASS。前台队列存在合法待报到任务入口，但本次未继续点击。已保留原运行脚本与完整私有证据，未在提交后修改脚本或重复浏览器。

后续检查实际执行80、处方、药房实发4+2、原生药品出库、出账740、收500/240均 **NOT_RUN_POLICY_STOP**。终态 `ydental.exam.result`、结算source/receipt/payment、account.move/payment/partial均0；没有原生发票或付款可供本批核销验收。三类费用、资金、审计链不能拼为S10完整PASS。mail_mail=0；模板源仍OID2100080、业务fee=0，源与目标均无活动连接。

## 证据与后续复核点

[脱敏机器证据](evidence/s10-e2e-w1/verification.json)列出执行的真实HTTP步骤、事件哈希、固定 OID、逐ID事件→快照→fee→stock.move、检查医嘱/任务、S01审计及原生账务零计数。原始浏览器事件、失败栈、Odoo私有日志和完整数据库/filestore留在 `.local/ydental_s10_test_20261015051000_e2e1a7b4/`；不上传账号密码、患者资料、原始日志或PDF。此轮没有截图，视觉截图证据为 `NOT_RUN`；Web动作以真实Firefox POST及只读DB/S01对照为限。

建议 GPT 独立复核后另行限定恢复方案：检查任务 ID 应从实际前台队列待报到项或检查行关联入口获取，而不能依赖治疗页仅供药房段显示的 `.task-id`。恢复应明确定义已提交治疗600与已签发检查医嘱的复用/幂等边界、允许的测试库和额度；本批不自发修改执行器再跑。历史库、事故现场和新失败库全部保全；S10整体技术及生产仍 `BLOCKED`，Native SIGSEGV 根因 `UNKNOWN`，S11 `NOT_STARTED`。
