# S10-P0-10：同源费库款、更正与原版重印可行性只读报告

**W3→W4→W5的真实克隆血缘与740/500/240原生账款可以追踪；R3的渠道更正、数量更正、实物退药分别存在，但属于不同患者/门店子案例。五库均无已有clinical print job，不能提供W5同源原版PDF重印正例。** 本批只读取证；S10整阶段技术/生产BLOCKED。

授权 [6208516504](https://github.com/Yredxin/YDental/issues/34#issuecomment-6208516504)，SQL前预检 [6208878059](https://github.com/Yredxin/YDental/issues/34#issuecomment-6208878059) 已API逐字读回；固定起点 `22d4762c8ddc0b8254b3492fe3ccc75664b5cf47`。22/22原断言/旧状态、P0-02—09限定增量/固定commit/回执与裁定逐行见[覆盖报告](s10-p0-10-gap02-coverage-report.md)与[coverage.json](evidence/s10-p0-10/coverage.json)，本报告不提升任何完整TC。

## 来源可采性、封存与真实克隆证明

仅五座授权既有合成库各一次严格只读REPEATABLE READ连接；先核本地config/marker SHA，SQL核实际库名/OID/cluster7694897083368259627及无其它连接，结束全部rollback/close。全部STATIC文件身份匹配、READONLY_SOURCE签名匹配，UNAVAILABLE_OR_DRIFT=0；无新建/恢复/写回/运行Odoo。基线算法不同明确保留：P0/R3按jsonb文本排序逐行追加换行，W链按ID排序且空表也含换行；不能横比不同算法哈希。

| 来源/固定commit | 库名/OID | config SHA / marker SHA | 现场封存匹配与限界 |
|---|---|---|---|
| P009 / `22d4762c8ddc0b8254b3492fe3ccc75664b5cf47` | `ydental_s10_test_20261016_p009_9e51b7c2` / 2100324 | `743808ca70ebf1baff4b4fc0a8191c7bcd7b514ec74d6096dfb4ddd5da45e2a9` / `59347fb41fb9a8593620fb94da4852a1bcaf0c7fc48f8379c6d7b68502212fdc` | 643表匹配，194文件/1075附件；READONLY_SOURCE_MATCH |
| R3 / `f24b0302569aefaa394391da6b696d915e3f0616` | `ydental_s10_test_20261014020300_8b6c1d4e` / 2056451 | `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778` / `96d261798a4b4370772d5700ba8516dd7677d2568f2b3fda80d3572b94a644e6` | 265表匹配，184文件/1070附件；READONLY_SOURCE_MATCH |
| W3 / `71a554667157cdd917c0062db5e4ddf1693f6410` | `ydental_s10_test_20261015060000_b6c7d8e9` / 2100285 | `dfc2d64d3cd32565bd8e901ca547cfe60170f8cc8c0826adfd77ff65c345eb45` / `8b923d1df4f2a285bb65a87779ee3410ef3529319b9cd0bb8a434d8f4be1c736` | 38表匹配，152文件/164附件；READONLY_SOURCE_MATCH |
| W4 / `79417da9043478501ffae586f93eebc1e5d7105d` | `ydental_s10_test_20261015064000_d41e7b62` / 2100301 | `464f29204afd03c63d1450db442f4d42454e1d164243ca6bb1dbe8eb787b10ba` / `82aaa9c49144987eaa2bf08268db145b62bb55f3ebd5fb373d94dfbd4e101b4a` | 38表匹配，152文件/164附件；READONLY_SOURCE_MATCH |
| W5 / `287881a824e9a18dd637522c570f74df139078f9` | `ydental_s10_test_20261015073500_e50f4a71` / 2100310 | `867f761771ecc20931f69103388df699b094b748e6a9d392e15ebe3d406e43c7` / `1a7f4a2a95e8aa0ea3d6da17abf6033976d2e39754185fa38e441a497351a5fa` | 31表匹配，152文件/164附件；READONLY_SOURCE_MATCH |

W4 marker明确source=W3/OID2100285，并保存W3 marker/config原SHA；W5 marker明确source=W4/OID2100301及其marker/config SHA。两条marker来源身份逐字段相等。进一步独立重读并校验固定历史私有 `before-upgrade.json`、`before-web.json` 的已发布SHA，实际clone-before **38/38签名**与本批父库签名相等；本批W3/W4的38表全等、W4/W5的31稳定表全等。详见[same-source-lineage.json](evidence/s10-p0-10/same-source-lineage.json)。这同时有克隆身份与封存连续证据，才称W链同源版本演进；没有把三个库的相同数字ID当同一业务的唯一依据。

R3→P0-09属于另一独立合成源家族。中间P0-02/03/04/06/07/08只静态引用固定证据，本批未连接它们；其克隆事实不是本批SQL亲测。R3与P0-09的10张原生费库款/更正关键全行签名直接相等；P0-09退款14、close9、receipt242/243及身份/审计则明确保留后继增量。R3 patient1/invoice1与W5 patient1/invoice1业务日、生成时间和哈希不同，不是同一笔付款。

## W链字段级血缘（主源W5/OID2100310，祖源W3/OID2100285、W4/OID2100301）

同一合成patient1、store1、company1、业务日2026-10-15；医生actor7、检查员12、药房13、收款经理5。store.company_id=1与原生move/company1实读；姓名、医疗文字、令牌及密钥不公开。

| 事实 | event/执行/actor | price/snapshot/fee | source→invoice/line | 批次/库存真实关联 | 层级 |
|---|---|---|---|---|
| treatment 1.0×600.0=600.0 | event1 / execution1 / actor7 | price1(记录revision4)→snapshot1(revision1)→fee1 | source4→invoice1/line4 | consumption[1]→inventory[3]→lot[2]/move[3]/move_line[5] | READONLY_SOURCE；fee→source关系见下说明 |
| exam 1.0×80.0=80.0 | event2 / execution2 / actor12 | price2(记录revision4)→snapshot2(revision1)→fee2 | source3→invoice1/line3 | consumption[]→inventory[]→lot[]/move[]/move_line[] | READONLY_SOURCE；fee→source关系见下说明 |
| prescription 4.0×10.0=40.0 | event3 / execution3 / actor13 | price3(记录revision4)→snapshot3(revision1)→fee3 | source2→invoice1/line2 | consumption[2]→inventory[4]→lot[1]/move[4]/move_line[6] | READONLY_SOURCE；fee→source关系见下说明 |
| prescription 2.0×10.0=20.0 | event4 / execution4 / actor13 | price3(记录revision4)→snapshot4(revision1)→fee4 | source1→invoice1/line1 | consumption[3]→inventory[5]→lot[1]/move[5]/move_line[7] | READONLY_SOURCE；fee→source关系见下说明 |

费用合计600+80+40+20=740；source按创建次序逆临床顺序为fee4/3/2/1→source1/2/3/4，不假定ID顺序相等。**投影限制**：新只读JSON未将`ydental_fee_id`列加入脱敏字段，因此该字段关系取固定W3 `business.ydental_settlement_source`（COMMITTED_NATIVE_SQL）；本批三库该表全行SHA相等支持保全，不称本批独立字段投影。price记录revision4与snapshot revision1是不同对象版本字段，结算source写S05:price_id；不能把快照revision1误作price记录revision4。

原生stock move1/2分别物料/药品入库20；lot2/product6物料20→19，lot1/product5药品20→16→14。实际出库move3=物料1（move_line5，location20→24），move4=药4（line6，19→24），move5=药2（line7，19→24），均done/company1/store1；检查无假材料move。对应inventory_event3/4/5、consumption1/2/3，批次batch2→lot2、batch1→lot1。这个药6=真实4+2，不是需求数代替发药事实。

| 账款对象 | W4/OID2100301付款前 | W5/OID2100310付款后 / 实读关联 |
|---|---|---|
| account.move1 | out_invoice/posted740，余额740 | 原posted740仍保留，payment_state paid、余额0，company1/journal1；商品line1—4及应收line5 |
| 第一次Web收500 | 无付款 | S10 payment1→native account.payment1/reconciled→posted move2/journal8；AR credit line7，partial1 amount500连接debit发票line5；receipt2记录余额240 |
| 第二次Web补240 | 无付款 | S10 payment2→native account.payment2/reconciled→posted move3/journal8；AR credit line9，partial2 amount240连接同line5；receipt3记录余额0 |
| 资金科目/分摊 | 应收line5/account5 debit740 | liquidity line6/8 account51各500/240，应收credit7/9 account5；两posted entry各借贷相抵，两partial合计740。payment_invoice_rel只各关联invoice1 |
| 日期/角色/审计 | bill receipt1，S01旧322行 | payment actual_at 2026-10-15 07:52:02.559463 / 07:52:03.952418 UTC；cashier5/store1/patient1，S01 settlement.pay accepted327/330 |
| 本批再验证上限 | 38表匹配封存 | 31稳定表匹配RO1-R1、资金move/payment/partial投影精确匹配；不是新执行Web，也未独立证明现实现金到账 |

以上真实Web两笔由历史W5 Codex回执/GPT裁定支持，本批SQL只证明当前已提交原生行仍对应；W5 browser exit1、final_audit NOT_RUN永久保留。receipt命令结果在本批脱敏JSON只hash，完整allocations取固定RO1-R1公开机器证据，不伪称本批打印其明文。

## R3单库更正、锁与实物退回筛查（OID2056451，P0-09经济同签名后继）

| 子案例 | 同源对象/金额/店/患者/actor | S01/原生关系 | 已成立与未成立 |
|---|---|---|---|
| F3现金标签更正微信 | patient2/store3/company1，cashier14，业务日2026-10-13；S10 payment6 amount100→native payment6，invoice5；correction1 cash→wechat→posted account.move14 | close1 cash100已由finance15解锁、close2 wechat100 confirmed；S01 476 close1→477 unlock1→478 correction1→479 close2；更正只做原生重分类，无新患者资金收退 | 单库模型历史链及本批字段可采；没有本批Web更正/重结；不能称新错日期绕锁负向已测 |
| 另日真实退款 | 同payment6，refund1 done100，approver/execute15，refund_business_date2026-10-14，wechat | credit note15、native outbound payment7；close4收费员15/wechat/2026-10-14已退100；旧申请收费员14的close3 unlocked | 真正退款是独立事实，不误认为渠道更正造成；未知/响应丢失全恢复仍缺 |
| 数量更正 | patient4/store7，原event13→correction event14(parent13,qty-1)，fee13 +600→fee14 -600(parent13)，snapshot13，source13/14 | invoice78原600与credit79，actor34，原事件/原因与价格引用保留 | 真实单库反向来源；不是patient1的4+2药方，也不是W5文书补录。不能拼成同患者完整F4 |
| 实物退药隔离 | R3 patient1/store1、原治疗处方event3，consumption2→inventory4药4/lot1；inventory19 return1(parent4)→stock.move19/line26 | line26实读location24→22，product5/lot1/company1；STATIC_REVIEW _return按config.quarantine路由；库存配置quarantine字段本批未独立投影 | 真实退回1与原出库有关联，**不能称售药可用库存自动+1**；不与patient4的数量贷项拼同源；本批未重退 |
| 更晚锁周期 | cashier14/store3/cash/2026-10-13 close62 cycle2 unlocked，最新close63 cycle3 confirmed/gross11 | 必须以最新cycle63判锁，不可只见早期close1 unlocked就说该日不锁 | 仅状态筛查；错实际日/业务日组合负向NOT_RUN。旧close9属于store1/card/2026-07-15，与此不同 |

R3有四状态结算PDF及S09报告历史字节，下表只重新读取原文件SHA和PDF magic，**没有本批渲染、提取或逐页视觉复核**；它们不提供W5同源原版。

| 固定已有文件 | 字节 / SHA | 本批结果 |
|---|---|---|
| bill-f2.pdf | 27664 / `cfa63dce5228dfd7d85cb7538cd9d40c462b1cacdeb07ec814e985580b81b17a` | PDF_BYTES hash匹配；本批视觉NOT_RUN |
| receipt-f2.pdf | 28023 / `121432b78ce740d2ab2a49a3deccd7a053258fd065674bb82375c515a6711144` | PDF_BYTES hash匹配；本批视觉NOT_RUN |
| refund-approved.pdf | 25248 / `83ccdd8633362c2aab407516b8ff6f48d10cf6cd366a0396d15cd87af12d11fd` | PDF_BYTES hash匹配；本批视觉NOT_RUN |
| refund-done.pdf | 26346 / `1f5ea396fcceef9b9fd7915f1a4e93a72637abd2a3be24272738bac91dc06a66` | PDF_BYTES hash匹配；本批视觉NOT_RUN |
| refund-f2.pdf | 26346 / `d947e3b84df66d2f0081a2ae141d5714398edb0cab9bc4d32ab3dc6e05707b49` | PDF_BYTES hash匹配；本批视觉NOT_RUN |
| refund-rejected.pdf | 25339 / `f68dbc1f0648c8a21e398de8b5c5c4f7820ffcf886205487aa77101403b464c3` | PDF_BYTES hash匹配；本批视觉NOT_RUN |
| refund-unknown.pdf | 25487 / `20b12d29910422faa996743e6919903e1465566defe3dd1b83855f7d95df21c4` | PDF_BYTES hash匹配；本批视觉NOT_RUN |
| s09-regression-report-223.pdf | 26494 / `236602bb37a04fc97a6b97cd5e28e19da16887b3d3e80ead620c3e781d62373a` | PDF_BYTES hash匹配；本批视觉NOT_RUN |

## 现行源码入口、幂等与PDF可行性

本批W5安装态view/module元数据未作独立SQL投影，现行QWeb仅STATIC_REVIEW文件及历史固定W5证据；下一批必须CREATE前重新核已安装arch和权限/资格，不把源码相同当现场视图必然相同。

源码仅静态读取，产品/核心零修改，文件SHA及函数行号见[source-entry-review.json](evidence/s10-p0-10/source-entry-review.json)。使用odoo-guidelines的事务、控制器、报告条目核读，未运行这些入口。

| 入口 | 静态合同与预计副作用 | 对本批/下一批的限界 |
|---|---|---|
| settlement._operate/_lock | 本人当前scope/write/finance，业务key+fingerprint；共享advisory锁和mutex revision+1；成功追加receipt；异常savepoint回滚 | 本批SQL不调用；若未来业务命令必须冻结mutex/receipt字段，不能整体豁免或误认为都是资金 |
| _reclassify/_close_guard/_unlock | 更正使用原payment cashier/day，检查旧/新渠道最新close；生成同公司平衡重分类entry及correction/S01；unlock须财务权/原因及最新cycle | 已发生F3可只读追踪；新错日期负向不得虚构实际时间，更不能重放旧unlock9 |
| clinical._acquire/_append/_confirm | 已离开serving/reserved/verify的文书可由合法responsible完成；当前资格/公司/medical write仍需核验。独占editor+session/revision+connection、expected_version/new key，确认追加版本；临床使用queue._locks公共fence | W5 doc1 pending/version2、responsible7是安全较小的后续源；资格所有字段本批未独立投影，未来CREATE前须补只读/源码校验，不满足STOP，不能自动新接诊 |
| treatment._return_material / inventory._return | 原treatment消费和原inventory事件关联，真实退回写客户→待核隔离location，审批后才可能release；不把财务贷项等同实物退回 | 本批只读现有inventory19。下一主候选不需要退药/库存写 |
| settlement._report_payload/_pdf | 每次从当前invoice/payment/refund投影；QWeb生成临时字节，zh_CN、no_attachment，S01 report_download；包含当前残额/退款状态和操作者 | 没有固定历史字节的原版读取入口；不能将当前渲染当以前未付款/在途票面原版。重新渲染hash也可能随操作者/状态变化 |
| print._job/_generate/_deliver | job绑定本人actor/session/revision/store与15分钟期限，重新核source_digest；生成保存DB二进制并审计，_operate有session fence及权限行锁 | 五库job均0；无可重印旧job。会话/期限不符或源变更需新演示副本，不属于S12正式永久原件 |

原版重印与调价600→620目前为 `NO_ELIGIBLE_SAME_SOURCE / INSUFFICIENT_EVIDENCE`：W链没有620价源和已有PDF；R3确有同catalog16/store7的price7=600与price8=620，snapshot13仍指price7/600、source13→invoice78/line160=600；后续source14→credit79/line162=-600。此patient4价源冻结有单库证据，但已保存PDF和report_download审计目标是其它invoice1/患者1等，不能拼成patient4调价后原版重印。没有可靠现有原版源的重印候选明确 `P0_11_NOT_AUTHORIZABLE_PENDING_SOURCE`。本报告未证明产品有bug，也不擅自扩张S12或修改PDF生命周期。

## 全22项与同源候选关系（原状态全部保留）

| 项 | 原始断言 / 历史状态 | 来源可采性、本批同源结论及剩余最小缺口 |
|---|---|---|
| F1 | S10-F1（独立合成数据）：治疗600+检查80+发药6×10=740，出账740→实收500欠240→补240结清。重复请求不再收款/出账。；SCOPED_ACCEPTED | 旧证据E-C, E-R3, E-W3, E-W5, E-R1，delta无均见覆盖报告固定目录；只读已结清W5费库款可保全；若用户最终要求单Firefox23步验收，另行限定，绝不重发旧500/240。；否；不重放旧钱款 |
| F2 | S10-F2：已收740→申请退100→他人批准，在途100/实退0→确认真实退100，累计已退100/净收640。拒绝另一申请须原因且不产生退款。；PARTIAL | 旧证据E-C, E-R3, E-FC1, E-FC2, E-UI4，deltaP0-03, P0-09均见覆盖报告固定目录；只补尚未证明的退款unknown/响应丢失恢复真实性，先固定非重复候选；外部渠道核验仍待政策。；完整实退子链需要；本批0 |
| F3 | S10-F3：实际微信录成现金且已日结→财务审批解锁留原因→更正登记→再日结，没有真实资金往返；实物退药另进待核查。；PARTIAL | 旧证据E-C, E-R3, E-FC1, E-FC2, E-UI4，deltaP0-04, P0-06均见覆盖报告固定目录；旧close9可见与unlock已证明；同店同收费员错业务日绕锁、更正与重结组合仍缺。；可能产生原生渠道重分类；非真实资金往返 |
| F4 | S10-F4：真实诊疗/检查/发药、批次扣减→结算→补旧文书/重印票据，费库款不再变化，调价也不改原已确认费用。；PARTIAL | 旧证据E-C, E-R3, E-W3, E-W4, E-R1，delta无均见覆盖报告固定目录；W5文书1 pending/version2且费库款已结清；优先只补原责任人的文书确认零经济变化；原版PDF基线不存在。；文字确认不需；数量/实物更正另需 |
| F5 | S10-F5（另一个独立场景）：旧账270、新账200，均选中，实收300→先核旧270，再核新30→旧账0、新账欠170，保留两张账单和一笔300收款。仅选新账时不得擅自核旧账。；SCOPED_ACCEPTED | 旧证据E-C, E-R3，delta无均见覆盖报告固定目录；保留270+200模型限定接受；此组合真实Web仍缺，当前不为覆盖重收300。；若新场景真实付款会需要；本批0 |
| F6 | S10-F6：前台小李有A结算权可从前台收款，无结算权者只能看到获准摘要。B看到A欠270仅只读；不能在B收A款，A权限且上下文合法时到A处理。；PARTIAL | 旧证据E-C, E-R3, E-UI4, E-UI6, E-UI7，deltaP0-04, P0-06, P0-09均见覆盖报告固定目录；列表store3过滤与两种unlock拒绝仅限定路径；直接票据/RPC/附件及患者合并矩阵未齐。；否 |
| T01 | S10-T01；740重复/并发出账；来源有效出账一次；SCOPED_ACCEPTED | 旧证据E-C, E-R3, E-W3，deltaP0-02均见覆盖报告固定目录；P0-02只同步视图；C并发唯一账仍可采，R3崩溃竞态未运行；勿为补表再次出账740。；完整新竞态会有出账；本批0 |
| T02 | S10-T02；740收500补240及重试；应收240→0，原生核销和实收一致；SCOPED_ACCEPTED | 旧证据E-C, E-R3, E-W5, E-R1，delta无均见覆盖报告固定目录；W5既有两付款/partial/残额0经本批复核；原浏览器收尾仍NOT_RUN，外部到账未证。；不需重发；禁止重收 |
| T03 | S10-T03；负/超额折扣、明确免单；非法拒绝，原因齐，零账无假收款；SCOPED_ACCEPTED | 旧证据E-C, E-R3，delta无均见覆盖报告固定目录；零账及折扣模型证据保留；Web零额/原因/权限组合缺。；新0元账有原生发票写，无款物 |
| T04 | S10-T04；退款自批与并发批准；自批拒绝，在途+已退不超允许额；PARTIAL | 旧证据E-C, E-FC1, E-FC2，delta无均见覆盖报告固定目录；P0-03是驳回，不证明双审批竞态；保留FC1/FC2，响应丢失/不同key额度组合待核。；批准本身无出款，额度状态有写 |
| T05 | S10-T05；退款失败/未知/实际完成/重试；不伪已退、不重复资金记录；PARTIAL | 旧证据E-C, E-R3, E-FC1, E-FC2，deltaP0-03, P0-07, P0-08, P0-09均见覆盖报告固定目录；13页2可见及14驳回不证明失败/unknown外部状态恢复；真实HTTP丢响应重试仍缺。；完整实际退款需要；本批0 |
| T06 | S10-T06；未收款减免；只调应收，不记实退；SCOPED_ACCEPTED | 旧证据E-C, E-R3，delta无均见覆盖报告固定目录；未收款减免原生贷项模型已有限接受，生产税/科目待审核。；减免会写贷项，无实际出款 |
| T07 | S10-T07；日结后改支付方式；财务解锁/原因/再确认，无伪退款；PARTIAL | 旧证据E-C, E-R3, E-FC1, E-FC2, E-UI4，deltaP0-04, P0-06均见覆盖报告固定目录；close9合法解锁及跨店拒绝已证明，不再重做；原收费员原业务日更正锁边界与重结未齐。；重分类分录/日结状态可能写，无虚构退款 |
| T08 | S10-T08；已出账数量更正、文字更正和实物退回；反向来源正确，文字不动费库，未退不回库；PARTIAL | 旧证据E-C, E-R3, E-W3，delta无均见覆盖报告固定目录；R3数量event13→14在patient4/store7，退药inventory4→19在patient1/store1；不拼同患者全链；W5只可先补文书。；纯文字不需；实物退回需要 |
| T09 | S10-T09；同法人调拨与跨法人交易；实际收发/凭证对应、公司店铺隔离；PARTIAL | 旧证据E-C, E-R3，delta无均见覆盖报告固定目录；集团多仓政策已批准；异币种/效期/posted失败原子性及同source并发仍缺。；实际测试会涉及原生库存/财务写 |
| T10 | S10-T10；他店代收/无权医疗全文或票据；越权拒绝，摘要与全文分离；PARTIAL | 旧证据E-C, E-R3, E-UI6, E-UI7，deltaP0-04, P0-06, P0-09均见覆盖报告固定目录；user10/14 unlock负向与store3列表过滤不等于PDF/RPC/附件/医疗全文/合并边界。；否 |
| T11 | S10-T11；中文票据及部分收退款；实收/欠款/在途/已退准确，法人门店正确；PARTIAL | 旧证据E-C, E-R3, E-UI4，delta无均见覆盖报告固定目录；R3现有PDF字节hash匹配，不是W5原版；W5 paid740/0当前PDF尚无字节；多状态票面视觉仍缺。；否；渲染可能审计/临时作业写 |
| T12 | S10-T12；安装升级及F4真实全链；事件、价格、批次、费账款一一对应；BLOCKED | 旧证据E-C, E-W3, E-W4, E-W5, E-R1，deltaP0-02, P0-07, P0-08, P0-09均见覆盖报告固定目录；新后继库签名保全及视图同步不消除W4元数据越界、W5退出1；完整S08/S09 HTTP/同Web全链仍BLOCKED。；子缺口文书不需；整链不能以零写补齐 |
| T13 | S10-T13；F5旧270新200收300及仅选新账；核销270+30、欠170，未合并账单；未选不核；SCOPED_ACCEPTED | 旧证据E-C, E-R3，delta无均见覆盖报告固定目录；原270+30/只选新账模型证据保留，特定Web组合未齐且不重复旧收款。；新收款场景需；本批0 |
| T14 | S10-T14；F6前台有/无billing权及跨店摘要；同一结算服务鉴权，无按岗位默认放开，无跨店代收；PARTIAL | 旧证据E-C, E-R3, E-UI4, E-UI6, E-UI7，deltaP0-04, P0-06, P0-08, P0-09均见覆盖报告固定目录；角色自动scope、unlock拒绝与列表最小化仅各自可采；全岗位/RPC/附件/跨法人未齐。；否 |
| T15 | S10-T15；已确认600调价620后结算/重印；退款驳回；仍取600快照；驳回原因和审计齐、不生贷项/退款；PARTIAL | 旧证据E-C, E-R3, E-UI4，deltaP0-03均见覆盖报告固定目录；refund14原因/审计/零出款子断言已接受；同一600→620价源的原版重印字节未齐，W5没有620版本或原版作业。；调价需配置写，无款物；原版现缺源 |
| T16 | S10-T16；日结锁后补录、解锁更正、删除/篡改审计；锁覆盖新增/更正，合法补录双时间可查，单据日志不可普通删改；PARTIAL | 旧证据E-C, E-R3, E-FC1, E-FC2, E-UI6, E-UI7，deltaP0-04, P0-06, P0-09均见覆盖报告固定目录；合法解锁审计与P009新增身份/阅读审计已可采；错日期绕锁、跨日补录双时间及删改RPC广度仍缺。；纯负向应零款物；合法补录可有写 |

## P0-11仅一个主候选和一个备选（均未授权）

### PRIMARY：W5已结清740同源pending文书1一次补确认，费库款签名零变

来源 `ydental_s10_test_20261015073500_e50f4a71` / OID2100310，证据缺口：此动作本批NOT_RUN；不证明纯文字correct、数量退药、600→620、原版重印、全T12或S08/S09回归。

前提：独立P0-11授权及CREATE前/API读回；新唯一隔离克隆且W5永久只读，不升级；doc1 patient1/store1/responsible7/pending/version2；原版本1/2及content hash不变；执行前重新核当前execution/capability/qualification/active membership和本人medical write；本批未独立投影全资格字段，任一不满足即STOP；使用同浏览器connection、本人session/revision、独占editor；不重建接诊工位或价格。

动作：本人user7合法登录/自动scope（若不自动合法绑定，仅明确预算内一次switch）；临床GET定位doc1；acquire一次→confirm既有合成内容一次(expected_version2,new key)→release一次；不发save/correct/新医嘱或经济动作；同库动作前后核event/fee/price/source/account/partial/stock完整签名；doc仅pending2→confirmed3、version追加1及受控编辑元数据/S01。

副作用白名单须事前冻结：身份login/session/device/S01（自动switch须逐字段归因）；临床doc1编辑元数据及state/version、追加clinical.version1、S01 edit_acquire/confirm/edit_release各1；临床GET还会产生clinical.view，按GET次数事前冻结；queue common fence/mutex事务写须按源码冻结，不能误要求该mutex不变；不改变queue执行/工位事实。

最低预算提案 `{"CREATE": 1, "ODOO_HTTP": 1, "FIREFOX": 1, "IDENTITY_LOGIN_POST": 1, "OPTIONAL_SCOPE_SWITCH_POST": 1, "CLINICAL_POST": 3, "FUNDS_POST": 0, "STOCK_POST": 0, "UPGRADE_INSTALL_SHELL": 0, "SUDO": 0}`。switch为至多1，合法自动绑定则0；heartbeat最低0，若执行时间需延长必须正式授权中先定上限，不能运行后放宽。退款14/close9旧负向与W5两笔钱款全部0重放。状态 `PROPOSAL_NOT_AUTHORIZED_CONDITIONAL_ON_ELIGIBILITY_PREFLIGHT`。

### BACKUP：W5同源已付invoice1当前内部账单PDF一次生成/核字节及零经济副作用

来源 `ydental_s10_test_20261015073500_e50f4a71` / OID2100310，证据缺口：原版重印NOT_RUN/INSUFFICIENT_EVIDENCE；生成第一份当前PDF不能冒充旧PDF重印；纯文字更正/调价/锁边界仍不覆盖。

前提：只在主候选不能合法进入且新授权明确选择备选时执行，不能两案都跑；新唯一克隆/无升级、本人user5店1 settlement read+export write及原生PDF环境静态核验；invoice1 posted740/residual0/四费源/两partial原样；没有已有原版PDF基线。

动作：本人登录/合法scope；仅一次GET /ydental/settlement/pdf/bill/1，取得新PDF字节，逐页核740/已收740/欠0及法人/门店，比较经济前后SHA。

副作用白名单须事前冻结：身份元数据与S01；settlement.report_download一次；不是资金动作，也不是原版字节重印；禁止访问退款页2或重复旧权限负向。

最低预算提案 `{"CREATE": 1, "ODOO_HTTP": 1, "FIREFOX": 1, "IDENTITY_LOGIN_POST": 1, "OPTIONAL_SCOPE_SWITCH_POST": 1, "BUSINESS_POST": 0, "PDF_GET_RENDER": 1, "FUNDS_STOCK_WRITE": 0, "UPGRADE_INSTALL_SHELL": 0, "SUDO": 0}`。switch为至多1，合法自动绑定则0；heartbeat最低0，若执行时间需延长必须正式授权中先定上限，不能运行后放宽。退款14/close9旧负向与W5两笔钱款全部0重放。状态 `PROPOSAL_NOT_AUTHORIZED_CONDITIONAL_ON_EXPORT_AND_PDF_PREFLIGHT`。

主候选只确认已有合成文书内容，不能冒称纯文字correct、数量更正/退药、调价或原版重印通过。备选是**第一份当前已付款账单PDF**，不是原版重印；不需要任何结算业务POST。若两案的合法源/权限/入口前提均不能安全满足，整体下一批必须标 `P0_11_NOT_AUTHORIZABLE_PENDING_SOURCE`，不能临时重建临床或收款来补齐。

本批预算实际CREATE/HTTP/Firefox/Chromium/真实或模拟业务POST/SQL及ORM写/Odoo CLI/shell/upgrade/install/test/sudo均0，只读来源5/5；R3 SIGSEGV UNKNOWN、W4元数据越界、W5 browser exit1/final_audit NOT_RUN持续保留。财务政策POLICY_PENDING、#34 OPEN、#35 S11 NOT_STARTED；没有Project/Issue正文或状态修改、合并部署或用户最终验收。最终提交与交付API逐字读回后立即STOP等待GPT独立复核。
