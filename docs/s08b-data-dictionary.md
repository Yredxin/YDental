# S08-B 数据字典与审核契约

本字典对应真实 `ydental_treatment` 模型；S08-A 文书七项及52牙字典继续适用。所有临床内容仅合成演示，正式字段、规格/用法/频次/疗程及签发条件须业务负责人审核。未知值保留空值，不自动写“无/正常/已告知”。B不签发PDF、不生成检查结果、不生成财务账单。

所有业务记录继承原 `ydental.access.source` 的门店/法人/业务类别和原审计来源；B再限定当前门店读。患者来源是原S04患者，不建立患者副本；操作者固定真实env.uid。所有 `_new/_save` 使用不可JSON伪造对象token；普通create/write/unlink、导出和附件绕过均拒绝。UTC时间配原S03门店日期，原生单位精度；货币遵循公司币种与原生round。

|实体|权威来源及版本|空值/签发条件|
|---|---|---|
|event|当前真实S06执行+文书版本；不可变source/fingerprint|未知原价保持pending；确认后不得覆盖|
|consumption|明确核实的S07真实lot/单位/数量|不使用默认建议量当实耗；缺库可无原生move|
|fee|event唯一；S05冻结快照或独立有据历史核价|单位价格必须正；差额数量可负/材料差额可0，非默取零价|
|order/line|原医生合法接诊；草稿CAS可改；开立集合冻结|药品结构字段显式录入，不自动医学决策；新增另单|
|segment|原处方+唯一S05派生任务+实际S06段|pending时execution可空；done保留结束时间|
|price.review|price-write人员有据核实原单价|一次；不以后来价替代|
|receipt|actor+key+完整参数hash+结果|不可跨参数复用，不向客户端暴露凭据|

## ydental_treatment_consumption

|字段|Odoo类型|必填/默认|关系/选项与单位|
|---|---|---|---|
|ydental_event_id|Many2one|必填|'ydental.treatment.event'; ondelete='restrict'|
|ydental_lot_id|Many2one|必填|'stock.lot'; ondelete='restrict'|
|ydental_quantity|Float|必填|; digits='Product Unit'|
|ydental_uom_id|Many2one|必填|'uom.uom'; ondelete='restrict'|
|ydental_kind|Selection|必填|[('treatment', 'Material'), ('chairside', 'Chairside medicine'), ('prescription', 'Take-away medicine')]; |
|ydental_inventory_event_id|Many2one|可空/未知|'ydental.inventory.event'; ondelete='restrict'|

## ydental_treatment_event

|字段|Odoo类型|必填/默认|关系/选项与单位|
|---|---|---|---|
|ydental_execution_id|Many2one|必填|'ydental.queue.execution'; ondelete='restrict'|
|ydental_document_id|Many2one|可空/未知|'ydental.clinical.document'; ondelete='restrict'|
|ydental_document_version|Integer|可空/未知|; |
|ydental_order_line_id|Many2one|可空/未知|'ydental.treatment.line'; ondelete='restrict'|
|ydental_parent_id|Many2one|可空/未知|'ydental.treatment.event'; ondelete='restrict'|
|ydental_source|Char|必填|; |
|ydental_fingerprint|Char|必填|; |
|ydental_kind|Selection|必填|[('treatment', 'Treatment'), ('chairside', 'Chairside medication'), ('prescription', 'Actual dispensing'), ('correction', 'Quantity correction')]; |
|ydental_catalog_id|Many2one|必填|'ydental.intake.catalog'; ondelete='restrict'|
|ydental_quantity|Float|必填|; digits='Product Unit'|
|ydental_uom_id|Many2one|必填|'uom.uom'; ondelete='restrict'|
|ydental_teeth|Json|可空/未知|; |
|ydental_actual_at|Datetime|必填|; |
|ydental_business_date|Date|必填|; |
|ydental_station_id|Many2one|必填|'ydental.space.station'; ondelete='restrict'|
|ydental_reason|Char|必填|; |
|ydental_already_performed|Boolean|可空/未知|; |
|ydental_price_snapshot_id|Many2one|可空/未知|'ydental.intake.snapshot'; ondelete='restrict'|
|ydental_price_review_id|Many2one|可空/未知|'ydental.treatment.price.review'; ondelete='restrict'|
|ydental_pending_reason|Char|可空/未知|; |
|state|Selection|必填；default='pending'|[('pending', 'Fact awaiting reconciliation'), ('confirmed', 'Fee and stock confirmed')]; |

## ydental_treatment_fee

