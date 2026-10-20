# [CODEX-STATUS] YD-S11-FOLLOWUP-LAB-V1 / 1.0

## 2026-10-20 09:04 UTC：剩余闭环认证路径复核与停止边界

本次为本地只读源码/证据调查；没有数据库连接、业务写入、服务启动、测试重跑或产品代码修改。核验基线为原分支 `codex/s11-followup-lab-r1`、HEAD `698220d06c533257c1d4c0a3fe67d37d9532e79d`，产品测试候选 `789619fa76674caa1f8eab6db2eaf559847f16bf`。既有2项T18选择用例、14项followup notification模型测试及独立读回仍是最近测试结果，见08:58节。

独立认证可行性审查确认：新用户2466只完成Odoo原生密码校验，尚无 `ydental.access.session` 与Store2 server-bound scope；user10有medical权限但没有patient写权限。直接从裸ORM用 `with_user`、构造binding或复用已回显session key会绕过服务身份边界，不采用。新角色的正常业务调用要求HTTP adapter建立session；此前owned HTTP child以SIGSEGV退出的STOP仍有效，因此不重启服务、不重跑浏览器登录。task720已timeout进入verify，不重开、不takeover、不重放。

独立通知可行性审查确认，完整T05/T12 controlled sink需要新合成患者自己的confirmed treatment event、Store2联系字段及偏好、medical读权限和followup责任角色。`.invalid`地址/偏好只能作为明确合成测试数据，不能报告成真实邮箱所有权已验证或真实患者同意；controlled sink状态`accepted`仅说明内部测试sink接收，不等于患者送达。patient364的event417不能复用于其他患者，受保护event/task继续保全。当前14项通知回归没有直接覆盖controlled sink send handler，因此不将这14项扩大解释为受控sink端到端通过。

独立源码路径复核确认T08初始lab order派单要求关联confirmed purchase line；purchase group原生company ACL会使独立合成采购用户可见PO147–149。历史用户授权允许在S11 Store2合成采购用户授予 `purchase.group_purchase_user`，但仍严格禁止查询、读取、使用或修改PO147–149；未以该授权访问这些记录。目前没有可安全复用的义齿confirmed treatment source，也没有新角色正常服务scope。新合成前置对象授权本身不构成临床适应证或已确认采购链，不能把generic event417或task720改作义齿来源。

结论：现有证据与授权下可继续准备明确标记的合成患者、联系方式/偏好以及价目/合作/仓库前置，但没有已验证的HTTP-free普通用户session路径来完成患者、临床和自动通知闭环；Native crash STOP禁止启动新HTTP/browser会话，T08还受confirmed采购行流程约束。当前无法满足S11 M1–M5技术关闭条件，保持 **PARTIAL / IN_PROGRESS**、#35 **OPEN**。需要用户决定是否单独批准对既有HTTP child Native SIGSEGV做只读诊断及修复，并在新鲜准入后建立新的正常Store2测试session；未获决定前不触发HTTP/browser链。未启用真实供应商、短信、生产、push/merge/deploy；没有读取PO147–149。

## 2026-10-20 08:58 UTC：T18与通知模型回归、独立测后读回

续行核验：分支 `codex/s11-followup-lab-r1`，HEAD `81fe5cd2f836696a0e16898d973838e294579103`，产品/测试候选 `789619fa76674caa1f8eab6db2eaf559847f16bf`；开始核验时跟踪工作区干净。前序用户授权创建的Store2有限权限合成操作员仍为唯一新建角色，本轮不重复创建、不创建患者、不重放已完成的业务动作。无产品代码变更。

在目标scratch OID2144130、固定候选81fe5cd上运行两个隔离 `--stop-after-init` MODEL/ORM批次，未启动HTTP服务：

- T18免费返工/返修关联所选测试2项通过，exit 0、0 failures/errors。operation `.local/s11/operations/20261020T085331Z-t18-free-rework-isolated-tests/operation.json` SHA-256 `d383a28a4b6393ecadeb855ce13d994194901b0985aacc5e02b0e1abd8701491`；result SHA-256 `6c098df107f622ff8aa765ec417a7fbee83bd8c10c49cb0a5c1f1bc76394c267`；log SHA-256 `a920b706ade9480b182b132b099a99bc01bae8a549825f299ff4dfc563a6b3d4`。
- `ydental_followup_test:TestFollowupNotification` 14项通过，exit 0、0 failures/errors。operation `.local/s11/operations/20261020T085502Z-followup-notification-model-tests/operation.json` SHA-256 `c1bc21e17839d429bd8dda383b18af0aa890c485991d58bbab747c0c578f53ec`；result SHA-256 `91f5276519d3d2ee61c0e360bd02bd47965a9eafa8dee0d0f6a121556da35205`；log SHA-256 `fddca7529fa885372f989f7b0113ef8ed1ad31c85dc0f84be25b5887954fa9b2`。

独立测后只读读回 `.local/s11/verification/s11-model-test-suites-postrun-readback-81fe5cd.json` SHA-256 `8e53ccfc0d06296fc98c05ee10a771b413ea4c7709cae8b819fa7a662704c742` PASS；独立审阅者核对六项operation/result/log哈希。读回确认测试前后mail.mail、mail.message、mail.activity、mail.notification、SMS、notification job、queue outbox七项计数零增量，D/C pin和保护计数一致，只读RR事务显式rollback/close，服务停止。准入 `.local/s11/verification/admission-81fe5cd-post-followup-model-independent-ro-recheck.json` SHA-256 `f3f67253b43225309c9473a15e60d85b4e4cc1ac5e4b1a4732ef14ae01c16958` PASS，确认scratch身份、受限角色和外发关闭。

证据范围限于所选合成MODEL/ORM测试，不证明task720完整T18临床续行，不证明HTTP/RPC、浏览器或controlled-sink/provider端到端。此前task720的Native crash STOP仍生效，不重启或takeover。S11仍PARTIAL/IN_PROGRESS，#35 OPEN；F1剩余闭环、supplier_return适用场景、合法联系方式下的通知策略端到端、T18实际戴用/独立followup、最终影响面回归及独立总验收均未完成。不得虚构义齿来源、联系方式或患者偏好，不读PO147–149。无push/merge/deploy。

本次独立计划覆盖复核仅检查现有计划、状态文档和固定证据，不访问数据库、不运行操作或测试。确认已有有限证据包括：F1 followup265浏览器完成及followup272无contact人工兜底、T03/T04 signed callback HTTP、F4/T15部分ORM、T06/T16/T17真实竞争、T08 discard、T18返工前段；F2首次收费竞争中一方提交、另一方遇SerializationFailure，先独立确认无第二经济事实，再对同一幂等键作有界恢复并读回唯一invoice。F2证据不等于两路并发均直接成功。依据 [S11实施计划](../../execution/S11_IMPLEMENTATION_PLAN.md) M1–M5及技术结束条件，独立验收结论为 **NOT ACCEPTED / PARTIAL**：仍缺T08 supplier_return及合格来源/入库链、有效联系与偏好下自动通知策略端到端、受Native crash STOP约束的task720后续临床戴用/followup、F1其余生命周期、F4完整双店采购/收货/成本/患者费链、最终影响面回归及涵盖完整计划范围的独立最终验收。不得把历史分项PASS叠加成计划整体完成。保持#35 OPEN。

## 2026-10-20 08:52 UTC：合成Store2患者/前台授权角色

用户授权在开发/测试阶段自行认证，并在缺少可用角色时创建并授予权限。保持分支`codex/s11-followup-lab-r1`、HEAD `d02a2363269aed29d7abde419d461890326f7d56`，产品测试候选`789619fa76674caa1f8eab6db2eaf559847f16bf`。针对HEAD的scratch admission PASS：`.local/s11/verification/admission-d02a236-independent-ro-recheck.json` SHA-256 `d3d17a92a6e779ffd98ed0983462d439569c56bd42a10ddcd13b981ed6ed8cd4`；覆盖分支/候选、DB/OID2144130/cluster、受限数据库角色、保护计数/D-C、外发关闭、服务停止与18411空闲。

经原生`ydental.access.service._create_account()`、`_grant()`创建普通合成用户2466，Store2 membership3871 / employee2434 / company1。仅有`ydental_base.ydental_base_group_user`原生组，仅授予Store2 `patient:write`与`frontdesk:write`，其余本店自定义授权均为none；无manager/system/purchase组、无其他门店membership。随机密码只写入ignored私有文件；通过Odoo原生`res.users.authenticate()`凭据校验，返回uid2466。没有建立HTTP浏览器session或创建患者/临床数据。

操作回执`.local/s11/operations/create_store2_synthetic_patient_frontdesk_operator_d02a236.json` SHA-256 `e74b1ce4e8bb23c64448932157da770758a5a675e8106fad00c532af8a838156`；独立RO/RR提交状态读回`.local/s11/verification/store2-patient-frontdesk-role-d02a236-independent-readback-attempt5.json` SHA-256 `afbeef401b11671c365fa41e6d76705492eeba94b31b92b070cc821968fcf7db`，14项权限、身份、审计、认证、渠道和回滚检查PASS，独立agent交叉核对通过。

实际副作用须保留：`mail.mail`+1，新行2461状态`exception`；`mail.message`+6。该邮件未发送/未排队，SMTP为0，未重试或删除；SMS、mail.notification、activity、notification job、queue outbox无新增。因先前HTTP子进程SIGSEGV后已有Native crash STOP，未重启服务或执行浏览器登录；当前只有模型层正常凭据校验。受此边界影响的HTTP/browser测试保持未验证。S11仍PARTIAL/OPEN、#35 OPEN；无push/merge/deploy。

结论：**PARTIAL / IN_PROGRESS**
Issue #35：**OPEN**
同步：本次继续实施的代码和状态尚未推送；依用户要求只在 plan 结束时发布最终结果与说明。
计划范围：S11-A 复诊和通知可靠性 + S11-B 内部外加工，含补充输入 v1.1。真实外部通知、生产、合并、部署、S12/S13 均未启用。

## 2026-10-20 授权后续行：合成路径准入与登录阻断

用户授权继续调查并使用S11 scratch内的明确合成测试场景。针对HEAD `284984004f3527d823fd25efe036560af33782e7` 的fresh admission通过：`.local/s11/verification/admission-2849840-independent-ro-recheck.json` SHA-256 `20b37c69b2a38195f8b4a41f4c8950dc238922ea5836ad75272b844c4d13a7a9`。独立复核确认检查通过且为RR只读/rollback/close；无业务数据库写入。角色和资源预检只读确认Store2 user9可建患者/处理前台/医疗，user10医疗，user2318医疗/复诊；当前发布映射2/价源455是$7 care，不能充当义齿来源。slot1594仍有余量但不重用已完成操作。

本次没有创建合成业务对象。原因是patient-write/前台actor9只有曾用于既有本机服务session；该session key先前曾在工具输出中回显，依保全约束不可复用。user10/2318现有正常scope没有patient-write；不以代码直接构造新认证身份或superuser绕过。fresh admission与role/resource检查无生产或业务写入。首次只读检查因脚本使用不存在的slot状态字段失败并自动关闭只读游标；修正后结果通过。后续需要通过获准私有provider建立actor9新scope，或确认另一名真实认证的Store2普通用户具patient/frontdesk write。T08还需另有合格义齿临床场景、义齿价源/有效采购行和相应操作员授权；purchase group的company级ACL可能使受保护PO147–149可见，既有明确限制仍禁止读取、使用或修改这些PO。S11保持PARTIAL/OPEN。

