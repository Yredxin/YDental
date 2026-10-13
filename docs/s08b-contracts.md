# S08-B 真实来源与事务合同

唯一实施依据为 #32 GPT-ACTIVATE6134476918 与 #23 当前总计划、有效评论。本批基线为 `234f5bfb6b929457533286f0956924557fc68ace`。本文件描述实现合同，不是测试通过或生产批准声明。

## 事实与边界

文书及作者版本继续由 S08-A 管理。实际项目独立写入 `ydental.treatment.event`；医嘱为 order/line；实际耗材引用 consumption；费用来源为 fee；药房每次待报到与执行历史由 segment 绑定真实 S05 task/S06 execution。原生 stock.move/move.line/quant 是唯一存货事实。没有第二套患者、队列、数量余额或财务账本。

费用为待 S10 读取的未出账来源，不是 account.move、发票、实收款项。当前价格策略明确使用 `demo_confirmation`，生产取价时点、药品审核、真实用药决定、税币种与正式签发政策没有被本批批准。用法、频次、疗程等字段必须人员输入，产品不默认医学判断。

## 准入与锁序

动作由已认证、CSRF保护的 POST 转交私有模型服务。HTTP 参数不能构造 Python 来源对象或内部 mutation token。普通 ORM create/write/unlink、RPC 私有方法、附件及导出不能绕过模型层保护。

每个 B 写事务先校验当前门店岗位权限与 server-bound S06 Connection，再按原顺序取得 S01 actor/session、S04 patient、S03 supply/space、S05 intake、S06 queue、S07 inventory、B fence。所有批次和 native move 锁在此后取得。B 来源适配器只重验已持有的授权与不可变来源，不在库存锁后请求新的上游 fence。S07 自身库存事务不反向调用 B 队列锁。独立双 backend/真实 barrier/有界 serialization retry 是运行验收条件。

医疗动作必须是当前本人、可信连接、有效 lease、medical serving、当前工位能力及人员资质、当前真实文书已保存版本；旧页、旧版本、过期连接、撤权及跨店在锁内重验。处方发药必须 pharmacy serving 与本次原处方任务/版本，不依赖前端按钮隐藏。

## 事件、价格、费用、库存矩阵

|来源状态|临床事实|冻结价|费用|库存|失败出口|
|---|---|---|---|---|---|
|纯草稿/确认文字/开方/报到/叫号|不生成实际项目|不取价|0变化|0变化|原 S08-A/S05/S06 回滚|
|新执行前缺料/缺价/批次禁用或过期|拒绝新增已执行|不伪0|不生成|不扣|整个 savepoint 回滚|
|合法实际执行|唯一实际事件|S05唯一有效发布价及 native rule核对|唯一来源|真实 native move|同 source/key 返回原记录|
|已实际发生但缺价|原事件和责任/时间保留|UNKNOWN，显式 missing_price|暂缓|暂缓|price-write 人员有据核原价，再由原来源核对|
|已实际发生但库存短缺|原事件保留|原价保留|暂缓|原 S07 pending，无伪入库|真实入库/正向盘点证据后恢复原 S07 event，再核对原 B event|
|已实际发生且原生业务异常|原事件及责任/时间保留|原价保留|经济savepoint回滚|无半move/半费用|bookkeeping_failed，保留失败代码审计，原actor核对；DB serialization/deadlock仍抛回框架|
|数量更正|新增关联差额事件|沿原快照|差额/反向来源|新增实耗或独立实物退回|不能覆写原事件/费用|
|实物退回|既往实发不删|旧费源不变|不自动退款|原 S07 quarantine，核验后才可能释放|不恢复处方可领总额|

执行事实、费用、库存之间以数据库唯一约束和引用核验。无价时不默取0；之后调价不自动重取；人工核价必须正数、原币种和证据引用，形成独立不可变 review。无法核实原价继续待核对。

## 医嘱与药房状态动作

|动作|前置/权限|原子副作用|失败出口|
|---|---|---|---|
|order/edit_order|当前 medical serving +已保存文书/CAS|草稿独立；重编保留旧草稿行|不改已开立集合|
|issue|原接诊、草稿版本|冻结集合/版本；检查各精确任务或处方唯一待报到段|不自动入队/扣库/计费|
|cancel_exam|当前合法患者、已开立未开始、附原因|取消未做行及其号码/任务|已开始拒绝，不伪取消|
|dispense|本人 pharmacy serving、原处方版本/行、真批次|实际事件/费用/原生库存同事务；累计不得超批准量|未实发的缺价缺料拒绝；明确已实发则保留pending及批准量占用，账未齐禁finish；同键/源不双发|
|finish|本次合法持有人、所有本段账实已确认|原 execution/entry completed、task done、append ended、原 actor/station/time保留、释放工作台 lease|剩余同原处方唯一新 task，pending，不自动报到|
|refer|真实 medical来源、精确目标区域/能力、目标法人授权|S05 原定时预约扣额或不定时有效期记录|失败回滚；不宣称原治疗完成或交还|

4+2 流程是一个原处方、两个真实发药段和两个 native issue move（4、2），累计6；余量任务与原门诊资格分离，不再次扣原门诊名额。每个新段独立明确报到、叫号、start；closed 追加沿原 S06 按 task/date 控制，已结束许可不转借。退回不重开可领量。

