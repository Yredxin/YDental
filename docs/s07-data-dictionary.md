# S07 数据字典｜YD-N1 R1

来源为[#31](https://github.com/Yredxin/YDental/issues/31)及其正式启用。此字典描述当前实际模型；不定义S08/S10/S11未来业务。固定product/test/final及TC结果见[s07-report.md](s07-report.md)。动作、错误、事务与来源payload见[s07-contracts.md](s07-contracts.md)。

## 共同字段、权限与历史

`ydental.inventory.config/event/operation/batch`均继承`ydental.inventory.record`及S01`ydental.access.source`。原生库位/批次/移动扩展字段是同一原生表的列，不另建库存账。

|共同字段|类型/必填/默认|来源及归属|读写/保留/约束|
|---|---|---|---|
|id|原生integer主键|数据库分配；永久内部标识|不以显示码代替，不重编号|
|name|Char，必填|受控服务写入动作/来源名称|原事件不因主数据更名重建|
|ydental_store_id|Many2one→ydental.access.store，必填，restrict，index|可信session/来源对象；法人由store.company_id|实时warehouse-read；事件调拨目标例外只读；公司restriction；普通归属改写拒绝|
|ydental_category|Selection，必填，默认warehouse|服务器固定业务大类|不从客户端提权；S01审计分类|
|ydental_version|Integer，必填，默认1，readonly|_save在同事务递增|不可普通写/import；原生移动/来源历史保留|
|create_uid/create_date/write_uid/write_date|原生用户/naive UTC时间|ORM，sudo不改变本批真实uid；另外显式actor字段|用于工程追溯，业务actual_at独立|

共同权限：warehouse实时read（当前店）+导出另需export-write；普通create/write/unlink全拒绝。集团产品catalog权限不授予事件/数量读取。所有关系ondelete=restrict；原生必需关系按核心保留。可信token只在服务私有方法中生成；没有可写余额字段或客户端授权flag。

## 模型/字段实表

下列字段类型/默认值直接对应本批模型声明。required未标注表示False，default未标注表示原生空值/False；readonly是界面语义，模型级token/来源scope仍构成真正写保护。Float库存结果用Product Unit精度，digits=0表示输入原精度，避免先截断再换算。Json快照/回执只接受受控服务生成对象，不承载患者病历或附件。

### product.template

实现：`ydental_inventory/models/product_template.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_inventory_kind|Selection [('medicine', 'Medicine'), ('material', 'Material'), ('prosthesis', 'Prosthesis')]|readonly=True; string='Inventory product kind'|
|ydental_specification|Char |readonly=True; string='Specification'|
|ydental_issue_uom_id|Many2one 'uom.uom'|readonly=True; ondelete='restrict'; string='Issue unit'|
|ydental_stock_step|Float |default=0.01; readonly=True; digits=0; string='Minimum stock quantity step'|
|ydental_suggested_quantity|Float |readonly=True; digits='Product Unit'; string='Suggested quantity only'|

### stock.location

实现：`ydental_inventory/models/stock_location.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_store_id|Many2one 'ydental.access.store'|readonly=True; ondelete='restrict'; index=True; string='Inventory store'|

### stock.lot

实现：`ydental_inventory/models/stock_lot.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_store_id|Many2one 'ydental.access.store'|readonly=True; ondelete='restrict'; index=True; string='Inventory store'|

### stock.move

实现：`ydental_inventory/models/stock_move.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_store_id|Many2one 'ydental.access.store'|readonly=True; ondelete='restrict'; index=True; string='Inventory store'|

### stock.move.line

实现：`ydental_inventory/models/stock_move_line.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_store_id|Many2one 'ydental.access.store'|readonly=True; ondelete='restrict'; index=True; string='Inventory store'|

### stock.quant

实现：`ydental_inventory/models/stock_quant.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_store_id|Many2one 'ydental.access.store'|readonly=True; ondelete='restrict'; index=True; string='Inventory store'|

### stock.warehouse

实现：`ydental_inventory/models/stock_warehouse.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_store_id|Many2one 'ydental.access.store'|readonly=True; ondelete='restrict'; index=True; string='Inventory store'|

### ydental.inventory.batch

实现：`ydental_inventory/models/ydental_inventory_batch.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_lot_id|Many2one 'stock.lot'|required=True; ondelete='restrict'; string='Native manufacturer lot'|
|ydental_enabled|Boolean |default=True; string='Store lot enabled'|
|ydental_received_at|Datetime |readonly=True; string='First actual store receipt'|
|ydental_processing_reference|Char |readonly=True; string='Stable processing source'|

数据库约束：

- `models.Constraint('UNIQUE(ydental_store_id, ydental_lot_id)', 'Each store has one lifecycle for a manufacturer lot.')`

### ydental.inventory.config

实现：`ydental_inventory/models/ydental_inventory_config.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_warehouse_id|Many2one 'stock.warehouse'|required=True; ondelete='restrict'; string='Warehouse'|
|ydental_medicine_id|Many2one 'stock.location'|required=True; ondelete='restrict'; string='Pharmacy location'|
|ydental_material_id|Many2one 'stock.location'|required=True; ondelete='restrict'; string='Material location'|
|ydental_prosthesis_id|Many2one 'stock.location'|required=True; ondelete='restrict'; string='Prosthesis awaiting collection'|
|ydental_quarantine_id|Many2one 'stock.location'|required=True; ondelete='restrict'; string='Return verification location'|
|ydental_supplier_id|Many2one 'stock.location'|required=True; ondelete='restrict'; string='Supplier location'|
|ydental_customer_id|Many2one 'stock.location'|required=True; ondelete='restrict'; string='Actual issue location'|
|ydental_loss_id|Many2one 'stock.location'|required=True; ondelete='restrict'; string='Loss location'|
|ydental_policy_configured|Boolean |string='Alert policy configured'|
|ydental_near_days|Integer |string='Near expiry days'|
|ydental_wait_days|Integer |string='Collection alert days'|
|ydental_low_quantity|Float |string='Low stock quantity'; digits='Product Unit'|
|ydental_policy_reason|Char |string='Policy reason'|

数据库约束：

- `models.Constraint('UNIQUE(ydental_store_id)', 'Each store has one inventory warehouse.')`
- `models.Constraint('UNIQUE(ydental_warehouse_id)', 'Inventory warehouses cannot be shared between stores.')`
- `models.Constraint('CHECK(ydental_near_days >= 0 AND ydental_wait_days >= 0 AND ydental_low_quantity >= 0)', 'Alert thresholds cannot be negative.')`

### ydental.inventory.event

实现：`ydental_inventory/models/ydental_inventory_event.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_source_key|Char |required=True; index=True; string='Source key'|
|ydental_kind|Selection [('receipt', 'Receipt'), ('replenishment', 'Replenishment'), ('treatment', 'Treatment consumption'), ('chairside', 'Chairside medicine'), ('prescription', 'Take home prescription'), ('inventory', 'Inventory correction'), ('transfer', 'Same company transfer'), ('return', 'Physical return'), ('verification', 'Return verification')]|required=True; string='Source kind'|
|ydental_source_namespace|Char |required=True; string='Source namespace'|
|ydental_count_fingerprint|Char |readonly=True; string='Original count fingerprint'|
|ydental_fingerprint|Char |required=True|
|ydental_product_id|Many2one 'product.product'|required=True; ondelete='restrict'; string='Product'|
|ydental_lot_id|Many2one 'stock.lot'|required=True; ondelete='restrict'; string='Lot'|
|ydental_quantity|Float |required=True; digits='Product Unit'; string='Stock quantity'|
|ydental_input_quantity|Float |required=True; digits=0; string='Confirmed input quantity'|
|ydental_uom_id|Many2one 'uom.uom'|required=True; ondelete='restrict'; string='Confirmed input unit'|
|ydental_unit_snapshot|Json |required=True; string='Unit precision snapshot'|
|ydental_from_id|Many2one 'stock.location'|required=True; ondelete='restrict'; string='From location'|
|ydental_to_id|Many2one 'stock.location'|required=True; ondelete='restrict'; string='To location'|
|ydental_target_store_id|Many2one 'ydental.access.store'|ondelete='restrict'; string='Transfer target'|
|ydental_move_id|Many2one 'stock.move'|ondelete='restrict'; string='Native movement'|
|ydental_parent_id|Many2one 'ydental.inventory.event'|ondelete='restrict'; string='Original issue or return'|
|ydental_responsible_id|Many2one 'res.users'|required=True; ondelete='restrict'; string='Responsible user'|
|ydental_actor_id|Many2one 'res.users'|required=True; ondelete='restrict'; string='Actual source actor'|
|ydental_summary|Char |string='Necessary execution summary'|
|ydental_reason|Char |required=True; string='Evidence and reason'|
|ydental_price_snapshot|Json |string='Original price snapshot'|
|ydental_fee_reference|Char |string='Original fee association'|
|ydental_actual_at|Datetime |required=True; string='Actual source time'|
|ydental_synthetic|Boolean |string='Synthetic validation source'|
|state|Selection [('pending', 'Pending reconciliation'), ('done', 'Stock confirmed'), ('observed', 'Count matched; no stock movement')]|required=True; default='done'|

数据库约束：

- `models.Constraint('UNIQUE(ydental_store_id, ydental_source_namespace, ydental_source_key)', 'An inventory source is applied once.')`

### ydental.inventory.mutex

实现：`ydental_inventory/models/ydental_inventory_mutex.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_revision|Integer |default=0|

### ydental.inventory.operation

实现：`ydental_inventory/models/ydental_inventory_operation.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|ydental_key|Char |required=True|
|ydental_fingerprint|Char |required=True|
|ydental_result|Json |required=True|
|ydental_actor_id|Many2one 'res.users'|required=True; ondelete='restrict'|

数据库约束：

- `models.Constraint('UNIQUE(ydental_store_id, ydental_key)', 'Inventory request keys are unique within the store.')`

### ydental.inventory.record

实现：`ydental_inventory/models/ydental_inventory_record.py`；#31/S07-T01—T09按下方用途映射。

|字段|类型/关系/枚举|必填/默认/精度及字段说明|
|---|---|---|
|name|Char |required=True|
|ydental_category|Selection |default='warehouse'|
|ydental_version|Integer |default=1; required=True; readonly=True; string='Version'|

## 模型用途与字段来源

|模型|来源/公司/门店/负责人|状态/版本/生命周期|数据权限、迁移与TC|
|---|---|---|---|
|config|warehouse-write的setup；warehouse.company=store.company|每店唯一、warehouse唯一；版本递增；policy初始未配置|所有库位由服务器类别创建，不接受任意库位；T08/T09|
|batch|lot创建或真实同法人调入；store×native lot唯一|本店enabled、首次实际received_at；processing_reference当前空，S11未接入|无数量/余额；本店启停互不影响；T03/T08/T09|
|event|warehouse证据动作或可信临床来源；store/actor/responsible明确|pending→done；盘点相符observed；done绑定原生move；来源键唯一|普通不可改删；原snapshot/fee ref/actual time不变；T01—T09/F1—F3|
|operation|本店动作+请求key+指纹，真实actor|store×key唯一；result只存受理必要ID/状态/数量|重试原回执，无患者记录；T01/T02/T05/T06|
|mutex|模块数据建立一行；无业务公司/患者|revision仅用于RR竞争强制重试|无普通ACL，不对外返回；SQL固定语句；T02真实双连接|
|原生扩展|product为集团物资定义；stock对象company/store由受控service|native stock业务状态；批次expiry原生；原生表扩展列为可空兼容普通Odoo对象|不接管历史仓库；本批新库install/u实测；T03/T07/T08/T09|

## 直接复用的原生字段与API

|对象/字段|原生语义/精度/关系|本批使用与写入口|保留、安全及TC|
|---|---|---|---|
|product.template/product.product：name/default_code/type/is_storable/tracking/use_expiration_date/uom_id/active|集团产品、原生库存类型consu+storable、lot追踪、单位及停用|集团product/product_edit服务；售价不取list_price，不改S05price|原生产品唯一ID；不通过原生qty_available读出跨店量；T04/T07/T09|
|uom.uom：name/relative_uom_id/relative_factor/factor/parent_path/active|原生单位树和换算；Product Unit decimal.precision|仅明示stock/issue两单位；已引用祖先换算冻结|无uom.rounding旧API；事件冻结实际factor/digits/step；T04|
|stock.warehouse：company_id/code/view_location_id/lot_stock_id|法人仓库及真实原生层级|本店setup建立新仓库；不重新归属已有仓库|company固定由门店推导；warehouse不可多店共用；T08/T09|
|stock.location：company_id/location_id/usage|native internal/supplier/customer/inventory层级|类别归位、退回待核查和损失固定目标|外部不能传任意库位；原生入口写受控token；T05/T07/T08|
|stock.lot：name/ref/product_id/company_id/expiration_date|厂家批次、产品法人及naive UTC效期|本店lot创建；调拨使用同一native lot；store生命周期另表|过期新执行服务端拒绝；不复活过期批次；T03/T08|
|stock.move：product_id/uom_id/product_uom_qty/quantity/location_id/location_dest_id/company_id/origin/state/is_inventory/picked|原生移动需求/实量/路径/状态；库存单位精度|受控service建confirm/unreserve/实际行/done；origin稳定关联event ID|native done历史不可普通删/改；所有原生变动与来源/审计一事务；T01/T02/T05/T08|
|stock.move.line：move_id/product_id/lot_id/uom_id/quantity/location_id/location_dest_id/company_id/picked|实际批次、单位、用量|每事件明确一组实际行，不用未确认建议量|失败无半行；准确对账；T01/T02/T04|
|stock.quant：product_id/lot_id/location_id/quantity/reserved_quantity/owner_id/package_id/in_date|原生实际/预留、批次位置和入库时间|native _action_done维护；工作台只读投影quantity-reserved|无自研平行余额；盘点拒reservation/owner/package；internal禁负；T02/T04/T08|
|res.currency/ydental.intake.snapshot：币种/精度/price_id/unit_price/amount|S05已冻结演示快照|可信来源冻结JSON，recover不quote当前价|真实S05调价20→99后仍用原version/20/amount；真实费用NOT_RUN；T06|
|ydental.access.audit全部S01字段|原生用户/门店/事件/类别/目标/结果/原因/前后/来源|inventory.*注册S01，真实发起者；查看/导出有审计|原生不可改删；仅必要元数据；T01—T09|
|ir.attachment/res.partner/ydental.patient.clinical|S04已有患者/附件边界|库存不建立病历附件；库存/批次/移动来源的无类型附件拒绝|public flag/content token不绕过；仓管不读全病历；T07|

## Json契约与投影

|字段/接口|确定结构|不允许/空值处理|
|---|---|---|
|unit_snapshot|input_uom/stock_uom/input_factor/stock_factor/digits/stock_step|原native精度冻结，不能用客户端默认值；无静默截断|
|price_snapshot|version/currency/unit_price；合成引用真实S05时另有snapshot_id/amount|非临床库存来源可空；可信临床来源缺version/currency/价格拒绝；不是费用凭证|
|fee_reference|原可信来源给出的稳定关联字符串|warehouse普通事件可空；本批合成前缀S07-SYNTHETIC-FEE，不生成S10费用|
|operation.result|accepted状态及原event/move/config/product ID、数量/版本等|无患者完整数据、session/cookie/token；重试只回原结果|
|工作台lot|native ID、产品名称、类别、库存单位、实存/可发/待核查、效期、实际入库、启停和预警|过期/停用实存保留，可发0；无全店/集团预测量|
|工作台event|event ID/kind/state/quantity/product/lot/move/必要summary/责任人/synthetic|无患者ID、完整病历、附件、任意域查询；目标店仅看对应transfer|
|扫码|result=unsupported_source，received=false|不接受授权token；未装S11不能写加工入库成功|

## 安装、迁移与保留

本批新模块是加表/加列，native列可空以兼容普通原生对象；没有迁移S00—S06历史库。install及真实-u在新S07库中运行；有业务数据后的-u用event/batch/move/move_line/quant签名比较证明本次原生库存/来源历史不漂移，不冒称已升级完整历史生产库存。任何未来生产迁移仍需独立授权与真实数据核查。原失败库、失败证据和迭代提交保留，不重置/接管/删除。
