# YDental 用户验收手册｜YD-UAT-R1 / 1.1

**HANDBOOK_PARTIAL · ENV_PREPARED_STOPPED（部分前置） · ENVIRONMENT_NOT_READY · USER_ACCESS_UNVERIFIED**。本材料用于计划、操作导航和用户记录；所有用户用例初始为 **NOT_RUN**。源码存在或历史技术测试不等于用户验收通过，也不证明候选已部署。产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`，文档起点 `c6cd8cbb6bef956ab05d7b9c7ecfd6d4d150cb0a`。正式开始前由环境负责人完成[环境及数据准备](00-guide/environment-and-data.md)，使用私有副本登记和保存截图。

从[唯一执行清单](00-guide/execution-checklist.md)与[逻辑对象映射](00-guide/scenario-data-map.md)安排本次来源，先读[验收计划与阶段登记](00-guide/acceptance-plan.md)、[使用与截图方法](00-guide/how-to-use.md)、[权限矩阵](00-guide/role-permission-matrix.md)和[已知限制](00-guide/known-limitations.md)。岗位是体验视角，实际操作取决于门店、能力等级及其他必要授权；不得使用历史受保护业务对象重放。具体步骤和记录只在各用例中。

L1 首次体验请查看[只读路线](00-guide/l1-first-session.md)、[访问与受控启停](00-guide/l1-access-and-startup.md)及[L1 独立审查](00-guide/l1-readiness-review.md)。目前本机服务已停止、用户端访问未验证；实际操作时在该账号已授权的页面核对当前门店，无法核实时停止。

按测试账号开始：[账号功能与验收导航](00-guide/account-based-testing.md)。

## 按岗位进入

[集团管理](10-roles/group-admin/README.md) · [店长](10-roles/store-manager/README.md) · [前台](10-roles/front-desk/README.md) · [治疗医生](10-roles/treatment-doctor/README.md) · [检查医生](10-roles/exam-doctor/README.md) · [药房](10-roles/pharmacy/README.md) · [仓库](10-roles/warehouse/README.md) · [收费](10-roles/cashier/README.md) · [财务审批](10-roles/finance-approver/README.md) · [复诊联络](10-roles/followup-contact/README.md) · [外加工](10-roles/lab-coordinator/README.md) · [经营报表](10-roles/report-user/README.md)

## 按场景进入

1. [门店和员工准备](20-scenarios/01-store-staff/README.md)
2. [预约、到店与叫号](20-scenarios/02-intake-queue/README.md)
3. [治疗与病历](20-scenarios/03-treatment-record/README.md)
4. [治疗、检查及返回](20-scenarios/04-exam-return/README.md)
5. [药房报到与分次发药](20-scenarios/05-pharmacy/README.md)
6. [出账、收款、退款和日结](20-scenarios/06-settlement/README.md)
7. [医生交接及文书责任](20-scenarios/07-document-handover/README.md)
8. [复诊、转诊和外加工](20-scenarios/08-followup-lab/README.md)
9. [文书、原件和报表](20-scenarios/09-documents-reports/README.md)
10. [跨店与异常](20-scenarios/10-exceptions/README.md)

## 按功能进入

[员工与权限](30-functions/access/README.md) · [空间与排班](30-functions/space-scheduling/README.md) · [患者、预约与队列](30-functions/intake-queue/README.md) · [治疗与检查](30-functions/clinical-exam/README.md) · [库存与药房](30-functions/inventory-pharmacy/README.md) · [结算](30-functions/settlement/README.md) · [复诊与外加工](30-functions/followup-lab/README.md) · [文书、打印与报表](30-functions/documents-reporting/README.md)

[1.1 员工与患者增量](30-functions/rework-access-patient/README.md) · [1.1 检查与结算增量](30-functions/rework-clinical-finance/README.md) · [1.1 复诊、加工及L4](30-functions/rework-lab-evidence/README.md)

## 记录与依据

[结果汇总入口](40-results/README.md) · [阶段登记](40-results/stage-status.md) · [问题](40-results/issues.md) · [UI 意见](40-results/ui-feedback.md) · [需求反馈](40-results/requirements-feedback.md) · [复验](40-results/retest-register.md) · [最终结论](40-results/final-review.md)

[修订缺口](00-guide/rework-gap-register.md) · [用例所有权](00-guide/case-ownership-map.md) · [术语](00-guide/terminology.md) · [需求追溯](00-guide/requirements-trace.md) · [源码索引](00-guide/source-index.md) · [1.1 修订报告](00-guide/handbook-v11-review.md) · [环境就绪报告](00-guide/environment-readiness.md) · [1.0 历史生产报告](00-guide/handbook-production-report.md)。P14-V2 为 PARTIAL、T09 FAIL，历史 P12 A04 和旧 P14/T09 失败保留；R3 整体 PARTIAL，R3-BUG-001 仅限定 FIXED_VERIFIED。审计入口及部分功能仍有缺口，详见限制和追溯。#37 保持 OPEN。
