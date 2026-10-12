# S05字段字典｜YD-N1 R1

仅记录#29已实现模型。完整状态/动作/权限、锁序及恢复见[s05-contracts.md](s05-contracts.md)，测试与commit见[s05-report.md](s05-report.md)。下列字段由最终源声明逐个展开，不以源码引用代替字段列表。所有自研业务字段为ydental_前缀；Odoo原生name/active/state/id及日志字段保留原名。

## 共同归属与权限

`ydental.intake.record`继承S01 `ydental.access.source`。普通CRUD不得写业务字段，必须受控server action；删除一律拒绝。私有_new/_save只接受不可伪造mutation对象，_save逐条增加乐观version。source store→法人由S01实时检查；不重复复制company。索引/唯一约束在下方逐个列出，Many2one全部restrict保留历史。

catalog：集团共享，允许当前门店frontdesk/price/medical/exam读取；维护需集团权限和price write。mapping：相同必要角色仅本店读取，维护本店price write。price/snapshot：本店price read，价目维护price write；演示snapshot明确price write且写会话检查，不能当费用。业务entitlement/task/arrival/position/referral：仅当前门店frontdesk/medical/exam read；前台受控写、医生仅受控转诊或未来可信来源。operation：actor本人并满足记录业务类读取；不开放任意写/删。mutex无普通ACL。源导出均需export write及读取。附件不作为S05患者业务入口。

全部业务对象原生日志字段：`id`整数稳定主键；`create_uid/write_uid`原生用户关系、`create_date/write_date`naive UTC；CRUD入口受上述保护。真实业务发起者另外保存在receipt、audit和专项actor字段，不把sudo创建人冒称发起人。默认值写“原生/空”时，由Odoo字段类型处理，未自造业务默认。

## 引用与历史

catalog.product→原生product.product/template；产品UoM/类别等由受控catalog创建。mapping→集团catalog、本店报到area、执行area，不能任意跨店。price→catalog、原生pricelist/item/currency/uom；快照冻结名称/单位/数量/币种/精度/版本/取价时间。entitlement→S03唯一claim；claim内slot、policy、原池及event/operation是唯一容量来源。task→独立entitlement或可信parent task；position→明确task，没有医生/工位/号序字段。

患者业务记录都有canonical `ydental_patient_id`、不可变`ydental_origin_patient_id`和`ydental_identity_snapshot`。merge仅迁移live canonical引用和版本，其余历史不重写。arrival是历史事实，保留origin/canonical原引用，查询通过S04 identity IDs覆盖旧身份；不合并/改造旧日期。referral来源task为历史引用，不赋予来源医生目标店普通写权。

金额字段的currency_field均为ydental_currency_id；snapshot.quantity保存原生Product Unit精度，另外冻结quantity_digits和currency_rounding。价格/到店/位置时间均UTC，arrival.date按store时区，timezone冻结。幂等fingerprint仅对规范JSON请求摘要，不存认证密钥。

## product.template

来源 `ydental_intake/models/native.py`；继承 ['product.template', 'ydental.intake.native']。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_intake_owned`|Boolean: 继承关系/标签或原生值|required=继承/否; default=原生/空|readonly=True; copy=True|

## product.pricelist

来源 `ydental_intake/models/native.py`；继承 ['product.pricelist', 'ydental.intake.native']。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_intake_owned`|Boolean: 继承关系/标签或原生值|required=继承/否; default=原生/空|readonly=True; copy=True|
|`ydental_intake_store_id`|Many2one: 'ydental.access.store'|required=继承/否; default=原生/空|readonly=True; ondelete='restrict'|

## ydental.intake.entitlement

