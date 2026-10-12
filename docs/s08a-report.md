# S08-A 交付报告｜YD-N1 R1

本批完成真实治疗接诊文书、FDI 交互、独占编辑/版本、真实 S06 保存交还与 D1 待完善责任移交。仅申请 GPT 独立技术复核，全部运行结果为 Codex 自测，不代表 GPT 亲测、用户验收或生产可用。

## 来源、基线和环境

唯一启用：[GPT-ACTIVATE6122378640](https://github.com/Yredxin/YDental/issues/32#issuecomment-6122378640)。完整读取 #23 正文/全部2条评论、#32正文/启用评论及 #31 最新技术PASS6122197570、状态指令6122208075和回执6122311778；开工评论 [6122503237](https://github.com/Yredxin/YDental/issues/32#issuecomment-6122503237) 写回逐字读回后实施。交付前再读记录见证据索引。

- baseline：`a5f53ac72d6d43901932adedc64c56cf6f97c675`。
- product：`a69ac8bc431adb412341cd2fbff508d69ca0b84a`。
- test：`be5f28ef336295633fd0d753c3e97051a2dc457d`。
- final：本报告/证据/AGENTS 所在提交，完整 SHA 由 #32 交付评论固定（不在自身提交内制造循环SHA）。
- 分支：`codex/s08-a-clinical-doc-r1-20261012`，从指定 S07 final 创建；无 PR/合并/强推。
- 实际 Ubuntu26.04.1、Python3.12.15（核心.venv）、锁定 Odoo20 fork `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`、PG18.6。没有声称此 fork 已核对同 SHA 官方上游。
- PG `127.0.0.1:5432/odoo`，cluster `7694897083368259627`；最终全新合成库 `ydental_s08a_test_20261012113731_3d646c4f`，独立端口18155。创建UTC/OID/config SHA/dbfilter/data_dir/进程证据见 final-tests.json。

Project完整读取21字段/15条目/6视图及字段/7公开workflow；唯一一次mutation #32执行状态待启用→进行中。两次全读回仅 name/optionId 两叶差异；#32 S08/进行中/Todo/OPEN，#31待用户验收。交付前再次两次深比较无新增差异。没有更改workflow，也不声称读取未公开内部action/trigger。

## 需求完成情况

|R/功能|状态|实现位置/限制|
|---|---|---|
|R12—R14/R17—R20/R24 中 A 文书子范围|完成|ydental_clinical；上游事实经 S01/S04/S05/S06 复用|
|真实medical已领取段→治疗工作台|完成|controllers/clinical.py；实际患者/工位/服务/段状态、独立文书及待完善入口|
|恒乳牙与牙面|完成|service `_content`、QWeb与document.js；52FDI+显式0无对应牙位；后端校验|
|7项结构化草稿/模板字典|完成草案|[数据字典](s08a-data-dictionary.md)；正式临床审核未批准，不自动正常/已告知|
|自动保存/CAS/独占/旧端/离线|完成|真实版本持久化、服务端时间、随机摘要token与当前资格；串行自动保存/中文未同步|
|文字确认/原因更正/作者历史|完成|不可改写version链；不完成实际治疗/不收费/不扣库|
|S06真实保存/交还/编辑释放|完成|真实私有上层hook与同事务SaveIntent；失败回滚、唯一后继|
|D1待完善/移交、D2合法新接诊|完成A子范围|D1独立补记不占椅；D2真实报到领取、另一文书；D2实际项目完成NOT_RUN|
|保留/restore/verify|完成适用接口回归|真实保存/文书链接/lease历史；S09未装，合法外检前提仅明确合成测试|
|经济/药房/转诊/PDF|未做|S08-B/C未授权；没有未来模型或假成功按钮|

## 流程实际回放与适用TC

|例/TC|合成前提与真实操作|预期/实际及结果|固定test证据|
|---|---|---|---|
|F1-A / T01|真实接诊，连续3次自动保存；之后牙位/文字多次保存|版本连续、旧请求不覆盖；已有存货/演示价格快照无变化，PASS|模型test_three_real_saves；Firefox；经济签名对比|
|T02|同文书并发编辑/CAS、旧连接/租约/版本、独立D1/D2|一有效编辑/版本；旧端拒绝；不同文书独立，PASS|模型+16组双连接+Firefox|
|F2-A / T05|实际保存→handover，非法方向/保存失败；S06 reserve/restore及verify|原段历史保留，锁正确释放、唯一后继，失败完整回滚，PASS|模型真实hook；并发handover/rollback；Firefox|
|T06-A|D1交还，前台报续诊，其他医生/椅真实start D2，D1补记/移交/确认|不占原椅、不自动确认另一文书、贡献作者不改，PASS；D2真实项目完成NOT_RUN|D1/D2模型、Firefox04–09|
|T09|当前权限/跨店/公司丢失、附件/RPC/导出/假来源；合法目的性共享历史|拒绝旁路；合法read/export后撤权即时拒绝，PASS|模型/HTTP，安全审查|
|T10-A|确认后附原因更正|新关联版本/作者保留、经济不变，PASS；数量/费用更正NOT_RUN|模型confirm/correct，Firefox08/09|
|T12|新库安装/升级/带业务升级，S01—S07关键动作|无反向依赖，真实上游关键路径PASS；不是历史全套重跑|final-tests.json、模型/HTTP与审计签名|
|T14-A|续诊沿原care方向，其他合格医生/工位领取|不复制外检设备、不指定原医生，PASS；跨店转诊双分支NOT_RUN|真实handover/continuation/start、Firefox|
|T15|恒乳牙/前后牙/缺失/未知/0/模板中文|合法结构保存；非法值服务端拒绝，PASS|FDI模型/HTTP、Firefox01–03，翻译|
|T16-A|查看/保存/确认/更正/导出/责任移交|S01区分审计，原价和库存不变，PASS；经济事件/PDF部分NOT_RUN|原生source.export与clinical审计；经济签名|
|T03|真实项目确认并发/重复|NOT_RUN，B实际事件/费用/库存|没有用文字确认冒充实际项目|
|T04|真实已做缺料、核对恢复与调价|NOT_RUN，B/S10经济联调|S07原技术范围保留，不当作S08实测|
|T07|检查原单增项/删已做/取消未做|NOT_RUN，B/S09|没有真实检查单|
|T08|4+2、重复/超量/椅旁实际用药|NOT_RUN，B药房|没有发药/处方空壳|
|T11|三类中文PDF与正式审核|NOT_RUN，C|没有打印/假签署|
|T13|处方→报到叫号→4+2续领/次日closed|NOT_RUN，B药房|没有模拟统一药房闭环|

T09/T12等仅指本批适用子范围，不等于整个S08或全项目PASS。新服务接收、真实检查、收费/退款/跨法人交易及加工单不是本批验证。

## 最终运行结果

最终固定 test 的逐项结果、完整命令/角色/退出码、PID/日志hash以及失败链在 [证据索引](evidence/s08a/README.md) 和 [final-tests.json](evidence/s08a/final-tests.json)。最终库创建于2026-10-12 11:37:51 UTC，OID1043393，专属端口18155。

|验证|实际结果|退出码|
|---|---|---|
|新库install|30：21模型+7真实HTTP/RPC，额外2原生资产初始化|0|
|首次upgrade|28：21模型+7真实HTTP/RPC|0|
|带已提交文书/续诊数据upgrade|28，10组完整行签名相同|0|
|真实双连接|16/16，16对不同backend PID，barrier，14次有界serialization retry，deadlock0|0|
|Firefox|28/28项、11图全部逐张目视核验、pageerror0|0|
|中文导出|150/150，odoo-python metadata正确，source错误码保留|0|
|隔离guard|5/5|0|
|只读SQL|8类不变量均0；16份已提交文书/28版本/18真实接诊段|0|
|纯文书前后经济签名|event/batch/move/move_line/quant/S05 snapshot 6组相同，原合成600快照不变|0|

最终保留1个S05演示快照、50条原生move、36条move_line和40条quant；没有已提交S07受控库存event/batch，文书未新增库存或费用。外部inventory库位的原生演示对手负quant不当作内部可用余额，未修改它们。模型回归里的真实收/发货在测试事务回滚，不冒称最终committed业务。最终committed临床审计包括26个save、1confirm、1correct、3责任移交；原生source.export成功/撤权负向在模型事务验证，不能称生产导出或打印。

验证模块 `ydental_clinical_test` 只允许新S08A创建marker+匹配进程环境。只有 S03 合成demo容量前提override；临床文书无adapter、未依赖 ydental_queue_test。hold/restore的单一测试临时提供合成外检前提；S06保存、文书和接诊事务都是真实产品，不能称真实S09通过。库存模型回归实际receive10/issue2，在rollback测试内设置原生多库位前提，避免原生config向导对已存在合成价目的副作用；不改S07产品。

## 字段、动作、权限和审计

完整[动作/状态/权限/错误/失败恢复契约](s08a-contracts.md)、[文书与FDI数据字典](s08a-data-dictionary.md)、[安全自审](s08a-security-review.md)。确认仅文字，正式签发资格/临床字段/同意书仍需业务负责人审核。S06心跳/超时等仍未生产批准；测试2/20或2/600秒不能作为正式政策。

不可变原始execution与可恢复current_execution分开，restore不改原作者/历史来源。每版本冻结正文、模板、作者、服务器时间、前版本和请求签名；移交只改责任。查看/编辑/确认/更正/导出分开审计，元数据不复制病历全文/token。原生RPC、缓存读取、目的性共享历史/导出及权限撤销均在模型层约束。

## 用户操作（仅合成演示）

1. 合格医生登录选本店，打开工位队列，合法坐诊、叫号并开始本次医疗接诊；工作台显示真实患者/段状态。
2. 点击治疗接诊工作台，取得该独立文书编辑；输入主诉三次，观察服务端版本和UTC保存时间递增。
3. 点击恒/乳牙，选择明确状态及合法牙面；缺失/未知不填牙面，0表示无对应牙位。非法结构后端拒绝。
4. 填所见、诊断草案等，保存并交还；原段交还、旧编辑释放、文书待完善、唯一续诊待报到，不产生治疗完成或费用/库存。
5. 医生退出空闲原椅；从待完善打开D1补记，不取得患者位置。前台为唯一后继明确报到，其他合格医生在合法工位领取并start D2。
6. D2创建独立文书；D1有效编辑未释放时转派拒绝。D1责任人释放后附原因移交给有权合格人，旧作者不改名。
7. 新责任人核实可核实内容后仅确认D1文字，附原因更正追加版本；D2仍独立草稿/真实接诊，不自动被完成。
8. medical-read用户只读，不能编辑；模拟浏览器断网显示未同步，刷新后以服务端已提交版本为准。价目来源链接仍需独立权限，不表示已收费。

## 数据、迁移与回滚

只新增两个文书模型、私有服务、上层hook/来源注册/附件阻断和中文界面。升级仅本新增表NULL current_execution回填原execution；不重写患者/队列/价格/库存历史。没有生产迁移或真实病历。带持久业务升级前后10组完整行签名均相同；经济不变另按实际库存/价格行签名比较。

只在本批新合成库运行；历史库、Odoo核心、odoo-12、既有未提交内容/服务及系统依赖保留原样。预览只按专属config/PID核对后SIGTERM退出；无重启既有服务。所有失败/中间提交/脱敏证据保留，凭据/原始日志只留权限600的本机.local，仓库只记录hash/摘要与合成截图。

回滚须先停止匹配的本批预览，在另一个新隔离环境检出固定S07 baseline重新验证；不要在含文书数据的库上强行降级/删表，不删除历史证据或业务数据。A未获生产发布授权，不制定生产回滚执行。

## 未完成与复核申请

S08-B真实项目/经济执行/处方药房/4+2/转诊正式入口、S08-C PDF打印、S09—S13、50会话性能、生产参数/运维部署全部NOT_RUN。S07历史SIGSEGV根因仍未知，**生产稳定性/部署继续BLOCKED**；本批无崩溃不能称已修复或稳定性通过。如再次崩溃按授权立即留证并停止相关运行。

#32保持 S08/进行中/Todo/OPEN，发布交付评论逐字读回后立即停止等待GPT独立技术复核，不自动启用B/C、不关闭Issue、不合并/强推、不发布生产。最终统一用户验收仍未进行。

最终逐项16项TC机器可读表见[tc-matrix.json](evidence/s08a/tc-matrix.json)。最终截图如下（均Codex逐张目视核验）：

|截图|内容|
|---|---|
|[01-permanent-anterior-autosave.png](evidence/s08a/browser-attempts/20261012T114410131012/01-permanent-anterior-autosave.png)|52颗牙可读，11的M/I选中、O禁用；真实患者/接诊状态、服务器版本4及中文保存提示清楚|
|[02-primary-missing-unknown.png](evidence/s08a/browser-attempts/20261012T114410131012/02-primary-missing-unknown.png)|乳牙55/O、48缺失、51未知及0不适用摘要正确，未知/缺失没有牙面|
|[03-structured-draft.png](evidence/s08a/browser-attempts/20261012T114410131012/03-structured-draft.png)|7项文字草稿入口清楚；合成所见/诊断，不自动填写其他临床结论|
|[04-D1-pending-after-handover.png](evidence/s08a/browser-attempts/20261012T114410131012/04-D1-pending-after-handover.png)|D1原段交还，文书待完善，版本11/原作者责任及历史可见；字段只读|
|[05-D1-pending-independent-editor.png](evidence/s08a/browser-attempts/20261012T114410131012/05-D1-pending-independent-editor.png)|D1在idle无椅环境补记，服务器版本12；交还按钮禁用|
|[06-D2-new-reception.png](evidence/s08a/browser-attempts/20261012T114410131012/06-D2-new-reception.png)|另一合格诊椅真实D2接诊，新文书版本1；D1待完善仍独立|
|[07-valid-editor-transfer-denied.png](evidence/s08a/browser-attempts/20261012T114410131012/07-valid-editor-transfer-denied.png)|有效D1编辑时转派返回editor_busy中文提示，原责任与版本保留|
|[08-D1-confirmed-author-history.png](evidence/s08a/browser-attempts/20261012T114410131012/08-D1-confirmed-author-history.png)|D1文字已确认版本14，新责任doctor2，原作者doctor及所有贡献版本保留|
|[09-text-correction-new-version.png](evidence/s08a/browser-attempts/20261012T114410131012/09-text-correction-new-version.png)|版本15为文字更正，原因可读；旧confirm14和原作者版本仍在|
|[10-readonly-medical-denied.png](evidence/s08a/browser-attempts/20261012T114410131012/10-readonly-medical-denied.png)|medical-read编辑尝试显示access_denied中文提示，正文只读|
|[11-offline-unsynchronized.png](evidence/s08a/browser-attempts/20261012T114410131012/11-offline-unsynchronized.png)|D2仍草稿/实际执行中，未同步合成文本清楚可见，服务端仍版本1，无假保存成功|
