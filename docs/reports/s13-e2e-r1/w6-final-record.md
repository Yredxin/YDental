# E2E-W6 新团队续验记录

计划：YD-S13-E2E-R1 / 1.1。状态：**IN_PROGRESS**。本记录由新 C-W6 维护，补充既有 [W6 记录](w6-record.md)与[断网记录](w6-offline-record.md)，不覆盖旧证据或将尚未实测的项目记为通过。

## 固定承接与边界

- 活动分支 `codex/s13-e2e-r1`，本地产品 HEAD `dca4e1d2821b20df7b4b940d28d461270c310225`，tree `4c09b0c5207f5a5c342ad3ccb63f2a51db2e5bad`。目标须每次现场核实为隔离合成库 `ydental_s11_synth_20261023_01`、OID `2171423`、cluster `7694897083368259627`；本记录的身份不代替新的现场核查。
- 本团队的 A、B、C 为 W6 续验新线程；各次浏览器使用新的独立 Context 和正常 Odoo 登录表单，不复用其他阶段的 Session。C 负责事实和证据登记，不直接把 A 的观察定成产品 BUG；主控统一安排共享环境与业务写入。
- A／B 测试门店为 `541`／`542`。W5 终态独验中，患者 `1647` 的文书 `509`–`511` 和 `513`、CBCT 任务 `888`、续诊任务 `898` 仍待处理；负例患者 `1645` 的文书 `512`、续诊 `895` 和发药续领 `897` 的未完成责任须保留。任何后续测试前均须重新核对状态，不从旧快照推断当前事实。
- 账单 `169` 已结清，退款 `12` 已合成实退 `100`，首链净合成实收 `640 USD`；账单 `174`／`175` 经一次合成收款 `300` 分配 `270`／`30`，后者剩余 `170 USD`。发药事件 `353`／`354`、原生库存流水 `755`／`756` 与退药待核事件 `757` 均已提交，不得重放。各原始回执及独立物理读回见 [W4](w4-record.md)、[W5](w5-record.md)。
- W5 阶段独立全保护快照 SHA-256 `c4663d87b05b8f38b87749b3e0fa47e7ddeeccbf091f8aa3dc9b75b79eb6e485`；相对 W4 的 145 表旧投影无删除、83 旧文件引用保留，其他新增及变更按原报告分列。目标升级后 16 个旧 URL／menu／view 缺紧邻完整前像，26 项复杂字段未直接对照，技术保护仍为 **UNKNOWN**；此前库存 mutex `13 → 0` 及技术摘要差异保持，不直接 SQL 回写。
- W5 终态记载 11 个 UAT 账号仍 active，测试结束需保留身份和审计并停用登录；当时无活动 lease／hold／执行及目标其他连接。测试端口已停，`web.base.url` 为本轮值、最终须依主控流程恢复。以上均为交接时点，须由本团队独立前检及终验确认。
- 不接触生产、真实患者／资金、正式外部通知或支付，不伪造权限、状态、业务身份或时间。对未知提交先只读回核实，不能盲重试。保留正常审计、原始失败、工具退出和不可重放记录。

## 继承事实与续验清单

| 场景 | 本次续验起始状态 | 已有事实与仍需证据 |
|---|---|---|
| A／B 店权限与跨店写入 | PARTIAL | 旧 W6 在旧候选真实观察 A 写／B 读页面及授权；B 店医疗写的真实服务端拒绝和合法历史读取／跨店写分离仍须适用前置与本候选证据。 |
| 旧页切店／撤权 | PARTIAL | 旧 W6 有旧页切店 `409`、前台撤权旧 GET 和 POST `403`；W5 另有医生对本次原件 `310` 撤权后旧页真实 `403` 并恢复权限。不能将这些结果扩大到全部岗位或动作。 |
| 无业务权限及无资质医疗动作 | PARTIAL | 无资质账号真实叫号取得 409 `no_eligible_waiting`，B 核无执行／费用副作用；资格筛选为源码及前置推断，非响应指明具体拒因。无业务权限其他医疗动作仍须实际证据。 |
| 退款申请人不得自批 | PARTIAL | 新申请 `13` 经本人单次审批得到通用服务端拒绝，独立物理读回未发生退款及贷项；具体拒绝首因未从响应或日志直接证实。随后申请已取消、临时权限有效恢复，见下方记录。旧退款 `12` 已完成，**不得重放**。 |
| 同患者并行双执行 | PARTIAL | 同患者实际接诊时，对新检查任务报到取得真实服务端 409；B 独立前后物理读回无双执行及非法副作用。正常交还及独立浏览器复测仍待记录，见下文。 |
| 过号、故障撤呼、人工追加、取消返额 | PARTIAL | 单候选过号与自然超时后进入触发撤呼、停接人工追加并报到、未使用现场资格取消返额均有真实网页与 B 物理读回；过号位移、多候选故障顺位和自动 cron 延迟未验。退款 `13` 的 `240` 可退额为源码推断，不等于直接读回。 |
| 未完成文书、检查、库存核对和未知事务 | PARTIAL | 上述 pending 文书、CBCT、续诊、负例续领与退药 `757` 隔离待核为已确认交接事实；仍需核对本候选下实际未完成责任未被自动标成完成。未知提交先查原生记录。 |
| 合成复诊、厂商及人工外加工 | PARTIAL | 已创建合成复诊及内部待办，未发送通知、未完成联系或复诊；厂商及人工外加工仍待验，不触真实外部服务或历史工单。 |
| 断网与未知提交 | PARTIAL | 旧 W6 仅对新患者创建表单以浏览器离线模拟验证无虚报成功，非物理链路中断或服务端拒绝；其他业务断网与未知事务需各自真实证据。 |
| 阶段保护、资源和角色终验 | NOT_RUN | 比对固定候选、独立物理快照、业务／库存／资金／文书／附件／审计及责任，记录真实正常审计和锁变化，关闭本阶段各自 Context 及资源。 |

