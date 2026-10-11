# S03 定向返工补充契约

本次只依据 [GPT-REVIEW 6110896380](https://github.com/Yredxin/YDental/issues/27#issuecomment-6110896380)与同一S03会话用户授权修三个BLOCKER。原d652026代码/文档/证据及失败链保留；原[s03-contracts.md](s03-contracts.md)中容量、返池、转换、原子事务、营业、离职及下游NOT_RUN契约继续有效。本文件只补实际修正，不新增计划。

## BLOCKER-1：合格工位建议

区域安排查本门店目标区域子树的工位；直接工位安排也通过同一过滤。每个建议工位必须active、enabled，且`active工位能力集合 <= active员工能力集合`。空required集合在能力维度不要求额外能力，仍须满足地点/启用条件。任意交集不能替代完整覆盖。

_assignment_warning、_replacement_candidates和_workbench_suggestion均按active能力完整覆盖解释资格。直接保存不具备完整能力的默认安排仍合法且有warning，但不会因此将该工位列为合格建议。增加缺失能力后可返回。建议仍是hint_only / execution=not_connected，真实S06租约、实际资质与占用未接入，不授予实际执行资格。

## BLOCKER-2：独立assignment冲突处理

新增私有`_handle_assignment_conflicts(assignments=None)`：只由已经通过各所属模型权限检查的服务器change hook或已鉴权的adjust调用，不能RPC调用；不在GET/compute中写数据。采用既有S03空间advisory+mutex锁，查询state=active且end>服务器now的安排。对当前有warning、没有assignment级pending的记录生成disposition与不可变assignment_conflict事件；初始草稿保存仍只提示，不要求先发布槽。

|触发|处理|
|---|---|
|resource.calendar.leaves create/write|复查既有有效安排，不依赖published slot；重复同一absence或hook去重|
|station active/enabled/callable/增减能力变更|复查安排，动态warning和替班候选保留；原slot失效路径照常执行|
|人员账号active/能力、原生employee.active变更|生成对应安排处理；停用员工warning明确；不自动取消安排|
|既有图元关联/归档、资源能力、能力字典active变化|复用当前服务器hook复查；只对实际warning创建处理|
|adjust默认安排|更改后复查同一安排；既有容量覆盖失效处理继续独立执行|

assignment级待办定义：assignment_id非空、slot_id为空、state=pending；同一安排只有一个当前pending，已有pending保持原记录/原因。查找在同一互斥锁下执行，pending关系一次批量查询，重复服务器事件不能无限追加。已结束或已取消安排不新建冲突待办。

冲突消失不自动resolve，不抹处理事实；人工resolve需本店capacity写、页面revision和记录version，填写处置原因，保留旧记录及事件。resolve后仍有冲突并再次发生服务器变更时可生成新pending，旧resolved历史不改写。既有离店/离职取消未来安排的处理设计继续有效，不用本机制替代它。

有published slot时两类对象独立：assignment级记录指向具体默认安排；slot级记录指向供给槽。slot继续只在published→suspended时生成其失效处理，反复hook不追加同一暂停事实；assignment记录不会被slot记录覆盖。二者解决的问题分别是人员默认安排与已发布资格供给，均不删除已有claim。

新增原生hr.employee继承仅监听active写入，不新建人员模型/身份；无新字段、表或ACL。assignment warning依赖补齐账号/员工active和能力active；请假等外部变更仍由服务器hook锁刷新缓存。

## BLOCKER-3：当地墙钟与DST

统一私有`_local_to_utc(store, value)`接受无时区的ISO当地时间字符串或naive datetime，返回naive UTC datetime。门店IANA时区为唯一解释依据，不使用浏览器时区。带UTC offset的当地表单值拒绝，避免混合语义。

分别尝试fold0/1，转换UTC并round-trip至门店当地年月日时分秒：没有有效候选表示nonexistent，返回可读错误；两个不同UTC候选表示ambiguous，也拒绝并要求选非歧义时间。普通时间只有一个不同UTC候选，往返保留原输入。**统一策略为拒绝不存在和歧义时间，没有静默选fold或平移。**

|入口|语义|
|---|---|
|assign/adjust表单|start/end均调用helper|
|batch表单|每个当地日期+start_time/end_time都调用helper；任一行异常整批不保存|
|slot/extend表单|所有datetime-local字段调用helper，之后仍执行原UTC时段/同营业日校验|
|copy previous week|先在naive门店当地时间构造上一周/当前周起点，分别转UTC；不得UTC直接减168小时。每条起止先转当地、加7个当地日，再用相同helper转UTC；目标缺失/歧义整批拒绝|
|周视图|当地本周/下周起点分别转UTC，正确覆盖167/169小时的DST周|
|private service /显式UTC JSON payload|保持原UTC契约，_interval不调用当地helper；明确的UTC可表示歧义当地时间的任一真实时刻|

纽约秋季示例：上一周2026-10-26 00:00=04:00UTC，本周2026-11-02 00:00=05:00UTC；00:30安排必须包含，前一周日23:30排除。春季对应窗口分别05:00/04:00UTC，不能错误多收前一周最后一小时。复制保持当地墙钟；2026-03-08 02:30不存在、2026-11-01 01:30有歧义，均明确拒绝。

生产配置发布边界、容量来源默认fail-closed、demo不可生产消费、真实S05/S06接入/00:10清理NOT_RUN均未改变。最终自测与固定SHA见[s03-rework-report.md](s03-rework-report.md)。