来源 `ydental_intake/models/ydental_intake_business.py`；继承 'ydental.intake.record'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_patient_id`|Many2one: 'ydental.patient'|required=True; default=原生/空|ondelete='restrict'; index=True|
|`ydental_origin_patient_id`|Many2one: 'ydental.patient'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_identity_snapshot`|Json: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_mapping_id`|Many2one: 'ydental.intake.mapping'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_claim_id`|Many2one: 'ydental.supply.claim'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_channel`|Selection: [('reservation', 'Reservation'), ('phone', 'Telephone'), ('walkin', 'Walk-in')]|required=True; default=原生/空|无额外声明|
|`state`|Selection: [('held', 'Valid unused qualification'), ('started', 'Started, cannot return capacity'), ('cancelled', 'Qualification cancelled')]|required=True; default='held'|无额外声明|
|`ydental_source_task_id`|Many2one: 'ydental.intake.task'|required=继承/否; default=原生/空|ondelete='restrict'|
|`ydental_reason`|Char: 继承关系/标签或原生值|required=继承/否; default=原生/空|无额外声明|

数据库约束/索引：

- `_claim_unique`：`models.Constraint('UNIQUE(ydental_claim_id)', 'A claim belongs to one current qualification.')`

## ydental.intake.task

来源 `ydental_intake/models/ydental_intake_business.py`；继承 'ydental.intake.record'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_patient_id`|Many2one: 'ydental.patient'|required=True; default=原生/空|ondelete='restrict'; index=True|
|`ydental_origin_patient_id`|Many2one: 'ydental.patient'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_identity_snapshot`|Json: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_mapping_id`|Many2one: 'ydental.intake.mapping'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_entitlement_id`|Many2one: 'ydental.intake.entitlement'|required=继承/否; default=原生/空|ondelete='restrict'|
|`ydental_parent_task_id`|Many2one: 'ydental.intake.task'|required=继承/否; default=原生/空|ondelete='restrict'|
|`ydental_source_kind`|Selection: [('independent', 'Independent service'), ('continuation', 'Same encounter continuation'), ('derived', 'Derived external service')]|required=True; default='independent'|无额外声明|
|`state`|Selection: [('pending', 'Pending reporting'), ('accepted', 'Intake position accepted'), ('started', 'Started by downstream server'), ('done', 'Finished by downstream server'), ('cancelled', 'Qualification cancelled')]|required=True; default='pending'|无额外声明|
|`ydental_missed_count`|Integer: 继承关系/标签或原生值|required=继承/否; default=0|无额外声明|
|`ydental_reason`|Char: 继承关系/标签或原生值|required=继承/否; default=原生/空|无额外声明|

## ydental.intake.arrival

来源 `ydental_intake/models/ydental_intake_business.py`；继承 'ydental.intake.record'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_patient_id`|Many2one: 'ydental.patient'|required=True; default=原生/空|ondelete='restrict'; index=True|
|`ydental_origin_patient_id`|Many2one: 'ydental.patient'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_identity_snapshot`|Json: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_date`|Date: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_timezone`|Char: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_occurred_at`|Datetime: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_actor_id`|Many2one: 'res.users'|required=True; default=原生/空|ondelete='restrict'|

数据库约束/索引：

- `_arrival_unique`：`models.Constraint('UNIQUE(ydental_store_id, ydental_patient_id, ydental_date)', 'One arrival fact per patient, store and local date.')`

## ydental.intake.position

来源 `ydental_intake/models/ydental_intake_business.py`；继承 'ydental.intake.record'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_patient_id`|Many2one: 'ydental.patient'|required=True; default=原生/空|ondelete='restrict'; index=True|
|`ydental_origin_patient_id`|Many2one: 'ydental.patient'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_identity_snapshot`|Json: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_task_id`|Many2one: 'ydental.intake.task'|required=True; default=原生/空|ondelete='restrict'; index=True|
|`ydental_active`|Boolean: 继承关系/标签或原生值|required=继承/否; default=True|无额外声明|
|`ydental_accepted_at`|Datetime: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_reason`|Char: 继承关系/标签或原生值|required=继承/否; default=原生/空|无额外声明|

数据库约束/索引：

- `_one_position`：`models.UniqueIndex('(ydental_patient_id) WHERE ydental_active')`

## ydental.intake.referral

来源 `ydental_intake/models/ydental_intake_business.py`；继承 'ydental.intake.record'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_patient_id`|Many2one: 'ydental.patient'|required=True; default=原生/空|ondelete='restrict'; index=True|
|`ydental_origin_patient_id`|Many2one: 'ydental.patient'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_identity_snapshot`|Json: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_mapping_id`|Many2one: 'ydental.intake.mapping'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_source_task_id`|Many2one: 'ydental.intake.task'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_valid_until`|Datetime: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_task_id`|Many2one: 'ydental.intake.task'|required=继承/否; default=原生/空|ondelete='restrict'|
|`state`|Selection: [('pending', 'Pending target walk-in qualification'), ('accepted', 'Target qualification acquired')]|required=True; default='pending'|无额外声明|
|`ydental_reason`|Char: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|

## ydental.intake.catalog

来源 `ydental_intake/models/ydental_intake_catalog.py`；继承 'ydental.intake.record'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_store_id`|Many2one: 继承关系/标签或原生值|required=False; default=原生/空|无额外声明|
|`ydental_category`|Selection: 继承关系/标签或原生值|required=继承/否; default='price'|无额外声明|
|`active`|Boolean: 继承关系/标签或原生值|required=继承/否; default=True|无额外声明|
|`ydental_code`|Char: 继承关系/标签或原生值|required=True; default=原生/空|index=True|
|`ydental_kind`|Selection: [('care', 'Outpatient'), ('exam', 'Examination'), ('medicine', 'Medicine'), ('procedure', 'Procedure'), ('prosthesis', 'Prosthesis')]|required=True; default=原生/空|无额外声明|
|`ydental_product_id`|Many2one: 'product.product'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_capability_id`|Many2one: 'ydental.access.capability'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_qualification`|Char: 继承关系/标签或原生值|required=继承/否; default=原生/空|string='Required qualification'|

