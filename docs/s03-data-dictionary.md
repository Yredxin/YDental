# S03 数据字典

仅记录 #27 实际模型与字段；需求与动作约束见 [s03-contracts.md](s03-contracts.md)。整数容量单位为“份”，不表示金额/时间分钟；Datetime 为 naive UTC，业务日按门店 IANA 时区，Char 不用于保存患者身份。所有新模型属于 ydental_supply，均无患者/真实医生执行绑定。

## 所有供给记录共同约束

除私有 mutex 外，各实体继承 ydental.supply.record → ydental.access.source。`name` 必填；`ydental_store_id` 必填 Many2one→ydental.access.store，restrict、索引，法人从 store.company_id 唯一派生；`ydental_category` 固定capacity；`ydental_version` 必填整数，默认1，仅受控动作自增。原生 `id/create_uid/create_date/write_uid/write_date/display_name` 保留，不改名；create_uid可能为受控sudo技术用户，真实发起人以event.ydental_actor_id和S01公共审计为准。

读：内部账号、服务端会话当前门店、有效membership/employee、capacity>=read，继承S01动态源域。写：普通ORM/导入/RPC全部拒绝，受控私有服务capacity=write；本人今日/反馈采用独立窄读写授权。原生导出还要求export=write及源读权限；打印/附件继承S01注册源保护。本阶段无患者/凭据字段，原因仅作业务描述；交付数据均为合成。删除：全部禁止，状态取消/更正和event保留。升级：新增表/字段，无历史业务迁移，policy与event不可变。

字段表“默认/必填”按声明列出；全部关系跨店/有效性在私有服务验证，M2M只接受服务器验证后set的现有ID，不接受客户端sudo命令。状态列虽然不是readonly视图字段，底层create/write仍由不可伪造token保护，不能任意越边。

## `ydental.supply.assignment`

