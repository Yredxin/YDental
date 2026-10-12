# S06-A 四项修正契约

唯一修正来源为[GPT-REVIEW6117074066](https://github.com/Yredxin/YDental/issues/30#issuecomment-6117074066)及本次用户指令。原启用6116491783和A批边界继续适用。原`840df8921cfb5a70c601e6e8ed81fb7d03aacd5b`、原报告及全部失败链保留；本文补充[原契约](s06a-contracts.md)，不另立业务计划。

## 未解决execution与原人员

`_actor_execution(user_id=None)`以execution→lease→真实actor查询serving/verify事实，不以lease.active决定实际执行是否解决。该查询供进入工位、call、start、全局status、S01 execution store fence及dashboard共用。

- serving timeout仍仅将execution/entry变verify并失效连接。原患者、原工位、原人员三个围栏同时继续有效。
- 原actor不能进入任何新椅、call或start另一患者。没有active lease并不表示空闲。另一session、切店不能消除execution store fence；有目标店真实membership和写权限时，人工业务写仍拒绝。
- status在失效lease后从execution返回旧店/区/工位及state=verify；页面和后台全局提示使用“待现场核实”标签，所有进入/换椅入口对该actor不可用。
- 其他合格人员可以在其他合法空椅工作；旧椅及同患者仍不可复用。旧token继续拒绝。
- `_handover_contract`仍默认拒绝；没有管理员强抢、核实完成、接手、交还或治疗完成入口。

## 统一task/station资格

私有`_eligibility(entry, station, actor=None)`返回空字符串表示可领取，否则返回稳定错误前缀及已翻译原因。call、start和页面“无在岗原因”使用同一helper，客户端不传eligibility结果。

|层次|服务端判断|
|---|---|
|人员|actor及membership/employee仍有效；当前工位类别业务write；完整覆盖全部active工位能力；无未解决execution|
|报告位置|task/entry/station同店；entry reporting area等于task mapping reporting area及station queue area，均有效|
|执行位置|station实际area必须等于S05 mapping execution area或其合法后代；整条祖先链有效且同店，不以同一reporting area替代execution area|
|能力|entry能力等于当前task mapping catalog的有效固定能力，station精确覆盖；不改任务服务或能力|
|资质|catalog.ydental_qualification为空不增加条件；非空必须经`_qualification_satisfied(task,station,actor)`返回严格True|
|患者|无未解决实际execution；start仍通过原S05真实资格/claim consume与canonical/current relation检查|

基础`_qualification_satisfied`无条件False，不猜测岗位名称、字符串相等或客户端context。测试provider只存在于guard保护的`ydental_queue_test`；冻结QualificationSource绑定actor/task/station/requirement/布尔事实，经私有server方法落到无普通ACL的合成表。create/write还需object身份，JSON/context/dict不能伪造；源资质要求或人员/任务/工位任一不符均不授权。HTTP正路径使用服务器准备事实，HTTP自身不能提交“已合格”。没有新增真实资质业务模块。

call锁后筛选，start锁后重新执行相同helper；call成功后撤资质或改变执行区/目录能力，start拒绝且claim仍held、calling保留，无半consume。

## missed与fault的排序

call在改变entry之前要求区域N>0；N=0直接configuration_required，entry仍waiting、lease仍空闲。页面提示未发布且call按钮禁用，JS保留服务器disabled状态，直接POST也拒绝。心跳/超时及N仍未生产批准。

新增entry服务器字段：

|字段|类型/含义|写入边界|
|---|---|---|
|ydental_call_rank|Integer；本次call之前的有效区域位置（1起）|call冻结；不是前端数组或客户端输入|
|ydental_call_order_before|Integer；call前排序锚点|call冻结；其他真实missed需要归一坐标时按同一有效顺序等价变换，保留该live call的相对锚点|

两字段默认0（尚未call），无关系/货币/隐私凭据；沿原entry来源读取与导出权限，普通CRUD不可写，只有object身份受控服务事务可改，非客户端承诺或生产配置。新增时仅本批全新库install/upgrade，没有业务数据迁移。

`_ranked_area`将waiting和仍calling的服务器锚点统一排序。calling使用call前opportunity和order；患者暂时离开waiting集合不导致区域队首重新计数。

真实missed从max(本次call前位置, 当前有效锚点位置)向后N位；不足N位到队尾。不会因本椅只覆盖部分能力而将区域第3/4位重插到队首。消耗本次return机会后，还不能超越其他未用return机会。其他有效任务相对顺序保持；顺序归一同时保留其他calling锚点，真实多连接验证另一能力call竞争。

fault/timeout只恢复call前opportunity及有效order锚点，不调用N算法，不增加missed，不清既往真实missed。同任务重报继续沿用已有排序/机会/计数。原回诊分类及S05 position/资格/容量语义未改。

## 自动timeout审计

自动过期由固定`base.user_root`（系统自动化身份）调用公共audit，event=`queue.connection_timeout`、source=`workstation_timeout_automation`。该身份由服务器固定选取，不是调用方提供。

after固定保留holder_user_id、lease_id、station_id、release_reason=timeout、calling_returned、verification_required。无关B请求触发A过期时，audit.user不会成为B，也不冒充A主动退出；cron与请求触发共享同一`_expire`实现和事件语义。持有人主动退出仍是既有holder_exit事件，未混为自动过期。

## 原内核、未启用与回滚

继续S01 session→patient→supply→intake→queue固定锁序、RR更新锚点、有界40001重试验证、原token/session/connection绑定及唯一约束。S03账本、S04 merge、S05真实hook/position/start、价格快照均未重写。修改仅在全新隔离S06-A库install/upgrade，不迁移业务库。

当前execution历史终身唯一仍保留；A没有合法终态。按review留给B的结构要求：引入合法交还/结束段之前须扩展为仅未解决事实的部分唯一或等价设计，保留历史，不能物理删除execution规避。原生Odoo账号logout的专用业务释放hook仍未实现；当前明确“退出/休息/登出工位”业务按钮及连接timeout语义保留。

B保留/接手/交还/后继/追加、C日终/推送、S07和真实S08文书均NOT_RUN。S08固定文书锁默认拒绝及原合成验证保留。生产心跳/超时/过号N、生产部署均未批准。原commit/失败库/证据不删除；本批未安装业务库，回滚只需回到原固定提交/分支，不执行真实数据回滚。
