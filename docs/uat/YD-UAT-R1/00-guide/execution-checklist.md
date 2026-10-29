# 1.1｜唯一执行清单

**DATA_NOT_READY：本表是路线，不是已执行的记录。** 环境负责人先按[合成对象映射](scenario-data-map.md)提供本次合法、独立的对象及状态；逻辑编号不是数据库 ID。所有用户结果仍 NOT_RUN。

表中每行是一个用例或明确的用例片段，操作栏指向唯一原始用例；在该用例按步骤顺序逐项执行并逐步比较其预期，不在本表另造第二份步骤或结果。类型同时列出本行可能包含的动作：只读（可能产生正常访问审计）、准备（输入或核对）、提交（持久写入）、接续（承接已提交状态）。涉及提交的每个具体按钮与判定条件由链接用例逐步规定；不得将一整行视为单次点击。

执行前：核实际岗位、门店、目标对象和上一行结果；不满足前置时记录 BLOCKED。提交后的响应或状态不明、来源不能唯一辨认、患者/门店不一致、P0 风险时立即停止该支线，由负责人核实；不更换请求、不重复提交。编号是本清单导航次序，并非全部场景必须线性执行；不同支线需要不同对象。

| 顺序 | 唯一原用例／动作片段 | 实际岗位 | 真实入口 | 前置 | 合成对象 | 类型 | 完成后应见状态 | 下一步 |
|---:|---|---|---|---|---|---|---|---|
| 01 | [UAT-ACC-001](../30-functions/access/cases/UAT-ACC-001.md) | 集团管理员／店长 | `/ydental/access` | 授权组织、唯一登录名 | `SC01-ORG-A` | 准备＋提交 | 合成账号和成员；建店独立核回 | ACC-002 |
| 02 | [UAT-ACC-002](../30-functions/access/cases/UAT-ACC-002.md) | 集团管理员／店长 | `/ydental/access` | ACC-001、授权方案 | `SC01-STAFF-A` | 准备＋提交 | 16 类授权预览与结果 | SPC-001 |
| 03 | [UAT-SPC-001](../30-functions/space-scheduling/cases/UAT-SPC-001.md) | 空间配置人员 | `Clinic space → Floors / Areas / Workstations` | ACC-002、独立空间方案 | `SC01-SPACE-A` | 准备＋提交 | 楼层区域和工位可读回 | SPC-002 |
| 04 | [UAT-SPC-002](../30-functions/space-scheduling/cases/UAT-SPC-002.md) | 集团／空间配置人员 | `Clinic space → Resource library` | SPC-001、集团资源权限 | `SC01-RESOURCE-A` | 准备＋提交 | 资源与能力可见 | SCH-001 |
| 05 | [UAT-SCH-001](../30-functions/space-scheduling/cases/UAT-SCH-001.md) | 排班员／员工 | `/ydental/supply、/ydental/supply/today` | SPC-001、有效员工 | `SC01-SCHEDULE-A` | 准备＋提交 | 安排与建议可见 | SCH-002 |
| 06 | [UAT-SCH-002](../30-functions/space-scheduling/cases/UAT-SCH-002.md) | 容量人员 | `/ydental/supply` | SCH-001、真实测试策略 | `SC01-SUPPLY-A` | 准备＋提交 | 时段 published；可售另核 | SCH-003 |
| 07 | [UAT-SCH-003](../30-functions/space-scheduling/cases/UAT-SCH-003.md) | 容量人员 | `/ydental/supply` | 独立区域当天无营业日记录 | `SC01-DAY-A` | 准备＋提交 | 按用例开停接后重开 | INT-002 |
| 08 | [UAT-INV-001](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md) | 仓库 | `/ydental/inventory` | 合成商品及独立批次 | `SC05-LOT-A` | 准备＋提交 | 批次及 Receipt 可读回 | PHA-002 |
| 09 | [UAT-INT-001](../30-functions/intake-queue/cases/UAT-INT-001.md) | 价目维护人 | `/ydental/intake/prices` | 服务、区域能力匹配 | `SC01-PRICE-A` | 准备＋提交 | 映射和价格发布 | INT-002 |
| 10 | [UAT-PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | `/ydental/patients` | 新合成身份和联系人 | `SC02-PAT-A` | 准备＋提交 | 患者及关系存在 | INT-002 |
| 11 | [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | `/ydental/intake` | PAT-001、INT-001、SCH-002/003 | `SC02-TASK-A` | 准备＋提交 | 资格和任务可辨认 | INT-003 |
| 12 | [UAT-INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | `/ydental/intake` | INT-002 当日有效资格 | `SC02-TASK-A` | 提交 | 实际到店及任务报到 | QUE-001 |
| 13 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | `/ydental/queue` | INT-003 报到、匹配空工位 | `SC03-EXEC-C` | 提交 | 对应医疗任务 serving | TRT-001 |
| 14 | [UAT-TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | `/ydental/clinical` | QUE-001 当前医疗接诊 | `SC03-EXEC-C` | 准备＋提交 | 保存版本；确认分支 C 可选 | TRT-002 |
| 15 | [UAT-TRT-002](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | 治疗医生 | `/ydental/treatment` | TRT-001 已保存；价源/批次 | `SC03-EXEC-C` | 准备＋提交 | 实际治疗事件及来源可读回 | FIN-001 |
| 16 | [UAT-PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | `/ydental/patients` | 该分支新合成身份 | `SC07-PAT-A` | 准备＋提交 | 患者及门店关系 | INT-002 |
| 17 | [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | `/ydental/intake` | PAT-001、合法供给与映射 | `SC07-TASK-A` | 准备＋提交 | 本分支资格及任务 | INT-003 |
| 18 | [UAT-INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | `/ydental/intake` | 本分支当日有效资格 | `SC07-TASK-A` | 提交 | 本分支实际到店及报到 | QUE-001 |
| 19 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | `/ydental/queue` | 本分支任务已报到、合法空工位 | `SC07-EXEC-A` | 提交 | 本分支医疗段 serving | TRT-001 |
| 20 | [UAT-TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | `/ydental/clinical` | 独立 A 接诊已开始 | `SC07-EXEC-A` | 准备＋提交 | 仅保存 S、文书 pending；不确认 | TRT-003 A |
| 21 | [UAT-TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 治疗医生／负责人 | `/ydental/clinical` | A 保存 S；只执行步骤 1–5 | `SC07-EXEC-A` | 提交＋接续 | A handover 与责任转派读回 | 准备 B |
| 22 | [UAT-PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | `/ydental/patients` | 不同于 A 的新合成身份 | `SC07-PAT-B` | 准备＋提交 | B 患者及关系 | INT-002 |
| 23 | [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | `/ydental/intake` | B 患者、合法供给及映射 | `SC07-TASK-B` | 准备＋提交 | B 资格及任务 | INT-003 |
| 24 | [UAT-INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | `/ydental/intake` | B 当日有效资格 | `SC07-TASK-B` | 提交 | B 实际到店及报到 | QUE-001 |
| 25 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | `/ydental/queue` | A 已处理；B 任务已报到及工位可用 | `SC07-EXEC-B` | 提交 | B 医疗段 serving | TRT-001 |
| 26 | [UAT-TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | `/ydental/clinical` | B 与 A 不同，B 已开始 | `SC07-EXEC-B` | 准备＋提交 | B 文书已保存；确认按其用途选择 | TRT-003 B |
| 27 | [UAT-TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 治疗医生 | `/ydental/clinical` | B 为不同接诊且已保存；只执行步骤 6–7 | `SC07-EXEC-B` | 接续＋提交 | B completed；A 保持 handover | DOC-001 |
| 28 | [UAT-PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | `/ydental/patients` | 该分支新合成身份 | `SC04-PAT-A` | 准备＋提交 | 患者及门店关系 | INT-002 |
| 29 | [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | `/ydental/intake` | PAT-001、合法供给与映射 | `SC04-TASK-A` | 准备＋提交 | 本分支资格及任务 | INT-003 |
| 30 | [UAT-INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | `/ydental/intake` | 本分支当日有效资格 | `SC04-TASK-A` | 提交 | 本分支实际到店及报到 | QUE-001 |
| 31 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | `/ydental/queue` | 本分支任务已报到、合法空工位 | `SC04-EXEC-A` | 提交 | 本分支医疗段 serving | TRT-001 |
| 32 | [UAT-TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | `/ydental/clinical` | 独立检查接诊已开始 | `SC04-EXEC-A` | 准备＋提交 | 仅保存文书；原工位有效 | EXM-002 前半 |
| 33 | [UAT-EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 治疗医生／前台 | `/ydental/treatment、/ydental/queue` | 只执行步骤 1–5a；SC04 文书已保存、检查服务/资质 | `SC04-EXEC-A / SC04-EXAM-A` | 准备＋提交 | 医嘱冻结、原工位保留、派生任务报到 | QUE-001 检查 |
| 34 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 检查医生 | `/ydental/queue` | EXM-002 派生任务已报到 | `SC04-EXAM-A` | 提交 | 检查执行段 serving | EXM-001 |
| 35 | [UAT-EXM-001](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 检查医生 | `/ydental/exam` | 检查段 serving、实际批次/价源 | `SC04-EXAM-A` | 准备＋提交 | 执行、结果确认与段结束 | EXM-002 后半 |
| 36 | [UAT-EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 原治疗医生 | `/ydental/queue` | 只读接续步骤 5b 后执行 6–8；EXM-001 结束、保留有效、患者返回 | `SC04-EXEC-A` | 接续＋提交 | 原医疗接诊恢复 serving | 后续由负责人安排 |
| 37 | [UAT-PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | `/ydental/patients` | 该分支新合成身份 | `SC05-PAT-A` | 准备＋提交 | 患者及门店关系 | INT-002 |
| 38 | [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | `/ydental/intake` | PAT-001、合法供给与映射 | `SC05-TASK-A` | 准备＋提交 | 本分支资格及任务 | INT-003 |
| 39 | [UAT-INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | `/ydental/intake` | 本分支当日有效资格 | `SC05-TASK-A` | 提交 | 本分支实际到店及报到 | QUE-001 |
| 40 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | `/ydental/queue` | 本分支任务已报到、合法空工位 | `SC05-EXEC-A` | 提交 | 本分支医疗段 serving | TRT-001 |
| 41 | [UAT-TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | `/ydental/clinical` | 独立处方接诊已开始 | `SC05-EXEC-A` | 准备＋提交 | 文书版本已保存 | PHA-001 |
| 42 | [UAT-PHA-001](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) | 治疗医生 | `/ydental/treatment` | SC05 文书已保存、映射齐备 | `SC05-RX-A` | 准备＋提交 | 处方冻结并产生药房任务 | PHA-002 |
| 43 | [UAT-PHA-002](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 前台／药房 | `/ydental/queue、/ydental/treatment` | PHA-001、INV-001 可用批次 | `SC05-RX-A` | 接续＋提交 | 两次已确认事件、来源可追溯 | INV-002 |
| 44 | [UAT-INV-002](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | 仓库 | `/ydental/inventory` | PHA-002 选唯一移动号 | `SC05-RETURN-A` | 只读＋提交 | 退回隔离及原来源可读 | FIN-001（如来源适用） |
| 45 | [UAT-FIN-001](../30-functions/settlement/cases/UAT-FIN-001.md) | 收费 | `/ydental/settlement` | SC03-EXEC-C 的 TRT-002 已确认未出账费用及原 RUN | `SC06-BILL-A` | 准备＋提交 | 唯一账单及应收余额读回 | FIN-002 |
| 46 | [UAT-FIN-002](../30-functions/settlement/cases/UAT-FIN-002.md) | 收费 | `/ydental/settlement` | FIN-001 账单 A 未付 | `SC06-BILL-A` | 准备＋提交 | 模拟全额收款，余额归零 | FIN-003 |
| 47 | [UAT-FIN-001](../30-functions/settlement/cases/UAT-FIN-001.md) | 收费 | `/ydental/settlement` | 不同合成患者和另一未出账费用 | `SC06-BILL-B` | 准备＋提交 | 另一账单 B 尚有应收 | 欠款只读分支 |
| 48 | [UAT-FIN-001](../30-functions/settlement/cases/UAT-FIN-001.md) | 收费 | `/ydental/settlement` | 账单 B 已读回未付；不重发出账 | `SC06-BILL-B` | 只读 | 未付清列表显示账单 B 与余额 | FIN-003（账单 A） |
| 49 | [UAT-FIN-003](../30-functions/settlement/cases/UAT-FIN-003.md) | 收费／不同财务审批人 | `/ydental/settlement` | FIN-002 已读回 A 收款 | `SC06-BILL-A / SC06-REFUND-A` | 接续＋提交 | 申请、审批待实退、模拟实退分别读回 | FIN-004 |
| 50 | [UAT-FIN-004](../30-functions/settlement/cases/UAT-FIN-004.md) | 原收费员 | `/ydental/settlement` | FIN-003、完整日结范围 | `SC06-CLOSE-A` | 准备＋提交 | 同店人员渠道日结确认 | RPT-001 |
| 51 | [UAT-FUP-001](../30-functions/followup-lab/cases/UAT-FUP-001.md) | 复诊联络 | `/ydental/followups` | 另备可选状态 confirmed 治疗事件 | `SC08-FUP-A` | 准备＋提交 | 计划及合成联络记录 | LAB-001 或结束 |
| 52 | [UAT-FUP-002](../30-functions/followup-lab/cases/UAT-FUP-002.md) | 治疗医生／目标前台 | `/ydental/treatment、/ydental/intake` | 独立源接诊、目标门店及供给 | `SC08-REF-A` | 准备＋提交 | 目标接收同时到店；源释放后既有任务报到 | LAB-001 或结束 |
| 53 | [UAT-LAB-001](../30-functions/followup-lab/cases/UAT-LAB-001.md) | 集团管理／仓库 | `Dental Laboratory → Vendor qualifications / Store cooperation` | 合成供应商、授权 | `SC08-VENDOR-A` | 准备＋提交 | 资质与合作状态可见 | LAB-002 |
| 54 | [UAT-LAB-002](../30-functions/followup-lab/cases/UAT-LAB-002.md) | 治疗医生／仓库／复诊 | `Dental Laboratory → Work orders` | LAB-001、合法采购行及独立事件 | `SC08-LAB-A` | 准备＋提交 | 工单回货入库，关联复诊 ready | DOC-001 或结束 |
| 55 | [UAT-DOC-001](../30-functions/documents-reporting/cases/UAT-DOC-001.md) | 有权文书使用者 | `/ydental/documents` | SC03-EXEC-C 的 TRT-001 C 已确认原 RUN 文书，无原件 | `SC09-DOC-A` | 准备＋提交 | 唯一新原件可读回 | DOC-002 |
| 56 | [UAT-DOC-002](../30-functions/documents-reporting/cases/UAT-DOC-002.md) | 有权文书使用者 | `/ydental/documents` | DOC-001 原件 | `SC09-DOC-A` | 只读＋提交 | 打印请求返回 PDF；不代表出纸 | RPT-001 |
| 57 | [UAT-RPT-001](../30-functions/documents-reporting/cases/UAT-RPT-001.md) | 报表使用者 | `/ydental/reports` | FIN-002 合成收款、来源读权限 | `SC06-BILL-A` | 只读 | 来源和筛选可回看 | RPT-002 |
| 58 | [UAT-RPT-002](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 报表使用者 | `/ydental/reports` | RPT-001、export write、技术来源可定位 | `SC06-BILL-A` | 只读＋提交 | CSV 可对照；审计入口未知则 BLOCKED | 结束 |
| 59 | [UAT-ACC-003](../30-functions/access/cases/UAT-ACC-003.md) | 授权者／受测人员 | `/ydental/access；受测业务入口未知` | 独立账号／受限业务入口固定前阻断 | `SC10-ACCESS-A` | 准备＋提交 | ENTRY_UNKNOWN，未固定不执行 | 结束 |
| 60 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 持有工位人员 | `/ydental/queue` | 专用新任务已合法报到；只执行步骤 1–4，步骤 5 不执行 | `SC10-QUEUE-A` | 提交 | 正确任务 calling，暂停在执行前 | QUE-002 |
| 61 | [UAT-QUE-002](../30-functions/intake-queue/cases/UAT-QUE-002.md) | 持有工位人员 | `/ydental/queue` | QUE-001 仅步骤 1–4 已执行；专用任务 calling 且未开始 | `SC10-QUEUE-A` | 提交 | waiting，Missed 增 1 | 结束 |

## 1.1 新增独立分支（逐项先核数据）

下表按依赖选择执行；每个 X 编号均为逻辑占位，负责人须事前分配并私下记录真实映射。`DATA_NOT_READY` 时不得启动；实际停点和每步预期以对应唯一用例为准。FIN-007 只接续原 FIN-004，PAT-003 只接续原联系人；其余支线不重用不相容的来源。

| 顺序 | 用例 | 实际岗位 | 入口 | 前置 | 合成对象 | 类型 | 完成后状态 | 下一步 |
|---:|---|---|---|---|---|---|---|---|
| 62 | [UAT-ACC-004](../30-functions/rework-access-patient/cases/UAT-ACC-004.md) | 授权人员、受限账号 | /ydental/access、/ydental/patients | 独立账号和患者，旧页已打开，权限满足用例 | `X-ACC-004-A` | 准备＋提交 | 撤权读回，旧页写入被拒 | 结束；不再以同对象执行ACC-003 |
| 63 | [UAT-ACC-005](../30-functions/rework-access-patient/cases/UAT-ACC-005.md) | 授权摘要读取者 | /ydental/access | 合法可见的已有合成人员事件 | `X-ACC-005-A` | 只读 | 看到限定范围摘要或记录无法定位 | 结束 |
| 64 | [UAT-PAT-002](../30-functions/rework-access-patient/cases/UAT-PAT-002.md) | 患者维护者、集团核验人 | /ydental/patients | 两份无冲突独立合成身份及目标内部ID | `X-PAT-002-S / X-PAT-002-T` | 准备＋提交 | 申请及集团确认后合并追溯 | 结束；不重合并 |
| 65 | [UAT-PAT-003](../30-functions/rework-access-patient/cases/UAT-PAT-003.md) | 患者资料维护者 | /ydental/patients | PAT-001既有未验证联系人原RUN | `SC02-PAT-A / X-PAT-003-CONTACT` | 接续＋提交 | 可见验证记录及虚构依据 | 结束 |
| 66 | [UAT-INT-004](../30-functions/rework-access-patient/cases/UAT-INT-004.md) | 前台 | /ydental/intake | 新患者、当日合法供给、服务区域映射及营业日 | `X-INT-004-PAT / X-INT-004-TASK` | 准备＋提交 | 资格、到店及报到分别读回 | 可按QUE-001接续 |
| 67 | [UAT-EXM-003](../30-functions/rework-clinical-finance/cases/UAT-EXM-003.md) | 兼具资质的治疗医生 | /ydental/exam | 独立医疗serving段、原工位连接及未执行检查行 | `X-EXM-003-EXEC / X-EXM-003-ORDER` | 准备＋提交 | 检查结束后原医疗接诊及工位仍持有 | 负责人合法处理接诊 |
| 68 | [UAT-EXM-004](../30-functions/rework-clinical-finance/cases/UAT-EXM-004.md) | 检查医生 | /ydental/exam | 独立已报到并serving的检查段和未执行行 | `X-EXM-004-EXEC / X-EXM-004-ORDER` | 准备＋提交 | 确认实际执行并记录部分完成 | 负责人核后续责任 |
| 69 | [UAT-FIN-005](../30-functions/rework-clinical-finance/cases/UAT-FIN-005.md) | 收费员 | /ydental/settlement | 独立未付清账单，四渠道锁状态及金额精度满足用例 | `X-FIN-005-BILL` | 准备＋提交 | 原余额减去免单且仍为正 | 结束；不重复免单 |
| 70 | [UAT-FIN-006](../30-functions/rework-clinical-finance/cases/UAT-FIN-006.md) | 收费员 | /ydental/settlement | 独立未更正收款，原/目标渠道及账户合法 | `X-FIN-006-COLLECTION` | 准备＋提交 | 原收款与金额保留；更正由合法来源核实 | 结束；未知则停止 |
| 71 | [UAT-FIN-007](../30-functions/rework-clinical-finance/cases/UAT-FIN-007.md) | 财务审批人 | /ydental/settlement | FIN-004已确认最新周期原RUN及完整快照 | `SC06-CLOSE-A` | 接续＋提交 | 日结解锁且原三项汇总保留 | 结束；不重复解锁 |
| 72 | [UAT-FUP-003](../30-functions/rework-lab-evidence/cases/UAT-FUP-003.md) | 治疗医生、目标前台 | /ydental/treatment、/ydental/intake | 独立源接诊及目标门店可售时段，目标当日无到店 | `X-FUP-003-EXEC / X-FUP-003-TASK` | 准备＋提交 | 目标有时段资格与任务；无新增到店 | 目标实际到店按用例接续 |
| 73 | [UAT-LAB-003](../30-functions/rework-lab-evidence/cases/UAT-LAB-003.md) | 治疗医生、仓库 | Dental Laboratory → Work orders | LAB-002独立原RUN、工单available且未戴用 | `X-LAB-003-ORDER` | 接续＋提交 | 原单返工退回并生成草稿子单 | 结束；不另建同来源复诊 |
| 74 | [UAT-LAB-004](../30-functions/rework-lab-evidence/cases/UAT-LAB-004.md) | 医生、仓库、采购权限人员 | Dental Laboratory → Work orders | 独立工单已入库，另有入库后不同接诊的戴用事件 | `X-LAB-004-ORDER / X-LAB-004-EVENT` | 接续＋提交 | 采购成本来源与戴用出库可读回 | 结束；不复用返工对象 |
| 75 | [UAT-EVD-001](../30-functions/rework-lab-evidence/cases/UAT-EVD-001.md) | 用户、证据负责人 | 本用例及固定历史报告 | 提供可审阅证据索引；不足则DATA_NOT_READY | `X-EVD-001-SET` | 只读 | 逐项记录证据范围及UNKNOWN | 进入最终用户结论 |

## 暂停、恢复与分支

- 每一行从用例的原始记录或 RUN-ID 恢复，记下步骤、对象、版本与已提交状态；有持久动作结果未知时暂停，先由负责人核查，不能假定失败或重试。
- SC07 的 A 只能交还，B 只能正常完成；两者不是 SC03 确认文字的 C 接诊。先执行 TRT-003 的 A 步骤 1–5，再按清单用不同新对象准备 B；TRT-003 步骤 6 引用 B 的 QUE-001/TRT-001 既有记录，不再重复创建，接续步骤 7。不能把同一接诊既交还又完成。
- SC04 的 EXM-002 先到步骤 5a 派生任务报到并暂停；检查岗执行 QUE-001 和 EXM-001，原医生以步骤 5b 只读引用两份 RUN 结果，再接续步骤 6–8。不能重复到店、发行医嘱或检查。
- SC05 先有有效医疗接诊与已保存文书，再开处方；两次发药属于同一处方的两个不同段，每段只做一次，待核对时不结束段。
- SC06-BILL-A 来自 SC03-EXEC-C 的唯一 TRT-002 已确认费用；全额收款后余额为零，用于退款和日结；欠款只查看另一笔 SC06-BILL-B，不能对 A 同时期待欠款。账单 B 依另一 confirmed 未出账费用和独立合成患者，由 FIN-001 新建；若缺来源则欠款支线 BLOCKED。退款申请、独立审批、模拟实退、日结顺序不可互换。
- SC09-DOC-A 引用 SC03-EXEC-C 的 TRT-001 C confirmed 文书及该 RUN；如 C 未确认或已有原件，保持 BLOCKED，不能因生成原件重新确认文书。
- SC10-QUEUE-A 的 QUE-001 只执行 1–4 取得 calling 并在 5 前暂停，再执行 QUE-002；绝不预做开始执行或重复叫号。
- 财务统计、原件、报表、复诊和外加工以已建立的唯一来源为准，使用前先核状态；外加工自动建立的复诊不得再以 FUP-001 对同一来源新建。
- 本清单不要求用户创建环境、账号或政策。历史对象不得作为本次来源；不实际发送外部通知或支付。L4 仅审阅已准备的专项证据。


## 每个原用例的步骤检查索引

每个条目对应原始用例的一个可观察步骤；步骤编号、预期与停止条件以链接原文为准。对应对象、入口、前置与下一用例见上方同 ID 的执行路线；同一 ID 多次出现在路线时，以该行所分配的不同对象和 RUN-ID 为准。标记 `提交` 包括可能自动保存或形成审计的操作；`接续` 只使用已确认结果，不能重做前段。这里不另行保存结果。

| 用例与步骤 | 实际岗位 | 类型 | 完成后应观察（原用例预期） | 下一步 |
|---|---|---|---|---|
| [UAT-ACC-001 第 1 步](../30-functions/access/cases/UAT-ACC-001.md) | 集团管理员／店长 | 读 | 页面显示当前门店名称，或未选择时为 -；不要把 - 当作已选门店。 | 步骤 2 |
| [UAT-ACC-001 第 2 步](../30-functions/access/cases/UAT-ACC-001.md) | 集团管理员／店长 | 接续 | 返回页面后 Current store 显示所选门店；不属于账号的门店不应出现在可选列表。 | 步骤 3 |
| [UAT-ACC-001 第 3 步](../30-functions/access/cases/UAT-ACC-001.md) | 集团管理员／店长 | 读 | Staff 只列 Account ID、Name、Employee ID 和 Store manager，不显示 Login；登录名是否被占用不能由此表证明。发现碰撞或无法确认时停止。 | 步骤 4 |
| [UAT-ACC-001 第 4 步](../30-functions/access/cases/UAT-ACC-001.md) | 集团管理员／店长 | 提交 | 返回门店员工页面；该登录名若对应活动内部账号会关联，否则创建内部账号并关联当前门店。不要假设已发密码。 | 步骤 5 |
| [UAT-ACC-001 第 5 步](../30-functions/access/cases/UAT-ACC-001.md) | 集团管理员／店长 | 读 | 新关联员工出现在当前门店列表；身份与准备清单相符。 | 步骤 6 |
| [UAT-ACC-001 第 6 步](../30-functions/access/cases/UAT-ACC-001.md) | 集团管理员／店长 | 提交 | 目标与当前门店关联；跨公司权限不足时被拒绝，不得以其他身份绕过。 | 步骤 7 |
| [UAT-ACC-001 第 7 步](../30-functions/access/cases/UAT-ACC-001.md) | 集团管理员／店长 | 提交 | 请求返回员工页面；该页面不提供新店列表的直接读回，负责人须在获准的门店管理入口独立确认新店名称、公司及时区；若无可见读回入口，记为待验，不能据跳转认定建店成功。新店不自动成为当前账号的可选成员门店，须按授权配置关联后才能切换。 | 按上方路线交接 |
| [UAT-ACC-002 第 1 步](../30-functions/access/cases/UAT-ACC-002.md) | 集团管理员／店长 | 读 | 当前门店和目标账号相符；若管理表单不见或对象不符，停止。 | 步骤 2 |
| [UAT-ACC-002 第 2 步](../30-functions/access/cases/UAT-ACC-002.md) | 集团管理员／店长 | 准备 | 类别和等级与事前授权清单一致，尚未提交。 | 步骤 3 |
| [UAT-ACC-002 第 3 步](../30-functions/access/cases/UAT-ACC-002.md) | 集团管理员／店长 | 提交 | 请求返回门店员工页。源码规定单项设置只提交所选类别；仅凭返回页面不能观察或证明其他类别未改变。需要事前和事后的完整预览才能验证。 | 步骤 4 |
| [UAT-ACC-002 第 4 步](../30-functions/access/cases/UAT-ACC-002.md) | 集团管理员／店长 | 读 | 出现 Confirm template changes 表格，逐类别列出 Account、Store、Business category、Before、After；如事先记录了 Before，可与本次 Before 比较未选类别。 | 步骤 5 |
| [UAT-ACC-002 第 5 步](../30-functions/access/cases/UAT-ACC-002.md) | 集团管理员／店长 | 读 | 可观察到目标账户、门店及全部类别的前后等级；与清单有任何差异时点 Cancel，不确认替换。 | 步骤 6 |
| [UAT-ACC-002 第 6 步](../30-functions/access/cases/UAT-ACC-002.md) | 集团管理员／店长 | 提交 | 返回员工页；模板对该目标是全部类别替换，不是合并；缺失类别成为 None。 | 步骤 7 |
| [UAT-ACC-002 第 7 步](../30-functions/access/cases/UAT-ACC-002.md) | 集团管理员／店长 | 读 | Before 列反映已提交的等级；取消不应用第二次替换。 | 按上方路线交接 |
| [UAT-ACC-003 第 1 步](../30-functions/access/cases/UAT-ACC-003.md) | 授权者／受测人员 | 接续 | Current store 显示 A，门店选项仅包含当前有效成员门店。 | 步骤 2 |
| [UAT-ACC-003 第 2 步](../30-functions/access/cases/UAT-ACC-003.md) | 授权者／受测人员 | 读 | 页面当前显示受权的合成对象；若原本无法读取，记录前置不满足并停止。 | 步骤 3 |
| [UAT-ACC-003 第 3 步](../30-functions/access/cases/UAT-ACC-003.md) | 授权者／受测人员 | 接续 | Current store 显示 B；原标签页仍显示切换前的旧内容。 | 步骤 4 |
| [UAT-ACC-003 第 4 步](../30-functions/access/cases/UAT-ACC-003.md) | 授权者／受测人员 | 提交 | 请求因页面版本已改变被拒绝并提示需刷新（可能为错误页面）；不得将页面旧显示当成仍处于 A。若非拒绝，记录实际结果并停止。 | 步骤 5 |
| [UAT-ACC-003 第 5 步](../30-functions/access/cases/UAT-ACC-003.md) | 授权者／受测人员 | 接续 | 页面显示最新门店；切回时只选择实际有成员资格的门店。 | 步骤 6 |
| [UAT-ACC-003 第 6 步](../30-functions/access/cases/UAT-ACC-003.md) | 授权者／受测人员 | 提交 | 请求返回员工页；这是一次持久撤权。 | 步骤 7 |
| [UAT-ACC-003 第 7 步](../30-functions/access/cases/UAT-ACC-003.md) | 授权者／受测人员 | 读 | 需要该类别 read 的受限数据不再可读；若该页面还有其他合法授权路径，应由负责人预先指定仅依赖该类别的测试入口，不能把复杂权限推断为单类别拒绝。 | 步骤 8 |
| [UAT-ACC-003 第 8 步](../30-functions/access/cases/UAT-ACC-003.md) | 授权者／受测人员 | 读 | 非成员门店不出现在选择列表；不自行构造越权请求。 | 按上方路线交接 |
| [UAT-EXM-001 第 1 步](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 检查医生 | 读 | 行中患者、医嘱、任务、项目方向与准备清单一致；不同则停止。 | 步骤 2 |
| [UAT-EXM-001 第 2 步](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 检查医生 | 读 | 确认没有已存在真实执行；若已有来源，不得重复执行。 | 步骤 3 |
| [UAT-EXM-001 第 3 步](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 检查医生 | 提交 | 结果草稿可见；点击 查看独立结果与版本 在新标签打开原始 JSON，查看 version 字段后返回原工作台；必要时请环境负责人协助。未知不能填写为已测量。 | 步骤 4 |
| [UAT-EXM-001 第 4 步](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 检查医生 | 准备 | 内容与授权模拟清单相符；耗材和价源不明时停止。 | 步骤 5 |
| [UAT-EXM-001 第 5 步](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 检查医生 | 提交 | 本行显示真实执行者、费用来源和费源状态；若待核对则记录，不冒账务已完成。 | 步骤 6 |
| [UAT-EXM-001 第 6 步](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 检查医生 | 提交 | 结果状态为已确认；点击 查看独立结果与版本，在新标签原始 JSON 中核对 version 增加并返回原工作台；必要时请环境负责人协助。仅当有实际执行及非空所见才能确认，并不代表正式签发。 | 步骤 7 |
| [UAT-EXM-001 第 7 步](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 检查医生 | 提交 | 检查段结束；检查结果确认与工位段结束分别记录。若结果待核对或未解决则停止并保留事实。 | 步骤 8 |
| [UAT-EXM-001 第 8 步](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | 检查医生 | 接续 | 结果可由有权限人员按来源查阅；患者返回处理由 UAT-EXM-002 后半执行。 | 按上方路线交接 |
| [UAT-EXM-002 第 1 步](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 治疗医生 | 准备 | 页面显示 Explicit purpose、Exact service mapping 和 Approved quantity。 | 步骤 2 |
| [UAT-EXM-002 第 2 步](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 治疗医生 | 提交 | Orders 列表出现该患者检查草稿；不等同已发行或实际执行。 | 步骤 3 |
| [UAT-EXM-002 第 3 步](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 治疗医生 | 提交 | 医嘱冻结，产生对应检查任务；记下该任务，勿再次开同一医嘱。 | 步骤 4 |
| [UAT-EXM-002 第 4 步](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 治疗医生 | 提交 | Reserved return 显示原工位及保留状态；这是暂停原医疗段，不是完成或交还。 | 步骤 5a |
| [UAT-EXM-002 第 5a 步](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 前台 | 提交 | 派生检查任务进入队列，不重复记录到店；记录 RUN 后暂停。 | QUE-001 检查、EXM-001 |
| [UAT-EXM-002 第 5b 步](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 原治疗医生 | 读 | 引用 QUE-001、EXM-001 原 RUN，核同任务结果已确认、检查段结束；不重做。 | 步骤 6 |
| [UAT-EXM-002 第 6 步](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 原治疗医生 | 读 | 原工位保留仍有效，且无未解决的其他实际执行；若过期或存在未解决执行则停止。 | 步骤 7 |
| [UAT-EXM-002 第 7 步](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 原治疗医生 | 提交 | 原医疗任务恢复 serving，保留被解决；检查结果仍独立保留。 | 步骤 8 |
| [UAT-EXM-002 第 8 步](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 原治疗医生 | 读 | 当前 SC04 接诊后续由有权负责人合法处理；比较交还与完成按独立 SC07 A/B 及已有 RUN，不把返回当作完成，也不把 SC04 当作 SC07 A/B 重复操作。 | 按上方路线交接 |
| [UAT-TRT-001 第 1 步](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | 读 | 患者和当前合成任务一致；新文书创建前无原作者和历史；没有当前接诊时页面提示 No current medical reception，停止。 | 步骤 2 |
| [UAT-TRT-001 第 2 步](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | 提交 | 页面取得可编辑状态，显示 Server version 和编辑结果；若编辑占用或连接失效，停止。 | 步骤 3 |
| [UAT-TRT-001 第 3 步](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | 提交 | 输入出现在选定字段；无牙位可选 No corresponding tooth；未观察不能写成已观察。页面约 900ms 后可能自动保存并创建持久版本。 | 步骤 4 |
| [UAT-TRT-001 第 4 步](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | 提交 | 页面显示服务器已保存并记录 Server version 与时间；自动保存可能先产生版本，因此不能预设仅增加一次。若没有成功确认则停下核对。 | 步骤 5 |
| [UAT-TRT-001 第 5 步](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | 读 | 服务端内容与合成文本一致，刷新后查看 Authored version history 中的保存版本、原作者和责任人；不一致则保留本页并记录差异。 | S 结束；独立 C 可选择步骤 6 |
| [UAT-TRT-001 第 6 步](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | 提交 | 文字状态为 confirmed，服务器版本增加；刷新后查看版本历史中的确认版本，不表示治疗执行、接诊完成或正式签署。 | 步骤 7 |
| [UAT-TRT-001 第 7 步](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | 读 | 未见新增治疗事实或费用即可继续；若已确认需更正，使用有原因的追加更正，不覆盖旧版本。 | 按上方路线交接 |
| [UAT-TRT-002 第 1 步](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | 治疗医生 | 读 | 均与本次合成接诊匹配；无当前患者或写权限则停止。 | 步骤 2 |
| [UAT-TRT-002 第 2 步](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | 治疗医生 | 准备 | 选择的是本店真实存在的服务映射；无目标项目则停止并登记环境缺口。 | 步骤 3 |
| [UAT-TRT-002 第 3 步](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | 治疗医生 | 准备 | 字段与合成测试清单一致；牙位不适用使用 0 和 not applicable。 | 步骤 4 |
| [UAT-TRT-002 第 4 步](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | 治疗医生 | 准备 | 批次、数量和单位与准备清单一致；库存不足或批次不明停止。 | 步骤 5 |
| [UAT-TRT-002 第 5 步](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | 治疗医生 | 读 | 可见事实与此次合成演练一致；不能将已有事实当新治疗重做。 | 步骤 6 |
| [UAT-TRT-002 第 6 步](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | 治疗医生 | 提交 | 页面短暂提示后重载，在 Immutable actual events 区核对患者、项目、数量、来源及状态；若 pending，记录待核对原因而非视作已完成账务。响应未知则停止核查，不重试。 | 步骤 7 |
| [UAT-TRT-002 第 7 步](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | 治疗医生 | 读 | 治疗事实有独立来源；文书确认与本操作各自独立。 | 按上方路线交接 |
| [UAT-TRT-003 第 1 步](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 治疗医生／负责人 | 读 | A 为当前有效 serving 接诊，文本已在服务端保存且仍待完善。 | 步骤 2 |
| [UAT-TRT-003 第 2 步](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 治疗医生／负责人 | 提交 | 文书保存成功后原接诊进入 handover，并产生可接续任务；这不是正常完成。若无成功回执，停止并核对。 | 步骤 3 |
| [UAT-TRT-003 第 3 步](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 治疗医生／负责人 | 读 | 待完善文书仍有明确责任人，原作者和版本可见。交还已释放本次编辑器；若仍有有效编辑者须停止并由持有人释放。接诊任务交接责任与文书责任分别核对。 | 步骤 4 |
| [UAT-TRT-003 第 4 步](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 原负责人或有权店长 | 提交 | 责任人变为所选医生，版本历史及原作者保留；编辑占用未释放或资格不符时应拒绝。 | 步骤 5 |
| [UAT-TRT-003 第 5 步](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 新负责人 | 提交 | 服务器版本与补充内容可读，编辑占用释放；原作者和旧版本仍可见。 | 先准备独立 B，再接续步骤 6 |
| [UAT-TRT-003 第 6 步](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 治疗医生／负责人 | 接续 | 只引用已完成 B 的 QUE-001/TRT-001 原 RUN；B 与 A 不是同一来源、B 为 serving 且文本已保存、原工位连接有效；未准备则先按清单 22–26，已完成动作不重放。 | 步骤 7 |
| [UAT-TRT-003 第 7 步](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | 治疗医生／负责人 | 提交 | B 接诊段状态为 completed，任务结束；工位租约可仍保留，不能仅凭完成推断工位退出。A 的交还不会变成正常完成。 | 按上方路线交接 |
| [UAT-DOC-001 第 1 步](../30-functions/documents-reporting/cases/UAT-DOC-001.md) | 有权文书使用者 | 读 | 页面显示该患者在当前授权范围内的候选来源；没有候选则停止检查权限和来源。 | 步骤 2 |
| [UAT-DOC-001 第 2 步](../30-functions/documents-reporting/cases/UAT-DOC-001.md) | 有权文书使用者 | 准备 | 所选患者、来源和状态与准备清单一致，模板为合成测试。 | 步骤 3 |
| [UAT-DOC-001 第 3 步](../30-functions/documents-reporting/cases/UAT-DOC-001.md) | 有权文书使用者 | 读 | Reviewed source 预览显示所选合成内容，展开 Source and template trace 可见来源和模板摘要。 | 步骤 4 |
| [UAT-DOC-001 第 4 步](../30-functions/documents-reporting/cases/UAT-DOC-001.md) | 有权文书使用者 | 读 | 预览与合成输入相符，且没有把已有原件作为新建对象。 | 步骤 5 |
| [UAT-DOC-001 第 5 步](../30-functions/documents-reporting/cases/UAT-DOC-001.md) | 有权文书使用者 | 提交 | 页面显示 Operation accepted；此提示本身不证明已保存，结果不明不重复提交。 | 步骤 6 |
| [UAT-DOC-001 第 6 步](../30-functions/documents-reporting/cases/UAT-DOC-001.md) | 有权文书使用者 | 读 | 看到原件版本、生成时间、来源及 PDF SHA256；记录原件内部编号和版本供后续用例。 | 步骤 7 |
| [UAT-DOC-001 第 7 步](../30-functions/documents-reporting/cases/UAT-DOC-001.md) | 有权文书使用者 | 读 | 新标签显示保存的PDF，患者及合成文书内容与已审核预览一致；无法读取时记录并停止。 | 按上方路线交接 |
| [UAT-DOC-002 第 1 步](../30-functions/documents-reporting/cases/UAT-DOC-002.md) | 有权文书使用者 | 读 | Saved originals 列出已准备的原件。 | 步骤 2 |
| [UAT-DOC-002 第 2 步](../30-functions/documents-reporting/cases/UAT-DOC-002.md) | 有权文书使用者 | 读 | 四项与准备记录一致，不能确认则停止。 | 步骤 3 |
| [UAT-DOC-002 第 3 步](../30-functions/documents-reporting/cases/UAT-DOC-002.md) | 有权文书使用者 | 读 | 页面明确显示请求不代表已验证物理出纸。 | 步骤 4 |
| [UAT-DOC-002 第 4 步](../30-functions/documents-reporting/cases/UAT-DOC-002.md) | 有权文书使用者 | 提交 | 浏览器新标签接收原件PDF；记录是否可打开，不推断纸张输出。 | 步骤 5 |
| [UAT-DOC-002 第 5 步](../30-functions/documents-reporting/cases/UAT-DOC-002.md) | 有权文书使用者 | 读 | 原件版本仍可辨识；如PDF未返回或权限错误则停止并记录。 | 按上方路线交接 |
| [UAT-RPT-001 第 1 步](../30-functions/documents-reporting/cases/UAT-RPT-001.md) | 报表使用者 | 读 | 显示 Operating reports and source documents 和可选指标；无指标则停止核权限。 | 步骤 2 |
| [UAT-RPT-001 第 2 步](../30-functions/documents-reporting/cases/UAT-RPT-001.md) | 报表使用者 | 准备 | 日期与合成来源的门店营业日期一致。 | 步骤 3 |
| [UAT-RPT-001 第 3 步](../30-functions/documents-reporting/cases/UAT-RPT-001.md) | 报表使用者 | 读 | 已应用范围显示该门店、当地日期、币种和查询时间；选择门店不改变当前工作门店。 | 步骤 4 |
| [UAT-RPT-001 第 4 步](../30-functions/documents-reporting/cases/UAT-RPT-001.md) | 报表使用者 | 读 | 该行的门店、业务日期、状态和金额与准备记录一致；总额以全部匹配来源为准，不必等于单行金额。 | 步骤 5 |
| [UAT-RPT-001 第 5 步](../30-functions/documents-reporting/cases/UAT-RPT-001.md) | 报表使用者 | 读 | 来源详情显示该来源及所选过滤条件；未经授权的来源不应出现。 | 步骤 6 |
| [UAT-RPT-001 第 6 步](../30-functions/documents-reporting/cases/UAT-RPT-001.md) | 报表使用者 | 读 | 详情与来源记录一致；返回保留原过滤条件与页码。 | 按上方路线交接 |
| [UAT-RPT-002 第 1 步](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 报表使用者 | 读 | 页面显示已应用的日期、门店及币种，目标来源可辨识。 | 步骤 2 |
| [UAT-RPT-002 第 2 步](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 报表使用者 | 读 | 模型与 ID 与负责人已确认的目标来源一致；无法对应或来源超出范围则停止并记 BLOCKED。 | 步骤 3 |
| [UAT-RPT-002 第 3 步](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 报表使用者 | 提交 | 浏览器下载 CSV；导出按已应用筛选重新查询全部匹配来源，而非固定的页面快照，也不限于当前页。 | 步骤 4 |
| [UAT-RPT-002 第 4 步](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 报表使用者 | 读 | 在相同筛选且来源未变化时，范围和目标来源信息与页面对应；CSV 不提供页面原生收款单号。多币种分开。若期间来源变化，保留原结果、重新对照并记录变化，不重发经济业务；无法建立对应则 BLOCKED。 | 步骤 5 |
| [UAT-RPT-002 第 5 步](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 报表使用者 | 读 | 有证据时记录证据位置及版本；不能仅凭下载成功宣称审计已读回。 | 按上方路线交接 |
| [UAT-FUP-001 第 1 步](../30-functions/followup-lab/cases/UAT-FUP-001.md) | 复诊联络 | 读 | 显示准备好的合成门店。 | 步骤 2 |
| [UAT-FUP-001 第 2 步](../30-functions/followup-lab/cases/UAT-FUP-001.md) | 复诊联络 | 准备 | 患者与事件选项中的姓名一致；不匹配时停止。 | 步骤 3 |
| [UAT-FUP-001 第 3 步](../30-functions/followup-lab/cases/UAT-FUP-001.md) | 复诊联络 | 准备 | 输入的日期时间符合门店时区及前置要求。 | 步骤 4 |
| [UAT-FUP-001 第 4 步](../30-functions/followup-lab/cases/UAT-FUP-001.md) | 复诊联络 | 提交 | 返回工作台；在患者行看到类型、计划时间、责任人及状态；记录此行，不能仅凭跳转认定唯一提交。 | 步骤 5 |
| [UAT-FUP-001 第 5 步](../30-functions/followup-lab/cases/UAT-FUP-001.md) | 复诊联络 | 提交 | Contact history 出现该次合成记录；状态需重新查看，不能把 Unknown 当已送达。 | 步骤 6 |
| [UAT-FUP-001 第 6 步](../30-functions/followup-lab/cases/UAT-FUP-001.md) | 复诊联络 | 读 | 未关联预约时不能据此认定已预约、到店或治疗完成；预约由前台用例单独创建。 | 按上方路线交接 |
| [UAT-FUP-002 第 1 步](../30-functions/followup-lab/cases/UAT-FUP-002.md) | 治疗医生／目标前台 | 读 | 患者及接诊与准备记录一致。 | 步骤 2 |
| [UAT-FUP-002 第 2 步](../30-functions/followup-lab/cases/UAT-FUP-002.md) | 治疗医生／目标前台 | 准备 | 目标店及服务与准备数据一致；此模式不占用容量。 | 步骤 3 |
| [UAT-FUP-002 第 3 步](../30-functions/followup-lab/cases/UAT-FUP-002.md) | 治疗医生／目标前台 | 准备 | 仅无时段截止时间有值；时间位于允许范围。 | 步骤 4 |
| [UAT-FUP-002 第 4 步](../30-functions/followup-lab/cases/UAT-FUP-002.md) | 治疗医生／目标前台 | 提交 | 页面显示 Untimed source awaiting target acceptance at initiation 和编号；这不是目标资格或到店。 | 步骤 5 |
| [UAT-FUP-002 第 5 步](../30-functions/followup-lab/cases/UAT-FUP-002.md) | 目标店前台 | 读 | 依据负责人核定的唯一服务名和截止时间找到转诊；列表不显示源数值编号，不能仅凭编号匹配，不唯一则停止。 | 步骤 6 |
| [UAT-FUP-002 第 6 步](../30-functions/followup-lab/cases/UAT-FUP-002.md) | 目标店前台 | 提交 | 在目标店 Qualifications／Service tasks 检查新资格与任务的患者、服务和状态，并在 Actual arrivals 查看本次到店；目标接收同时取得资格并记录到店，未确认唯一结果则停止。 | 按上方路线交接 |
| [UAT-LAB-001 第 1 步](../30-functions/followup-lab/cases/UAT-LAB-001.md) | 集团管理 | 读 | 列表显示供应商、资质参考、有效期和状态；公司在授权范围内。 | 步骤 2 |
| [UAT-LAB-001 第 2 步](../30-functions/followup-lab/cases/UAT-LAB-001.md) | 集团管理 | 读 | 所有内容属于合成供应商，有未来有效期；资料缺失则停止。 | 步骤 3 |
| [UAT-LAB-001 第 3 步](../30-functions/followup-lab/cases/UAT-LAB-001.md) | 集团管理 | 提交 | 状态显示 approved，查看 reviewed by 和 reviewed at；已 approved 时跳过审批，不重复点击。 | 步骤 4 |
| [UAT-LAB-001 第 4 步](../30-functions/followup-lab/cases/UAT-LAB-001.md) | 仓库 | 读 | 可见供应商、Active、local reference 和负责人；若记录已归档，使用 Archived 筛选同一记录，找不到则 BLOCKED；确认 Active 状态。 | 步骤 5 |
| [UAT-LAB-001 第 5 步](../30-functions/followup-lab/cases/UAT-LAB-001.md) | 仓库 | 提交 | Active 从未启用变为启用；原已启用时跳过，不要来回切换。 | 按上方路线交接 |
| [UAT-LAB-002 第 1 步](../30-functions/followup-lab/cases/UAT-LAB-002.md) | 有采购权限人员／治疗医生 | 准备 | 表单所选来源、患者、商品及供应商均为准备好的合成对象；来源和患者由系统关联。 | 步骤 2 |
| [UAT-LAB-002 第 2 步](../30-functions/followup-lab/cases/UAT-LAB-002.md) | 治疗医生／仓库／复诊 | 提交 | 工单处于 draft；记录内部编码、患者、来源和责任人。创建时自动建立关联 waiting 复诊计划，只读查看关联，不另建计划。 | 步骤 3 |
| [UAT-LAB-002 第 3 步](../30-functions/followup-lab/cases/UAT-LAB-002.md) | 治疗医生／仓库／复诊 | 提交 | 状态变为 sent，资质及合作快照可查；此动作只记录模拟发出，不代表真实外部交付。 | 步骤 4 |
| [UAT-LAB-002 第 4 步](../30-functions/followup-lab/cases/UAT-LAB-002.md) | 具 medical 与 warehouse 权限人员 | 提交 | 状态变为 received，显示接收时间与责任人；此时不等于已入库。 | 步骤 5 |
| [UAT-LAB-002 第 5 步](../30-functions/followup-lab/cases/UAT-LAB-002.md) | 具 medical 与 warehouse 权限人员 | 提交 | 状态变为 available，显示库存事件；记录工单和事件标识，不重复入库。 | 步骤 6 |
| [UAT-LAB-002 第 6 步](../30-functions/followup-lab/cases/UAT-LAB-002.md) | 复诊岗位 | 读 | 核对该同一关联计划由 waiting 转为 ready；不将入库视为已通知、已预约或已戴用。 | 按上方路线交接 |
| [UAT-INT-001 第 1 步](../30-functions/intake-queue/cases/UAT-INT-001.md) | 价目维护人 | 读 | 页面标明当前门店及演示快照不代表确认费用。 | 步骤 2 |
| [UAT-INT-001 第 2 步](../30-functions/intake-queue/cases/UAT-INT-001.md) | 价目维护人 | 读 | 能辨认代码和名称；无集团权限或无合成服务时停止并交由合格人员准备；本用例只查现有合成服务，新增集团服务尚未验收。 | 步骤 3 |
| [UAT-INT-001 第 3 步](../30-functions/intake-queue/cases/UAT-INT-001.md) | 价目维护人 | 提交 | Store service mappings 显示所选服务及执行区域。 | 步骤 4 |
| [UAT-INT-001 第 4 步](../30-functions/intake-queue/cases/UAT-INT-001.md) | 价目维护人 | 提交 | Price versions 出现该服务的草稿、价格与有效区间。 | 步骤 5 |
| [UAT-INT-001 第 5 步](../30-functions/intake-queue/cases/UAT-INT-001.md) | 价目维护人 | 提交 | 该版本变为 reviewed，出现 Publish 条件控件。 | 步骤 6 |
| [UAT-INT-001 第 6 步](../30-functions/intake-queue/cases/UAT-INT-001.md) | 价目维护人 | 提交 | 版本状态变为 published；重叠有效版本不得当作成功发布。 | 按上方路线交接 |
| [UAT-INT-002 第 1 步](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | 读 | 门店与患者测试计划一致。 | 步骤 2 |
| [UAT-INT-002 第 2 步](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | 准备 | 选项保持 Reservation；不要选择含 reporting 的组合动作。 | 步骤 3 |
| [UAT-INT-002 第 3 步](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | 准备 | 所选患者和服务与测试计划一致。 | 步骤 4 |
| [UAT-INT-002 第 4 步](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | 准备 | 两个时刻及日期与准备的时段一致。 | 步骤 5 |
| [UAT-INT-002 第 5 步](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | 提交 | Qualifications 出现该患者和服务的有效资格，Service tasks 可见相关任务；记录其状态。 | 步骤 6 |
| [UAT-INT-002 第 6 步](../30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | 读 | 预约本身不是实际到店；不能仅凭预约声称已报到或叫号。 | 按上方路线交接 |
| [UAT-INT-003 第 1 步](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | 读 | 门店与测试记录一致。 | 步骤 2 |
| [UAT-INT-003 第 2 步](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | 提交 | Actual arrivals 显示该患者与到店时间。 | 步骤 3 |
| [UAT-INT-003 第 3 步](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | 读 | 患者号码、服务和任务状态与资格相符。 | 步骤 4 |
| [UAT-INT-003 第 4 步](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | 提交 | Accepted positions 出现相应位置，任务进入已接收路径。 | 步骤 5 |
| [UAT-INT-003 第 5 步](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | 读 | 有接受位置并可交接工位队列；到店和报到是两项独立事实。 | 步骤 6 |
| [UAT-INT-003 第 6 步](../30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | 接续 | 不再对同一任务重复报到。 | 按上方路线交接 |
| [UAT-PAT-001 第 1 步](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | 读 | 门店名称与本次被授权门店一致；不一致即停止。 | 步骤 2 |
| [UAT-PAT-001 第 2 步](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | 读 | 列表显示匹配结果；没有匹配时不把其他人的记录当成测试对象。 | 步骤 3 |
| [UAT-PAT-001 第 3 步](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | 提交 | 出现新档案并可在列表中找到；号码与姓名可识别为本次合成记录。 | 步骤 4 |
| [UAT-PAT-001 第 4 步](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | 读 | 重复提示仅为提示；新号码可见，不因共享电话自动合并。 | 步骤 5 |
| [UAT-PAT-001 第 5 步](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | 提交 | 当前门店关系出现；首次实际到店仍显示 Not yet recorded，建立关系不代表到店。 | 步骤 6 |
| [UAT-PAT-001 第 6 步](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | 提交 | Contacts and declared guardians 出现该合成联系人及关系，显示 Pending verification；声明监护人不等于已核验。 | 步骤 7 |
| [UAT-PAT-001 第 7 步](../30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台 | 接续 | 后续仅复用这个新合成患者，结果记录不包含真实联系方式。 | 按上方路线交接 |
| [UAT-QUE-001 第 1 步](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | 读 | 工位与合成任务能力匹配且显示可进入。 | 步骤 2 |
| [UAT-QUE-001 第 2 步](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | 提交 | 页面显示当前持有人、工位位置及连接到期时间。 | 步骤 3 |
| [UAT-QUE-001 第 3 步](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | 读 | 该任务位于对应区域且等待；若没有合格工位，页面给出人员／工位提示。 | 步骤 4 |
| [UAT-QUE-001 第 4 步](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | 提交 | 下一条匹配任务进入 calling；核对确为本次合成任务，若不是则停止并请负责人处理，不执行下一步。不能指定其他不匹配能力。 | 步骤 5 |
| [UAT-QUE-001 第 5 步](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | 提交 | 任务进入实际执行阶段；本步骤不等同治疗、检查或发药完成。 | 步骤 6 |
| [UAT-QUE-001 第 6 步](../30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生 | 接续 | 记录执行交接，后续实际医疗动作由对应功能用例完成。 | 按上方路线交接 |
| [UAT-QUE-002 第 1 步](../30-functions/intake-queue/cases/UAT-QUE-002.md) | 持有工位人员 | 读 | 当前人员确实持有对应工位，任务状态为 calling。 | 步骤 2 |
| [UAT-QUE-002 第 2 步](../30-functions/intake-queue/cases/UAT-QUE-002.md) | 持有工位人员 | 提交 | 该行 Missed 数相对操作前增加 1，状态变为 waiting；记录实际排序。 | 步骤 3 |
| [UAT-QUE-002 第 3 步](../30-functions/intake-queue/cases/UAT-QUE-002.md) | 持有工位人员 | 读 | 过号计数为原值加 1，状态为 waiting；位移按测试环境明确配置，不凭岗位名称推断。 | 步骤 4 |
| [UAT-QUE-002 第 4 步](../30-functions/intake-queue/cases/UAT-QUE-002.md) | 持有工位人员 | 读 | 显示连接状态或现场核验提示；未确认成功不能作为已完成。 | 步骤 5 |
| [UAT-QUE-002 第 5 步](../30-functions/intake-queue/cases/UAT-QUE-002.md) | 持有工位人员 | 接续 | 无需通过重复提交制造第二次过号。 | 按上方路线交接 |
| [UAT-INV-001 第 1 步](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md) | 仓库 | 读 | 显示的是约定的隔离测试门店。 | 步骤 2 |
| [UAT-INV-001 第 2 步](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md) | 仓库 | 读 | Lots and alerts 显示当前授权门店的匹配产品／批次；若已有同名待建批次则停止。 | 步骤 3 |
| [UAT-INV-001 第 3 步](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md) | 仓库 | 提交 | 返回工作台后查询该产品可见新批次；记录批次名称。 | 步骤 4 |
| [UAT-INV-001 第 4 步](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md) | 仓库 | 准备 | 提交前产品、批次、单位和数量与测试计划一致。 | 步骤 5 |
| [UAT-INV-001 第 5 步](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md) | 仓库 | 提交 | 搜索相同产品：Lots and alerts 显示该批次及库存；Inventory sources and recovery 显示 Receipt 来源和 Stock confirmed 状态。 | 步骤 6 |
| [UAT-INV-001 第 6 步](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md) | 仓库 | 读 | 新批次起始库存为零且无并发操作时，入库后 On hand／Available 与入库数量一致；存在保留时记录差异并停止后续发药。 | 按上方路线交接 |
| [UAT-INV-002 第 1 步](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | 仓库 | 读 | 显示处方或补货来源、产品、批次、数量、责任人、Native movement 及 Stock confirmed，且移动号与事先记录完全相符；否则停止。 | 步骤 2 |
| [UAT-INV-002 第 2 步](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | 仓库 | 读 | 记录三个独立数值及该移动对应的原发出数量，来源属于当前门店。 | 步骤 3 |
| [UAT-INV-002 第 3 步](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | 仓库 | 准备 | 可见 Confirmed unit、Actual quantity、Unique source reference、Evidence and reason。 | 步骤 4 |
| [UAT-INV-002 第 4 步](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | 仓库 | 提交 | 新的 Physical return 来源出现；该数量进入 Quarantine，而不是直接成为 Available。 | 步骤 5 |
| [UAT-INV-002 第 5 步](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | 仓库 | 读 | 在无并发变更时 Quarantine 增加本次退回数量；原发药来源仍保留。 | 步骤 6 |
| [UAT-INV-002 第 6 步](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | 仓库 | 接续 | 不自动选择 Verify physical destination、放行或报损；处方额度不因退回恢复。 | 按上方路线交接 |
| [UAT-PHA-001 第 1 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) | 治疗医生 | 读 | 页面显示约定合成患者和医生的当前接诊。 | 步骤 2 |
| [UAT-PHA-001 第 2 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) | 治疗医生 | 准备 | 显示处方草稿输入区。 | 步骤 3 |
| [UAT-PHA-001 第 3 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) | 治疗医生 | 准备 | 药品和服务单位相符，四项说明均非空；数量按单位步长可拆成两次。 | 步骤 4 |
| [UAT-PHA-001 第 4 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) | 治疗医生 | 提交 | Frozen orders and remaining quantities 出现该患者的草稿、明细与版本；不出现实际发药事实。 | 步骤 5 |
| [UAT-PHA-001 第 5 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) | 治疗医生 | 提交 | 该订单显示 Issued, frozen（已开立、冻结），显示对应药房 Segment 及 task，任务仍待明确报到；处方不再是可编辑草稿。 | 步骤 6 |
| [UAT-PHA-001 第 6 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) | 治疗医生 | 接续 | 不重复创建或冻结处方。 | 按上方路线交接 |
| [UAT-PHA-002 第 1 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 前台报到 → 药房第 2 步开始 | 提交 | 对应任务进入已报到路径；药房在第 2 步叫号并开始，不为其他任务报到。 | 步骤 2 |
| [UAT-PHA-002 第 2 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 药房 | 接续＋提交 | 当前执行段显示约定任务编号并进入服务中；若叫到其他任务立即停止。 | 步骤 3 |
| [UAT-PHA-002 第 3 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 药房（pharmacy write） | 读 | 患者、药品、批准总量、待发量与计划一致，处方显示 Issued, frozen（已开立、冻结）。 | 步骤 4 |
| [UAT-PHA-002 第 4 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 药房（pharmacy write） | 提交 | 当前行 Remaining 比之前减少第一部分数量；Immutable actual events 出现该次实际发药记录，状态为 Fee and stock confirmed，且可见费用来源和 native stock moves。若显示 Fact awaiting reconciliation、费用或移动缺失，停止，不结束段或重复发药。 | 步骤 5 |
| [UAT-PHA-002 第 5 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 药房（pharmacy write） | 提交 | 当前段完成并释放工位；若仍有剩余，处方仍显示 Issued, frozen，产生新的待报到段及任务。 | 步骤 6 |
| [UAT-PHA-002 第 6 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 前台报到 → 药房叫号及开始（pharmacy write） | 接续＋提交 | 队列中的任务编号与新处方段一致；治疗页再核对同一合成患者。 | 步骤 7 |
| [UAT-PHA-002 第 7 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 药房（pharmacy write） | 提交 | Remaining 为零；第二次实际发药记录显示 Fee and stock confirmed 且费用和 native stock moves 可见，分别保留两次数量与移动号。若状态待核对或来源缺失，停止，不结束段或重复发药。 | 步骤 8 |
| [UAT-PHA-002 第 8 步](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 药房（pharmacy write） | 提交 | 当前段完成，处方显示 All approved quantities dispensed（全部批准数量已发放）；不再产生新的发药段。 | 按上方路线交接 |
| [UAT-FIN-001 第 1 步](../30-functions/settlement/cases/UAT-FIN-001.md) | 收费 | 读 | 门店与准备的合成门店相同。 | 步骤 2 |
| [UAT-FIN-001 第 2 步](../30-functions/settlement/cases/UAT-FIN-001.md) | 收费 | 读 | 患者被明确选择；搜索列表本身不代表已选中。 | 步骤 3 |
| [UAT-FIN-001 第 3 步](../30-functions/settlement/cases/UAT-FIN-001.md) | 收费 | 读 | 费用与准备记录相符；待核对费用不选作出账。 | 步骤 4 |
| [UAT-FIN-001 第 4 步](../30-functions/settlement/cases/UAT-FIN-001.md) | 收费 | 准备 | 所选患者号、业务日及金额与第3步一致。 | 步骤 5 |
| [UAT-FIN-001 第 5 步](../30-functions/settlement/cases/UAT-FIN-001.md) | 收费 | 提交 | 页面提示受理；该提示本身不是持久提交证明。 | 步骤 6 |
| [UAT-FIN-001 第 6 步](../30-functions/settlement/cases/UAT-FIN-001.md) | 收费 | 读 | 新账单原金额及余额等于该费用金额；记录账单号供收款使用。 | 按上方路线交接 |
| [UAT-FIN-002 第 1 步](../30-functions/settlement/cases/UAT-FIN-002.md) | 收费 | 读 | 已出账未付清列出目标账单号及余额。 | 步骤 2 |
| [UAT-FIN-002 第 2 步](../30-functions/settlement/cases/UAT-FIN-002.md) | 收费 | 读 | 所列勾选项含目标账单号及余额。 | 步骤 3 |
| [UAT-FIN-002 第 3 步](../30-functions/settlement/cases/UAT-FIN-002.md) | 收费 | 准备 | 金额不大于所选账单余额，方式与测试约定一致。 | 步骤 4 |
| [UAT-FIN-002 第 4 步](../30-functions/settlement/cases/UAT-FIN-002.md) | 收费 | 准备 | 时间、方式及说明与合成测试记录一致；不填写真实凭据。 | 步骤 5 |
| [UAT-FIN-002 第 5 步](../30-functions/settlement/cases/UAT-FIN-002.md) | 收费 | 提交 | 页面提示受理；不能仅凭提示认定已提交。 | 步骤 6 |
| [UAT-FIN-002 第 6 步](../30-functions/settlement/cases/UAT-FIN-002.md) | 收费 | 读 | 出现对应金额和方式的 Collection；目标账单余额为零并出现在已结清列表。 | 按上方路线交接 |
| [UAT-FIN-003 第 1 步](../30-functions/settlement/cases/UAT-FIN-003.md) | 收费／不同财务审批人 | 读 | 收款单号及金额与前例记录一致。 | 步骤 2 |
| [UAT-FIN-003 第 2 步](../30-functions/settlement/cases/UAT-FIN-003.md) | 收费／不同财务审批人 | 提交 | Refund request 出现对应原收款、金额和申请状态；申请不是实际退款。 | 步骤 3 |
| [UAT-FIN-003 第 3 步](../30-functions/settlement/cases/UAT-FIN-003.md) | 财务审批人 | 读 | 目标申请及原收款一致，出现 Review refund request。 | 步骤 4 |
| [UAT-FIN-003 第 4 步](../30-functions/settlement/cases/UAT-FIN-003.md) | 财务审批人 | 提交 | 退款状态变为已批准、等待线下实退；此时尚未登记实际退款。 | 步骤 5 |
| [UAT-FIN-003 第 5 步](../30-functions/settlement/cases/UAT-FIN-003.md) | 收费员 | 准备 | 金额与已批准申请一致，模拟说明不含真实财务信息。 | 步骤 6 |
| [UAT-FIN-003 第 6 步](../30-functions/settlement/cases/UAT-FIN-003.md) | 收费员 | 提交 | 目标退款状态变为已完成；原收款及退款记录均可定位。 | 步骤 7 |
| [UAT-FIN-003 第 7 步](../30-functions/settlement/cases/UAT-FIN-003.md) | 收费／不同财务审批人 | 接续 | 审批与实退分别留有记录；不能以审批状态代替实际退款。 | 按上方路线交接 |
| [UAT-FIN-004 第 1 步](../30-functions/settlement/cases/UAT-FIN-004.md) | 原收费员 | 读 | 门店和账号与该收退款的执行记录一致。 | 步骤 2 |
| [UAT-FIN-004 第 2 步](../30-functions/settlement/cases/UAT-FIN-004.md) | 原收费员 | 读 | 准备独立期望：收款、实退及待处理额度分别列出，不把待处理当已退款。 | 步骤 3 |
| [UAT-FIN-004 第 3 步](../30-functions/settlement/cases/UAT-FIN-004.md) | 原收费员 | 准备 | 日期和方式与准备记录一致，不是未来日期。 | 步骤 4 |
| [UAT-FIN-004 第 4 步](../30-functions/settlement/cases/UAT-FIN-004.md) | 原收费员 | 提交 | 页面提示受理；不以提示作为持久提交证明。 | 步骤 5 |
| [UAT-FIN-004 第 5 步](../30-functions/settlement/cases/UAT-FIN-004.md) | 原收费员 | 读 | 状态已确认；Actual collections、实退和待处理快照分别等于准备值。 | 步骤 6 |
| [UAT-FIN-004 第 6 步](../30-functions/settlement/cases/UAT-FIN-004.md) | 原收费员 | 读 | 可识别该次日结；净额按收款减实退计算，不减待处理快照。 | 按上方路线交接 |
| [UAT-SCH-001 第 1 步](../30-functions/space-scheduling/cases/UAT-SCH-001.md) | 排班员／员工 | 读 | 页面显示当前选中门店和本地时区；Weekly plan 包含员工、地点、时间和状态。 | 步骤 2 |
| [UAT-SCH-001 第 2 步](../30-functions/space-scheduling/cases/UAT-SCH-001.md) | 排班员／员工 | 准备 | 表单显示 Employee、Workstation、Area、Start、End、Reason；只能选工位或区域之一。 | 步骤 3 |
| [UAT-SCH-001 第 3 步](../30-functions/space-scheduling/cases/UAT-SCH-001.md) | 排班员／员工 | 提交 | 该员工一条新安排显示选择的地点和本地时间；若有警告，记录具体内容。 | 步骤 4 |
| [UAT-SCH-001 第 4 步](../30-functions/space-scheduling/cases/UAT-SCH-001.md) | 排班员／员工 | 读 | 在测试日对应安排显示门店、时间、工位或区域；未命中当天时显示无有效安排提示。 | 步骤 5 |
| [UAT-SCH-001 第 5 步](../30-functions/space-scheduling/cases/UAT-SCH-001.md) | 排班员／员工 | 读 | 页面明确安排只是建议；当前会话门店在用户选择前保持原值，建议页面提供信息而不等同工位已接诊。 | 按上方路线交接 |
| [UAT-SCH-002 第 1 步](../30-functions/space-scheduling/cases/UAT-SCH-002.md) | 容量人员 | 读 | 能辨认适用策略；工位优先于最近区域，再到门店；已有时段保留原策略版本。 | 步骤 2 |
| [UAT-SCH-002 第 2 步](../30-functions/space-scheduling/cases/UAT-SCH-002.md) | 容量人员 | 准备 | 所选能力属于该工位；安排区域本身不增加容量。 | 步骤 3 |
| [UAT-SCH-002 第 3 步](../30-functions/space-scheduling/cases/UAT-SCH-002.md) | 容量人员 | 提交 | 该工位的 Shared capacity 表出现新时段、总数、预约与现场剩余及状态；零预约分配时显示警告。 | 步骤 4 |
| [UAT-SCH-002 第 4 步](../30-functions/space-scheduling/cases/UAT-SCH-002.md) | 容量人员 | 提交 | 该行状态显示已发布；这是资格覆盖确认，仍取决于策略和营业日，不能直接推断可以预约。 | 步骤 5 |
| [UAT-SCH-002 第 5 步](../30-functions/space-scheduling/cases/UAT-SCH-002.md) | 容量人员 | 读 | 同一时段工位的共享总量只计一次，不按每个能力重复相加；记下实际数值。 | 按上方路线交接 |
| [UAT-SCH-003 第 1 步](../30-functions/space-scheduling/cases/UAT-SCH-003.md) | 容量人员 | 读 | 已存在的当天区域显示名称、状态和本地日期；未开接的区域可在 Open a reporting area today 下选择。 | 步骤 2 |
| [UAT-SCH-003 第 2 步](../30-functions/space-scheduling/cases/UAT-SCH-003.md) | 容量人员 | 提交 | 当天该区域显示 open；这是区域开接，不代表整个门店全部区域开接。 | 步骤 3 |
| [UAT-SCH-003 第 3 步](../30-functions/space-scheduling/cases/UAT-SCH-003.md) | 容量人员 | 提交 | 状态显示停止普通报到（draining）；不要将其解释为已停止所有叫号。 | 步骤 4 |
| [UAT-SCH-003 第 4 步](../30-functions/space-scheduling/cases/UAT-SCH-003.md) | 容量人员 | 提交 | 状态变为 closed；如仍有待叫或正在叫号，系统应拒绝关闭并保留当前状态。 | 步骤 5 |
| [UAT-SCH-003 第 5 步](../30-functions/space-scheduling/cases/UAT-SCH-003.md) | 容量人员 | 提交 | 该区域回到 open；不开启其他区域，也不恢复旧日队列。 | 按上方路线交接 |
| [UAT-SPC-001 第 1 步](../30-functions/space-scheduling/cases/UAT-SPC-001.md) | 空间配置人员 | 提交 | 楼层列表中出现该门店的新名称；重开记录可见相同门店和宽高。 | 步骤 2 |
| [UAT-SPC-001 第 2 步](../30-functions/space-scheduling/cases/UAT-SPC-001.md) | 空间配置人员 | 提交 | 保存后区域属于该楼层；独立报到区域显示为自身的 Reporting area。 | 步骤 3 |
| [UAT-SPC-001 第 3 步](../30-functions/space-scheduling/cases/UAT-SPC-001.md) | 空间配置人员 | 提交 | 重开记录显示所选楼层、区域及开关；Reporting area 与区域的报到归属一致。 | 步骤 4 |
| [UAT-SPC-001 第 4 步](../30-functions/space-scheduling/cases/UAT-SPC-001.md) | 空间配置人员 | 提交 | 显示结果来自已放置资源的能力与 Added 的并集，再扣除 Removed；它不是用户权限等级。 | 步骤 5 |
| [UAT-SPC-001 第 5 步](../30-functions/space-scheduling/cases/UAT-SPC-001.md) | 空间配置人员 | 读 | 平面可识别刚建立的区域和工位，位置与表单值对应；记录具体视口和看见的错位。 | 按上方路线交接 |
| [UAT-SPC-002 第 1 步](../30-functions/space-scheduling/cases/UAT-SPC-002.md) | 集团／空间配置人员 | 读 | 可见的资源属于该门店或允许读取的公共资源；不推断列表涵盖其他门店。 | 步骤 2 |
| [UAT-SPC-002 第 2 步](../30-functions/space-scheduling/cases/UAT-SPC-002.md) | 集团／空间配置人员 | 准备 | 表单提供对应字段；上传仅为本次测试素材。 | 步骤 3 |
| [UAT-SPC-002 第 3 步](../30-functions/space-scheduling/cases/UAT-SPC-002.md) | 集团／空间配置人员 | 提交 | 名称、门店和类型与输入一致；系统保留净化后的 SVG，不要求原始上传文件仍存在。 | 步骤 4 |
| [UAT-SPC-002 第 4 步](../30-functions/space-scheduling/cases/UAT-SPC-002.md) | 集团／空间配置人员 | 提交 | 集团账号可保存该公共资源；普通门店写账号不能据此获得公共资源写权。未准备该身份时此步记为未执行。 | 步骤 5 |
| [UAT-SPC-002 第 5 步](../30-functions/space-scheduling/cases/UAT-SPC-002.md) | 集团／空间配置人员 | 读 | 门店账号可查看授权范围内共享资源；公共资源更改不应获得仅凭门店 space=write 的授权。 | 按上方路线交接 |
