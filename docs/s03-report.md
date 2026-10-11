# S03 交付验收申请｜YD-N1 R1

本报告是 Codex 作者实现与自测交付，申请 GPT 独立技术复核。不是 GPT 已通过、用户已验收或生产发布。只实现 #27；完成交付评论并读回后停止，不进入 S04。

## 来源与固定版本

本次用户明确启用 S03。开工前完整读取 #23 当前 R1 正文及有效评论、#27 当前正文及全部有效评论、#26 最终技术复核与状态同步。执行边界是 [GPT-ACTIVATE 6110183188](https://github.com/Yredxin/YDental/issues/27#issuecomment-6110183188)，流程依据是 [6110178328](https://github.com/Yredxin/YDental/issues/23#issuecomment-6110178328)。[开工检查6110252817](https://github.com/Yredxin/YDental/issues/27#issuecomment-6110252817)先写回、完整读回，之后才实施。没有读取撤销旧计划、旧聊天或四份旧对照文件补需求。

S02 [最终技术复核PASS](https://github.com/Yredxin/YDental/issues/26#issuecomment-6110161675)及[状态同步](https://github.com/Yredxin/YDental/issues/26#issuecomment-6110222109)满足前置，#26保持OPEN/待用户验收。当前来源全文保存在[requirement-sources.json](evidence/s03/requirement-sources.json)；交付前再次读取#23/#27，正文与原读取相同，没有新增范围决定，核对见[delivery-source-check.json](evidence/s03/delivery-source-check.json)。

|项目|固定值|
|---|---|
|Git根/远端|sd-addons独立仓库；Yredxin/YDental|
|工程基线|`e97f721270a991bd4a737c15808896b286e488e9`|
|核心|`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，本地声明20.0 fork；未冒称已核对同SHA官方上游|
|产品最终提交|`743fc4312a0abde36c8123de27024fd4577e341c`|
|产品+最终测试提交|`7b2fb524829d1a8e3f5e4dfad893919effe0eceb`|
|最终文档/证据提交|本文件所在提交；#27交付评论固定其完整SHA|
|分支|`codex/s03-supply-r1-20261011`；直接推送独立分支，无强推/合并|
|版本一致性|产品→test只改scripts与ydental_supply_test；test→final只改AGENTS及S03文档/证据，无测试后产品变更|

## 实际环境与隔离

仅在本次新建的6个S03隔离库使用合成数据；没有接管S00/S01/S02历史库或业务库。创建与每次动作的完整摘要、退出码、被测SHA、私有日志SHA256见[runtime-history.json](evidence/s03/runtime-history.json)，所有失败库和原始日志留在本机私有目录，不上传原始日志。

|最终运行标识|值|
|---|---|
|数据库|`ydental_s03_test_20261011153907_87f7ea2a`|
|创建UTC/OID|2026-10-11T15:39:07.390284+00:00 / 261433|
|端点/集群|127.0.0.1:5432，角色odoo；7694897083368259627|
|配置SHA256|`ab7124b36c49010a0a6a842eb5415c8ddd12762c9526f9ad55d359cf58fcf7e4`|
|运行配置|独立配置/data_dir/日志；精确dbfilter；HTTP仅127.0.0.1:18105；list_db=False、cron0、SMTP127.0.0.1:1；进程外发限制|
|Python/浏览器|核心.venv/bin/python；既有Playwright依赖与Firefox155，默认sandbox未覆盖|
|预览生命周期|最终截图/账本提取后，仅核对并停止本次精确PID/config的S03预览；见[preview-lifecycle.json](evidence/s03/preview-lifecycle.json)|

scripts/s03.py先检查新库名、端点、集群、库不存在，再创建并记录OID；后续升级/探针/预览必须匹配创建记录及配置哈希。拒绝无记录旧库、错误端点、业务端口；不能drop/reset/adopt。浏览器只允许本次loopback端点。未安装系统依赖、修改核心、停止/重配既有服务或触碰父目录既有未跟踪AGENTS。

## 需求完成情况

|R/功能|本阶段状态|实现位置/范围|
|---|---|---|
|R01 工程契约/字典/翻译/审计|完成S03范围|ydental_supply；[契约](s03-contracts.md)、[数据字典](s03-data-dictionary.md)、[作者安全自查](s03-security-review.md)；245条zh_CN核对|
|R06 人员安排、周视图、批量/复制、调整|完成|assignment与service；工位/区域二选一；人员/工位/跨法人同账号冲突；原生absence；区域人员不生容量；跨DST按当地墙钟复制|
|R06 我的今日/建议/反馈/未来处置|完成S03范围|_today/_default_candidates/_feedback；S01会话与离店钩子；反馈接收权限、无接收者店长提示；disposition处理记录|
|R07 共享槽/配置/覆盖核查|完成|slot/policy；能力视图不相加、区域去重；草稿可存与供给发布分离；动态能力损失暂停新增保留资格|
|R08—R09 来源/返池/转换/改期重配|完成S03内核与合成验证|claim/event/operation，私有_capacity_action；无患者/预约/实际医生绑定，真实下游接入NOT_RUN|
|R15—R16 营业/临时开诊/延长/加额|完成S03范围|business按门店区域当地日；open/draining/closed/reopen；真实清队、执行保留、00:10由S06负责，NOT_RUN|
|S04/S05/S06真实业务|未做，符合启用边界|无患者主档、预约、队列、真实坐诊租约模型；只提供固定服务器扩展点，不建未来空壳|

原生评估已检查锁定resource/calendar/hr_leave源码；复用hr.employee→resource.resource与resource.calendar.leaves。当前Community无planning，不引入OCA。完整hr_holidays审批流未安装实测，不将absence模型测试说成审批联调。UI为功能性服务器表单/周分组表，无新的static资源；统一美化仍归S13。

## 流程实际回放

以下均在最终test提交的合成环境断言；“预约/开始”表示S03资格内核操作，不是已经实现真实患者预约或坐诊。

|示例|合成前提/操作|预期与实际|固定证据|
|---|---|---|---|
|F1|洁牙S1、洁牙/补牙S2，各Q6；依能力占用|PASS：区域总12；洁牙优先S1、补牙S2；能力视图不可相加；最后一个预约份额仅一连接成功|test_t02；concurrency last_capacity|
|F2|固定服务器时钟，独立资格在开始前/后/过期/consume后取消|PASS：开始前返原池；开始后同槽现场；过期/停接转不可再售；consumed拒返；重复取消仅一条释放事件；与consume竞争只允许一个终态|test_t03/test_t10、stopped_release；concurrency cancel_start/repeat_cancel|
|F3|两连接强制两种预约/转换锁顺序；改期目标满额；成功重配|PASS：先占只转剩余，先转则拒迟预约；失败原资格不动；成功新占旧取消原子；只改来源记账，无医生绑定|test_t03/test_t04、successful_move；concurrency reservation_first/conversion_first/source_move|
|F4|同一员工当前A、下一时段B；新旧独立登录；A反馈与移除；跨公司集团离职|PASS：当前登录建议A，后续新登录建议B，旧A会话不跳；反馈只送有效写人员；移除A未来安排取消并留待办，B资格不受影响、A已占claim保留；集团离职保留历史|test_t12/test_t13、cross_company_conflict_departure；Firefox我的今日/反馈截图|

## 测试结果与逐TC映射

全部最终命令使用上述新库、18105、最终test SHA。runner安装/升级启用`--test-tags /ydental_supply_test`；普通业务操作以有权writer、readonly reader、仅自助staff执行，root仅创建合成环境和断言观察，不以超级用户替代权限测试。HTTP通过真实登录请求，Firefox通过真实表单。

|实际命令/检查|结果|数量/退出码|证据|
|---|---|---|---|
|`../.venv/bin/python scripts/s03.py install --db <最终库> --port 18105`|PASS|0 failed / 0 errors / 32；exit0|runtime-history最终run的install|
|同runner `upgrade`|PASS|0 / 0 / 30；exit0|runtime-history最终run的upgrade|
|同runner `probe`|PASS|6组真实独立PG连接交错；exit0|[concurrency-final.json](evidence/s03/concurrency-final.json)|
|`../.venv/bin/python scripts/test_s03_guard.py`|PASS|5；exit0|[guard-final.json](evidence/s03/guard-final.json)|
|`scripts/s03_browser.py --db <最终库> --port 18105`|PASS|Firefox155，17检查；exit0|[browser-final.json](evidence/s03/browser-final.json)，5张截图及SHA256|
|同runner `export`+Babel解析实际POT/PO比对|PASS|245源条目；缺失/多余/空译/引用错位均0|[translations-final.json](evidence/s03/translations-final.json)|
|合成预览固定字段只读账本快照|PASS|8槽守恒；6claim、41事件、6安排、1反馈、3营业记录|[ledger-final.json](evidence/s03/ledger-final.json)|

32安装项中，实质S03测试为26模型+4真实HTTP=30项；另2为原生HOOT桌面/移动入口无本模块匹配资源返回，不冒称完整JS套件。升级30项均为实质测试。TC是复合需求映射，不能将“14条定义”与方法/断言数量相加。

|TC|S03结果|实际断言/补充证据|需下游补验|
|---|---|---|---|
|T01|PASS|Q1/2/3/6、floor/nearest、0告警、冻结版本、production demo门禁；Firefox预览|正式参数批准未发生|
|T02|PASS|能力共享总量/来源排序；last_capacity两个PG连接最后份额|真实预约来源接入NOT_RUN|
|T03|PASS|同键幂等、换参拒绝、重复取消、失败改期/重配保持原值；成功迁移、consume后不倒改|真实预约/号序同事务NOT_RUN|
|T04|PASS|两种有序交错均实测；converted一次、拒迟预约、守恒|真实渠道联调NOT_RUN|
|T05|PASS|跨门店/跨法人同账号、工位冲突；原生absence；既有安排警告/替班|完整hr_holidays审批NOT_RUN|
|T06|PASS|工位停用、图元/资源/能力/人员/absence变化暂停新增，claim保留；待办与处理|真实预约迁移/联系送达NOT_RUN|
|T07|PASS|readonly/越权拒绝、真实槽+原因、加额/减额保护/延长后重核查；HTTP/Firefox|无额外生产发布声明|
|T08|PASS（S03）|本地日营业唯一、先draining才closed、未接队列默认拒绝、合成清空检查、重开不加容量、次日新记录|真实队列/失效号/保留/00:10 NOT_RUN|
|T09|PASS|最终空库安装32/升级30；配置/历史保留；无未来模型依赖|生产迁移NOT_RUN|
|T10|PASS（内核）|开始前/后/过期/停接/已consume取消；cancel_start双连接互斥、repeat_cancel一次释放|真实接诊/租约竞争NOT_RUN|
|T11|PASS|周视图两种分组、批量原子、复制/冲突重开、区域不生额、DST；Firefox真实表单|无需未来业务|
|T12|PASS（S03）|完整F4，独立会话、反馈接收者/无接收者、自助建议；HTTP/Firefox；合成S06全局位置钩子阻止他店写|真实租约/无排班坐诊/换椅NOT_RUN|
|T13|PASS（S03）|单店移除/集团离职未来取消，历史/其他店/claim保留，待办可查|真实患者联系/预约处置NOT_RUN|
|T14|PASS|资质不符草稿保存有提示；发布覆盖独立核查、记录核查快照；claim无医生字段|实际人员/工位执行资质S06 NOT_RUN|

并发使用不同backend PID、repeatable-read真实事务；barrier同步、边界两个场景以服务器私有时钟缝与事件控制先后，不伪造客户端时间。共享mutex UPDATE迫使旧快照整事务SerializationFailure重试。每次attempt的PID、隔离级别、重试、结果及最终R/W/unavailable/used均保存在并发证据。未以线程内存锁或单连接模拟代替数据库争用。

真实HTTP4项涵盖周页/自助页/写表单、业务权/跨店/旧页409、私有RPC拒绝、伪造ORM token拒绝、CSRF400、营业不增额；Firefox17项详见结果逐项清单，没有关闭安全控制。

## 配置、前后账与人员处理专项材料

完整字段、关系、状态、权限、不可变来源见[数据字典](s03-data-dictionary.md)；所有动作参数/前置/锁/原子副作用/失败恢复及下游外层事务要求见[工程契约](s03-contracts.md)。

|配置|本次明确演示/工程策略|生产处置|
|---|---|---|
|默认比例|1:2，Q1/2/3/6预览0:1、0:2、1:2、2:4|1:2已确定；本次不是实际营业发布|
|取整|floor；另测nearest|具体选择待负责人确认|
|覆盖层级|工位→最近祖先区域→门店；槽冻结版本|策略已交付，实际门店版本待确认|
|电话代约|reservation；另测walkin|真实S05渠道来源待接入及正式选值|
|截止|演示0，另测15/20分钟；开始转换只一次|正式值待确认；转换后永不接受新预约|
|demo/正式|demo显式标记；生产_allow_demo_supply=False；published需approved=true|生产来源适配器默认拒绝；无正式参数被本批批准|

[ledger-final.json](evidence/s03/ledger-final.json)含每个事件的actor、原因、policy ID和before/after完整快照，以及当前8槽守恒。选取范围仅本次probe创建的合成预览门店；无备份、患者或凭据。模型用例TransactionCase记录会回滚，F2及离职断言依据固定测试源码及运行摘要，不伪造其持久截图。预览disposition=0表示此浏览器流程未执行离职；不将空表冒称离职实证。

|人员专项|真实验证|证据/边界|
|---|---|---|
|首页|staff本人当日门店、时段和工位；区域建议合格工位；会话不随时钟换店|T12、HTTP、Firefox截图05；execution明确not_connected|
|安排有误|本人安排才可反馈；writer接收、reader不接收，待办可查；重试去重；无负责人manager_required|T12及fallback额外测试、HTTP、Firefox；未发短信/邮件|
|单店移除|A未来安排取消、A历史保留、B不受影响、A已占资格保留且供给失效待办|T13；与S01真实移除钩子联测|
|集团离职|同账号跨法人关联处理、对应未来安排取消、历史原因保留|cross_company_conflict_departure额外测试；非真实员工离职|
|供给失效处理|替班候选、暂停新增、保留已占与联系/迁移待办；resolve留原因；重发布另行核查|T06及capability/absence/resolve额外测试；无下游自动迁号|

## 用户效果验证入口与步骤

角色仅给语义，不提供凭据：本店排期读写writer、只读reader、仅自助staff。菜单“排期与容量”“我的今日”；路由`/ydental/supply`、`/ydental/supply/today`。本次自己的预览已停止；需要重看时可用原创建记录启动`scripts/s03.py serve --db <最终库> --port 18105`，访问凭据仅在本机私有access.json。不得复用历史业务库。

1. writer进入周排期，切换工位/人员及上一周/下一周；内容按当地日期显示。
2. 复制上一周并重开页面；保留安排，冲突全批拒绝。用批量表单保存区域/工位安排，区域不增加槽总量。
3. 保存不具备完整工位能力的默认安排；页面提示草稿可保存、发布需独立核查，给出替班候选。
4. staff进入我的今日，查看本人门店/时段；进入建议工作台只显示建议与未接S06，不产生真实租约。
5. staff点安排有误；writer刷新看到待办，reader看不到写操作；确认两个会话不相互换店。
6. writer创建明确demo策略，查看Q1/2/3/6整数和0预约告警；新策略不更改已有槽版本。
7. 新建真实工位时段Q6，按实际合成人员覆盖核查发布，再加额到Q9；多能力共用一份总量，原因/前后账可查。
8. 取消/改期/重配查看固定内核测试与账本：开始前返原池、开始后返现场、目标满额原资格保留。当前没有S05患者预约页面，不以伪患者按钮替代该业务。
9. 显式开诊、停普通报到、带原因重开；槽数量不变。停止普通叫号在未接真实队列时拒绝，合成检查只在隔离测试使用。

最终Firefox截图：[周排期](evidence/s03/browser-attempts/20261011T154327482490/01-weekly-plan.png)、[共享容量](evidence/s03/browser-attempts/20261011T154327482490/02-shared-capacity.png)、[营业日](evidence/s03/browser-attempts/20261011T154327482490/03-business-day.png)、[只读](evidence/s03/browser-attempts/20261011T154327482490/04-readonly-capacity.png)、[我的今日/反馈](evidence/s03/browser-attempts/20261011T154327482490/05-my-today-feedback.png)。截图仅虚拟业务；纯功能表单样式不代表S13美化已交付。

## 失败链与补交

没有用最终PASS覆盖历史失败。6个创建记录与全部动作均保存在runtime-history；每条指向原被测提交和不可变日志哈希。浏览器历史attempt目录也全部保留。

|隔离库时间/后缀|历史结果与处置|
|---|---|
|150626_af74a5b9|首次ACL导入exit255；按锁定Odoo20实际model_id点分名称API修复|
|150745_c0b603d1|原生配置fixture API错误；后续重复合成账号/会话冲突、字段标签脚本语法错误及未隔离查询断言失败；逐项修复，原失败摘要/哈希与Git提交保留；最终该库升级28项通过，但不作为最终交付库|
|152424_37af4cf3|安装31/升级29通过；新增有序边界probe首次未开合成营业日而失败，补开明确营业日后6组通过；该次Firefox17通过保留|
|153311_5f62005c|安装31/升级29、6组并发、Firefox17均通过；随后为完整F4/全局位置契约增加测试|
|153707_63085904|新F4 fixture本人当日跨A/B两条安排被当作singleton，安装0 failed/1 error/32；仅改测试选择A当前店安排，不改产品|
|153907_87f7ea2a|最终全新库安装32/升级30、6组并发、Firefox17、guard5、翻译245全部通过|

## 数据、审计、回滚与未交范围

新增仅ydental_supply实际S03表/菜单/ACL/种子mutex；生产未安装、无业务数据迁移。测试模块不得用于业务库。没有费用、库存、资金、临床文书写入。UTC时间、门店当地日、冻结policy与覆盖快照、actor/reason/幂等receipt/不可变事件用于追溯；源ORM改删/导入越权被阻止，安全细节见作者自查。

回滚在未部署现状只需保留独立分支与本次私有库供复核，不合并即可；如需代码回看切回S02固定分支，不卸载有历史记录的模块或删账本。未来真实部署前必须另行批准参数/迁移及可恢复备份；不把本次合成快照当备份恢复实证。

NOT_RUN：S04患者主档，S05真实预约/现场业务与已有资格报到不重扣的端到端流程，S06真实waiting/calling/号序保持、执行租约/资质/全局位置、无排班换椅/加班/保留直返/追加、00:10清前日及真实跨日服务；完整hr_holidays审批；真实邮件短信送达；生产参数/迁移/发布；S13统一美化、50会话、持续备份恢复目标。上述只交付服务器边界与必要合成验证，不算真实联调通过。

本次没有写Project任何字段、原生Status、workflow或Issue/PR实体状态，没有PR合并、关闭#26/#27或生产发布。证据哈希清单见[artifact-manifest.json](evidence/s03/artifact-manifest.json)。申请GPT审查固定产品/test/final版本；本轮交付后停止，等待复核，不启动S04。
