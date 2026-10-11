# [CODEX] S00-T05 / Project #4 最小安全整理固定交付与复核申请

任务：YD-N1 R1 / [#24](https://github.com/Yredxin/YDental/issues/24) / S00-T05。用户本次明确启用，唯一执行边界为当前[#23](https://github.com/Yredxin/YDental/issues/23)、#24正文及最新[GPT-DECISION 6107161042](https://github.com/Yredxin/YDental/issues/24#issuecomment-6107161042)。本轮完整重新获取正文及全部评论，随后再次读取确认#23有1条、#24有15条；来源时间、正文与评论哈希见[issue-source-index.json](evidence/s00-t05-minimal/issue-source-index.json)。旧浏览器登录/自动化内部详情前置已由该决定撤销；没有要求用户登录GitHub或截图。

**结论：S00-T05本次最小安全整理实测PASS，当前计划视图也PASS；申请GPT技术复核和用户效果确认，不宣称整个S00完成。** 第一轮56条Project mutation逐条立即完整读回，第二轮同一同步函数真实执行、0 mutation；20项证据断言全部通过。安装、升级、HTTP、PDF、隔离及浏览器S00-A/B证据未重测、未改结论；S01未启用。

## 版本、环境与保护边界

- 实际仓库`/home/redxin/code/odoo/odoo-sd/code/sd-addons`，独立Git根，origin为`https://github.com/Yredxin/YDental.git`；接续基线`fa60549200c1140591fb43096bd9b7c250d13cec`，开工工作区干净。分支`codex/s00-t05-project-r1-20261011`；未切默认分支、reset或覆盖既有改动。
- 两轮同步被测固定提交：`e8f3ec76276682c9ef8623bfc1f08cb5b17117c6`；只读证据验证被测提交：`321962f9203cc8960f317685c11ce3c3241d3923`。最终固定交付提交由#24同名评论给出，本报告、脚本和证据随该提交固定；后续只补报告/证据，不改被测同步脚本。
- 既有认证gh CLI 2.102.0，API viewer=Yredxin；Python用核心既有`.venv/bin/python`，3.12.15。没有读取、导出或发布token/cookie/密码，没有浏览器认证、安全配置或系统依赖变更。
- 操作目标严格固定`PVT_kwHOA3_tu84BmcLJ` / [Yredxin Project #4](https://github.com/users/Yredxin/projects/4)。不改Odoo核心、odoo-12、addon、数据库、服务或业务需求；不创建/关闭Issue，不修改PR，不修改任何workflow及原生Status。
- 旧阻塞报告与证据完整保留于[s00-t05-report.md](s00-t05-report.md)及原证据目录。本轮使用独立`docs/evidence/s00-t05-minimal/`，没有覆盖旧快照。

## 需求完成情况

|范围|结果|实际完成与位置|
|---|---|---|
|R01 / #24 D-E / S00-T05最小安全整理|PASS|22张历史卡归档、15张当前卡唯一、两个自定义字段及值、当前计划视图、两轮同步与完整读回|
|金丝雀与逐步保护|PASS|先仅归档Issue #1，CLOSED/评论数0不变；#23—37、Status及workflow元数据不变；之后每张归档/每条字段及视图写入均单独读回|
|当前计划视图|PASS|新增“当前计划”表格视图#6，显示Title/阶段/执行状态；精确保存筛选，服务端实际只返回#23—37|
|自动化元数据及保护|PASS，限API可读部分|7项enabled均true、ID/名称/时间戳前后及第二轮一致；workflow mutation=0|
|workflow内部trigger/filter/action/target|BLOCKED/未知|API未暴露；按最新DECISION不再是本轮整理前置，不把元数据一致冒充内部配置核验|
|浏览器登录GitHub及UI截图|NOT_RUN|本轮不再要求；用真实API读回证据，不制作或复用截图冒充本轮UI验证|
|S00-A/B及浏览器补证、S01及后续|NOT_RUN|前者已技术复核不重做，后者未启用|

## 流程实际回放与两轮同步

|时点UTC|真实操作|结果/退出码|
|---|---|---|
|08:59:57—09:04:07|第一轮：写前完整读取→#1金丝雀→其余21张逐张归档→2字段→15卡各2字段值→创建视图→筛选→最终完整读回|PASS，56 mutation / exit0|
|09:04:13—09:04:23|第二轮：再次完整读取→执行同一个`Sync.sync()`目标状态逻辑→完整第二次读回|PASS，0 mutation / exit0|
|09:04:29|只读证据验证与服务端实际筛选查询|20/20断言PASS / exit0；查询返回15项，#23—37，无历史卡|

两轮均使用同一份同步脚本和同一被测commit，第二轮不是两次空读取的替代。第二轮0重复item、0重复字段、0重复选项、0额外归档、0非预期状态变化；after与second-check完整语义对象相同（仅忽略连接顺序/分页游标）。本轮同步与最终筛选验证合计117次真实API调用：61 query、56 mutation，全部exit0。更早只读能力探测的失败另存，不计入成功调用数。

写前37 items / 19 fields / 5 views / 7 workflows；写后及第二轮37 / 21 / 6 / 7，其中22 archived、15 active。items明确同时读取ARCHIVED和NOT_ARCHIVED；所有根连接、逐卡fieldValues及各视图fields均检查完整性，未丢掉归档卡来制造数量一致。

固定快照：[project-before.json](evidence/s00-t05-minimal/project-before.json)、[project-after.json](evidence/s00-t05-minimal/project-after.json)、[project-second-check.json](evidence/s00-t05-minimal/project-second-check.json)。全操作/输入/时间/退出码见[operation-log.json](evidence/s00-t05-minimal/operation-log.json)，每条mutation的目标与立即完整读回链接见[mutation-table.md](evidence/s00-t05-minimal/mutation-table.md)；56份`check-NNN.json`保留逐步证据。

|Mutation|条数|精确对象/允许副作用|
|---|---:|---|
|archiveProjectV2Item|22|Issues #1—12、#14—22及PR #13，仅Project item archive|
|createProjectV2Field|2|阶段、执行状态；创建前按名称、类型及唯一选项核对|
|updateProjectV2ItemFieldValue|30|#23—37逐卡阶段与执行状态；只写两个新字段ID|
|createProjectV2View|1|仅新增“当前计划”，原5视图不覆盖|
|updateProjectV2View|1|仅新视图#6的filter|

## 字段、状态与三次身份读回

字段定义及ID/选项颜色/说明固定于[field-definition.json](evidence/s00-t05-minimal/field-definition.json)。阶段为`PLAN,S00—S13`，15个唯一选项；执行状态为`待启用、进行中、待复核、待用户验收、返工、阻塞、已验收`，7个唯一选项。阶段ID`PVTSSF_lAHOA3_tu84BmcLJzhlLbVk`，执行状态ID`PVTSSF_lAHOA3_tu84BmcLJzhlLbVo`。

#23选PLAN，明确其为总计划而不是重复S00阶段；执行状态进行中表示总计划当前只有获启用S00在推进，不授权其他阶段。#24为S00/待复核，表示本次专项已执行、提交复核，未写已验收。#25—37为S01—S13/待启用。没有新增/删除/重复Project item，也没有把历史CLOSED当作归档授权；历史身份来自本次明确允许清单。

原生Status字段ID`PVTSSF_lAHOA3_tu84BmcLJzhlFOho`及三个选项完整不变：Todo=`f75ad846`，In progress=`47fc9ee4`，Done=`98236657`；颜色/说明也未变。21张历史Issue均CLOSED/Done；PR13仍OPEN/draft=true/merged=false/autoMergeRequest=null/Status Todo；#23—37均OPEN/Status Todo。原生Status只用于保护差异检查，不参与执行状态推导或同步写入。

三次身份、Project item ID、archive、阶段/执行状态、实体state、原生Status、评论数详表见[identity-table.md](evidence/s00-t05-minimal/identity-table.md)。所有实体内容选择项及评论计数/最后评论ID前后均一致；不存在同步产生的新评论或关闭/重开/合并。快照中的#24评论数15不包括交付结束后本次按要求发布的报告评论。

## 视图与自动化

新增[当前计划视图#6](https://github.com/users/Yredxin/projects/4/views/6)，ID`PVTV_lAHOA3_tu84BmcLJzgMAjcw`，TABLE_LAYOUT，可见列仅Title/阶段/执行状态。filter为：

```text
repo:Yredxin/YDental is:issue 阶段:PLAN,S00,S01,S02,S03,S04,S05,S06,S07,S08,S09,S10,S11,S12,S13
```

GitHub[单选字段官方筛选规则](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-single-select-fields)支持逗号分隔多个选项；本轮进一步使用保存后的同一filter调用服务端`items(query:...)`，实际返回且仅返回#23—37，证据[view-filter-readback.json](evidence/s00-t05-minimal/view-filter-readback.json)。历史卡无自定义阶段且已归档。该视图不会自动添加或启用未来任务。

原Backlog、Board、Current iteration、Roadmap、My items五个视图的ID/name/layout/filter/可见field IDs均前后一致；19个既有字段定义不变。

|Workflow编号|名称|enabled前→后→第二轮|
|---|---|---|
|10|Auto-add sub-issues to project|true→true→true|
|13|Auto-add to project|true→true→true|
|9|Auto-close issue|true→true→true|
|12|Item added to project|true→true→true|
|7|Item closed|true→true→true|
|11|Pull request linked to issue|true→true→true|
|8|Pull request merged|true→true→true|

完整元数据前后及第二轮见[workflow-metadata-before-after.json](evidence/s00-t05-minimal/workflow-metadata-before-after.json)。内部trigger/filter/action/target仍未知；没有修改、关闭或新建workflow，没有依赖其名字猜测安全结果。实测保护依据是每步完整预期差异与实体状态核对。

只读能力探测中，`view.configuration.visibleFields`触发GitHub服务端内部错误，CLI exit1，操作/时间/错误保存在[preflight-query-rejected.json](evidence/s00-t05-minimal/preflight-query-rejected.json)及[view-read-diagnostics.json](evidence/s00-t05-minimal/view-read-diagnostics.json)。拆分定位后改为现有`view.fields`只读接口，读取及后续真实视图创建、字段配置和筛选写入/读回全部成功；没有扩大权限、换凭据或改安全策略。实际mutation输入schema见[mutation-input-schema.json](evidence/s00-t05-minimal/mutation-input-schema.json)。这段失败证据保留，不覆盖最终视图PASS，也不假报原查询PASS。

## 测试结果及动作保护

|TC/检查|结论|命令/角色|实际数量/退出码|证据|
|---|---|---|---|---|
|S00-T05第一轮|PASS|`../.venv/bin/python scripts/s00_t05_sync.py --round first`；既有Yredxin API身份|1轮；56写入逐条读回；exit0|[sync-first.json](evidence/s00-t05-minimal/sync-first.json)|
|S00-T05第二轮|PASS|同脚本`--round second`，同身份/被测commit|1轮；0写入；exit0|[sync-second.json](evidence/s00-t05-minimal/sync-second.json)|
|完整证据/保护断言|PASS|`../.venv/bin/python scripts/s00_t05_verify.py`，只读|20/20；exit0|[verification.json](evidence/s00-t05-minimal/verification.json)|
|本地写入护栏单元检查|PASS|`../.venv/bin/python -m unittest discover -s scripts -p test_s00_t05_sync.py -v`，无网络mutation|6/6；exit0|[execution-summary.json](evidence/s00-t05-minimal/execution-summary.json)|
|workflow内部配置|BLOCKED/未知|当前API能力边界；不要求浏览器登录|0项完整内部配置|workflow元数据证据注明未知|
|S00其他TC|NOT_RUN|本轮仅专项T05；既有结论保留|未重测|原S00-A/B报告及技术复核|

单元检查只验证拒绝重复字段/选项、识别实体/Status/workflow变化、第二轮禁止写入，以及非预期读回后停止；不冒充真实Project同步。真实运行断言覆盖22历史卡、15唯一当前卡、全部值、所有既有字段/视图、37实体及原生Status、7 workflows、金丝雀、逐写读回和两轮幂等。

同步脚本无任意mutation命令入口，无实体修改、原生Status写入、workflow修改、item新增/删除或数据库操作。请求写前先落operation log；失败或非预期差异立即停止，不自动重试未知结果或自动修复。每次成功写入后先完整读回、只允许本条预期差异，再继续。运行版本/哈希、环境、计数详见execution-summary.json。

## 用户效果验证

1. 打开[Project #4](https://github.com/users/Yredxin/projects/4)，选择“当前计划”视图#6；应有15张当前计划卡。
2. 查看三列Title、阶段、执行状态；#23应为PLAN/进行中。
3. 查看#24：S00/待复核，Issue仍OPEN；这是复核申请，不是用户已验收。
4. 查看#25—37：S01—S13，执行状态全部待启用；卡片出现不授权开工。
5. 在Project归档项中查#1—12、#14—22及PR13：22张卡已归档；打开原实体，旧Issue仍CLOSED，PR13仍OPEN且draft。
6. 原有5个视图仍存在；原生Status选项及7个workflow保持原样。以自定义执行状态判断当前进度。

不要求用户登录服务器、搬运报告或提供截图；查看GitHub本身使用用户正常权限。本轮无浏览器截图，API结果及完整快照是自动验证证据。

## 数据、审计、回滚与复核申请

仅Project元数据变化：22归档、2字段、30字段值、1新视图及其filter。无业务数据/费用/库存/资金/PDF/签名变化，未修改Issue正文/状态、PR或现有workflow。#24报告评论及本分支Git提交/推送属于用户明确要求的交付动作。

没有执行回滚。若需回退，由用户另行确认具体范围后，先重新读取实时Project并比对本轮快照，再按operation-log逆序撤销本轮新增视图/自定义值和字段、取消指定22卡的archive；删除新字段会影响其后其他人的使用，须先核实引用，不触碰原生Status/workflows/Issue/PR状态。不自动回滚、不删除旧失败证据；脚本/文档代码可在本分支使用revert。历史归档为可恢复的Project显示调整，历史实体均保留。

未解决事项：workflow内部配置仍不可读取，已按最新DECISION明确接受为本轮能力边界；不需要再安排Ubuntu浏览器登录。当前计划视图实际PASS，无遗留整理阻塞。请求GPT复核上述固定提交/证据及用户确认Project效果；不替用户验收、不关闭#24、不修改PR、不进入S01。#24写回并读回确认后停止。
