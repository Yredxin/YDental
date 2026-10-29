# 收费员

当前环境 **ENVIRONMENT_NOT_READY**；所有用户用例初始 **NOT_RUN**。本岗位是业务体验身份，不是固定权限模板或自动授权。先由负责人核对实际账号、当前门店、允许公司范围、类别等级及业务前置；只用独立合成数据。

## 职责与门诊作用

依据已确认来源生成账单，登记模拟收款、退款申请与本人日结，供后续追溯。

## 真实权限及范围

当前门店 settlement write 及允许公司范围；只读 settlement read。退款审批由不同账号以 finance_approval write 完成，不能把申请或审批当成已退款。

16 个实际授权类别及等级说明参见 [岗位与权限矩阵](../../00-guide/role-permission-matrix.md)。业务能力、Odoo 组、门店成员关系与权限类别是不同条件，不能从岗位名互相推导。

## 推荐顺序与功能用例

按照列出的用例及其前置依赖顺序进行；跨岗位项只执行本账号承担的部分，其余交由有权人员完成。操作与原始结果只保存在对应的用例内。

[UAT-FIN-001](../../30-functions/settlement/cases/UAT-FIN-001.md) → [UAT-FIN-002](../../30-functions/settlement/cases/UAT-FIN-002.md) → [UAT-FIN-003](../../30-functions/settlement/cases/UAT-FIN-003.md) → [UAT-FIN-004](../../30-functions/settlement/cases/UAT-FIN-004.md) → [UAT-RPT-001](../../30-functions/documents-reporting/cases/UAT-RPT-001.md)

每项先核各用例的页面、权限、数据和停止条件。观察桌面、平板、窄屏三档布局及实际浏览器、宽度、缩放，在原用例记录实际 UI 意见；不将不同岗位或设备的体验代填为 PASS。

## 参与的跨岗位场景

[账单、收款、退款与日结](../../20-scenarios/06-settlement/README.md) · [文书、原件与报表](../../20-scenarios/09-documents-reports/README.md) · [跨店与常见异常](../../20-scenarios/10-exceptions/README.md)

## 常见异常与限制

会计及四渠道模拟配置须事先齐备；日结范围须核全店、收费人、业务日及渠道，结果未知不重发。

任何持久提交结果不明、对象或权限不符、来源不能唯一识别时停止受影响动作，由环境负责人核对，切勿盲目重试。真实患者、资金、正式签署、外部通知与生产环境不在本资料制作授权内。

## 阶段记录入口

先在对应功能用例中填写实际结果，再在 [阶段完成登记](../../40-results/stage-status.md) 引用用例及问题编号；[问题汇总](../../40-results/issues.md) 和 [UI 意见](../../40-results/ui-feedback.md) 只索引原始记录。

## 1.1 补充用例

[UAT-FIN-005](../../30-functions/rework-clinical-finance/cases/UAT-FIN-005.md) · [UAT-FIN-006](../../30-functions/rework-clinical-finance/cases/UAT-FIN-006.md)

先核用例真实权限、前置和独立逻辑对象；其他岗位的动作由相应有权人员执行。
