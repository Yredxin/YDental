# 1.1｜场景合成对象分配与交接

下列均是**逻辑占位符，不是已经存在的数据库 ID 或验收结果**。环境负责人为本次独立合成环境逐项分配真实对象、可见编号及当前状态，并通过私有方式向对应岗位交付；不得把真实账号凭据、患者信息或私有对象映射写到公开仓库。没有可安全准备或核对的对象，相关行保持 `DATA_NOT_READY` / `BLOCKED`。本页不替代各用例的执行记录。[执行清单](execution-checklist.md)是动作所有权与顺序入口。

对象标识用于把**同一来源的接续**与**不同来源的再次执行**区分开；一个逻辑对象可包含关联的患者、任务及版本，但实际映射必须由负责人逐项给出。不能仅凭相同姓名或相同批次猜测来源。用户不查询数据库，也不制造来源或政策。

| 场景 | 逻辑对象 | 需要负责人准备或在用例执行后记录的对应关系 | 来源归属、状态及后续 |
|---|---|---|---|
| 01 | `SC01-ORG-A`、`SC01-STAFF-A` | 合成公司/门店、唯一未占用登录名、成员与权限对象；不是历史账号 | ACC-001/002；环境必需岗位账号可事先准备，但验收创建动作需另有未使用对象，不得重新创建已准备账号。 |
| 01 | `SC01-SPACE-A`、`SC01-RESOURCE-A` | 新楼层、报到区域、工位和资源；人员能力与门店匹配 | SPC-001/002 新建；若环境已准备运行所需基础工位，验收用另一个独立空间。 |
| 01 | `SC01-SCHEDULE-A`、`SC01-SUPPLY-A`、`SC01-DAY-A`、`SC01-PRICE-A` | 安排/合法供给、该区域当天尚无日记录、服务映射及价格 | SCH-001/002/003、INT-001 各自产生或记录；正式供给政策不由用户设置；测试供给须真实符合身份。 |
| 02→03 | `SC02-PAT-A`、`SC02-TASK-A`、`SC03-EXEC-C` | 一名新合成患者、资格任务及其医疗执行段，记录任务编号与当前持有人 | PAT-001→INT-002→INT-003→QUE-001；TRT-001 的 C 文字确认为可选，再 TRT-002。若执行段仍 serving，安排后续独立患者/医生/工位，或由负责人先合法处理。 |
| 07 | `SC07-PAT-A/B`、`SC07-TASK-A/B`、`SC07-EXEC-A/B` | 两个**不同接诊**及各自文书、患者、任务与工位，必要时分别准备独立医生 | A：TRT-001 只保存 S、保持 pending，再 TRT-003 A 交还与责任接手。B：在 A 完成后开始，或不同医生及工位独立准备；TRT-003 B 正常完成。同一接诊不得两种终态。 |
| 04 | `SC04-PAT-A`、`SC04-TASK-A`、`SC04-EXEC-A`、`SC04-EXAM-A` | 独立医疗段、原工位/持有人，以及本次检查医嘱、派生任务、检查工位和资质 | TRT-001 保存 → EXM-002 步骤1–5a 开医嘱、保留及派生报到 → QUE-001 检查 → EXM-001 → EXM-002 步骤5b引用两份原RUN及6–8由原医生确认患者返回并恢复。检查任务不重复记录患者到店。 |
| 05 | `SC05-PAT-A`、`SC05-TASK-A`、`SC05-EXEC-A`、`SC05-RX-A`、`SC05-LOT-A`、`SC05-RETURN-A` | 不同医疗接诊和保存版本、可分两段的处方、匹配库存批次，以及按原生移动号唯一辨认的退回来源 | PHA-001 冻结→PHA-002 两次执行段→INV-002 隔离退回；发药事件或库存来源待核对、无法唯一识别时停止。环境已有基础库存则 INV-001 验收用新批次，须事前明确是否供本处方使用。 |
| 06 | `SC06-BILL-A`、`SC06-REFUND-A`、`SC06-CLOSE-A` | SC03-EXEC-C 患者与 TRT-002 原 RUN 的已确认未出账费用、唯一账单、同一收款人之收款与退款、完整门店日期渠道日结范围 | A：FIN-001→FIN-002 全额收款余额零→FIN-003 申请、不同审批人审批、模拟实退→FIN-004 日结；申请、批准、实退各是独立事实。 |
| 06 | `SC06-BILL-B` | 另一个独立合成患者、不同 confirmed 未出账费用和账单 | FIN-001 在新来源上另行执行一次，读回未付余额后只读查看欠款；不能将 A 的零余额描述为欠款。缺独立来源则该支线 BLOCKED。 |
| 08 | `SC08-FUP-A`、`SC08-REF-A` | 独立的可选治疗事件与独立跨店转诊接诊，目标合成门店和唯一可识别目标条目 | FUP-001 和 FUP-002 是不同支线；无时段转诊目标接收即记到店，源位置释放后只报到既有任务，不重复到店。 |
| 08 | `SC08-VENDOR-A`、`SC08-LAB-A` | 合成供应商/资质合作、同公司同供应商已确认采购行、独立治疗来源及责任人 | LAB-001→LAB-002；工单自动关联 waiting 复诊，入库后核 ready，不对同一来源再执行 FUP-001 新建。 |
| 09 | `SC09-DOC-A`；报表引用 `SC06-BILL-A` | SC03-EXEC-C 的 TRT-001 C 已确认文书及原 RUN、无前版原件、适用模板/PDF；已提交 A 收款来源 | DOC-001 生成原件→DOC-002 请求 PDF；RPT-001/002 只读或导出已有来源，不重做收款。 |
| 10 | `SC10-ACCESS-A`、`SC10-QUEUE-A` | 无历史责任的专用账号、两店及受限业务入口；专用新任务已合法报到且未叫号 | ACC-003 当前业务入口 ENTRY_UNKNOWN，不得先撤权；QUE-001 仅执行步骤 1–4 取得 calling，暂停步骤 5 前再执行 QUE-002；不使用已经 serving 的任务或重叫。超时及库存不足另需专门安全对象，未准备则 BLOCKED。 |

