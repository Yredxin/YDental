# S03 修正交付与复核申请｜YD-N1 R1

本报告是 Codex 定向修正及作者自测，申请 GPT 独立复核；不表示技术已复核通过或用户已验收。只修 [GPT-REVIEW 6110896380](https://github.com/Yredxin/YDental/issues/27#issuecomment-6110896380) 的三个 BLOCKER，继续当前 S03 会话和分支。原交付及失败链完整保留，未进入 S04。

## 来源、流程与固定版本

返工前完整读取上述最新评论，并重读 #23/#27 当前正文及有效评论；未读撤销计划或上一聊天补需求。当前来源全文见 [requirement-sources.json](evidence/s03-rework/requirement-sources.json)。S02 最终技术 PASS / #26 OPEN 待统一用户验收的依赖状态不变。

按本轮用户明确授权，**先完成 Project #27 自定义“执行状态”更新为“返工”，完整读回并二次同步确认，随后实施**。唯一 mutation 于 2026-10-11 16:06:16 UTC 发起；16:06:29 UTC 完成两次读回。原值“待启用”→“返工”；原生 Status=Todo、Issue=OPEN、其他字段、视图及 API 可见 workflow 元数据不变。交付前第三次完整读取仍与第二次一致。没有在代码交付后擅自改为“待复核”。

读取范围为 Project 4 全部37项（含归档）、21字段及选项、6视图（可见字段/分组/排序）和7 workflow 的公开身份、启用状态与时间戳，分页与嵌套数量均核对。API 不公开 workflow 内部 trigger/action；冗余 configuration.visibleFields resolver 报错，完整可见字段通过 views.fields 读取。没有写 workflow 或原生 Status。完整前后快照、唯一 mutation 及最终比对见 [Project 证据](evidence/s03-rework/project/verification.json)。

|项目|固定值|
|---|---|
|原最终交付|`d652026eb6236cf0fccbff9ab6da6cab685758bf`，保留原报告与证据|
|本轮产品修正|`ac34c247c35e531567871ae2d8da065826833fe9`|
|本轮产品+最终测试|`31d69ccaf2ef4e7ce7c49c7d8e0acce3c5f903d6`|
|本轮最终文档/证据|本文件所在提交；#27 修正交付评论固定完整 SHA|
|分支/远端|`codex/s03-supply-r1-20261011` / Yredxin/YDental，继续原分支，普通推送|
|核心/Python|`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` / 核心 `.venv/bin/python`；本地声明20.0 fork|
|版本关系|ac34→31d69 只修测试fixture；31d69→final 只增加文档/证据及更新 AGENTS，无测试后产品变化|

## 三项修正与针对性证据

实际工程补充契约见 [s03-rework-contracts.md](s03-rework-contracts.md)。

|BLOCKER|最终行为|新增实际验证|
|---|---|---|
|1 合格工作台|区域子树内 active/enabled 工位，全部 active 工位能力必须被员工 active 能力覆盖；空 required 集合允许；直接工位安排同样过滤|模型2项 + HTTP1项：Cleaning 员工仅返回 Chair1，Cleaning+Filling 的 Chair2 排除；直接指向 Chair2 仍有 warning 且不建议；增加 Filling 后返回；空集/子区域/区域外/停用/归档边界；Firefox 区域及直接建议|
|2 assignment 级处置|服务器变化钩子复查 active、尚未结束安排；无 published slot 也产生 assignment_id 有值、slot_id 为空的 pending disposition 及不可变事件；同一安排 pending 去重|模型4项 + HTTP1项：后加 leave 有 warning/替班候选/处理记录；重复 hook 不追加；停用工位/能力变化/停用账号/独立归档员工；已结束/取消不新建；冲突消失 pending 保留；人工 resolve 保留历史；有槽时 assignment 与 slot 各自一条且已占 claim 保留；reader resolve=403，writer=200；Firefox 可见及处理历史|
|3 DST|统一 server helper，表单全部使用门店时区；不存在和歧义当地时间均明确拒绝；普通输入 UTC 往返不移时；copy 和周视图在当地构造两端再各转 UTC|模型4项 + HTTP2项：纽约秋季周一00:30及周日23:30包含、窗口外排除；春季不误收前一周末一小时；复制目标 gap/fold 整批拒绝；assign/adjust/batch/slot/extend 全部 gap/fold=409 且无部分写入，正常时间全部精确 UTC；显式内部 UTC 保持有效；Firefox 秋季边界复制与 gap/fold/正常表单|

新增10模型 + 4 HTTP，连同原26模型 + 4 HTTP 全部回归。处置查询在既有 S03 advisory+mutex 边界内批量查已有 pending，避免逐安排重复查同一待办。新增 hr.employee 继承只监听原生 active 写入；没有新业务模型、字段、ACL 或公开 RPC。

歧义统一策略是**拒绝**：纽约 `2026-11-01 01:30` 有两个 UTC 候选，提示选择非歧义时间；`2026-03-08 02:30` 没有候选，提示该时间不存在。没有静默 fold=0 或平移一小时。服务器内部明确 UTC 的调用保持原契约，仍可表示这两个真实 UTC 时刻。

copy 的上一周窗口用两个当地周一00:00分别转 UTC。纽约秋季 `2026-10-26 00:00=04:00UTC` 至 `2026-11-02 00:00=05:00UTC`，共169小时；春季对应167小时。复制每条起止保持当地墙钟，目标落入 gap/fold 则整批拒绝。周视图同样修正本周/下周当地边界，避免复制正确却显示漏行。

## 全新隔离运行与全量结果

只新建本轮2个 S03 隔离库，未接管或改写原 d652026 测试库、S00—S02 历史库及任何业务库。失败库未重置。最终产品和测试固定之后，在第二个全新库重新 install + upgrade。每次创建记录、动作、被测 SHA、退出码及私有原日志哈希见 [runtime-history.json](evidence/s03-rework/runtime-history.json)，已逐条验证日志哈希。

|最终环境|值|
|---|---|
|数据库|`ydental_s03_test_20261011162014_50ff775a`|
|创建 UTC / OID|2026-10-11T16:20:14.981240+00:00 / 279263|
|端点 / 集群|127.0.0.1:5432 / odoo；7694897083368259627|
|配置 SHA256|`5ae2b06c0976cf4fbd3e1caa3c41f0f59e2d82b8d3b08fec243f098ce9f52688`|
|隔离|独立配置/data_dir/日志；精确 dbfilter；127.0.0.1:18105；list_db=False、cron0、SMTP127.0.0.1:1、进程外发限制|
|预览门店|纯合成数据；六组并发后另置 America/New_York 以验证 DST UI；营业历史记录仍保留各自冻结时区|

所有最终运行固定 `31d69ccaf2ef4e7ce7c49c7d8e0acce3c5f903d6`。普通操作使用 writer、reader、staff，HTTP 经实际登录和请求，不以 root 替代权限验证；root 仅构造合成前提及观察断言。

|命令/验证|实际结果|固定证据|
|---|---|---|
|`../.venv/bin/python scripts/s03.py install --db <最终库> --port 18105`|PASS：0 failed / 0 errors / 46，exit0|runtime-history + [model-http-final.json](evidence/s03-rework/model-http-final.json)|
|同 runner `upgrade`|PASS：0 / 0 / 44，exit0|同上，全部44实质用例重跑|
|同 runner `probe`|PASS：六组真实 PG 并发，exit0|[concurrency-final.json](evidence/s03-rework/concurrency-final.json)|
|`../.venv/bin/python scripts/test_s03_guard.py`|PASS：5/5，exit0|[guard-final.json](evidence/s03-rework/guard-final.json)|
|同 runner `export` + Babel 比对实际 POT/PO|PASS：251条，缺失/多余/空译/引用错位均0|[translations-final.json](evidence/s03-rework/translations-final.json)|
|`scripts/s03_browser.py --db <最终库> --port 18105 --evidence s03-rework`|PASS：Firefox155，原17 + 新8 = 25项；默认 sandbox，无未处理页面错误|[browser-final.json](evidence/s03-rework/browser-final.json)，9张 PNG 及哈希|
|合成预览只读固定字段快照|PASS：8槽逐槽守恒；6 claim、53事件、15安排、1反馈、2处置、3营业记录|[ledger-final.json](evidence/s03-rework/ledger-final.json)|

安装46项含36模型 + 8真实 HTTP = 44实质测试，另2为原生 HOOT 入口无本模块匹配资源返回，不冒称完整 JS 套件。升级44项全为实质测试。模型 TransactionCase 数据会回滚，不能将它们冒称预览库持久记录。

六组并发保留原算法与实际不同 backend PID、repeatable-read事务、barrier、mutex/序列化重试，全部新库重跑：last_capacity 只一方取得最后份额；reservation_first/conversion_first 两种锁顺序均不双售；cancel_start 只一终态；repeat_cancel 只一释放事件；source_move 竞争失败保留旧资格。两个边界场景仍用服务器私有时钟缝控制先后，不依赖客户端时间，不表示真实预约/租约联调。

### T01—T14 回归

|TC|本轮结果与证据|下游边界|
|---|---|---|
|T01|PASS：整数/取整/0告警/冻结版本及 production demo 门禁|正式参数批准未发生|
|T02|PASS：共享总额/来源选择，last_capacity 实库竞争|真实预约接入 NOT_RUN|
|T03|PASS：幂等/重复取消/失败迁移保持旧资格及成功迁移|真实预约事务 NOT_RUN|
|T04|PASS：转换截止/重复转换，两种有序并发|真实渠道联调 NOT_RUN|
|T05|PASS：账号/工位/请假冲突；新增无槽 assignment 处置|完整 hr_holidays 审批 NOT_RUN|
|T06|PASS：失效暂停、claim保留；assignment/slot 处理各自去重|真实预约迁移/联系送达 NOT_RUN|
|T07|PASS：权限/原因/加减额保护/延长核查；全部当地表单边界|无生产发布|
|T08|PASS：当地营业日、停接/清队契约/重开/次日新记录|真实队列/00:10 NOT_RUN|
|T09|PASS：最终空库 install46/upgrade44、历史配置、无未来模型|生产迁移 NOT_RUN|
|T10|PASS：取消前后/过期/停接/consume，cancel_start/repeat_cancel|真实租约竞争 NOT_RUN|
|T11|PASS：周视图/批量原子/复制；新增春秋 DST 边界及无效时间|不增加未来业务|
|T12|PASS：我的今日/默认建议/反馈/会话稳定；新增部分能力过滤|S06真实执行/全局位置 NOT_RUN|
|T13|PASS：单店移除/跨法人离职、历史/他店/claim保留|真实患者联系 NOT_RUN|
|T14|PASS：不符草稿与发布核查分离；直接安排建议也过滤|S06实际执行资质 NOT_RUN|

所有原额外模型和 HTTP 用例也重跑，完整方法名见 model-http-final。没有修改已接受的 slot/policy/claim/event/operation/business/disposition 文件；容量动作、取消/consume/改期/重配/转换/营业/离职关键 service 方法 AST 与 d652026 相同，核对见 [preservation.json](evidence/s03-rework/preservation.json)。原31份合同/报告/证据文件逐字节保持。

## 用户效果与可复查证据

本次预览已在截图、账本提取后停止，仅核对并停止本次精确 PID/config 的进程；见 [preview-lifecycle.json](evidence/s03-rework/preview-lifecycle.json)。未停止或重配既有服务。需复查时用最终新库创建记录及 `scripts/s03.py serve` 启动，账号访问材料仅在本机私有 access.json，GitHub不包含密码或会话。

1. writer 打开“排期与容量”，验证原周排期两种视图、批量、容量、营业流程仍可用；reader 无写表单。
2. 部分能力 staff 打开“我的今日”的区域安排建议，仅看到单能力 Chair1；直接安排到双能力 Chair2 时不能获得合格建议。
3. writer 查看“处理记录”：没有槽的未来安排后加请假也有 assignment 待办。带原因处理后仍显示 resolved 历史。
4. 查看只读账本：assignment99 的 disposition34 已 resolved、无 slot；assignment98 的 disposition33 仍 pending。两者保留原因；不是将冲突消失假装为处理完成。
5. 周视图选择纽约 2026-11-02 周，复制上一周；周一00:30和周日23:30都出现，上一周窗口外记录不复制。
6. 排班表单提交纽约 2026-03-08 02:30，明确拒绝；提交 2026-11-01 01:30 也明确拒绝；普通当地09:30保存及重开仍09:30。
7. 容量、取消返还、转换、并发与离职行为查看原测试和本轮全量回归/账本；没有新增 S05 患者预约按钮或 S06 真实坐诊入口。

9张最终截图：[周排期](evidence/s03-rework/browser-attempts/20261011T162212262746/01-weekly-plan.png)、[共享容量](evidence/s03-rework/browser-attempts/20261011T162212262746/02-shared-capacity.png)、[营业日](evidence/s03-rework/browser-attempts/20261011T162212262746/03-business-day.png)、[只读](evidence/s03-rework/browser-attempts/20261011T162212262746/04-readonly-capacity.png)、[我的今日/反馈](evidence/s03-rework/browser-attempts/20261011T162212262746/05-my-today-feedback.png)、[部分能力区域建议](evidence/s03-rework/browser-attempts/20261011T162212262746/06-partial-area-suggestion.png)、[无槽安排处理](evidence/s03-rework/browser-attempts/20261011T162212262746/07-assignment-handling.png)、[DST周复制](evidence/s03-rework/browser-attempts/20261011T162212262746/08-dst-week-copy.png)、[歧义输入拒绝](evidence/s03-rework/browser-attempts/20261011T162212262746/09-dst-input-rejected.png)。06/08/09 已实际查看。仅功能性服务器表单；美化仍属 S13。

## 保留失败链、安全自查与停止边界

原 d652026 的全部6库运行历史、浏览器尝试、失败与补交原样保留在 docs/evidence/s03，原报告不覆写。本轮另存 docs/evidence/s03-rework：首库 `ydental_s03_test_20261011161821_41f1b887` 安装 0 failed / 3 errors / 46，原因是新增 station fixture 未传 S02 必需 ydental_version；仅修测试后固定31d69，在全新第二库全量通过。首库、原日志与日志哈希保留，没有 reset 或把失败摘要改为成功。最初产品222b8d5及测试fdb2e66也保留在当前分支提交链。

安全增量自查：新 helper/处理方法均为私有；GET/compute不写待办；change hook 在原模型 super().write/create 权限检查成功后运行；sudo仅用于服务器内部不变量扫描/记账，不让客户端指定任意人员或门店处理范围。沿用原 S01 session、店内权限、CSRF、revision、记录version和既有锁；无新公开 ORM 写入口、SQL拼接、ACL放宽、外发或动态执行。HTTP重新验证 reader越权、跨店旧页、伪造ORM/CSRF及新增处置拒绝；时间错误整批回滚。保留原 [作者安全自查](s03-security-review.md)。

本轮不修非阻断的重复人工取消历史和 My Today 跨店操作提示；没有借返工扩大业务。未修改核心、既有未提交内容、系统依赖、原生 Status、workflow 或 Issue/PR 状态；未合并、关闭或生产发布。回滚维持原“保留独立分支与隔离库，不卸载历史模块、不删账本”边界。

NOT_RUN 继续包括 S04患者、S05真实预约/现场业务、S06真实队列/坐诊租约/执行资质/00:10、完整请假审批、真实联系送达、生产参数/迁移/发布及S13。下游只有原服务器扩展契约及合成验证。

新证据哈希清单见 [artifact-manifest.json](evidence/s03-rework/artifact-manifest.json)。完成 #27 `[CODEX] S03修正交付与复核申请` 写回并完整读回后停止，Project 保持“返工”，等待 GPT 技术复核，不进入 S04。