数据库约束/索引：

- `_code_unique`：`models.Constraint('UNIQUE(ydental_code)', 'Service codes must be unique across the group.')`
- `_product_unique`：`models.Constraint('UNIQUE(ydental_product_id)', 'A native product belongs to one service.')`

## ydental.intake.mapping

来源 `ydental_intake/models/ydental_intake_catalog.py`；继承 'ydental.intake.record'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_category`|Selection: 继承关系/标签或原生值|required=继承/否; default='price'|无额外声明|
|`active`|Boolean: 继承关系/标签或原生值|required=继承/否; default=True|无额外声明|
|`ydental_catalog_id`|Many2one: 'ydental.intake.catalog'|required=True; default=原生/空|ondelete='restrict'; index=True|
|`ydental_area_id`|Many2one: 'ydental.space.area'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_execution_area_id`|Many2one: 'ydental.space.area'|required=True; default=原生/空|ondelete='restrict'|

数据库约束/索引：

- `_mapping_unique`：`models.Constraint('UNIQUE(ydental_store_id, ydental_catalog_id, ydental_area_id)', 'A store service area mapping must be unique.')`

## ydental.intake.price

来源 `ydental_intake/models/ydental_intake_price.py`；继承 'ydental.intake.record'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_category`|Selection: 继承关系/标签或原生值|required=继承/否; default='price'|无额外声明|
|`state`|Selection: [('draft', 'Draft'), ('reviewed', 'Reviewed'), ('published', 'Published')]|required=True; default='draft'|无额外声明|
|`ydental_catalog_id`|Many2one: 'ydental.intake.catalog'|required=True; default=原生/空|ondelete='restrict'; index=True|
|`ydental_pricelist_id`|Many2one: 'product.pricelist'|required=继承/否; default=原生/空|ondelete='restrict'|
|`ydental_rule_id`|Many2one: 'product.pricelist.item'|required=继承/否; default=原生/空|ondelete='restrict'|
|`ydental_currency_id`|Many2one: 'res.currency'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_uom_id`|Many2one: 'uom.uom'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_unit_price`|Monetary: 继承关系/标签或原生值|required=True; default=原生/空|currency_field='ydental_currency_id'|
|`ydental_start`|Datetime: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_end`|Datetime: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_reviewed_by_id`|Many2one: 'res.users'|required=继承/否; default=原生/空|ondelete='restrict'|
|`ydental_published_by_id`|Many2one: 'res.users'|required=继承/否; default=原生/空|ondelete='restrict'|
|`ydental_published_at`|Datetime: 继承关系/标签或原生值|required=继承/否; default=原生/空|无额外声明|
|`ydental_reason`|Char: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|

数据库约束/索引：

- `_interval`：`models.Constraint('CHECK(ydental_end > ydental_start)', 'Price validity must have positive duration.')`
- `_positive`：`models.Constraint('CHECK(ydental_unit_price > 0)', 'A published base price must be positive. Free service requires an explicit discount.')`

## ydental.intake.snapshot

来源 `ydental_intake/models/ydental_intake_price.py`；继承 'ydental.intake.record'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_category`|Selection: 继承关系/标签或原生值|required=继承/否; default='price'|无额外声明|
|`ydental_catalog_id`|Many2one: 'ydental.intake.catalog'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_price_id`|Many2one: 'ydental.intake.price'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_product_name`|Char: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_quantity`|Float: 继承关系/标签或原生值|required=True; default=原生/空|digits='Product Unit'|
|`ydental_quantity_digits`|Integer: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_currency_rounding`|Float: 继承关系/标签或原生值|required=True; default=原生/空|digits=(16, 8)|
|`ydental_uom_id`|Many2one: 'uom.uom'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_uom_name`|Char: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_currency_id`|Many2one: 'res.currency'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_unit_price`|Monetary: 继承关系/标签或原生值|required=True; default=原生/空|currency_field='ydental_currency_id'|
|`ydental_amount`|Monetary: 继承关系/标签或原生值|required=True; default=原生/空|currency_field='ydental_currency_id'|
|`ydental_quoted_at`|Datetime: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_policy`|Selection: [('demo_confirmation', 'Demonstration confirmation time price, not production policy')]|required=True; default=原生/空|无额外声明|
|`ydental_source`|Char: 继承关系/标签或原生值|required=True; default=原生/空|index=True|
|`ydental_actor_id`|Many2one: 'res.users'|required=True; default=原生/空|ondelete='restrict'|