## 观察、复核与问题登记

本阶段每个观察先标 `OBSERVED`，记录实际场景、身份、前后状态、操作、预期／实际、浏览器／HTTP／RPC 证据、是否持久提交及安全重现条件。B 独立复核后按产品、操作、数据、环境、需求歧义或 UNKNOWN 分类；只有经独立确认并必要时由主控裁定的真实产品问题进入正式缺陷清单。无法复现不能自动判 A 错误或产品通过。

此前 W6 `W6-CROSS-01`、`W6-OLD-SCOPE-01`、`W6-REVOKE-01`、`W6-REVOKE-POST-01` 和 `W6-OFFLINE-01` 的步骤、局限与原始回执保留在原阶段报告；其产品候选为 `181c861…`，不能未经最终候选的适用验证拼成当前全部通过。W5 原件旧页撤权证据见 [W5 记录](w5-record.md)。本记录不包含密码、Cookie、Session 或可公开的认证材料。

## 工作记录

初始化时仅阅读用户计划、活动 `CURRENT_TASK.md`、旧 W6／W5／W4 报告并核本地 Git HEAD／tree；C 尚未登录、启动服务、连接数据库、执行业务或发送 GitHub 消息。所有实际业务证据须由 A、B 分别提交，C 只核对来源、记录和摘要。

### 退款自批负例

A 报告正在准备正常网页申请、同人审批与必要收尾的工具，仍须由 B 独立审查和主控统一调度；截至该报告，未启动目标服务或提交业务。首次本机选择器 mock 因浏览器运行库路径缺失失败，其原输出仅在工具会话；A 随后在不连接目标的纯合成 DOM 中分别重现一次缺库失败、修正库路径后的选择器成功。重现失败输出 SHA-256 `fe5ac6cf1a237b0b06ba70ddd04c9ff4a75d8976c38cfde50057735cefe88e51`／exit 1；成功结果 SHA-256 `e38907f452b3432176e9e2613ef6eda27f737b2f4e07a1cfec1f524ddb54c231`／exit 0。C 已实际核两文件摘要及退出码；这只证明本机工具模拟，不代替真实网页或服务端验收。

B 独立源码初核：现有结算 HTML 拒绝可能统一表现为 HTTP 303 和通用 denied，具体异常正文及拒绝原因未必可由页面或审计直接取证；因此以后即使观察到通用拒绝，也必须区分实际响应与根据前置／源码作出的推断，不能预写为已观察到同人审批拒绝。若为该负例临时授予角色权限，恢复到有效 `none` 可能保留一条显式权限记录和审计；不能用 SQL 删除或称数据字节完全未变。上述均为准备和源码分析，**自批服务端负例仍 NOT_RUN**。

A 后续启动工具时，首次因指定 Python 路径不存在退出 127，第二次因非交互 stdin 为空导致 JSONDecodeError／退出 1；A 报告两次均在建立目标服务及浏览器 Context 之前，退出原文只在工具会话、未落盘。随后正常启动后，管理员 `1541`／A 店在 `1548` 的财务审批权限表单停于 `GRANT_READY`，该时点尚无授权 POST；运行 intent／服务日志位于本机 `.local/s13-e2e-r1/w6-final-grant-grant-once/`，最终回执尚未生成。该段为 A 报告，实际提交及权限状态仍待 B 独立核实，不能以 READY 记为授权成功。

后续 A 报告 B 已只读核实权限记录 `5026`、审计 `80992`：`finance_approval` 由 `none` 变为 `write`，其余类别不变；账号 `1548` 对收款 `32` 单次申请 `1 USD`，形成新退款 `13`、状态 `requested`、申请人 `1548`，没有原生支付或贷项凭证。退款申请是已提交动作，**不得重放**；B 独立读回材料及最终裁定仍待收集。

C 实际读取浏览器回执：授权操作 `result.json` SHA-256 `3e085a7249da70e44c5c72bd7d27876f6366838cea895289389ae075e737986d`，载明单次授权 POST 为 HTTP 303，浏览器／Context 关闭；退款申请 `result.json` SHA-256 `21c60c8d6e6b7bab2d6d401c7286f32dc4649f1c4c106f5d3499c5c0b76af079`，载明付款 `32`、金额 `1`、账号 `1548`，一次请求收到 HTTP 303 与通用受理提示，浏览器／Context 关闭。HTTP 提示本身不能证明数据库状态；上述退款编号与状态依赖 B 的独立读回，等待记录证据。自批拒绝尚未执行，不得记 PASS。

