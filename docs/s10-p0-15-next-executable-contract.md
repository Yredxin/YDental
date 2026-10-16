# S10-P0-15 固定源码合同与下一最小工作包

本文件只提出下一步，当前授权不允许执行。唯一父Git `a66c9dfd4b65573a27ff3e45733a87103f17bf32`；以下产品路径/行号均取该提交，完整方法原文、起止行及SHA见 [static-action-contract.json](evidence/s10-p0-15/static-action-contract.json)。判断为 Codex STATIC_REVIEW，不是 GPT 亲测或新REAL_WEB PASS。当前所有执行预算0，S10/生产/T12 BLOCKED。

## F4/T08 文字更正的逐字段合同

| 层 | 真实源码及必要条件 | 应保留的事实 |
|---|---|---|
| 原生入口 | `ydental_clinical/controllers/clinical.py:63` action，POST `/ydental/clinical/action`，auth=user、默认CSRF；SID绑定本人的session，传revision/connection；QWeb `#correct-document` 按钮“Append text correction”，`#correction-reason`。 | 真实原生按钮；不能注入属性、客户端绕过权限或代替本人请求。 |
| store/actor | `ydental_clinical_service.py:52` `_access`及`_document`：medical write、source store/company、患者当前关系；`_eligible_responsible:140`：user.active、公司包含、active membership/employee、medical=write、snapshot capability及资格。S01 `_scope:225` 绑定user/session/revision，`_check:292`展开真实grant，岗位名不授予权限。 | 不把P0-14过去资格自动推广为下一批当前资格。 |
| acquire及锁 | clinical `_operate:104` 在savepoint内使用queue._locks（patient/supply/intake公共fence；queue._locks实际转调intake._all_locks，不据此声称更新queue自身mutex），再核store/connection；`_acquire:165` 对serving/reserved/verify要求本人有效工位lease，verify拒绝；其余状态只许当前responsible且当前eligible；已有效editor拒绝/过期editor失效有审计。 | doc/editor/session/revision/connectionhash/tokenhash/editorlease/expiry绑定；不是随意建立新接诊。 |
| 持有及版本 | `_held:190`和`_valid_editor:150`核当前资格、session revision/store、expiry/lease、本人editor、connection及token；`_append:213`校验expected_version非负整数、key16–128，digest覆盖expected_version+完整content+kind+reason；同key作者/digest一致才可识别既有结果，CAS不等拒绝。 | 本批不执行重试。冲突、响应不确定、已提交但release失败均STOP，不能再次correct。 |
| correct不是confirm/save | `_correct:249`持有editor且非空reason；`_append`仅confirmed可correct，非空内容；append新number=expected+1、kind=correct、author=current uid、reason、previous=最新版本、template。save/confirm拒绝confirmed；confirm用于确认原文，save用于草稿。 | 若未来独立父源确为v3，应只追加v4 previous3，原v1–3逐行不变，仍confirmed。此条件不允许复用P0-14。 |
| 文本/审计 | `_content`固定七文字字段和teeth结构；S01 `_audit_values:308`固定user/store/category/target/before/after/reason/source，clinical._audit:47为clinical_document来源；correct写before.version3/after.version4及原因。`ydental_access_audit.py:22/25`禁止write/unlink。 | 只更正已批准合成非医疗标记；其余原文字段/牙位完整保持，不发明诊断、用量或病史。 |

JS `ydental_clinical/static/src/document/document.js:102–175`：changed标记dirty/generation，**只有非confirmed**才900ms autosave；已confirmed编辑不自动保存草稿。correct从实际页面取完整content/expected_version/key/reason，terminalPending禁并发保存；成功后原生脚本自动release并GET重定向。`document.js:240–256`每heartbeat间隔尝试queue/editor heartbeat，saving或needsReconcile时跳过；本合成来源旧参数2秒（`ydental_treatment_test/tests/common.py:87`），源码配置要求正数且小于timeout。填文案期间仍可能heartbeat，不能复制P0-14“未改原文、heartbeat0”的预算。未来需单独冻结原生计时和所有redirect GET/heartbeat上限；禁止停表、伪造数据属性或拦截成功响应去省预算。

S01 `ydental_access/security/ir.access.csv`没有audit普通访问条目；审计由已鉴权service `_audit` 内部创建，不能直接RPC造audit。临床 `security/ir.access.csv:2–3`只给基础组document/version的read；版本模型 `ydental_clinical_version.py`用私有mutation创建、number/key唯一约束并禁止write/unlink。上述固定产品内部受控权限机制仅被静态读取，本批没有执行sudo。

