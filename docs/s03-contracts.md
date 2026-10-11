# S03 工程契约

仅依据 #23 当前 R1、#27 当前正文、[GPT-ACTIVATE 6110183188](https://github.com/Yredxin/YDental/issues/27#issuecomment-6110183188)与本会话用户授权；开工检查 [6110252817](https://github.com/Yredxin/YDental/issues/27#issuecomment-6110252817) 已写回并完整读回。本文记录实际实现，不是新增业务计划。S02 固定依赖 e97f721，核心 f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb（本地20.0 fork）。

## 原生复用与模块边界

`ydental_supply` 直接依赖 ydental_space、resource、hr、web。已核对锁定源码 resource.resource 的 user_id/calendar_id、resource.calendar 的 fixed/variable/undefined 及 attendance/leave、resource.calendar.leaves 的 resource_id/date_from/date_to/count_as。Community checkout 无 planning。复用 S01 单账号和各法人 hr.employee/resource.resource；请假判定读取同账号所有公司员工对应资源的有效 absence 及适用公共假期，working_time 不作请假。未安装 hr_holidays 的完整审批工作流，不冒称完成该流程联调；其已批准请假生成 resource.calendar.leaves 后可被本层读取。

`ydental_supply_test` 只装在独立 S03 合成库。其服务器适配器要求精确 S03 库名及 runner 环境标识，不能用于业务库。不创建患者、预约、waiting/calling、真实租约、临床文书或收费模型；不引入 OCA。

## 数量和配置发布

|参数|实现/演示选择|正式发布边界|
|---|---|---|
|预约:现场|默认权重1:2，可配置正整数权重|已确定默认；其他比例必须明确配置|
|取整|floor：预约=floor(Q×R/(R+W))，现场=Q-预约；nearest：正数四舍五入预约份额，现场取剩余|本次只发布工程策略，演示选择floor；生产选择待负责人确认|
|Q=1/2/3/6|floor结果0:1、0:2、1:2、2:4；预约0显示告警|界面可保存明确demo并预览；不冒称已批准生产|
|覆盖层级|工位→最近祖先区域→门店；同层最新不可变policy记录优先|各槽冻结policy ID，不跟随后续修改|
|电话代约归池|显式reservation或walkin；本批演示reservation，另测walkin|生产选择待确认；来源适配器保留真实渠道，claim记录实际池|
|新预约截止|slot.start-cutoff_minutes，截止时刻起拒绝新预约；cutoff>=0，演示0及15/20|生产选择待确认；转换仅在start<=now<end，converted永久拒绝新预约|
|演示与正式|policy.mode=demo/published；published要求独立approved=true确认|生产内核 `_allow_demo_supply()` 默认为False，demo槽不能分配真实资格；仅隔离测试适配器允许demo消费|
|营业日|门店IANA时区，UTC存储，业务日单独date并记录时区|00:00边界；00:10清前日归S06，当前NOT_RUN|

整数守恒：`total = reservation_free + walkin_free + unavailable + held/consumed claim数`。能力视图只是同一批槽的筛选，不能相加；区域按槽ID去重。来源按能力较少槽、稳定station ID、slot ID排序，允许保守利用率，不承诺最优排程。工位时段不重叠，区域人员安排不生成槽。

减额最多移除free及已释放不可售余量，不能移除held/consumed；加额按冻结policy拆分，时段开始后全部进现场。延长同日时段须无重叠，暂停新增并重新核查覆盖，不自动增额。临时开诊创建真实槽、能力、数量、原因；不存在人工追加患者加容量动作。

## 权限、事务和不可变历史

所有网页POST保留CSRF、auth=user、请求大小限制；POST先建立服务端会话绑定并核对页面revision。自研模型复用S01 capacity读权限/当前门店域；通用create/write/import禁止，仅私有受控服务可持有不可JSON伪造的object token。普通CRUD不能写状态、余量、版本、来源或审计；unlink始终拒绝。事件不可改写。

