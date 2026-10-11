# S01 字段、动作与安全契约

唯一业务来源：[当前 #23](https://github.com/Yredxin/YDental/issues/23)、[当前 #25](https://github.com/Yredxin/YDental/issues/25) R1；前置依据为 [#24 最终收口](https://github.com/Yredxin/YDental/issues/24#issuecomment-6107583497)。这是 #25 的工程落地记录，不新增计划或恢复旧规则。通用约定继续见 [contracts.md](contracts.md)。

`ydental_access` → `hr`、`ydental_base`、`auth_signup`、`auth_timeout`、`auth_password_policy`、`auth_totp_mail`。只有两个新 addon：实际 S01 能力，以及独立的 `ydental_access_test` 合成验证模块；后者不用于生产，没有患者/库存/费用/排班业务实现。

## 账号与员工

法人复用 `res.company`，门店为 `ydental.access.store` 经营场所，不用原生公司分支冒充经营场所。员工复用 `hr.employee` 的 `UNIQUE(user_id,company_id)`；一个账号在同公司多个门店关联同一员工，跨公司另建员工。邀请和重置保持原邮箱，不返回重置链接或 token。员工账号创建仅授固定应用入口，不授原生 HR、财务或系统管理组；已有内部账号按登录名或明确 account ID 复用，门户不自动提升。

|公共字段|可信源→映射|维护与同步|
|---|---|---|
|公共岗位名称|`res.users.ydental_job_title`→每公司 `hr.employee.ydental_job_title`|集团维护；readonly related、related_sudo=False；员工侧直接 write 拒绝，无同步回路|
|公共能力/资质关联|`res.users.ydental_capability_ids`→每公司同名字段|同上；能力代码唯一；不等于真实临床资质审查或执行授权|
|原生身份/联系|原生 employee.resource_id / user_id / work_contact_id / email/phone 关系|保留锁定源码映射；不再把 `_sync_user` 描述为 name/email 全字段复制|
|合同、薪酬、部门、原生 job_id|原生公司员工/版本记录|不加入公共同步；不互盖；合成测试验证不同公司 department_id 保持不同|

加店只建立目标任职；移店仅清目标授权、归档目标任职；最后离开该公司归档其员工，仍在其他店的账号保持启用；集团离职归档全部任职/员工并停用账号。记录不物理删除。店长须先通过独立任免处理，离职/模板不隐式撤销店长。S03 从 `_after_membership_removed` 处理未来排期，不反向依赖 S03。

## 模型与完整字段字典

各表均采用原生 `id/create_uid/create_date/write_uid/write_date`，ID 为数据库稳定键，时间 UTC；不新增展示流水号。`active` 为原生归档语义。`ondelete=restrict` 保留历史引用。所有新增自研字段均以 `ydental_` 命名。

|模型|字段；类型/必填/默认|归属、读取、写入及约束|
|---|---|---|
|`ydental.access.store`|name Char 必填；company_id M2o res.company 必填；ydental_timezone Char 必填；active Boolean=True|法人限制 `company_ids`；内部应用用户只读，集团可创建/修改；有效 IANA 时区；已有任职不得改法人；无 unlink 权限|
|`ydental.access.membership`|ydental_user_id M2o res.users 必填；ydental_store_id M2o store 必填；ydental_employee_id M2o hr.employee 必填；ydental_is_manager Boolean=False；active=True|user+store 数据库唯一；员工公司由服务匹配门店；无公开 CRUD ACL；受控服务写，职责内页面投影读取|
|`ydental.access.grant`|ydental_membership_id M2o membership 必填；ydental_category Selection 必填；ydental_level Selection 必填/none|membership+category 唯一；固定 16 类及三级；无公开 CRUD；服务写并审计真实 actor；无模板关联|
|`ydental.access.template`|name Char 必填；ydental_levels Json 必填/{}；active=True|集团 cru；JSON 只接受已登记类别和 none/read/write；模板本身 create/modify 留痕；不反向传播|
|`ydental.access.capability`|name Char 必填/translate；ydental_code Char 必填；active=True|集团 cru；code 唯一；公共人员能力字典，不能用作业务角色或任免|
|`ydental.access.session`|ydental_key_hash Char 必填/NO_ACCESS；ydental_user_id M2o users 必填；ydental_store_id M2o store 可空；ydental_revision Integer=0|hash 唯一；无公开 CRUD；只存服务端 SID 稳定前缀的 SHA256，不保存 cookie/token；按用户核对、切店递增版本；不公开字段|
|`ydental.access.audit`|ydental_user_id M2o users 必填；ydental_store_id M2o store 可空；ydental_event/category/target_model/source Char 必填；ydental_target_id Integer 必填；ydental_result Selection accepted/denied 必填；ydental_reason Char 可空；ydental_before/after Json 可空|受控固定模型写入；无公开 CRUD；write/unlink 始终拒绝；查询服务投影限定职责及真实源读取；不保存密码、SID 或病历正文|
|扩展 res.users|ydental_job_title Char；ydental_capability_ids M2m capability|字段组限定集团/原生 HR；更改公共源还须集团身份；不新增账号副本或当前门店字段|
|扩展 hr.employee|同名两个 readonly related 字段|公司员工映射到账号；related_sudo=False；禁止员工侧直接 write，原生公司私有字段保留|
|抽象 `ydental.access.source`|ydental_store_id M2o store 必填；ydental_category 固定 Selection 必填|上层已安装业务继承；源 ACL 与本层门店域同时满足；拒更改归属/物理删除；查看/修改/导出留元数据，不记录正文|
|测试 `ydental.access.test.record`|继承 source；name Char 必填；ydental_text Char 可空|仅合成 space/medical/settlement 记录；明确不能声称病历/财务实现|

抽象 `ydental.access.service`、扩展 `base`/`ir.http`/`ir.attachment`/`ir.actions.report` 无新增持久字段。新能力 XML 标识见各模块 security/data/views；原入口和许可证保留，没有机械重命名。

## 动作权限矩阵

无/只读/读写使用稳定码 `none/read/write`。下表为业务映射契约；尚不存在的业务入口由所属阶段继承本层、登记 source，不能把字典编码当功能已实现。

|类别码|动作及最低级别|数据范围/审计/实际实现|
|---|---|---|
|frontdesk|前台查看 read、操作 write|本店；后续到店/登记事件，不实施前台业务|
|patient|患者必要信息 read、维护 write|本店操作与集团确认分开；后续主档/合并，不实施患者业务|
|medical|诊疗用途历史 read；医疗操作 write|显式 care 用途允许集团相应医疗历史读；写仅当前店；source.view/modify，合成验证；真实文书 S08|
|exam|检查用途历史 read；检查操作 write|与 medical 同样分离共享读和本店写；真实检查后续阶段|
|pharmacy|必要药房信息 read、发药 write|本店；不因摘要给完整医疗读取；真实事件由上层注册|
|warehouse|库存 read、库存操作 write|本店与原生公司隔离；源权限不开放他店库存原单|
|followup|复诊联系 read/write|本店；后续通知/关闭事件|
|outsourcing|外加工 read/write|本店；后续取消/返工事件|
|settlement|结算 read/write|本店；共享医疗读不开放他店财务原单；合成回归|
|finance_approval|审批 read/write|本店；店长授予权不等于自身审批权；退款发起/审批分离由 S10 验证|
|personnel|人员只读 read；入职/加店/移店/授权 write|本店普通人员管理员受自身等级约束，禁止自改；独立店长授本店权限不受该上限；集团另有独立身份|
|space|空间 read/write|本店；S01 合成对象校验三级，真实空间 S02 未启用|
|capacity|排班容量 read/write|本店；后续容量变更事件，S01 仅扩展点|
|price|价目 read/write|本店；集团基础目录由独立集团职责；实际 S05|
|supplier|厂商合作 read/write|门店合作与集团资料分开；实际后续阶段|
|export|报表 read 不代表下载；导出要求 write|当前门店导出 write **且** 源记录 read；保留原生 group_allow_export；原生、CSV、分组/批量出口全部经过 export_data|

菜单不是授权。内部源模型的 search/CRUD/批量、附件、报告、控制器遵循模型服务；客户端 `is_system`、store/context 不能构造服务器 `Binding` 对象。集团/系统组不由业务模板授予，也不自动产生医疗资质或医疗阅读权。框架超级用户及维护脚本为明确可信边界，不将其表现作为普通人员权限证明。

## 实际动作表与恢复

每个 HTTP 写动作 POST+CSRF、参数白名单，服务每次核对角色/任职。切店锁定 session 行；授权/生命周期锁定目标 user；店长任免锁定 store。模板最多 50 个不同目标，按顺序锁定，整批预校验，不保留半批提交。授权更新按新级别分组写、审计批量写。无人工 commit，唯隔离 seed 自己打开的 cursor 执行一次合成初始化 commit。

|动作|入口/权限/前置|原子副作用、事件、重复或失败|
|---|---|---|
|创建门店|store POST；集团；允许的法人/有效时区|建经营场所、发起者任职、store.create；不自动任命店长|
|登录/页面绑定|原生登录 hook；服务器 SID；有效内部入口|login/login.scope；服务器对象绑定真实 actor；不返回 session hash|
|切店|switch POST；有效门店任职|只改该 session 的 store/revision、store.switch；相同店不递增；失败保原范围|
|账号创建或关联|account POST；人员授权/独立管理身份|固定入口组、复用 login、join；account.create/employment.join；不自动发邮件/授权未来业务|
|加店|join POST；人员管理员/本店店长/集团|复用每公司员工；需要扩公司只能集团；已有任职返回同一 ID，不重复身份|
|移店|remove POST；人员管理|目标授权清无、目标任职归档、最后公司员工归档、S03 hook；历史及其他店账号不删；重复 already_accepted|
|集团离职|depart POST；集团；禁止自停用|全部任职/员工归档、账号停用，employment.depart；有店长任职先独立处理；账号已离职幂等返回|
|公共字段修改|profile POST；集团|只写账号公共源，所有公司 related 映射实时变化；profile.change 前后值；私有字段不写|
|授权|grant POST；普通人员人员 write 且不高于自身/不得自改；店长本店例外；集团|只改目标类别；每项 authorization.change 前后值；不改管理员组；相同值无新增变更事件|
|预览模板|preview POST；对每个目标先完整鉴权|展示全部 16 项前后值、生成 receipt；不改授权；任一越权整批拒绝|
|确认模板|apply POST；有效 preview receipt|重新核对目标/模板/现值，缺项清 none，来源 template:id；template.apply；变化后旧 receipt version_conflict；不保持模板关系|
|修改模板|集团模型 cru|仅模板本体变化；template.create/modify；已展开授权不变|
|店长任免|manager POST；独立集团身份且已配置政策|manager.appointment；从未发布状态拒绝；配置 group_with_replacement 时最后在职店长需先有接替者；模板不能任免|
|安全参数配置|policy POST；独立技术组；明确数值+页面确认|security.policy；只允许指定政策、密码长度、闲置及 MFA 设置；不接受任意配置 key；不自动发布建议值|
|邀请/重置受理|invite POST；人员管理；特权账号需技术组|原生邀请服务、account.invitation；只证明受理，delivery=not_verified；不返回 token 或宣称送达|
|源查看/修改/导出|模型与源 ACL、server Binding、门店/用途/级别|source.view/modify/export；修改只审计字段名而非正文；原生导出还校验源 read；跨店人工写受 S06 权威租约 hook 阻止|
|附件/报告|原生路径及受控附件路径；源 read|source.download/report_render；公开标记或 attachment token 不能绕过；PDF 缓存前也检查；生成不等于实体出纸|
|审计查询|职责内受控投影|普通账号无直接 read/write/unlink；业务日志 metadata 同样核对真实源权限；失败操作 savepoint 回滚后 HTTP adapter 写 denied；直接模型拒绝另记不含目标内容的安全日志|

`access_denied` 无业务提交、不泄露不合法源内容；`version_conflict` 拒绝旧页/旧 receipt，刷新/重新预览；`accepted` 为受理；`already_accepted` 为原对象已完成。HTTP拒绝为 403/409；未预料异常回滚并由框架处理，不伪报成功。

## 会话与下游边界

页面版本随表单和原生 user_context **按页面快照**携带，值 0 显式写成字符串；服务器会话在数据库校验，不靠 Cookie 内 current_company 或客户端 flag。相同账号两个原生登录 Cookie 使用不同 server scope；切店不改 account.company_id 或全局 groups。普通 RPC/JSON2 的伪造 context 无法制造 Binding；受保护源的浏览器 DataSet adapter 重新从 SID 绑定，所有非已知读取入口均需页面 revision。

S03 覆盖 `_get_default_store_id`、`_after_membership_removed`；S06 覆盖 `_get_execution_store_id` 并接真实全局坐诊信息。下层默认无实际租约，合成 mock 只证明“他店执行则拒人工写”钩子契约。S08/S09 等上层继承 source、在 `_get_sources` 登记固定模型、接业务动作和查看/更正事件，按实际文书/附件/PDF再次验。S01 不查 registry 中未安装业务，不创建未来空模型。

全局原生后端 systray 显示当前门店及执行店 hook；本阶段执行值为空，不冒充工位定位。当前固定环境无只读副本；审计式读取需要主库事务，本批未验证数据库只读 replica 路由兼容，未来接入副本前必须针对该入口验证。

## 参数处置

|项|当前方案/配置|正式状态|
|---|---|---|
|店长任免|提供 group_with_replacement：集团任免、最后在职店长需先有接替者；未配置时拒任免|用户尚未选择，未发布；合成单测显式设置/回滚|
|独立集团/技术身份|两原生独立组；初始化由用户明确人员配置；安装不自动授予 base.user_admin|正式人员名单待用户；测试仅合成角色|
|默认岗位模板|可建集团模板；整体覆盖、缺项无、medical/exam 不隐式授予；不自动装生产默认岗位|明细待发布；合成前台模板仅测试，无医疗/检查读取|
|密码强度|原生最小长度参数；界面接受 8—128，建议 12|建议不自动发布；隔离预览沿原生默认 8，不作为正式批准|
|二步验证|原生 TOTP + auth_totp_mail employee_required 策略；实际邮箱渠道另核实|建议内部必须二步验证，正式强度待定；测试验证策略配置/短密码拒绝，不声称真实邮件送达|
|闲置/锁屏|原生组 lock_timeout_inactivity + MFA；界面接受 1—1440 分钟，建议 15|未发布建议；合成测试设置后回滚；实际长期闲置/真实 MFA 通道未验|
|初次登录/重置|管理员账号创建+原生邀请/重置，无自助注册；模块安装 invitation_scope=b2b|真实邀请送达须有正式邮箱通道；本批外发关闭|
|门店时区|建店必须明确 IANA，不提供全集团默认|只在合成 A/B 使用 Asia/Shanghai，C 使用 UTC|

以上建议由本会话提供，未收到生产选择，不视为用户批准。正式任免和登录安全参数未发布不阻碍当前合成验证，也不能因此声称正式启用完成。
