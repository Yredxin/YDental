# 需求与技术阶段追溯

需求和TC来自 [#23 现行正文](https://github.com/Yredxin/YDental/issues/23)，是目标，不证明入口、执行或通过。用例链接只表示部分相关；明确缺口不自动变为 N/A。用户结果均 NOT_RUN。L4由Codex准备固定版本专项证据供用户审阅，未取得则保持缺口。

| 需求 | 主要阶段和TC（#23） | 对应用例 | 缺口和限制 |
|---|---|---|---|
| R01 | S00-T01—T09；各阶段安装升级/字典/翻译 | L4专项证据待准备 | 工程/字典/翻译及技术契约仅L4证据，未安排用户操作。 |
| R02 | S01-T05/T06；S03-T13 | [UAT-ACC-001](../30-functions/access/cases/UAT-ACC-001.md) | 跨公司身份同步完整性需额外证据。 |
| R03 | S01-T01/T02/T08/T09/T10 | [UAT-ACC-002](../30-functions/access/cases/UAT-ACC-002.md) | 完整模板与人员管理员边界按用例；未涵盖全部组合。 |
| R04 | S01-T07/T11/T12/T13；S04-T05/T06；S08-T09/T16；S12-T06 | [UAT-PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md), [UAT-DOC-001](../30-functions/documents-reporting/cases/UAT-DOC-001.md), [UAT-RPT-002](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 跨店历史/审计读取入口及批量负例未全部覆盖。 |
| R05 | S01-T03/T04；S03-T12；S06-T01/T05/T14 | [UAT-ACC-003](../30-functions/access/cases/UAT-ACC-003.md), [UAT-QUE-002](../30-functions/intake-queue/cases/UAT-QUE-002.md) | 撤权旧页入口未知，BLOCKED；完整跨店多会话待补。 |
| R06 | S02-T01—T10；S03-T11/T12/T13 | [UAT-SPC-001](../30-functions/space-scheduling/cases/UAT-SPC-001.md), [UAT-SPC-002](../30-functions/space-scheduling/cases/UAT-SPC-002.md), [UAT-SCH-001](../30-functions/space-scheduling/cases/UAT-SCH-001.md), [UAT-SCH-002](../30-functions/space-scheduling/cases/UAT-SCH-002.md) | 无排班/换椅/离职全部负例待补。 |
| R07 | S03-T01/T02/T04/T06/T14 | [UAT-SCH-002](../30-functions/space-scheduling/cases/UAT-SCH-002.md), [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md) | 名额比例、共享额和返额完整专项未覆盖。 |
| R08 | S05-T01/T11；S06-T02；S08-T14；E01 | [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md), [UAT-FUP-002](../30-functions/followup-lab/cases/UAT-FUP-002.md) | 有时段转诊新增 FUP-003，数据未准备；其余预约组合仍未覆盖。 |
| R09 | S03-T03/T07/T10；S05-T02/T06/T12 | [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md), [UAT-INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md) | 现场登记新增 INT-004，数据未准备；改期/返池等待补。 |
| R10 | S05-T03/T04/T08/T12；S06-T03/T21；S09-T01 | [UAT-INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md), [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md), [UAT-EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 换区、作废与容量的完整负例待补。 |
| R11 | S06-T04/T05/T09 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md), [UAT-QUE-002](../30-functions/intake-queue/cases/UAT-QUE-002.md) | 复杂优先序和多任务专项待补。 |
| R12 | S06-T01/T05/T17/T18/T19；S08-T02 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md), [UAT-TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md), [UAT-TRT-002](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | 独占、多窗口和换椅竞争需专门证据。 |
| R13 | S06-T06/T07；S09-T03/T07 | [UAT-EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 检查返回后续条件详见用例；竞争负例未完整覆盖。 |
| R14 | S06-T08/T16；S08-T05/T06/T14；S09-T04/T12 | [UAT-TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md), [UAT-EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 交还与完成分开；全部后继分配组合待补。 |
| R15 | S05-T05；S06-T09/T10/T11 | [UAT-SCH-003](../30-functions/space-scheduling/cases/UAT-SCH-003.md), [UAT-QUE-002](../30-functions/intake-queue/cases/UAT-QUE-002.md) | 停接清队与人工追加完整链需专项。 |
| R16 | S06-T12/T20；S09-T08；S11-T11；S13-T14 | [UAT-SCH-003](../30-functions/space-scheduling/cases/UAT-SCH-003.md), [UAT-TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 跨日任务/00:10清理及幂等需专门受控环境和L4。 |
| R17 | S08-T01/T03/T06/T10/T15/T16；S12-T03 | [UAT-TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md), [UAT-TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 作者/版本与文书责任按用例；正式签署未批准。 |
| R18 | S08-T07；S09-T02/T04/T05/T06/T13 | [UAT-EXM-001](../30-functions/clinical-exam/cases/UAT-EXM-001.md), [UAT-EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 同工位与部分完成新增 EXM-003/004，数据未准备；其余取消及竞争待补。 |
| R19 | S07-T01—T09；S08-T04 | [UAT-INV-001](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md), [UAT-INV-002](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md), [UAT-TRT-002](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | 过期、库存不足及待核对恢复需专项数据。 |
| R20 | S08-T08/T13；S07-T05；S10-T08 | [UAT-PHA-001](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md), [UAT-PHA-002](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md), [UAT-INV-002](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | 退款不自动退库；真实药品业务未批准。 |
| R21 | S05-T10/T13；S10-T01—T16；S12-T11 | [UAT-INT-001](../30-functions/intake-queue/cases/UAT-INT-001.md), [UAT-FIN-001](../30-functions/settlement/cases/UAT-FIN-001.md), [UAT-FIN-002](../30-functions/settlement/cases/UAT-FIN-002.md), [UAT-FIN-003](../30-functions/settlement/cases/UAT-FIN-003.md), [UAT-FIN-004](../30-functions/settlement/cases/UAT-FIN-004.md) | 免单、渠道重分类和解锁新增 FIN-005—007；账单例外、跨法人等仍未完整覆盖。 |
| R22 | S04-T01—T10；S12-T12 | [UAT-PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 合成合并和联系人验证新增 PAT-002/003；真实身份验证及文书政策未完整覆盖。 |
| R23 | S11-T01—T18 | [UAT-FUP-001](../30-functions/followup-lab/cases/UAT-FUP-001.md), [UAT-FUP-002](../30-functions/followup-lab/cases/UAT-FUP-002.md), [UAT-LAB-001](../30-functions/followup-lab/cases/UAT-LAB-001.md), [UAT-LAB-002](../30-functions/followup-lab/cases/UAT-LAB-002.md) | 有时段转诊、返工与戴用新增 FUP-003、LAB-003/004；真实通知、外部平台及其他返修仍未覆盖。 |
| R24 | S08-T11；S09-T10；S10-T11；S12-T01—T12 | [UAT-DOC-001](../30-functions/documents-reporting/cases/UAT-DOC-001.md), [UAT-DOC-002](../30-functions/documents-reporting/cases/UAT-DOC-002.md), [UAT-RPT-002](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 正式签署、税票和真实设备未授权；审计入口未固定。 |
| R25 | S06-T13；S12-T09；S13-T05/T10 | [UAT-RPT-001](../30-functions/documents-reporting/cases/UAT-RPT-001.md), [UAT-RPT-002](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 断网、补录与全部统计口径需专项证据。 |
| R26 | S13-T08/T09/T15 | L4专项证据待准备 | 50会话、持续备份、异机及恢复为L4专项，当前未由用例完成。 |

## 阶段索引

每阶段映射只代表本手册涉及的子范围；各阶段TC及缺口见上表。

| 阶段 | 范围 | 对应用例 / 缺口 |
|---|---|---|
| S00 | 工程基线 | L4工程证据待准备；无用户操作用例 |
| S01 | 权限 | [UAT-ACC-001](../30-functions/access/cases/UAT-ACC-001.md), [UAT-ACC-002](../30-functions/access/cases/UAT-ACC-002.md), [UAT-ACC-003](../30-functions/access/cases/UAT-ACC-003.md) |
| S02 | 空间 | [UAT-SPC-001](../30-functions/space-scheduling/cases/UAT-SPC-001.md), [UAT-SPC-002](../30-functions/space-scheduling/cases/UAT-SPC-002.md) |
| S03 | 排班容量 | [UAT-SCH-001](../30-functions/space-scheduling/cases/UAT-SCH-001.md), [UAT-SCH-002](../30-functions/space-scheduling/cases/UAT-SCH-002.md), [UAT-SCH-003](../30-functions/space-scheduling/cases/UAT-SCH-003.md) |
| S04 | 患者 | [UAT-PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md) |
| S05 | 受理价目 | [UAT-INT-001](../30-functions/intake-queue/cases/UAT-INT-001.md), [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md), [UAT-INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md) |
| S06 | 队列交还 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md), [UAT-QUE-002](../30-functions/intake-queue/cases/UAT-QUE-002.md), [UAT-TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md) |
| S07 | 库存 | [UAT-INV-001](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md), [UAT-INV-002](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) |
| S08 | 医疗药房 | [UAT-TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md), [UAT-TRT-002](../30-functions/clinical-exam/cases/UAT-TRT-002.md), [UAT-PHA-001](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md), [UAT-PHA-002](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) |
| S09 | 检查 | [UAT-EXM-001](../30-functions/clinical-exam/cases/UAT-EXM-001.md), [UAT-EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md) |
| S10 | 结算 | [UAT-FIN-001](../30-functions/settlement/cases/UAT-FIN-001.md), [UAT-FIN-002](../30-functions/settlement/cases/UAT-FIN-002.md), [UAT-FIN-003](../30-functions/settlement/cases/UAT-FIN-003.md), [UAT-FIN-004](../30-functions/settlement/cases/UAT-FIN-004.md) |
| S11 | 复诊加工 | [UAT-FUP-001](../30-functions/followup-lab/cases/UAT-FUP-001.md), [UAT-FUP-002](../30-functions/followup-lab/cases/UAT-FUP-002.md), [UAT-LAB-001](../30-functions/followup-lab/cases/UAT-LAB-001.md), [UAT-LAB-002](../30-functions/followup-lab/cases/UAT-LAB-002.md) |
| S12 | 文书报表 | [UAT-DOC-001](../30-functions/documents-reporting/cases/UAT-DOC-001.md), [UAT-DOC-002](../30-functions/documents-reporting/cases/UAT-DOC-002.md), [UAT-RPT-001](../30-functions/documents-reporting/cases/UAT-RPT-001.md), [UAT-RPT-002](../30-functions/documents-reporting/cases/UAT-RPT-002.md) |
| S13 | 全链和专项 | [UAT-TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md), [UAT-FIN-004](../30-functions/settlement/cases/UAT-FIN-004.md), [UAT-RPT-001](../30-functions/documents-reporting/cases/UAT-RPT-001.md) |

## 1.1 增量追溯（源码与文档，用户均 NOT_RUN）

- U02：[UAT-INT-004](../30-functions/rework-access-patient/cases/UAT-INT-004.md)。
- U05：[UAT-EXM-003](../30-functions/rework-clinical-finance/cases/UAT-EXM-003.md), [UAT-EXM-004](../30-functions/rework-clinical-finance/cases/UAT-EXM-004.md), [UAT-FIN-005](../30-functions/rework-clinical-finance/cases/UAT-FIN-005.md), [UAT-FIN-006](../30-functions/rework-clinical-finance/cases/UAT-FIN-006.md), [UAT-FIN-007](../30-functions/rework-clinical-finance/cases/UAT-FIN-007.md)。
- U06：[UAT-FUP-003](../30-functions/rework-lab-evidence/cases/UAT-FUP-003.md), [UAT-LAB-003](../30-functions/rework-lab-evidence/cases/UAT-LAB-003.md), [UAT-LAB-004](../30-functions/rework-lab-evidence/cases/UAT-LAB-004.md)。
- U07：[UAT-ACC-004](../30-functions/rework-access-patient/cases/UAT-ACC-004.md), [UAT-ACC-005](../30-functions/rework-access-patient/cases/UAT-ACC-005.md), [UAT-PAT-002](../30-functions/rework-access-patient/cases/UAT-PAT-002.md), [UAT-PAT-003](../30-functions/rework-access-patient/cases/UAT-PAT-003.md), [UAT-EVD-001](../30-functions/rework-lab-evidence/cases/UAT-EVD-001.md)。

对应 R/TC 见各用例固定说明；L4 的历史证据不外推当前环境。数据未准备或政策待定仍须阻断。
