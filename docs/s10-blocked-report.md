# 交付验收申请｜YD-N1 R1｜S10｜原生崩溃阻断批

**结论：BLOCKED，申请独立技术复核；不是 S10 技术 PASS 或用户验收。** 依据 [#34 最新 GPT-ACTIVATE 6145995580](https://github.com/Yredxin/YDental/issues/34#issuecomment-6145995580) 及本轮用户正式授权执行。已在开工读取 #23、#33、#34 当时正文和有效评论；交付前再次读取。开工检查见 [#34 回执 6146104902](https://github.com/Yredxin/YDental/issues/34#issuecomment-6146104902)。Git 起点 `d06b1056700c4fcf899deb68a32e8496e3f8195e`，分支 `codex/s10-settlement-finance-r1-20261013`，候选 product `47258e3763666cc37f8d0afe7092c65919e1062b`，失败探针 test `9bc86841619824627bfe03e97da43ce856b5ec28`，final SHA 见 #34 BLOCKED 评论。product→test 仅原样保存实际执行的测试探针；test→final 仅 AGENTS、报告与脱敏证据。旧 S09 及更早提交、数据库、日志、截图未修改。

隔离库 `ydental_s10_test_20261013125916_2b3e556e`，OID `1598603`，PostgreSQL cluster `7694897083368259627`，127.0.0.1:5432，专用 HTTP 端口 `18210`，独立配置 SHA256 `680c975afba34f3f5224cfdedf05572ecd91a1bcce669198b8ae3b44b9ab2a6a`。Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`、Python 3.12.15；原 Odoo/odoo-12 服务、核心、Docker 镜像和 volume 未改。创建前有 131 个 YDental 合成库，创建后 132 个；未删除或重置旧库。数据库配置与原始日志在本机 `.local/` 权限受限目录，仓库仅有[脱敏索引](evidence/s10-blocked/incident.json)、[Project 摘要](evidence/s10-blocked/project.json)和[崩溃摘录](evidence/s10-blocked/native-crash-excerpt.txt)。

## 需求完成情况

| 功能 | 状态 | 依据与缺口 |
| --- | --- | --- |
| 真实 S08/S09 confirmed fee → 原生 posted invoice 唯一来源、S05 价快照、折扣 | 候选代码，BLOCKED | `ydental_settlement` 已编写；崩溃前安装／升级的代码版本早于最终 product 候选，最新固定 product 未实装验证。没有真实 S10 fee／invoice。 |
| 结算工作台、明确授权前台入口、跨店欠款最小摘要 | 候选代码，BLOCKED | 控制器／QWeb 已编写；真实 Firefox 和安全负向均未运行。 |
| 原生 offline payment、partial reconcile、旧账 270＋新账 200 的 300 分摊 | 候选代码，BLOCKED | 实际探针未抵达业务脚本；原生 account.payment 和 account.partial.reconcile 均 0。 |
| 双人退款、在途额度、实退、失败／未知恢复、未收款减免 | 候选代码，BLOCKED | 仅静态实现；没有原生贷项／反向付款实测，也没有并发额度验证。 |
| 日结、锁、财务解锁、支付方式重分类 | 候选代码，BLOCKED | 没有真实付款与日结行为；当前库对应记录 0。 |
| 同法人 S07 调拨及跨法人原生销售采购收发和财务凭证 | 未完成，BLOCKED | S07 原有同法人 `_transfer` 已只读核实；S10 尚未实现跨法人受控交易，T09 必需关口缺失。 |
| 三类中文 PDF、翻译、Firefox 点击及上游联调 | 模板候选，BLOCKED | PDF 未生成／逐页核对，PO 未完成，浏览器未运行。 |

产品候选代码只能作为返工起点，**不应安装到真实业务库或用于收退款**。正式科目、税、日记账、支付政策均未获财务生产批准；本轮仅在隔离库安装了 Community `account/l10n_cn/sale/purchase` 并试图建立显式演示配置，不代表生产政策。

## 流程实际回放

| 流程 | 预期 | 实际 |
| --- | --- | --- |
| F1 治疗600＋检查80＋发药60→出账740→收500欠240→补240 | 原生 invoice/payment/partial reconcile 完整链 | **NOT_RUN/BLOCKED**。先仅尝试单笔治疗600探针；第一次 fixture 预约容量不足退出1并回滚。修正 fixture 的第二次调用在 registry 初始化中 SIGSEGV，业务脚本未执行。 |
| F2 已收740→申请退100→他人批准→实际退100／拒绝另一申请 | 在途与实退分离、原生退款凭证 | **NOT_RUN/BLOCKED**。 |
| F3 微信误录现金→日结→解锁→原生重分类→再日结 | 无虚构退收 | **NOT_RUN/BLOCKED**。 |
| F4 真实治疗／检查／发药／lot→结算→文字更正／重印／调价 | 费库款稳定 | **NOT_RUN/BLOCKED**。 |
| F5 旧270＋新200，付款300→270＋30，欠170 | 两原账单、一付款、两核销 | **NOT_RUN/BLOCKED**。 |
| F6 有权前台与跨店摘要／拒绝代收 | 真实角色和浏览器操作 | **NOT_RUN/BLOCKED**。 |

**实际事件链表：** 新库的 `ydental_treatment_event`、`ydental_treatment_fee`、`ydental_settlement_source/payment/refund/close`、`account_payment`、`account_partial_reconcile` 在崩溃后只读 SQL 中全部为 **0**。因此没有任何 S10 事件→价快照→费→账单→核销→退款→库存逐行数据可列，不借用 S09 历史 PASS 冒充本轮 740 或 270＋200 业务。

## 测试结果

| 关口 | 状态 | 真实命令／退出及证据 |
| --- | --- | --- |
| 隔离库创建 | 首次 FAIL 后成功 | 首次手写创建脚本因 `CREATE DATABASE cannot run inside a transaction block` exit1，未创建；修正 autocommit 后新库创建 exit0，OID/cluster 读回一致。 |
| 原生依赖安装前 shell 路径 | FAIL，无 Odoo 启动 | 首次命令把日志相对路径指向核心工作目录下不存在的 `.local`，shell 重定向 exit1；改用隔离库绝对日志路径后才实际运行安装。 |
| Community 财务／采购销售依赖安装 | PASS，仅依赖 | `odoo-bin -i account,l10n_cn,sale,purchase --with-demo --stop-after-init --no-http` exit0；没有 S10 交易。 |
| S10 首次安装候选 | 两次 FAIL、一次安装 exit0 | `-i ydental_settlement` 第1次缺本机隔离 `phonenumbers` 路径 exit255；第2次报表 action/template XML ID 碰撞 exit255；修复后第3次 exit0。失败均保留。 |
| S10 候选升级 | exit0，范围有限 | `-u ydental_settlement` exit0。**这仍不是最终 product SHA 的安装/升级证据**：升级后又有候选代码调整，随后发生停止条件。 |
| 单笔600前置探针 | FAIL | `odoo-bin shell ... probe_600.py` 第1次 exit1：上游合成预约容量 `insufficient_balance`，事务回滚。 |
| 单笔600修正探针 | **原生 SIGSEGV，exit139** | PID `1965906`，2026-10-13 13:20 UTC，registry 初始化后 `Garbage-collecting → contextlib.__exit__ → registry.new`；探针脚本尚未执行。日志 SHA256 `9c62be35195a765bacf11f57629dd67c6d6156f5591c1d42dd2bc8a3e2cb47ef`，实际执行源码 SHA256 `eb4a22badeffd2bb33fd232527f47d89dec454adbeb103a20702ff22441766ac`。core limit 0、Apport 处理器、`/var/crash` 无本次 core；无 native stack，根因 **UNKNOWN**。不推断与旧 S07/S08-C/S09 崩溃为同一根因。 |
| 崩溃后只读保全 | PASS，非业务验收 | 新库 OID 1598603，7 个关键模块 installed；上述交易表全0、deadlock0；崩溃 PID 不存在，原 Odoo HTTP `/web/login` 200。无 Odoo、Firefox、业务数据库写或测试重跑。 |
| 新库固定 test 安装／升级／带已提交业务再升级 | **NOT_RUN/BLOCKED** | 测试模块未完成；最终 product 未再次安装。 |
| 真双 PostgreSQL backend/barrier、SQL 全财务／库存勾稽 | **NOT_RUN/BLOCKED** | 只完成崩溃后只读零记录与 deadlock 查询，不是业务并发通过。 |
| Firefox 真按钮、多角色跨店负向、中文 PDF 逐页、PO、S08/S09 集成回归 | **NOT_RUN/BLOCKED** | 按 signal11 停止。 |

**S10-T01—T16 逐项状态均为 NOT_RUN/BLOCKED。** T01 唯一出账、T02/T13 原生核销、T03 折扣、T04/T05 退款审批／额度、T06 减免、T07/T16 日结锁、T08 更正返库、T09 跨法人、T10/T14 权限、T11 PDF、T12 全链、T15 调价与驳回均没有最终固定 test 的实际 PASS。尤其不能以静态代码或依赖安装 exit0 替代 T02/T04/T09/T16。具体各日志的 SHA、大小和退出码在[机器索引](evidence/s10-blocked/incident.json)；原始日志本机保留。

## 字段、动作与配置

候选模块增加 7 类受控元数据：演示配置、fee→原生 invoice line 唯一来源、线下付款关联、退款状态、日结周期、支付方式更正、幂等回执。源码定义了 `bill/pay/refund_request/refund_approve/refund_reject/refund_execute/refund_uncertain/refund_recover/close/unlock/reclassify/waive` 私有服务动作，服务端检查本店 `settlement` 或 `finance_approval` 授权并用 S01 审计；无 ACL 的新元数据通过内部受控服务处理。以上都是**候选设计，未通过最终原生会计／权限／竞争测试**。账户映射仅允许 `demo_confirmation`；四类线下方式须不同合法 native journal 和 outstanding account，生产正式映射未批准。S07 同法人 `_transfer` 的源码仅已核对，S10 跨法人 sale/purchase 与目标财务权限的必要合同尚未完成。

## 用户效果验证

拟定的 7 步 UI 核对顺序：①有结算权前台进入结算台；②选本店 confirmed 费用出原生账；③勾选账单收500再补240；④另一人审批退100并确认实际退款；⑤旧270/新200勾选收300；⑥财务解锁并更正方式后重日结；⑦下载三类中文 PDF。**本轮 7 步全部 NOT_RUN，截图 0、PDF 0、纸张 UNKNOWN**。工作台模板存在不等于浏览器可用。

## 数据、审计与回滚

Project #4 开工前两次完整只读、一次 #34 自定义执行状态 `待启用→进行中`、变更后两次完整读回及交付前又两次完整读回，六快照均 15 当前＋22 归档、21 字段／选项、6 视图／visibleFields 9/9/5/3/7/3、7 公开 workflow。pre1=pre2、post1=post2=final1=final2 深比较一致；前后仅 #34 同一字段 `name/optionId` 两叶变化。#34 保持 **S10／进行中／Todo／OPEN**；#32/#33 待用户验收、#35—#37 待启用，其余 Project 零写。原始只读响应在本机 `.local/s10-start/`、`.local/s10-final/`，提交[脱敏摘要](evidence/s10-blocked/project.json)。

Git 候选提交及失败探针均保留；不改写 S09 历史，不删除新旧数据库、volume、日志或失败证据。因没有已提交 S10 业务交易，**没有财务逆向流水或真实资金回滚可执行**；新隔离库保持安装与零交易原状，不擅自清理。若未来返工，需在获授权的边界内先诊断 native crash，再创建新的受控合成执行，不把本库重置成“新库”。产品代码如需撤销应仅通过未来审查批准的 Git 变更，不能把尚未验证的候选发布生产。

## 复核申请

请 GPT 先独立复核本次 SIGSEGV 停止条件、保全证据、原生环境及未完成范围，并给出有界 native 诊断／返工边界。**本轮不申请 S10 技术 PASS、用户验收或 Project 状态升级**。在新崩溃根因 UNKNOWN 和 T02/T04/T09/T16、Firefox／PDF／全链均未完成前，生产继续 BLOCKED；不启 S11、不合并／强推／部署、不关闭 #34。
