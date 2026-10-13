# S10 D1 受控恢复与 D2 定向返工：持续 BLOCKED 技术复核申请

## 1. 授权、基线和交付范围

唯一续作授权：[ #34 GPT-REVIEW/AUTHORIZE 6147246260 ](https://github.com/Yredxin/YDental/issues/34#issuecomment-6147246260)。已重读 #23、#34 正文及全部有效评论；本轮最后核对 #34 评论至 6147335402，#23 评论至 6125774169。沿原分支 `codex/s10-settlement-finance-r1-20261013`，从保全基线 `a73bcd7d198b5ee9c372c3c658a34053e61be048` 线性前进。当前返工 product 为 `a5d0307da427e393dddc303fdef7f83fe362ea30`，固定 test 为 `3b7e159b2332dd85dd43241810954fa993103f0a`；最终文档/证据提交 SHA 见 #34 回执。原失败 `87bad3b...`、后续所有候选提交和数据库均保留。Project 0 mutation，Issue #34 未关闭。

## 2. D1.0/D1.1 闸门

D1.0 离线审查 S10 manifest 及 Odoo20 真实 addon 递归依赖 51 个；诊断安装仅 `ydental_settlement`，不安装或绕过 `ydental_treatment_test` pre-init guard。shell canary 仅使用 Odoo shell 注入的 `env`，AST/compile、config、DB guard 静态检查通过。先在 #34 发布 `[CODEX] S10 D1二次有界诊断离线预检回执`（评论 6147335402）并逐字读回。

D1.1 只建新库 `ydental_s10_test_20261013140300_d11a5e73`，OID 1641937，端口 18212，PG cluster `7694897083368259627`，config SHA `ddf402269248d1da0a820ed8935e7006b3c0832e0976b6fcea58338e4ac97c71`。严格两个 Odoo 子进程：安装 PID 1990449 exit 0、日志 SHA `bbf2f1bd8df75e977797cadbe7875b9c0c4c59f951efe819ff9b564aee389b48`，产品 `installed`；只读 shell PID 1991188 exit 0、日志 SHA `5d7b97673cfc67585558b058433a7ba9886bf4aa08fc5b0a31d08fe3fc4ce5c8`，真实模型/库身份读回。两次 signal11 均 0。此闸门仅允许 D2，**原 PID1965906 SIGSEGV 的 native 根因仍 UNKNOWN，生产继续 BLOCKED**。

## 3. 需求完成情况和实现位置

| 功能 | 状态 | 固定实现/限制 |
|---|---|---|
| confirmed 费源、S05 快照、原生 invoice/payment/partial.reconcile | 已实测 | `ydental_settlement/models/ydental_settlement_service.py`；数据库唯一费源，竞争者经 Odoo 原生有限序列化重试后读取同一账单 |
| pending 事件独立待核对栏 | 已实测 | `_workbench` 读真实 pending event，无假费用 |
| 本店结算入口、前台实际收款 | 已实测一条 | 工作台和 controller；Firefox manager/frontdesk 各点击收款 10，无权访问 403；全部业务按钮尚未逐一点击 |
| 折扣、免单、应收与未收款减免 | 部分 | 负/超折扣拒绝、明确折扣 20、应收 80 原生贷项减免为 0；零元出账、仅选新账未跑 |
| 双人退款、批准在途、完成、驳回、未知撤销与额度恢复 | 部分 | 100 实退原生 outbound/贷项；80 未知经不同财务人员核查无付款撤销释放；失败态及竞争批准未测 |
| 日结锁、财务解锁、支付方式更正、再日结 | 部分 | 300 现金锁定→解锁→原生重分类→微信再日结，实际资金往返 0；补录双时间/跨日冲突未测 |
| 同法人调拨、跨法人 sale/purchase/stock/account | 已实测一条 | 真实 stock move；两法人原生 SO/PO、收/发 stock move、posted 销项/采购凭证各 1；仅显式合成演示科目/无税配置 |
| 三类中文 PDF | 已实测三类 | 账单、小票、退款单各真实 PDF 1 页，提取中文 97/123/100 字并逐页目视；重印两次经济数据未变，PDF 字节可因动态元数据不同 |
| 生产财务配置和 native 稳定性 | BLOCKED | 生产科目/税/凭证/支付政策未批准；原生 SIGSEGV 根因未知 |

## 4. 实际业务回放与财务勾稽

固定 D2 库 `ydental_s10_test_20261013152000_f60a5e7d`，OID 1837936，端口 18221，原 cluster，config SHA `84a74cc07586b728844490acdcdb754358bbd0aeea27a55cfadc119437a78d45`。固定 test 安装、首次升级、带已提交业务再次升级均 exit 0；13 条 guard 动作全部 exit 0，无 signal。两 PostgreSQL backend PID 256593/256592 同屏障；第一笔出账成功、第二笔在独立事务经一次 Odoo 同类有限序列化重试后读到同一 invoice 18，费源记录仅 1，deadlock 0。旧竞争失败库和唯一约束异常/测试屏障失败全部保留。

| 场景 | 真实费用/账单 | 原生资金与核销 | 余额/结果 |
|---|---|---|---|
| F1 | 治疗 600 + 检查 80 + 发药 6×10=60；fee 1/2/3 → posted invoice 1=740 | account.payment 1=500、2=240；account.partial.reconcile 1=500、2=240 | 740→240→0；后续真实退 100，净收 640，不倒改原账 |
| F5 | 旧 invoice 4=270，新 invoice 5=200，两账单保留 | 一笔原生 payment 3=300；partial 3=270 先核旧，partial 4=30 后核新 | 旧 0，新 170；Firefox manager 另收 10→160，frontdesk 另收 10→150，均有独立原生 payment/partial |
| F2 | 退款申请 100，自批拒绝，另一真人审批时实退 0 | 实际执行后 outbound account.payment 4=100、posted credit 7；驳回 50 无贷项/资金；未知 80 撤销前占额度，核查未付后释放 | 累计已退 100；原款净收 640；额度返回 240 |
| F3 | 门店现金日结 300，财务解锁有原因 | 原生重分类 move 9；微信再日结 300 | 实际现金退款 0、没有假逆向收付 |
| T09 | 跨法人 source company 1、target company 2，金额 80 | sale.order 1、purchase.order 1；stock.move 11/12 done；销项 invoice 10、采购 bill 11 posted | 双公司真实单据配对；未绕开目标公司仓库及财务权限 |

最终只读 SQL：10 临床 event、9 fee、9 source、5 线下 payment、4 refund、2 close、1 trade；原生 20 account.move、7 account.payment、10 partial.reconcile、20 stock.move、1 SO、1 PO。`source_without_posted_invoice=0`、`posted_company_null=0`、`valid_trade_count=1`、deadlock 0。业务再升级前后 16 张业务/原生表逐行哈希完全相等；最终前台补收 10 后另存 final SQL 快照，未混称升级前后相等。详情和逐页截图见 `docs/evidence/s10-rework/verification.json`。

## 5. F1—F6 与 T01—T16 状态

| 项 | 实际状态及未达合同部分 |
|---|---|
| F1 | PARTIAL：740/500/240 真实链通过；重复请求完整重放未做 |
| F2 | PARTIAL：100 审批与实退、驳回、未知撤销通过；失败执行与并发批准未做 |
| F3 | PARTIAL：日结解锁、方式更正、再日结通过；补录与真实退药待核对未做 |
| F4 | PARTIAL：真实临床/检查/发药/批次/出账与重印有效 PDF 通过；补旧文书及所有原单不变量未全面回归 |
| F5 | PARTIAL：270+200 收 300 与原生 270+30 通过；仅选新账且旧账仍未付场景未做 |
| F6 | PARTIAL：前台有权实际 Firefox 收款与无权 403、跨店代收拒绝通过；B 店只读 A 店欠款摘要及合法切 A 未做 |
| T01 | PARTIAL：双 backend 同费源唯一出账通过；740 重复/并发整体未做 |
| T02 | PARTIAL：740 实收 500+240/原生核销通过；完整重试未做 |
| T03 | PARTIAL：非法折扣拒绝及未收款减免通过；零元账无假收款未做 |
| T04 | PARTIAL：自批拒绝、批准未退通过；并发额度审批未做 |
| T05 | PARTIAL：未知撤销与实际完成通过；失败及重试未做 |
| T06 | PASS：未收款 80 由贷项核销，应收 0，实际退款 0 |
| T07 | PASS：锁定、财务解锁、方式更正、重新日结，无伪退款 |
| T08 | PARTIAL：数量反向费源/贷项通过；文字更正及真实实物退回未做 |
| T09 | PASS：同法人实际调拨及跨法人原生双单/收发/凭证一组通过 |
| T10 | PARTIAL：跨店付款、无权工作台/PDF 403 通过；医疗全文隔离矩阵未做 |
| T11 | PARTIAL：三类中文 PDF 真实逐页通过；批准在途票据和全部部分收退款组合未做 |
| T12 | PARTIAL：安装、首次升级、带已提交交易再升级与全链通过；S08/S09 必要集成回归未执行 |
| T13 | PARTIAL：270+30 原生核销通过；仅选新账未做 |
| T14 | PARTIAL：前台有权真实 Firefox、无权 403 通过；跨店摘要及切店未做 |
| T15 | PARTIAL：原 600 调价 620 后仍按 600、驳回无贷项通过；原单在调价后重印专项未做 |
| T16 | PARTIAL：锁和来源不可改删通过；补录双时间、审计删除/篡改全部负向未做 |

**结论：F1—F6 与 T01—T16 未全部完成，S10 持续 BLOCKED，不能请求技术 PASS 或用户验收。**

## 6. 失败历史、安全审查与环境

原事故库 OID1598603/PID1965906 signal11、D1 初次失败库 OID1620922、D1.1 库 OID1641937 和 D2 各候选 OID1663493/1685272/1707097/1728911/1750620/1772411/1794256/1816099/1837936 均保留。候选曾遇合成权限/财务账户适配错误、PDF 中文乱码和结构排版错误、并发屏障位置错误、同费源唯一约束裸露异常与原生 `SerializationFailure`；逐项改后使用新库，不把失败抹成 PASS。额外前台浏览器探针最初断言在点击前写错（期待 150 而实际应为 160），两次 exit1 未发付款；已保留失败源码/hash，修正后一笔真实前台 10 收款 PASS。重印探针初稿误将 PDF 二进制哈希相等当业务合同，exit1；修为两张有效单页 PDF 及余额不变后 exit0，原失败保留。曾有一次后台预览进程未保持、端口拒绝，以及预览停止后的 `TIME_WAIT` 使 upgrade guard 先 exit1；均未触碰数据库，端口释放后同固定 test upgrade exit0。

按 `odoo-guidelines` 检查 ORM 保存点与具体异常范围；按 `odoo-security` 扫查 S10 sudo、动态模型、SQL、路由/CSRF、XSS/文件/反序列化入口。产品动作先验证绑定会话、门店和双公司权限，再最小范围使用原生会计 sudo；仅参数化 advisory lock SQL；写接口 POST 且 CSRF 保留。`ydental_settlement/security/ir.access.csv` 没有放宽公共 CRUD。此为 Codex 静态自查，跨角色完整矩阵仍未通过。原生 SIGSEGV 根因不明，本轮无新 signal11 不能证明已修。

仅隔离合成库和显式演示科目/日记账/无税配置；无支付平台接口或银行自动到账。旧数据库/volume/Odoo20 core/odoo-12/Project 均未变更，没有真实患者或生产资金。现有产品候选尚未经财务生产政策批准。正常 Git push，不合并/强推/部署；旧日志、core 可见性限制、原始事故证据持续保全。可逆回退为停止使用独立分支及隔离库，历史库不删除。

## 7. 用户效果和证据

前台入口为 `/ydental/settlement`；获得当前门店结算写权的前台登录、切本店、看到已出账未付 170、选新账并填写真实线下支付宝登记 10，点击“确认实际收款并原生核销”，页面显示 160，原生付款 6；另一前台以同样真实按钮追加 10→150、原生付款 7。无结算权角色的工作台和 PDF 都返回 403。三份 PDF 均注明“演示线下业务凭据；非税务发票、非银行或支付平台到账证明”，每页 PNG 及 PDF 固定提交。Firefox 当前仅覆盖收款按钮和少量负向入口，**并未覆盖全部实际业务按钮**。

## 8. 技术复核申请与停止

申请 GPT 复核本次 D1 有界恢复、D2 候选实现和 BLOCKED 边界。未完成项包括 F5 仅选新账、F6 跨店摘要、T04 并发额度、T05 失败恢复、T08 文字/实物更正、T12 S08/S09 回归、T16 补录/审计篡改，以及真实 Firefox 全按钮，均不能靠已有样例推定通过。生产科目、税、正式凭证、支付政策未审批；生产部署继续 BLOCKED。#34 保持 OPEN/进行中/Todo；不启动 S11。评论逐字读回后停止，等待 GPT 独立技术复核。