本批上层新增 queue.execution/entry `completed` 及终态时间约束，保留未解决患者/lease部分唯一索引。完成状态不可通过卸载模块删除历史。S06超时、清理、推送继续处理同一权威记录。S09未启用时真实检查开始/结果继续明确拒绝，不冒充检查完成。

## 幂等、错误与审计

B receipt 使用 actor+request key唯一约束及完整参数hash；执行 store+source唯一；fee每event唯一；consumption每event+lot唯一；pharmacy segment每task、order+sequence唯一且每order仅一个待报到/活动段。客户端响应不明留原页和核对入口，不自动重放。危险动作先明确确认范围，请求中冻结输入，比较完整输入再决定刷新；S08-A原终态保护保留。

错误前缀包括 access_denied、execution_required、save_required、version_conflict、invalid_quantity、invalid_order、order_frozen、missing_price、inventory_pending、overdispense、source_category_mismatch、exam_integration_required、policy_unpublished。看、草稿、开立、实际执行、发药、段结束、数量更正、物理退回、核价、恢复、转诊分别审计，实际操作者不因受控sudo改变。

## 尚未启用

S08-C PDF/签署/打印、S09真实检查执行/设备/报告、S10真正出账收退款、S11及生产验证 NOT_RUN。S07历史SIGSEGV与共享内存长期增长根因仍未知；开发安装通过不能解除生产BLOCKED。真实患者/药品决策与正式业务字段审核不由合成测试代替。


## 原始时间、价源与牙位

实际时间使用明确UTC秒值，留空为确认时间；必须在当前已开始执行段内且不晚于服务器当前时间。事件冻结门店日期/actor/station/doc version，S07原event和后续补账保留原actual_at，不把补账时间改成业务发生时间。物理发药新事件采用本次真实确认时点。价格由医嘱行精确S05服务catalog取价；S07物理medicine由原处方product锁定，批次必须相同，单位必须与药品和服务单位一致。演示策略不等于正式药品售价、税币种或审核政策已批准。

实际项目牙位状态必须显式选择存在/缺失/未知；0只可与“不适用”配对。牙面规则复用A的同一真实内容校验器。A仍保留52牙可操作图及七文本独占/终态冻结；B不自动把选择牙号解释为正常临床结论。

## 全部动作参数

HTTP只接受operation/revision/connection/key/payload及Odoo CSRF。payload严格按下表Python签名绑定，未知字段和客户端单价拒绝。请求key为actor作用域；source为本店不可变业务来源，JSON不能传可信Pythonpermit对象。

|动作|实际参数（代码签名）|
|---|---|
|execute|`execution_id, lease_id, lease_token, document_id, document_version, catalog_id, quantity, source, reason, materials, teeth, already_performed, policy, actual_at=None`|
|reconcile|`event_id, reason`|
|review_price|`event_id, unit_price, currency_id, evidence`|
|correct|`event_id, execution_id, lease_id, lease_token, document_id, document_version, delta, source, reason, materials`|
|return_material|`event_id, inventory_event_id, quantity, uom_id, source, reason`|
|order|`execution_id, lease_id, lease_token, document_id, document_version, kind, purpose, lines`|
|edit_order|`order_id, version, execution_id, lease_id, lease_token, document_id, document_version, purpose, lines`|
|issue|`order_id, version, execution_id, lease_id, lease_token, document_id, document_version`|
|cancel_exam|`line_id, order_version, execution_id, lease_id, lease_token, document_id, document_version, reason`|
|dispense|`execution_id, lease_id, lease_token, order_id, order_version, line_id, lot_id, quantity, source, reason, policy, already_performed=False`|
|finish|`execution_id, lease_id, lease_token, order_id, order_version, reason`|
|refer|`execution_id, lease_id, lease_token, document_id, document_version, mode, mapping_id, reason, start=None, end=None, valid_until=None, source=None`|

## 稳定错误前缀与审计来源

错误：access_denied, already_started, correction_required, exam_integration_required, execution_required, history_immutable, invalid_action, invalid_material, invalid_order, invalid_quantity, invalid_referral, invalid_source, invalid_time, missing_price, order_frozen, overdispense, policy_unpublished, qualification_required, reconcile_required, save_required, source_category_mismatch, source_required, version_conflict。上游S01/S05/S06/S07错误前缀与翻译沿用。

B审计：treatment.actual_dispense, treatment.actual_execution, treatment.bookkeeping_pending, treatment.exam_unperformed_cancel, treatment.execution_view, treatment.historical_price_review, treatment.order_draft, treatment.order_draft_edit, treatment.order_issued, treatment.order_view, treatment.pharmacy_completed, treatment.pharmacy_segment_finished, treatment.physical_return_quarantine, treatment.reconcile, treatment.referral_initiated；另有queue.pharmacy_completed及原inventory.movement审计。审计scope为真实门店/大类/操作者，内容只记录必要ID/状态/原因，不输出编辑或连接凭据。

## 回退与历史保护

回退先关闭B入口或停止精确config/hash/PID匹配的专属预览，保留B数据库、filestore、日志和全部Git提交。不可将含completed历史的B库直接用A代码升级或卸载B，不级联删除已完成段。需要回退演练时使用另一全新隔离库；生产数据迁移与部署不在本批授权内。
