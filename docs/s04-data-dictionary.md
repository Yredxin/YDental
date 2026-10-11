# S04 字段字典

来源及权限、验证、动作、历史保护见[s04-contracts.md](s04-contracts.md)；实际固定版本和TC见[s04-report.md](s04-report.md)。下表列出产品所有声明字段及原生复用；安装后实际解析的类型/required/readonly/selection/关系/ondelete/index/default元数据另保存在evidence/s04最终probe的schema，覆盖继承属性。源码列空属性表示继承或框架默认，不是无约束。

## 公共约束及原生复用

- 所有业务表继承`ydental.patient.record`及S01`ydental.access.source`：name、门店、业务大类、资料版本，原生id/create_uid/create_date/write_uid/write_date/display_name。required按继承合并；`name`、`ydental_store_id`、`ydental_category`、`ydental_version`必填。业务类初始category=patient，临床=medical；version=1。
- `res.partner`复用name/phone/email/lang及原生联系人基础能力；仅服务白名单同步。comment、chatter、临床字段、患者登录不写入。新增owner字段groups=base.group_no_one、copy=False、restrict，仅私有服务维护。
- 日期/时间使用Date与naive UTC Datetime，业务日期由store IANA时区计算；患者建档recorded_at/business_date与关系created_at、真实arrival及其recorded_at分开。原生审计时间不冒充业务时间。
- 行政全局读需要当前门店行政或medical/exam读取权；行政写需要patient/frontdesk write；临床读写按medical/exam分类，跨店仅真实患者care scope读取，导出另需export write。合并/回执按当前店、actor或集团法人范围限制。mutex无普通ACL。
- 全部业务字段只由受控动作修改，readonly不作为安全控制；普通CRUD、导入、动态context均不能替代动作。历史不可删；归档active，不物理删除。
- 字段确认：姓名必填；出生信息可未知，birth_date不能未来；sex允许unknown；phone_region为明确ISO地区，phone_status三态；联系方式不强制门槛，guardian只是声明关系，verified必须人工记录依据。临床安全背景单字段上限4000，真实字段审批仍待业务负责人审核。
- 关系均restrict，避免删除患者/门店/操作者毁历史。患者号和number.name分别UNIQUE，partner身份UNIQUE；当前门店关系(patient,store)部分唯一；policy(store,code)唯一；operation(actor,key)唯一；merged_into!=self。
- 身份快照在临床背景创建时取原patient id/number/name/birth_date/sex，此后更名/合并不更新。主档引用可迁移，origin_patient/actor/snapshot不迁移；已过账原单与正式PDF未实现，后续真实复验NOT_RUN。

## 模块与字段声明

### res.partner