更新到HEAD `e08e3a527f708c5caf34d755f408017eea7eb9a3`后重新准入PASS：`.local/s11/verification/admission-e08e3a5-independent-ro-recheck.json` SHA-256 `28b4df9812cb214b175327eca5fb3aabe801bca00aef4fc8881450bb08ee1f00`；新鲜角色/资源RR只读读回PASS `.local/s11/verification/store2-role-resource-preflight-2849840.json` SHA-256 `9da69b68a867d6d1a9f1f513d21b0f9880a9b08d47d1a8d1dc9009246edd4d7c`。两证据确认S11 scratch/OID和受限角色、保护计数/D-C、外发关闭、服务停止；当前Store2 patient/frontdesk写权限仅在actor9，但缺安全可用的新鲜认证scope。user10/2318的现存scope不具patient write。映射2/价源455为care而不是义齿，slot1594仍发布且有capacity；本轮没有业务写入或已完成测试。

独立审阅复核了上述两份证据的SHA、候选/分支、权限/资源及只读事务标记，确认准入和资源检查PASS；没有查询数据库或凭据。

## 最新续行状态（2026-10-20 08:33 UTC）

分支仍为`codex/s11-followup-lab-r1`；本节证据核验时HEAD为`210a2ca275caf6cff4e5256f186fbdebe210b814`，本次文档更新不改产品代码；已测代码/测试候选为`789619fa76674caa1f8eab6db2eaf559847f16bf`。789到210只有报告/状态文档变化；7bd到789增加报告和F4测试，没有产品源码变化。HEAD210独立fresh admission PASS：`.local/s11/verification/admission-210a2ca-independent-ro-recheck.json` SHA-256 `3d4a5d0921d7d9b3fc2c22d2bf450cfd87568053a2c801d7d4172929942a119d`。

经普通Store2供给服务一次发布slot1594：station2，2026-10-20 10:24–10:54Z，容量3、user10覆盖。独立RR只读读回PASS `.local/s11/verification/store2-slot1594-independent-readback.json` SHA `b398104f27bb8e4ffe06a43b59dd6efab4b7d5f7bc12a025e1872a7f4fb55f11`：policy305、容量和覆盖匹配，两条原生供给操作/event/audit唯一，224保护计数与D/C通过，无临床、采购、库存或通知副作用；没有读取PO。首次脚本启动误用系统Python，在数据库连接前导入失败；改用项目`.venv`后唯一业务操作exit0。

Store2 source preflight证实event417是已提交、有效且未被复诊使用的confirmed treatment，actor2318具本店medical/followup权限；独立证据 `.local/s11/verification/event417-followup-source-preflight-210a2ca.json` SHA `f5695bf7514da4dd0e60180570702e7f716fdd9bf6b51f4a309ff6441336632a`。patient364无已验证联系方式/偏好，因此按原生规则不会排自动通知job。为验无联系路径，actor2318从正常浏览器工作台对event417只提交一次post_visit，创建followup272；POST303、刷新GET200。receipt SHA `0e43dd055e67f8a561956c44b7ac9adf6def435b0e4807332f57591dcb6ec245`，stdout SHA `8ea2f76f08cdf7e563d1bb7b4dc28936b6b7794a1133466d5f4be9799fc15fa3`。独立RR读回PASS `.local/s11/verification/followup272-event417-browser-independent-readback-finalized.json` SHA `a23f9cfd1075933ea19b44f4be72052475fc78506895da0622621b0ee0cd0bd2`：状态`to_notify`、内部activity恰1、contact/job=0；followup265/event416未变；增加1条内部chatter `mail.message`，没有邮件/SMS/outbox或外部送达。

执行期间的一次本机私有session文件核对发生了未脱敏工具输出，短暂回显一个scope key值；该值未进入仓库或业务操作收据，后续不会复述或复用。私有运行配置保持原状，此事项列为本地会话凭据处理风险，未推送GitHub。T05/T12的无contact人工兜底分支现有浏览器/持久状态证据；policy controlled sink的自动派发、免打扰/退订/日上限完整端到端仍未完成，因为没有已验证患者联系渠道，不能伪造联系方式或同意偏好。合格义齿来源、supplier_return、F4完整采购/接收、T18返工/返库与最终影响回归/独立计划验收仍未完成；#35 OPEN，无push/merge/deploy。下方按时间记录的历史进度保留当时事实；如与本节或覆盖矩阵冲突，以本节及矩阵当前候选为准。

### 本次只读覆盖调查

独立覆盖审阅未运行测试、未查询数据库、未读取PO147–149。F4/T15候选789619f的真实ORM资质审批/双店隔离测试已有通过记录及独立post-test读回，因此不重复执行。代码和测试中没有supplier_return实际业务链；现有event417是generic care，不能转作义齿临床来源。T18有隔离事务合成闭环用例，但task720已超时进入verify，不能重开/重放；隔离用例不能替代task720实际后续。T05/T12已有无联系路径的浏览器持久状态证据，不能据此声称controlled-sink自动派发通过；自动路径仍需合法联系/偏好。此次没有发现可安全推进以上真实闭环的新来源，因此这些范围仍保持NOT_RUN/PARTIAL。

## 2026-10-20 followup265 attempt12：浏览器完成与独立状态读回通过

候选/HEAD `f2e159e0093f2cde0af29c7117ab6780b8a13fa5` 的fresh admission、followup265/event416专用preflight和独立静态审查均PASS。preflight `.local/s11/verification/followup265-preflight-f2e159e-attempt12.json` SHA-256 `a591ff56e3697b5c9a6f8e167044a2fca2ba7ab1654c902d43b7655bd7e3dbe6`；attempt12 receipt `.local/s11/operations/followup265-completion-browser-attempt12.json` SHA `b97b653da9764264fedc3bd05f6f3ba37a77b29ab0caf2c0a1443f6ab44bf9d8`。actor2318在Store2展开“Complete from actual treatment”表单，选定event416并只提交一次；HTTP返回303，workbench刷新GET=200且followup265不再出现在开放列表。页面无JS错误。此前attempt7–11的不可重放收据/失败与只读读回均保留。

独立RR只读/显式rollback/close持久状态验收PASS `.local/s11/verification/followup265-attempt12-independent-readback.json` SHA-256 `f2c5587b6b504c832855a8f93ceae14de02cb89302452d2355c102f59da661f7`：followup265=`done/seen`，唯一关联event416/execution536；event为同Store2/患者364的confirmed treatment，执行为handover；恰一条actor2318/store2的accepted `followup.complete` audit；contacts和notification jobs为空。已有activity232未改变。页面读取审计38条及正常session/device记录保留。保护计数增加仅包含访问审计/session与1条`mail_message`；独立检查确认这条message为本次followup状态变更生成的内部tracking message，mail_outbox仍10，SMTP/SMS关闭、无外发。D/C pin匹配；service STOPPED/18411空闲；未查询PO147–149，也未重试。

此结果完成F1中followup265从人工联系至实际接诊关联的浏览器操作及已提交状态验收。S11仍PARTIAL/IN_PROGRESS，#35 OPEN；通知HTTP回调/策略端到端、适用supplier_return、F4双店E2E、T18后续、最终影响回归和独立总验收仍待完成。无push/merge/deploy。

## 2026-10-20 T03/T04：signed provider callback HTTP

在 `7bd9f0d09173288ee748c56227501f10be9329fe` 新增 `HttpCase`，针对`/ydental/followups/provider-callback`经真实Odoo test HTTP处理器提交raw JSON和HMAC header。单项定向HTTP测试 exit 0、1 post-test、0 failed/error：合法签名返回accepted/delivered；相同event第二次返回duplicate且只留一条receipt；错误签名返回403；无transport/dispatch调用。operation/result/log `.local/s11/operations/20261020T080614Z-followup-callback-http/`，log SHA-256 `9ed5d5b101babf5f23975b81d66e044f2e85ae6c465ce620a861db2d09921f0c`。独立静态审查、compileall和ruff均通过；fresh admission见`.local/s11/receipts/s11-admission-7bd9f0d-20261020T080601Z.json`，SHA `d67e422953b5fb63fe4c0467ae581133930596a24671247852752ac9867b8322`。

独立post-test RR只读/rollback/close读回PASS `.local/s11/verification/followup-callback-http-7bd9f0d-posttest-readback.json` SHA-256 `2a78569c12f53579ad3ec6610b0c7c76bf399ea733fc7710855056a8e337ffd3`：224保护计数零增量，D/C和模块集匹配，测试合成store/job/callback/audit及测试secret均无持久残留，mail_message/mail_outbox仍1080/10，SMTP/SMS关闭，service STOPPED/18411空闲。此仅是callback HTTP路由/鉴别/幂等验收，真实供应商仍NOT_RUN，策略端到端仍未完成。

## 2026-10-20 F4/T15：真实ORM资质与双店合作隔离回归

候选 `789619fa76674caa1f8eab6db2eaf559847f16bf` 新增 `TestLaboratoryGuards.test_vendor_qualification_and_cooperation_use_real_store_scoped_records`。测试在隔离事务内创建同公司两个门店、两名普通仓库用户和一个带合成资质附件的供应商；用原生审核动作批准资质，再由各店scope内的用户分别创建合作。断言两名用户的`_access(write=True)`只解析到各自门店、跨店缺少合作时拒绝、两条合作均建立后记录仍按门店隔离且第二店供应商校验通过。定向测试exit0，1 post-test、0 failed/error；operation/result/log `.local/s11/operations/20261020T081641Z-f4-real-cooperation-matrix/`，log SHA-256 `d7052e73305485959ab978ab2e22459108a8abe5bcc0aa42e9c178c37477ce8e`。Fresh admission `.local/s11/verification/admission-789619f-independent-ro-recheck.json` SHA `c4bcca927a630ee0dfa5bb2078718bb6b5239ef9498cf000856ac036b38a0fa8`。

独立post-test RR只读/rollback/close验收PASS `.local/s11/verification/f4-real-cooperation-789619f-posttest-readback.json` SHA-256 `16c47dca90f2888aa1f4621d6c294dbfede9c4f1d126cf408677060cd78fe67f`：保护计数未降、D/C与模块集匹配；测试store/users/vendor/cooperations/audit/internal expiry jobs及mail/activity/outbox无残留，外发provider关闭，service STOPPED/18411空闲。没有读取PO或创建采购/临床对象。此用例将F4/T15资质和合作证明从mock模型断言提升到真实ORM/原生审核与用户store scope，但仍不覆盖开单、收货、成本/患者费闭环。

测试日志记录3条auth_signup “Signup email sent”提示及一次Odoo测试filestore GC `3 checked, 3 removed`。独立数据库读回确认无新增mail/message/outbox，SMTP/SMS/provider均关闭；没有证据证明邮件外部送达。Odoo test cleanup仅处理filestore checklist中未被`ir.attachment`引用的文件，但operation没有保留被删路径或hash，因此最终交付列为测试清理限制，不推断文件逐项来源。

## 2026-10-20 候选2afd515验证进度

