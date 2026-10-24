# S12 证据索引

Plan ID：YD-S12-DOCUMENTS-REPORTS-V1 / 1.0。最终带数据限定六模块升级已完成并独立通过；最终十六行独立总验收已签 TECHNICALLY_COMPLETE（610053fb…）；GitHub同步已正常完成并实际读回（见文末c4b9d8e6…），SYNCED不由技术通过自行推导。

唯一实际目标：`ydental_s11_synth_20261023_01` / OID `2171423` / cluster `7694897083368259627`；锁定 core：`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。业务从 S11 `e100e098dea5b919f3c9ca09454d239189e69ad1` 承接；未重建、改名或复制目标，未使用旧 scratch/attempt30/旧经济链补证。

所有路径均为本机忽略目录中的证据定位符，**不是公共附件或可公开下载链接**。本索引只手工摘录状态、层级、合成对象 ID、候选和文件 SHA-256；不复制原始 JSON、日志、连接配置、会话、凭据或正文。未新增公开原件文件。复现只读查看已生成原件；下列已提交业务不可整链重跑。

关键执行候选：首链 `333ef10`；首次 W2 `025e65e`；第一次普通修复 `b160587d96ab54cb70deb7e6ff11d72bc6556146`；真实财务/超时 `007900f3d4141a5e7a07f21aaf3e972a7126c68c`；QR 修复及当前 31 方法套件 `5cb1e46fbe1e4243c7a292f64ecfd375afb3dce2`。报告 HEAD 与产品候选分列；最终升级执行候选为 `3127a575b1403ea072c950f1e1d4e79d8055141d`，其产品/工具字节与 `5cb1e46fbe1e4243c7a292f64ecfd375afb3dce2` 相同。

## 交付后的运行事实更正

本轮用户明确“运行期限”仅指Odoo展示服务，非SSH、浏览器登录或平台授权期限；账号由Codex用既有获准私有凭据自行正常登录，不要求用户找roles.json。可见浏览器能力已核为缺少GUI/交接通道，当前只能操作不可见自动化浏览器，不能冒用户已登录。以下私有文件包可沿现有SSH/SFTP取阅，只有静态成果，不含认证状态且不代签用户效果。

|可见性与取阅证据|真实范围|私有路径|SHA-256|
|---|---|---|---|
|未实现者可见浏览器能力核验|SOURCE/OS：同UID仅TTY/manager、无X/Wayland/GUI浏览器，工具无可见交接接口；监督父子仍活，无新DB/HTTP/信号|`.local/s12/acceptance/visible-browser-capability-independent.json`|`f93645d2b71f3e9eccf12896fafc4c3e2f48721ce19a02bd7ae3abd8c3e5d6a7`|
|只读文件包准备原始结果|正常doctor/settlement登录选店、10次已存原件授权下载及7旧下载字节复用；17PDF/6静态图/README/manifest；16已获准秘密值逐成员0命中；无生成/经济动作/会话共享|`.local/s12/verification/view-bundle-downloads/result.json`|`03b208ac4fca7ab0d8692fe7e320039e5d70b88d76cac693b7fdf2f9cf231b9a`|
|用户可经现有SSH/SFTP取阅的私有ZIP|25个文件、1,352,579 bytes，17PDF+6PNG+2说明/清单；不上传Public仓库，不冒交互或已交用户登录浏览器|`.local/s12/viewing/S12-view-only-20261024.zip`|`11ce563c856ddc6b01336114081402a4317048e78fae9f8f25e8c728e9721f05`|
|未实现者只读ZIP独立核验|25安全成员/实际字节与manifest/hash、17PDF等既交付SHA；无profile/session/HTML/日志/执行文件；16获准秘密值对raw及解码PDF/PNGmetadata0命中、强模式0；非39页视觉重验|`.local/s12/acceptance/view-only-bundle-independent-review.json`|`43096806267732726082b3a2da3e90bcb93222cd8460a8cacb202a11d099e25a`|

用户后续明确启用S12效果准备，当前新run与用户待确认状态见下表和summary第9节。这里的03:34停止记录是历史收尾，不能用它覆盖新窗口实际状态；原S12技术验收、候选和失败记录保持。

|效果准备证据|实际层级与限制|私有路径|SHA-256|
|---|---|---|---|
|本次目标/权限/外发只读核实|真实新PG/RR/RO、rollback/close；未业务写或重装|`.local/s12/admission/effects-review-target-20261024.json`|`e7613f937d0495bd13d8db4f300a998f754d780f354851b3d939ba94b9f82225`|
|未实现者fresh准入审阅|SOURCE/实际原始观察/环境PURE；保留旧保护post，不冒新全库零diff|`.local/s12/acceptance/effects-window-fresh-probe-independent-review.json`|`b095d65a0f06ef8c1a5b358e687795ca0430bee29ef1e83251ef83c113bbd1a7`|
|本次tmux/监督/子进程及登录页独立就绪|真实OS、出生/父子/严格argv/独占loopback与HTTP登录页；Odoo展示服务运行期限05:52:53UTC，非用户认可|`.local/s12/acceptance/effects-tmux-os-login-readiness-independent.json`|`57e954d8929f9331e78bb9927e3744b03a0ccdb2ef113cecb8933733142a307e`|
|首次查看准备结果及工具收尾FAIL保留|正常doctor/settlement登录、16原件行、7下载、账单/报表均实际成功；误拦原生登录后页面加载，不冒产品拒绝|`.local/s12/verification/user-effects-20261024/result.json`|`f600f564917743fdfb8ee600bd32ce9d8054bb23060f3ed9985e62b4fb83c365`|
|限定接续真实链接查看成功|普通settlement/followup正常目标登录，collections7/lab214/followup280表内真实drill；无重复下载/经济/生成，用户效果仍待确认|`.local/s12/verification/user-effects-drill-continue-20261024/result.json`|`92f3065b33bdab899a1def6283525ba92e5c52bc982640c0c5316d64032aa2e7`|
|聊天展示的已保存原件99首页|从本次正常下载PDF渲染，不新生成文件内容；PDF SHA仍230d82e7…，展示不冒用户反馈|`.local/s12/verification/user-effects-20261024/original-99-page-1.png`|`c43e314b052befa7a5c16a0379f40844099f6c6f4e1d01a874d75adde7f63053`|
|未实现者查看准备独立核验|离线SOURCE/原始结果、7下载实际SHA及14截图hash；亲看7张图，保留首FAIL及限定接续；只签本机准备可用，客户端路径/用户反馈仍待确认|`.local/s12/acceptance/user-effects-preparation-independent-review.json`|`15bba3c8551f38ee00b6be1c2db044f2c51cea4f709a09035e22ee0d8728564b`|

2026-10-24用户“继续”后，实际巡检发现最终效果窗supervisor已不在、原child成为精确可核的孤儿；此前“最多04:54UTC”的上限不能证明当前持续在线。主控及未实现者分别dry核通过，主控于03:34:03—04UTC复用已有pidfd单SIGTERM与全套精确检查完成回收，原active原字节归档，该次03:34核实STOPPED/18411无监听。原supervisor/child退出码未知、不补0；无DB/HTTP业务请求、无重放、未自动复开。不改变已完成软件、实际文件与独立技术验收结论。

|证据|层级与限制|私有路径|SHA-256|
|---|---|---|---|
|精确孤儿单次回收结果|真实OS/pidfd；确认exit与释放端口；原exitcode保留null，不冒正常进程退出0|`.local/s12/runs/20261024T025453Z-f8f22a02427f/orphan-recovery-outcome.json`|`fd7acbaff92d2dc071a7215c7490564cb41f8932b66868369a34e4ea60b3e63f`|
|未实现者独立运行终态核验|SOURCE/OS/私有原始材料；亲跑信号前dry，信号后核child不存在、无listener、原字节归档；无DB/HTTP或reviewer发信号|`.local/s12/acceptance/effect-window-orphan-recovery-independent.json`|`efe07bf0cef6be892c40a0225d3e33d4dbde485342fdc373bf61eb6400b684ae`|

## 准入、环境与原生测试

`SOURCE/PURE` 表示源码或无业务运行校验；`MODEL` 表示原生模型测试（套件事务回滚）；`HTTP` 表示正常角色请求；`BROWSER` 表示真实浏览器交互；`RO/RR` 表示另一真实物理连接、只读可重复读事务及 rollback/close。角色分工不构成 OS 隔离证明。下列独立回执由未实现对应内容的 acceptance agent 审核；tester 的结果不能替代独立签署。

## 准入与套件回执

|证据 / 实际结论|层级与限制|私有路径|SHA-256|
|---|---|---|---|
|唯一目标原生准入|真实 RO/RR，权限/身份核实，rollback/close，无业务写|`.local/s12/admission/target-readonly-confirmed.json`|`d35806698a60e9cfd65a967621fdf1ed05edf3c55bdd50305ea3891266466dbf`|
|字体与私有 native PDF 依赖|独立 SOURCE/PURE；实际 fontconfig/fc-match、rl-renderPM 4.0.3 项目私有 payload/hash 和负例；不冒 QR HTTP|`.local/s12/acceptance/runtime-environment-source-pure-independent.json`|`d2142bc653b9d3964ba537a770577258771e4850fa581ef0492902fed1010528`|
|初始限定升级独立回执|限定四模块，child0/ERROR0；旧事实保全，非最终升级|`.local/s12/acceptance/initial-upgrade-independent.json`|`932e7ad196ffd12b5f42e56af1750488af2373270d45f5c74cf09c461e03d04c`|
|首次 W2 升级独立回执|四模块更新、reporting/test 两模块安装；99 installed；非全模块重装|`.local/s12/acceptance/first-w2-upgrade-independent.json`|`3dca2c580aecb09bfb2b087240c76a8ef98faf95c2618a216ea8672d18e3c67e`|
|首套件原始 FAIL|28 post-tests：1 failed/20 errors，child1/wrapper2；未发生 Native 崩溃|`.local/s12/checks/first-suite-suite/result.json`|`da18d84602c7597c062cb5b0001ddb69df236491aa1cceffba62b77c7824a3c7`|
|首套件独立首因|fixture 基类重绑定角色环境及原生 placeholder 预期错误；保留原 FAIL，不修改产品 ACL|`.local/s12/acceptance/first-suite-failure-independent.json`|`eebdbff7ee3e9ebd757382906054a52786c9e482c7bcbd3f8fa2f22d63de3928`|
|首套件后独立保护|业务/文件/权限/配置保留；仅模块技术时间变化；不把保护通过当套件通过|`.local/s12/acceptance/first-suite-protection-independent.json`|`4a7e28078247c4f04be25f41782c7418bf687b6ea22a8482fd65addaf98dd832`|
|第二套件原始 FAIL|b160：29 post-tests，1 failed/0 errors，child1；URL placeholder 取值预期仍错|`.local/s12/checks/fixed-suite-suite/result.json`|`3e2a9685a3511eec25d7912f6c019bcfee7a0713763056e3df74634233231c0a`|
|第二套件独立分类|修精确 native PNG 预期，未删除断言；该失败之后的 RPC 当时未运行|`.local/s12/acceptance/fixed-suite-failure-protection-independent.json`|`772648d24b8fa16532851f2233ec23721ce38d71137117051ac38b46b5b48c3f`|
|007 原生 29 方法独立回执|0 failed/0 errors；医疗/检查/财务四组合真实类别 HTTP、直链、撤权等；MODEL 非持久业务补证|`.local/s12/acceptance/007900f-29-native-suite-independent.json`|`3baf4687151c7ec695739d26610e4e4eb921d71769fe2118405f708e3611e5c6`|
|QR 修复限定升级独立保护|旧业务及全部受保护原件保留；非最终全数据收尾|`.local/s12/acceptance/qr-source-fix-upgrade-independent.json`|`45ba056c8b4de8e2e954b1f3117e60d7716e98c55c40b002fa237c5cf626a2bb`|
|最终产品套件原始结果|5cb：child0；31 post-tests，0 failed/0 errors，无 Native；日志/方法全表见独立回执|`.local/s12/checks/qr-source-fix-suite/result.json`|`035c48fc66834a91db3180ccb571f9d7ad508e49471ed992a1b8034349b68c7d`|
|31 方法独立验收|22 MODEL + 7 HTTP + 2 受控 encoder/authorization seam；后二者不冒真实 PNG 或普通授权实测|`.local/s12/acceptance/5cb1e46-31-native-suite-independent.json`|`18158ffe369b5b3077f1bd501e375a7239c85a8e487d41dd03f9e79d6c822b85`|

关键原生命令入口：`../.venv/bin/python scripts/s12/run_checks.py --phase upgrade|suite --candidate <固定候选> --modules <限定模块> --freeze <完整冻结记录> --pre <即时完整前态> --label <唯一标签>`。suite 实际原生参数包含 `-u ydental_s12_test --test-enable --test-tags /ydental_s12_test`；完整非秘密命令、子进程退出码与日志 SHA 留在对应私有 operation/result 中。31 方法实际官方结果是 `31 post-tests in 84.61s`、`0 failed, 0 error(s) of 31`，不以定义数、查询数或继承 fixture 数代替执行结果。

## 首闭环、历史原件、竞争与超时

正常入口是 `/ydental/documents`，preview/generate/download/print_request 经普通角色及真实 CSRF；旧原件下载读保存 bytes。所有失败先保留请求意图并独立核提交，再决定同 key 恢复；未重跑来源、治疗或资金。

## 原件闭环与恢复回执

|证据 / 实际结论|层级与限制|私有路径|SHA-256|
|---|---|---|---|
|首语言失败|正常 preview409；无原件/无改名；后由正常管理激活中文后仅续后段|`.local/s12/first-loop/first-normal-20261024/result.json`|`2b1c99b12c103509b758fd539fd50421d18b4beeff9537961e01e618151b8c10`|
|首字体失败|正常 generate409 font_unavailable；独立核原 key 无提交后恢复；非 Native 崩溃|`.local/s12/first-loop/first-normal-resume-zhcn-20261024/result.json`|`d5de94a48080908601e2f3ccc19c95c34a52ac0cf56653adeeffd068b3a55e0d`|
|原 key 恢复首闭环|正常 HTTP + 新物理提交核验；新 patient254/doc273，旧件1下载→正常更名→重印同 bytes|`.local/s12/first-loop/first-normal-recover-font-20261024/result.json`|`1a18f99e715d2619b38f2635074fbd314bd10c0cc9b1a0e5c36deca4e4db1a1d`|
|首链独立动态总回执|实际 HTTP/已提交源/逐页 PDF；旧件1旧排版问题保留，后续新版本复验|`.local/s12/acceptance/first-loop-independent.json`|`3828129241eb8d68da59eaa278c28d340842f76dfb98e0f1a2bf544ec26a1976`|
|首链独立已提交读回|源/模板/render/附件/两次下载/审计及经济保护|`.local/s12/acceptance/first-original-readback.json`|`2ea980e333ac92f13d380e4365f0a48d56ba15b582750355558e2c9d8beb0b5d`|
|T12 原始工具 exit2 保留|A/B 两事务均已 commit；收尾把 semantic source SHA 与 stamped render SHA 混比，工具误断言，不重放|`.local/s12/source-version-race/t12-doc273-source-version/result.json`|`ec17a0f99cdd4372ecec5b93a99bfa9c528137febb0ce6da75862a9fcb3c1dee`|
|T12 离线正确分类|仅离线证据和 PDF；source 与 render 各自匹配，无 DB/HTTP/业务重跑|`.local/s12/source-version-race/t12-doc273-source-version/tester-offline-digest-classification.json`|`8711b17dd5f971ca57e1b487fc6743f1df299aa3ae6a116d41a9c67ec197ea05`|
|T12 独立通过|真实两个 PG/RR 连接及同步 hook；A reader16 冻结 v2，B author9 正常更正提交 v3；A 原 native renderer 仍输出完整旧 v2 新件30；非 HTTP 并发|`.local/s12/acceptance/t12-independent.json`|`ebc047413d21de4742f079c06b107f38659927ea61131bf54049e651ce9cb570`|
|T07 真实客户端超时|0.75 秒实际 HTTP ReadTimeout；test-only 默认关闭 seam 延迟后仍原 native PDF；新 RO 确认提交后同 key 恢复，未重复治疗资金|`.local/s12/client-timeout/t07-http-timeout-recovery/result.json`|`9e9addc76a2d227093af381ed69299dd2a7e0168ebd80bbea548bf777acefd3e`|
|T07 独立验收|实际时序/普通请求/已提交原件57/旧原件保护；延迟是显式 test-only 受控条件，非实机打印失败|`.local/s12/acceptance/t07-independent.json`|`01da7c4beb1e84302d717603de8880e30ae54531fe77af82423b6cc9f1deed1b`|
|T02 正常合并原始结果|source patient254→本阶段新656，受控 request/confirm；原273作者/版本及未完604保留|`.local/s12/first-loop/s12-verified-merge-originals/result.json`|`4929b97279445391f195393e31e8c5c3041e5bb01452d0402d4c03068ca220fa`|
|T02 合并独立验收|1/30/57 前后 HTTP bytes 相同、授权按当前 canonical 源重核；新100 v4，旧原件不覆盖|`.local/s12/acceptance/merge-original-independent.json`|`c389e39c584a912ab2e69c1911c0a5a3d05ce253e66953d26d360812c5f4b7d9`|

原件关键映射（均为合成，不公开 PDF 正文）：

|原件|来源/前版|实际 PDF SHA-256|结论|
|---|---|---|---|
|1|doc273 v2，首 A4 两页|`ddb3962685c62ff531360c16edcf1e5ab9d9a829cd616ee81688e7b8a01ac8d1`|更名及最终合并后重印字节不变；旧排版不覆盖|
|30 v2|doc273 冻结 v2 / previous1|`529acd19b12c3658487400692f1715aac570dc5547c59239909accdd6fb7267e`|T12 A 输出旧快照；现源已 v3，文件无新更正 marker|
|57 v3|doc273 v3 / previous30|`51441047b8103b3a8a9bc80a064fcb767a3e24c5b1de5acb8befd51d663d6476`|T07 未知结果核实后同 key 恢复|
|100 v4|合并后新正常生成 / previous57|`537e8f3887c258a018a70d4eaa56bd032ec501c32f552aea3d47a40752a96e3b`|正常新版本、两页独立视觉；不重渲染旧件冒原版|

T12 实际命令入口：`../.venv/bin/python .local/s12/verification/source_version_race.py --candidate b160587d96ab54cb70deb7e6ff11d72bc6556146 --label t12-doc273-source-version`。原工具 exit2 与离线分类/独立 PASS 同时保留；不把后者写成原工具 exit0。T07 仅在主控明确绑定本阶段目标/actor/source/version 的四个测试环境项时生效，正常启动默认关闭。

## 财务、税务原件机制与指标回源

|证据 / 实际结论|层级与限制|私有路径|SHA-256|
|---|---|---|---|
|F2/T05/T11 新真实合成经济链|正常原生出账/付款分摊/退款批准及执行；HTTP PDF + 已提交读回，exit0；旧账链未重放|`.local/s12/first-loop/s12-economics-new-20261024/result.json`|`a4956847b51d8e8142b1591949b7d5ccf12b61a919e21bd5a8969e3c84793e30`|
|六财务指标逐项对账|正常14 HTTP × 三日期范围全分页/钻取 + 新 RO 原生原单/核销；保护投影显式排敏感列；exit0|`.local/s12/financial-report-reconcile/s12-econ-native-report-reconcile/result.json`|`53f2ca08d6a8bbd4530ab3f3a6932bf29c2722d1e760315fff4ae3f8c8d28729`|
|财务独立验收|四实际阶段含批准100未执行快照；部分付款/跨日实退/历史价格/原件逐页及账务核对|`.local/s12/acceptance/financial-independent.json`|`65c74ae13234c06d674ebf35462352693ed4438cba334c57e0788e63215b78d5`|
|非税票原件示例实际链|醒目 SYNTHETIC NOT TAX 有效 PDF；正常上传/授权下载/打印请求/none17拒绝，exit0；不得重传|`.local/s12/tax-original-loop/s12-tax-example-original/result.json`|`50064e440a11e012df080b6c9fa8e78147db43ea618f4e3f68b9db2ba8f160b9`|
|非税票机制独立验收|原上传 bytes 不变、原件关联、403/审计/unknown paper；真实票种和税务开票 NOT_RUN|`.local/s12/acceptance/tax-original-independent.json`|`e88a9dc47a3886fd84277a926dac2be441ac0d13c817c67eb55d1ca67a48d53a`|
|真实新物料消耗链|正常新 SKU/lot 收10→真实治疗执行耗2→量8；报表/CSV/钻取只计耗2排收10，非直接 consume 伪事件；exit0|`.local/s12/consumption-loop/s12-new-material-current-window/result.json`|`fba63bd203ea89c5c35f2cde037640261f1bf36b1d2f2566092a9da9546a170f`|
|库存指标独立验收|native event/move/line/quant/UOM/fee 与报表一致；临时导出权限已正常恢复；非真实物资/盘点效果|`.local/s12/acceptance/consumption-native-independent.json`|`2b80ee6286d00edb5447010938e022d742c269e6e287156634c914be711cd8d1`|
|加工/复诊待办实际链|新 PO127/line127，native incoming9，显式正常 send214 sent；label 无接收/入库副作用，exit0|`.local/s12/lab-pending-loop-v3/s12-lab-scoped-type-sent/result.json`|`236dd77b2dec08db4a35aa7d3571e9bff90a674858728401ef119fbe09d17b79`|
|加工/复诊指标独立验收|按真实状态归类与原单；实体发运/接收/入库/付款 NOT_RUN，旧件93冻结 draft 源不改|`.local/s12/acceptance/lab-pending-followup-independent.json`|`b942cb8db0ae2cc765270ce7a5ed33d66c9f54bdc18c2ffceaaa3975c93009a6`|
|加工/复诊 CSV 和钻取独立核验|实际授权导出及 native 原单链接；不以页面200代替 source 一致|`.local/s12/acceptance/lab-followup-csv-drill-independent.json`|`590cafe18ebe520f29ddbbf9f8bc10d3121fde89810273f29f8774fd06e65b98`|

新财务来源：patient521/522/523；bill72=740、昨日实际合成收500、尚欠240；refund3 批准100时实退0，今日执行100另有凭据。bill76/77=270/200，pay8=300 实际分摊270+30、欠170。bill79 确认600，后正常目录价620，历史费用及原件不变。新贡献：原出账1810、冲销100、实收800、实退100、当前应收1010、批准待退0；授权范围旧背景另列，未当新链补证。当前余额明确为查询时点，未冒历史截至日余额；按实际门店 UTC/单一币种1分别对账，不冒多币种换算政策。

## 临床、同意书、检查/处方/加工标签及视觉

## 文书集成、状态与逐页视觉

|证据 / 实际结论|层级与限制|私有路径|SHA-256|
|---|---|---|---|
|两区域真实链原失败|patient524/arrival517、care/exam 已提交、64/65/66 已生成；label409 为 PNG source 摘要不稳定；保留断点，未整链重放|`.local/s12/integration-loop/s12-two-area-live-chain/result.json`|`6185245715799d130daab998757852a3bf4a5345e06b2bc7b61cf5d4b1df7bd2`|
|标签原 key 续行|5cb 最小修复 semantic source 与 typed native PNG render 分离；只续214标签，原件93；exit0|`.local/s12/integration-label-continuation/s12-label-source-fixed/result.json`|`10f0b3bebae33b32019d92d655a26dd0e7a27a1089ff2c0777d798edca9b110e`|
|集成及 F4 独立验收|同患者两个区域：真实到店+1、唯一患者+1、确认执行+2；临床64/处方65/检查66/标签93，真实原生 PNG；无发药/接收入库副作用|`.local/s12/acceptance/integration-label-f4-independent.json`|`c378be85120584ee5a06f2cd0a676359c16f1576d4f8e1d47ae698ba354a81fd`|
|临床/检查/处方逐页独立视觉|实际 PDF 全六页亲看，字段/作者/状态回源；处方开立不冒实际发药|`.local/s12/acceptance/integration-three-pdf-visual-independent.json`|`6741fcaa01ac28c37f1888f1e0d57564c0de34a20cf4bebbaa5a4bee4decc580`|
|同意书/摘要前置拒绝保留|doctor9读取station配置被正确guard拒（未新建D1或模板） STOPPED；后续只按实际已提交源续行，不编造通过|`.local/s12/consent-summary-loop/s12-consent-summary-long-fdi/result.json`|`0a5cb70cf17841842555ea4765a410da2bc854289e65ae856e0150549c7e65c7`|
|同意书及完整/部分摘要正常链|D1+D2 complete409；draft/有发布合成政策 excerpt；D1 正常确认后 complete 新版本；上传 pending/受控核验/跨店不继承；exit0|`.local/s12/consent-summary-loop/s12-consent-summary-fdi-ready/result.json`|`0c54dcf092348599d06f61e585e1a40d43432ed82be10b7d92b8ba99f4301d55`|
|同意书/摘要独立验收|六样张22页全看：临床长表4、draft3、excerpt3、A4同意书4、80mm演示5、complete3；长中文/重复表头/页边界，非物理出纸|`.local/s12/acceptance/consent-summary-independent.json`|`113b0899d0f7707428626ca596345ab93dd5727014a623697ec3baf72f808f5e`|

同意书/摘要原件：94 长表；95 draft v1 → 96 excerpt v2 → 99 complete v3，保存所选来源集合及排除原因；97 A4 / 98 显式80mm演示配置同意书。所有六份在模板/政策/源变化后真实下载重印相同。合成模板仅测试环境审核发布；正式正文未批准不发布。上传件10/11仅合成软件核验流程，不冒真实签署或已临床告知。视觉记录的非阻断限制包括英文单词内折行、部分元数据跨页及 A4 同意书末页仅来源，均未改成“完美纸型”结论。

## 真实浏览器效果与权限

|证据 / 实际结论|层级与限制|私有路径|SHA-256|
|---|---|---|---|
|原四角色浏览器结果保留|3角色通过；doctor preview 后下载等待失败；不是凭单个 HTTP200 签通过|`.local/s12/verification/browser-effects-normal-effects-finance-new/result.json`|`221018d1e56e726e38f936cfb33dd48865a19d9eb3fba8d1cf595ffaf7c4e44b`|
|下载 pointer 诊断|正常9真实 hit-test/pointer/click/submit；等待实际 main navigation/load/fonts 后 GET 与 preview 两场景均下载旧件1；DIAGNOSIS_COMPLETE 非全业务 PASS|`.local/s12/verification/browser-pointer-settled-navigation-pointer/result.json`|`215e3fd8cc14fda28224db054fdfd8aba7a1d636d07b6a3bb00f44375cbe40d8`|
|doctor 专项正常浏览器补验|真实 preview/原件下载/日期过滤/新 arrival514 点击钻取，exit0；未重跑其他3已通过角色、未 generate/收费|`.local/s12/verification/browser-effects-normal-doctor-settled-navigation/result.json`|`f2bee68d66ff70b4b089d5c6ce7cb37a7d35f9510c84559d61a957ab9f111841`|
|浏览器独立审阅|四普通角色14/9/16/17，截图亲看、原件SHA及真实403；该阶段仅 scoped，后续缺口由其他独立回执接续|`.local/s12/acceptance/browser-independent.json`|`d86c54a1073b1beeaeac2ab1cb680bad314ddd03d95e949ee620df0fbf250d04`|

正常 HTTP 权限矩阵在31方法实际套件核医疗/检查/财务各自源读取×批量导出四组合；单份下载与批量导出区别；原生附件、缩略图、model binary、report直链、撤权旧页、切店/公司、CSRF、源版本及普通模板无害注入负例。原生 `/web/image` 无权时可200返回**精确原生 placeholder PNG**，验的是该 bytes 非原文件/非隐私图并且 `download=1` 拒绝，未把所有200视为通过。浏览器独立回执是截图/原始请求离线审核，未另冒其本次新数据库连接。

旧 browser tool 的失败、三个初始下载探针及一次 porcelain 工具前置误判均留本机；修的是 navigation 等待及后续 raw porcelain 解析，未改 core、浏览器安全、产品权限或 eval-submit/force click。真实 normal pointer 补验通过不证明每个旧等待失败有单一产品原因。

## 十六行覆盖与最终待办

|要求|本阶段适用软件证据|外部/最终限制|
|---|---|---|
|F1|首闭环、T12、consent-summary、merge 独立回执|正式完整病历/摘录政策未批准|
|F2|financial-independent；新740/500/100及270+200/300原生链|合成资金，非正式财务政策|
|F3|consent-summary、31方法 print_request/模拟失败|真实签署/设备出纸 NOT_RUN|
|F4|integration-label-f4、financial、consumption、lab-pending-followup|当前已实现指标语义，正式经营口径待审核|
|T01|22页同意书/摘要及其他原件逐页独立视觉|80mm仅明确演示，真实设备纸型 NOT_RUN|
|T02|更名首链、真实合并、模板政策变化、600→620及旧件重印|仅本阶段新对象变更，旧文件不覆盖|
|T03|实际 D1+D2 complete409→正常补确认→新完整摘要|不把过滤草稿称完整|
|T04|生成待签→上传 pending→核验/拒绝、跨店/版本政策|软件合成核验，真实临床告知 NOT_RUN|
|T05|真实新部分付/批准待退/执行退款/原件|真实资金 NOT_RUN|
|T06|31实际方法三类别权限矩阵/直链/批量；四角色浏览器|不以SOURCE或预拦截冒产品拒绝|
|T07|真实 ReadTimeout→独立确认提交→同key恢复；生成失败及模拟打印失败|设备失败仅受控模拟，物理故障 NOT_RUN|
|T08|内部 bill 与显眼非税票原件入口/字节/授权/审计|实际票种/真实税票/开票 NOT_RUN|
|T09|两区域一次 arrival、跨日实收/退与冲销、去重/源钻取|当前应收不冒历史截至余额|
|T10|限定安装/升级、注入及撤权；最终完整pre→六模块升级→post及独立核验 PASS|最终十六行总验收及同步另列|
|T11|270+200收300分摊270+30欠170；600历史与620目录|无税率/毛利/收入确认新政策|
|T12|真实双PG交错、当前门店发布策略及查看/下载/打印请求审计|并发是 MODEL 真连接同步 harness，非浏览器并发|

最终带数据升级实际限定六模块：`ydental_print,ydental_exam,ydental_settlement,ydental_lab,ydental_reporting,ydental_s12_test`。即时完整 pre 成功后运行，原生命令参数 `--stop-after-init --without-demo=all --no-http -u ydental_exam,ydental_lab,ydental_print,ydental_reporting,ydental_s12_test,ydental_settlement`；实际 child exit0 / ERROR0 / 无 Native，未启动 HTTP、未重跑业务。执行候选 `3127a575b1403ea072c950f1e1d4e79d8055141d`，产品/工具固定字节同 `5cb1e46fbe1e4243c7a292f64ecfd375afb3dce2`。

|最终升级证据|层级 / 结果|私有路径|SHA-256|
|---|---|---|---|
|冻结|限定六模块、完整候选绑定|`.local/s12/verification/freeze-final-s12.json`|`61bd48b5c55127b3697dd8a4f40a9d2a457e3d3da7a814328ddf2f17b672534c`|
|即时完整 pre|145业务表 / 13技术metadata表 / 37受保护附件；成功后才升级|`.local/s12/verification/upgrade-final-s12-pre.json`|`0bd8b9c45a383b7b67e99691d4794face785d9e4cef0e85d3348ff6b51284499`|
|实际升级执行结果|exit0 / ERROR0 / 无 Native；日志SHA另存result；非测试事务补证|`.local/s12/checks/final-s12-upgrade/result.json`|`5bdbd7ff8387a9f5e89432654335d20e37ef368ca7e96912c6b1e45e3801d9e1`|
|完整 post|实际已提交源/三原件族文件/版本/权限/配置/索引核验|`.local/s12/verification/upgrade-final-s12-post.json`|`04a210ab368e3f2473607ff97a57e2a503f976ef972d8f73a0b000dac184d131`|
|前后差异分类|业务及实际文件保持；仅原生技术时间与view备份刷新，见独立分类|`.local/s12/verification/final-s12-upgrade-diff.json`|`64d9bd1d1d48f4129b98648241acad095a01fa74cba0e20a44a0c32059272339`|
|最终升级独立回执|真实独立 RO/RR + 实际文件及差异核验；PASS，不冒全库物理零diff|`.local/s12/acceptance/final-s12-upgrade-independent.json`|`21dccf1a26b927820aa60ab94a6b3ac551bb1e04b2b1ae3cbfc9a31274818fd4`|

独立逐项分类：37附件及业务、PDF bytes、来源/模板/render事实、有效权限语义、配置及索引约束保留。25条 ACL 与1条 group 的差异仅 `write_date`；report/action/menu/module/paperformat 等为原生技术时间；view1591 的 `arch_prev` 是原生升级备份刷新，与有效 en_US arch 一致，有效 arch 未改变。没有把技术差异解释为全库物理零diff，也没有删除旧原件或未完责任任务。

**已完成**：最终十六行独立软件总验收610053fb…；**已完成**：正常push及远端Issue正文/closed状态/唯一最终回执逐字读回。

历史原始 17表 whole-row 哈希曾把 `account_move` 的 portal `access_token` 列纳入摘要计算，未输出该值；因此旧材料不能再声称“零认证列被选择”。原工具及结果保留，后续独立分类及新工具从 schema 排除 password/secret/token/credential/session 等列再投影；未搜索旧被拒账号，未借此重放业务或冒称发生原值泄漏。新财务/库存/合并独立核验明确敏感排除和 rollback/close。

所有独立局部 PASS 的边界保持；本索引不是最终独立总签。正式临床正文/发布政策、真实票种及税务原件、物理打印/设备、正式用户效果均单列 NOT_RUN/待审核，承接 #37；不 S13、不合并、不部署。S11 组合扫码需求差异继续待产品决定，标签未增加接收/入库副作用。

最终16行独立软件总签：`.local/s12/acceptance/final-16-row-independent.json`，SHA `610053fb6bfb995dbf3db6d29580bc6269d79d260bd33b361c21bbccafa2fae8`。TECHNICALLY_COMPLETE；16行适用软件PASS、当前未处置软件缺口0；正式临床/签署/税票/设备/政策/用户效果不包含在该PASS中，仍归#37。GitHub正常push/ref、正文/closed状态及唯一最终评论均实际读回，见下面同步证据。

## 最终正常效果复开

|证据|层级与限制|私有路径|SHA-256|
|---|---|---|---|
|最终升级后只读正常浏览器|normal9/14：273当前源、100原件下载537e…、新arrival514/bill72报表钻取；未生成/重付/重退；最终产品字节未变|`.local/s12/verification/browser-effects-final-after-upgrade-readonly/result.json`|`4af881e70f2b571c131678494b525abed4943577dc20718cee8560a205047b68`|

最终正常效果窗口：`.local/s12/verification/final-normal-effect-window.json`，SHA `3d6ca329d14329602b54e581eb75ee1fc6402f5a564ca5ed19b8b06d0602d3b7`。run20261024T025453Z-f8f22a02427f，source执行3127，loopback18411/cron0/测试flag全off，最多至2026-10-24约04:54UTC（或正常提前停止），scope原08:00不延；不保证永久在线。

## 最终正常同步

|证据|结论/边界|私有路径|SHA-256|
|---|---|---|---|
|升级后正常浏览器独立核验|normal9/14、原件100同537e…、过滤/新源drill；8截图实际亲看，无新增业务|`.local/s12/acceptance/final-browser-effect-independent.json`|`4802e6d3997dbc78292beeb7b53dd9a03fc23c33c16c74008794e3cdbc62df50`|
|首完整GitHub读回|a5c1ec4正常push/ref/报告正文相同；main e277仅路由；#36正文原要求保留/closed completed及comment6379065844逐字一致，共2评论|`.local/s12/sync/first-final-github-readback.json`|`c4b9d8e6ea72772d4d1969c23196acf708851750e5d3d9d718afe93403e08b3c`|
|公开增量预检|140新blobs、当前获准16秘密值及强模式0命中，无旧拒绝provider搜索/原始材料上传|`.local/s12/verification/public-scan-technical-report.json`|`ba458f78bf8b2c29d20943cab664e8cee88a16413e2b7559d32608ecfa087a0e`|
|main路由公开预检|仅文档路径/17blobs，同16当前秘密值/强模式0命中；没有产品merge|`.local/s12/verification/public-scan-main-final-route.json`|`640eae678d50104d7c86bf5d19383ec395c3b9a49463a451e05019ab8d336cf1`|

[唯一最终回执](https://github.com/Yredxin/YDental/issues/36#issuecomment-6379065844)原位记录最后docs-only报告HEAD与main ref正常读回；不为嵌入自身Git hash循环提交或重跑业务。当前软件技术与同步完成；正式启用/外部条件/用户效果仍归#37。
