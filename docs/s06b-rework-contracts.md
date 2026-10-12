# S06-B三个生命周期阻断的修正契约

唯一边界：[GPT-REVIEW6118213551](https://github.com/Yredxin/YDental/issues/30#issuecomment-6118213551)。本补充覆盖原B文档中“verify无出口”和“revoked永久阻断”的历史描述；其余A/B契约不变。原产品/测试/最终及失败材料保留，不是新阶段计划。

## 现场核实

`takeover_verify(execution_id, confirmed, reason)`只处理当前店的verify execution。`handover_verify_hold(execution_id, confirmed, reason)`只处理reserved execution对应的verify hold。两个动作都要求当前server-bound登录及连接、对应业务write、active员工、原工位的全部能力、精确服务/执行区域/可信资质、未漂移的服务快照、当前患者门店关系。原因必填且按S05文本上限校验，confirmed必须为布尔True。持有其他有效lease/未解决execution/hold的人不能处理；目标原lease必须失效。派生station来自旧lease，不接收替换医生/工位/租约参数。

“到现场”是操作人的明确业务确认，不冒称地理位置或设备传感器验证。管理员身份没有额外force-release/steal入口，仍需上述业务资格。远程RPC私有方法、context和JSON saved/source声明不能提供资格或保存证明。

两个出口均先调用默认拒绝的`_save_before_handover`。成功后才释放旧文书占用，任何后续失败同事务回滚。真实S08不存在；仅guard内冻结合成来源证明流程。未配置可信来源时继续拒绝，不伪造治疗完成。

- execution：旧verify变interrupted并保ended_at；新serving通过resumed_from链接旧段，继承task/patient/service snapshot，绑定新actor/session/revision/connection/token的lease。旧entry永久只start一次；原S05资格已消费，不再start/扣容量，不改任务为完成。链可再次超时核实；entry显示按task同步为verify。
- hold：旧hold变handover、记录ended_at和resolution_lease；旧lease/actor/station/source不变；原reserved段保第一次ended_at并记handover时间；创建/复用唯一pending continuation，保持原门诊服务/能力/资质，无新entitlement。处理人取得原工位的新lease，可叫下一位。外检已有actual execution不被强撤或伪造完成。

沿用session→patient→supply/space→intake→queue锁序和RR稳定锚点。两个不同合格人员竞争同一verify：第一人提交后第二人重验状态拒绝；不将第二次处理伪报幂等成功。部分唯一仍只约束serving/verify，不删除或重写旧持有人。

## 保留期间的目标

report的_valid_task和_queue_assert_idle，以及call/start的_eligibility，共享固定`_hold_target_reason`。active与verify hold同样适用：source task和任何Care等普通门诊task拒绝；不同店拒绝；只有exam/medicine可进入。初始target在reserve时已经经可信来源确认，保留其授权；每个额外target必须独立通过`_external_target_authorized(old_execution, task) is True`。基础hook为False，不接受client allowlist/context字典。普通S05资格/到店/位置/服务能力检查仍执行。

restore是独立动作，原持有人明确确认回诊后通过原服务资格校验，不经普通report重发号。hold终态后目标限制消失，后续Care按普通S05规则进入；历史hold不污染资格。

## revoke与重新营业

closed仅接受当前task/mapping/capability/store/date一致的active permit。revoke原子撤waiting/calling，保留entitlement/claim held及容量；closed当下不能start。以后已有S03业务输入变open，普通report/call/start不再查询历史permit终态作为否决条件。旧revoked记录永久保留，不创建替代permit，不重复扣/返容量。draining沿用既有S05/S03逻辑，本批不实现营业状态机、日终或推送。

## 字典补充

|对象|新增/修改|约束|
|---|---|---|
|execution.state|interrupted：因现场接手结束的历史段|与reserved/handover一样必须有ended_at；不是医疗完成|
|hold.ydental_resolution_lease_id|现场交还后新连接租约，可空，Many2one lease，restrict|只由现场动作写入；旧ydental_lease_id和actor不改|
|audit|queue.onsite_takeover / queue.onsite_hold_handover|真实当前actor，旧/新lease、source execution/hold、原因和continuation引用，不含token|

沿用原B字典，其余字段未新增。工位switch只阻断未解决execution，历史段不再永久占椅。生产心跳/timeout/N未批准，测试2秒/20秒/N=2仅合成参数。S06-C、S07及真实S08/S09继续NOT_RUN。