B 独立物理读回证据位于本机 `.local/s13-e2e-r1/b-w6-final/`：授权前 `physical-pre-grant-v2.json` SHA-256 `372b779dc209358647a6f0e6f7b5af5e74f08d50bcdc0448ab4c774f87a1716f`，原结算权限 write、导出 none、审批无行（有效 none）；授权后 `physical-post-grant.json` SHA-256 `c82a50494eba8c9099b9abd4a5fee746922c86d0ceceb4f52fdb55000679d824`，记录授权和审计，其他权限及账务不变；申请后 `physical-post-request.json` SHA-256 `4fa2eb6576dc8ebc169bd35d05fee74ca42a4b8bf82567e638b296c210e04429`，唯一新退款 `13` 符合上述状态，无原生付款及贷项，原退款 `12` 全行、收款 `31`–`33` 和账单 `169`–`176` 未变，服务已停且连接和准备事务为零。C 核实上述三个证据文件摘要；业务内容由 B 独立读取并报告。临时权限仍须依主控安排恢复并独立核验，不能删除审计或声称字节原貌。

A 以申请人 `1548` 正常页面对退款 `13` 单次提交本人审批，HTTP 303，页面为通用“请求未完成”反馈；服务日志有 `settlement.action`／denied 安全拒绝，A 报告日志 SHA-256 `34a9ae032977d8e44ea56a4e3902d8f778139df9865fffe200c822d69b4ff00a`。浏览器回执 `.local/s13-e2e-r1/w6-final-refund-approve-once/result.json` SHA-256 `d0e660e571dcdb5a964a5a42ba3c79f5726d70107d08071123f900b4454067f1`，C 核摘要。

B 审批前独立物理读回 `physical-approve-ready.json` SHA-256 `303cb6a5efdec511eb2ab2946a74f6b9f817d81888f069376f20b2c5581bb30d`：`1548` 结算及审批均 write，退款 `13` 本人申请／requested／1 USD，无原生退款及贷项。审批后 `physical-post-approve.json` SHA-256 `6126e74a05f6bbafd6a1b0efc481e0d8254702475adef867480b1e7fdfec9f66`：退款整行未变、仍 requested 且无审批人／原生退款／贷项，原退款 `12`、付款 `31`–`33`、账单 `169`–`176` 和权限未变。C 核以上两文件摘要。实际取得的为通用服务端拒绝和未发生财务副作用；精确拒绝首因只能根据源码及前置推断，不能称响应明确表明自批原因，也不能写成 HTTP 403。该场景最终判定由主控结合限制决定。

B 报告在一次真实取消提交后独立读回 `physical-post-cancel.json`，SHA-256 `837b537b18ba4e066e9b0aa796f9663834d2d6d79d60ae8c407d608267811abf`（C 核摘要）：退款 `13` 为 cancelled，申请及取消人均 `1548`、`release_verified=true`，无原生退款或贷项；原退款 `12`、付款和账务不变。B 根据当前源码额度规则推断付款 `32` 无活动占用退款、额度恢复 `240`；此推断应与实际页面或额度读回区分。取消网页回执及授权恢复证据待收集。

A 补报取消由 `1548`／A 店在正常页面单次 POST，HTTP 303，通用受理反馈；`.local/s13-e2e-r1/w6-final-refund-cancel-once/result.json` SHA-256 `f951955981ef18c23db28e95508b5aa7e531e9ba241514c6712e4db9a4c611e2`（C 核摘要）。浏览器、Context、服务正常关闭，私有配置已移除；实际取消状态以上述 B 独立物理读回为准。

B 在权限恢复后独立读回 `physical-post-restore.json`，SHA-256 `ffb08faa94f67f26e23be24b1b8e84d0f19b0d1aea370704c3622e206c624a7b`（C 核摘要）：权限记录 `5026` 的 `finance_approval` 已为 none，审计 `81025` 由 `1541` 记录 write→none；`1541`／`1548` 其他授权逐行与本场景开始前一致，两笔退款、付款 `31`–`33`、账单 `169`–`176` 与恢复前一致；活动执行／租约、连接和准备事务均为零。原先无该权限行，如今保留 none 行及两条正常授权审计，故是有效权限恢复而非字节还原。

A 恢复操作由 `1541`／A 店单次正常页面 POST，HTTP 303；`.local/s13-e2e-r1/w6-final-grant-restore-once/result.json` SHA-256 `f85c0e5b815f02a35fbbbac8b4ae24c867cbd9f4a49a0a682b4c7e49e79c917c`（C 核摘要），Context、浏览器及服务关闭，私有配置删除。实际恢复以 B 的物理读回为准。

### 跨店读取与旧页切店

`1541`／B 店通过正常网页临时授予 `1550` 前台 write，形成授权 `5027` 和审计 `81030`；`1550`／B 通过正常页面为合成患者 `1647` 单次建立 B 店关系 `1677`，无到店，旧 A 店关系 `1676` 整行不变，审计 `81037`。`1541` 随后将前台权限恢复为有效 none，保留医疗 read，审计 `81045`；新增 none 行和正常审计保留，非数据库字节还原。`1544`／A 正常网页新建唯一明确标记的合成病史背景 `1`，版本 1，审计 `81054`。这些提交不可盲目重放。

`1550`／B 使用新 Context 正常登录并查看 `history_review`，GET 200，实际看到 A 店来源的合成背景及跨店只读提示，该记录编辑表单数为 0；B 用独立新 Context 真实表单登录和访问复验相同结果，形成合法访问审计 `81075`。B 回读授权、关系、背景、原文书／待办及原件摘要未变，连接和准备事务为零。该结果支持跨店合法历史读取及界面只读，**不证明当前 B 店跨店写的服务端权限拒绝**。

另由 `1550` 在同一 Context 的 A 店旧背景表单（revision 2）中切换至 B 店（revision 3），单次实际提交得到 HTTP 409 `version_conflict: The store changed. Refresh this page.`；B 独立核背景整行、权限、A／B 关系、原文书、待办与原件摘要不变。此为旧页面门店 revision 冲突拒绝，不能记作当前 B 店直接跨店写 403。该项无经独立确认的产品缺陷。