|字段|Odoo类型|必填/默认|关系/选项与单位|
|---|---|---|---|
|ydental_event_id|Many2one|必填|'ydental.treatment.event'; ondelete='restrict'|
|ydental_parent_id|Many2one|可空/未知|'ydental.treatment.fee'; ondelete='restrict'|
|ydental_price_snapshot_id|Many2one|可空/未知|'ydental.intake.snapshot'; ondelete='restrict'|
|ydental_price_review_id|Many2one|可空/未知|'ydental.treatment.price.review'; ondelete='restrict'|
|ydental_quantity|Float|必填|; digits='Product Unit'|
|ydental_unit_price|Float|必填|; digits=(16, 6)|
|ydental_currency_id|Many2one|必填|'res.currency'; ondelete='restrict'|
|ydental_amount|Monetary|必填|; currency_field='ydental_currency_id'|
|ydental_policy|Selection|必填|[('demo_confirmation', 'Demonstration; production pricing policy awaits approval')]; |

## ydental_treatment_line

|字段|Odoo类型|必填/默认|关系/选项与单位|
|---|---|---|---|
|ydental_order_id|Many2one|必填|'ydental.treatment.order'; ondelete='restrict'|
|ydental_mapping_id|Many2one|必填|'ydental.intake.mapping'; ondelete='restrict'|
|ydental_product_id|Many2one|可空/未知|'product.product'; ondelete='restrict'|
|ydental_quantity|Float|必填|; digits='Product Unit'|
|ydental_uom_id|Many2one|必填|'uom.uom'; ondelete='restrict'|
|ydental_specification|Char|可空/未知|; |
|ydental_usage|Char|可空/未知|; |
|ydental_frequency|Char|可空/未知|; |
|ydental_course|Char|可空/未知|; |
|ydental_reason|Char|可空/未知|; |
|ydental_task_id|Many2one|可空/未知|'ydental.intake.task'; ondelete='restrict'|
|state|Selection|必填；default='draft'|[('draft', 'Draft'), ('issued', 'Awaiting execution'), ('cancelled', 'Unperformed item cancelled'), ('started', 'Started by examination service'), ('done', 'Execution completed')]; |

## ydental_treatment_order

|字段|Odoo类型|必填/默认|关系/选项与单位|
|---|---|---|---|
|ydental_execution_id|Many2one|必填|'ydental.queue.execution'; ondelete='restrict'|
|ydental_document_id|Many2one|必填|'ydental.clinical.document'; ondelete='restrict'|
|ydental_document_version|Integer|必填|; |
|ydental_kind|Selection|必填|[('exam', 'Examination order'), ('prescription', 'Take-away prescription')]; |
|ydental_purpose|Char|必填|; |
|ydental_version|Integer|必填；default=1|; |
|state|Selection|必填；default='draft'|[('draft', 'Draft'), ('issued', 'Issued, frozen'), ('done', 'All approved quantities dispensed')]; |

## ydental_treatment_price_review

|字段|Odoo类型|必填/默认|关系/选项与单位|
|---|---|---|---|
|ydental_event_id|Many2one|必填|'ydental.treatment.event'; ondelete='restrict'|
|ydental_currency_id|Many2one|必填|'res.currency'; ondelete='restrict'|
|ydental_unit_price|Float|必填|; digits=(16, 6)|
|ydental_evidence|Char|必填|; |
|ydental_reviewed_at|Datetime|必填|; |

## ydental_treatment_receipt

|字段|Odoo类型|必填/默认|关系/选项与单位|
|---|---|---|---|
|ydental_key|Char|必填|; |
|ydental_fingerprint|Char|必填|; |
|ydental_result|Json|必填|; |

## ydental_treatment_record

|字段|Odoo类型|必填/默认|关系/选项与单位|
|---|---|---|---|
|name|Char|必填|; |
|ydental_patient_id|Many2one|可空/未知|'ydental.patient'; ondelete='restrict'|
|ydental_actor_id|Many2one|必填|'res.users'; ondelete='restrict'|

## ydental_treatment_segment

|字段|Odoo类型|必填/默认|关系/选项与单位|
|---|---|---|---|
|ydental_order_id|Many2one|必填|'ydental.treatment.order'; ondelete='restrict'|
|ydental_task_id|Many2one|必填|'ydental.intake.task'; ondelete='restrict'|
|ydental_execution_id|Many2one|可空/未知|'ydental.queue.execution'; ondelete='restrict'|
|ydental_sequence|Integer|必填|; |
|ydental_finished_at|Datetime|可空/未知|; |
|state|Selection|必填；default='pending'|[('pending', 'Awaiting explicit reporting'), ('active', 'Actual dispensing segment'), ('done', 'Segment finished')]; |

## 状态与动作

|实体|合法状态|变更入口|
|---|---|---|
|event|pending→confirmed|execute/dispense/correct；原事件reconcile只补账|
|order|draft→issued→done|order/edit_order；issue冻结；实际全部发完才done|
|line|draft/issued/cancelled/started/done|草稿修订保留旧取消行；未开始取消有原因；S09开始仍未启用|
|segment|pending→active→done|实际任务start后dispense/finish；每处方最多一个pending/active|
|原S06 execution/entry|新增completed|仅持有人finish真实药房段；原actor、lease、station历史不改|

详细动作、异常矩阵及锁序见 [契约](s08b-contracts.md)。禁止卸载模块时级联删除completed历史；回退只停止B入口，不删数据或重置旧库。
