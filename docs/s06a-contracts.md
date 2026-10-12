# S06-A 工程契约

唯一业务来源：[启用6116491783](https://github.com/Yredxin/YDental/issues/30#issuecomment-6116491783)、#30第3节A及#23当前正文/6110178328。S05基线50ac95ac368c8c53bc264d8360c9daa94c0e362b。本文记录落地，不另立业务计划。

## 数据权威与依赖

`ydental_queue`直接依赖intake/patient/supply/space/access；低层文件未修改，无反向依赖或registry探测。S05资格、任务、到店、position，S03 claim/供给账本，S04 canonical/current relation/merge fence继续各自唯一。S06新增lease、entry、execution；没有临床文书/医嘱/治疗完成模型。

- entry：每task一个持久号位；waiting/calling患者全局唯一。号码采用原生ir.sequence，保存区域前缀、门店当地营业日、IANA时区，范围唯一约束。序列可有间隙，不承诺每日从1重置；完整跨日处理属于C批。
- lease：服务器随机256位token仅返回持有浏览器，库中只存SHA256；另绑定actor、S01 session/revision、持有页随机connection摘要及station。有效actor和station分别部分唯一索引。令牌及会话敏感字段`fields.NO_ACCESS`，不能经read/export取回。普通context/dict不能替代冻结Connection/StartPermit。
- execution：与连接分离；患者、entry、lease各唯一。只有serving/verify两种未解决事实。A批无完成/交还/删除出口；连接失效不删除此行。B/S08须按批准来源扩展，不能直接改状态。
- test.document：只在受guard保护的`ydental_queue_test`中存在，不是临床病历。固定DocumentSource验证不同独立文书可分别编辑，同文书唯一；失效lease不再构成编辑权。

## 固定锁与死锁分析

业务动作：S01本会话行锁 → S04 patient(28004及RR更新锚点) → S03 supply(26002，与S02 space共用advisory锁，及RR锚点) → S05 intake(29005及锚点) → S06 queue(30006及锚点)。S05 `_all_locks`由上层继承追加queue；S04 merge的intake扩展锁后追加queue。lease/queue/execution同一串行边界，不出现先lease再patient的相反路径。

S01 grant扩展：本会话 → 目标user advisory → patient→supply→intake→queue，再执行原权限检查与grant写；锁后重读权限。HTTP初始化的既有S01账号锁位于业务fence之前。S06业务fence后不获取新账号锁、不锁别人的session。timeout固定server入口只取上述四业务fence，不依赖持有人scope，不做管理员定点释放。

S02配置原有space advisory→floor/record行锁→supply同advisory重入路径保留；S06不反取floor/record行锁，读稳定配置后操作。S03/S05业务不反取queue→patient；已持同一锁的S05 start嵌套重入保持顺序。所有状态及审计同框架事务提交，无产品手工commit。RR锚点更新使旧快照产生40001，由真实HTTP框架/并发脚本重新开启事务并重读；不能只靠advisory等待后沿用旧快照。

16组真实双连接覆盖抢椅/同账号两椅/call/void/start/heartbeat-timeout-reclaim/switch/grant，含有序持锁交错和同时barrier；记录不同backend PID、重试次数、业务结果及全局不变量。50会话吞吐仍归S13，未以全局串行正确性冒充性能通过。

## 完整动作表

共同输入只由固定POST schema进入私有`_operate`；auth=user、CSRF、16KB上限；持有动作须有效S01 scope/revision、actor、session、connection、token及live业务write。全量savepoint成功提交或不变。模型CRUD即使sudo也需不可JSON伪造的MUTATION。无远程强抢动作。

|动作|前置/权限|锁内变更、结果|重复/失败与恢复|
|---|---|---|---|
|S05 arrive/report|本店frontdesk write，真实到店、合法S05 task/claim、同当地日/原资格有效|真实hook在四锁下建立entry waiting，再建立position；不acquire第二次|同task重报返回原position；hook失败整笔回滚；已有号码/资格保留|
|S05换任务报到|新目标受理检查通过，无未解决execution|同事务撤旧waiting/calling及其呼叫关联，建立新唯一位置|目标拒绝保旧号、呼叫和lease；同task回报复用持久entry，不刷新missed/机会|
|enter(station_id)|当前店、员工active、对应medical/exam/pharmacy write、全部active工位能力被人员覆盖、工位active/enabled/callable、有效报到区|expire超时连接后取得一个actor/工位lease；返回一次token、心跳间隔|无排班也成功，不建供给/task/claim；占用或verify失败；不自动踢旧持有人|
|switch(lease_id,token,station_id)|当前持有端，无calling/execution；同店合法空闲目标|全部目标检查通过后旧lease holder_exit、新lease取得，原子提交|失败保旧；忙时拒绝；同椅幂等返回同lease；旧token永久失效|
|heartbeat(lease_id,token)|持有端session/revision/connection/token有效，实时能力与权限有效|仅续本lease heartbeat/expires；使用当前显式配置|另一会话/只读页/旧token/context伪造拒绝；过期返回connection_expired并提交故障处理；不能复活|
|call(lease_id,token)|合格有效工位持有人，工位无calling/execution|只取自身queue area内明确capability匹配waiting；记call前机会，calling绑定实际lease|无匹配返回no_eligible_waiting；不改服务、任务映射、容量来源椅；同能力竞争只一方取得|
|missed(lease_id,token,entry_id)|本lease当前calling，区域N为显式正整数|任务missed+1，消耗本次首次机会，按当前有效区域队列顺延N位/不足队尾，再waiting|重复旧calling请求拒绝；重报不清missed；配置未发布configuration_required|
|start(lease_id,token,entry_id)|本lease当前calling，实时精确能力仍匹配，canonical/current relation、S05资格有效，无患者execution|冻结StartPermit接S05真实start/consume一次claim、撤position，entry serving，新增唯一execution|与void和其他start同锁；失败无半consume/执行；重复start版本冲突；前台不能抹除started|
|exit/rest/logout workstation|持有端，无calling/serving/verify占用|唯一主动退出路径，lease holder_exit|忙时handover_required；退出失败保原占用；不提供管理员第三种释放|
|timeout / acquire时expire|固定server入口或合法业务动作，服务器时间达到expires|idle释放；calling恢复call前机会、原rank回waiting；serving变verify，释放连接但保留患者及旧工位核实占用|幂等，不记录治疗完成；旧token拒绝；verify工位不可重新进入、同患者别处不可报到/start|
|handover server contract|A批默认fail-closed|无真实接手/保留/交还流程|B启用后以真实来源与保存原子扩展|
|document-lock server contract|A产品默认fail-closed|S08未连接；测试模块仅冻结Synthetic DocumentSource验证独占|不同文书独立；只有持有人释放或lease失效；无管理员强抢|
|GET queue/status/全局systray|内部用户；队列明细须本店frontdesk/medical/exam read|只读，不续租/不清队；显示当前店/区域/工位及expired标识|另一登录页面不获token；站点显示具体停用/权限/能力/占用及可进入工位入口|

## 排序、回诊与故障

新task以门店当地当天既往真实started queue历史判定非首次回来；不看病种、外检次数或当天配额。每个task首次受理冻结return/原报到时间/当地日；已有task离开再报和换区回来不重新获得机会。A批不提供历史治疗完成入口，回诊多轮源在测试中明确用固定历史事实适配；B/S08真实后继仍须后续联合验证。

有效排序：未使用的回诊首次机会 → 持久有效order → 首次reported_at →稳定ID。真missed消耗首次机会并按区域N移动位置；普通未missed任务相对顺序保留。故障撤呼只还原本次call前的opportunity_used；不清更早真missed、不改rank/资格/号码。前台撤号不是missed，不自动返容量/撤医嘱/退费。

## 配置与提示

`ir.config_parameter`的`ydental_queue.heartbeat_seconds`和`ydental_queue.timeout_seconds`必须显式正整数，heartbeat < timeout ≤ 86400。缺配置拒绝建立新lease/新队列，不内置生产默认。复用S02区域`ydental_missed_limit`作为N，0表示未发布，真实过号动作拒绝。测试明确2秒/20秒、N=2；这些仅合成值。建议30秒/300秒、N=3供用户与门店运营负责人评估批准，未批准生产。

cron每分钟检查连接，合法动作也同步expire；读取超时但尚未sweep时显示expired，不把它显示为有效连接。持续有效heartbeat的闲置/锁屏连接不释放；浏览器被挂起且不再心跳则按实际连接超时处理。班次查询只是提示；没有排班或班次结束均不撤lease、不拦合法已受理队列，不创造容量。

## 未启用与回滚

B保留/返回/交还/后继/追加，C完整营业并发/跨日/00:10/推送/屏幕凭证，以及S07/S08真实文书/医嘱/完成均NOT_RUN。A的号码仅建立唯一展示范围，不冒称C日终已完成。真实临床保存、真实发药、费用、库存、支付、生产发布、50会话尚未执行。

新增模块只安装于本批隔离库，回滚使用固定S05分支/commit，不删除S05证据；本批数据库与失败历史保留，不drop或接管历史库。生产迁移及真实数据回滚尚未授权。
