# S06-A修正交付与复核申请｜YD-N1 R1

本次仅按[GPT-REVIEW6117074066](https://github.com/Yredxin/YDental/issues/30#issuecomment-6117074066)修BLOCKER-1—4，沿用当前S06-A会话/分支，原启用6116491783及A批边界继续适用。这是Codex实现、自测与安全自查交付，不代表GPT技术PASS或用户验收；交付写回读回后停止。

## 来源、Project及固定提交

2026-10-12 UTC重新读取#23当前正文/全部有效评论、#30正文/全部有效评论及#29最终S05技术复核/状态同步记录，完整读取最新定向返工评论。#23最终统一用户验收决定6110178328继续适用。

用户本次单独授权#30自定义执行状态→返工。实施前完整读取Project #4的21字段、15条目、6视图、7公开workflow元数据，只执行一次字段mutation：#30“执行状态”从“待启用”→“返工”，两次完整读回仅此值变化。原生Status保持Todo、阶段保持S06、其他字段/条目/视图/workflows/Issue实体状态未改。执行状态保持返工，不自行转待复核。[Project证据](evidence/s06a-rework/project-state.json)。

|固定版本|值|
|---|---|
|原S06-A final|`840df8921cfb5a70c601e6e8ed81fb7d03aacd5b`；原报告/证据/失败链原样保留|
|S05基线|`50ac95ac368c8c53bc264d8360c9daa94c0e362b`，不重做|
|当前分支|`codex/s06-a-queue-r1-20261012`，无强推/自动合并|
|修正product|`dfc6ff4a08e3ed80977e114042f08a0491d5ca0b`|
|最终test|`fe0df66f7ffb55f3895d192f381d9dc7448d2b50`|
|最终final|包含本文的文档/证据提交，完整SHA固定于#30修正交付评论（避免自引用SHA）|

product→test仅翻译验证脚本和新增测试内中文状态断言；产品树一致。test→final仅AGENTS/文档/脱敏证据。原840df89及其前序commit均为祖先，不重写历史。

## 环境与隔离

底座固定本地Yredxin/odoo `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，声明20.0；不冒称同SHA官方上游核对。使用核心`.venv/bin/python`及既有进程本地资产，无系统依赖安装。核心、odoo-12、业务库及既有服务未修改。

最终全新库`ydental_s06a_test_20261012034435_fa34a4e9`；127.0.0.1:5432/odoo，cluster7694897083368259627，HTTP18116，独立config/data/log、精确dbfilter、创建/OID/config hash记录、0 cron、SMTP禁用、进程外发guard；详情见[隔离记录](evidence/s06a-rework/isolation.json)。只合成数据，不复用原S06-A或S00—S05库。自建预览验证后仅核对本批PID/精确config退出，既有服务不动。

## 四项修正

|BLOCKER|完成情况|实现与实际结果|
|---|---|---|
|1 未解决execution约束原actor|完成A范围|统一_actor_execution供enter/call/start、S01执行店fence、status及页面使用。timeout→verify后原actor不能新椅或另一患者、不能借新session/目标店有权身份跨店人工写；旧工位在页面和全局systray继续显示待现场核实。其他人可在其他空椅工作，旧患者/工位/token继续保护|
|2 task/station eligibility|完成|call/start/UI共用helper，S05 reporting area、execution area本身/合法后代、catalog精确能力及live人员权限/能力全部校验。非空qualification基础hook严格fail-closed；仅guard下冻结合成provider证明正负路径，JSON/context不能伪造；call后撤资质/改执行区或能力，start拒绝且claim仍held|
|3 missed及N未发布|完成|call前N<=0拒绝、waiting和idle lease不变，UI禁用且POST仍拒绝。持久call_rank和order anchor；区域第3/4位真实过号从原位置后移N/不足到尾，不能重插队首；return真实过号消耗机会，fault恢复原锚点/机会且不计missed|
|4 自动timeout审计|完成|请求和cron共用固定系统base.user_root、source=workstation_timeout_automation。after保留holder_user_id、lease_id、station_id及call/execution结果；无关用户B不被写成A超时actor，竞争仅产生一个自动事件|

实现位置：ydental_queue/models/ydental_queue_service.py、ydental_access_service.py、ydental_queue_entry.py、controllers/queue.py及对应QWeb/Owl/JS/PO。原queue/lease/token/S05 start/position设计保留；S03账本、S04 merge内核、价格快照未重写。

## 实际回放与测试结果

|场景|合成操作/预期|实际|
|---|---|---|
|verify人员围栏|真实S05 start→serving；停止心跳→timeout；原actor新椅/新session/跨店写拒绝，旧位置仍verify；另一人可工作|模型、HTTP、真实竞争及Firefox PASS；无B接手/交还入口|
|执行区/资质|同一reporting区两子执行区且同能力，服务指定A；B椅拒call/start，A/合法后代可做；非空资质无provider拒，可信源满足才通过，start重验|模型/HTTP及错误区Firefox PASS；无真实资质业务空壳|
|混合能力missed|区域Panorama、CBCT、Cleaning…；Cleaning-only叫原第3/4，N=2后仅后移或尾；同时另一能力叫号|模型/HTTP及真实竞争PASS，原排序锚点与其他call保留|
|fault/未发布N|fault恢复rank/机会且missed不增；N=0时call前拒绝|模型/HTTP/Firefox PASS；生产N仍未发布|
|自动审计|A过期；B合法动作及cron竞争cleanup|系统actor/source一致；holder=A；只一事件，模型/HTTP/竞争PASS|
|原F1/F6及A批回归|回诊/真实过号/重报、无排班坐诊、空闲换椅失败保旧、班次只提醒、真实hook/一次consume|原32业务方法与原16竞争保持并PASS，原26个Firefox关键路径回归|
|F2/F3/F4/F5与其他批|保留/返回/交还/人工追加、日终/推送及真实临床|NOT_RUN；没有用固定合成契约冒充真实链|

|检查|结果、数量/退出码|固定证据|
|---|---|---|
|install|PASS；0 failed/0 errors/50，exit0；48业务+2原生安装检查|final-verification及日志hash|
|upgrade|PASS；0/0/48，exit0|final-verification及日志hash|
|业务方法|PASS；37模型+11真实HTTP/RPC=48；原26+6不改，新增11+5|[方法清单](evidence/s06a-rework/model-http-cases.json)|
|原32连续性|PASS；原文件AST不变，安装/升级日志均核对实际执行全部48方法|[continuity](evidence/s06a-rework/continuity.json)|
|PostgreSQL真实竞争|PASS；21/21，exit0、deadlock0；原16+新增5，每组两个同时存活backend PID及完整RR重试轨迹|[最终并发](evidence/s06a-rework/probe-attempts/ydental_s06a_test_20261012034435_fa34a4e9-20261012T034648074369.json)|
|Firefox|PASS；36/36、exit0、14张截图、0 pageerror，Firefox155默认sandbox；原26项+新增10项|[最终浏览器与截图](evidence/s06a-rework/browser-attempts/20261012T034732097030/summary.json)|
|guard|PASS；5/5，exit0|final-verification|
|翻译|PASS；144/144、missing0、invalid code metadata0，exit0；原HTML消息DOM ID保留|[translation](evidence/s06a-rework/translation.json)|
|编译/格式/安全自查|PASS；compileall、diff检查、适用模式/ACL/来源检查|[安全材料](s06a-rework-security-review.md)|

新增5组为：serving timeout先于原actor新椅、既有verify原actor新椅vs sweep、execution-store fence vs跨店写、无关请求cleanup vs cron审计、mixed missed vs另一能力call。第二组明确以既有verify开始，不冒称再次发生serving timeout。原16组顺序/名称和不变量连续；各独立实际start场景改用新的合成人员，旧人员execution留存，不能通过删除/清状态绕过新围栏。21组全局一账号一椅、一waiting/calling、一actual execution、S03守恒均成立；50会话性能仍归S13。

命令使用核心Python：`scripts/s06a.py install/upgrade/probe/export --db DB`（依次各动作）、`scripts/s06a_rework_continuity.py --db DB`、`scripts/s06a_translation.py --db DB`、`scripts/test_s06a_guard.py`；serve后`scripts/s06a_browser.py --db DB`。复现须用另一个全新合规名称，不能接管已完成probe夹具或原历史库。

## 字段、动作与配置

[原完整字典](s06a-data-dictionary.md)与[原动作表](s06a-contracts.md)继续适用；两项排序字段、资格hook、未解决actor围栏、自动化audit和修正动作结果详见[补充契约](s06a-rework-contracts.md)。没有真实资质/临床业务表，测试provider只在ydental_queue_test中。

心跳/超时/过号N继续只做可配置，未生产批准。明确合成2秒/20秒/N=2；N=0不允许call。未将建议30秒/300秒/N=3或任何演示值写成正式配置。真实S08文书仍仅默认fail-closed的固定锁扩展，原合成独立文书锁验证继续回归。

## 用户效果验证

入口：后台全局工位提示→`/ydental/queue`；合成合格医生、前台、只读角色，无凭据公开。最终Firefox截图路径/hash由[browser summary](evidence/s06a-rework/browser-attempts/20261012T034732097030/summary.json)固定；已查看关键新增图，原工位待核实、错误执行区拒绝和N未发布提示与实际结果一致。

1. 无排班合格医生进入合法空椅，显示当前店/区/工位，不创造供给（图01）。
2. 另一人占目标后用旧页面换椅，失败保旧；目标主动退出再换成功，旧token拒绝（图02/03）。
3. S05真实报到→叫号→真实过号→同任务再报，missed保持1（图04/05）。
4. 停止calling心跳并真实等待超时，回队且不清既往missed，旧端不能复活（图06）。
5. 重新合法叫号/start，真实consume一次，serving忙时退出拒绝（图07）。
6. 只读无按钮且POST拒绝；中文工作台和全局坐诊提示可读（图08—10）。
7. serving持有端停止心跳并真实等待超时，由另一合法人员触发清理；原医生页面仍显示旧工位待核实（图11）。
8. 原医生无进入/换椅按钮，直接enter也拒绝；后台systray仍显示旧工位待现场核实，不能变idle（图12）。
9. 第二位合格人员进入同能力但错误execution子区椅，call被拒；页面原因与任务仍waiting一致（图13）。
10. 进入N=0合成区域工位；call按钮禁用、直接POST configuration_required、任务仍waiting（图14）。

## 失败链、数据与回滚

本批全部新库动作、提交、测试数/退出码和私有日志hash见[runtime-history](evidence/s06a-rework/runtime-history.json)。原840df89及docs/evidence/s06a原样保留，新增证据仅进入s06a-rework。

|新库后缀|失败/中间结果|修正及保留|
|---|---|---|
|033352_38ac94ca|首装翻译导入exit255，未进入业务测试；新增PO缺module标记|补原生metadata；库及私有原日志hash保留|
|033510_4c058dd4|安装50/升级48通过；probe原16+新增2通过后，在跨店夹具grant处因无B membership失败|只给新合成测试人员建立B membership以证明“有权仍被围栏拒绝”；不放宽产品，18组失败摘要保留|
|033833_e28069b1|安装50/升级48/probe21/词条144覆盖通过；Firefox29项/11图后全局中文verify检查失败，0 pageerror|实际PO缺odoo-python运行时标记；按真实导出对齐code metadata，加强翻译及真实中文状态断言；失败图/摘要保留|
|034435_fa34a4e9|最终固定test的新库全量结果|仅最终完整证据用于本次通过声明，见final-verification|

只新增两个受控entry排序字段及test-only资格事实，未迁移真实患者、删除历史execution、改写S03账本或S05快照；无真实医疗完成、费用/库存/资金写入。自动事件固定system语义且保留holder事实。原始log/config/access/cookie/token及备份不进入GitHub，公开文件通过私有访问值扫描和截图检查；[manifest](evidence/s06a-rework/artifact-manifest.json)固定hash。

没有生产部署或业务库安装；回滚可回到原840df89，保留本批新库/失败链，不drop历史库或重配服务。execution当前历史终身唯一的B前置改造要求、原生账号logout的业务释放整合按review记入补充契约，未提前实现。真实接手/交还、B/C、S07/S08/S09联调、日终/推送、发药、生产参数及50会话均NOT_RUN或未批准。

## 复核申请

申请GPT按固定product/test/final复核四项修正及其证据，随后按#23流程统一用户验收。Codex自测PASS不代表GPT或用户已通过。#30保持OPEN、Project执行状态保持返工，无原生Status/workflow写、强推、合并、关闭或生产发布。修正交付评论逐字读回后停止，不进入S06-B、S06-C或S07。
