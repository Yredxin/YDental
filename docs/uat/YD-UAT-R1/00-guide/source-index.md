# 程序入口及源码索引

以下位置固定产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE 依据；仅证明代码存在，安装、授权、数据和实际运行须另核。具体页面入口、控件、服务与安全条件见用例，不按需求文字猜测菜单。

| 功能 | 用例索引 | 页面源码 | 控制器或服务 |
|---|---|---|---|
| 门店、员工与权限 | [功能用例](../30-functions/access/README.md) | [页面](../../../../ydental_access/views/ydental_access_menus.xml) | [控制器或服务](../../../../ydental_access/controllers/access.py) |
| 空间 | [功能用例](../30-functions/space-scheduling/README.md) | [页面](../../../../ydental_space/views/ydental_space_views.xml) | [控制器或服务](../../../../ydental_space/models/ydental_space_station.py) |
| 排班与容量 | [功能用例](../30-functions/space-scheduling/README.md) | [页面](../../../../ydental_supply/views/ydental_supply_templates.xml) | [控制器或服务](../../../../ydental_supply/controllers/supply.py) |
| 患者 | [功能用例](../30-functions/intake-queue/README.md) | [页面](../../../../ydental_patient/views/ydental_patient_templates.xml) | [控制器或服务](../../../../ydental_patient/controllers/patient.py) |
| 预约、价目 | [功能用例](../30-functions/intake-queue/README.md) | [页面](../../../../ydental_intake/views/intake.xml) | [控制器或服务](../../../../ydental_intake/controllers/intake.py) |
| 队列 | [功能用例](../30-functions/intake-queue/README.md) | [页面](../../../../ydental_queue/views/ydental_queue_templates.xml) | [控制器或服务](../../../../ydental_queue/controllers/queue.py) |
| 文书治疗 | [功能用例](../30-functions/clinical-exam/README.md) | [页面](../../../../ydental_clinical/views/ydental_clinical_templates.xml) | [控制器或服务](../../../../ydental_treatment/controllers/treatment.py) |
| 检查 | [功能用例](../30-functions/clinical-exam/README.md) | [页面](../../../../ydental_exam/views/ydental_exam_templates.xml) | [控制器或服务](../../../../ydental_exam/controllers/exam.py) |
| 库存药房 | [功能用例](../30-functions/inventory-pharmacy/README.md) | [页面](../../../../ydental_inventory/views/ydental_inventory_templates.xml) | [控制器或服务](../../../../ydental_treatment/models/ydental_treatment_service.py) |
| 结算 | [功能用例](../30-functions/settlement/README.md) | [页面](../../../../ydental_settlement/views/ydental_settlement_templates.xml) | [控制器或服务](../../../../ydental_settlement/controllers/settlement.py) |
| 复诊外加工 | [功能用例](../30-functions/followup-lab/README.md) | [页面](../../../../ydental_followup/views/ydental_followup_views.xml) | [控制器或服务](../../../../ydental_lab/models/ydental_lab_service.py) |
| 原件 | [功能用例](../30-functions/documents-reporting/README.md) | [页面](../../../../ydental_print/views/ydental_document_templates.xml) | [控制器或服务](../../../../ydental_print/controllers/printing.py) |
| 报表 | [功能用例](../30-functions/documents-reporting/README.md) | [页面](../../../../ydental_reporting/views/ydental_reporting_templates.xml) | [控制器或服务](../../../../ydental_reporting/controllers/reporting.py) |

权限来源：[16类别](../../../../ydental_access/models/constants.py)、[服务](../../../../ydental_access/models/ydental_access_service.py)；对已知技术结论查阅[限制](known-limitations.md)。本次没有运行环境。
