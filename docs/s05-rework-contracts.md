# S05定向返工补充契约

依据#29 GPT-REVIEW6115823569及用户本次明确指令，仅修BLOCKER-1/2/3。原76335d9、原报告/证据及失败链原样保留；本契约对原S05契约中的目录权限、预约日和转诊发起端授权作以下定向替代。没有新增业务字段、容量账本、队列或临床模块。

## 集团目录与本店业务

|来源/动作|实时授权|权限边界|
|---|---|---|
|catalog/catalog_edit|原生内部认证、S01绑定session/revision、当前active门店、live集团管理员身份；写时锁定session|不要求price或其他门店业务等级；不自动补任何grant或company权限|
|catalog及对应原生product读取|上述集团目录读取，或既有当前门店必要frontdesk/price/medical/exam读取|集团例外只在catalog来源和原生产品使用，不扩展mapping、price、任务或患者读取|
|mapping/mapping_edit/price/review/publish/snapshot|继续本店price-write、写session及原有执行门店约束|集团身份无本店写例外；price-read仅查看价目/快照|

`/ydental/intake/prices`允许集团目录角色进入。catalog控件按集团身份；本店控件按price-write；price-none不读取/输出本店价目与快照。原生受管产品仍只能由受控目录动作改写。撤集团身份后下一请求拒绝目录动作。

## 预约报到营业日

独立entitlement的report/start资格检查，在原held/slot未过期/供给有效检查基础上，要求：S03 `_date(store, slot.start) == _date(store, intake._now())`，按门店IANA时区计算，不按UTC日或操作者时区。覆盖reservation、phone、timed referral及已有walk-in资格。

同一门店当地日可在slot.start前任意早到，不检查剩余可售余额/售卖截止，不重新acquire，不新增提前分钟限制。明日或更后营业日资格今天报告拒绝`reporting_date_mismatch`，不创建position/queue，不改task/entitlement/claim或容量。实际到店作为独立真实事实保留；预约日再显式到店和报到。

没有独立entitlement的derived/continuation不套预约slot日检查，继续原目标open、实际到店和执行互斥契约。

## 转诊来源、目标与审计

普通`_operate`及HTTP/form不能执行refer_timed/refer_untimed，伪context、dict permit和原生RPC调用private方法均拒绝。固定入口为`_referral_action(operation, payload, key, permit=None)`；它只接受两种referral动作，调用`_authorize_referral(operation,payload,permit)`，默认抛AccessError，即使服务器调用也不自动开放。

以后S08集成必须在override验证真实治疗/医嘱/执行来源及不可伪造permit，返回真实来源类别medical或exam；S05在锁前、取得patient→supply→intake锁后都再次验证来源授权及该类别的当前店write权限。普通前台或仅目录管理员没有临床来源权。当前没有S08真实来源，也没有临床转诊发起UI。

|动作|固定参数|结果/恢复|
|---|---|---|
|private refer_timed|source_task_id/version、目标mapping_id、UTC start/end、reason、可信permit、key|目标active/open、精确能力；经S03获取目标预约claim，建立S04 relation和任务；失败整笔回滚、不改来源；目标报到受其预约当地日限制|
|private refer_untimed|source_task_id/version、目标mapping_id、明确valid_until/reason、可信permit、key|目标active/open，只建待目标受理记录，无预占；明确到期后重新确认，不静默延期|
|普通accept_referral|目标店frontdesk-write、record_id/version、当天start/end、key|目标实际到店时占现场；无额/停接/过期拒绝且无半relation/claim/task|

目标公司是不是来源医生的company_ids、医生有没有目标membership都不是可信转诊资格。受控动作仅可写固定目标资格/转诊字段，不授予目标普通reserve/cancel/task/mapping/price/queue或切店人工业务权；无需扩展医生原生多公司访问范围。将来若有跨法人限制，须显式集团转诊政策，不借用company_ids。

receipt及S01 audit保留真实来源actor、medical/exam类别、source_store_id、target_store_id、source_task_id、target_mapping_id；S03目标claim/event保留目标容量账链。无sudo管理员冒充actor，无费用/库存/真实临床写入。

测试模块仅在新S05隔离guard内提供`SyntheticReferralPermit`冻结dataclass，绑定actor/source store/action/完整payload hash/来源类别，普通JSON不可构造。合成来源明确先经过S05测试start再记录done，作为完成执行的stand-in；不是S08真实治疗。typed permit、源task/version/state/类别均校验。原13组竞争只将T11调用改接可信测试入口并补合成来源前提，不更改锁序、RR重试、末额竞争及守恒断言。

幂等key/版本/审计、价格不可变快照、position成功后撤旧、S03返池/改期和S04 merge冲突迁移继续原S05实现。无新字段，原数据字典继续适用，以上权限与动作替代优先。
