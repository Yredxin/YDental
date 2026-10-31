# 按测试账号进行验收

本页按账号说明职责、可看入口及后续要验收的功能。账号标签是本手册的索引，**不是登录名**；实际登录名、门店和密码由环境负责人通过获准的私有方式提供。十个普通合成账号已设置同一个测试密码，并分别以新会话完成本机登录核验；实际登录名与共同密码仅保存在本机私有清单；链接已提供，用户自述本次前台登录成功，其他岗位是否查阅或使用尚未核实。用户已自述本次 Windows 前台登录、当前门店及患者列表正常；这是该前台账号本次有限反馈，不代表其他账号或业务流程已验。服务现已停止，下次体验须由环境负责人另行安排运行窗口并核对状态，不能仅凭账号已创建就开始。见[账号设置记录](account-setup-status.md)、[环境状态](environment-readiness.md)与[局域网记录](l1-lan-access.md)。

下表的类别和等级是指定合成门店授权；统一密码后独立读回确认授权未变，不是岗位名称自动赋权；账号须仍为有效成员，操作还受公司范围、对象、工位与资格约束。实际授予与可访问功能以负责人重新核查为准。所有原用例结果保持 **NOT_RUN**。

## 如何使用

1. 请负责人确认服务和 Windows 入口可用，并私下提供本次账号、统一测试密码和合成门店名称；每次换账号应先退出当前账号，再登录对应账号，核对**当前门店**。无法确认时停止。
2. 先依[首次只读体验](l1-first-session.md)选择该账号适用的只读子步骤，观察页面标题、可见导航和数据；不点击创建、保存、报到、叫号、处方、治疗、发药、出账、退款或日结。
3. 每次设备或账号体验在相关用例填写新 RUN-ID、浏览器、窗口宽度、缩放、实际现象和 UI 意见；部分只读步骤成功不等于整个用例 PASS。问题记 ISSUE-ID，不重做已提交操作。详见[填写方法](how-to-use.md)。
4. 下文列出的业务操作是**未来合成业务验收**；当前前置不足、L2/L3 未准出，暂不能执行。后续由负责人提供独立合成对象、状态和授权，再按链接用例的步骤执行。业务结果不明时停止核实，不能重试已提交动作。

## 按账号验收的顺序

1. 从下表选择一个账号，打开该行的岗位导航，了解该账号承担的工作；不同账号共用测试密码，不代表权限相同。
2. 仅在前置条件满足时，观察该账号行内标为可用的 L1 入口；BLOCKED 或返回 422 的入口只记录阻断，不安排执行。在实际页面核对当前门店、标题与可见内容。将日期、账号标签、环境、浏览器和观察写入对应原用例的新 RUN；整例仍保持 NOT_RUN，直到执行其完整适用步骤。
3. 再由环境负责人核对该账号的写权限、工位资格、独立合成对象及步骤前置。具备条件后才打开该行“后续业务验收”的用例，按用例的有序步骤操作并逐步比较预期结果；尚缺条件的项目登记 BLOCKED 或 DATA_NOT_READY，不假设已通过。
4. 涉及交接时按[唯一执行清单](execution-checklist.md)交给下一账号，引用既有 RUN 和同一来源的结果。已提交动作不重复执行；如需另一个分支，由负责人分配独立合成对象。
5. 用例中登记实际结果、失败步骤、问题编号及 UI 意见，截图保存至私有副本的对应 RUN 目录；暂停和恢复均先核对象状态。

例如，前台 A01 可先观察患者和队列入口；若负责人准备了可执行的新合成预约/到店来源，再按 INT-002、INT-003 分别记录。治疗医生 A02 的病历保存、实际治疗和结束属于后续业务步骤，不因为前台页面可见而视为准备完成。

## 账号索引

