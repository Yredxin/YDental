# 经营报表使用者

当前环境 **ENVIRONMENT_NOT_READY**；所有用户用例初始 **NOT_RUN**。本岗位是业务体验身份，不是固定权限模板或自动授权。先由负责人核对实际账号、当前门店、允许公司范围、类别等级及业务前置；只用独立合成数据。

## 职责与门诊作用

按获准门店和来源查看经营数据，追溯来源并在获准范围导出合成报表。

## 真实权限及范围

每个所选门店须在允许公司范围并有指标来源 read；收款示例需 settlement read。导出另需 export write；审计读取入口和权限须另行核定，不由报表或导出权限推定。文书示例 DOC-001/002 涉及临床来源时另需 medical read 或更高及患者与公司范围。

16 个实际授权类别及等级说明参见 [岗位与权限矩阵](../../00-guide/role-permission-matrix.md)。业务能力、Odoo 组、门店成员关系与权限类别是不同条件，不能从岗位名互相推导。

## 推荐顺序与功能用例

按照列出的用例及其前置依赖顺序进行；跨岗位项只执行本账号承担的部分，其余交由有权人员完成。操作与原始结果只保存在对应的用例内。

[UAT-RPT-001](../../30-functions/documents-reporting/cases/UAT-RPT-001.md) → [UAT-RPT-002](../../30-functions/documents-reporting/cases/UAT-RPT-002.md) → [UAT-DOC-001](../../30-functions/documents-reporting/cases/UAT-DOC-001.md) → [UAT-DOC-002](../../30-functions/documents-reporting/cases/UAT-DOC-002.md)

每项先核各用例的页面、权限、数据和停止条件。观察桌面、平板、窄屏三档布局及实际浏览器、宽度、缩放，在原用例记录实际 UI 意见；不将不同岗位或设备的体验代填为 PASS。

## 参与的跨岗位场景

[文书、原件与报表](../../20-scenarios/09-documents-reports/README.md) · [跨店与常见异常](../../20-scenarios/10-exceptions/README.md)

## 常见异常与限制

报表收款不等于收入；导出重新查询，来源变化时保留结果并重新对照；审计入口未固定为阻断。

任何持久提交结果不明、对象或权限不符、来源不能唯一识别时停止受影响动作，由环境负责人核对，切勿盲目重试。真实患者、资金、正式签署、外部通知与生产环境不在本资料制作授权内。

## 阶段记录入口

先在对应功能用例中填写实际结果，再在 [阶段完成登记](../../40-results/stage-status.md) 引用用例及问题编号；[问题汇总](../../40-results/issues.md) 和 [UI 意见](../../40-results/ui-feedback.md) 只索引原始记录。

## 1.1 补充用例

[UAT-ACC-005](../../30-functions/rework-access-patient/cases/UAT-ACC-005.md) · [UAT-EVD-001](../../30-functions/rework-lab-evidence/cases/UAT-EVD-001.md)

先核用例真实权限、前置和独立逻辑对象；其他岗位的动作由相应有权人员执行。