纯文字路径的业务写集合应限于 `ydental_clinical_document` editor/content/version/saved_at、`ydental_clinical_version`追加版本及`ydental_access_audit`追加acquire/correct/release与页面阅读审计。外围原生登录可能新增/更新res_users、res_users_log、access device/session及公共fence、ORM signaling等，必须按下一批真实入口逐字段重新冻结，不能照搬通用白名单。clinical GET还可产生`clinical.view`与`source.view`，terminal redirect GET必须计数。

固定 `_correct→_held/_append` 没有治疗bookkeep、库存move、出账或退款调用；AST直接调用集也单独固定。未来实证仍必须逐行比较费用event/fee/source、price/snapshot、account.move/line/payment/partial、S10 payment/refund/close、stock move/line/quant/lot、附件及所有禁写表，不能以静态“无调用”替代零副作用实测。

**当前来源结论 NOT_AUTHORIZABLE_PENDING_SOURCE**。合法后续需要一套新的、独立授权的纯合成已确认父文书/患者/接诊责任链与已批准非医疗更正文案；可先只授权其准备合同，不预设伪造v3。若父版本不是3，应如实expected N→N+1，不能为了截图强凑v4。W5 pending2不能通过重confirm准备；P0-14 v3克隆禁止复用。未知原文时不编写更正文案。

## T08 数量、药品实物与钱款合同

| 动作 | 真实产品方法/原生入口 | 经济与库存结果及阻断 |
|---|---|---|
| 治疗/椅旁数量更正 | `ydental_treatment/models/ydental_treatment_service.py:470` `_correct`；controller `treatment.py:81` `/ydental/treatment/action`；QWeb:102 “Append quantity correction”，JS workbench:51/74绑定medical lease。`_medical:119`/`_serving:104`要求当前serving、本人有效medical lease、snapshot不漂移、患者关系及当前文书CAS。 | 只支持confirmed treatment/chairside，同患者；delta有限且符合原生UOM精度，累计net≥0；负delta不可同时附材料；chairside旧药关联不足拒绝。不能拿已handover W5过期lease直接更正，不得重建旧接诊避门禁。 |
| 价格与费源 | `_event:285` correction parent继承原price_snapshot/review，不按新620重价；`_quote:245`普通新事件按真实发生时点取S05价；`_settle:365`库存证据齐再建新fee、parent_fee、signed qty×旧unit_price/currency.round。 | 追加独立correction event/fee，不改旧行；pending不能伪造fee/半库存。正delta及新材料可消费原生库存；负delta不是自动实物退回。 |
| S09检查更正 | `ydental_exam/models/ydental_exam_service.py:340` `_correct`，经exam controller `/ydental/exam/action`；`_editor:198`要求原responsible、CAS及session/revision/connection；`_version:259`追加previous/actor/reason。 | 更正findings/measurements/conclusion、保留未改measurement，result/version及audit写；不是数量修正，没有治疗_event/bookkeep或库存调用。检查实际执行 `_perform:307`才产生原始event/fee。 |
| 发药数量修改支持边界 | 治疗 `_dispense`依据原order line/方向、当前pharmacy lease、实际SKU/单位/批次/余额；`_correct`父kind白名单排除prescription。 | 已发生发药不能以通用quantity correction改剂量或原单余额。若需专门药品数量/费用更正功能，需另行极小产品设计和授权，本批无改动；不能用退药或退款冒充该功能。 |
| 实物退药 | treatment `_return_material:489`：prescription取pharmacy write，否则medical write，必须event链接真实done consumption/inventory；调用inventory `_return:399`，QWeb:104 “Receive physical return into quarantine”。 | 库存parent实际只接受done replenishment/prescription；泛化材料return按钮不表示treatment/chairside stock parent被后端支持。lot/product/UOM沿parent，同source key防重复，累计退回≤实际发出；customer→quarantine、独立return event/native move/line/quant，原fee保持；`_remaining:628`只按原prescription事件扣余额，实物退回不重新开放处方发药allowance。 |
| 隔离后复核 | `ydental_inventory_service.py:412` `_verify`，独立warehouse write，parent return、累计数量、release/discard与lot可用性；`_move:305`真实native stock.move/line/_action_done。 | quarantine→可用库或损耗须单独授权复核；收到实物不等于可直接发药，也不等于已实退现金。 |
| 反向记账 | `ydental_settlement_service.py:258` `_bill_correction`，需原negative parent_fee、原source/invoice同store；原out_invoice，原金额上限，创建原生posted out_refund与新source/旧priceversion。 | 数量correct先追加event/fee，并不自动调用本接口；另一次`_bill:173`选择单条negative fee、核`_close_guard_any:330`后才进入反向记账。只按min(原应收余额,反向额)核销；旧已paid/residual0可形成贷项而无现金出款，返回actually_refunded0。必须单独授权经济写/日结日期与并发边界，不能称零款写。 |
| 实退资金 | settlement `_refund_execute:520`及实际退款原生审批/证明/渠道/时点合同；权限、不同审批者、额度、日结锁、幂等与native account.payment独立。 | 真出款才有outbound/payment/partial/实际退款状态；此路径没有库存补回。历史退款14、close9、退款13分页及500/240不重复。 |