| 标签 | 体验账号 | 上次记录的业务授权 | L1 入口及观察 | 后续业务验收（当前 DATA_NOT_READY） |
|---|---|---|---|---|
| A01 | [前台](../10-roles/front-desk/README.md) | frontdesk write、patient write | `/ydental/patients` 看患者列表入口；`/ydental/queue` 看队列入口。仅核当前门店、页面标题与可见内容；详情对象及队列任务未确认。参见 [PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md)、[QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md)。 | 患者档案和关系、预约/登记、实际到店与报到分别依 [PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md)、[INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md)、[INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md)、[INT-004](../30-functions/rework-access-patient/cases/UAT-INT-004.md)。报到后由工位人员叫号；不可重复记录到店。 |
| A02 | [治疗医生](../10-roles/treatment-doctor/README.md) | medical write | `/ydental/supply/today` 看 My today 入口；具体安排未核，原供给已过期。无接诊参数访问临床页曾返回 422，保持阻断。参见 [SCH-001](../30-functions/space-scheduling/cases/UAT-SCH-001.md)。 | 准备有效资质、工位与独立接诊后，按 [TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md) 保存或确认文字、[TRT-002](../30-functions/clinical-exam/cases/UAT-TRT-002.md) 实际治疗、[TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md) 在不同接诊比较交还及完成；检查与处方分别交接对应岗位。 |
| A03 | [检查医生](../10-roles/exam-doctor/README.md) | exam write | `/ydental/exam` 看检查工作台入口；仅入口文字曾在本机观察，任务行未核。参见 [EXM-001](../30-functions/clinical-exam/cases/UAT-EXM-001.md)。 | 有匹配能力、有效工位及已报到任务后，按 [EXM-001](../30-functions/clinical-exam/cases/UAT-EXM-001.md)、[EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md)、[EXM-004](../30-functions/rework-clinical-finance/cases/UAT-EXM-004.md) 验收检查及结果；EXM-002 中 A03 只承担检查段，下单、保留及恢复由原医生执行。 [EXM-003](../30-functions/rework-clinical-finance/cases/UAT-EXM-003.md) 同工位检查要求同一治疗医生兼检查操作者同时具备 medical write 与 exam write 并持原医疗工位；目前 A02、A03 分别只有各自类别写权，须先合法配置同一身份及工位能力，否则 BLOCKED。结果确认不等于治疗完成。 |
| A04 | [药房](../10-roles/pharmacy/README.md) | pharmacy write | `/ydental/queue` 只看可见队列入口；药房工作台数据和权限须在用户端另核，不进入工位或发药。参见 [QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md)。 | 前台先对派生任务报到、医生先开立处方；工位、批次和库存齐备后按 [PHA-002](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) 分次发药。每次是独立提交；库存退回由仓库承担。 |
| A05 | [仓库](../10-roles/warehouse/README.md) | warehouse write | `/ydental/inventory` 入口曾返回 200，但库存目标区域空态未核，当前该子步骤 BLOCKED；不提交入库。参见 [INV-001](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md)。 | 仓库和批次尚未准备；之后按 [INV-001](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md)、[INV-002](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) 试入库与退回；来源不能唯一识别时停止。外加工接收由对应有权岗位负责。 |
| A06 | [收费](../10-roles/cashier/README.md) | settlement write | `/ydental/settlement` 入口曾返回 200，账单目标区域空态未核，当前子步骤 BLOCKED；不点出账、收款、退款或日结。参见 [FIN-001](../30-functions/settlement/cases/UAT-FIN-001.md)。 | 模拟会计配置及独立费用/账单未准备；后续按 [FIN-001](../30-functions/settlement/cases/UAT-FIN-001.md)、[FIN-002](../30-functions/settlement/cases/UAT-FIN-002.md)、[FIN-003](../30-functions/settlement/cases/UAT-FIN-003.md)、[FIN-004](../30-functions/settlement/cases/UAT-FIN-004.md) 验出账、收款、退款及日结。全额收款和欠款支线须不同账单；审批交 A07。 |
| A07 | [财务审批](../10-roles/finance-approver/README.md) | settlement read、finance_approval write | `/ydental/settlement` 曾有本机 GET 200；审批数据与页面内容未核，不能据此视为可审批。 | 由另一收费账号先发起合成退款，按 [FIN-003](../30-functions/settlement/cases/UAT-FIN-003.md) 验证审批；批准只进入待实退状态，实际退款由 A06 办理。日结解锁按 [FIN-007](../30-functions/rework-clinical-finance/cases/UAT-FIN-007.md) 核具体权限与来源。 |
| A08 | [复诊联络](../10-roles/followup-contact/README.md) | followup write、medical read | `/ydental/followups` 曾有本机 GET 200；列表内容与可用来源未核。 | 有合法治疗来源、患者门店关系和负责人时，按 [FUP-001](../30-functions/followup-lab/cases/UAT-FUP-001.md) 验收计划与联系记录；外加工自动关联计划不得重复创建。真实通知通道未授权。 |
| A09 | [外加工协调](../10-roles/lab-coordinator/README.md) | medical write、followup write | 无接诊参数的 `/ydental/clinical` 曾返回 422；当前不冒称该入口可用。 | 采购、供应商、工单及库存前置未准备；按 [LAB-001](../30-functions/followup-lab/cases/UAT-LAB-001.md)、[LAB-002](../30-functions/followup-lab/cases/UAT-LAB-002.md)、[LAB-003](../30-functions/rework-lab-evidence/cases/UAT-LAB-003.md)、[LAB-004](../30-functions/rework-lab-evidence/cases/UAT-LAB-004.md) 分别由医疗、采购、仓库和复诊有权人员配合，不能认为 A09 拥有全部权限。 |
| A10 | [报表](../10-roles/report-user/README.md) | settlement read、export write | `/ydental/reports` 看页面入口；本机仅核路径和全页文字，指标与来源未核。参见 [RPT-001](../30-functions/documents-reporting/cases/UAT-RPT-001.md)。 | 有获准来源后按 [RPT-001](../30-functions/documents-reporting/cases/UAT-RPT-001.md)、[RPT-002](../30-functions/documents-reporting/cases/UAT-RPT-002.md) 验证报表和导出；不得把 export 当成全部来源或审计读取权限。 |

当前没有已任命的店长账号：任命依赖尚未批准的政策，不能以集团或系统管理员冒称。所有业务对象只用环境负责人分配的合成对象；用户自述本次 Windows 前台登录、当前门店及患者列表正常；其他账号及未来运行窗口中的页面、列表和完整浏览器交互仍需实际核实。历史 P14-V2 T09 FAIL、P12 A04 和旧 P14/T09 FAIL、R3 PARTIAL 不因本页改变。