当前仍在原分支 `codex/s11-followup-lab-r1`，修正测试payload后的HEAD为 `353e0fa3f99bfc6e7c02fe952a724d0dbc0ea8bd`，实现候选仍为 `2afd5156c9b9b4e9a3a778df9b04d6f001f309f4`。353 fresh admission PASS，证据 `.local/s11/verification/admission-353e0fa-readonly.json` SHA-256 `3598bfe0c9acb35e5eb7dec107252a1cafea825910209bf5b4484c7885527534`；包含scratch身份/受限角色、224保护计数、D/C、模块集、外发关闭及服务STOPPED/18411空闲核验，未读取PO147–149。

三组定向回归均exit 0：32项临床/队列回归 `.local/s11/operations/20261020T073544Z-clinical-queue-expiry-handover-regression/`（日志SHA-256 `a808911cd9a3b1018a5c3ad9989034af64a0a97e2608913c5a39d7b043e7ed5e`）、followup生命周期1项 `.local/s11/operations/20261020T073625Z-followup-completion-regression/`（`31e7550a5b39fbb109da4508f44d7b4faba6e53aeb292807e7fa949ec707a82d`）、无frontdesk医疗角色HTTP工作台1项 `.local/s11/operations/20261020T073639Z-followup-http-medical-without-frontdesk/`（`155f81268665033a52526b75aa6cfb8891085d680f992765b52f1b2eec28619f`）。HTTP日志记录`GET /ydental/followups`=200；生命周期用例执行原生reservation reschedule并验证新slot DTO。独立post-test只读/rollback/close读回PASS `.local/s11/verification/posttest-353e0fa-readback.json` SHA-256 `b086cfccc26741735facb61b42b2655bcc027bea3e05978095ae38144945ef3d`：224保护计数、D/C、模块、SMTP/SMS及mail/outbox与测试前一致，owned服务STOPPED/18411空闲。之前2afd运行因测试调用参数错误报1 error的失败记录及独立读回保留；修复已在353e0fa提交，不计为PASS。

候选e373上followup265/event416 fresh只读资格预检PASS `.local/s11/verification/followup265-preflight-e3732fd.json` SHA-256 `380544dc4331f68394055bbbbbf4e15ea8e8b3772f5be3705cbca451b7f4ba7b`：followup265仍to_notify且未关联预约/完成事件/执行，没有contact/job；event416仍是同Store2患者治疗事件，execution536已handover结束、文书507关联一致；actor2318仍为active internal user且有medical/followup写权；无已有链接或外发，预约来源校验正常，服务STOPPED/18411空闲。该只读预检在状态提交前，后续需对新HEAD重新admit并fresh preflight。确认后可使用新attempt ID做一次真实浏览器完成；attempt6仍`do_not_retry`且不重放。#35仍OPEN、无push/merge/deploy。

## 2026-10-20 followup265 attempt11：折叠表单中的选择器不可见

attempt11通过认证并打开Store2 access/workbench；唯一complete marker定位至正确表单，但表单位于`details`中且尚未展开，选择event416时Playwright报不可见超时。未发生业务action POST；attempt11 receipt为`OUTCOME_REQUIRES_READBACK`/`do_not_retry=true`。独立RR只读/rollback/close读回PASS `.local/s11/verification/followup265-attempt11-independent-readback.json` SHA-256 `b34316e6c38df7ddc6cc15f57f903dfd92e6045756d3ab9e5cc7724ac17f3d95`：保留login/store及16条accepted source.view审计、两条设备记录；保护计数仅access_session+1/access_audit+19。followup265/event416、contacts/jobs/完成链接、D/C和外发/mail计数不变；服务STOPPED/18411空闲。后续全新attempt应点击对应details summary展开，再进行一次性表单提交。

## 2026-10-20 followup265 attempt10：工作台GET通过、表单定位停止

attempt10使用新准入和资格预检，HTTP认证后Playwright成功GET Store2 access和followup workbench（均200）；由于`form.filter(has=...)`没有唯一匹配完成表单，在任何业务action POST前停止。receipt为`OUTCOME_REQUIRES_READBACK`/`do_not_retry=true`，attempt10和锁不重用。独立RR只读/rollback/close读回PASS `.local/s11/verification/followup265-attempt10-independent-readback.json` SHA-256 `62cb4bc31607c3aa2fce8fb06e17367aedc9a237bfb2266f81683e23485ad775`：followup265/event416、contacts/jobs/completion link、D/C和outbound/mail计数不变；保留登录/范围切换、两条设备记录及16条accepted source.view审计；服务STOPPED/18411空闲。接下来修正为唯一操作input locator并用其ancestor form精确定位，验证followup_id=265及event416选项，随后全新attempt ID/准入/预检。

## 2026-10-20 followup265 attempt9：access页面文本断言停止

attempt9经HTTP认证成功（uid2318）并读取`/ydental/access`=200；脚本因用英文响应正文查找“Store 2”未匹配，在Playwright打开前安全停止，无followup workbench GET或completion POST。receipt `.local/s11/operations/followup265-completion-browser-attempt9.json` 为`OUTCOME_REQUIRES_READBACK`/`do_not_retry=true`，owned service `20261020T075100Z-be97da6ffcdc`已正常停止。独立RR只读/rollback/close读回PASS `.local/s11/verification/followup265-attempt9-independent-readback.json` SHA-256 `531bfc03b3672b3d55d264dcd81a6fb0ba0cf252c8d5bdfe9d495f0c40b68b8d`：保留session3925、device82及三条accepted登录/范围审计；保护计数仅access_session+1/access_audit+3。followup265/event416、contact/job/完成链接、D/C、外发计数不变，18411空闲。错误是普通本地化断言，不是业务拒绝；后续新attempt应删除该文本断言，交由浏览器检查Store2选择器。

## 2026-10-20 followup265 attempt8：认证后等待超时

候选1ad7a1f上的attempt8使用正确的CPython3.12 Playwright/greenlet导入顺序，普通用户登录成功，但Playwright等待`/web` URL匹配超时，尚未访问Store2业务工作台，更未提交followup完成POST。receipt `.local/s11/operations/followup265-completion-browser-attempt8.json` 标记`OUTCOME_REQUIRES_READBACK`/`do_not_retry=true`，attempt8不重放；owned service `20261020T074613Z-4ed754dd6c47`已正常停止。独立只读读回PASS `.local/s11/verification/followup265-attempt8-independent-readback.json` SHA-256 `39bebe854a4e128730bf5d01f5e5cc316c56599201c0f779fc22cd2dbeb871fc`：登录成功产生session3924、device81和三条正常认证/范围审计；除这些认证副作用外保护数据未变。followup265仍to_notify/unlinked，event416未变，无contact/job/完成链接，D/C及SMTP/SMS/mail/outbox计数不变；运行日志无access或followup应用路由，服务STOPPED/18411空闲。

下一attempt需使用独立新ID及fresh admission/preflight；可沿用已验证的普通登录HTTP/RPC认证，核实其uid严格为2318并将该session cookie交给Playwright，然后直接访问已授权Store2 access/workbench页和提交一次表单。此前attempt7导入失败原件保留且不重用。

## 2026-10-20 followup265 attempt7：浏览器运行时导入失败

候选506b019上的一次性attempt7在Playwright导入`greenlet._greenlet`时失败；浏览器未登录，没有followup workbench GET或completion POST。运行 receipt `.local/s11/operations/followup265-completion-browser-attempt7.json` 标记`OUTCOME_REQUIRES_READBACK`，attempt7和锁均不重用。owned service `20261020T074259Z-aa6268eeb9c2`已停止。独立RR只读/rollback/close读回PASS `.local/s11/verification/followup265-attempt7-independent-readback.json` SHA-256 `af4ace34f0ee301968d0625eb94e7da9b2c21e69a508a873ecb1e14b02ed9446`：仅有预期未认证`/web/login` GET；无认证session、访问审计、设备记录、复诊动作；followup265/event416和contact/job/完成链接未变；保护计数、D/C、外发及mail/outbox未变，服务STOPPED/18411空闲。

根因是运行脚本把私有browser_runtime放在site-packages前，导致CPython3.14的greenlet扩展覆盖`.venv`内兼容CPython3.12的greenlet。后续独立纯导入核验应采用先加载venv site-packages、再加载browser_runtime的顺序；对attempt7不重试，后续只能使用fresh admission/preflight和全新attempt ID。

## 2026-10-20 followup265 attempt6：已定位并保全的GET拒绝

候选 `2d87dba95b90c3601b558bbcda3f37975e514842` 的fresh admission与followup265/event416前置读回曾通过，但新的单次browser attempt6在唯一工作台GET遇到403，完成POST未发送。receipt `.local/s11/operations/followup265-completion-browser-attempt6.json` 为`OUTCOME_REQUIRES_READBACK`、`do_not_retry=true`；owned run `20261020T072753Z-f01909785bf8`已正常停止。独立RO回读 `.local/s11/verification/followup265-attempt6-independent-readback.json` SHA-256 `76182b60ff97cb951ba4effdc858952d7af94927b3f09d3b7ba42e6794f22f0a`确认followup265/event416没有业务变化；仅有本次预期认证session、设备记录和3条认证/门店审计，外发0，保护表与D/C保全通过。

日志显示工作台403原因不是ACL而是attempt5修复中错误假设claim source key始终等于task ID。独立RO核实同店entitlement475/claim493在合法重排后source key为`475-v1`，所关联task758为cancelled；另一有效entitlement485/claim503/task799使用task ID `799`。该 source key格式来自原生 `_reschedule()`（`entitlement.id-v<prior version>`）。当前dirty修订改为按entitlement精确关联任务，校验初始ID或精确重排key；任何其他不匹配capacity选项只被省略，不放宽权限或中断整个工作台。S11生命周期测试现以原生服务执行reservation reschedule并核对新的slot DTO；该修订尚待候选冻结、fresh admission、测试和独立post-test读回。attempt6不重放；F1后续新尝试必须使用新ID。

## 2026-10-20 续行：followup265 完成前置核验

fc0测试及独立post-test读回之后，状态/报告提交为 `e73bcd72535d651e9662db2f08cb6438472ec8cd`（工作台实现候选不变）。e73 fresh admission与followup265/event416同一只读事务预检PASS：`.local/s11/verification/admission-e73bcd-readonly.json` SHA-256 `eb2cddd966829cfcba5c521ee7113a5d96cc8a89d6e7315c060a1673d148a37d`。RR READ ONLY显式rollback并关闭；目标、受限角色、模块/外发、224项保护计数和D/C pin、服务停止均通过。

读回确认followup265仍`to_notify`、无预约/完成事件/执行、无联系记录或通知job；actor2318仍为active store2内部用户并具followup与medical写权，patient364当前store2关系存在。event416为confirmed treatment，执行536于2026-10-20 05:50:14 UTC handover结束，document507、patient364和store2链匹配；原生`_complete`允许该事件，但要求明确勾选无预约关联并填写非空原因，不要求文书状态confirmed。该次只读预检未触碰PO147–149、未写数据库。attempt5只有workbench GET 403、无completion POST，不能重放；在状态/准入按新HEAD刷新后，新的浏览器attempt6才可使用该前置事实。

## 2026-10-20 最新续行：工作台权限修复候选 fc0f614

