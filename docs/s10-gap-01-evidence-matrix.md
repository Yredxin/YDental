# S10-GAP-01：已有实证覆盖与剩余验收差距

基线：`5876740dabf342372b0970682947e6be8356fa8c`；唯一授权 [#34/6190487418](https://github.com/Yredxin/YDental/issues/34#issuecomment-6190487418)；[预检与API逐字读回](https://github.com/Yredxin/YDental/issues/34#issuecomment-6190538707)。#23 当前正文/3条评论、#34 当前正文/预检前169条评论及 #35 OPEN/0 已经 API 读取。现行原文以 [#34正文](https://github.com/Yredxin/YDental/issues/34) 第5—7节为准；[最终统一用户验收决定](https://github.com/Yredxin/YDental/issues/23#issuecomment-6110178328)仍适用。

## #23第7节交付验收口径

| 项目 | 本批事实 |
|---|---|
| 任务与启用来源 | #34 GPT授权6190487418；仅S10-GAP-01只读证据矩阵，不申请S10阶段技术PASS。 |
| 计划/分支/环境 | #23 R1与#34现行正文已核；起点`5876740dabf342372b0970682947e6be8356fa8c`；原分支`codex/s10-settlement-finance-r1-20261013`；本批只用仓库文件与GitHub API。最终提交由#34交付回执固定。 |
| 需求完成情况 | F1—F6/T01—T16全部22行在下表；没有新产品实现、业务执行或新的技术PASS。 |
| 流程实际回放 | 本批无现场回放。W3/W4/W5与RO1-R1历史链只在血缘图中按各自库/提交引用。 |
| 测试结果 | 仅离线校验22行、证据路径/提交、允许文件差异及JSON语法；Odoo/SQL/Web/PDF新运行均`NOT_RUN`。历史退出码与角色见各固定报告，不能记为本批测试数。 |
| 字段、动作与配置 | 本批不更改字段、业务动作、权限和配置；原生账务、状态、金额、角色按固定证据目录追溯，生产财税配置仍待业务确认。 |
| 用户效果验证 | 本批只提供中文可读矩阵、机器索引和下一批候选；没有真实用户操作或效果验收。 |
| 数据、审计与回滚 | 数据库、业务记录、filestore、历史证据零修改；仅新增三份审计文件，正常Git提交可逆；保留所有旧失败与STOP事实。 |
| 复核申请 | 仅申请GPT独立核对覆盖归类；不替用户验收，不启动候选、S11或部署。 |

## 判读规则

- `SCOPED_ACCEPTED`表示至少一个关键子路径已有GPT限定技术接受，**不表示整条原TC FULL_PASS**；`PARTIAL`有真实证据也有缺断言；`BLOCKED`存在明确停止关口。全矩阵 `FULL_PASS=0`，不重裁定先前GPT结论。`NOT_RUN`只用于实际未运行的子项，`INSUFFICIENT_EVIDENCE`用于尚不能从固定材料判定实现或结果的子项。
- `REAL_ODOO_MODEL`、`COMMITTED_NATIVE_SQL`、`TWO_TRANSACTION`、`REAL_WEB/FIREFOX`、`PDF_BYTES`分别代表已有历史真实Odoo模型/已提交原生账务SQL/双事务/Web浏览器/PDF字节证据。`STATIC_REVIEW`和`SIMULATED_PASS`单独列出，不升级为现场通过。本批没有连接数据库、运行Odoo或浏览器。
- 每行证据代号指向下方**固定提交、库、GPT评论、报告和机器索引**。行中的合成角色与业务源为历史报告身份。本批不能访问GPT未亲见的私有原始HTTP、日志、PNG和PDF；对应现场声明来自Codex固定脱敏回执。不同库的结果仅按克隆血缘关联，不能拼作同一次Web执行。

## F1—F6 业务流程矩阵

| 流程 | #34原断言/拆分 | 已获限定证据、源数据/角色 | 仍缺/原因 | 状态；需新业务执行 | 缺口类别／产品／政策 | 固定证据 |
|---|---|---|---|---|---|---|
| F1 | 600+80+6×10=740；500后欠240、补240结清；重复请求不重复账款；同源四费与两次发药、唯一posted账、两次入款/partial/余额、幂等 | C/R3模型完成；W3真实Web四费与posted740；W5真实Web收500/240；R1只读核对原生凭证/partial/余额0。源/角色：合成患者/店1；经理收款，医生/检查员/药房分别完成来源 | W5 browser exit1、final_audit NOT_RUN；23步不在同一Firefox完成；外部现金到账未证 | SCOPED_ACCEPTED；条件需要单会话验收，非本批；既有资金勿重跑 | NOT_RUN、POLICY_PENDING；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-W3](#e-w3)、[E-W5](#e-w5)、[E-R1](#e-r1) |
| F2 | 收740→申请退100→异人批准在途100/实退0→真退100；有原因驳回无退款；身份隔离、额度、终态、原生出款/贷项、拒绝原因 | C/R3模型正例及驳回；FC1/FC2两事务取消/执行和终态幂等；UI4指定Web退20与异人审批。源/角色：合成收款；申请人、异人审批者、执行人及财务核查者 | 原F2全序列没有同一次真实Web和外部资金确认；响应丢失HTTP重放、更多审批同退款组合不足 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE、POLICY_PENDING；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-FC1](#e-fc1)、[E-FC2](#e-fc2)、[E-UI4](#e-ui4) |
| F3 | 现金误录微信且已日结→财务解锁→更正→重结；无虚构退款，实物退药另核；锁、审批、渠道重分类、重结、无资金往返、实物归库分离 | C/R3模型；FC2更正后微信原生outbound40及当日close；UI4实际Web解锁。源/角色：合成现金误录；经理/前台、财务解锁者、原生渠道日记账 | 合法错日期绕锁、不同业务日/渠道组合与实物退药同链、完整Web更正交互不足 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-FC1](#e-fc1)、[E-FC2](#e-fc2)、[E-UI4](#e-ui4) |
| F4 | 真实诊疗/检查/发药批次扣减→结算→补旧文书/重印；调价不改旧费库款；同一来源链、补录/更正和重印前后逐行不变量 | C/R3模型及库存；W3真实Web治疗/检查/4+2/post740；W4业务签名保全；R1证实W5付款未改临床/库存。源/角色：合成同患者临床/检查/药房源及S07批次、原生账 | 同一完整临床链补旧文书与原版重印、S08/S09必要HTTP回归及全链签名未齐；不合并跨库为单次PASS | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-W3](#e-w3)、[E-W4](#e-w4)、[E-R1](#e-r1) |
| F5 | 旧270+新200收300→270+30、欠170；仅选新账不碰旧；业务日/ID顺序、双账不合并、只核选中 | C/R3真实模型与原生partial，含仅选新账和同日ID顺序。源/角色：合成旧/新两张同店原生账；结算操作者 | 当前UI Web没有同一组合完整选择/付款证据；生产科目及币种映射待审核 | SCOPED_ACCEPTED；非本批；现有关键路径勿重跑 | NOT_RUN、POLICY_PENDING；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3) |
| F6 | 有权前台A收款，无权只见许可摘要；B只见A欠款摘要，B不得代收A；同一服务鉴权、店铺隔离、摘要最小化、切合法A会话 | C/R3模型及HTTP摘要；UI4有权前台；UI6/7撤权/旧页与跨店会话限定负向。源/角色：前台有/无billing、经理、跨店B会话与A欠款摘要 | 跨店原生RPC/附件/完整票据直链及患者合并组合不足；角色矩阵未穷尽 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-UI4](#e-ui4)、[E-UI6](#e-ui6)、[E-UI7](#e-ui7) |

## T01—T16 测试断言矩阵

| 用例 | #34前提/预期与关键断言 | 已获限定证据、源数据/角色 | 仍缺/原因 | 状态；需新业务执行 | 缺口类别／产品／政策 | 固定证据 |
|---|---|---|---|---|---|---|
| T01 | 740重复/并发出账→来源有效出账一次；同费源双事务、唯一posted invoice、重放 | C双后端同源唯一账；R3固定窗口动作前SIGSEGV，不能算R3竞态。源/角色：同费源两个独立PG后端及出账操作者 | W3只单次Web出账，未在该库并发；不同批次限制需保留 | SCOPED_ACCEPTED；非本批；现有关键路径勿重跑 | NOT_RUN；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-W3](#e-w3) |
| T02 | 740收500补240及重试→应收240→0、原生核销与实收一致；两笔Web付款、posted分录、AR partial、重复key | C/R3模型；W5两POST各一次；R1对W4/W5 read-only原生凭证、partial及S01逐项勾稽。源/角色：合成发票1、经理Web现金500/240、原生应收行 | W5完成marker和final_audit未运行；真实现金到账及跨故障HTTP响应丢失不在本条已验范围 | SCOPED_ACCEPTED；非本批；现有关键路径勿重跑 | NOT_RUN、POLICY_PENDING；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-W5](#e-w5)、[E-R1](#e-r1) |
| T03 | 负/超额折扣拒绝；明确免单有原因，零账无假收款；非法折扣、原因、独立0元posted账、无payment | C负/超额拒与免单；R3固定库独立0元posted invoice且无假付款。源/角色：合成折扣/免单操作者、0元原生发票 | 0元Web操作与所有折扣权限/审计组合尚非完整现场；原R3固定双连接未完成 | SCOPED_ACCEPTED；非本批；现有关键路径勿重跑 | NOT_RUN；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3) |
| T04 | 退款自批与并发批准→自批拒、在途+已退不超额；同退款双审批者竞争、同收款额度竞争、无重复贷项 | C自批拒/额度竞争；FC1同一退款批准胜者+另backend40001；FC2取消竞争。源/角色：申请者、两个审批后端和额度来源收款 | 不同请求key及响应丢失场景、外部付款核验未齐；锁对象种类未独立证明 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-FC1](#e-fc1)、[E-FC2](#e-fc2) |
| T05 | 退款失败/未知/实际完成/重试→不伪已退、不重复资金；failed/unknown人工核查、done终态、取消/执行竞争、同key重试 | C/R3模型；FC1执行胜与取消回滚；FC2取消先行、done后重复/拒绝、unknown/failed受控恢复与原生单笔出款。源/角色：退款执行/取消后端、人工核查角色、原生outbound | 真实HTTP响应丢失后同key重放与外部支付状态真实性未测；unknown与实际出款并发不足 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE、POLICY_PENDING；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-FC1](#e-fc1)、[E-FC2](#e-fc2) |
| T06 | 未收款减免只调应收，不记实退；原生应收贷项、payment/refund为0 | C/R3未收款免单原生贷项且无真实出款。源/角色：未收账的免单操作者与原生贷项 | 适用合成模型路径；生产税额和财务映射未批准 | SCOPED_ACCEPTED；非本批；现有关键路径勿重跑 | POLICY_PENDING；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3) |
| T07 | 日结后改支付方式→财务解锁/原因/再确认，无伪退款；锁阻断、授权解锁、原生重分类、重结及退款渠道正确 | C/R3单进程；FC1 close先行；FC2原cash→wechat、微信outbound与新close；UI4 Web解锁。源/角色：收费员、财务解锁者、实际退款人、渠道日记账 | 合法业务日跨日绕锁、不同渠道/收费员组合仍不足；更正Web全入口未覆盖 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-FC1](#e-fc1)、[E-FC2](#e-fc2)、[E-UI4](#e-ui4) |
| T08 | 已出账数量更正、文字更正与实物退回→反向来源、文字不动费库、未退不回库；原事件引用、贷项/新费、文字零经济变化、退药隔离 | C/R3分别有模型更正和真实退药隔离库存。源/角色：临床原事件/文书、药房批次与隔离库 | 同患者同接诊并结合W3费库款/报告重印后的逐行签名与Web动作不足 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-W3](#e-w3) |
| T09 | 同法人调拨与跨法人交易→实际收发/凭证对应、公司店隔离；双法人SO/PO/收发/posted账、非法来源/币种/批次/并发 | C/R3同法人与跨法人原生正例及多种拒绝；集团多仓策略已批准。源/角色：同法人门店及两法人SO/PO、库存与account.move | 异币种、效期/配置失败、同source双事务订单及原生posted失败原子性未获匹配证据 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE、POLICY_PENDING；产品缺口未从固定证据证实；集团多仓/多库位政策已在#6170791208批准；生产公司科目、税、币种配置仍待确认 | [E-C](#e-c)、[E-R3](#e-r3) |
| T10 | 他店代收、无权医疗全文或票据→越权拒绝，摘要与全文分离；店铺最小摘要、原生账/医疗全文/附件/PDF直链鉴权 | C/R3跨店拒与最小摘要；UI6 reader两PDF直链403、撤权及旧revision拒。源/角色：reader、经理、跨店会话、PDF下载者 | 跨法人医疗全文、附件/原生RPC、患者合并后的旧身份访问矩阵证据不足 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-UI6](#e-ui6)、[E-UI7](#e-ui7) |
| T11 | 中文票据及部分收退款→实收/欠/在途/已退准确，法人门店正确；bill/receipt/refund PDF字节、中文、各退款状态票面及多账余额 | C/R3多张中文PDF；UI4三类实际HTTP200 PDF字节/哈希/各1页，覆盖指定60/20部分资金。源/角色：合成bill/receipt/refund及部分付款/退款状态 | 批准在途、unknown/rejected/done、零额/多账组合的实际PDF逐页和法人店边界未全覆盖；GPT未亲见私有图 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE、POLICY_PENDING；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-UI4](#e-ui4) |
| T12 | 安装升级及F4真实全链→事件、价格、批次、费账款一一对应；安装/首次及带业务升级、同一Web完整临床到结清、S08/S09回归 | C固定库安装/双升级及模型；W3 20步真实Web费库/posted740；W4安装态QWeb同步和38表保全；W5付款/R1只读核账。源/角色：W3医生/检查员/药房/经理与W4/W5克隆账 | W4元数据越界STOP；W5 browser exit1/final_audit NOT_RUN；同Firefox23步与完整上游HTTP回归未通过 | BLOCKED；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-W3](#e-w3)、[E-W4](#e-w4)、[E-W5](#e-w5)、[E-R1](#e-r1) |
| T13 | 旧270新200收300及仅选新账→270+30、欠170、未选不核；跨日/同日稳定次序、两张原生账保留、单选新账 | C/R3模型原生partial、仅选新账与超额/跨店拒。源/角色：旧270/新200两张账和一个300收款操作者 | 此特定多账组合真实浏览器未见；不同库结果不并成同次Web PASS | SCOPED_ACCEPTED；非本批；现有关键路径勿重跑 | NOT_RUN；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3) |
| T14 | 有/无billing前台和跨店摘要→同一服务鉴权、无岗位默认开放、无跨店代收；有权Web入口、无权POST、跨店摘要/旧页撤权 | C/R3模型/HTTP；UI4有权前台；UI6六组负向与撤权，UI7旧HTML303拒绝。源/角色：front有/无billing、manager切店/撤权旧页 | 全岗位、跨法人患者合并及原生RPC/附件拒绝未穷尽 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-UI4](#e-ui4)、[E-UI6](#e-ui6)、[E-UI7](#e-ui7) |
| T15 | 确认600调价620仍按600结算/重印；退款驳回有原因/审计、无贷项退款；价源冻结、同源重印字节、驳回原因及S01审计/零出款 | C/R3模型冻结600与驳回无贷项；UI4指定PDF字节可用。源/角色：已确认600费源、调价操作者、驳回者和PDF | 同一旧费源调价后原版重印与更正后的签名、驳回PDF/审计全字段组合不足 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-UI4](#e-ui4) |
| T16 | 锁后补录、解锁更正、删除/篡改审计→锁覆盖新增/更正、双时间、普通人不可删改；真实跨日补录、错日期绕锁、审计/单据不可改删、close逆序竞争 | C/R3双时间/六次篡改拒；FC1/FC2部分close与退款/更正竞态；UI6/7撤权旧页。源/角色：收费员、财务解锁者、审计记录、两个事务后端 | 合法时点而错业务日绕锁、跨日补录与同收费员全渠道组合、审计原生删除/RPC广度不足 | PARTIAL；是 | NOT_RUN、INSUFFICIENT_EVIDENCE；产品缺口未从固定证据证实；无新增业务规则待决定；生产科目/税/支付政策仍待单列确认 | [E-C](#e-c)、[E-R3](#e-r3)、[E-FC1](#e-fc1)、[E-FC2](#e-fc2)、[E-UI6](#e-ui6)、[E-UI7](#e-ui7) |

## 固定证据目录与层级

以下文件路径均为仓库固定提交的脱敏材料。机器索引中的私有材料仅有哈希；GPT评论给出独立审查的能力边界。

| 代号 | 固定提交／合成库 | GPT独立裁定 | 报告／机器索引 | 层级与限界 |
|---|---|---|---|---|
| <a id="e-c"></a>E-C | `d99f27fffcd6f9b79f1b1ac271dd026493b826b6`；ydental_s10_test_20261014002200_7b91d4e6 / OID1925429 | [6158230350](https://github.com/Yredxin/YDental/issues/34#issuecomment-6158230350) | [报告](https://github.com/Yredxin/YDental/blob/d99f27fffcd6f9b79f1b1ac271dd026493b826b6/docs/s10-completion-blocked-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/d99f27fffcd6f9b79f1b1ac271dd026493b826b6/docs/evidence/s10-completion/verification.json) | REAL_ODOO_MODEL, COMMITTED_NATIVE_SQL, TWO_TRANSACTION, REAL_WEB/FIREFOX, PDF_BYTES |
| <a id="e-r3"></a>E-R3 | `f24b0302569aefaa394391da6b696d915e3f0616`；ydental_s10_test_20261014020300_8b6c1d4e / OID2056451 | [6159493421](https://github.com/Yredxin/YDental/issues/34#issuecomment-6159493421) | [报告](https://github.com/Yredxin/YDental/blob/f24b0302569aefaa394391da6b696d915e3f0616/docs/s10-r3-native-crash-blocked-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/f24b0302569aefaa394391da6b696d915e3f0616/docs/evidence/s10-r3-blocked/incident.json) | REAL_ODOO_MODEL, COMMITTED_NATIVE_SQL, STATIC_REVIEW |
| <a id="e-fc1"></a>E-FC1 | `7ee2c5e091fa1d29bd01e493b07902d2827f4a35`；ydental_s10_test_20261014145000_fc1a84d7 / OID2100197 | [6171308225](https://github.com/Yredxin/YDental/issues/34#issuecomment-6171308225) | [报告](https://github.com/Yredxin/YDental/blob/7ee2c5e091fa1d29bd01e493b07902d2827f4a35/docs/s10-fc1-finance-concurrency-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/7ee2c5e091fa1d29bd01e493b07902d2827f4a35/docs/evidence/s10-fc1/verification.json) | REAL_ODOO_MODEL, COMMITTED_NATIVE_SQL, TWO_TRANSACTION |
| <a id="e-fc2"></a>E-FC2 | `d766b70b0a9c922c809248cdc87e76efa8d5bc23`；ydental_s10_test_20261014152000_fc2a7d31 / OID2100212 | [6173646820](https://github.com/Yredxin/YDental/issues/34#issuecomment-6173646820) | [报告](https://github.com/Yredxin/YDental/blob/d766b70b0a9c922c809248cdc87e76efa8d5bc23/docs/s10-fc2-finance-regression-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/d766b70b0a9c922c809248cdc87e76efa8d5bc23/docs/evidence/s10-fc2/verification.json) | REAL_ODOO_MODEL, COMMITTED_NATIVE_SQL, TWO_TRANSACTION |
| <a id="e-ui4"></a>E-UI4 | `3e2f863d089d1df4bf979eb99624a84abbfad292`；ydental_s10_test_20261015033000_a4c82d17 / OID2100265 | [6183855658](https://github.com/Yredxin/YDental/issues/34#issuecomment-6183855658) | [报告](https://github.com/Yredxin/YDental/blob/3e2f863d089d1df4bf979eb99624a84abbfad292/docs/s10-ui1-r4-blocked-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/3e2f863d089d1df4bf979eb99624a84abbfad292/docs/evidence/s10-ui1-r4-blocked/verification.json) | REAL_WEB/FIREFOX, COMMITTED_NATIVE_SQL, PDF_BYTES |
| <a id="e-ui6"></a>E-UI6 | `09cbcfea575bd488e617a5f597bab3c9d9286eae`；ydental_s10_test_20261015052000_b6d2a94f / OID2100267 | [6184556009](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184556009) | [报告](https://github.com/Yredxin/YDental/blob/09cbcfea575bd488e617a5f597bab3c9d9286eae/docs/s10-ui1-r6-blocked-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/09cbcfea575bd488e617a5f597bab3c9d9286eae/docs/evidence/s10-ui1-r6/verification.json) | REAL_WEB/FIREFOX, COMMITTED_NATIVE_SQL |
| <a id="e-ui7"></a>E-UI7 | `7efa4e25583b667cc0de22d115b54d67d0d10a3b`；ydental_s10_test_20261015060000_c1d2e3f4 / OID2100268 | [6184708258](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184708258) | [报告](https://github.com/Yredxin/YDental/blob/7efa4e25583b667cc0de22d115b54d67d0d10a3b/docs/s10-ui1-r7-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/7efa4e25583b667cc0de22d115b54d67d0d10a3b/docs/evidence/s10-ui1-r7/verification.json) | REAL_WEB/FIREFOX, COMMITTED_NATIVE_SQL |
| <a id="e-w3"></a>E-W3 | `71a554667157cdd917c0062db5e4ddf1693f6410`；ydental_s10_test_20261015060000_b6c7d8e9 / OID2100285 | [6185715797](https://github.com/Yredxin/YDental/issues/34#issuecomment-6185715797) | [报告](https://github.com/Yredxin/YDental/blob/71a554667157cdd917c0062db5e4ddf1693f6410/docs/s10-e2e-w3-blocked-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/71a554667157cdd917c0062db5e4ddf1693f6410/docs/evidence/s10-e2e-w3/verification.json) | REAL_WEB/FIREFOX, COMMITTED_NATIVE_SQL |
| <a id="e-w4"></a>E-W4 | `79417da9043478501ffae586f93eebc1e5d7105d`；ydental_s10_test_20261015064000_d41e7b62 / OID2100301 | [6186530230](https://github.com/Yredxin/YDental/issues/34#issuecomment-6186530230) | [报告](https://github.com/Yredxin/YDental/blob/79417da9043478501ffae586f93eebc1e5d7105d/docs/s10-e2e-w4-blocked-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/79417da9043478501ffae586f93eebc1e5d7105d/docs/evidence/s10-e2e-w4/verification.json) | REAL_ODOO_MODEL, COMMITTED_NATIVE_SQL |
| <a id="e-w5"></a>E-W5 | `287881a824e9a18dd637522c570f74df139078f9`；ydental_s10_test_20261015073500_e50f4a71 / OID2100310 | [6187844624](https://github.com/Yredxin/YDental/issues/34#issuecomment-6187844624) | [报告](https://github.com/Yredxin/YDental/blob/287881a824e9a18dd637522c570f74df139078f9/docs/s10-e2e-w5-blocked-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/287881a824e9a18dd637522c570f74df139078f9/docs/evidence/s10-e2e-w5/verification.json) | REAL_WEB/FIREFOX, COMMITTED_NATIVE_SQL |
| <a id="e-r1"></a>E-R1 | `5876740dabf342372b0970682947e6be8356fa8c`；W4 OID2100301 → W5 OID2100310; NEW_READONLY_SQL | [6190103223](https://github.com/Yredxin/YDental/issues/34#issuecomment-6190103223) | [报告](https://github.com/Yredxin/YDental/blob/5876740dabf342372b0970682947e6be8356fa8c/docs/s10-e2e-w5-ro1-r1-readonly-report.md) / [机器索引](https://github.com/Yredxin/YDental/blob/5876740dabf342372b0970682947e6be8356fa8c/docs/evidence/s10-e2e-w5-ro1-r1/verification.json) | COMMITTED_NATIVE_SQL, STATIC_REVIEW, SIMULATED_PASS |

## 跨批次血缘与不可合并的运行状态

```text
W3 / OID2100285  Web临床20步：治疗600＋检查80＋处方4+2，stock done 1/4/2，posted invoice740
  └─只读克隆→ W4 / OID2100301  同步安装态QWeb；38表经济签名保全；模块元数据越界STOP，未收款
      └─只读克隆→ W5 / OID2100310  Web现金500、240各POST一次；原生invoice余额740→240→0
          └─RO1-R1只读审计：W4/W5 42表/102列契约，posted凭证、AR partial、S10 receipt及S01审计核对
```

W3的bill后台已posted，但HTML返回200，步骤21浏览器确认未完成；W4没有Web付款；W5两笔付款是真实Web合成业务且被GPT限定接受，但第二笔后浏览器测试判据遗漏`reconciled`而exit1，`browser-complete.json`未写、正式第二笔截图未捕获、`final_audit`未运行。RO1-R1的新增证据是**只读SQL**，第一笔后Web余额240来自W5历史响应/截图；它没有再次POST。故“单Firefox会话23步PASS”“W5执行器完整PASS”均不成立。

FC1/FC2真实双后端竞争已覆盖批准胜/取消胜、执行胜、同执行人退款先于日结、现金更正微信后的原生微信出款等指定路径；`40001`证明事务隔离回滚，未证明每个底层锁等待链。UI1-R4/R6/R7覆盖指定Web正负权限、旧页撤权反馈和三类真实PDF字节；不重复这些资金与PDF场景。R3的55退款/55日结**服务端分页**是旧库的模型事实，固定Firefox第2页动作被SIGSEGV停止；之后UI1的**>50条真实资金历史HTTP分页始终NOT_RUN**，不可称前台旧申请/旧日结可操作性已验。

## 产品、政策和最终验收边界

- R3已有退款/日结服务端分页实现与模型证据；对应当前安装态Web中的旧pending退款、已确认日结的可达性、授权操作及当前版本行为仍`INSUFFICIENT_EVIDENCE`，不先推定产品缺陷。R3固定并发窗口SIGSEGV发生在动作前，不能抵消C/FC历史限定实证，也不证明Native根因已解决。
- 财务并发FC1/FC2与UI1、W3/W4/W5的结果来自不同固定库/commit。B1历史费用205条、F5仅选新账、零元原生账、跨法人合法交易和价格600→620仍按600等模型结果仍可引用；不可把旧库截图/离线Fake记为最新W5现场。
- [集团多仓/多库位政策](https://github.com/Yredxin/YDental/issues/34#issuecomment-6170791208)已批准，仅覆盖该政策。生产会计科目、税、币种、现金/微信/支付宝/银行卡真实渠道及资金到账证据、正式税务票种和实际门店配置仍待业务/财务确认；当前合成账不能代替。
- S10整阶段技术及生产继续`BLOCKED`；#34 OPEN，#35 S11 `NOT_STARTED`。#23决定S13后统一用户效果验收，S10目前没有用户最终统一验收通过的事实。旧Native SIGSEGV根因`UNKNOWN`，本批不调查基础设施。

## 本批实际资源与复核请求

`CREATE=0; SQL_DB_CONNECTION=0; BUSINESS_WRITE=0; PAYMENT/REFUND_POST=0; ODOO_HTTP/CLI/SHELL/INSTALL/UPGRADE=0; FIREFOX=0; SUDO=0`。产物是只读证据整合；下一批仅见[候选方案](s10-gap-01-next-batch-proposals.md)，状态均`PROPOSAL_NOT_AUTHORIZED`。请求GPT独立核对原断言、固定身份与有限证据归类，尤其审查任何不该提前提升的行。
