# [CODEX] S00-T05 / Project #4固定交付与复核申请

任务：YD-N1 R1 / [#24](https://github.com/Yredxin/YDental/issues/24) 的Project专项；依据[总计划#23](https://github.com/Yredxin/YDental/issues/23)、#24当前正文与[最新GPT-NEXT专项边界](https://github.com/Yredxin/YDental/issues/24#issuecomment-6107029151)，用户本次明确启用。于2026-10-11重新获取两单正文及全部评论：#23有1条、#24有11条，最新边界为6107029151；来源索引见[issue-source-index.json](evidence/s00-t05/issue-source-index.json)。不使用旧业务正文补规则。

**结论：S00-T05仍BLOCKED，Project mutation为0。** 本轮新实测确认：CLI认证/Project读取有效、全分页现状已固定；官方可用API schema仍无workflow条件/动作；真实Firefox可运行，但本批正常浏览器profile尚未登录GitHub。需用户在专用浏览器完成一次正常网页登录/二次验证。不是沿用旧“无浏览器”结论，也不是将S00-A/B重做。

## 版本与保护边界

- 接续基线：`2d352f4d2f84a23bb56c277e03e8f10a0d6d123e`，原S00-B分支工作区干净；新分支`codex/s00-t05-project-r1-20261011`，不改默认分支。
- 快照脚本首次执行版本：`3e19e470fb92bf509b18f75252f2c64e8c98b332`（完整SHA在before.code_commit）；浏览器及后两次快照执行版本：`4d9ed4f5aac55717051f51285fd0476e23a87860`。最终固定交付SHA在#24同名报告评论；最终提交仅文档、批次说明与脱敏证据。
- 核心/odoo-12、addon、业务库、配置/服务及S00-A/B运行证据均未修改或重测。无PR创建/合并、Issue关闭、Project写入或S01开发。
- 既有gh CLI 2.102.0正常认证为Yredxin；不读取/打印/export认证token。浏览器使用本仓库忽略目录下0700专用profile；不抓取/导出/注入cookie或CLI token，不关闭sandbox及主机安全控制。

## 完成与未完成

|范围|本轮结果|实际完成/未做原因|
|---|---|---|
|写前现状与全分页读取|PASS|37 items、19 fields及选项、5 views及filter/layout、7 workflows元数据；37项fieldValues均完整，所有根连接hasNextPage=false|
|身份与真实状态核对|PASS|#23总计划、#24—37共14阶段各1卡；#1—12、#14—22及PR13共22历史项身份明确；0重复、0无关项；全部isArchived=false|
|API能力重新核验|PASS，限能力定位|ProjectV2Workflow现有8字段无trigger/filter/action；fields/views创建更新mutation确实存在，但前置不满足故未执行|
|自动化详情|BLOCKED|7项都enabled=true；触发、条件、动作字段及目标值均未知，未据名字猜测|
|真实浏览器读取配置|BLOCKED|Firefox155/Playwright1.63正常启动；未认证配置请求404、登录页200；需要正常登录/2FA|
|历史项归档|BLOCKED|未满足自动化安全前置，0归档/删除|
|阶段/执行状态字段|BLOCKED|当前均不存在，未创建或用Status冒充；原生Status保留|
|当前计划视图|BLOCKED|当前不存在；5个原视图未改/删|
|workflow修改|NOT_RUN|无详情不能判干扰，0禁用/删除/修改|
|第一次/第二次同步|NOT_RUN|不是两个“空操作同步”；有两次独立只读回查，不能替代幂等mutation验收|

## 写前与两次只读回查

|时点UTC|items / fields / views / workflows|实际操作与退出码|对比|
|---|---|---|---|
|08:18:50—08:18:58|37 / 19 / 5 / 7|写前全分页读取，exit0|Project完整对象基线|
|08:20:47—08:20:54|37 / 19 / 5 / 7|阻塞后首次完整只读回查，exit0|与本轮写前对象完全相等|
|08:20:54—08:20:59|37 / 19 / 5 / 7|第二次完整只读回查，exit0|与第一次及写前完全相等|

本轮15个Project GraphQL查询全部exit0。未执行Project mutation，故不能称“两次同步成功”。证据：[project-before.json](evidence/s00-t05/project-before.json)、[project-after.json](evidence/s00-t05/project-after.json)、[project-second-check.json](evidence/s00-t05/project-second-check.json)、[operation-log.json](evidence/s00-t05/operation-log.json)、[verification.json](evidence/s00-t05/verification.json)。

Issue/PR → Project item ID → archived → 阶段 → 执行状态完整37行表见[identity-table.md](evidence/s00-t05/identity-table.md)，同表也直接写入#24报告评论。三个时点均无阶段/执行状态字段。#23—37保持OPEN/物理Status Todo；#24未写已验收或Done；#25—37在需求授权上仍待启用，不把Todo冒充已实施七态。旧21个Issue保持CLOSED/Status Done；PR13保持OPEN/draft/未合并/autoMergeRequest=null/Status Todo。没有以Closed作为归档依据，也没有关闭/删除实体。

原生字段：Title、Assignees、Status(Todo/In progress/Done)、Labels、Linked pull requests、Milestone、Repository、Reviewers、Parent issue、Sub-issues progress、Created、Updated、Closed、Priority(P0/P1/P2)、Size(XS/S/M/L/XL)、Estimate、Iteration、Start date、Target date，选项ID及迭代配置见快照。

原视图：Backlog/TABLE空筛选、Board/BOARD空筛选、Current iteration/BOARD筛选iteration:@current、Roadmap/ROADMAP空筛选、My items/TABLE筛选assignee:@me；均保持原样，当前并无“当前计划”专用视图。未把这些视图当作已排除历史项。

## 自动化写前/写后

[workflow-details.json](evidence/s00-t05/workflow-details.json)逐项记录ID、number、name、enabled；trigger、conditions_filter、action_field、target_value均为null并标BLOCKED。写前/两次读回的元数据一致，配置内容未获读取，不能说“配置前后已核验一致”。

|编号|名称|enabled前→后|触发/条件/动作目标|
|---|---|---|---|
|10|Auto-add sub-issues to project|true→true|BLOCKED，未知|
|13|Auto-add to project|true→true|BLOCKED，未知|
|9|Auto-close issue|true→true|BLOCKED，未知|
|12|Item added to project|true→true|BLOCKED，未知|
|7|Item closed|true→true|BLOCKED，未知|
|11|Pull request linked to issue|true→true|BLOCKED，未知|
|8|Pull request merged|true→true|BLOCKED，未知|

本轮实际schema返回createdAt/enabled/fullDatabaseId/id/name/number/project/updatedAt，与[GitHub官方schema](https://docs.github.com/en/graphql/reference/projects#projectv2workflow)的能力边界相符。按[官方内置自动化说明](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations)，实际条件/字段需在Workflows界面查看；未把文档默认值当本Project配置。

初次合并4个__Type.fields选择被GraphQL查询限制拒绝，gh退出1；[原错误](evidence/s00-t05/schema-query-rejected.json)保留。按限制拆为两次合法只读查询，各退出0，现有schema分别在[workflow-view-schema.json](evidence/s00-t05/workflow-view-schema.json)、[field-mutation-schema.json](evidence/s00-t05/field-mutation-schema.json)。这是查询结构校正，不是获取额外凭据或绕过权限。

## 浏览器新实测与需要用户的一步

真实Firefox155.0默认安全启动，Playwright1.63.0，1280×900，08:20:14—08:20:21 UTC。请求`https://github.com/users/Yredxin/projects/4/workflows`返回404，title为Page not found，meta user-login为空；随后正常登录页返回200，title为Sign in to GitHub，用户名及密码输入框存在且为空。**404不被推断为Project不存在或URL已认证可用**；已认证CLI能读到Project，当前具体缺失为浏览器正常登录会话。

[browser-access.json](evidence/s00-t05/browser-access.json)、[真实空白登录页截图](evidence/s00-t05/project-workflows-login-required.png)保存新实测，probe退出2。截图已视觉检查，无密码、token、cookie或私密资料；没有截取任何填充后的登录/二次验证页面。

最新授权边界明确写道：**“若需要用户进行一次GitHub网页登录/二次验证，停止并明确告诉用户具体一步，不要猜配置。”** 因此停止Project写入，不关闭workflow、不用CLI token注入浏览器、不请求额外凭据。

需要用户在**Ubuntu图形桌面的终端**执行以下一次登录命令。普通浏览器会打开正常GitHub登录页；用户自己输入账号/密码并完成2FA，再关闭该专用浏览器窗口。不要把凭据或cookie/token发给Codex。现Codex命令环境无DISPLAY/WAYLAND_DISPLAY，不能代用户完成交互；不伪造display值或改主机策略。

```sh
cd /home/redxin/code/odoo/odoo-sd/code/sd-addons
PYTHONPATH="$PWD/.local/s00-b-deps/verify-lib" \
PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/s00-b-deps/browsers" \
LD_LIBRARY_PATH="$PWD/.local/s00-b-deps/browser-libs/usr/lib/x86_64-linux-gnu" \
../.venv/bin/python scripts/s00_t05_browser.py --interactive-login
```

交互模式需现有桌面display，当前无display所以此模式NOT_RUN；它只是正常登录入口，未测试/承诺登录必成功。专用profile由Firefox正常管理，位于`.local/s00-t05/github-firefox-profile`且0700，不提交。普通个人浏览器的登录不会自动登录此profile；无需导出个人浏览器数据。登录后告知“专用浏览器已登录”，接续时先重新核对Project与正常认证，再读取全部7项配置；不继承过期快照后直接写入。

用户查看[Project #4](https://github.com/users/Yredxin/projects/4)，菜单Workflows查看自动化；当前无新建视图，未声称看板整理完成。无需用户截图或搬运本报告。

## 数据、回滚与复核申请

Project及Issue/PR实体状态/正文mutation全部为0（不计本任务要求的#24报告评论和Git推送），故无外部配置回滚；没有业务数据、迁移、费用库存资金或文书变化。只提交两个只读工具、当前批次说明和脱敏证据；代码可在本分支revert，失败/补交证据保留。私有登录profile仅在用户自行登录后产生正常会话，可通过该浏览器正常退出登录撤销，不导出cookie或删除其他profile。

S00-T05验收为BLOCKED；归档、字段/视图写入、两个同步轮次和幂等验收均未执行。申请仅复核本轮能力定位、保护边界及新证据，**不申请T05或整个S00通过**。S00-A/S00-B及浏览器补证原技术复核保留；不修改其结论，不关闭#24、不合并、不启用S01。报告回写并再次读回后停止，等待上述一次登录条件。