分支 `codex/s11-followup-lab-r1`，候选 `fc0f614f2af90c4e0714ed6c9db5ae0bb5918175`，core仍锁定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。`ydental.intake.service._followup_reservation_options()` 限定当前store、授权patient relation、reservation entitlement和精确引用的claim/slot；校验reservation pool、来源task/source_key、store/patient/entitlement关联及held→held、started→consumed状态，只返回最少展示DTO。followup controller/template不再直接读取受保护capacity记录，未扩大ACL。患者canonical关系批量解析保留旧ID→合并链最终患者当前门店关系，并检查循环和缺失记录。

候选fc0 fresh admission PASS（`.local/s11/verification/admission-fc0f614-readonly.json` SHA `73f5e0f0fee0e8608990155468a0b4a1d394e2f2244584941ad9bb781b4dae68`）。测试结果：32项临床/队列回归、1项含原生A→B→C合并链和held/started预约DTO的followup生命周期测试、1项无frontdesk能力医疗角色的HTTP工作台测试均exit 0，0 failures/errors。私有运行目录和日志SHA见 `CURRENT_TASK.md` 当前快照。曾对S04专用`ydental_patient_test`选择器跑出0 tests，未计PASS且未在S11安装/绕过其pre_init约束；最终A→B→C覆盖已迁至已安装的S11 followup生命周期测试并在fc0通过。

独立测试后读回PASS：`.local/s11/verification/fc0f614-post-test-readback-attempt2.json` SHA `b988064fd4c4c869295a7ff28e8474c8975e114b838f8b665b2266239a8010f5`。RR只读/rollback/close确认224保护计数不变，D/C pin和安装模块集一致，SMTP/SMS为零，服务停止且18411空闲。首次post-test读回FAIL原件 `.local/s11/verification/fc0f614-post-test-readback.json`（SHA `282890ebbb7a64cbbe6e22fda812b91488e65a05db6714fb90046c328c0beac2`）因预期4条而本次真实3条；保留后由第二独立读回对三条日志/退出码和保护事实完整复核。

attempt5验证了followup265在未修候选下的页面403；独立读回确认没有completion POST，attempt5不可重放。fc0覆盖该权限路径的HTTP测试已通过。下一步需在同步当前状态文档并对新HEAD重新准入后，为followup265执行新的只读资格核验，再决定是否开展全新浏览器attempt6。计划仍PARTIAL/OPEN；task942固定care映射和event417/doc508不支持义齿临床场景，不能当作T08义齿来源，也不查询PO147–149。通知回调/策略端到端、适用supplier_return、F4双店E2E、T18后续、F1完成、影响回归和最终独立验收仍待完成。

## 2026-10-20 续行：followup 工作台容量权限修复（实现待测）

当前分支仍为 `codex/s11-followup-lab-r1`，HEAD `f2e320b78cf11e912f6ea129f6ddb3754dc02090`；下述实现/测试增量尚未提交，工作树有7个tracked文件改动。候选未冻结，也未运行该增量的数据库测试。`git diff --check` 与Python 3.12 `compileall`通过；独立代码审查未发现确定安全、数据流或ORM缺陷。

attempt5实际登录成功，但 `/ydental/followups` 返回403：工作台模板读取当前预约所关联的受保护capacity claim/slot，触发原生ACL拒绝。独立只读/显式回滚读回证据 `.local/s11/verification/followup265-attempt5-independent-readback-v2.json`（SHA-256 `8def40fc69a105579ee32e0ee7c3a2ee347f08a8e50471ae90d4748b24f9421c`）确认没有提交followup完成动作，followup265仍`to_notify`、event416未变，也没有contact、notification job/outbox、邮件或SMS副作用。登录的用户日志、设备日志、session及三条认证审计真实存在并予以保留。原attempt receipt与锁不重用。

本次改动在intake服务中以当前授权关系和同店reservation entitlement为边界，只沿精确claim/slot引用做受限读取并校验来源、任务、门店与状态，controller/template只传递患者ID、entitlement ID和slot start DTO；未扩大访问组。另将患者current relation lookup批处理，避免workbench每个patient重复查canonical chain。新增模型层held及started/consumed预约选项断言、合并别名A/B→C解析断言，以及无frontdesk能力但有医疗只读/复诊写能力的HTTP工作台测试。尚未证明带真实预约选项的HTTP渲染；需后续实测和独立状态读回。

task942的当前T08只读评估显示固定mapping2/catalog2属于care、event417/doc508没有义齿临床语义，且entry431/task759先排队；因此不把现有来源改作义齿采购，不访问PO147–149。S11仍PARTIAL/OPEN，通知HTTP/策略、T08适用外加工分支、F4双店端到端、T18后续、F1完成动作、影响回归及最终独立验收仍待推进。

当前续行快照（2026-10-20 06:50 UTC）：保持原分支 `codex/s11-followup-lab-r1`，HEAD `e65c078a4807b3ef6842a7df8d991c9aa861cd23`，产品addon候选 `2df07373fa5257589115d39f4354dcd4c25c2997`；分支ahead 110，未push/merge/deploy。e65为状态/报告文档提交。最新HEAD准入 `.local/s11/receipts/s11-fresh-admission-e65c078-20261020T064816Z.json` SHA `9c86da547cfd573ca5b744aabf1add91d17c1d6a3403b1ac27ec585df016e420` 经独立review PASS；receipt SHA亦绑定在当前 admission。

用户明确授权给专用S11 Store2合成采购测试用户加入`purchase.group_purchase_user`，接受原生ACL可见PO147–149；仍禁止查询、读取、使用或修改这些PO。采购组尚未授予。T08来源event417/doc508/fee415的当前只读适用性证据 `.local/s11/verification/t08-source-417-preflight-5e961f7.json` SHA `2f7898802139626724125eed4c1cd0a9d806a31a124b8bc35768a66449d36a79` 确认关系正确、无既有lab order，但原记录只有generic synthetic continuation；无义齿产品/订单行/材料语义，不能作为义齿外加工临床来源，禁止据此直接建单。

只读路由评估发现task942为pending/store2/patient364，固定mapping2/catalog2是`S10 independent C synthetic care`、kind=care。原生continuation可以创建独立新文书/治疗event且保留event417/doc508，但必须新鲜核对task/到店/资格/价格并确认该固定映射适用；不能编辑task快照。若不适用，应从另一个正常合格的合成临床任务开始。临床文字需明确标记为合成测试，并清楚记录义齿适应场景；不得由系统代码的宽松校验推导临床依据。未查询PO147–149、未写DB。

当前续行快照（2026-10-20 06:45 UTC）：原分支 `codex/s11-followup-lab-r1`、HEAD `5e961f7a36dac100351ef6b4d3e2d1c6a56ef758`，产品addon候选 `2df07373fa5257589115d39f4354dcd4c25c2997`。用户已明确授权给独立S11 Store2合成采购测试用户加入 `purchase.group_purchase_user`，接受原生ACL使PO147–149可见；仍禁止查询、读取、使用或修改这些PO。该组尚未实际授予，执行计划将采购用户与医疗/仓库操作用户分开。当前候选新鲜准入 `.local/s11/receipts/s11-fresh-admission-5e961f7-20261020T064523Z.json` SHA `e915cd4f522300734144a1b37149ebc2232f2a4fd7ae663d7ba5769b4ac66ea6`，经独立review PASS；范围包括受限scratch身份、97个已安装模块、外发关闭、S10保护计数及D/C pin。SMS guard模块已安装，代码仅阻断厂商记录SMS composer发送/排程。

获准的单次HTTP调查 run `20261020T064355Z-8dcdb386fe49` 只完成actor2318登录、`GET /odoo`与`GET /web/webclient/load_menus`：200、200、403；owned child正常exit0，服务STOPPED/18411空闲，未复现SIGSEGV。faulthandler没有fatal crash栈；日志中的`Stack`是Odoo导入测试框架路径触发的`stack_info`。请求记录 `.local/s11/operations/http-faulthandler-diagnostic-5e961f7.json` SHA `29eb324ac74bc2626f6bfa2757c8490e81bf495b9a6a5b10b1200b30f216cf45`；server log SHA `f63aeaa9b6b374f45293a1e7a7c1ccbfc2444cebfed8ef159e9ab414a62cd17d`；exit receipt SHA `d5320f258815c9c29c9ed3d32ae5aaef03678edef345f753da8628279a7539a3`。独立RR只读、显式rollback/close结果 `.local/s11/verification/http-faulthandler-diagnostic-5e961f7-independent-readback-reconciled.json` SHA `6011d2c19ca04ea9892c10c1315c85230f8533e2fa9da56655ab652aef713c76`确认只有正常登录device log、session和3条认证/门店切换审计，业务followup/lab/purchase/财务无变化。403不是HTTP E2E PASS；SIGSEGV根因未定，不再复现。

当前续行快照（2026-10-20 06:38 UTC）：分支 `codex/s11-followup-lab-r1`，报告修改前文档HEAD `24f9b63664db01f4137813f923340d9d51ae8cc8`，最近实现/测试候选 `57a3fcbc5d093de92f5f2aa13423ca3bfcff238d`，产品addon候选 `2df07373fa5257589115d39f4354dcd4c25c2997`。候选既有32项临床/队列post-tests、1项followup regression及新增F4单项MODEL regression通过；F4独立post-test保护状态读回PASS（范围有限）。当前F4资质/合作/任务只读快照见 `.local/s11/verification/f4-vendor-current-readonly-08a1050-attempt2.json`。HEAD08a及24f9为文档增量；私有runtime/admission仍绑定57a，未为只读文档HEAD重绑准入。#35仍OPEN；无push、merge、deploy。

## 当前候选与运行边界

- 分支 `codex/s11-followup-lab-r1`；最新实现/测试 HEAD `57a3fcbc5d093de92f5f2aa13423ca3bfcff238d`，本轮报告和状态文档待提交；产品 addon候选为 `2df07373fa5257589115d39f4354dcd4c25c2997`。产品候选已通过32项临床/队列 post-tests、1项followup regression；固定HEAD另通过F4 store-scoped合作MODEL回归1项，并fresh admission PASS：`.local/s11/verification/admission-57a3fcb-independent-ro-recheck.json` SHA `76813c58c3c2c86cd29c241325630682c7415fc93a24fe01e738c568552622cf`。锁定 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。较早候选 `caabf67` 的62 post-tests、旧 `98412e7` admission及前述报告内容保留作历史证据，不代表当前 HEAD 的运行态准入。分支未推送；无merge/deploy。
- 使用的目标为指定 scratch OID 2144130 / cluster `7694897083368259627`。S11 runtime、admission 与 launcher 位于本机忽略的 `.local/s11`，mode 0600；本机凭据不进入 Git、聊天、报告或请求日志。S10 main DB OID 2144129 未安装或写入；未知 8069/PID42433 未操作。
- launcher 在本候选启动过 owned Odoo 服务并执行过只读 HTTP/RPC 和浏览器工作台检查，随后正常停止。外部 SMTP、SMS、供应商、支付均未启用；本地受控 sink 只代表内部测试受理，不代表患者送达。
- 首次安装中的依赖和 Odoo 20 Registry 导入问题已在普通开发中修复；保留两次先前失败及只读保全记录，不覆写历史。当前候选成功完成带数据模块升级和测试，详见下文。

## 已取得的候选匹配证据

