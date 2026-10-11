# 交付验收申请｜YD-N1 R1｜S00｜S00-A

任务：[S00 #24](https://github.com/Yredxin/YDental/issues/24)，总计划[#23](https://github.com/Yredxin/YDental/issues/23)。发起来源：用户在2026-10-11本次会话明确启用S00-A，范围评论[已记录](https://github.com/Yredxin/YDental/issues/24#issuecomment-6106155290)。本报告由Codex提交，不是用户批准或GPT复核。

只交付现状核实、当前入口、工程约定。Project整改受自动化完整读取能力阻塞，**本批不能报全部完成；整个S00未完成**。报告后停止，等待技术复核和用户确认；S00-B/S01及其他阶段未启用。

## 依据、分支与改动

先读GitHub #23、#24当前正文及全部评论：#23为R1、有效需求复审明确非代码/生产验收；#24启用前无评论。正文更新时间分别2026-10-11T06:03:40Z、05:42:54Z；当前索引身份另逐一核对#25—#37，未修改任何Issue正文，也未用撤销任务/四份旧文件/历史计划或验收补规则。正文和评论哈希在evidence/s00-a/summary.json。

初始本地分支codex/p00-baseline，HEAD为5468a14e630833e9b8308dacc0ab7e125b4bb3d9，工作区干净；本地origin缓存陈旧。git ls-remote和fetch核实远端该分支为e9a608ab826b19637eac5b47bce42704ee935544，领先4个文档提交。差异仅AGENTS/README/contracts/reuse，撤下旧规则；据此从远端最新基线建立codex/s00-a-r1-20261011，原本地分支保留。没有把历史功能当当前已验收，没有改默认分支main。

本批改AGENTS.md、README.md、docs/contracts.md；为docs/baseline.md、docs/acceptance.md增加历史提示，原正文保留；新增本报告和脱敏证据。docs/reuse.md撤销说明保留。不改addon、脚本、配置样例、许可证或核心。固定最终commit和远端读回结果由#24同一报告评论给出，避免提交内自引用。

## 实际环境和保护边界

|项目|实际只读结果|边界/影响|
|---|---|---|
|主机|Ubuntu26.04.1 LTS，Linux7.0.0-38-generic|未安装/重配系统|
|odoo-sd|/home/redxin/code/odoo/odoo-sd，无.git；git rev-parse不在仓库|容器工作区父目录，不是Git根|
|核心Git根|/home/redxin/code/odoo/odoo-sd/code，分支20.0|独立于sd-addons；禁止核心写入|
|核心远端/HEAD|https://github.com/Yredxin/odoo.git；f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb|GitHub显示fork源odoo/odoo；本提交无父，为根快照，不能据此证明精确上游提交/API兼容|
|核心工作区|?? AGENTS.md、?? sd-addons/；tracked无修改|父AGENTS是既有未跟踪文件，未改；50463个tracked/受保护文件内容哈希复核无变化|
|自研Git根|核心内sd-addons；远端https://github.com/Yredxin/YDental.git|不是核心分支/副本，不创建重复仓库|
|源码版本声明|odoo/release.py为20.0、Python3.12—3.14、PG最低16|只读源码，不等于Odoo运行验证|
|Python|核心.venv/bin/python 3.12.15；66个已装包；uv pip check退出0|现有requirements.txt及markdown2==2.5.5额外依赖不改；完整当前包清单已保存|
|启动|既有PID42433使用核心.venv/bin/python、odoo-bin -c 核心odoo.conf --logfile .local/log/odoo.log|读取/proc命令行及监听元数据；未启动/停止/登录或请求业务服务|
|HTTP|127.0.0.1:8069监听|保留原服务，不作为本批效果访问步骤|
|当前配置|addons_path=addons；db_name=odoo20_dev；dbfilter=^odoo20_dev$；DB连接127.0.0.1:5432；data_dir=核心.local/share/odoo|没有sd-addons，不能声称牙科入口已在当前服务加载；私有配置内容不公开、不修改|
|PostgreSQL|odoo20-db，postgres:18；实际18.6；持久volume postgresql_odoo20-db-data；unless-stopped|Docker实际暴露0.0.0.0/::的5432，与父AGENTS的仅本机说法不同；记录差异，不重配|
|数据库核查|仅连接维护库postgres，BEGIN READ ONLY读取server_version和pg_catalog.pg_database；退出0|不连接odoo20_dev或任何测试业务库，不查业务表、不CREATE/DROP/安装升级；此为资产元数据，不是业务数据库测试|
|既有库|odoo20_dev OID16388；历史baseline02 OID20083；native OID20084；postgres/template0/template1|名称前缀不等于可操作授权；所有既有库保持|
|历史隔离记录|baseline02/native marker的端点127.0.0.1:5432、OID与目录配置吻合；独立data_dir、精确dbfilter、cron0；HTTP8089/8079|仅静态记录核对，旧baseline目录另有残留；不复用旧库验当前功能、不删目录/失败证据|
|PDF/字体|PATH找不到wkhtmltopdf；fc-list :lang=zh family退出0但无匹配|后续B基础PDF依赖缺口；本批不安装，PDF测试NOT_RUN|
|odoo-12/无关服务|odoo-12原目录保留；Docker列表见odoo12-db映射15432、无关mysql服务|不进入odoo-12，不改/删/重配/停服；其他项目不操作|

入口核对：初始本地AGENTS仍含#1/P00及旧contracts入口；旧contracts还含OCA候选方向。远端最新已撤销这些规则但仍称无新计划。当前分支更新为#23—#37/R1。父核心AGENTS仍有“sd-addons为空”、仅本机DB映射等陈旧环境描述，本批不覆盖用户文件；新仓库入口明确指出差异，停止从其示例推导运行授权。

## 可复用资产与API只读核验

现有唯一自研模块ydental_base（20.0.1.0.0、LGPL-3、depends web），一个顶级菜单、一个URL动作/ydental、auth=user的只读GET页面，源码含内部用户与入口组检查；无新增业务模型/字段。它是候选：当前页面仍含P00及“基线已就绪”文案，manifest/菜单/QWeb含中文源字符串且无i18n/zh_CN.po，不满足当前翻译交付，不能据旧测试认定已验收。

scripts/p00.py只读发现库名白名单、维护库核对OID/端点、创建记录、独立data_dir/config、精确dbfilter和端口保护。它仍是旧P00候选工具，未在本批执行，错误端点拒绝/竞态等须B获启用后实测，不宣称当前安全护栏通过。

|API/用途|实际源码定位（均固定核心commit）|本批结论|
|---|---|---|
|权限模型|[odoo/addons/base/models/ir_access.py:64—66](https://github.com/Yredxin/odoo/blob/f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb/odoo/addons/base/models/ir_access.py#L64)|实际为ir.access，不能盲抄旧权限CSV；未创建ACL/运行鉴权|
|约束/唯一索引|[odoo/orm/table_objects.py:88](https://github.com/Yredxin/odoo/blob/f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb/odoo/orm/table_objects.py#L88)、221|Constraint/UniqueIndex定义存在；并发唯一未测|
|翻译|[odoo/orm/environments.py:344](https://github.com/Yredxin/odoo/blob/f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb/odoo/orm/environments.py#L344)|env._定义存在；未导出/安装翻译|
|日期/时间|[odoo/orm/fields_temporal.py:141](https://github.com/Yredxin/odoo/blob/f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb/odoo/orm/fields_temporal.py#L141)、226|context_today/context_timestamp取env时区；业务需显式门店上下文|
|PDF分层|[odoo/addons/base/models/ir_actions_report.py:788](https://github.com/Yredxin/odoo/blob/f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb/odoo/addons/base/models/ir_actions_report.py#L788)、817；[addons/base_report_wkhtmltox/__manifest__.py](https://github.com/Yredxin/odoo/blob/f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb/addons/base_report_wkhtmltox/__manifest__.py#L1)及models/ir_actions_report.py:489|实际为引擎分层，wkhtmltox实现需二进制；未运行或安装|

API表是静态源码证据，不是Odoo模型测试。精确上游来源比对与当前底座运行兼容性尚未实测，不静默更换版本。

## 需求完成情况

|R/条款|完成/部分/未做|位置与原因|
|---|---|---|
|R01 / #24 A|完成只读核实|本报告、summary环境/保护证据；不包括安装兼容|
|#24 B|仅候选评估|现有应用入口可评估，代码/翻译/运行待B|
|#24 D/E|部分，BLOCKED|完整条目/字段/视图及自动化元数据已读；配置详情不可读，停止看板写入；旧22项尚未归档|
|#24 F—I|完成本批契约发布|docs/contracts.md；业务实现/实测及用户确认仍未做|
|#24 C及S00-B|未做，NOT_RUN|未获启用；不新建库、不安装升级/授权登录/PDF/并发测试|
|备份资源|完成资源需求登记|本批无持续备份/恢复部署或测试，不声称S13完成|

## Project前后核对

Project #4实际id PVT_kwHOA3_tu84BmcLJ，viewerCanUpdate=true；账号Yredxin有仓库admin/push能力，但完整自动化配置无可用读取通道。已读取37条items（含归档标记/类型/仓库/每项全部fieldValues）、19字段、5视图、7自动化；各层pageInfo.hasNextPage=false，无漏页。所有37张当前均未归档，旧22个实体由当前标题“已撤销”或“原计划已撤销”的历史PR确认，**没有按Closed一概归档**，没有读取旧业务需求补规则。无无关卡片，未动任何其他Project。

表1：Issue/PR→Project item，前后id不变。

|Issue/PR|Project item ID|身份核对|
|---|---|---|
|#1|PVTI_lAHOA3_tu84BmcLJzg_1od4|已撤销旧项|
|#2|PVTI_lAHOA3_tu84BmcLJzg_1oyo|已撤销旧项|
|#3|PVTI_lAHOA3_tu84BmcLJzg_1o6Y|已撤销旧项|
|#4|PVTI_lAHOA3_tu84BmcLJzg_1pFE|已撤销旧项|
|#5|PVTI_lAHOA3_tu84BmcLJzg_1pSY|已撤销旧项|
|#6|PVTI_lAHOA3_tu84BmcLJzg_1pgY|已撤销旧项|
|#7|PVTI_lAHOA3_tu84BmcLJzg_1pxw|已撤销旧项|
|#8|PVTI_lAHOA3_tu84BmcLJzg_1p8A|已撤销旧项|
|#9|PVTI_lAHOA3_tu84BmcLJzg_1qG4|已撤销旧项|
|#10|PVTI_lAHOA3_tu84BmcLJzg_1qOk|已撤销旧项|
|#11|PVTI_lAHOA3_tu84BmcLJzg_1qbg|已撤销旧项|
|#12|PVTI_lAHOA3_tu84BmcLJzg_1qig|已撤销旧项|
|PR13|PVTI_lAHOA3_tu84BmcLJzg_15as|旧计划历史PR|
|#14|PVTI_lAHOA3_tu84BmcLJzg_8SXc|已撤销旧项|
|#15|PVTI_lAHOA3_tu84BmcLJzg_8Stc|已撤销旧项|
|#16|PVTI_lAHOA3_tu84BmcLJzg_8WZ4|已撤销旧项|
|#17|PVTI_lAHOA3_tu84BmcLJzg_8Wls|已撤销旧项|
|#18|PVTI_lAHOA3_tu84BmcLJzg_8Wyc|已撤销旧项|
|#19|PVTI_lAHOA3_tu84BmcLJzg_8XJw|已撤销旧项|
|#20|PVTI_lAHOA3_tu84BmcLJzg_8XbA|已撤销旧项|
|#21|PVTI_lAHOA3_tu84BmcLJzg_8Xio|已撤销旧项|
|#22|PVTI_lAHOA3_tu84BmcLJzg_8Xxw|已撤销旧项|
|#23|PVTI_lAHOA3_tu84BmcLJzg_8ibQ|当前总计划|
|#24|PVTI_lAHOA3_tu84BmcLJzg_8jDA|当前阶段|
|#25|PVTI_lAHOA3_tu84BmcLJzg_8jnU|当前阶段|
|#26|PVTI_lAHOA3_tu84BmcLJzg_8kWQ|当前阶段|
|#27|PVTI_lAHOA3_tu84BmcLJzg_8kos|当前阶段|
|#28|PVTI_lAHOA3_tu84BmcLJzg_8k7M|当前阶段|
|#29|PVTI_lAHOA3_tu84BmcLJzg_8lIQ|当前阶段|
|#30|PVTI_lAHOA3_tu84BmcLJzg_8ln0|当前阶段|
|#31|PVTI_lAHOA3_tu84BmcLJzg_8l6I|当前阶段|
|#32|PVTI_lAHOA3_tu84BmcLJzg_8mLM|当前阶段|
|#33|PVTI_lAHOA3_tu84BmcLJzg_8mdA|当前阶段|
|#34|PVTI_lAHOA3_tu84BmcLJzg_8mwI|当前阶段|
|#35|PVTI_lAHOA3_tu84BmcLJzg_8nCU|当前阶段|
|#36|PVTI_lAHOA3_tu84BmcLJzg_8nQw|当前阶段|
|#37|PVTI_lAHOA3_tu84BmcLJzg_8nno|当前阶段|

表2：阶段/执行状态，未把标题推定字段冒充已配置。物理Status仍为Todo；本批无状态写入。

|Issue|阶段来源|写前→读回/二次核对物理Status|实际授权/进度|
|---|---|---|---|
|#24|S00（由当前标题核对，非已有阶段字段）|Todo → Todo|仅S00-A获启用；报告后待技术复核，Project受阻；B未启用|
|#25|S01（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#26|S02（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#27|S03（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#28|S04（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#29|S05（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#30|S06（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#31|S07（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#32|S08（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#33|S09（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#34|S10（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#35|S11（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#36|S12（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|
|#37|S13（由当前标题核对，非已有阶段字段）|Todo → Todo|未启用，无开工/验收声明|

表3：操作/读回/第二次核对。

|时点|总数/当前阶段/重复|旧实体未归档|字段/视图/自动化|实际操作与结果|
|---|---|---|---|---|
|写前|37 / 14 / 0|22|19 / 5 / 7|全分页读取；总计划另有1卡|
|读回，06:19:31 UTC|37 / 14 / 0|22|19 / 5 / 7|与写前对象全量相等；Project写入0|
|二次只读核对，06:19:33 UTC|37 / 14 / 0|22|19 / 5 / 7|与写前全量相等；同步mutation因前置受阻NOT_RUN|

这是受阻后的两次只读核对，**不是“同步两次成功”或幂等写入验收**；T05仍BLOCKED。旧Issue状态保持Closed，历史PR保持Open/draft/auto_merge=null，当前#23—#37保持Open，没有关闭#24。

字段全表：

|字段|类型|选项/处理|
|---|---|---|
|Title|TITLE|保留|
|Assignees|ASSIGNEES|保留|
|Status|SINGLE_SELECT|Todo, In progress, Done|
|Labels|LABELS|保留|
|Linked pull requests|LINKED_PULL_REQUESTS|保留|
|Milestone|MILESTONE|保留|
|Repository|REPOSITORY|保留|
|Reviewers|REVIEWERS|保留|
|Parent issue|PARENT_ISSUE|保留|
|Sub-issues progress|SUB_ISSUES_PROGRESS|保留|
|Created|CREATED|保留|
|Updated|UPDATED|保留|
|Closed|CLOSED|保留|
|Priority|SINGLE_SELECT|P0, P1, P2|
|Size|SINGLE_SELECT|XS, S, M, L, XL|
|Estimate|NUMBER|保留|
|Iteration|ITERATION|3个当前iteration，已读取日期/周期，未调整|
|Start date|DATE|保留|
|Target date|DATE|保留|

视图：Backlog/TABLE无filter；Board/BOARD无filter；Current iteration/BOARD为iteration:@current；Roadmap/ROADMAP无filter；My items/TABLE为assignee:@me。未改名称、筛选或布局。当前无阶段字段，无待复核等中文执行状态；#24建议的阶段/七态仍未物理配置，不将Todo直接等同用户已启用。

自动化全量元数据：

|编号|名称|写前→读回enabled|配置核验|
|---|---|---|---|
|10|Auto-add sub-issues to project|true → true|条件/动作配置API未暴露；未修改|
|13|Auto-add to project|true → true|条件/动作配置API未暴露；未修改|
|9|Auto-close issue|true → true|条件/动作配置API未暴露；未修改|
|12|Item added to project|true → true|条件/动作配置API未暴露；未修改|
|7|Item closed|true → true|条件/动作配置API未暴露；未修改|
|11|Pull request linked to issue|true → true|条件/动作配置API未暴露；未修改|
|8|Pull request merged|true → true|条件/动作配置API未暴露；未修改|

BLOCKED原因：实际GraphQL ProjectV2Workflow schema仅暴露id/name/number/enabled/createdAt/updatedAt/project等元数据，不暴露触发条件、筛选和动作目标；当前没有已认证浏览器/UI工具。无法确认Auto-close触发状态、Auto-add筛选范围等。用户要求完整读自动化后才整理Project，安全前置未满足，故停止所有Project mutation，不删除工作流绕过，不尝试设Done。GitHub官方[workflow schema](https://docs.github.com/en/graphql/reference/projects#projectv2workflow)与[内置自动化说明](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations)支持此能力边界；自动关单可随状态变更触发，不能仅凭名称推断安全配置。

仓库Actions工作流列表total_count=0；保留历史PR无auto_merge。未启用自动开发/自动合并，没有创建新PR或改旧PR。也不能据这些结果宣称已审尽账号外部后台集成。

## 当前工程约定、模板与未决配置

完整文本在docs/contracts.md，来源只为#23/#24当前条款：

- 命名：ydental命名空间；模块/新增字段/XML局部名ydental_，模型ydental.。实际模块ydental_base、入口组/动作/菜单保留；baseline_page/user_demo例外登记，不机械改名/重授权。当前无自研业务模型或字段。
- 依赖：原生+自研，不引OCA；当前ydental_base→web。低层不探测未来模型，上层依赖/继承真实扩展点，钩子登记输入/输出/权限/事务；模型层鉴权和受控派生，不拿菜单隐藏或readonly替代。
- 翻译/时间/精度：英文静态源字符串+每模块zh_CN；naive UTC存时间戳，门店IANA时区决定显示和业务日，补录双时间；币种舍入和UoM精度，不固定两位或门店码长度。当前翻译缺口已记，未批准生产时区/币种。
- 编号：患者号集团唯一；业务单据门店归属和稳定内部ID；叫号显示号门店+报到区域+业务日唯一。原子序列/数据库约束，不用max+1；跨日/并发防重，历史单据不随更名重编号。
- 字典模板栏目：技术名/说明、原生映射、类型/关系/单位/精度、必填/默认、来源/可信入口、归属、读写导出/敏感级别、唯一约束、状态/版本/历史快照、删除更正迁移、Issue/TC/commit。
- 动作模板栏目：入口/版本、输入/幂等/来源、前置状态/版本、权限门店会话、锁约束/原子变更、输出、费库款/队列/文书副作用、审计外发、重复/失败、恢复入口/负责人/重试、TC/commit。稳定区分hint_only/accepted/already_accepted/append_required/handover_required/access_denied/insufficient_balance/version_conflict，并补outcome_unknown。只查提示、受理、送达和真实执行分开，失败不留半笔，恢复补原事件，不管理员强抢。
- 删除/证据：普通操作不得物理删业务单据和确认记录；作废/更正留原因和来源。长期保留脱敏验收、可重复测试、失败补交链；临时垃圾清理不能删失败证据。S01才实现审计，S00仅契约。
- 备份：每天DB+filestore/PDF全备、至少30天恢复链、异机、季度演练与RPO≤15分钟/RTO≤4小时同时满足；需资产量/增长/WAL/压缩实测/30天依赖链/异机带宽容量/隔离恢复资源/密钥托管/负责人和告警。不虚填GB，不将日全备等同15分钟RPO。

契约只是本批工程发布，生产参数仍按#23第3.2节和责任阶段提供方案并由用户确认：门店时区/门店码、实际币种税/票种、取价锁价、真实临床文书签发、心跳/超时/过号、权限模板/店长任免、通道与设备、门店规模及备份地点容量。已定00:00/00:10、1:2、50会话、RPO/RTO和周期不重新泛化待定。

## 流程实际回放与测试结果

|示例|前提/操作|预期|实际|证据|
|---|---|---|---|---|
|S00-F1本批|读GitHub、核实双Git根、保留改动、核对Project|实际路径/分支准确，当前索引14卡，旧项退出执行视图|路径与14卡核对完成；旧项退出因自动化详情BLOCKED|本报告及project三快照|
|S00-F2|需B授权和全新隔离库|安装/升级/普通与无权/PDF|NOT_RUN|无运行样张，不借旧证据|
|S00-F3|翻译/门店日期/并发编号|跨日期正确、内部码与旧编号稳定|NOT_RUN；只做纯stdlib文字时间换算|2026-10-10T16:30Z→合成Asia/Shanghai 2026-10-11T00:30；不是生产选择或Odoo测试|

|TC|结果|命令/角色|测试数/退出码与限制|
|---|---|---|---|
|S00-T01|PASS（本批只读保护）|git status/rev-parse/remote/log；保护哈希比对；本机redxin|50463文件内容不变，核查退出0；核心未跟踪文件保留，addon初始无未提交改动|
|S00-T02|NOT_RUN|未安装升级|Odoo测试0；退出码N/A|
|S00-T03|NOT_RUN|未进行授权/无权/匿名登录|0；N/A，不复用旧HttpCase PASS|
|S00-T04|NOT_RUN|未生成或访问PDF|0；N/A；wkhtmltopdf PATH查询退出1，中文字体查询退出0无匹配|
|S00-T05|BLOCKED|gh api graphql；Yredxin|37项/19字段/5视图/7自动化元数据、两次只读核对退出0；mutation0，幂等同步测试未运行|
|S00-T06|NOT_RUN|未执行错误端点/非隔离库拒绝测试|0；N/A；仅读旧工具实现，未认定护栏通过|
|S00-T07|PASS（核实/报告差异部分）|源码release/HEAD/来源、配置白名单、Docker元数据|静态核实退出0；发现差异不改版本；安装兼容测试仍NOT_RUN|
|S00-T08|NOT_RUN|未运行翻译/业务日期/并发编号工具|0；N/A；契约与纯时间算例不代替业务实测|
|S00-T09|PASS（契约文档检查）|命名清单、字典/动作/错误恢复/删除保护、git diff --check、文档检查|静态栏目齐全；不宣称实现审计/业务保护，Odoo测试0|

实际命令、当前依赖包、脱敏输出与退出码在summary.json。uv pip check退出0，66包兼容仅表示Python依赖元数据一致，不是Odoo用例通过。只读维护库catalog查询退出0不是业务DB测试。定位时个别猜测路径不存在（rg退出2）已改查实际base_report_wkhtmltox/orm路径，不把搜索失败计为测试通过；未删失败验收证据。最终文档与保护检查结果在checks.json。

## 用户效果验证（文档复核，非运行验收）

角色为有仓库/Project读取权的技术复核者，不提供凭据。按#24报告中的固定commit完成：

1. 打开README：仅当前#23和#24—#37索引，不出现旧计划继续执行入口。
2. 打开AGENTS：确认只启用S00-A、保护范围及停止点。
3. 打开本报告环境表和summary：核对双Git根、具体HEAD、配置与映射差异。
4. 对照Project三快照和三表：14阶段各1卡；22旧实体仍未归档，状态未改，BLOCKED明确。
5. 打开contracts：核对现有标识例外、依赖边界、字典/动作/恢复栏目、生产待发布项。
6. 对照测试表：未执行安装/运行/PDF/数据库用例均NOT_RUN，没有样张/截图/录像或业务登录成功声明。
7. 技术复核在#24写范围/commit/通过或返工/证据不足；之后由用户明确确认。本文不代做这两步。

## 数据、审计、回滚和阻塞

本批只有文档，无业务数据变更或迁移，不改费库款/历史PDF；没有新增审计服务。本次协作留Git分支/commit、启用评论和本报告；不把这称为业务审计实现。

回滚本批可在工作分支revert本批文档提交，保留历史证据，不reset/强推，不涉及数据库恢复、核心或配置变更。Project未写，无需Project回滚。原本地codex/p00-baseline和远端旧PR保留。

|阻塞/条件|影响|下一批所需|
|---|---|---|
|BLOCKED：自动化触发/条件/动作详情不可读|Project整理、状态字段/视图实施、T05二次同步幂等验收未完成|提供可认证的Project工作流配置读取/管理通道；先完整读取7项配置，确认Auto-close及Auto-add安全边界，再仅归档确认旧22实体、保留14阶段唯一卡/真实进度，读回并二次同步|
|仅有fork根快照来源声明|不能证明精确官方上游对应/运行兼容|B前继续明确底座来源证据和支持的实际API，不静默升级核心|
|PDF二进制/中文字体缺口|B的基础PDF目前无真实证据|B获明确启用后准备具体依赖方案，按授权处理；本批不系统安装|
|现有页面中文源字符串/P00文案、无zh_CN|当前翻译/入口体验未验收|B获启用后在addon工作分支修复并真实安装升级/正负权限/PDF验证|
|B运行隔离与真实生产参数|本批不批准运行/生产|用户明确启用B；全新允许范围库/固定端点/独立运行资源，错误端点拒绝实测；未发布参数继续在责任阶段确认|
|备份资源未发布/机制未部署|S13实际持续备份和恢复仍未完成|资源清单、负责人、异机容量/带宽/密钥、恢复机和告警；S13实测，不由S00-A宣布达标|

## 复核申请和停止

申请对本批固定commit的文档/只读证据作技术复核，并请用户确认实际范围。Project整改仍BLOCKED，不申请整个S00完成，不关闭#24、不合并PR、不自动进入B/S01、不发布生产。报告写回后停止。