写动作要求本店capacity读写、有效会员与员工、S01全局执行门店限制。源事件审计记录真实actor，内部sudo仅固定模型、固定字段和已授权门店；自研不调用任意模型/任意sudo命令。自助今日只窄读本人有效安排和仍有权门店，不因此给予capacity读取或排期编辑权。反馈只允许本人当前门店安排，接收者取有效capacity读写人员；无接收者明确提示店长处理，不发送短信/邮件。

锁序：S01会话写锁→S02全局space advisory lock 26002→S03固定mutex行UPDATE→必要floor/station锁。mutex UPDATE使repeatable-read旧快照发生SerializationFailure，整个外层事务须由Odoo重试；不能只释放advisory锁后沿用旧快照。S02配置变更通过继承钩子进入同一锁。全部业务原子执行，不手工commit；测试probe仅在自己创建的独立游标提交合成数据。

幂等键按门店唯一，fingerprint包含actor、动作、规范JSON参数；同键同参数返回原receipt/already_accepted，不重扣；换参数同键拒绝。资格来源(store, source, source_key)另有唯一约束，已取消来源不能换幂等键重建，改期必须同source的新revision key。不可使用姓名/证件等作为source_key；下游提供稳定不敏感内部键。

## 完整动作表

共同失败：权限不足access_denied；版本/来源/重叠冲突version_conflict；无容量insufficient_balance；非法参数ValidationError。异常在savepoint回滚全部动作，原资格/号位由上层事务保留；动作receipt与账本同事务提交。无费用、库存、款项、文书、真实队列副作用。事件带actor、原因、配置ID、槽/安排前后版本与字段快照。

|入口/动作|参数与前置|权限/锁/原子结果|重试及恢复|
|---|---|---|---|
|_operate policy|name/mode/rounding/phone_pool/cutoff/reason，选填正权重、area/station、approved|capacity写；新不可变策略版本，返回Q预览|旧槽冻结原版本；新策略不覆盖旧记录|
|assign|user_id、start/end UTC、station/area二选一|有效本店员工；同账号跨公司及工位时间重叠拒绝；absence拒绝；能力不符草稿可保存并提示|返回安排ID和warning；不生容量|
|adjust|id/version/values/reason|未来active安排；重新验证人员地点/冲突；记录完整前后快照|失败原安排不变；必要供给损失待办|
|cancel_assignment|id/version/reason|取消默认安排，保留历史；供给独立保留|不删除已占槽，不返患者资格|
|batch|1—50行assign参数|有界批量，同一savepoint全部成功|任一冲突全批不落库|
|copy|week_start当地日期|取上一周最多50条有效安排，保持当地墙钟时刻跨DST复制，逐条核对新冲突|receipt保留source_ids和新ids，不生成容量|
|slot|station/start/end/total/capability_ids/reason|有效可接诊工位、报到区域、同营业日、不重叠；能力有效；冻结policy，draft|返回真实槽ID/0预约告警|
|publish|id/version/user_ids/reason|核查有效门店人员无absence、能力并集覆盖；保存核查人/时间/能力快照|草稿与发布分开；不绑定患者医生；动态变化还会复核|
|resize|id/version/total/reason|减额不小于held/consumed；加额记原policy来源|完整前后账；不能复活资格|
|extend|id/version/end/reason|只延长原营业日内，无重叠，暂停供给|重新publish核查延长时段|
|convert|slot id|start<=now<end；未用预约余量原子转现场一次|converted不可逆；与新预约共锁，不双售|
|business|area/state/reason/已有version|首次显式open；draining停普通报到；closed只允许draining且服务器队列清空核查；重开有原因|不增额、不复活号；没有队列连接时closed失败关闭|
|resolve|entity=feedback/disposition,id/version/reason|记录处置结果；不自动恢复供给或迁移资格|复核coverage后独立publish|
|_feedback|本人安排id/reason/key|有效会员、本人、当前门店；待处理同安排反馈去重；通知待办可由排班员读取|无接收者返回manager_required；不要求短信模块|
|_workbench_suggestion|本人今日安排id|hint_only；工位/区域子树合格能力工位列表，execution=not_connected|一键建议页无真实租约；S06接入前不宣称进入执行|
|_today/_default_candidates|服务端当前账号|本人仍有效安排；当前或最近将到的当日安排建议；多候选选择|一次登录建议；无安排取仍有权的上次店，否则选店；不按时间跳会话|
|_availability|area/capability/start/end/channel|capacity读，返回共享总额/去重余量和非可加能力余量|hint_only，无占用|
|_capacity_action acquire|area/capability/start/end/channel/source/source_key，选填slot_id仅服务器来源重配选择|默认拒绝未接入来源；合格槽扣一次池，生成held claim/来源唯一|原资格报到不得再acquire；其他实际椅执行不再扣|
|cancel|claim id/reason|仅held；开始前原池，开始后同槽现场；过期/停接/暂停记unavailable；consumed不返|取消与consume共锁；cancelled重试无第二释放事件|
|consume|claim id|仅held→consumed；cancelled拒绝；由S06真实执行服务器验证后调用|重复不二扣，不决定实际工位/医生|
|reschedule|旧claim id、target acquire参数、reason|held；同source新revision key；新占与旧取消同savepoint|新目标失败旧claim不动；下游队列/预约改动必须放在同一外层事务|
|reassign|held claim id、目标slot id、reason|同门店区域时段和原池、目标能力合格且可售；目标扣额、原槽返同渠道或不可售池、原claim改来源slot|无新claim；不动上层号序；失败原claim不动|
|_after_membership_removed|S01已授权membership|取消本店未来active安排；历史不删；覆盖失效槽暂停、资格保留、替班迁移联系待办|集团depart沿S01逐店调用；不做反向依赖|