- **SOURCE/PURE：** addon、权限、XML、launcher 与依赖检查及本地 launcher 测试曾通过。候选 `caabf67` 新增代码的 Ruff、compileall 与 diff 检查通过；不计作实际业务 PASS。
- **MODEL / 安装升级：** `.local/s11/operations/20261019T104659Z-caabf67-followup-lab-upgrade-test/result.json`：候选 `caabf67cb0b5f50d098081dc5c6d72124f8f35e2`，退出码0；62个 Odoo post-tests、0 failed、0 errors。日志 SHA-256 `4b5810ce679579d169726724dd5292c4eedbe7a2a6c0ed9166fd890d7f28b8c9`。模块集是 S11 两产品 addon、两 test addon、必要结算扩展及因已安装核心 SMS 功能新增的 `ydental_lab_sms_guard`；没有 `-u all` 或升级 core。较早候选 `cb02075` 有一次失败升级尝试，具体错误和独立失败后保护读回见下方，保留其原始日志。
- **T11 / 独立升级后状态：** 新增 `ydental_lab_test.tests.test_t11_exam_continuation.TestS11NextDayExaminationContinuation.test_yesterday_completed_panorama_today_revalidates_cbct`，通过真实 S06/S08 检查、队列、临床、治疗服务，证明昨日全景完成后次日 CBCT 旧任务先拒绝，必须重新接诊并复核后才实际确认；不安装或绕过 `ydental_exam_test` 的 S09-only 门禁。独立读回 `.local/s11/receipts/s11-independent-post-upgrade-7f03f49-20261019T102809Z.json`，SHA `ac950a915ef7c78a991fad737f7f15280c88bf32812fa015ee34905a12acbc05`，确认60项0错、T11用例日志、96模块版本和旧对象投影保全。独立读回确认当前模块数96、旧224项保护计数未下降、S10 D/C 摘要一致、既有 S11 订单/库存/通知/费用来源投影未变。该证据注明旧行内容的限制，计数不等于逐行全库证明。
- **通知任务：** job450 的原稳定 request-id 在候选 6706 同 key 恢复；独立读回 `.local/s11/receipts/s11-independent-job450-same-key-recovery-readback-6706bc7-20261019T095200Z.json`，SHA `7211f9d83d06b1566cb7701bfbb0bbbcaa8a7d5ba3127167d8b5447844004e7f`。任务 accepted、delivered=false、attempt=1，新增一条指派给负责人的内部 vendor activity；`mail.mail` 不变；SMTP/外部 provider 仍关闭。另有先前候选的真实双连接领取结果，但在较早版本的 activity 写路径上失败，随后才以原 key 做恢复；不把较早 race 直接称为当前候选完整成功 dispatch race。
- **扫码并发：** 候选 `43af67a` 的真实普通用户模型动作 `ydental.lab.code.scan.action_scan` 由两个不同 PostgreSQL backend 同时调用同一码；均解析到合成订单181。私有收据 `.local/s11/operations/20261019T103146Z-lab-scan-race-43af67a.json`，独立读回 `.local/s11/receipts/s11-independent-scanner-race-readback-43af67a-20261019T103241Z.json`，SHA `ef4bc95f1f6db9a37d4e30239dbf7ac34d7a66a49c90e216c1843b6ab346ff36`；确认订单状态、实验室事件、原生库存、采购行和成本前后不变。该证据仅证明并发扫码只解析、不产生库存/成本副作用，不覆盖并发收货/入库。
- **T02 / T10 新增代码与实测：** `TestFollowupCrossStore.test_cross_store_referral_completes_followup_and_close_requires_reason` 在候选 `caabf67` 带数据升级中运行通过，真实使用转诊/接受/异店治疗/来源复诊服务，覆盖跨店授权拒绝、显式未关联关联、不得伪造源店预约和关闭原因。附件修复在 `ydental_access.models.ir_attachment` 内容返回路径校验受限 `res_field` 字段授权，未知字段拒绝；`TestLaboratoryAttachmentFieldHTTP.test_manager_only_vendor_evidence_denied_by_field_and_direct_attachment_url` 通过真实普通 HTTP/RPC 验证管理者可取文件、普通仓库用户可读普通元数据但字段读取和猜测附件直链均拒绝且不泄露测试标记。原首轮发现 vendor 审计类别字段错误也已修正。两个新用例均计入62 post-tests。
- **首轮新回归失败及保全：** 较早候选 `cb02075` 带数据升级运行 `.local/s11/operations/20261019T104242Z-cb02075-followup-lab-upgrade-test/result.json`，61项中2错误、退出码1。跨店用例仓库编码超五字符；附件 HTTP 用例初始化时普通经理无权创建 `res.partner`，因此安全断言未执行。独立只读失败后读回 `.local/s11/receipts/s11-independent-post-failure-cb02075-20261019T104441Z.json`，SHA `d0cd98755a821d7f76406f92befafd2462956c64fe070ffaeaa7a76679b6247a`，确认96模块、224项保护计数、S10 D/C及S11费用/通知投影未变化，服务停止且18411空闲。夹具修复后候选 `caabf67` 实测通过。失败后模块状态保全不等于失败安装升级整体回滚。
- **候选匹配独立升级后读回：** `.local/s11/receipts/s11-independent-post-upgrade-caabf67-20261019T104848Z.json`，SHA `7cc2b3e7bcff888be05dc221ce959fea44ebe4a340d07855b6eaba2faf82da58`。独立核实确切候选与日志、62项0错、96个已安装模块、原91模块哈希、224项保护计数、D/C及S11费用/通知/订单/采购/库存/复诊投影保全；运行身份、角色和scope吻合，服务已停止，18411空闲。计数及指定投影不能证明全部历史行内容逐行相同。
- **HTTP/RPC：** `.local/s11/operations/20261019T0954Z-6706-http-rpc.json`，普通合成用户539登录并切到门店1；复诊页、门店切换和 `ydental.lab.order.search_read` 均 HTTP 200，返回的订单只含本店合成加工记录。
- **真实浏览器：** `.local/s11/operations/20261019T0954Z-6706-browser.json`，同普通用户、真实 Chromium、只读打开复诊工作台并读到既有 `to_notify` 行；HTTP 200、无页面异常。此项没有在浏览器中完成复诊业务变更。
- **原生追加费用与核销：** 已提交的合成收费来源51绑定真实追加周期202，冻结演示 S05 价37.80，在实际服务确认后关联 S10 原生已过账发票97 / 来源79 / 行193。现有非费用源和供应商成本独立读回仍按旧候选路径复核；具体独立收费读回见 `.local/s11/receipts/s11-independent-charge-acceptance-b08d493-20261019T080200Z.json`，收费实现自该候选至6706未变。候选6706新增了真实 1.80 合成贷项143、不可变调整源116与部分核销54，将发票余额从37.80降到36.00；无付款或现金退款。独立当前候选读回 `.local/s11/receipts/s11-independent-charge-credit-acceptance-6706bc7-20261019T101200Z.json`，SHA `180e1d89cc409d166d27327b70ae2930e1612a214b7cb3fc666e44221cdf6b16`。
- **收费幂等竞争：** 两个真实 PostgreSQL backend 同时调用同一已提交收费修正键，经 Odoo 原生事务重试层后均返回 `already_accepted` 和同一贷项/调整ID，且只保留一条调整、发票余额不再变化。私有操作 `.local/s11/operations/20261019T1015Z-charge-credit-idempotent-race-result.json`；独立状态读回 `.local/s11/receipts/s11-independent-charge-credit-idempotent-replay-6706bc7-20261019T101052Z.json`，SHA `68f9cd70dceb6bf90460139f69ccc765c85ff177430151f1d19064fa215bc7e1`。另一次首次写竞争中直接调用 `_operate` 的一方遇到 serialization failure；未盲重试，独立只读核实最终仅一条贷项后，才对已知稳定键进行上述无副作用幂等重放。
- **真实多连接竞争：** T06 收货同键与收货后入库同键 races 在候选 `03949443` 分别使用 order432 执行，独立读回确认各自唯一持久结果；具体收据和此前准入留在 ignored `.local/s11/races`、`.local/s11/verification`。取消限于 `draft/sent/processing`、入库要求 `received`，因此合法竞争组合为取消/收货与收货后入库，不能把取消/入库伪造成同一初态竞态。 续行在候选 `73ec1c7` 用 order434 完成 T06 duplicate putaway race，runner 与独立只读读回均通过；操作事实见下方。
- **T16/T17 新证据与独立验收：** T16 order433 首轮 runner exit3 原样保留，不重放；T16 order434 在 `377ae373` 运行 PASS，receipt `.local/s11/races/20261020T014807Z-a173a69b-lab-cancel-receive.json` SHA `c8e28791a3f90400fa58a9dc0ee20e2ed2c08e901765dd0f236ec6d75bfd069f`。T17 package-code race receipt `.local/s11/races/20261020T014504Z-51ef7495.json` SHA `73163f282ae0dd0bd64554b2807a9a20d258d326b4b259792ec28a06e688511b`。两项均为数据库服务层真实不同 backend；独立验收为 RR READ ONLY 并显式 ROLLBACK。T16 event1069 赛前/赛后均读得 `draft→sent`，新收货 event1071 唯一；T17 只为433追加一个 code-bound event，434保留 sent/unbound。后续 T06 putaway race 用 order434，receipt `.local/s11/races/20261020T015223Z-2e41fc22-lab-putaway-duplicate.json` SHA `58c8f70b01d584833a20605362a3e79215a240a5f75b0dd13b54d9fc2e694cb0`；独立验收 `.local/s11/verification/race-putaway-order434-independent-readback-73ec1c7.log` SHA `78af20984e6d3aa80be91c716f72c14bb28a96376bbd568dc7044c0097b226c8`。两 backend 为 accepted/already_accepted，唯一event/move/幂等操作/audit/followup；库存目标/来源精确+1/-1，成本$42.75、患者费$137.25、order433绑定及D/C保持。 T08 discard 分支使用 order432 在 `5c69855` 上执行一次，ordinary model runner exit0、`_operate(exception, discard)` 返回 accepted；独立 RR READ ONLY + 显式 rollback 读回 order v5 exception、唯一 event1074/inventory event+move904/audit40296/operation1021。实物由义齿库移至损耗库，数量−1/+1且 reserved 不变；followup239关闭并保留内部resolution activity，既有 accepted job1012仍 accepted、delivered_at空；原收货/入库902、PO147 $42.75、fee384 $137.25保留，没有新增fee/charge/credit/refund/fit，D/C摘要一致。证据 `.local/s11/verification/t08-discard-order432-independent-readback-final.log` SHA `dc2f2403d06e041ebfc54ad06aa532fa62698f507bc3b19551fb7b78b562ed7e`；receipt `.local/s11/races/20261020T020257Z-t08-discard-order432-committed.json` SHA `0e65d9374140660dd250e589155628bced4fd8fa1d08dcfb49d0e87f974b8e15`。第一次/第二次 harness 分别因关系类型断言/无效 inventory domain 字段在业务调用前退出1，未建session、未写业务；保留日志SHA `370909d6245bf609113b250468406061a555d08f2fd9a2efab65c8c4e04637f1` 与 `291947bb3a81708a8ab8b7311c4af3c3983b9dd74bb701babe7b4bdc19cd4292`；修正后第三次执行退出0，日志SHA `9c4eaf9a97f248f28a50cda66261a81e4fa43c0496e22dc617e3046106d3f5b3`。supplier_return处置分支仍未实测。
- **T17 夹具与保护：** 为取得第二张合格活动订单，按正常 S06/S08 与采购流程新建 event388/doc388/fee386（$137.25）和 PO149/line149/order434（$42.75）。source 独立读回 `.local/s11/verification/source388-independent-readback.log` SHA `a0db668353629134c2a018a854d90bb9a208c26cab95fbd7cf24acb416aca9a`；fixture 独立读回 `.local/s11/verification/fixture-source388-independent-readback.log` SHA `b9bf933f4956e68c1f171df982be1cd2767f773f9bcca28820c2db29a3cd6f6f`。两阶段均无库存/外加工/复诊/通知副作用；D/C 标量投影保持 `33f8730aa39cc869e749827e66f10505a0fe9e5aedd5677c9cb1b17718202ae8`。
- **S10保护：** 独立收费/通知读回均核了 D/C 财务链摘要及相关 S10 计数。旧D6收款、2退款、净4链没有重演；S10原文书、附件原件、旧日结与审计没有为 S11 重新操作。

