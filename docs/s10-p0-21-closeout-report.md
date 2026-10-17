# YD-N1 R1 S10-P0-21 B 收尾：具体阻断交付

本批结论为 **S10_TECHNICAL_EXIT_BLOCKED**，提交给 GPT 独立复核具体阻断和已固定子证据，不能申请全阶段技术 PASS。已完成新合成原生财务/库存场景和内部 bill 最小原件产品；同源文书完成链、完整附件图片负向证据及带业务升级未闭环。P020 A 的限定采纳只引用正式裁定，不重做；P020 B、所有旧失败与永久 UNKNOWN 不改判。完整 22 行新增退出层见 [退出表](s10-p0-21-exit-table-final.md)，机器表逐行保留完整 P020 历史对象，不替换旧行。

唯一授权为 [6229311739](https://github.com/Yredxin/YDental/issues/34#issuecomment-6229311739)，P020 裁定为 [6229289071](https://github.com/Yredxin/YDental/issues/34#issuecomment-6229289071)。仓库、origin、工作目录及原分支匹配。父提交 `7a4bdb93cb4a2d625f01df7eb0ac41d76c5e0e46`；core 固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，无修改。#23/#34 正文及初始全部 3/253 评论 API 完整读取；交付前正文及全部原评论逐字相同，#34 共257评论，仅新增本批4条预检/冻结记录。#35 OPEN/0；Issue/Project mutation0。远端在本批推送前仍为父提交，未发现其他执行/交付冲突。

|固定层|SHA／证据|
|---|---|
|产品（全程不再改）|`be1d12a2d21771ca411ca8bdd510437980b68ef3`，仅7文件|
|首次测试|`bb495b51cf55cd47cd98c06fe6733da4d2fcb1af`，24个新脚本|
|R1 测试身份分层|`5853a75d6176cf4370c7bc463a6274be26282836`|
|R2 精确提交后校验|`425ba30455acbd5634fabba863d1bd1c175bfcb1`|
|R2 Decimal 校准／实际运行冻结 HEAD|`39880be1ae4dda46c16815ce3ca7b0ee9803c33e`|
|最终离线封存脚本|`07e9fb00fbcddffb7c3dd43ff8b9ec76c28b9175`（仅3份离线脚本，运行窗口结束后提交）|
|报告证据|交付回执固定最终线性证据提交 SHA；所有文件 SHA256 见 `file-sha256.json`|

唯一正式预检 [6229577294](https://github.com/Yredxin/YDental/issues/34#issuecomment-6229577294) 在任何产品改动或 DB/Odoo 操作前发布，并 REST GET 全文全等读回。实际产品/测试冻结 [6229596349](https://github.com/Yredxin/YDental/issues/34#issuecomment-6229596349)、R1 [6229624264](https://github.com/Yredxin/YDental/issues/34#issuecomment-6229624264)、R2 [6229730414](https://github.com/Yredxin/YDental/issues/34#issuecomment-6229730414) 均先读回后执行。四份 `*-api-readback.json`、初始/runtime/round1/round2 冻结与完整 SHA 索引保留；旧冻结不覆盖。R2 文案“document_original 与其余13组”是数量笔误，实际合同为 `SCENARIOS` 总14个，本批没有虚构第15个场景。

本批唯一新 B 为 `ydental_s10_test_20261017050000_21b0cafe`，OID **2122140**，cluster **7694897083368259627**，端口 **18322**。通过一次 template0 CREATE、正常原生安装构成，未复制或连接旧业务库。独立 data_dir/config/marker 绑定新 OID。初始管理员在普通业务前提交 chart 及多仓库、多库位、pricelist 三项原生 feature；普通人员授权与初始配置分列。临床、检查、发药、财务均为真实普通账号的合法绑定服务，执行器 sudo0；核验 Environment(uid1)只读显式展示投影和原生事实，不用其执行业务 lambda。币种实际为 USD，演示线下确认政策，不声称生产人民币配置、税务票据或平台到账。

稳定事实校验使用真实 PG catalog 列/类型、tableoid/regclass 物理来源+ID/完整关系 tuple。全部 account/stock/库存/治疗/结算资金及 S05 价格快照/币种/UOM 的 stored 列，包括 stored 计算金额和余额，均保留并按 Decimal 精确比较。来源、公司、门店、患者、价版、数量、借贷、核销、退款状态和批次不只比汇总。显式 `display_name`、M2O 展示投影另保存，不作为经济门禁。每次关键动作先 flush，保存私有全值、逐表/行/列全差异及公开脱敏完整索引，然后断言。失败的 acquire 也留下实际4行差异，未只存回滚后状态。

正常自有业务 cursor 在验证原生事实后保存完整 precommit/私有 pending、COMMIT intent/returned；独立新 RO/RR 连接读回，校验通过后才发布交接 marker。原生提交后的 rank 是真实存储事实，不冒称展示字段：固定 `addons/account/models/account_move.py:6370–6386` 和 `addons/account/models/partner.py:883–917` 产生精确 customer/supplier rank 回调。R2 在每次 COMMIT 前捕获 partner/field/delta/actor，仅允许本次注册的精确 rank 与技术时间/actor，不豁免整表或金额。患者 owner/公司/源等仍精确相同。原生信号仅保存并限制每个比较段逐条新增；不是通用白名单扩张。

|三组实际执行|已持久化／独立读回的限定结果|
|---|---|
|组1 收支、防重、退款、多账|patient1/execution1/doc1、fee1—4 为600+80+40+20，药event3/4及move4/5真实4+2。发布620后仍旧600，invoice1 posted740，付款350+390、partial1/2、余额0。新多账仅选新200不动旧账，选300按270+30、欠170，同日按ID。退款100异人批准后真实原生出款/贷项，拒50无资金，unknown80核实未付取消释放到390。负/超折扣拒绝、posted零额无付款；未收80减免仅贷项。bill重试不增源，card5同键仅一笔，改payload拒绝。|
|组2 日结、权限、交易|新现金日结550锁→异人解锁→300现金改微信的原生重分类move15→微信重结300，无现金往返。前日实际收10、次日录入，锁后补1拒绝、异人解锁合法补1、重结11。六类无结算岗位工作台/PDF/收款拒绝。新跨法人 sale/purchase/库存/posted凭证及无权前台拒绝；新同法人调拨move24/qty5。真实普通前台 UI 额外收 alipay3，只核 invoice9，200→197。|
|组3 价库款、数量、实物、票据、原件|主链价/费/账款及第一原件已提交。独立数量例旧600不取620，反向费14关联原费13/贷项20，只减应收不伪退款。主链药event3真实退1到quarantine、原处方剩余仍0、不新增费或退款。三份当前bill/receipt/refund真实PDF各1页逐页目视。原件v1实际留存、合法前台同SHA取回；真实经理UI明确生成v2关联v1，点击v1原件链接下载同SHA，旧记录/附件完全未变。主链文书完成及升级未完成，不能宣称完整F4/T12/T15通过。|

上述场景不是来自回滚中间打印：原生场景 checkpoint 文件、完整独立 RO 签名、最终645表快照和 `offline-tail-review.json` 对照。F1 首次 runner exit1 的原提交事实由 R2 只读恢复，未重交资金；其他11个独立场景均 exit0 并提交读回。各场景患者/门店来源独立列出，不把数量子例或跨法人子例拼成主链一次全程。`native-scenario-output-index.json` 特别标注打印本身不是提交证明。

|原始失败／残留阻断|事实、处理及最低补齐|
|---|---|
|R1 前置投影身份缺陷|运行普通业务前静态定位：普通收费/药房 env 不应读取其无权模型的跨域展示。只切换同 cursor 的只读核验投影身份，业务角色不变。保留初始脚本/冻结；使用第1轮额度。|
|F1 提交后判据及外层游标|已记录 COMMIT returned 与独立读回；旧门禁误拒 partner15 rank1→3，完整经济行相同。外层闲置 registry cursor 清理又报连接关闭，发生在已提交核验之后；系统原因 UNKNOWN，不称崩溃修复。R2 精确 native callback 判据、关闭闲置外层事务、只读恢复当前全存储事实后发布 marker；资金不重交。真实反例拒过量rank、patient owner、stored total。使用第2轮，余额0。|
|同源 document acquire FAIL|原始差异4行：新增 clinical.acquire审计、doc1 editor/session字段、queue mutex修订、patient mutex108→109；所有stored经济行全等。固定 `ydental_patient/models/ydental_patient_service.py:62–67` 为患者序列化 fence，冻结门禁遗漏该技术字段。自有 cursor 回滚；尾审 doc1 pending/v2/editorNULL、原件1和账款仍在。门禁 FAIL不改、不跑confirm/correct/release；只继续无依赖场景首次执行。最低动作是精确患者锁来源/字段反例合同及合法同源文书完成、旧原件重取，不重收已提交资金。|
|普通审计场景静态 BLOCKED|`scripts/s10_p0_21_b_audit_integrity.py:28` 残留 `payment.amount==500`，本批首笔真实350。此前预检“全部交接检查”不充分，此项纠正已公开保留；脚本未执行，无第三轮修改。最低动作从真实提交marker/金额绑定，补六项纯负向write/unlink，不重放收款。原件模型/附件不可替换的19项检查另已真实执行，不能代替该六项。|
|Web 尾部负向 FAIL／全局停|前台pay3和原件v2 POST均303，旧原件链接GET200/27665字节且文件SHA匹配；content161 GET404；image161 GET200/6078字节，冻结断言要求403/404失败。原生 `addons/web/controllers/binary.py:189–219` 捕获 UserError，AccessError是其子类 (`odoo/exceptions.py:57`)，无download图片可回退 `web.image_placeholder` (`addons/web/data/ir_attachment.xml:3`)。这与日志一致，但实际响应体未保存，永久保留本次字节证据缺口，不宣布泄露或负向PASS。HTTP正常exit0、Firefox本体exit0、browser runner/Web外层exit1；警告日志保留。不重复登录/点击；停止全部后续业务及升级，仅一次新B RO/RR尾审。最低动作应保存真实响应体/类型/哈希并验证占位图语义，兼顾新原件跨公司、患者family/混源反例；不放宽只看status的通用门禁。|
|带业务 S10-only 升级 NOT_RUN|受Web停止边界影响，audit-before/upgrade/audit-after全部0。原生安装成功不代替升级。最低动作在GPT明确安全来源后只升S10，对已提交业务/权限/旧附件逐字段相同核对，不重复已核经济动作。|

两轮额度内的失败、修复代码、旧判定和 Git 冻结全部保留。此后没有更改文书/图片合同重试，也没有改账单余额或另换库。P020 缺失瞬时差异仍永久 UNKNOWN；历史 Native 根因及生产风险没有解除。本批未发现新的 SIGSEGV 或无法解释的经济存储变化，但这不证明历史稳定性修复。

内部 bill 原件产品实际落在7文件：新 `models/ydental_settlement_bill_original.py` 的受控不可变记录；`models/ydental_settlement_original_service.py` 的真实源校验、生成/版本及无渲染取回；`models/ir_attachment_original.py` 的特殊附件不可写删及原生 binary/token 提前拒绝；`controllers/bill_original.py` 的 authenticated POST/CSRF/revision 和 GET；两个 `__init__`；现有工作台模板增加明确原件生成及指定版本链接。已有动态 `_pdf/_report_payload` 和收退款/日结/库存产品源码均未改变。新模型没有普通ACL，服务经过live settlement read+export write和公司/店/患者family/每条真费源校验后，才固定模型、固定模板、服务器字节作窄范围内部附件访问。不是 executor sudo，也不是通用认证 fallback。原生附件正文/RPC和limited-token入口静态审核及服务负向已有证据，图片HTTP整体验证仍按上述FAIL处理。

|原件字段组|实际绑定／边界|
|---|---|
|身份|invoice/patient历史源/store/company/currency；actor/generated_at；每请求当前权限及源校验|
|版本/幂等|actor+request_key、invoice+version唯一；previous关联latest；重复同key不再渲染；旧记录/附件write/unlink拒绝|
|来源|JSON保存源fee/event/line、价格版本及S05 snapshot、数量单价金额/币种、借贷/partial；source SHA|
|模板|固定 `ydental_settlement.ydental_settlement_pdf` 及有效arch SHA；生成前后再核源/模板一致|
|文件|原生private attachment，res_model/res_id/company绑定，无公开token；实际字节SHA；GET只取保存字节、缺件/损坏拒绝，不生成替代|

第一原件1/attachment161，SHA256 **05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4**，27665字节。合法前台服务读取及真实Firefox v1链接下载均相同；v2为独立original2/attachment630、previous1，旧v1记录和附件每列完全相同。v2实际字段/文件SHA见尾审。主链文书变化未完成，因此**同SHA重取子断言有证据，留存后合法文书/主档/模板变更再重取的完整断言仍NOT_RUN**。不能用退款后的旧文件下载替代后者，也不能用动态当前PDF或新生成文件冒充历史原件。

真实Web子证据为2个独立普通角色会话、2张已查看截图、真实旧原件PDF及1页已查看图。当前bill/receipt/refund另外3份3页已逐页目视：原价来源600/80/40/20、740/余额0；首付款350/已退100/净250/在途0；退款done100/微信。总共4份4页实际查看，新增渲染5次（原件v1、3当前票据、原件v2）。本批没有重新下载A当前PDF。冻结浏览器未保存逐HTTP事务的即时SQL快照或完整DOM；只保存实时请求账、真实截图/文件与整段Web前后完整存储差异。该边界明确列出，不声称与原生逐动作捕获一样细。

最终离线尾审41项核验仅解释已有保存快照：Web新settlement payment9/native payment10/move26、两条借贷共3、partial13仅invoice9、200→197；其他已有账单完整相同；所有临床/患者/价源/费用/库存/退款/日结、groups/membership/company/权限关系不变。新增24条S01审计、2个登录scope/session及原生device/login记录、原生首登timezone/HR同步技术时间、会计partner25 rank12→13、2条cache信号、7个首次资产附件及1个新原件附件分别列明。完整全值和差异先保存，再出该离线结论，不是事后更改运行合同。`res_users.py:861–877` 首登时区与 `addons/hr/models/res_users.py:196–265` 的关联员工同步解释该身份技术时间，不把这些字段统称纯展示。无成员/授权/公司迁移。

|实际预算|使用／上限|
|---|---|
|maintenance／CREATE|1／1，各一次；旧业务库连接0|
|install／configure|各1且exit0；无整模块升级|
|原生场景|14计划中13首次执行：11 exit0；F1及doc runner exit1保留。audit_integrity静态阻断0执行|
|显式COMMIT returned／已核检查点|14／14；F1 marker通过额外只读恢复，没有重交资金|
|独立严格RO/RR|17／32，均新B，ROLLBACK/关闭；最终645物理表|
|native后端累计／池|max8；控制进程累计31、专属HTTP累计21，共52，允许原生postgres目录DSN；逐PID未标DSN则UNKNOWN，不把累计当池占用|
|HTTP／Firefox|各1，context2；两次真实login/switch、payPOST1、originalPOST1、旧原件GET1、附件负向GET2；原生日志全部37请求／350，含redirect GET及wkhtml资产请求|
|最终持久实体|users58／120、store13／30、patient4／25、fee14／80、settlement payment9／30、refund3／20、stock move24／150、original2／5、S01audit1169／10000|
|PDF|实际render5／12；4份4页已目视|
|修复／后续|定向2／2；第三轮0；升级/后续业务0；S11/P022/合并/部署/Issue与Project变更0|

全部控制进程结果及退出码、backend日志SHA、实时transaction/HTTP账、公开完整逐列差异索引在 `docs/evidence/s10-p0-21/`；私有全值、配置、会话标识和完整日志留在权限700 `.local/s10-p0-21/` 和独立新库run目录，不提交。文件SHA索引、私有证据内容摘要索引只含路径/大小/哈希。最终离线 `seal.py`、`tail_review.py`、`exit_table.py` 的实际exit均0；它们没有数据库/Odoo/HTTP导入和操作，不能将工具PASS升级为阶段PASS。初始13项静态检查虽exit0，但残留500证明交接审查不充分，此原报告原字节保留并以本报告纠正。

历史兼容只使用固定Git对象和原裁定：现行财务服务与父提交逐字相同；相对旧R3最终，除 `_workbench` 外列出的财务方法AST相同，详见 `historical-compatibility.json`。旧并发、不同状态票面、跨店摘要/旧页证据只在原来源和原限定结论内引用，不连接旧库、不扩张为本批重跑或把两库业务拼全链。通用正式文书/模板/签署属于S12，统一美化、容量/备份及最终用户效果验收属于后续约定；本批不能拿它们替代或隐藏上述真实S10功能证据阻断。

以下8步是本批**已执行效果及保存材料的回看路径**，不是允许现在重启服务或重新付款的指令。专属HTTP/Firefox已经关闭；账号完整login仅私有marker保存，不公开口令。

1. 查看 `ordinary-frontdesk-payment.png`：真实普通前台切新B store3进入线下结算，勾选一张新账单。
2. 查看截图的付款9/alipay3及invoice9余额197；对照尾审partial13/native move26，而非再点付款。
3. 查看 `original-workbench.png`：真实经理store1可见已结清invoice1、740/0；动态链接仍称“下载当前内部账单 PDF”。
4. 同图查看“生成并留存内部账单原件”与v2/v1两个指定版本链接，证明不是注入按钮。
5. 查看HTTP账中原生POST303、受控v1链接GET200及保存 `UI-retained-original.pdf`；SHA与第一次留存相同。
6. 查看 `UI-original-1.png` 及三份当前票据页图，核患者编号、法人门店、原价格版本、金额和状态。
7. 对照 `original-security-result.json` 的19个实际拒绝和 `Web-partial-proof.json` 的404/200失败边界，不把图片200当已验证拒绝。
8. 查看最终22行退出表及文书acquire完整差异，明确升级/同源文书后原件重取尚未执行。

回滚原则：当前未部署或合并，无线上回滚动作。保留所有已提交合成账款、原件、数据库、日志及旧历史；不DROP、reset、clean、force-push或删除附件。若后续经明确授权取消候选产品，使用正常新提交逆向这7文件，并先决定已留存原件的受控读取/模型兼容方案，不能卸载抹历史。本次不实施该逆向操作。

最低补齐是上述四类具体阻断：精确患者锁合同和同源文书/旧原件重取、修正审计脚本真实交接后的纯负向、新原件图片响应及必要隔离反例取证、合法安全来源上的带业务S10-only升级；T05/F6/T14的范围不足亦在22行逐项列明。由GPT判断可采范围及下一步边界。本次只申请独立技术复核具体BLOCKED交付，在#34正式回执REST逐字读回后立即STOP，不自启S11或P022。