原始浏览器回执均在本机 `.local/s13-e2e-r1/`：`w6-final-cross-grant-grant-once/result.json` SHA-256 `91afa201c07809bb3cc6c5d2b177b71310ce4c1a05a904fbb844438bfe1a1c07`；`w6-final-cross-patient-relation-once/result.json` `21dcc5186593be2376eb392ad6dead1efd6687f75233967cd84078a457fc9287`；`w6-final-cross-grant-restore-once/result.json` `40e2fa484152e0924bbd36009db21d53a296de77776d5956e78d95f166fc6f14`；`w6-final-cross-patient-add-once/result.json` `e7427f8a2724b5b6d919c4df68cc9324d29215f088449e22f01942d374b56dd9`；`w6-final-cross-patient-read-once/result.json` `21c551a02a049eaffdbf53dc96e8811306c1823be92941e67e9ed10539267015`；`w6-final-cross-old-old-once/result.json` `8e002bdc7e512717c5ec54630f3c5114301b25c8cddb3be332d1c421b3ec2b7d`。B 独立浏览器回执 `b-w6-final/independent-read-read-once/result.json` `e3730aa980343631c2fe22b93a3c48be23e6736af965e02be5c366adcd553fce`；均经 C 核文件摘要。

B 物理读回依次为 `b-w6-final/cross-pre-grant.json` SHA-256 `91ca4fc2bed3f4f5fff3a8259c83556240dd32c4010c98335e8a64dbf2eb55ae`、`cross-post-grant.json` `3c20831823f6ceaf7fbef4d851384056166e45a65e582ff16ff101393b5bd47c`、`cross-post-relation.json` `56710b938935d39fa9e77c57cc261548c6696a6369dbc990548c9cc2ce10a530`、`cross-post-restore.json` `25ebfbd332f18280cbe2b1dc8e748f7b1d2ef53a47fbb277c85262ae9dca1dea`、`cross-post-add.json` `aab462a84a6e2caefed92e7f1fe0a0dffeddaea63b078eebe9dc12cb4d34a85b`、`cross-post-read.json` `ce09e35f5d1f325fb0dc9f142a451be5f7bff915679e29223c79049e5b2d8c57`、`cross-post-independent-read.json` `8ff7c9c0fef918d586390e1bba5a24484d773deed20e2531b46d0d552dc76421`、`cross-post-old.json` `8d6ce71b21b3b9d2cd692dfc3dcfffc5c71ffe45aabb95fc504d75689c01c3ab`；C 已核以上摘要，业务内容由 B 独立读取报告。

### 同患者实际执行冲突

A 报告医生 `1544`／A 店正常接诊形成执行 `549`，签发单项合成检查医嘱 `33`／明细 `53`／任务 `899`；前台 `1543` 使用独立 Context 对当日任务 `899`／版本 1 单次正常页面报到，实际 HTTP 409：`handover_required: This patient has an unresolved actual execution.` 前台 Context 关闭。浏览器事件 `.local/s13-e2e-r1/w6-final-tools/double-conflict-events.jsonl` SHA-256 `c4e5ce906300780a0f56697da73f8a01021b8bb2cc8c71aabfcc3ca0dc017c59`，C 核摘要。

B 独立物理前像 `.local/s13-e2e-r1/b-w6-final/double-conflict-ready.json` SHA-256 `75d791b5804de87df836d48c69ad3a738817b997dcd14095b1a07a4cd2aa303b` 与后像 `double-post-conflict.json` SHA-256 `89dd3f621a55eb893c44bc2781ee6fdb211f013be07e52fb6943f7d21918f35b` 比对，任务／位置／队列／执行／医嘱／文书／6 条费用事件／slot／claim 均不变，`899` 保持 pending、`549` 仍唯一 serving；C 核两个摘要。此为真实服务端拒绝及 B 独立物理复核，不是 B 独立浏览器重复提交或真实并发压力测试。医生随后正常交还及未完成责任状态仍待回读，已提交医嘱和执行不得盲重放。

主控转达 B 交还后物理读回 `.local/s13-e2e-r1/b-w6-final/double-post-handover.json` SHA-256 `46a35f1867f8cf865afac0a03cbd7dde1ec5863f785551406c760a3db83963d9`（C 核摘要）：执行 `549` 为 handover，文书 `514` 为 pending／v2，检查任务 `899` 与续诊 `900` 均 pending；医生已正常退出。业务内容和最终资源终态由 B 继续独立核验，不得把这些未完成责任自动标为完成。

B 最终退出后读回 `.local/s13-e2e-r1/b-w6-final/double-post-exit.json` SHA-256 `42d5ed02b11f8420d758f04978d3d513114a3d8cae6b98a064739840431ddc8a`：文书 `514` pending／v2、责任人 `1544`，执行 `549` handover，原续诊 `898` handed_over／v6，检查 `899` 和新续诊 `900` pending／v1，旧检查 `888` pending／v1；6 条费用及 6 条费用事件未变，批次 `278` 实物流和隔离 quant 同场景前。无活动 lease／hold／执行及数据库连接。医生网页回执 `.local/s13-e2e-r1/w6-final-double-doctor-once/result.json` SHA-256 `c7c47c234256f8f6b9ec44b58be0513bee513cb6bb6e0c2b7326573e88edfe6c`；以上 C 核摘要，状态由 B 独立读回。