## 2026-10-20 continuation checkpoint

本轮在候选 `1b8f5b6` 上将task720正常报告至queue position408/entry408；queue enter/call/start已提交为execution400/lease400。resume runner因clinical service参数签名错误在clinical.open之前停止，未创建clinical document、treatment event、fee或material consumption。原token不在receipt中且不能从hash恢复；expired lease经固定原生`ydental.queue.service._timeout()`按唯一expired active ID 400回收。timeout receipt `.local/s11/races/20261020T-native-timeout-lease400.json` SHA `f20a744923d68aa4676f2cfc5f3843f32178c1484a350bc18dafe4e911a44e4f`；独立RR READ ONLY回读 `.local/s11/verification/t18-native-timeout-expiry400-independent-readback.log` SHA `5e00d0ff195b0f8bd0b459c34291ce925a514a478b29c223b0ca42d9f70cc22`确认lease400 timeout释放、execution400/entry408为verify、task720仍started v6、position408 inactive、唯一自动审计40339；lot144 qty1/reserved0、area1294 open v10。临床模块的takeover要求先有已保存真实文书；这次失败发生于open前，故不takeover、不重报、不重开task720，station1继续被verify execution保护。

当前candidate `98412e7` fresh admission PASS，服务停止且scope有效；receipt见上。独立RO资源核验：store1只有station1，user8的execution400仍verify；user6具station capability但不能越过站点fence，users539/952没有该capability。store2有station2和合格普通clinicians users9/10，但其mapping/catalog对应的published prices 2–5均已于2026-10-19过期，vendor98没有store2 cooperation，且未发现普通warehouse-write actor。候选S11 synthetic confirmed treatment event扫描没有安全可复用记录：13条S11合成治疗事件属于patient150/orders432–435/source388保护链；其他无followup事件属于S10保护链。扫描证据 `.local/s11/verification/f1-followup-candidate-search-15a6624.json` SHA `fb4c5ecc3354c280b4d6629494acf4a77ca95a18a706431c3c9ef89022a1143c`。因此F1、T08 supplier_return、通知端到端、F4双店合作、T18戴用/followup及F2首次收费并发仍未完成；这些下一步都需要建立真实的新合成治疗来源并有合格服务站/价源/普通操作权限。未改业务语义、未触及S10保留对象、未运行外部通道。`#35`保持OPEN，状态 **PARTIAL / IN_PROGRESS**。

## F1–F5 与 T01–T18 覆盖状态

候选 `caabf67` 的一次测试命令实际通过62个post-tests，不是62个需求，也不能把下列部分证据升级成场景全PASS。候选及层级按独立审查与原始结果限定：

| 项目 | 当前证据与缺口 |
|---|---|
| F1 / T01、T13 | 生命周期模型测试涵盖提醒、未接通、联系成功、超期、预约关联/改期和真实接诊关联；actor2318对confirmed event414创建followup265，并在attempt12通过真实浏览器关联后续合格event416。POST返回303、工作台刷新200/条目消失，独立已提交状态读回确认done/seen、唯一event416/execution536及唯一完成审计；attempt12详情见本报告顶部。跨店接诊 T02 新模型闭环在 `caabf67` 运行通过。 |
| F2 / T07、T18 | 免费返工、成本与患者收费分离、S05冻结价、实际服务后原生出账及版本贷项模型测试通过；task941首次收费两连接竞争中一方提交invoice179，另一方收到mutex更新SerializationFailure。独立读回先确认无loser receipt且无第二经济事实，再对未提交的同一幂等key单次恢复，最终两个receipt key指向唯一posted unpaid $7 invoice179；payment=0、库存/材料与D/C不变。runner未保存原始backend PID及loser响应，故限称数据库竞争加核实后的幂等恢复，不称两路并发直接成功。完整 unknown 通知→返工周期链仍缺。 |
| F3 / T08、T16 | T08 discard/报废分支有模型覆盖并已有真实持久状态独立读回，验证实物损耗去向、成本与患者费用未变、待办关闭且无假戴牙/退款；supplier_return分支尚未实测。T16 首次在 order433 执行时 runner 退出3；根因为 before/after 事件字典使用了不对称字段投影。独立读回确认当次恰一收货业务结果，但赛前两列不可证明。提交 `377ae373` 统一补读并新增纯测试后，order434 的 T16 race runner 与独立读回均 PASS：两 backend，收货一胜；取消在明确 SerializationFailure 后有界重试并观察状态冲突；旧 event1069 的 before/after 原始值两侧一致，新 event1071、audit40283、operation1019 唯一，无库存/复诊/成本/费用副作用。独立证据 `.local/s11/verification/race-cancel-receive-order434-independent-readback.log` SHA `dba6892be4087d13d3acac8bf4339120ebf73387e264e08a51d094fc1d5064d4`。|
| F4 / T15 | 资质审核、合作/开单约束、过期旧单与内部活动消息测试通过；T10 HTTP回归验证普通仓库用户不能下载管理组限定厂商资质附件。当前候选新增模型用例 `TestLaboratoryGuards.test_vendor_cooperation_is_store_scoped_within_shared_company` 通过1项post-test、0错，检查同公司门店不能复用对方的合作；operation/result/log在 `.local/s11/operations/20261020T063019Z-f4-store-scoped-model-test/`，log SHA `129dd9c2f0c0b4975e384bb5da6e7c5205ccfde6ad893dc2cd21758a71494384`。 最新候选`789619f`另以真实ORM/原生审批和两名店内warehouse actor运行`test_vendor_qualification_and_cooperation_use_real_store_scoped_records`，通过1项post-test并独立读回PASS（详见顶部F4/T15段落）。独立post-test RR读回PASS（限定范围）：`.local/s11/verification/f4-posttest-independent-readback-facts.json` SHA `f9632b35fc463bf18746ded9bbca7e4e5eb1ceeecf44b9a97099cccb5318672a`，核对224保护计数无下降、D/C pin、测试窗口业务表零增量、T08/T18相关投影、PO成本和job语义、service stopped/18411空闲；explicit rollback/close。原自动读回FAIL `.local/s11/verification/f4-posttest-independent-readback.json` SHA `d172ef5e8def3537081488e8d10ee69d86ba5d582d5cd57469e73980da4e4ec2`保留；原脚本将旧投影字段名硬匹配且要求工作树clean，而主控同步中的两处仅文档变更导致其总判定FAIL，候选与测试/运行/准入绑定本身一致，补充事实读回修正该解释。这仍非双店端到端合作矩阵。最新当前数据只读快照 `.local/s11/verification/f4-vendor-current-readonly-08a1050-attempt2.json` SHA `63b6df0a7215490e8a1cd8aced69888ebbf64f8b45fab9985638171d85e330a8`（HEAD08a、RR READ ONLY/ROLLBACK/close）：vendor98为approved/company1、有效至2026-11-18，cooperation98(store1)、235(store2)均active；vendor249为approved/company1、valid_until 2026-10-20，cooperation236(store2) active。job450(store1/vendor98) accepted/attempt1/no delivery timestamp；job1050(store2/vendor98) pending/attempt0/due 2026-11-18；job1051(store2/vendor249) accepted/attempt1/no delivery timestamp。均无外部送达事实。该快照早于当前HEAD，但当前HEAD08a仅增加报告/状态文档；不把快照当E2E验收。T08可行性快照仍缺store2 lab order及同actor的medical+warehouse权限；新增purchase组会扩大company级可见范围到受保护PO147–149。无权限扩张或PO写入。 |
| F5 / T06、T14、T17 | T06 order432 收货及入库 duplicate races 在候选 `03949443` 已实测并独立读回；order434 在 `73ec1c7` 的入库 duplicate race 也完成 runner 与独立持久读回，详见前述 SHA。T17 在 `377ae373` 对 order433/434 执行两个 backend 同码竞争：433 唯一绑定，434 收到 `code_conflict`；event1070/audit40278/operation1018 各唯一，数据库 unique constraint 报错经产品冲突映射对应 loser 结果；库存、成本、费用与 D/C 未变。独立读回 `.local/s11/verification/race-package-code-433-434-independent-readback.log` SHA `b467643311661cf57a7e087c64101abcdacb04b102a78be122f096ee7716c0f4`。T14预约版本仍只有模型证据。|
| T03、T04 | 模型覆盖unknown、签名、重复/乱序、冲突和取消后不复活；候选`7bd9f0d`新增HTTP `HttpCase`真实路由定向验收：有效HMAC accepted/delivered、重复event duplicate且唯一receipt、invalid HMAC 403，独立post-test回读PASS（详见顶部T03/T04段落）。回调HTTP路径不调用transport；真实供应商通道仍NOT_RUN，T05/T12策略端到端未完成。 |
| T05、T12 | 免打扰/退订/日上限/未配置及通知失败不阻断人工加工有模型覆盖。event417新建followup272的真实Store2浏览器链验证无已验证联系时进入`to_notify`、仅留内部activity且不建job/contact；独立持久读回PASS（见本节上方）。完整controlled-sink自动派发、静默窗口/退订/日上限端到端仍未完成，因为没有合法可用联系偏好/联系方式；真实通道NOT_RUN。 |
| T09 | 完成后关联返修单的模型测试通过；独立只读读回 `.local/s11/receipts/s11-independent-t09-post-fit-repair-43af67a-20261019T103711Z.json`（SHA `8b052154098557d4e43eec8eb1c58f88f7449f8f5e336f8315bd43eea4a99e09`）确认父订单200仍完成、治疗与义齿出库事件保留，恰有一个独立返修子单249并有自身收货/采购成本/复诊待办。此为持久状态读回，不是新操作或并发测试，也未证明每条历史记录内容不变。 |
| T10 | 无权来源/未知码与病历边界有模型/HTTP覆盖。候选 `caabf67` 新增真实 HTTP/RPC 附件回归通过：普通仓库用户的直接附件 URL 被拒绝，管理用户下载成功；失败负载不含合成标记。 |
| T11 | 新的 S11 专用 TransactionCase 已在候选7f03随完整带数据升级执行通过（计入60 post-tests），独立读回确认；通过实际检查/续诊/CBCT复核服务链测试昨日全景已完成、次日未复核拒绝旧CBCT、续诊并验证后才完成。S09-only `ydental_exam_test` 门禁保持未绕过。证据为上方升级日志与独立读回。 |