数量更正的 `_operate:64` 先核category write/company、queue connection，再在savepoint内queue._locks→inventory._lock→advisory32008，重核权限/连接及actor+key请求指纹并追加receipt；库存 `_operate:128`有独立来源/操作键/锁，`_source_action:438`只许受控真实来源及冻结价格。并发、断网响应丢失、跨日/店/法人、过期批次/配置失败等没有因为这些源码检查而获得新的动态PASS。不同接口返回类型及store/date锁也不能用同一个通用白名单覆盖。

## 历史原版、当前渲染及内部票据

`ydental_settlement/controllers/settlement.py:135` GET `/ydental/settlement/pdf/<kind>/<source_id>`；`_report_payload:1077`要求settlement read及export write，绑定公司/门店/患者与原生单据。bill来自当前source links、原冻结priceversion、原金额，实收来自当前原生payment partial，应收取当前invoice.residual，经办人也是当前请求人。`_validate_pdf_scope:1146`前后payload hash只防当前渲染漂移，不提供历史字节档案。

`_pdf:1159`每次`_render_qweb_pdf`，zh_CN、force_report_rendering、report_pdf_no_attachment=True；检查magic/≤10MB/≤20页，写`settlement.report_download`，after仅kind/pdf_sha256；controller输出Content-Type/attachment及`X-YDental-PDF-SHA256`。report action `report/ydental_settlement_reports.xml:2`无attachment/attachment_use；QWeb `report/ydental_settlement_templates.xml:1`明确内部演示、非税务/非银行渠道到账，bill显示fee/原价格版本/金额、total/received/residual。它不能承诺跨次相同字节（当前operator及渲染元数据等可能不同）。

`ydental_print/models/ydental_print_job.py`是clinical/prescription/consent的短期演示数据库binary任务，不含settlement bill。print service `_generate:273`核实际source digest/CAS，生成后保存字节及digest、session/revision/key，15分钟过期；`_job:261`再次核actor/session/revision/store/expiry及当前source signature；`_deliver:309`读已有字节并核PDF digest，才是有效临时job的原字节交付，不保证永久历史重印。源变更、过期或换session均可能拒绝。

旧索引八份R3外部PDF的SHA由GAP-02继承保存，包括bill-f2 `cfa63dce5228dfd7d85cb7538cd9d40c462b1cacdeb07ec814e985580b81b17a`、receipt-f2 `121432b78ce740d2ab2a49a3deccd7a053258fd065674bb82375c515a6711144`及五份退款PDF/一S09报告；本批只读公开索引，未打开私有原件或再作字节/视觉验证。W5同源历史原件缺失，不能以这些R3文件或新render填补。

## 唯一推荐及最小前置缺口

**暂无一条本批固定公开证据已完整证明全部前提、可直接启动的业务路径。唯一保留候选是“W5同源paid740/0的首份当前内部账单PDF”，状态 NOT_AUTHORIZABLE_PENDING_SOURCE。** 它不重复旧收款、原文确认或退款，也不声称历史原版；纯文字correct与历史重印的来源缺口更大。旧P0-10主候选“再次确认doc1”已被P0-14完成，明确退役。

最小下一工作包应只补此候选的**来源/权限资格只读门禁**，另取正式授权：在执行前冻结严格只读SQL、连接预算和API检查点，投影W5 user5/store1/company1的active user、company_ids、在职membership/employee，实际grant `ydental_membership_id/ydental_category/ydental_level` 中settlement≥read、export=write；核相关report模块、安装态action/template及原740/0源链接的固定一致性。**该前置包不CREATE、不登录、不render、不补grant或安装/同步模板。** 本批SQL0；不在本文件嵌入可执行SQL或启动器。

