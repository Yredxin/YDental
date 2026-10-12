# S06-B数据字典

与原S06-A完整字典及返工契约共同适用。以下完整列出B涉及的execution、hold、permit、task和entry字段；原生id/create_uid/create_date/write_uid/write_date继续由ORM维护。module为ydental_queue，无新临床/库存模块。

所有业务事实继承queue.record或S05 intake.record：当前门店业务读取经S01 scope和权限，普通CRUD/导入/RPC均不能持久修改；服务端私有MUTATION对象授予固定动作最小sudo。原生导出仍要求源读取和export写权限。公共/portal/匿名无业务ACL；字段涉及合成/真实患者标识、工作人员、原因和服务资质，按门店必要数据处理。附件没有新业务来源，hold/permit也禁止任意附件。快照含服务ID/能力/资格/区域，不含患者病历文字。

时间均naive UTC；业务日和时区只由门店服务计算，客户端不能给日期。关联ondelete=restrict；所有事实禁止普通物理删除。name/store/category/version沿用queue.record，版本从1起由_save递增；hold默认medical、permit由服务设置frontdesk。task保留原origin_patient/identity_snapshot，续诊用canonical patient并关联来源段。

## ydental.queue.execution

|字段|类型|关系|必填/默认|来源与修改|
|---|---|---|---|---|
|`ydental_patient_id`|Many2one|`ydental.patient`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_entry_id`|Many2one|`ydental.queue.entry`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_resumed_from_id`|Many2one|`ydental.queue.execution`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_task_id`|Many2one|`ydental.intake.task`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_service_snapshot`|Json|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_lease_id`|Many2one|`ydental.queue.lease`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_started_at`|Datetime|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_ended_at`|Datetime|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_handed_over_at`|Datetime|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`state`|Selection|`-`|必填 / 'serving'|服务端冻结来源、受控动作；禁止客户端CRUD|

## ydental.queue.hold

|字段|类型|关系|必填/默认|来源与修改|
|---|---|---|---|---|
|`ydental_patient_id`|Many2one|`ydental.patient`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_task_id`|Many2one|`ydental.intake.task`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_target_task_id`|Many2one|`ydental.intake.task`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_execution_id`|Many2one|`ydental.queue.execution`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_lease_id`|Many2one|`ydental.queue.lease`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_station_id`|Many2one|`ydental.space.station`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_area_id`|Many2one|`ydental.space.area`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_actor_id`|Many2one|`res.users`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_created_at`|Datetime|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_ended_at`|Datetime|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`state`|Selection|`-`|必填 / 'active'|服务端冻结来源、受控动作；禁止客户端CRUD|

## ydental.queue.append.permit

|字段|类型|关系|必填/默认|来源与修改|
|---|---|---|---|---|
|`ydental_patient_id`|Many2one|`ydental.patient`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_task_id`|Many2one|`ydental.intake.task`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_mapping_id`|Many2one|`ydental.intake.mapping`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_capability_id`|Many2one|`ydental.access.capability`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_business_date`|Date|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_timezone`|Char|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_actor_id`|Many2one|`res.users`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_created_at`|Datetime|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_reason`|Char|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_revoked_by_id`|Many2one|`res.users`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_revoked_at`|Datetime|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_revoke_reason`|Char|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`state`|Selection|`-`|必填 / 'active'|服务端冻结来源、受控动作；禁止客户端CRUD|

## ydental.intake.task

|字段|类型|关系|必填/默认|来源与修改|
|---|---|---|---|---|
|`ydental_queue_opportunity_used`|Boolean|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_source_execution_id`|Many2one|`ydental.queue.execution`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_continuation_snapshot`|Json|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`state`|Selection|`-`|继承S05必填 / pending|只追加suspended/handed_over；ondelete set default；受控动作|

## ydental.queue.entry

|字段|类型|关系|必填/默认|来源与修改|
|---|---|---|---|---|
|`ydental_task_id`|Many2one|`ydental.intake.task`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_patient_id`|Many2one|`ydental.patient`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_area_id`|Many2one|`ydental.space.area`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_capability_id`|Many2one|`ydental.access.capability`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_lease_id`|Many2one|`ydental.queue.lease`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_business_date`|Date|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_timezone`|Char|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_reported_at`|Datetime|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_started_at`|Datetime|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_number`|Char|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_order`|Integer|`-`|必填 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_return`|Boolean|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_opportunity_used`|Boolean|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_call_used_before`|Boolean|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_call_rank`|Integer|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`ydental_call_order_before`|Integer|`-`|可空 / 空/False|服务端冻结来源、受控动作；禁止客户端CRUD|
|`state`|Selection|`-`|必填 / 'waiting'|服务端冻结来源、受控动作；禁止客户端CRUD|

## 状态、唯一性与迁移

|对象|状态和语义|数据库保护/迁移|
|---|---|---|
|execution|serving/verify未解决；reserved原段已结束等待外检；handover合法交还历史|patient/lease仅未解决部分唯一；entry终身unique允许空；resumed_from终身unique；entry与resume恰有一来源；历史态必须ended_at。task和service_snapshot为兼容旧行可空字段，init完成回填后新动作必供；handed_over_at分开记录交还，不改保留时实际ended_at|
|hold|active原椅等待；verify连接失效待现场核实；restored原医生确认真实返回；handover已保存交还|source execution终身unique；patient/lease在active/verify部分唯一。原actor/椅/来源段固定；终态保留所有来源，不创建第二actual execution|
|append.permit|active尚未start；started已实际执行；ended本段结束；revoked普通撤销|task在active/started部分唯一；绑定patient/task/store/mapping/capability/date不可转借。日期失配即无效，不自动生成新资格；撤销留操作者/时间/原因|
|task|原pending/accepted/started/done/cancelled保留；新增suspended与handed_over表示本执行段暂停/交还，不宣告治疗完成|source_execution终身unique保证同交还仅一后继；continuation_snapshot用于report/call/start防服务漂移。无医生/工位指定字段，无复制entitlement|
|entry|原waiting/calling/serving/verify/void保留，新增reserved/handover供历史展示|原task unique、患者waiting/calling部分唯一、lease calling部分唯一及号码范围unique全部保留；restore不新建entry、不重置排序/过号/机会|

服务快照字典键为catalog_id、capability_id、qualification、area_id、execution_area_id。恢复从hold源段复制；续诊从原门诊段复制，明确同catalog调方向只调整两个area键并留原因。外检task的设备能力不会写入门诊快照。

S04合并仍以patient→supply→intake→queue顺序保护。serving/verify和active/verify hold阻止未解决身份被合并；仅合法可迁移的active permit随其pending/accepted任务迁移canonical patient，历史来源保持。字段版本、原价格快照、容量claim和患者号不重编。
