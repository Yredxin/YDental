# 治疗医生

当前环境 **ENVIRONMENT_NOT_READY**；所有用户用例初始 **NOT_RUN**。本岗位是业务体验身份，不是固定权限模板或自动授权。先由负责人核对实际账号、当前门店、允许公司范围、类别等级及业务前置；只用独立合成数据。

## 职责与门诊作用

在有资质的医疗工位接诊、记录文书、执行治疗，并与检查、药房和外加工岗位交接。

## 真实权限及范围

当前门店 medical write、有效员工和医疗业务能力、相应工位连接及来源资质；文书编辑和接诊状态须符合用例前置。开处方、转诊、外加工不因排班或医生称谓自动授予。

16 个实际授权类别及等级说明参见 [岗位与权限矩阵](../../00-guide/role-permission-matrix.md)。业务能力、Odoo 组、门店成员关系与权限类别是不同条件，不能从岗位名互相推导。

## 推荐顺序与功能用例

按各用例的前置条件和场景执行；结束、转诊和外加工等分支可需要各自独立合成接诊，不假设一条接诊能串行覆盖所有分支；跨岗位项只执行本账号承担的部分，其余交由有权人员完成。操作与原始结果只保存在对应的用例内。

[UAT-QUE-001](../../30-functions/intake-queue/cases/UAT-QUE-001.md) → [UAT-TRT-001](../../30-functions/clinical-exam/cases/UAT-TRT-001.md) → [UAT-TRT-002](../../30-functions/clinical-exam/cases/UAT-TRT-002.md) → [UAT-EXM-002](../../30-functions/clinical-exam/cases/UAT-EXM-002.md) → [UAT-PHA-001](../../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) → [UAT-FUP-002](../../30-functions/followup-lab/cases/UAT-FUP-002.md) → [UAT-LAB-002](../../30-functions/followup-lab/cases/UAT-LAB-002.md) → [UAT-TRT-003](../../30-functions/clinical-exam/cases/UAT-TRT-003.md) → [UAT-DOC-001](../../30-functions/documents-reporting/cases/UAT-DOC-001.md)

每项先核各用例的页面、权限、数据和停止条件。观察桌面、平板、窄屏三档布局及实际浏览器、宽度、缩放，在原用例记录实际 UI 意见；不将不同岗位或设备的体验代填为 PASS。

## 参与的跨岗位场景

[医生治疗与病历](../../20-scenarios/03-treatment-record/README.md) · [治疗、检查及返回](../../20-scenarios/04-exam-return/README.md) · [药房与分次发药](../../20-scenarios/05-pharmacy/README.md) · [医生交接与文书责任](../../20-scenarios/07-document-handover/README.md) · [复诊、转诊与外加工](../../20-scenarios/08-followup-lab/README.md)

## 常见异常与限制

文字确认不等于实际治疗，交还不等于正常完成；结果未知停止核实，不重做费用或耗材。

任何持久提交结果不明、对象或权限不符、来源不能唯一识别时停止受影响动作，由环境负责人核对，切勿盲目重试。真实患者、资金、正式签署、外部通知与生产环境不在本资料制作授权内。

## 阶段记录入口

先在对应功能用例中填写实际结果，再在 [阶段完成登记](../../40-results/stage-status.md) 引用用例及问题编号；[问题汇总](../../40-results/issues.md) 和 [UI 意见](../../40-results/ui-feedback.md) 只索引原始记录。