数据库约束/索引：

- `_source_unique`：`models.Constraint('UNIQUE(ydental_store_id, ydental_source)', 'A price source can only be snapshotted once.')`

## ydental.intake.record

来源 `ydental_intake/models/ydental_intake_record.py`；继承 'ydental.access.source'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`name`|Char: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_store_id`|Many2one: 继承关系/标签或原生值|required=继承/否; default=原生/空|string='Store'|
|`ydental_category`|Selection: 继承关系/标签或原生值|required=继承/否; default='frontdesk'|readonly=True; string='Business category'|
|`ydental_version`|Integer: 继承关系/标签或原生值|required=True; default=1|readonly=True; string='Version'|

## ydental.intake.operation

来源 `ydental_intake/models/ydental_intake_record.py`；继承 'ydental.intake.record'。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_actor_id`|Many2one: 'res.users'|required=True; default=原生/空|ondelete='restrict'|
|`ydental_key`|Char: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_fingerprint`|Char: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|
|`ydental_result`|Json: 继承关系/标签或原生值|required=True; default=原生/空|无额外声明|

数据库约束/索引：

- `_key_unique`：`models.Constraint('UNIQUE(ydental_actor_id, ydental_key)', 'Action keys must be unique per actor.')`

## ydental.intake.mutex

来源 `ydental_intake/models/ydental_intake_record.py`；继承 原生Model。

|字段|类型/关系/枚举|必填/默认|精度/其他声明|
|---|---|---|---|
|`ydental_revision`|Integer: 继承关系/标签或原生值|required=继承/否; default=0|无额外声明|

## 原生扩展与合成模型

原生product.template/pricelist的ydental_intake_owned仅由私有token设置，不能客户端启停/复制旁路；pricelist的ydental_intake_store_id固定归属。variant通过template marker受保护，item通过pricelist marker受保护。上述扩展不重授权普通非S05产品。

S04 patient.service、S03 supply.service、S01 access.service和ir.attachment仅继承方法，无新业务字段。新的原生dataset controller只绑定真实登录SID，不授权客户端context。

`ydental_intake_test`的`ydental.intake.test.queue`仅隔离库合成适配：task/patient Many2one、active Boolean、state waiting/calling/void；无普通ACL，不进生产字典、无真实号序/叫号/租约。测试guard同时检查库名和服务器运行环境，pre_init拒绝业务库。测试中人工设置missed_count、done仅是合成下游事实，不能当真实临床执行。