独立覆盖矩阵完整结果以本段为准；不将未执行/旧候选验证写 PASS。外部通知测试 sink 与真实 SMS 分列：真实供应商 **NOT_RUN / OUT_OF_CURRENT_ACTIVATION**。

## 独立验收、状态与下一步

独立审查（实现者未给自己签收）确认：S11收费来源/费用成本分离与S10原生出账、贷项契约；T09持久状态、T02/T10 HTTP/RPC、升级保全读回；T06/T16/T17真实多连接动作和独立状态读回；T08 discard处置、task941首次收费竞争后状态；F1 followup265真实浏览器完成和followup272无contact人工兜底；T03/T04 signed callback HTTP；F4/T15真实ORM资质审批及双店scope隔离。当前`PARTIAL / IN_PROGRESS`：自动通知策略端到端因缺已验证联系渠道未运行；supplier_return及完整F4采购/收货链缺合格义齿临床来源；T18后续返工/返库链未完成（task720失败后按原事实保持verify、不takeover）；最终综合影响回归及独立总验收仍缺。旧SIGSEGV日志与后续HTTP浏览器成功尝试均保留，不重试旧run；#35保持OPEN。

已知差错与修复保留：早期安装缺 Python `phonenumbers`；Odoo20 registry import路径已修；ruff排序曾破坏模型依赖import顺序并导致模块注册失败，已恢复依赖顺序；Odoo mail.activity默认消息可能触发邮件，现通过 quick-update 抑制活动邮件并限制 vendor message API；通用 composer/template及可选 SMS模块存在外发路径，新增 vendor guard 与 `ydental_lab_sms_guard`，普通 reader 负测确认不会增加短信/邮件。各失败、候选、日志与保全读回仍在本地 ignored `.local/s11/operations`/`receipts`，最终交付前需生成不含秘密的可发布证据索引。

剩余工作继续限于 S11：补齐适用异常、通知、资质/合作与返工闭环，并完成浏览器业务步骤、必要影响面回归及独立最终验收。任何需改业务语义或放宽安全门禁的事项不自行处理。plan结束时更新本文件与同一 `CURRENT_TASK.md`，然后统一同步 GitHub 最终结果并按证据处理 #35；此前不发布 Issue 中间评论。

当前 owned Odoo 已停止；正式效果入口仍需在最终报告列出正常 launcher、普通角色及可复现步骤。无生产批准，不合并、不部署，不启动 S12/S13。


## 2026-10-20 S11续行：过期预约队列守卫与实际到店报告

固定候选 `2df07373fa5257589115d39f4354dcd4c25c2997`，分支 `codex/s11-followup-lab-r1`。新增只读预约资格检查：预约结束、资质/发布价失效或预约业务日期不符时，未开始的保留任务不进入 queue call 候选，queue start 再次核验并拒绝已过期资格；已开始、暂停、交接、完成的任务保留已消费预约容量语义，避免过期原时段阻断当前执行或后续流程。队列返回服务资格复用同一检查。修改涉及 `ydental_queue/models/ydental_intake_service.py`、`ydental_queue/models/ydental_queue_return.py`、中文翻译和 `ydental_clinical_test/tests/test_document.py`。

本候选的 S11 兼容临床/队列升级回归为 32 post-tests、0 failed、0 error；完整私有日志 `.local/s11/operations/20261020T043731Z-clinical-queue-expiry-handover-regression/odoo.log`，摘要 `result.json`，日志 SHA-256 `131ad44f558fd0fe56300aa1d21792e07225ec9bc98dc70bfb0597d2013ecf16`。followup 生命周期精确回归 1 post-test、0 failed、0 error；证据 `.local/s11/operations/20261020T043813Z-followup-completion-regression/result.json`，日志 SHA-256 `a171d64a18fcbd1ce2a6f64718ae24d2c0fe150aa0d64e068249c879ec4d1927`。更早的错误测试选择（0 tests）不计通过；32测套件发现的 suspended 任务错误已通过同一容量语义修复解决。此前 started 状态错误及后续修复细节不覆盖，原始日志留在 `.local/s11/operations`。

独立 post-suite RR READ ONLY/ROLLBACK 读回通过：候选/DB身份匹配；task758 recovery→execution421/entry430/lease421→task799/ent485/claim503链保全；task759/entry431、slot1297/1299、protected counts与D/C摘要未变；无新增治疗、费用、库存或通知外发事实。一个 inventory mutex 内部时间戳触碰（revision0/write_uid1）被准确记录，不伪称完全无DB写痕。证据 `.local/s11/verification/queue-clinical-followup-postsuite-readback.json`，SHA-256 `faf3d15caf24cdad930e2d3d784f6341af5a5e82ee5e84f41219bcef62e7abba`。独立准入复核确认候选/受限角色/DB与运行时绑定有效，无ACL更改；其他数据库上仅继承PUBLIC CONNECT，`odoo20_dev.public`另有继承PUBLIC USAGE/CREATE且已记录，未撤销全局权限。见 `.local/s11/verification/admission-2df0737-ro-recheck.json`，SHA-256 `ab2c17485d825c348e800356b29248d6560ef1442aaa3c9d4c4d8ebc43fef61a`。

本轮 RO 前置核实后，以actor9本店普通前台身份，通过原生 `ydental.intake.service._operate('report', ...)` 对patient364/task799 version2登记排队，复用已存在的当天arrival359，没有重复arrive。动作发生于 `2026-10-20T04:41:51.779672Z`，返回position544、task v4、waiting。受限于待排 slot1297在05:09 UTC开始，后续接诊不得提前调用或跳过原生队列。执行receipt `.local/s11/operations/store2-patient364-task799-report.json`。独立RR提交状态读回待本节续记；本次report不构成治疗、戴用、followup完成或计划完成证明。

当前仍未完成：T08 supplier_return；F1完整浏览器生命周期（followup265已建但未由后续合格事件完成，浏览器POST后投影未确认）；通知 unknown/策略端到端；F4双店资质合作矩阵；T18 continuation/followup后续及最终影响回归；F2首次收费并发；以及独立最终验收与计划收尾。原task720在clinical.open前失败后已timeout转verify，不takeover/不重报/不重用。真实供应商/短信仍NOT_RUN / OUT_OF_CURRENT_ACTIVATION。#35保持OPEN，未向GitHub发布中间更新；无push、合并或部署。

## 2026-10-20 S11续行：task799原生治疗与handover

固定产品候选 `f423cc7363b399e0e1713f5674e33d62eb94e590`，原分支不变。预约1297真实开放后（DB UTC 05:09:25），普通store2医疗角色actor10在单一原生事务中接诊已等待的task799/entry544，建立execution534、打开并保存临床文书505，执行一次合成catalog2治疗并按 `demo_confirmation` 形成event414、price snapshot511（price455，USD 7.00）及fee412（$7）；无材料、库存、invoice/payment。handover创建/复用 continuation task940 并退出lease541。操作回执 `.local/s11/operations/task799-native-clinical-handover.json`；运行摘要 `.local/s11/operations/task799-native-clinical-handover-run.log`。文书handover后为pending v2；治疗事件固定关联handover前保存的v1，immutable versions 1/2各一条。task799进入handed_over v7、continuation940仍pending，因此不冒充后续continuation完成。

独立RR READ ONLY/ROLLBACK读回最终PASS；attempt4证据 `.local/s11/verification/task799-clinical-handover-independent-readback-attempt4.json` SHA-256 `7dd2c6515b06d32a2768558a2141db13b5e08ee614f7bc1654039f13077cd04b`。核实DB/OID/cluster/受限角色与候选匹配；task799/entry544/execution534 handover，lease541 inactive，position inactive；entitlement485已started、claim503 consumed、slot1297 reservation_free仍0；event414 confirmed关联doc505 v1和snapshot511/price455，fee412 $7；continuation940 pending且来源为execution534/parent task799。无消费、库存事件或stock move；224张保全表相对checkpoint无计数下降；D/C pin匹配；提交后mail/activity/message/SMS/notification/outbox均0；owned service stopped、18411空闲。早期两次核验查询错误及attempt3断言投影形状错误保留原FAIL证据，attempt4通过，不把验证器错误升级为业务失败。

T08 supplier_return前置仍有实际权限缺口：采购组ACL对purchase.order与purchase.order.line为CRUD，规则仅限制company，store1受保护单147–149也在company1。新授予store2合成用户 `purchase.group_purchase_user` 会让其获得这些记录读写范围；未创建该角色、未扩大跨店权限。继续处理不依赖该权限的范围；是否接受该company级访问须由用户在具体事实基础上决定。

## 2026-10-20 S11续行：store2 followup浏览器操作员

当时store2无followup writer。使用现有actor9 group-manager经原生访问服务创建合成user2318，company1范围、store2 membership3600/employee2287、session3589；仅授权store2 `followup:write` 和 `medical:write`，仅base internal group，无采购/manager/system组。账号回执 `.local/s11/operations/create_store2_followup_operator_attempt2.json`；独立RR READ ONLY读回 `.local/s11/verification/followup-operator-attempt2-independent-readback.json` SHA-256 `9112f562bd7dfd4254273c19d60b28689fbae044cba5849f0cfbfb96a68541d5`。224项保护计数无下降、D/C pin匹配，权限和session符合预期。

账号创建同时产生1条 `mail.mail`（state=`exception`）及6条mail.message；mail记录没有已发送状态，外发SMTP server为0，未见短信、notification job或queue outbox增量。该失败投递记录按原样保留，不删除或重试邮件；独立读回按“无外发副作用”严格检查标记FAIL，报告按事实区分“邮件失败记录存在”和“无投递”。第一次账号尝试由新用户自身执行 `_join` 而被拒，事务回滚；独立RR读回确认无账号、membership、grant、session或通知计数残留，证据 `.local/s11/verification/followup-operator-attempt1-rollback-readback.json` SHA-256 `6b1b2fc278d71e1b6f8f9c34a40c256f2143ff44258bf200a7383dba1b9bd8f7`。该工具/脚本错误已修正为管理员actor9授权加入，不重放已提交操作。


## 2026-10-20 S11续行：event414 followup创建

候选HEAD `64d841f357b66dbe76e5de91b1a5cf51271ffd47`（纯文档变更，产品代码仍为 `2df07373fa5257589115d39f4354dcd4c25c2997`）。owned launcher准入刷新后启动局部S11服务，actor2318以真实浏览器表单仅提交一次patient364 / confirmed event414的post_visit计划，计划时间2026-10-27 09:00。首次Playwright启动缺少libatk私有动态库时在表单前退出；使用仓库私有依赖路径后执行。POST后客户端投影断言未能确认结果，未重放。独立RR READ ONLY/ROLLBACK核实followup265恰一条，store2、patient364、source event414、created/responsible actor2318、state `to_notify`，证据 `.local/s11/verification/followup-265-browser-independent-readback.json` SHA-256 `9a69d9eed29eb2bab99aacf0ea2aeb4bee3313dd85ae1d838061f9d38fdf4dc3`；本地核对记录 `.local/s11/verification/followup-event414-browser-ambiguous-readback.json` SHA-256 `77ce401907712ffab9f2a45c0aa26af260b795981c826575125ec4b15aa5dd5b`。

