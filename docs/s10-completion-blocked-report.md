# S10 定向补全与持续阻断报告

## 1. 任务、授权与固定版本

- 唯一续作授权：[#34 GPT-REVIEW/AUTHORIZE 6149055777](https://github.com/Yredxin/YDental/issues/34#issuecomment-6149055777)；任务 [#34](https://github.com/Yredxin/YDental/issues/34)，总计划 [#23](https://github.com/Yredxin/YDental/issues/23)。2026-10-14 UTC 重读正文及全部当前有效评论。D1 已合格，本批没有重跑 D0/D1。
- 原分支 `codex/s10-settlement-finance-r1-20261013`，基线 `f4a1e20203b040642667404f7ce07db0c2523d66`，最后产品 `c85c5fbd42d25345ffe217aeeefad24ca89ee9f1`，固定测试 `38252243b7b671e95017b2bf9a2e39320b0eb3d7`。product→test 差异仅 `scripts/`；final 只纳入本报告、AGENTS 和脱敏合成证据。最终 SHA 以 #34 回执为准。
- **结论：S10 持续 BLOCKED。** B1/B2/B3 主要缺口已定向修复并在同一固定库实证；下表仍有必要的 PARTIAL，不能称 F1—F6/T01—T16 全部 PASS，更不能启动 S11 或生产部署。

## 2. 需求完成情况

| 项 | 状态 | 实际证据与剩余边界 |
|---|---|---|
| B1 历史费用与欠款 | 已验证目标修复 | `_workbench` 先按门店、患者和原生 source/invoice 过滤，再分别 50 条分页；同店 205 笔真实确认新费后，旧患者的未出账费与旧欠单仍可按患者及第 5 页找回。 |
| B2 药房 4+2 | 已验证目标修复 | 同一处方首次实发 4、余 2 待再次报到、第二次实发 2；两次确认事件/费源 40+20、原生库存 move 2 笔合计 6，接 600+80 出账 740。 |
| B3 多账单 | 已验证目标修复 | 不同业务日 270/200；仅选新账收 200 不动旧 270；逆序勾选两账收 300，原生 partial 270+30；同日逆序勾选按 invoice ID。 |
| F1 | 主要流程 PASS | 原生 invoice 740、payment 500+240、partial 500+240、residual 240→0。重账/收款 key 回放与双后端同费源唯一账单。 |
| F2 | PARTIAL | 申请 100、本人自批拒、他人批准在途 0、实际原生退 100；50 驳回、80 未知经证据撤销；失败注入与 60 恢复、300 并发额度竞争。未测两审批者对同退款竞争、完成后取消及响应丢失重试。 |
| F3 | PARTIAL | 错记现金 300，现金日结锁→财务解锁→原生分录更正微信→重新日结；实际发生/录入跨日及 close/pay 双后端竞争。close/refund 和 close/reclassify 首轮竞争未覆盖。 |
| F4 | PARTIAL | 600 冻结快照调 620 后仍按 600 出账；文字更正不动费库；项目 -600 原生贷项；药房实物退 1 进入原生隔离库存且不生成假退款。完整 S08/S09 模型、HTTP、报告与队列回归未全部重放。 |
| F5 | 主要流程 PASS | 两账保留不同 ID 和业务日；唯一 300 收款真实核旧 270 + 新 30，新欠 170；仅选新账及超额拒绝。 |
| F6 | PARTIAL | 经理/前台实际收款，无权限角色 403；B 店只返回最小欠款摘要且伪造 A 单付款 403，合法 A 上下文可处理。旧 tab/撤权、跨店附件与患者合并权限矩阵未全部覆盖。 |

## 3. 流程实际回放

固定合成库 `ydental_s10_test_20261014002200_7b91d4e6`，OID **1925429**，专属端口 **18234**，PG cluster `7694897083368259627`，配置 SHA256 `805fc75045ae2547cbb2a118c7d42409e422dec46a439f82d7e7346311fb21b2`，Odoo20 core SHA `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。固定 test SHA 全程未变。所有门店、人员、患者、批次与资金均为隔离合成数据；`demo_confirmation` 明示演示科目/手工线下资金，未接银行或微信平台。

| 业务 | 真实回放 | 原生勾稽 |
|---|---|---|
| 740 | 治疗 600、检查 80、药房 4×10+2×10；账单 740，实收 500 欠 240，再收 240 结清。 | fee 1—4、invoice 1，payment 1/2、partial 1/2 为 500/240，最终 residual 0；两个药房原生 move。 |
| 旧 270/新 200 | 旧日 2026-10-13、新日 2026-10-14；仅新账 200，旧 270 未动；另选旧新收 300。 | payment 4 关联 partial 4=270 到 invoice 4、partial 5=30 到 invoice 6，新余额 170。 |
| 退款/日结 | 100 申请→他人批准时实际退 0→outbound/贷项实退 100；50 驳回无贷项、80 未知后核查撤销；现金 300 更正微信。 | 最终 9 退款：done 4、cancelled 2、rejected 2、requested 1；完成单有原生 outbound 与 posted 贷项，非完成单无原生退款。 |
| 跨法人 | 双方有权的演示交易 1 笔。 | sale.order 1、purchase.order 1、不同公司 posted 销项/采购账、done 出库/入库各 1；未授权、数量不足、错误批次、重复 source、模拟原生库存失败回滚均拒绝/无残单。 |
| 跨店 | B 店查看 A 的余额最小摘要，伪造 A 原生单付款。 | HTTP 摘要 200，只有店/法人/币种/余额字段；伪造付款 403、无新 account.payment。 |

## 4. 测试结果

`YDENTAL_S10_EXPECTED_SHA=3825224… ../.venv/bin/python scripts/s10_completion_runner.py`：`create` exit0；`install` PID2322334 exit0；首次 `upgrade` PID2322952 exit0；21 个合成 shell 探针全部 exit0；带已提交真实业务再次 `upgrade` PID2326258 exit0。24 条守卫动作 signal11=0；最终专属预览 PID2325100 exit0，Firefox exit0/pageerror0。三组真实双 PG backend 首轮屏障：出账 365784/365785 两方共用一张账、退款 365796/365797 一方申请一方额度拒绝、日结/付款 365982/365981 付款被日结锁拒；六个 Odoo 并发子进程 exit0，deadlock0。16 张业务/原生表升级前后 count 与逐行 SHA256 相同。

| TC | 状态 | 证据/未闭环处 |
|---|---|---|
| T01 | PASS | 同源双后端仅一条 source/posted invoice；重放原单。 |
| T02 | PASS | 740→500/240，原生 partial 两笔及请求 key 重放。 |
| T03 | PARTIAL | 负/超额折扣拒、明确 20 折扣与未收 80 全免无付款；**独立 100% 出账为 0 的账单未测**。 |
| T04 | PARTIAL | 本人自批拒、双后端同一 500 资金最后额度 300 竞争；两批准者同退款并发未测。 |
| T05 | PARTIAL | native post 故障注入回滚、failed→独立核查→实退 60、unknown 撤销；完成单二次执行/取消与响应丢失未测。 |
| T06 | PASS | 未收 80 原生贷项冲应收，真实退款和 payment 均未增加。 |
| T07 | PARTIAL | 日结锁/解锁/渠道更正/重结及 close/pay 竞争；refund/reclassify 与 close 首轮竞态未测。 |
| T08 | PARTIAL | 文字/数量/真实药物退库分别实测，未退不回库；未全部形成同一接诊的集成回归。 |
| T09 | PARTIAL | 同法人 move 与跨法人销售采购/库存/账双边正例，5 项负向；异币种、效期不足、配置缺失和同 source 并发订单未测。 |
| T10 | PARTIAL | 6 类无结算权角色 board/PDF/pay 拒绝、B 伪造 A 付款 403；附件、导出、合并和旧页权限未全测。 |
| T11 | PARTIAL | bill/receipt/refund 六份真实中文 PDF 各一页逐页目视，覆盖已收/欠款/实退；批准在途/未知状态票面未逐页核验。 |
| T12 | PARTIAL | 新库安装、升级、持久业务再升级，F1 真治疗检查药房库存队列；S08/S09 所需全套模型/HTTP 回归未重跑。 |
| T13 | PASS | 跨日 270+200 收 300=270+30，仅新账 200 不碰旧账，同日 ID 顺序及超额拒绝。 |
| T14 | PARTIAL | 前台和经理实际按钮、无权 403、B 最小摘要/代收 403；撤权下一请求及同会话切店未测。 |
| T15 | PARTIAL | 600 调 620 后仍按 600 原生出账，50 驳回无退款；该同源重印/更正后的双签名未形成完整用例。 |
| T16 | PARTIAL | 真实跨日补录两时间、锁后阻断、财务解锁、更正、六次篡改拒绝及 close/pay 并发；错日期绕锁、close/refund 竞争未测。 |

本批没有为可逆的低影响变更编写镜像实现测试；上表是实际业务与原生数据结果。原 `ydental_settlement_test` 是受保护供给适配器，不含可替代上述合同的 Odoo test case。所有结果为 Codex 自测，不是 GPT/用户验收。

## 5. 字段、动作与配置

- `_workbench` 四个独立门店/患者来源分页，发票从原生 posted `account.move` 与 `settlement.source` 查询，不再由全店最新 200 笔 fee 派生。门店与患者关系依 S01/S04 服务端权限判定。默认每页 50，页码范围 1—10000；本人无权服务端拒绝。
- 退款 `requested/approved/unknown/failed/cancelled/rejected/done` 分离。新 `ydental.settlement.mutex` 单例版本行用于真实 REPEATABLE READ 容量序列化，独立核查证据才释放未知/失败额度。批准阶段不建实退；完成阶段才建立原生 outbound、贷项和核销。
- 日结按门店业务日、收款员、实际渠道锁；实际发生 UTC 与记录 UTC 分开。财务解锁保留原因，支付方式更正走原生平衡分录，无虚构资金返还。
- 生产科目、税、正式凭证及支付政策未经审批；只在合成库填演示日记账/科目。Odoo20 native SIGSEGV 历史根因仍 UNKNOWN，不能推断已根治；原生银行、微信回调和税务发票未连接。
- 现行 addon 尚无完整 `zh_CN.po` 覆盖审计；六份实际 QWeb PDF 的中文可读性已目视通过，不能以此替代 100% 全 UI 翻译验证。

## 6. 用户效果验证

Firefox 截图、实际下载 PDF 与逐页 PNG 均在 [合成证据目录](evidence/s10-completion/)；[机器索引](evidence/s10-completion/verification.json)记录原始 SHA256。经理在旧患者页选费出账、全额未收免单；新患者逐张出账，再勾两单实收 700，原生分摊 600+100。经理和前台各点击收 10；经理申请 5、前台批准、经理确认实际退 5；前台另一笔申请由经理驳回，再一笔批准→未知→经理核查撤销。经理日结、前台财务解锁、经理支付分类更正，点击下载账单/小票/退款凭据。无结算权者 workbench/PDF 403；B 店页无 A 单并对伪造付款返回 403，最小余额摘要 HTTP200。

六份 PDF 实际由本批 Odoo/QWeb 生成，均 1 页、无裁切/乱码：740 账单列明 600+80+40+20、500 收款小票列明实退 100、100 退款凭据列明 done；另三份来自 Firefox 实际下载，列明新账 200/已收 55/欠 145、10 收款/实退 5、5 实退。只验证浏览器下载，纸张真实打印仍 UNKNOWN。

## 7. 数据、审计、失败历史与保全

- 最终库原生数据：222 treatment event、221 fee、18 source、11 settlement payment、9 refund、6 close、2 correction、1 trade、40 account.move、15 account.payment、20 account.partial.reconcile、234 stock.move、1 sale.order、1 purchase.order。source→posted invoice 缺失 0、同 fee 重复 source 0、非完成退款生 native outbound 0、完成退款无 native outbound 0、PG deadlock 0。原生 partial 总金额 3491 演示货币单位；不把它误称单一场景营业额。
- 候选库与失败原样保留：`20261013234419_c84e6d12`/OID1859809 中错误屏障曾精确停止两自有 PID，留下 signal2 marker，**非 SIGSEGV**；`20261013235828_5e8ac4d1`/OID1881641 有夹具、关闭额和预览 guard 失败；`20261014001000_81ac9f72`/OID1903547 有退药缺队列连接及浏览器跨患者 403 的合理拒绝。三座候选均不是最终 PASS 来源，旧所有库/卷/失败日志未删除。
- 最终库原始日志、PDF、截图留于受保护 `.local/ydental_s10_test_20261014002200_7b91d4e6/`；仓库只保存脱敏合成件与 SHA。Project 本轮 0 写、#34 不关闭，不修改 Odoo20 核心/odoo-12。没有执行生产回滚；生产未部署。

## 8. 复核申请

申请 GPT 按本固定 product/test/final 和同库机器证据再次独立技术复核。B1/B2/B3 修正、原生主链、三组并发和 Firefox 有实测，但剩余 PARTIAL 不满足 #34 完整 F1—F6/T01—T16；**S10 持续 BLOCKED**。原 native SIGSEGV 根因及生产财务政策同样未解除。等待 GPT 下一步边界，不修改 Project 状态、不关闭 #34、不启 S11、不合并或部署。