## 1.1 新增支线对象

以下仍是逻辑占位，不代表已创建数据库对象。以执行清单对应行的角色、前置及停止条件为准；除明确写明接续原RUN者，各对象不得与其他已提交业务来源混用。

| 用例 | 逻辑对象 | 来源与状态 |
|---|---|---|
| [UAT-ACC-004](../30-functions/rework-access-patient/cases/UAT-ACC-004.md) | `X-ACC-004-A` | 独立账号和患者，旧页已打开，权限满足用例；撤权读回，旧页写入被拒。 |
| [UAT-ACC-005](../30-functions/rework-access-patient/cases/UAT-ACC-005.md) | `X-ACC-005-A` | 合法可见的已有合成人员事件；看到限定范围摘要或记录无法定位。 |
| [UAT-PAT-002](../30-functions/rework-access-patient/cases/UAT-PAT-002.md) | `X-PAT-002-S / X-PAT-002-T` | 两份无冲突独立合成身份及目标内部ID；申请及集团确认后合并追溯。 |
| [UAT-PAT-003](../30-functions/rework-access-patient/cases/UAT-PAT-003.md) | `SC02-PAT-A / X-PAT-003-CONTACT` | PAT-001既有未验证联系人原RUN；可见验证记录及虚构依据。 |
| [UAT-INT-004](../30-functions/rework-access-patient/cases/UAT-INT-004.md) | `X-INT-004-PAT / X-INT-004-TASK` | 新患者、当日合法供给、服务区域映射及营业日；资格、到店及报到分别读回。 |
| [UAT-EXM-003](../30-functions/rework-clinical-finance/cases/UAT-EXM-003.md) | `X-EXM-003-EXEC / X-EXM-003-ORDER` | 独立医疗serving段、原工位连接及未执行检查行；检查结束后原医疗接诊及工位仍持有。 |
| [UAT-EXM-004](../30-functions/rework-clinical-finance/cases/UAT-EXM-004.md) | `X-EXM-004-EXEC / X-EXM-004-ORDER` | 独立已报到并serving的检查段和未执行行；确认实际执行并记录部分完成。 |
| [UAT-FIN-005](../30-functions/rework-clinical-finance/cases/UAT-FIN-005.md) | `X-FIN-005-BILL` | 独立未付清账单，四渠道锁状态及金额精度满足用例；原余额减去免单且仍为正。 |
| [UAT-FIN-006](../30-functions/rework-clinical-finance/cases/UAT-FIN-006.md) | `X-FIN-006-COLLECTION` | 独立未更正收款，原/目标渠道及账户合法；原收款与金额保留；更正由合法来源核实。 |
| [UAT-FIN-007](../30-functions/rework-clinical-finance/cases/UAT-FIN-007.md) | `SC06-CLOSE-A` | FIN-004已确认最新周期原RUN及完整快照；日结解锁且原三项汇总保留。 |
| [UAT-FUP-003](../30-functions/rework-lab-evidence/cases/UAT-FUP-003.md) | `X-FUP-003-EXEC / X-FUP-003-TASK` | 独立源接诊及目标门店可售时段，目标当日无到店；目标有时段资格与任务；无新增到店。 |
| [UAT-LAB-003](../30-functions/rework-lab-evidence/cases/UAT-LAB-003.md) | `X-LAB-003-ORDER` | LAB-002独立原RUN、工单available且未戴用；原单返工退回并生成草稿子单。 |
| [UAT-LAB-004](../30-functions/rework-lab-evidence/cases/UAT-LAB-004.md) | `X-LAB-004-ORDER / X-LAB-004-EVENT` | 独立工单已入库，另有入库后不同接诊的戴用事件；采购成本来源与戴用出库可读回。 |
| [UAT-EVD-001](../30-functions/rework-lab-evidence/cases/UAT-EVD-001.md) | `X-EVD-001-SET` | 提供可审阅证据索引；不足则DATA_NOT_READY；逐项记录证据范围及UNKNOWN。 |

## 私有交接时应记录

负责人逐项提供环境标识、固定产品版本、门店、实际可见对象编号、初始状态、责任岗位、已准备的持久动作与其结果、可执行/阻断状态和分配时间。若准备动作已经创建某来源，其后用户只查看或接续；要测试“新建”须分配另一个尚未创建的对象。时段、营业日和租约会过期，暂停后先重新确认，不能仅凭旧清单继续提交。