依据：固定W3 `scripts/s10_e2e_w3_prepare.py:51`给manager settlement write，调用treatment_common.setup→common.setup；`ydental_treatment_test/tests/common.py:41`确有manager export write的设置意图；历史W5 membership行确有user5/store1/active。但公开P0-10 SQL的34条grant只投影id/create/write元数据，**没有上述三个业务字段**，也没独立投影employee.active/current company scope。不能把脚本意图、岗位名、create_uid=5或count34解释为当前实际export资格。原生PDF依赖和安装态也未在本批现场核验。这是最小缺口，无须先改产品代码；如实际grant不满足直接STOP，不能擅自补授权。

前置只读包只需4条真实断言：①W5名称/OID2100310/cluster/marker/config与固定643表身份吻合，源未变；②user5公司/在职/actual settlement read与export write逐字段满足；③invoice1原四fee/source与原生paid740/residual0及PDF report安装态满足；④只读事务rollback/连接close，源无写、无CREATE/HTTP/Firefox/业务POST。任一字段缺失、值不符、并行授权/ref漂移、意外连接或写入、凭据/私有内容外泄风险均STOP。不能通过修权限/换actor/安装模块推进。外部到账政策不因只读门禁而通过。

如未来该门禁成立且另获执行授权，唯一候选的合同为：

| 项 | 尚未执行的精确约定 |
|---|---|
| 来源/准备差异 | W5 pending2源保持，唯一新隔离合成克隆（不得P0-14/P0-13），父643表/身份先核；不升级、不重confirm、不新建经济事实。新克隆及双源保全预算届时独立授权/冻结。 |
| actor/按钮 | user5本人，store1/company1、actual settlement read+export write；`ydental_settlement/views/ydental_settlement_templates.xml:81` invoice1 “下载中文 PDF”，GET `/ydental/settlement/pdf/bill/1`，controller pdf→service `_pdf`→上述模板。登录/列表GET/重定向及按钮单次GET须精确计数，不顺手下载receipt/refund。 |
| 对象版本 | invoice1 posted740/residual0、fee1–4/四source/原price snapshot和两payment partial逐行hash作为CAS前提；该bill没有clinical document版本参数。原文pending2无需确认；不假称v3是bill版本。 |
| 非经济副作用 | PDF成功仅预期S01 settlement.report_download新增1、actor5/store1/target account.move1、kindbill/pdfhash；外围login/device/session/阅读audit、资产/ORM缓存signaling须下一批独立逐字段冻结，不能宣称总表只动audit。no_attachment上下文不能替代实测附件/filestore全等。 |
| 经济副作用/代码 | 费用、价格、账单、付款、退款、日结、库存各表逐行零变；产品路径已有，不需addon改动。依赖或安装态不符即STOP，不临时修产品/重装渲染器。 |
| 4条业务断言 | ①本人原生按钮仅一次成功PDF响应，magic/页数/bytes/SHA与响应header一致；②逐页可见原4费源/价格版本/总额740/核销740/余额0、法人门店患者来源正确且内部非税务标签；③同源经济/库存/旧临床/附件/filestore及所有禁写表全等，只允许预先逐字段冻结的非经济差异；④原W5前后独立只读全643表相等、全部进程/连接有界退出，证据封存。 |
| 所有STOP | 资格/源/模板/资产/元数据/白名单不符、GET多计或漏redirect、PDF渲染/页面/浏览器失败、UNKNOWN提交结果、意外写入/信号11、并行ref/授权漂移、预算超限立即STOP；不重试render、补钱款或重复历史动作。未获新授权不得执行。 |

有序备选仅两条：第一，先设计新的独立纯合成已确认父文书和非医疗文字更正fixture，明确来源与确认准备不能重放W5/P0-14，仍待来源授权；第二，建立W家族同源历史原始PDF留存与字节取回合同，是否需要极小addon持久原件功能须独立产品授权，现有动态render和15min job不满足永久原版。两者均不是当前READY，不以备选扩成整S10重跑。

正常提交推送后只发表正式Codex静态交付并REST逐字读回立即STOP。任何后续只读门禁、CREATE或业务执行均由GPT下一次独立授权决定。