### 无资质检查负例准备中的真实失败

`1541`／A 临时向 `1550` 配置检查权限 `5028`，profile 从 `[559]` 变为 `[559, 560]`、职称未变；B 核无检查资质。前台 `1543` 对检查任务 `899` 单次正常网页报到，实际 HTTP 409 `reporting_closed`；回执 `.local/s13-e2e-r1/w6-final-unqualified-report-report-once/result.json` SHA-256 `aa21aebb2772a9b9f23fe53ce03e1dd07954bede3709fd0247a7512d26ca08ef`。B 发现此前误把当地 10 月 27 日的营业开放当成 10 月 28 日仍有效；独立物理回执 `.local/s13-e2e-r1/b-w6-final/qualification-report-failed.json` SHA-256 `8269e86a8298292fae7f8f6459ce63aed3bcb0d4add58a3bb87eed6c4b438643`，确认 `899` 仍 pending／v1、任务位置等无副作用。C 已核两项摘要。

主控将此归类为测试前置／复核错误：B 自报先前审核漏核营业日期，不应归责 A；原失败及 B 更正保留、不计正式产品 BUG。该 409 不证明无资质服务端拒绝。无资质负例仍 NOT_RUN，临时权限须由主控协调恢复并独立核实，不盲重试已有提交。

随后按当前业务日正常开设检查区营业 `1227`，任务 `899` 正常报到形成队列 `558`／waiting。`1550` 能力匹配但无检查资质，通过真实页面叫号，得到 HTTP 409 `no_eligible_waiting`；B 独立物理回读 `.local/s13-e2e-r1/b-w6-final/qualification-post-call.json` SHA-256 `1ed0619d921ad0f3ac3c63f1960b6dc8dd5c4302b7d68928e02d073b1573b8eb`，确认无执行、费用及非法副作用。随后正常退出，lease `551` 为 holder_exit，队列仍 waiting；临时授权恢复及最终独立读回仍在进行。

该响应为通用候选不可用错误；将其归因于资格筛选仅是结合源码与前置条件的推断，不能声称服务端响应直接给出无资质拒因，也不能把未完成检查自动标为完成。正常开业、报到和叫号网页回执分别为 `.local/s13-e2e-r1/w6-final-unqualified-business-once/result.json` SHA-256 `83cba3a0a86bac314ae654d861d64ac5cc38f1bf954724c9459b50766308f393`、`w6-final-unqualified-report2-report-once/result.json` `33412071d17ebebe4c72b5188318fea5a52bfb728091e1a8b60fc7163a632468`、`w6-final-unqualified-call-once/result.json` `b142742f5edaf4d6d13715719d4e263b1a32ebb8ce3e5873b5c4260f2906e73a`；C 核实各摘要。先前 `reporting_closed` 原始失败及 B 更正仍保留。

B 最终独立读回 `.local/s13-e2e-r1/b-w6-final/qualification-final.json` SHA-256 `3df99dc7356baf7de7b0f6bef608619899b2e49e3017fdccefcf952170520438`（C 核摘要）：`1550`／A 的检查授权 `5028` 恢复有效 none（原为无行，非字节还原），医疗 write 不变，能力恢复 `[559]` 及原职称，`1545` 资格不变；`899`／队列 `558` 为 accepted／waiting，位置 active，无活动执行、租约及数据库连接。检查仍为未完成责任，不得自动完成或盲目重放。

## 本团队阶段汇总

本团队真实网页与独立读回覆盖：跨店 A 历史读取及 UI 只读、旧页切店的真实 409、同患者实际执行时检查报到真实 409 与合法交还、申请人本人审批的通用服务端拒绝及退款取消、无资质候选的通用 409；以上各项的实际范围及限制见各自记录。自批与无资质场景的通用拒绝未直接说明具体首因，只能结合前置和源码推断。B 对双执行提供独立物理复核，未独立重放浏览器动作。

尚无本团队经 B 独立确认、主控裁定的正式产品 BUG；原营业日期前置／复核错误与工具初始化失败已保留，不计产品 BUG。跨店直接写服务端权限拒绝、其他无业务权限医疗动作、过号多人位移、复诊厂商及人工外加工等仍未完成或 NOT_RUN；断网证据仅为原报告的患者表单模拟。原保护快照的未知项仍 UNKNOWN，不能将不同提交的旧阶段通过拼为最终候选全通过。检查 `899`、队列 `558`／`559`／`560`、文书 `514` 和任务 `888`／`900` 等未完成责任须延续保护；阶段级完整保护终验与准出由主控统一决定。

### 队列补验新合成患者

前台 `1543` 通过正常网页创建新合成患者 `1648`／`P00001648`。B 独立读回患者与旧任务、费用隔离；`.local/s13-e2e-r1/b-w6-final/queue-extra-post-patient.json` SHA-256 `a852d524a4886a82737f9abf1f93915d07f8c428ba7f0d170996aa39c827384f`，C 核摘要。后续现场资格、过号和取消须逐步以新业务前置及独立读回证明，创建患者不代表任何队列场景已通过；已有 `899`／`558` 待办和活动位置保持保护。

B 读回新患者登记：slot `1237` 自动执行真实转换，预约／现场由 `1／2` 变 `0／2`（先转为现场 `3`、再扣 `1`）；新 claim `603` 和 entitlement `575` held，task `901` pending。旧 claim `600`／`602`、任务／队列 `899`／`558` 及旧任务、文书、费用不变。`.local/s13-e2e-r1/b-w6-final/queue-extra-post-register.json` SHA-256 `b4934d27b354d7c07c0f16578ecdf5ec064b064e1db1672baffeedd1ecaf0b0c`，C 核摘要。登记已提交，不得盲重放；取消返额等仍待实际验收。

