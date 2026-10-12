# S06-A 数据字典
仅实际模型；来源为#30 A启用与本批代码。所有关系ondelete=restrict，历史不删除。下列非原生字段全部自研；原生id/create_uid/create_date/write_uid/write_date沿用Odoo，不另造编号或操作者字段。
## 共用字段与保护
lease/entry/execution继承ydental.queue.record→ydental.access.source。name为必填显示标签；ydental_store_id为必填索引门店(FK store)，法人由store.company_id唯一回源；ydental_category为必填业务枚举(medical/exam/pharmacy)，由合法工位/服务导出；ydental_version为必填int默认1，每次受控_save递增。
三表仅本店有frontdesk/medical/exam读取权者可读；写须服务器固定动作及MUTATION，普通用户/导入/RPC/create/write/unlink不能改。读取/查询/导出沿S01审计和export权限。公开工作台只显示任务号/能力/状态及必要人员元数据，不显示患者姓名。

## ydental.queue.lease
|字段|类型/关系|必填/默认|可信来源与用途|
|---|---|---|---|
|ydental_actor_id|Many2one → res.users|required=True; default=False/空|真实持有人，来自env.uid|
|ydental_station_id|Many2one → ydental.space.station|required=True; default=False/空|当前明确合法工位，不是容量来源椅|
|ydental_session_id|Many2one → ydental.access.session|required=True; default=False/空|服务器SID派生的S01会话，NO_ACCESS|
|ydental_revision|Integer|required=True; default=False/空|进入时S01会话修订，NO_ACCESS|
|ydental_token_hash|Char|required=True; default=False/空|服务器随机token的SHA256；NO_ACCESS，不存原token|
|ydental_connection_hash|Char|required=True; default=False/空|持有页connection的SHA256；NO_ACCESS|
|ydental_heartbeat_at|Datetime|required=True; default=False/空|最近持有端心跳，服务器UTC|
|ydental_expires_at|Datetime|required=True; default=False/空|最近续租时刻+显式timeout，服务器UTC|
|ydental_active|Boolean|required=False; default=True|连接占用默认true；仅主动退出或超时变false|
|ydental_release_reason|Selection|required=False; default=False/空|holder_exit/timeout两种释放事实|

## ydental.queue.entry
|字段|类型/关系|必填/默认|可信来源与用途|
|---|---|---|---|
|ydental_task_id|Many2one → ydental.intake.task|required=True; default=False/空|唯一S05来源task，不复制预约资格|
|ydental_patient_id|Many2one → ydental.patient|required=True; default=False/空|S04当前canonical患者；merge在同锁域迁移waiting/calling|
|ydental_area_id|Many2one → ydental.space.area|required=True; default=False/空|S05 mapping明确报到区域|
|ydental_capability_id|Many2one → ydental.access.capability|required=True; default=False/空|S05 catalog明确能力，精确领取不并集外检能力|
|ydental_lease_id|Many2one → ydental.queue.lease|required=False; default=False/空|实际呼叫/执行持有租约；撤呼清关联，serving保留历史持有人|
|ydental_business_date|Date|required=True; default=False/空|首次报到服务器时刻按门店IANA计算的当地营业日|
|ydental_timezone|Char|required=True; default=False/空|首次受理时门店IANA时区快照|
|ydental_reported_at|Datetime|required=True; default=False/空|首次合法报到UTC，重报不刷新|
|ydental_started_at|Datetime|required=False; default=False/空|真实开始UTC，不是文书保存或治疗完成|
|ydental_number|Char|required=True; default=False/空|原生ir.sequence及区域前缀快照；门店+区域+营业日唯一|
|ydental_order|Integer|required=True; default=False/空|持久有效排序整数；真过号原子重排|
|ydental_return|Boolean|required=False; default=False/空|本task首次受理按当天既往实际开始事实冻结回诊标志|
|ydental_opportunity_used|Boolean|required=False; default=False/空|本task首次机会已用，真实missed后不重置|
|ydental_call_used_before|Boolean|required=False; default=False/空|当前call之前的机会状态，故障撤呼仅恢复此值|
|state|Selection|required=True; default='waiting'|受控生命周期，枚举见下文|

## ydental.queue.execution
|字段|类型/关系|必填/默认|可信来源与用途|
|---|---|---|---|
|ydental_patient_id|Many2one → ydental.patient|required=True; default=False/空|S04当前canonical患者；merge在同锁域迁移waiting/calling|
|ydental_entry_id|Many2one → ydental.queue.entry|required=True; default=False/空|真实开始对应唯一entry|
|ydental_lease_id|Many2one → ydental.queue.lease|required=True; default=False/空|实际呼叫/执行持有租约；撤呼清关联，serving保留历史持有人|
|ydental_started_at|Datetime|required=True; default=False/空|真实开始UTC，不是文书保存或治疗完成|
|state|Selection|required=True; default='serving'|受控生命周期，枚举见下文|

## 枚举/唯一性/保留
entry.state=waiting/calling/serving/verify/void；execution.state=serving/verify。lease没有用active原生归档字段代替业务占用，ydental_active表示当前连接有效占用，历史不归档或删除。
lease两个部分唯一索引分别约束有效actor及station；entry唯一task、waiting/calling患者全局部分唯一、calling租约部分唯一及范围号码唯一；execution患者/entry/lease各唯一，A无终态出口。禁止普通导入/批量绕过。
ydental.queue.mutex只含ydental_revision=int默认0，由参数化UPDATE串行锚点；无普通ACL。新增S05 task字段ydental_queue_opportunity_used=Boolean默认false、readonly，仍受原S05 CRUD保护。原ydental_missed_count继续为唯一真实过号计数，不另建计数。
配置复用ir.config_parameter两个显式秒值及S02 area.ydental_missed_limit。无生产默认/隐式批准。原生ir.sequence是展示号来源，内部task/entry ID与显示号分离。
ydental.queue.service为无存储AbstractModel；固定server hooks及结果为普通dict。新表无金额、库存、收费、医疗正文或附件字段。没有未来空壳。
测试专属ydental.queue.test.document: ydental_key Char(required)合成独立文书键；ydental_lease_id FK(required/restrict)合成编辑者lease；ydental_active Boolean(default true)合成编辑占用；key WHERE active部分唯一。只在全新S06A guard库安装，禁止生产；不是真实临床模型。
所有状态修改/历史保存随框架事务，UTC timestamp使用Odoo naive UTC；首次营业日/时区/号码重报不变，跨日日终属C NOT_RUN。S04 merge仅迁移活动canonical引用，历史身份/S05快照不重写。
