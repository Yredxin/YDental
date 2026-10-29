# W0｜1.1 修订缺口登记

本登记以原手册 `0df9d14275e1bb4bed971afc684ee513914b7081` 与产品 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE 及既有报告为依据。它是工作清单，非本轮实现、动态验证或用户验收结论。35 个原编号、源路径、入口、权限、依赖及提交边界见 [用例所有权表](case-ownership-map.md)。全部原用例的用户结果仍为 `NOT_RUN`；本轮环境尚未证实，可操作状态暂按 `DATA_NOT_READY`，入口确实不明者另列 `ENTRY_UNKNOWN`，正式政策/外部能力按 `POLICY_PENDING`，必需前置不成立即 `BLOCKED`。

| ID | 范围及证据 | 待修订或需复核事项 | W0 状态／处理归属 |
|---|---|---|---|
| GAP-01 | [原验收计划](acceptance-plan.md)与10个场景 | U00—U07 是登记分组，不是可执行先后；须产出唯一执行顺序、页面、角色、前置、对象、接续状态及暂停恢复清单。不能令同一已提交来源被不同场景重复执行。 | 文档缺口；W1 |
| GAP-02 | [TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md)、[TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 文书保存、文字确认分支须可单独选择；交还A须保持 pending，正常完成B须为独立接诊，不能将A先交还再完成。自动保存也是持久版本。 | SOURCE KNOWN，连续路线待核；W1/医疗作者 |
| GAP-03 | [EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md)、[EXM-001](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 固定医嘱→原位保留→派生任务单独报到→检查执行→返回→原医生恢复的责任及状态；同一到店不重记，检查结果确认不等于返回或治疗完成。 | SOURCE KNOWN，环境前置 DATA_NOT_READY；W1 |
| GAP-04 | [PHA-001](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md)、[PHA-002](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 原医生有效接诊和已保存文书先于开方，冻结后由前台与药房分段接续；未准备来源不可提前执行处方或发药。 | SOURCE KNOWN，DATA_NOT_READY；W1/W5 |
| GAP-05 | [FIN-001—004](../30-functions/settlement/README.md) | 将已确认费用、出账、模拟收款、欠款、退款申请/审批/执行、日结分开，验证余额与权限；FIN-002 原例明确按全余额收款、余额归零；欠款须分配另一独立账单来源或独立不冲突支线，不能要求同一全付账单同时欠款。互斥支线须分配不同账单，日结核整个范围。 | SOURCE KNOWN，DATA_NOT_READY；W1/结算作者 |
| GAP-06 | [现有用例](../30-functions/access/cases/UAT-ACC-001.md)、[结果模板](../40-results/README.md) | 原单次用户填写区不足以保存多轮、多个问题、各视口UI意见与不覆盖的截图；须增加 RUN-ID、多个 ISSUE-ID、单独 UI 记录及明确的虚构示例，不能代填真实用户 PASS。 | 文档缺口；W2 |
| GAP-07 | [ACC-003](../30-functions/access/cases/UAT-ACC-003.md)、[RPT-002](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 旧页撤权所依赖的单类别受限业务入口与审计合法读回入口未固定；独立查源码、权限及可安全准备对象后，才能解除阻断或新增操作。 | `ENTRY_UNKNOWN / BLOCKED`；W3-A |
| GAP-08 | [PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md)、[INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md) | 现场登记、身份验证、联系人/监护人和实际支持的合并动作与权限需逐项核定；不把源码模型存在当作可操作入口。 | 部分已覆盖；其余 ENTRY_UNKNOWN，W3-B |
| GAP-09 | [EXM-001](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 外部检查已有用例；同工位、部分结果、不同医生接续与超时现场核实尚无完整操作证据。 | 部分 SOURCE KNOWN；其余入口/数据待核，W3-C |
| GAP-10 | [结算索引](../30-functions/settlement/README.md) | 免单、渠道更正、账单例外、日结解锁、多账单和跨店权限未完整覆盖，需查实际控件、状态及独立源，正式政策不得由手册推定。 | 部分 SOURCE KNOWN；数据/政策待核，W3-D |
| GAP-11 | [复诊加工索引](../30-functions/followup-lab/README.md) | 有时段转诊、加工返工、完成状态与采购成本来源待查；工单自动产生复诊计划，不能再为同一来源重复建计划。 | 部分 SOURCE KNOWN；其余入口/数据待核，W3-E |
| GAP-12 | [需求追溯](requirements-trace.md) R01/R16/R25/R26 | 50活动会话、真实并发、备份恢复、原件附件、断网及升级回滚需固定候选的专项证据审阅；用户不运行数据库或基础设施操作。缺证不得补 PASS。 | L4证据未准备，W3-F/W5 |
| GAP-13 | [源码索引](source-index.md)与用例源码链接 | 原用户目录内源码/历史报告相对链接指向仓库外，单独ZIP解压会失效；须转为固定候选或历史报告固定提交的GitHub链接，并验证ZIP内全部相对链接与文件哈希。 | 可移植性缺口；W4 |
| GAP-14 | [环境和数据](environment-and-data.md) | 需要核独立目标库、集群、已安装产品、角色、门店、登录、合法供给及合成对象；历史受保护库不得成为新UAT写入目标；目标身份/登录/就绪逐层独立核验，未确认用户端访问为 USER_ACCESS_UNVERIFIED。 | ENVIRONMENT_NOT_READY；W5 |
| GAP-15 | [历史限制](known-limitations.md) | P14-V2 PARTIAL/T09 FAIL、P12 A04及旧P14/T09失败、R3整体PARTIAL、R3-BUG-001仅限定FIXED_VERIFIED、E2E-BUG-002 OPEN、旧Session及前像UNKNOWN不得抹除。#37保持OPEN。 | 历史状态保留；W4/W6 |
| GAP-16 | [原受限供给入口](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_supply/models/ydental_supply_service.py) | demo供给不可售；isolated_test受真实数据库身份门禁；published需另获正式政策批准。不得伪造身份、改守卫或以环境准备改变业务规则。 | 未有本次合法目标证据；W5 |

## 盘点和验收边界

- 原编号共35个；[所有权表](case-ownership-map.md)记录用例对应页面、权限、对象及各次持久动作。静态源码存在不等于数据库已安装、按钮可用或用户访问已验证。
- 环境准备只可提交建立合法安全前置所必需的新合成对象，须在私有账本记来源与状态；不代用户执行实际治疗、药房发药、退款或其余用户应验收的一次性业务。
- 已有受保护文书、库存、费用、付款、退款、日结、原件、审计和合法责任账号不可重放、覆盖或清理。停止服务不证明会话失效或责任解除。
- 用户的结果、截图、合成对象实际映射及账号凭据保存在获准私有位置；Public Git 不保存口令、Session、真实患者或未经授权的原件。
- 本页与所有权表需要 W0 全新独立 Reviewer 核对后，才能开展大规模用例修订。各后续块仍需独立源码及文档复核，不依赖本表代签。

## 1.1 集成现状（限定源码与文档）

W1 的唯一清单、对象映射与存档分组已建立；W2 原35例具独立RUN与多问题模板。W3 新增14例，见[需求增量追溯](requirements-trace.md#11-增量追溯源码与文档用户均-not_run)。它们仅在独立审查确认的源码范围内提供步骤，不证明数据已准备或用户结果。原 ACC-003、完整审计导出、身份自动验证、历史超时与不同医生接续、账单例外、跨法人及正式外部政策仍按具体用例和限制保持未知或阻断；L4 未经本次专项实证的事项保持 UNKNOWN。W4 ZIP 和 W5 环境读回以最终报告为准。
