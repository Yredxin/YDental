# S06-B动作与事务契约

唯一业务来源为#23当前R1、#30正文及[GPT-ACTIVATE6117541343](https://github.com/Yredxin/YDental/issues/30#issuecomment-6117541343)。S06-A技术PASS6117519348及固定e13eaa2保留。本文记录本次实现，不增设需求或生产政策。

## 执行事实和历史

execution的serving/verify为未解决事实；reserved/handover为历史终态。数据库只对未解决patient/lease作部分唯一。entry_id仍终身唯一；真实start必须来自calling并走S05 start/一次consume。恢复不重启entry，不发新号：新execution的entry_id为空、resumed_from_id关联原历史execution，二者恰有一个来源；每个来源最多恢复一次。task_id和服务要求快照随新段保留。原entry继续展示任务状态；其唯一start事实不变。

保留时原实际执行结束；独立hold绑定原患者、门店、任务、来源段、目标任务、actor、lease、区域、工位和创建时间。active/verify hold分别维持等待和核实围栏，均阻止原医生call/switch/exit及其他人占椅。hold不是actual execution，不妨碍合法目标任务在另一处执行。S04合并对未解决hold另设冲突，不把hold伪装为execution；历史段身份和审计保留。

外检保留后再交还，原实际ended_at保持；handed_over_at单独记录后来交还时刻。没有删除历史、治疗完成或库存/费用动作。

## 动作表

入口均为已登录POST `/ydental/queue/action`，CSRF开启、JSON参数白名单由固定handler签名验证；session/revision由S01绑定。模型方法均私有，不提供公共RPC业务旁路。非查询操作在同一savepoint内原子提交；失败整笔回滚。

|动作/输入|前置、权限与防重|原子结果和失败恢复|
|---|---|---|
|reserve(lease/token/execution/target_task)|原serving、原actor/连接、本店medical write、同患者/本店明确exam或medicine目标；固定可信server来源hook必须返回True|原段历史reserved、任务suspended、唯一hold active；重复同段同目标返回原hold。目标不同/已处理拒绝；不造capacity/新服务，不自动外检报到|
|query_return(patient)|当前店具备最小业务读取，canonical/current relation有效；无lease/token要求|hint_only；有效hold提示原区/椅；过期/verify仅提示现场核实；无hold提示按目标task普通报到。不调用expiry，不新增业务对象、审计事件、号码、资格或容量；技术mutex版本不属业务事实|
|restore(lease/token/hold/confirmed=True)|原有效hold当前合法持有人确认实际看见患者；原服务快照未漂移，工位/人员/资质仍合格|其他serving/verify拒绝且保留hold；只有其他waiting/calling时经S05 withdraw原子撤号/position/旧call，再新建resume段；外检任务pending保留、原claim不返、不发新号。不要求重新预约；closed有效hold可直返。重复已恢复返回原resume段|
|handover(lease/token/execution, optional mapping/reason)|原合法serving或当前active hold；先 `_save_before_handover` 最新草稿成功；产品默认fail-closed。新mapping必须同catalog、本店合法门诊方向且有原因；独立服务拒绝|同事务保存→唯一pending continuation→释放当前患者文书→历史handover→结束hold，工位lease保留。失败无continuation、执行和文书继续；重复返回原后继。多结果只复用同来源段唯一后继，不自动报到、不承诺原医生/椅|
|append(task/reason)|本店frontdesk=write且独立group `ydental_group_append`；当前无hold/actual execution；明确当前任务、有效S05资格、已有非open营业输入和原因|唯一active permit绑定patient/task/store/mapping/capability/业务日期/时区，原资格与容量不变。不指定人员/工位；重复有效许可返回原记录，不改排序/过号/机会。不同任务/服务/日期不能借用；过期未解决permit须明确核对|
|revoke(permit/reason)|同双重追加权限，本店active许可且本段尚未开始|S05 withdraw只撤waiting/calling/position，permit→revoked留操作者/原因/时间；不取消资格/医嘱、不退款/返容量。重复撤销幂等。start已先提交则拒绝普通revoke|
|call/start|保留A全部授权、execution area/精确能力/资格重验、N发布/排序；新增对应医疗/检查/药房工位类型|closed普通task无permit不可领取；有效permit可领取并在真实start原子变started。revoke先提交则start不能发生。过号/故障/重报沿用原entry和permit，历史missed/优先不刷新|
|timeout|固定系统自动化actor；与请求同锁序|active lease失效、hold→verify；旧token无效、原actor/工位/门店围栏仍在；查询只提示核实。不自动释放给新医生，不自动完成；serving/verify执行保持A语义|

## 保存、目标来源与资质

产品 `_external_target_authorized` 默认False；`_save_before_handover`默认拒绝。S08/S09以后须继承真实来源及保存，保存和 `_release_execution_documents` 必须处于同事务。不能用JSON/context声称来源合法或已保存。B测试模块使用受新库guard约束的冻结ReturnSource/ReturnPlan，独立合成文书锁仅证明保存失败不释放、保存成功释放本患者文书；它不是病历/医嘱表。

continuation从原门诊段快照复制catalog、capability、qualification和reporting/execution area；默认同mapping，parent_task和source_execution可追溯。无原医生/工位字段、无新entitlement。call/start和report重验要求快照；不把Panorama/CBCT等设备能力并集复制。非空资格仍使用A可信server hook，无真实provider时fail-closed。部分结果不额外生成后继；新独立服务仍需S05新资格。

## 固定锁序及真实竞争

S01 actor/session→S04 patient→S03 supply/space→S05 intake→S06 queue。B沿用A全局稳定mutex和RR更新锚点，hold/execution/permit仅在最后边界修改；reception动作先S01 scope再全锁，之后重验双权限。restore撤S05 position虽调用原服务，已持有全部前级锁，不在queue之后首次取新前级锁。并发grant使用原相同fence；timeout不取得另一用户session锁。serialization failure仅由框架/独立测试cursor有界重试，产品不commit。

B真实竞争12组：restore先/外检start先、restore vs call、重复handover、保存失败 vs可信重试、两结果同时复用后继、同task重复append、revoke先/start先、hold timeout先/restore先、holding doctor call vs外检start；每组两条同时存活PostgreSQL连接、独立backend PID、barrier或持锁交错及重试轨迹。A原21组另行连续回归。

## 升级、配置和未实现

模块20.0.1.1.0。init仅移除A原patient/lease终身unique，保留entry unique及全部行，回填旧task/服务快照并建立未解决部分索引。验证使用全新B库中的A形态旧约束/旧行夹具，再真实-u；不接管A历史库，不宣称完整安装过A源码树后迁移。

心跳/超时/N仍显式配置且未生产批准。模型/UI合成2秒/20秒/N=2，并发夹具部分使用600秒避免测量干扰；不作为生产配置。closed只是既有S03输入，不实现C清队/日终/水位/推送/区域屏。外检/药房只验证queue/start/患者互斥，真实项目完成、结果、发药、医嘱、库存和治疗文书均NOT_RUN。verify/失效hold保留现场核实阻断，不增管理员强抢或无来源接管。