## 下游服务器扩展契约

S05/S06继承 `_check_capacity_source(operation,payload)`：必须从固定真实来源模型核对当前用户业务权、源门店、能力、资格状态及canonical内部键，返回当前门店record。不能以客户端context、字符串模型或伪造source通过。手工capacity写权不自动授权预约消费。当前生产实现一律拒绝，合成适配器仅测试边界。

S05普通报到通过其已有claim资格，不再扣或因free=0拒绝；S06执行选其他合格工位仅调用consume，不更改容量来源、不二扣。consume只是接收资格记账状态；真实执行独占/医师资质/租约/到店窗口由S06在同一事务证明。reschedule/reassign必须与真实预约和号序在同一外层事务提交；S03不生成/撤销号位。

营业稳定对象为business(store, area, local date)，下游报到和开关区必须先按相同锁序取得S03 mutex及business行。继承 `_check_queue_empty(business)` 在同一事务内读取真实waiting/calling并拒绝非空；当前默认拒绝停止普通叫号。没有真实队列时不能称已清队。00:10/跨日执行/保留/叫号和真实租约均NOT_RUN，交S06。

空间已有供给历史时拒绝station区域/报到拓扑改绑，防止旧槽偷偷换区域；普通几何/更名仍遵循S02。工位停用/能力丢失、图元改绑/归档、资源能力变化、能力字典停用、人员能力变化、absence及人员移除触发复核。失去覆盖只暂停新增、留待办，held/consumed不删除；恢复必须明确重新核查发布。

## 入口与标识

菜单：ydental_supply_menu（排期与容量）、ydental_supply_today_menu（我的今日）；URL动作ydental_supply_action/ydental_supply_today_action。GET /ydental/supply（week_start/group_by）、GET /ydental/supply/today；POST /ydental/supply/action（operation/revision/key与typed表单或JSON payload）。没有下游消费HTTP路由。

模板tokens仅复用CSRF/页面revision/动作key；不会显示或导出cookie。页面只使用QWeb转义和现有Bootstrap，无新static、JS补丁或外部资源。字段字典见[s03-data-dictionary.md](s03-data-dictionary.md)，安全自查见[s03-security-review.md](s03-security-review.md)。
