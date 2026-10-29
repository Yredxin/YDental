# 岗位与权限矩阵

岗位是体验视角，不是系统固定权限模板；实际授权是**用户 × 门店 × 类别 × 等级**。`none` 无权限、`read` 只读、`write` 包含读写；更高等级不代替公司范围、对象状态、工位能力、资格或额外组。此表是本手册案例所需条件索引，不是默认授予清单；未列类别不应推断为 none 或 write。具体动作以各用例的权限和源码合同为准。来源：[16类和等级](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/models/constants.py)、[授权服务](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_access/models/ydental_access_service.py)。

| 真实类别 | 功能视角 | 常见执行条件（按实际用例核对） |
|---|---|---|
| frontdesk | 登记、报到 | 前台办理 write；患者建档可按用例由 patient 或 frontdesk write |
| patient | 患者主档 | 读 read、建档/修改 write；医疗字段另受来源限制 |
| medical | 治疗、病历和医嘱 | 医生 write；有效资格、工位和接诊状态另核 |
| exam | 检查及结果 | 检查医生 write；对应检查能力、资格和工位另核 |
| pharmacy | 药房分次发药 | 药房 write；队列可用 read，工位及接诊另核 |
| warehouse | 批次、库存、退回 | 仓库查看 read、入库退回 write；需唯一来源 |
| followup | 复诊联系 | 计划/联系 write；源读取和患者关系另核 |
| outsourcing | 外加工 | 授权类别存在；本手册工单按用例核 medical、warehouse 等实际检查，不由名称推断可执行范围 |
| settlement | 账单、收款和实退 | 查阅 read、办理 write；不同审批条件另核 |
| finance_approval | 财务审批 | 审批 write，审批人与申请人不同；工作台读取需 settlement read |
| personnel | 人员授权 | write 仍受本人可授等级、店长/集团组及范围规则约束 |
| space | 门店空间 | 查阅 read、配置 write；公共资源另需集团条件 |
| capacity | 排班与容量 | 查阅 read、配置 write；排班不等于业务授权 |
| price | 价目 | 查阅 read、维护 write；集团目录及公司范围另核 |
| supplier | 供应商合作 | 合作按具体页面/门店核权限，集团资质另需相应组 |
| export | 导出 | 本手册报表导出 write，且来源须可读取；不推定全局审计权 |

## 角色到操作条件

| 体验岗位 | 用例中可能需要的最低业务条件与额外限制 |
|---|---|
| [集团管理](../10-roles/group-admin/README.md) | 集团管理员组及允许公司；建店、模板、公共资料各核实际条件；不自动拥有所有16类权限 |
| [店长](../10-roles/store-manager/README.md) | 有效店长身份；空间 space write、排班 capacity write、价目 price write 等分别核；文书转派还需本人 medical write 和责任条件 |
| [前台](../10-roles/front-desk/README.md) | frontdesk write 登记报到；patient/frontdesk write 按档案动作核；追加组及工位动作另核 |
| [治疗医生](../10-roles/treatment-doctor/README.md) | medical write、有效资质与工位/接诊；检查、药房由对应岗位执行 |
| [检查医生](../10-roles/exam-doctor/README.md) | exam write、匹配能力/资质及工位；检查任务先合法报到 |
| [药房](../10-roles/pharmacy/README.md) | pharmacy write 和药房工位；前台另以 frontdesk write 报到 |
| [仓库](../10-roles/warehouse/README.md) | warehouse read/write 按动作；外加工涉及医生、采购和复诊责任 |
| [收费](../10-roles/cashier/README.md) | settlement write 办理；审批由另一有权人执行 |
| [财务审批](../10-roles/finance-approver/README.md) | finance_approval write、settlement read；不可自批 |
| [复诊联络](../10-roles/followup-contact/README.md) | followup write；创建按来源另需 medical read 及患者门店关系 |
| [外加工协调](../10-roles/lab-coordinator/README.md) | 多人协作：medical write、warehouse write、followup write 和原生采购组按各动作分别核 |
| [报表](../10-roles/report-user/README.md) | 所选门店来源 read；导出另需 export write，审计入口须独立核定 |

系统管理员组与集团管理员组是不同条件；店长身份、门店成员、业务类别、工位能力及原生采购组互不自动等价。账号权限由环境负责人按真实合同配置，不在公共材料中公布账号密码。