源码：[ydental_supply_assignment.py](../ydental_supply/models/ydental_supply_assignment.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`ydental_user_id`|Many2one; 'res.users'|True / -|-|'restrict' / True|
|`ydental_employee_id`|Many2one; 'hr.employee'|True / -|-|'restrict' / -|
|`ydental_station_id`|Many2one; 'ydental.space.station'|- / -|-|'restrict' / True|
|`ydental_area_id`|Many2one; 'ydental.space.area'|- / -|-|'restrict' / True|
|`ydental_start`|Datetime; -|True / -|-|- / True|
|`ydental_end`|Datetime; -|True / -|-|- / -|
|`state`|Selection; [('active', 'Effective'), ('cancelled', 'Cancelled')]|True / 'active'|-|- / -|
|`ydental_reason`|Char; -|- / -|-|- / -|
|`ydental_warning`|Char; -|- / -|'_compute_warning'|- / -|

## `ydental.supply.business`

源码：[ydental_supply_business.py](../ydental_supply/models/ydental_supply_business.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`ydental_area_id`|Many2one; 'ydental.space.area'|True / -|-|'restrict' / True|
|`ydental_date`|Date; -|True / -|-|- / True|
|`ydental_timezone`|Char; -|True / -|-|- / -|
|`state`|Selection; [('open', 'Open'), ('draining', 'Ordinary reporting stopped'), ('closed', 'Ordinary calling stopped')]|True / -|-|- / -|
|`ydental_reason`|Char; -|True / -|-|- / -|

数据库约束：`UNIQUE(ydental_store_id, ydental_area_id, ydental_date)`。

## `ydental.supply.claim`

源码：[ydental_supply_claim.py](../ydental_supply/models/ydental_supply_claim.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`ydental_slot_id`|Many2one; 'ydental.supply.slot'|True / -|-|'restrict' / True|
|`ydental_capability_id`|Many2one; 'ydental.access.capability'|True / -|-|'restrict' / -|
|`ydental_pool`|Selection; [('reservation', 'Reservation'), ('walkin', 'Walk-in')]|True / -|-|- / -|
|`ydental_source`|Char; -|True / -|-|- / True|
|`ydental_source_key`|Char; -|True / -|-|- / True|
|`state`|Selection; [('held', 'Held'), ('consumed', 'Consumed'), ('cancelled', 'Cancelled')]|True / 'held'|-|- / -|

数据库约束：`UNIQUE(ydental_store_id, ydental_source, ydental_source_key)`。

## `ydental.supply.disposition`

源码：[ydental_supply_disposition.py](../ydental_supply/models/ydental_supply_disposition.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`ydental_assignment_id`|Many2one; 'ydental.supply.assignment'|- / -|-|'restrict' / -|
|`ydental_slot_id`|Many2one; 'ydental.supply.slot'|- / -|-|'restrict' / -|
|`ydental_reason`|Char; -|True / -|-|- / -|
|`ydental_resolution`|Char; -|- / -|-|- / -|
|`state`|Selection; [('pending', 'Pending replacement, migration or contact'), ('resolved', 'Resolved')]|True / 'pending'|-|- / -|

## `ydental.supply.event`

源码：[ydental_supply_event.py](../ydental_supply/models/ydental_supply_event.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`ydental_slot_id`|Many2one; 'ydental.supply.slot'|- / -|-|'restrict' / True|
|`ydental_claim_id`|Many2one; 'ydental.supply.claim'|- / -|-|'restrict' / -|
|`ydental_actor_id`|Many2one; 'res.users'|True / -|-|'restrict' / -|
|`ydental_operation`|Char; -|True / -|-|- / -|
|`ydental_reason`|Char; -|True / -|-|- / -|
|`ydental_before`|Json; -|- / -|-|- / -|
|`ydental_after`|Json; -|- / -|-|- / -|
|`ydental_policy_id`|Many2one; 'ydental.supply.policy'|- / -|-|'restrict' / -|

## `ydental.supply.feedback`

源码：[ydental_supply_feedback.py](../ydental_supply/models/ydental_supply_feedback.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`ydental_assignment_id`|Many2one; 'ydental.supply.assignment'|True / -|-|'restrict' / -|
|`ydental_user_id`|Many2one; 'res.users'|True / -|-|'restrict' / -|
|`ydental_recipient_ids`|Many2many; 'res.users'|- / -|-|- / -|
|`ydental_reason`|Char; -|True / -|-|- / -|
|`state`|Selection; [('pending', 'Pending'), ('resolved', 'Resolved')]|True / 'pending'|-|- / -|
|`ydental_resolution`|Char; -|- / -|-|- / -|

## `ydental.supply.mutex`

源码：[ydental_supply_mutex.py](../ydental_supply/models/ydental_supply_mutex.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`name`|Char; -|True / -|-|- / -|
|`ydental_revision`|Integer; -|- / 0|-|- / -|

## `ydental.supply.operation`

源码：[ydental_supply_operation.py](../ydental_supply/models/ydental_supply_operation.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`ydental_key`|Char; -|True / -|-|- / True|
|`ydental_fingerprint`|Char; -|True / -|-|- / -|
|`ydental_result`|Json; -|True / -|-|- / -|

数据库约束：`UNIQUE(ydental_store_id, ydental_key)`。

## `ydental.supply.policy`

源码：[ydental_supply_policy.py](../ydental_supply/models/ydental_supply_policy.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`ydental_area_id`|Many2one; 'ydental.space.area'|- / -|-|'restrict' / -|
|`ydental_station_id`|Many2one; 'ydental.space.station'|- / -|-|'restrict' / -|
|`ydental_mode`|Selection; [('demo', 'Demonstration'), ('published', 'Approved publication')]|True / -|-|- / -|
|`ydental_reservation_weight`|Integer; -|True / 1|-|- / -|
|`ydental_walkin_weight`|Integer; -|True / 2|-|- / -|
|`ydental_rounding`|Selection; [('floor', 'Round reservation down'), ('nearest', 'Round reservation to nearest')]|True / -|-|- / -|
|`ydental_phone_pool`|Selection; [('reservation', 'Reservation'), ('walkin', 'Walk-in')]|True / -|-|- / -|
|`ydental_cutoff_minutes`|Integer; -|True / 0|-|- / -|
|`ydental_reason`|Char; -|True / -|-|- / -|

## `ydental.supply.record`

源码：[ydental_supply_record.py](../ydental_supply/models/ydental_supply_record.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`name`|Char; -|True / -|-|- / -|
|`ydental_store_id`|Many2one; -|- / -|-|- / -|
|`ydental_category`|Selection; -|- / 'capacity'|-|- / -|
|`ydental_version`|Integer; -|True / 1|-|- / -|

## `ydental.supply.slot`

源码：[ydental_supply_slot.py](../ydental_supply/models/ydental_supply_slot.py)。共同归属、权限、保留规则见上文。

|字段|类型/关系/枚举|必填 / 默认|计算/来源|删除策略 / 索引|
|---|---|---|---|---|
|`ydental_station_id`|Many2one; 'ydental.space.station'|True / -|-|'restrict' / True|
|`ydental_area_id`|Many2one; 'ydental.space.area'|True / -|-|'restrict' / True|
|`ydental_start`|Datetime; -|True / -|-|- / True|
|`ydental_end`|Datetime; -|True / -|-|- / -|
|`ydental_capability_ids`|Many2many; 'ydental.access.capability'|- / -|-|- / -|
|`ydental_policy_id`|Many2one; 'ydental.supply.policy'|True / -|-|'restrict' / -|
|`ydental_total`|Integer; -|True / -|-|- / -|
|`ydental_reservation_free`|Integer; -|True / -|-|- / -|
|`ydental_walkin_free`|Integer; -|True / -|-|- / -|
|`ydental_unavailable`|Integer; -|True / 0|-|- / -|
|`ydental_converted`|Boolean; -|- / False|-|- / -|
|`state`|Selection; [('draft', 'Draft'), ('published', 'Published'), ('suspended', 'Suspended')]|True / 'draft'|-|- / -|
|`ydental_coverage`|Json; -|- / -|-|- / -|
|`ydental_reason`|Char; -|True / -|-|- / -|

数据库约束：`CHECK(ydental_total >= 0 AND ydental_reservation_free >= 0 AND ydental_walkin_free >= 0 AND ydental_unavailable >= 0)`。

## 可信来源与状态语义

|实体|字段来源与状态|历史和权限补充|
|---|---|---|
|policy|管理员显式策略；demo/published，后者必须独立approved确认|新版本新增行，旧槽policy_id不变；生产不消费demo|
|assignment|有效会员绑定员工；工位或区域二选一；active→cancelled|按user_id跨公司互斥；能力不符提示；未来调整快照完整保留|
|slot|能力来自有效工位；区域取最近报到祖先；total由人工显式配置；draft→published↔suspended|余额由事务动作计算；policy冻结；发布coverage JSON固定user_ids/capability_ids/checked_by/checked_at，不是患者医生绑定|
|claim|source/source_key由上层服务器来源生成；held→consumed或cancelled|与patient/appointment/queue无关系字段；只有slot是记账来源，不限制实际工位；取消/开始互斥|
|event|actor原始用户；operation/reason/policy及before/after由服务端生成|不可写删；JSON仅受控槽/安排/claim状态元数据，不接收任意客户端JSON|
|operation|key客户端请求标识；fingerprint为actor+操作+参数SHA256；result受控原返回|同门店唯一；重复不再执行；不是业务展示编号|
|feedback|本人安排、原因、有效capacity编辑接收者；pending→resolved|无接收者提示店长；不实施外发渠道|
|disposition|人员移除/空间或能力损失的槽/安排、原因；pending→resolved|既有资格不删除；resolution不自动复活供给或号位|
|business|门店+报到区域+门店当地日期唯一；timezone保存业务日来源；open→draining→closed，附原因reopen|closed需服务器队列钩子；不自增容量、不清真实队列|
|mutex|XML唯一固定行，ydental_revision仅用于数据库串行化|无ACL授予，不作为业务可编辑模型；SQL只UPDATE固定ID，防旧快照超卖|

## 原生模型扩展

未给S01/S02模型新增业务字段。继承 ydental.access.service 的来源注册、默认店建议、membership_removed；继承 space.station/space.resource/space.item 的已授权配置变更钩子；继承 resource.calendar.leaves、res.users、access.capability 的已授权原生变更后供给复核。保留原模型名、权限及S02稳定ID。无反向依赖、registry探测、未来空模型或核心修改。

## 枚举和错误保留

内部码始终为英文：policy demo/published；assignment active/cancelled；slot draft/published/suspended；claim held/consumed/cancelled；feedback/disposition pending/resolved；business open/draining/closed；pool reservation/walkin。只翻译标签，不翻译码。error码为access_denied、version_conflict、insufficient_balance，非法参数用ValidationError；已受理/already_accepted/hint_only契约见动作表。