来源：[ydental_patient/models/res_partner.py](../ydental_patient/models/res_partner.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|ydental_patient_owner_id|Many2one|Patient owner|ydental.patient|ondelete='restrict'; copy=False; groups='base.group_no_one'; index=True|

### ydental.patient

来源：[ydental_patient/models/ydental_patient.py](../ydental_patient/models/ydental_patient.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|name|Char|||index='trigram'|
|active|Boolean|||default=True|
|ydental_number|Char|Patient number||required=True; readonly=True; index=True|
|ydental_partner_id|Many2one|Administrative contact|res.partner|required=True; ondelete='restrict'|
|ydental_birth_date|Date|Birth date|||
|ydental_birth_note|Char|Birth information, if uncertain|||
|ydental_sex|Selection|Sex|[('unknown', 'Unknown'), ('female', 'Female'), ('male', 'Male'), ('other', 'Other')]|required=True; default='unknown'|
|ydental_phone|Char|Phone as provided|||
|ydental_phone_region|Char|Explicit phone region|||
|ydental_phone_normalized|Char|Normalized phone||index=True; readonly=True|
|ydental_phone_status|Selection|Phone verification status|[('empty', 'Not provided'), ('normalized', 'Normalized'), ('review', 'Manual verification required')]|required=True; readonly=True|
|ydental_email|Char|Email||index=True|
|ydental_merged_into_id|Many2one|Merged into patient|ydental.patient|ondelete='restrict'; readonly=True; index=True|
|ydental_recorded_at|Datetime|Recorded at||required=True; readonly=True|
|ydental_business_date|Date|Business date||required=True; readonly=True|

### ydental.patient.clinical

来源：[ydental_patient/models/ydental_patient_clinical.py](../ydental_patient/models/ydental_patient_clinical.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|ydental_category|Selection|Business category||default='medical'; readonly=True|
|ydental_patient_id|Many2one|Canonical patient|ydental.patient|required=True; ondelete='restrict'; index=True|
|ydental_origin_patient_id|Many2one|Original patient|ydental.patient|required=True; ondelete='restrict'; readonly=True|
|ydental_identity_snapshot|Json|Identity snapshot||required=True; readonly=True|
|ydental_allergies|Text|Allergies|||
|ydental_prior_history|Text|Prior history|||
|ydental_medication|Text|Medication|||
|ydental_recorded_at|Datetime|Recorded at||required=True; readonly=True|
|ydental_actor_id|Many2one|Actor|res.users|required=True; ondelete='restrict'; readonly=True|

### ydental.patient.contact

来源：[ydental_patient/models/ydental_patient_contact.py](../ydental_patient/models/ydental_patient_contact.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|ydental_patient_id|Many2one|Canonical patient|ydental.patient|required=True; ondelete='restrict'; index=True|
|ydental_origin_patient_id|Many2one|Original patient|ydental.patient|required=True; ondelete='restrict'; readonly=True|
|ydental_partner_id|Many2one|Administrative contact|res.partner|required=True; ondelete='restrict'|
|ydental_relation|Selection|Relation|[('contact', 'Contact'), ('guardian', 'Declared guardian'), ('emergency', 'Emergency contact')]|required=True|
|ydental_relationship|Char|Relationship||required=True|
|ydental_phone|Char|Phone as provided|||
|ydental_phone_region|Char|Explicit phone region|||
|ydental_phone_normalized|Char|Normalized phone||index=True; readonly=True|
|ydental_phone_status|Selection|Phone verification status|[('empty', 'Not provided'), ('normalized', 'Normalized'), ('review', 'Manual verification required')]|required=True; readonly=True|
|ydental_email|Char|Email|||
|ydental_verified|Boolean|Verified||readonly=True|
|ydental_verification_note|Char|Verification note|||
|active|Boolean|||default=True|

### ydental.patient.merge

来源：[ydental_patient/models/ydental_patient_merge.py](../ydental_patient/models/ydental_patient_merge.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|ydental_source_id|Many2one|Source|ydental.patient|required=True; ondelete='restrict'|
|ydental_target_id|Many2one|Target|ydental.patient|required=True; ondelete='restrict'|
|ydental_source_version|Integer|Source version||required=True|
|ydental_target_version|Integer|Target version||required=True|
|ydental_reason|Char|Reason||required=True|
|ydental_requested_by_id|Many2one|Requested by|res.users|required=True; ondelete='restrict'|
|ydental_confirmed_by_id|Many2one|Confirmed by|res.users|ondelete='restrict'; readonly=True|
|ydental_decision_reason|Char|Decision reason||readonly=True|
|ydental_conflicts|Json|Conflicts||readonly=True|
|ydental_reference_counts|Json|Reference counts||readonly=True|
|state|Selection||[('requested', 'Awaiting group verification'), ('blocked', 'Resolve active business conflicts'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')]|required=True; default='requested'; readonly=True|

### ydental.patient.mutex

来源：[ydental_patient/models/ydental_patient_mutex.py](../ydental_patient/models/ydental_patient_mutex.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|ydental_revision|Integer|Revision||default=0|

### ydental.patient.number

来源：[ydental_patient/models/ydental_patient_number.py](../ydental_patient/models/ydental_patient_number.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|ydental_patient_id|Many2one|Canonical patient|ydental.patient|required=True; ondelete='restrict'; index=True|
|ydental_origin_patient_id|Many2one|Original patient|ydental.patient|required=True; ondelete='restrict'; readonly=True|

### ydental.patient.operation

来源：[ydental_patient/models/ydental_patient_operation.py](../ydental_patient/models/ydental_patient_operation.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|ydental_actor_id|Many2one|Actor|res.users|required=True; ondelete='restrict'|
|ydental_key|Char|Key||required=True|
|ydental_fingerprint|Char|Fingerprint||required=True|
|ydental_result|Json|Result||required=True|

### ydental.patient.policy

来源：[ydental_patient/models/ydental_patient_policy.py](../ydental_patient/models/ydental_patient_policy.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|ydental_code|Char|Code||required=True|
|ydental_body_reference|Char|Body reference|||
|ydental_approved|Boolean|Approved||readonly=True|
|ydental_approved_by_id|Many2one|Approved by|res.users|ondelete='restrict'; readonly=True|
|ydental_required|Boolean|Required||default=True|
|active|Boolean|||default=True|

### ydental.patient.record

来源：[ydental_patient/models/ydental_patient_record.py](../ydental_patient/models/ydental_patient_record.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|name|Char|||required=True|
|ydental_store_id|Many2one|Store|||
|ydental_category|Selection|Business category||default='patient'; readonly=True|
|ydental_version|Integer|Version||required=True; default=1; readonly=True|

### ydental.patient.relation

来源：[ydental_patient/models/ydental_patient_relation.py](../ydental_patient/models/ydental_patient_relation.py)。

|字段|类型|标签|关系/枚举|必填、默认、访问及存储声明|
|---|---|---|---|---|
|ydental_patient_id|Many2one|Canonical patient|ydental.patient|required=True; ondelete='restrict'; index=True|
|ydental_origin_patient_id|Many2one|Original patient|ydental.patient|required=True; ondelete='restrict'; readonly=True|
|ydental_superseded_by_id|Many2one|Superseded by|ydental.patient.relation|ondelete='restrict'; readonly=True|
|ydental_first_arrival|Datetime|First arrival||readonly=True|
|ydental_first_business_date|Date|First business date||readonly=True|
|ydental_arrival_recorded_at|Datetime|Arrival recorded at||readonly=True|
|ydental_arrival_actor_id|Many2one|Arrival actor|res.users|ondelete='restrict'; readonly=True|
|ydental_arrival_reason|Char|Arrival reason||readonly=True|
|ydental_created_at|Datetime|Created at||required=True; readonly=True|

## 补充语义

|对象/字段|来源和迁移|验证/空值及保留|
|---|---|---|
|patient.number|集团原生sequence分配，原号稳定|数据库唯一；格式配置不重编；失败可缺号；不作幂等键|
|patient.birth_date/birth_note/sex|人工行政字段|date可空，note可记不确定信息，sex默认unknown；不强制年龄或证件|
|patient/contact.phone及region/normalized/status|原值人工输入，规范值服务器计算|未知地区不猜；原值保留；normalized/review/empty三态；不按同号合并|
|number.patient_id/origin_patient_id|当前主档/原身份分离|合并改当前引用，原身份不改；旧号可追溯|
|relation.first_arrival及日期/actor/reason|真实到店动作，非建档或预约|首次前可空，补录需原因且非未来；首次已录不能随意覆盖|
|relation.superseded_by_id|同店两档合并|保留旧关系行及事实，不删；部分唯一仅约束当前行|
|contact.relation/relationship/verified|普通/声明监护/紧急及核实依据|不是自动法律监护判断；联系人可归档及版本重验|
|clinical.patient_id/origin_patient_id/identity_snapshot|当前读取身份/原身份/创建时快照|更名合并只迁移当前引用；clinical actor不变，内容修改version+1|
|policy.approved/body_reference|集团在当前门店确认|正文或批准缺失只提示待完善，不签署、不卡行政建档|
|merge.source_version/target_version/version|申请两档版本及申请内容版本|confirm重验三者，刷新必须显式有原因，活动冲突仍重查|
|merge.conflicts/reference_counts|权威private hooks及合并服务|仅脱敏ID/kind/reference及计数，不放临床文本；冲突先处理|
|operation.fingerprint/result|服务器operation+store+payload SHA256及结果|actor+key唯一；不同参数不能复用；拒绝回滚不留成功回执|
|mutex.revision|固定SQL UPDATE|RR快照并发保护，无普通访问权，不是业务患者版本|

同意书、真正治疗记录、预约/队列及原生财务凭证/PDF不在此字典中；测试模块仅有合成activity/source，不能作为这些业务的空壳实现。