`1648` 实际到店生成 arrival `1442`，随后真实报到使 task `901` accepted／v4，生成独立 queue／position `559` waiting／active；entitlement `575`／claim `603` 仍 held，容量没有二次扣减，旧 `899`／`558` 等保持不变。B 物理读回 `queue-extra-post-arrival.json` SHA-256 `3f6006fd2c84f5ef8c3613a258e6b0634116ea99ef6edeb5039dbd4d5fd1b732`、`queue-extra-post-report.json` `42ff79b440313238fdddf0b67be5643e29611760f59992e42e894f46d9224063`，均在 `.local/s13-e2e-r1/b-w6-final/`，C 核摘要。新队列已有持久位置，后续不得盲重放报到。

医生 `1544` 正常进入工位 `1334`、叫号 `559`，对 calling 状态单次点过号，三次 HTTP 均为 200。B 核过号后 `559` 回 waiting／missed_count 1，task `901` accepted／v6／missed 1，`575`／`603` 仍 held，无执行，旧 `558`／`899`、容量及费用保持。当前区域仅一个候选，**不能证明配置的位移两人**。医生正常退出及资源终态待 B 核验。浏览器回执 `.local/s13-e2e-r1/w6-final-queue-missed-once/result.json` SHA-256 `2daa1e532f7ee68bf873e63374133db4ac356207649c93699bef71561dd56f1e`；B 物理回执 `.local/s13-e2e-r1/b-w6-final/queue-extra-missed-post-missed.json` `09b6aa11115752f12d58cc447be7f21b4ee9178db9e43efd79acde4111255a6e`；C 核摘要。

B 最终独立读回 `queue-extra-missed-post-exit.json` SHA-256 `b3045f73008867010ab9c004bd7731c8d076f19e4c5523cdbe26cdf7887548b8`（C 核摘要）：lease `552` 为 holder_exit，`559` 仍 waiting／missed 1、`575`／`603` held、旧责任不变，无执行及连接。过号次数和返回等待实证成立，位移仍未验证。

容量取消使用另一独立来源：新合成患者 `1649` 正常登记，B 核 task `902` pending／v2、entitlement `576`／claim `604` 为 held walk-in，slot `1237` 现场余额 `2 → 1`，未报到、未执行，旧两队列等不变。物理回执 `.local/s13-e2e-r1/b-w6-final/queue-extra-post-register2.json` SHA-256 `d9f7dd6d8575f64e0c376fcdc5dacf6a03a8d263d74462bfc28b934dee91e245`（C 核摘要）。这是新登记持久提交，取消及返额仍待真实结果和独立读回，不得重复登记。

前台 `1543` 对未使用 entitlement `576` 正常页面单次取消，POST 303。B 独立核 `576`／`604`／`902` 均 cancelled，slot `1237` 现场余额 `1 → 2`、预约余额保持 `0`、版本 `5 → 6`；过号来源 `603`／`559` 及旧 `899`／`558` 未变，无执行、连接或准备事务。网页回执 `.local/s13-e2e-r1/w6-final-queue-intake2-cancel-once/result.json` SHA-256 `861d9a05881f808ce9ee88b8dd9bb06d7f4db0ab48140ee2aab416bd18dad55c`；B 读回 `.local/s13-e2e-r1/b-w6-final/queue-extra-post-cancel2.json` `c8c2b8af649129828671a1488252c18dd6ac306c9337d940068d0e19e5cd2d35`；C 核摘要。此为未使用现场资格取消返额的限定实证，不扩大到其他来源或状态。

故障撤呼场景进行中：`1544` 再真实叫号 `559` 后关闭 Context、未正常 exit；B 独立读回唯一 active lease `553`，最后 heartbeat `19:34:46 UTC`、自然 `expires_at` `19:44:46 UTC`，`559` calling，其他 active lease／hold／执行均无。`.local/s13-e2e-r1/b-w6-final/queue-extra-fault-disconnected.json` SHA-256 `738727c6c4494b78cc4f6ee9e4b9199fdaf99bb9c864a07fce923a5a400dc4e5`，C 核摘要。正在等待自然期限及实际后续读回，此时不记撤呼通过，不伪造时间或手动改状态。

自然期限后 `1550` 以新 Context 正常进入 `1335`，触发原生清理；B 现场读回 lease `553` timeout，`559` waiting／order 1000／missed 1／opportunity true，后三项与故障前叫号前一致，旧 `899`／`558` 不变。`1550` 正常退出 HTTP 200，最终退出后物理读回待 B。网页回执 `.local/s13-e2e-r1/w6-final-queue-fault-once/result.json` SHA-256 `6e5b10aa18689b4747158f9a5ee4463c5ac63fe91a7685dbd10b18de75bfb781`；B 回执 `.local/s13-e2e-r1/b-w6-final/queue-extra-fault-post-recover.json` `ed8eb5a1e7a32853a246f681518eb0612d36a392c5860b8514d260b6084bd266`，C 核摘要。该实测由新进入动作触发清理，不证明 cron 自动运行时延。