创建仅新增1条内部activity及1条内部notification message；无notification job、outbox、email或SMS增量，外发渠道仍禁用。随后浏览器只读UI核验未找到预期workbench heading，故不报浏览器UI读回PASS；数据库独立已提交状态确认创建成功。该followup没有新的合格治疗事件，禁止用source event414自行完成。owned Odoo服务已由launcher正常停止，18411端口空闲。保护计数224项无下降、D/C pin匹配。


## 2026-10-20 S11续行：task940 continuation与HTTP崩溃边界

固定候选为当前docs HEAD `81daa65be1f158dea930a3dd76b4559015176c62`；产品代码候选仍为 `2df07373fa5257589115d39f4354dcd4c25c2997`。沿此前真实到店report task940/entry545，actor10通过普通store2医疗会话一次运行原生队列与临床链：call/start、execution536、clinical document507、一次独立synthetic `demo_confirmation` event416、price snapshot513（price455/$7）、fee414/$7；handover到pending continuation task941，lease543通过holder_exit释放。前序task799的event414/fee412保持不变；无材料/库存消耗。queue report唯一scope-version outbox id5621为store2/area2内部队列版本通知，不是患者通知或外发。

事务收据 `.local/s11/operations/task940-continuation-native-clinical-attempt2.json` SHA-256 `a24c72e91b121b08f89a9db5da84fc5e52ffed15935478bd92a219a82a1d6c60` 在commit后保持`COMMIT_PENDING_READBACK_REQUIRED`：原生DB commit已执行，脚本随后在cursor关闭后访问延迟ORM fee字段，没能写最终投影。不得重放。独立RR READ ONLY/ROLLBACK读回PASS：`.local/s11/verification/task940-clinical-attempt2-independent-readback.json` SHA-256 `62ce4fcd59bcd8db068fd5e03a47d58c8cccf2d651befd08bd2eeda45b3da152`，核实唯一execution536/event416/doc507/fee414及task941，来源、费用快照和handover一致；旧event414/fee412保留、无材料、无外发、224保护计数未下降、D/C pin匹配。补充closeout `.local/s11/operations/task940-continuation-native-clinical-attempt2-independent-closeout.json` 记录原receipt哈希和独立读回，原receipt未覆盖。第一次事务断言在commit前失败并rollback；独立读回SHA `36b729914936eb890b42bf8cc2f05ef00789397634fa2a6b602033ac45debe12` 确认无持久副作用。

followup265仍`to_notify`，源event414/doc505、无预约关联；不得用event414自行完成。后续浏览器运行仅通过actor2318认证并到达`/odoo`，没有进入followup workbench或提交complete POST。导航等待错误及SIGSEGV后的独立RR读回 `.local/s11/verification/browser-timeout-followup-final-independent-readback.json` SHA-256 `a2d3b8b3425ca2ab8a1eccb7d13adfd1f8f2731c1c6aa0e67b83a9a0d64302c1` 确认followup与event416关联未变，无contact/job/outgoing mail/SMS/outbox增量。认证产生1条无outgoing recipient的discuss.channel comment、3条accepted access audit及1个access session；因此mail_message/access_audit/access_session分别+1/+3/+1，按严格零计数变化标准不报全PASS。

owned launcher run `20261020T055248Z-18909ba92aa6` Odoo child退出码`-11`。owned service已停止且18411无监听。日志审查 `.local/s11/verification/run-20261020T055248Z-18909ba92aa6-crash-log-review.json` SHA-256 `dd0eeb3f44e5872a18d3c95208432ff4e97c29b954453df7bbbe57c0d49c0d43`：登录POST 303和`/odoo`页面后出现session rotation/registry cache invalidation，随后load_menus 403；两个missing-filestore FileNotFoundError附近静态asset后续200。日志未定位native crash原因，也没有业务action POST。依停止规则不重启HTTP/browser链路。HTTP后续失败证据与差错保留，不把导航错误当业务失败，也不重试followup。

本段对应task941首次收费竞争及其最终读回之前的状态快照；其后的续行已补做F2有限竞争与恢复验证，故本句不代表当前F2状态。T03/T04/T05/T12通知端到端、T08 supplier_return、F4完整双店业务矩阵及计划整体独立最终验收仍待处理；真实供应商/短信仍NOT_RUN。无push/merge/deploy，未向#35发过程评论。

## 2026-10-20 S11续行：task941完成与首次收费竞争

当前固定产品候选 `2df07373fa5257589115d39f4354dcd4c25c2997`，活动HEAD `1776c4e3520b742ac47ba874c5616bfe3240991f`。fresh task941资格核验通过：actor10具store2医疗权限/capability，task941仍pending且来源、到店、活动区域/站点和有效价源匹配；过期entry431/task759按原生规则排除。actor9有普通store2 settlement写权限及有效演示会计配置。一次report提交将task941更新至v3并生成position/entry546，arrival359复用；report回执 `.local/s11/operations/task941-native-report.json` SHA-256 `0435f67f3ed4af45f1495c3ceb35ec8069bbcbc8859f92b6bfab9912369de358`，独立readback `.local/s11/verification/task941-report-committed-independent-readback-1776c4e.json` SHA-256 `8110c9aa0a794bf39cdec5c5f7efa85e400a4bcdf9539aac46facfc43b9e21b7`。

actor10随后沿原生队列/临床/治疗路径一次完成task941，生成execution537、document508、event417、fee415（$7）、price snapshot514（锁定price455）；handover生成pending task942，lease544按`holder_exit`释放，没有材料消耗。操作receipt `.local/s11/operations/task941-native-clinical.json` SHA-256 `340b5c831219f5d2b7ae0926e33ac40ef408640b686d7082a5418eaaec046de5`。最终独立RR只读复核 `.local/s11/verification/task941-final-independent-ro-recheck2.json` SHA-256 `785da3fb188c5511aacb66cbf6e77fdc74f4f89f9a55b6c1fe1af345d37f17ae` PASS，显式ROLLBACK并关闭连接；核实新链唯一、旧event416/fee414及task940保留、task942待办和lease状态正确，保护库存/材料/财务计数与D/C pin符合预期，无fee415结算来源或外发副作用。早期独立读回FAIL因错误假设handover投影和receipt数量，保留原件并以复核解释，不覆盖历史；首次收费runner两个前置脚本错误均发生在数据库业务调用前，已修正后仅运行一次。

fee415首次发票竞争以两个同步barrier的独立数据库连接调用原生settlement。一次操作提交invoice179；另一操作在更新原生结算mutex时收到PostgreSQL `SerializationFailure`。runner随后在cursor关闭后延迟访问ORM字段，导致结果组装失败，未持久保存backend PID和loser原始返回值，因此没有重跑竞争。独立RR状态核验先确认fee415仅关联一张posted `out_invoice` invoice179（$7、residual $7、`not_paid`、payment_count 0），仅一条settlement source；loser key没有receipt，也没有第二张票、退款、贷项、付款或外发。基于该独立事实，仅对缺失的同一幂等key调用一次原生bill，得到既有invoice179并新增该key receipt，没有新增经济事实。最终独立只读读回 `.local/s11/verification/task941-first-invoice-race-final-independent-readback-1776c4e.json` SHA-256 `a345374fccf743834506374beeed59fdbf99402bfd6d0aa6e7288a8f43c55af2` PASS：两receipt key映射同一invoice179；move +1、line +2、source +1、settlement receipt +2、payment不变；库存/材料/D/C及邮件、短信、job、outbox无非预期变化。该证据代表真实数据库竞争和基于核实的幂等恢复；不代表两路并发调用均直接成功。首轮失败审计 `.local/s11/verification/task941-first-invoice-race-independent-status-audit-1776c4e.json` 保留为不完整的历史观察，不覆盖。

T08 supplier_return仍未运行。只读评估 `.local/s11/verification/t08-supplier-return-feasibility-1776c4e-final.json` SHA-256 `169b8b38070e6909757e15866ff1572bba3fc8bb45c66af45e148b14c88b0552` 显示store2有vendor98/cooperation235但无lab order；warehouse actor2043权限与medical actor不重合。supplier_return需要同时具store2 warehouse/medical权限的同一actor和已入库订单；完整PO成本来源还需要`purchase.group_purchase_user`，其ACL为CRUD、规则按company过滤，会覆盖company1受保护的store1 PO147–149。未授予该组、未触碰这些PO。此前用户的“授权”未指明是否接受这一company级访问扩展，因此不作为扩大访问权限的决定；其余不依赖该范围的计划项继续独立推进。

为补足F4当前候选可安全验证的门店隔离行为，新增 `ydental_lab_test.tests.test_lab_guards.TestLaboratoryGuards.test_vendor_cooperation_is_store_scoped_within_shared_company`：同一company范围下，合作查询对store1命中、store2无合作则拒绝。固定候选 `57a3fcbc5d093de92f5f2aa13423ca3bfcff238d` fresh admission由独立RR只读核验PASS，证据 `.local/s11/verification/admission-57a3fcb-independent-ro-recheck.json` SHA-256 `76813c58c3c2c86cd29c241325630682c7415fc93a24fe01e738c568552622cf`。精确MODEL运行退出码0、1 post-test、0 failed、0 error，`--no-http`；result `.local/s11/operations/20261020T063019Z-f4-store-scoped-model-test/result.json`，完整私有日志SHA-256 `129dd9c2f0c0b4975e384bb5da6e7c5205ccfde6ad893dc2cd21758a71494384`。同时修正该测试文件原有的Ruff告警（UTC别名及嵌套定义空行）。独立RR post-test事实核对 `.local/s11/verification/f4-posttest-independent-readback-facts.json` SHA-256 `f9632b35fc463bf18746ded9bbca7e4e5eb1ceeecf44b9a97099cccb5318672a` PASS：候选/运行/准入绑定一致、224保护计数无下降、D/C及订单/PO/job语义投影匹配、测试窗口相关业务表无写入、服务停止、事务显式rollback/close。首次自动汇总FAIL保留于 `.local/s11/verification/f4-posttest-independent-readback.json` SHA `d172ef5e8def3537081488e8d10ee69d86ba5d582d5cd57469e73980da4e4ec2`，其字段映射与dirty-doc检查问题已在补充事实读回中解释。该用例是模型层隔离断言，不能证明真实双店审批/开单/收货端到端。

HTTP/browser owned run `20261020T055248Z-18909ba92aa6`在followup真实完成POST之前以SIGSEGV停止，launcher已停、18411空闲。只读检查的run记录与server log没有native栈；`coredumpctl`无对应条目，`/var/crash`、`/var/lib/apport/coredump`、`/var/lib/systemd/coredump`也没有可用dump。现有日志审查 `.local/s11/verification/run-20261020T055248Z-18909ba92aa6-crash-log-review.json` SHA `dd0eeb3f44e5872a18d3c95208432ff4e97c29b954453df7bbbe57c0d49c0d43`只确认登录后到`/odoo`、load_menus 403及child exit -11，未定位native原因。故followup265真实完成、T03/T04回调HTTP、T05/T12端到端策略链、SIGSEGV后影响回归均仍缺；不重启或复现。F4双店合作矩阵仍未完成端到端部分。真实外部短信/供应商未启用；#35保持OPEN，无Issue中间更新或push/merge/deploy。
