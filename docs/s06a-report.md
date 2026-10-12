# 交付验收申请｜YD-N1 R1｜S06｜A批

这是Codex实现、自测和安全自查后的技术复核申请，不是GPT技术PASS或用户验收。只交付S06-A，交付评论读回后停止；S06-B、S06-C及S07未启用。

## 来源、版本与环境

2026-10-12 UTC完整读取#23当前正文及有效评论、#30正文及全部有效评论、#29最终技术复核和状态同步记录。唯一执行边界为[GPT-ACTIVATE 6116491783](https://github.com/Yredxin/YDental/issues/30#issuecomment-6116491783)，[开工检查6116516335](https://github.com/Yredxin/YDental/issues/30#issuecomment-6116516335)已写回逐字读回。交付前再次读取正文和启用评论，内容未变，见[来源证据](evidence/s06a/github-boundary.json)。#23最终统一用户验收决定6110178328继续适用。

#29最终S05技术PASS为6116482005，状态同步指令为6116491290；当前评论没有后续状态同步完成回执，本批不代改Project、不把指令冒称执行完成。S05固定交付与历史证据保留。

|版本|固定值|
|---|---|
|S05基线|`50ac95ac368c8c53bc264d8360c9daa94c0e362b`|
|分支|`codex/s06-a-queue-r1-20261012`；不强推、不自动合并或关闭Issue|
|product|`a2638afc637795a9dc148299f2075e0413b32f0e`|
|test|`8d0b347be18574c75d96673ce1264923bd98bcec`|
|final文档/证据|由包含本文的提交固定，完整SHA写入#30交付评论；避免自引用SHA|
|底座|本地Yredxin/odoo `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，声明20.0；未声称同SHA官方上游比对|
|解释器/依赖|核心`.venv/bin/python`；复用既有本地Playwright、Firefox、GTK和字体资产，无系统安装|
|最终新库|`ydental_s06a_test_20261012025405_2fd04bd7`，OID543425，仅合成数据|
|端点/隔离|127.0.0.1:5432、cluster7694897083368259627；HTTP18116、独立config/data/log、精确dbfilter、0 cron、SMTP禁用、进程本地外发限制|

完整隔离记录及配置hash见[isolation.json](evidence/s06a/isolation.json)。所有最终动作在test固定提交上运行；product→test仅增加翻译覆盖检查脚本，test→final仅文档/AGENTS/脱敏证据。核心、odoo-12、业务库及既有服务未修改。验证后只终止本批匹配PID/config的预览进程，保留数据库和失败材料。

## 需求完成情况

|要求|完成情况|落地位置与限制|
|---|---|---|
|真实S05队列hook、全局唯一waiting/calling|完成A范围|`ydental_queue/models/intake_service.py`及entry；真实report建立号位，撤号/换任务/失败与position同事务，不安装S05合成队列适配器|
|工位lease、一账号一椅、一椅一人|完成|lease部分唯一索引、稳定RR锚点及四业务锁；无管理员强抢出口|
|无排班合格人员坐诊、空闲换椅|完成|实时门店写权限、员工有效及工位全部能力；不创造供给。目标失败保旧椅，忙时拒绝|
|精确能力叫号、回诊机会及真实missed|完成A范围|同区精确能力，不改服务；持久首次报到/机会/顺序/missed，重报不刷新，故障只恢复本次机会|
|calling→serving真实执行互斥|完成最小范围|真实S05 start/claim consume、撤position、独立execution；未建治疗完成或病历业务|
|心跳、timeout、旧端、另一session、撤权|完成|服务器冻结来源、session/revision/connection/token摘要绑定、每次实时授权；idle心跳续租，旧端不能复活|
|calling掉线/serving掉线|完成|calling回队；serving→verify保留患者及旧工位核实占用，不能自动完成或异处开做|
|班次结束/全局提示/无在岗解释|完成|班次只提醒；全局当前店/区/工位；前台显示权限/能力/占用等原因及可进入工位|
|独立文书锁/S08扩展|仅固定契约|产品默认拒绝，测试模块独立合成DocumentSource证明文书级独占；真实文书未实现|
|B/C与后续临床|未做|保留、交还、人工追加、日终、推送、S08/S09真实联调均NOT_RUN|

实现清单及锁分析见[契约](s06a-contracts.md)、[数据字典](s06a-data-dictionary.md)、[安全自查](s06a-security-review.md)。低层现有模块通过上层继承接入，无反向依赖或未来空壳。

## 流程实际回放

|示例|合成前提/操作|预期|实际与证据|
|---|---|---|---|
|F1|同能力先来甲/乙、当天已有真实started历史的回诊丙；丙首次机会叫入，真实过号N=2，再报同任务；故障撤呼|先回诊；过号顺延；重报/故障不清既往missed|PASS；模型T04、真实HTTP和浏览器04—06。多轮历史为明确测试事实适配，不冒称B真实完成链|
|F6|无排班合格医生进入空椅；另一人占目标后用旧页面换椅；目标退出后再换；班次结束|可坐诊；失败保旧、成功一进一出；班次只提示；无新容量|PASS；T17—19、并发T18、浏览器01—03；容量满新增登记仍拒绝|
|F2/F3/F4|保留/返回、交还/后继、closed人工追加|须B启用及真实来源|NOT_RUN；默认拒绝扩展契约不能替代这些业务|
|F5|当地23:55/00:00/00:10及日终重跑|须C启用|NOT_RUN；本批日期记录不能当日终处理通过|

## 测试结果

最终证据索引：[final-verification.json](evidence/s06a/final-verification.json)、[32个业务方法](evidence/s06a/model-http-cases.json)、[并发16组](evidence/s06a/probe-attempts/ydental_s06a_test_20261012025405_2fd04bd7-20261012T025542887339.json)、[Firefox结果](evidence/s06a/browser-attempts/20261012T025645576311/summary.json)。PASS表示本批Codex实际执行结果。

|TC/验证|结果|命令/合成角色|数量、退出码及数据检查|
|---|---|---|---|
|T01|PASS|模型、`s06a.py probe`；两个合格人员/同账号两会话|同椅抢占、同人两椅各仅一lease，无残留|
|T02|PASS|模型、真实HTTP、probe；同能力持有人/前台|只一calling；call↔void、void↔start、真实start↔其他call/start；一次consume及一execution|
|T03|PASS|模型；全景患者/仅CBCT工位|不能叫入，服务/所需能力不变|
|T04|PASS|模型、HTTP、Firefox；前台/合格医生|F1排序、N=2、重复报到/换区不刷新、故障不清更早missed，多轮非每日一次|
|T05|PASS|模型、HTTP、probe、Firefox；持有端/另一登录/只读|idle持续心跳不释放、超时旧端拒绝；calling回队、serving核实且独占；两种heartbeat/timeout提交顺序|
|T14|PASS|模型、RPC、probe；门店管理员/持有人/只读|撤权下一次写拒绝；撤权↔heartbeat双顺序；伪造店/context/直接CRUD/敏感字段读取拒绝|
|T17|PASS|模型、HTTP、Firefox；无排班合格员工/前台|可坐诊叫既有队列；不增容量；零余量新增walkin不能借空椅|
|T18|PASS|模型、HTTP、probe、Firefox|空闲换椅原子成功、占用失败保旧、旧token拒绝；calling/serving不能换椅|
|T19|PASS|模型及班次提示UI；合格员工|结束班次仍可合法叫号/接诊，不强制释放|
|T15及A批回归|PASS（A范围）|install/upgrade；实际S03/S04/S05链|零余量复用资格、hook故障整笔回滚、单position、真实start/cancel、价格快照不变、未来日期拒绝、改期失败保旧call/claim、canonical merge迁移waiting|
|固定文书锁契约|PASS（合成）|模型；两个独立文书/持有端|各文书独占、不同文书独立、持有人退出或lease失效释放；真实S08 NOT_RUN|
|T06—T13、T16、T20、T21完整业务|NOT_RUN|B/C/S08未启用|不以A撤号互斥片段冒称B许可撤销/发药/完整日终通过|
|guard|PASS|核心Python `scripts/test_s06a_guard.py`|5项，退出0；错误端点/库/配置等拒绝|
|安装|PASS|`scripts/s06a.py install --db DB`|0失败/0错误/34项，退出0（32业务+2原生安装检查）|
|升级|PASS|`scripts/s06a.py upgrade --db DB`|0失败/0错误/32业务项，退出0|
|真实并发|PASS|`scripts/s06a.py probe --db DB`|16组，退出0、deadlock0；独立同时存活backend PID、barrier/持锁交错、40001有界重试及全局不变量|
|浏览器|PASS|serve后`scripts/s06a_browser.py --db DB`|Firefox155默认sandbox，26项/10图，0 pageerror，退出0|
|翻译|PASS|`scripts/s06a.py export --db DB`及`scripts/s06a_translation.py --db DB`|135/135导出词条覆盖，缺失0，退出0|
|编译/格式|PASS|compileall及git diff --check|退出0；未修改固定产品树|

命令均使用核心`.venv/bin/python`，DB为本报告最终新库；首次复现须生成另一个全新合规名称，不能复用已完成probe的夹具或接管历史库。并发证据记录初始独立PID及每次RR重试PID，允许事务归还后连接池复用；50会话吞吐未测，仍属S13。

## 字段、动作与配置

完整字段（类型、关系、默认、隐私、唯一约束）见[数据字典](s06a-data-dictionary.md)；权限、前后状态、副作用、防重、失败恢复与固定锁顺序见[动作表](s06a-contracts.md)。S01 session→patient→supply→intake→queue；权限grant同业务fence串行，避免等锁后沿用RR旧快照。令牌仅持有端返回，数据库只存摘要，敏感字段禁止原生read/export；审计保留真实actor。

心跳/超时仅显式配置`ydental_queue.heartbeat_seconds`与`ydental_queue.timeout_seconds`，无生产默认；区域N复用`ydental_missed_limit`，0视为未发布。合成验证2秒/20秒、N=2。建议30秒/300秒、N=3仅供批准，用户与门店运营负责人尚未批准，不能用于宣称生产配置通过。现有价格仍明确demo_confirmation，不改生产锁价政策。

## 用户效果验证

实际Firefox回放已经执行以下路径；合成角色和数据不含真实患者，凭据不发布。界面入口为后台工位全局提示→`/ydental/queue`，前台可只读队列。

1. 合格医生登录当前店，打开工作台；显示当前店、区域、工位与“无排班”提示。[图01](evidence/s06a/browser-attempts/20261012T025645576311/01-unscheduled-workstation.png)
2. 点击进入合法空椅；无排班也取得唯一坐诊，不新增供给或患者登记。
3. 第二人先进入目标椅，再从第一人的旧页面换椅；服务器拒绝且原坐诊保留。[图02](evidence/s06a/browser-attempts/20261012T025645576311/02-switch-failure-keeps-chair.png)
4. 第二人主动退出目标椅，再换椅；成功释放原椅并取得目标，旧token失效。[图03](evidence/s06a/browser-attempts/20261012T025645576311/03-idle-switch-success.png)
5. 前台用S05真实报到建立waiting，医生点击叫号；仅精确能力患者进入calling。[图04](evidence/s06a/browser-attempts/20261012T025645576311/04-real-calling.png)
6. 点击真实过号，再报同任务；missed仍为1，机会不刷新。[图05](evidence/s06a/browser-attempts/20261012T025645576311/05-missed-repeat-report.png)
7. 再叫号并停止持有端心跳，超过合成20秒；calling回waiting，更早missed保留，旧端续约失败。[图06](evidence/s06a/browser-attempts/20261012T025645576311/06-timeout-requeue-old-end-rejected.png)
8. 重新合法坐诊、叫号并开始；真实S05 start→serving，忙时退出拒绝，不能擦除患者执行。[图07](evidence/s06a/browser-attempts/20261012T025645576311/07-actual-serving-fence.png)
9. 只读角色查看等待；没有动作按钮，直接POST仍拒绝。另一登录不能续持有端。[图08](evidence/s06a/browser-attempts/20261012T025645576311/08-readonly-no-actions.png)
10. 原生个人语言改为中文，检查工作台和后台全局当前坐诊。[图09](evidence/s06a/browser-attempts/20261012T025645576311/09-chinese-workstation.png)、[图10](evidence/s06a/browser-attempts/20261012T025645576311/10-global-workstation-position.png)

## 数据、审计、失败与回滚

仅新增queue产品/guard测试模块及本批runner、并发/浏览器/翻译检查。只在全新隔离库安装；没有真实患者迁移、业务库升级、库存/资金/费用写入、临床完成或真实S08文书。S03容量、S04身份/关系及合并、S05价格快照与资格继续原权威，联动通过继承，未重写账本或merge内核。审计及状态同事务，无产品手工commit；无管理员强抢按钮/API。安全材料是Codex自查，见[复核记录](s06a-security-review.md)。

全部本批库/提交/动作退出码/测试数/私有日志hash见[runtime-history.json](evidence/s06a/runtime-history.json)，失败probe和浏览器目录也保留。主要失败及补交：

|新库后缀|实际失败/发现|修正与后续|
|---|---|---|
|022200_361ba737|首装3失败3错误/24项：非存储关联字段被SQL search、夹具容量/ID/mock错误；后续升级曾有2个全库数量断言失败，probe清理误选其他店合成夹具|产品改为读取后过滤；夹具与计数/清理按目标店限定；中间22项升级、14组probe成功仍保留|
|023210_3beb5dc8|浏览器依赖导入路径、脚本args遮蔽先后失败；真实UI发现QWeb head未显式传入，JS未加载|复用既有依赖并修脚本；按实际20源码修模板head及路由，随后升级32项、浏览器26项/10图通过|
|024203_378230aa|安装34项通过|保留该中间验证，不冒充最终固定提交|
|024420_1b4bfd09|安装34/升级32通过，probe“最终PID不同”断言失败；RR重试后池可复用已归还连接|记录初始同时存活PID及全部重试轨迹，保留真实双连接barrier/持锁竞争，不降为顺序调用|
|024916_5bd41763|安装34/升级32/probe16/浏览器26通过；翻译导出覆盖发现HTML分组词条缺失1项|修真实PO词条，135项全覆盖；重新用全新最终库验证|
|025405_2fd04bd7|固定test提交全套通过|本次唯一最终结果；所有动作及浏览器固定8d0b347…|

另一次新安装在本批自建预览收到SIGTERM但端口尚未关闭时被guard拒绝，未创建库。等自建进程退出后用另一个全新名称运行；没有绕过guard或接管服务。原失败原始日志留私有`.local`，公开只提交脱敏结果、hash与合成截图；不提交配置、密码、SID、token或备份。[artifact manifest](evidence/s06a/artifact-manifest.json)记录全部公开证据文件hash。

本批无生产部署或生产迁移，回滚可回到固定S05基线/原分支；不删除失败库/证据、不卸载既有业务系统。生产参数发布、真实文书/治疗完成、保留交还、日终推送、发药及50会话均待各所属阶段授权与实测。患者serving掉线的verify在A中有意保持阻断，后续接手/交还须B真实原子流程；不能通过管理员改状态绕过。

## 复核申请

申请按固定product/test/final审查S06-A工程与证据，并请用户随后实际看效果。上述PASS仅Codex本批自测，不替GPT或用户宣布通过。#30保持OPEN；未写Project字段/workflow、未自动合并/关闭/发布。交付评论写回并逐字读回后停止等待GPT复核，不进入S06-B、S06-C或S07。