B 最终核 `queue-extra-fault-final.json` SHA-256 `0e522ab13f2a34ba37e4cc60349d9762726d97510cd792e0479b008123a5798b`（C 核摘要）：新 lease `554` 正常退出，旧 `558` 等不变，无活动 lease／执行／连接及准备事务；`559` 恢复状态同上述读回。自然超时加新工位进入触发的单候选故障撤呼通过限定路径，多候选顺位及 cron 自动时延未验。

### 人工追加隔离前置

`1541`／B 店正常新增工位 `1339` 的 `isolated_test` 策略 `282`。B 核旧策略 `280`、明日 slot `1234` 整行及两等待队列和旧责任不变；物理回执 `.local/s13-e2e-r1/b-w6-final/append-post-policy.json` SHA-256 `15f2551ffac7cb2ab78f0b8ddacb3382b3c7afd48db896c0540f4919f304816a`（C 核摘要）。新 `1339` slot 后续优先选取此策略，是持久测试配置影响，不称完全无副作用。真实追加、区域恢复和权限恢复仍待逐步验收。

原生组授权首次工具尝试中，正常表单生成 `[[6,false,[17,68]]]`，测试门控错误地只接受另一种零值表示而拦截，未发保存 POST，随后工具超时；B 正独立核实际提交状态。此为工具观察，不是服务端拒绝，也不直接登记产品 BUG；原始退出及后续独立核验须保留，未知结果不可盲重试。

B 独立读回确认该次未提交，`1550` 完整组仍 `[17]`、保护状态不变；`.local/s13-e2e-r1/b-w6-final/append-group-grant-blocked.json` SHA-256 `2dd85086f2238cf1567a9ed0a8b3de359689bdd376812b9933548f66131bb17d`，C 核摘要。该次未知提交已按实读结果厘清，归为工具门控错误，不计产品缺陷。

随后通过正常 Odoo 原生用户页授组，B 独立核 `1550` 完整组由 `[17]` 变为 `[17, 68]`，其他授权及受保护数据不变；`.local/s13-e2e-r1/b-w6-final/append-group-post-grant.json` SHA-256 `eefc89f4c0c2f7b701bf4fd90a290f06964b12f0b6ec4a0019369d4f4fdbe205`（C 核摘要）。组变更已提交，最终须经正常入口恢复原组 `[17]` 并独立读回。

B 独立核 `1550`／B 临时 frontdesk 授权 `5027` 为 write、医疗 read 保持，组 `[17, 68]`；B 区本地 10 月 28 日营业 `1228` open，旧 `1225` 未变。新隔离 slot `1238` 为 draft、工位 `1339`、策略 `282`，时间 UTC 19:55–21:00，旧 demo slot `1234` 整行未变。`.local/s13-e2e-r1/b-w6-final/append-post-business.json` SHA-256 `ad7733be6cbfdbe86e18f83de57d94a4b5c2cfe8de2fabe9cd8d12c2df95171b`，`append-post-slot.json` `8cfafd51bc169149f247c08be0f42375542bad182dd210d39e964b762d19ee53`；C 核摘要。该新增营业及 slot 是持久测试前置，真实追加尚未完成，需最终恢复权限并记录区域状态。

slot `1238` 后续正常发布／v2，策略 `282`，预约／现场余量 `1／2`，旧 `1234` 和旧业务不变；`1550` 正常创建 B 店新合成患者 `1650`／`P00001650`、关系 `1680`，联系方式为空，B 核旧保护不变。B 读回 `append-post-publish.json` SHA-256 `acc5e6d2b22cfe81dabc5e22cb52a81fb03dbf00d0254b0a00b43c07f070ce56`、`append-post-patient.json` `c440ef6671afaa3302d1731b89106bd9d3d6a2fb8ec63035d3a1908afd410239`，均在 `.local/s13-e2e-r1/b-w6-final/`，C 核摘要；这是持久前置，不代表追加完成。

`1650` 合法登记后 B 核 task `903` pending、entitlement `577`／claim `605` held，slot 自然转换并扣减后预约 `0`／现场 `2`；`1550` 实际到店后 `1541` 正常将 B 店 business `1228` 转为 draining／v2，旧队列和费用不变。独立读回 `append-post-register.json` SHA-256 `02a163cfde8e367f7394a3dfc9933949c8d73e4909260a82c7e282b048338265`、`append-post-drain.json` `5ebd733b810bc88ce725bee0e5c3108b3927003d68d7ac6c4b5e055eb9688b51`（均在上述 B 目录、C 核摘要）。登记与停接是实际持久变更，不得盲重放；完成场景后须恢复营业 open 并独立核验。

`1550`／B 对 task `903` 正常页面追加，观察 POST HTTP 200，但响应正文读取失败，原工具失败保留。B 独立读回唯一 permit `1` active，绑定患者 `1650`／task `903`／mapping `1271`／capability `559`／actor `1550`，槽容量、资格及其他队列／文书／费用未变；提交已确认，**不得重放**。浏览器回执 `.local/s13-e2e-r1/w6-final-append-permit-append-once/result.json` SHA-256 `3d7dba0f08fa69f140120fa567eb4cc537cdcc6427f0e1a7ded817892241d6c7`，物理回执 `b-w6-final/append-post-permit.json` `fbb9218686bacb125e4af77118fa29d57e61d419687321a1d301776a2d50c241`，C 核摘要。正常报到及许可效果仍需实际验收，不能以 200 代替后续状态。

区处于 draining 时 `1650`／task `903` 正常报到；B 核 accepted／v4、唯一 position `560` active／queue `560` waiting，entitlement `577`／claim `605` held，slot 未二次扣减，A 店旧队列／费用不变，无执行或 lease。浏览器 `w6-final-append-intake-report-once/result.json` SHA-256 `6f568058cad8e8e0ab6de28974c1602160815f8bcba2e79db730cbd5723601ba`，B 物理读回 `b-w6-final/append-post-report.json` `d6312f6e40c0b1ec80f5d0e86169a0e0b85e1f35b4c034bd4a75a0f5fad4edfa`（均位于 `.local/s13-e2e-r1/`，C 核摘要）。该实际结果支持停接时任务绑定追加及报到；后续营业／权限恢复须单独读回，`560` 是未完成待办，不能自动完成。

B 最终独立读回 `.local/s13-e2e-r1/b-w6-final/append-final.json` SHA-256 `3c77c11fb5939b7050f6d91ef834923fa8f217fb6bd7c045df6375b91be80e8d`（C 核摘要）：`1550` 组恢复 `[17]`、B 店 frontdesk 有效 none／medical read 保持，business `1228` 恢复 open／v3；permit `1` active、`903`／`560` waiting 及资格 held 保留，旧 `558`／`559` 不变，无活动执行、lease、连接或准备事务。新增 `282` 策略、`1238` slot、`1650` 与许可和待办均是实际合成配置／数据，应保留审计，不称数据库原貌恢复。

### 合成复诊

医生 `1544` 获临时 followup write 后，正常页面单次创建复诊 `283`：患者 `1647`，源已确认治疗 event `352`，责任人 `1544`，计划当地 10 月 29 日 10:00，状态 `to_notify`。B 独立读回新增内部未完成 activity `215`；旧通知 jobs `51`、mail `13`、通知策略、源 event／队列／费用不变。网页回执 `.local/s13-e2e-r1/w6-final-followup-create-once/result.json` SHA-256 `8e41a99c6679f2070e9f3afb55ee1cf4e7a30cd816be1e5c6969014f6a520d33`、B 物理回执 `.local/s13-e2e-r1/b-w6-final/followup-post-create.json` `4bf000760787b3883736398325f6a92e8fb649cc46fcd3af228c6e604ad78ef2`，C 核摘要。复诊和 activity 是已提交未完成责任，不得重放或声称已联系、发送通知或完成复诊。临时权限恢复及独立终验仍在进行。

B 最终独立读回 `followup-final.json` SHA-256 `670a61982b4d44d56f5b6da555f1a00de949cba6b2215ae41f9528a3e2198052`（位于上述 B 目录，C 核摘要）：`1544`／A followup grant `5029` 恢复有效 none、medical write 保持；复诊 `283` to_notify／v2、activity `215` active、无 contact，通知策略／jobs／mail 及原事件业务不变。应继续保留负责人 `1544` 和未完成责任。

### 合成厂商与人工加工准备

厂商页面准备中，真实 partner 保存被测试工具本地字段门控拦截，保存 POST 数为 0。B 独立读回目标不存在，旧 vendor／order／cooperation／通知 job／mail 不变；`.local/s13-e2e-r1/b-w6-final/lab-partner-blocked.json` SHA-256 `61c17574fc5a5e637404ba0e270c13754b92da69f9e536c6fed01f84f88788ed`（C 核摘要）。原失败保留，分类为工具错误而非服务端拒绝或产品 BUG；厂商和人工加工业务仍未实际通过。

此前一次默认字段诊断亦未发送保存；随后正常 Odoo 页面创建无联系方式的合成 partner `3376`。B 独立读回旧 vendor `14`／order `24`／cooperation `14`、通知 job `51`／mail `13`、两条 disabled 通知策略及待办／费用均不变；`.local/s13-e2e-r1/b-w6-final/lab-post-partner.json` SHA-256 `fbe7ec9d1e1d79b788f8e0119675072a573b48002cb3eedceec37eb601ed7018`，C 核摘要。新增 partner 是真实持久前置，不能代替厂商资格或加工流程实测。

资格草稿首次因缺必填公司未发送请求，第二次测试工具门控拦截 `web_save`；B 最终独立读回没有新增 vendor，旧 14 厂商／24 工单／14 合作、jobs 51／mail 13 及待办／费用不变，连接和准备事务为零。`.local/s13-e2e-r1/b-w6-final/lab-vendor-final.json` SHA-256 `beada5d3d09cc15dc05215e7b5fd3a83a4ffe3efd33a2206d92be02ac828b4db`（C 核摘要）。主控停止该场景重试；资格草稿未完成，该失败非产品服务端拒绝。合作及人工外加工工单因潜在未来外发未执行，保持 NOT_RUN；不存在厂商或加工业务 PASS 证据。

### 阶段交接

本团队 W6 为 PARTIAL：真实独立网页与 B 物理读回限定证据和遗漏见本记录；正式产品 BUG 0，测试工具与前置复核错误留存。新合成待办包括 `899`／`558`、`901`／`559`、`903`／`560` 和 permit `1`、复诊 `283`／activity `215`，以及文书 `514`、旧检查 `888`／续诊 `900` 等，必须保持未完成状态与责任。新增策略 `282`、slot `1238`、partner `3376` 等为实际持久测试数据和配置，策略影响工位 `1339` 将来的新 slot；未修改旧策略 `280`／旧 slot `1234`。跨店直接写拒绝、多候选位移、复诊联系及厂商／加工、自动 cron 等无相应完成证据；旧保护差异与 UNKNOWN 延续。完整资源和全保护终验由主控与后续新 W7 团队独立完成。
