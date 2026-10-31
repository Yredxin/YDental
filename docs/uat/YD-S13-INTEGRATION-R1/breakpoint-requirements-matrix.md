# S13 集成断点与需求映射｜初稿

状态：W0 初稿。基于 2026-10-31 本地产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`、现有 UAT 文档和 #23 当前正文；运行实例、当前配置及本包最终候选尚未核定。历史证据的环境与适用范围见原报告，不能视为本包结果。

本表是排查队列：对应关系表示需求或拟验覆盖，不代表入口可达、前置齐备、实施完成或验收通过。本包独立预验收均 **NOT_RUN**，原 49 项 HUMAN 结果均 **NOT_RUN**；具体场景、对象、入口和证据待逐项核定。不能因旧只读工作包表述误禁本包获授权的新合成业务。

## 主链和支线断点

| 岗位与动作 | 前置、上游 → 下游 | 当前已知问题或未知 | 归属与验证 |
|---|---|---|---|
| 各岗位从牙科首页找工作 | 有效内部身份、门店成员与类别能力 → 对应业务工作台 | 当前候选 `/ydental` 为欢迎页和 PDF 样张；无岗位工作台 | W1 首页与权限；各岗位真实浏览器核合法入口、上下文和空态 |
| 人员授权 / 空间 / 排班 | 合法员工及授权 → 工位能力 → 实际业务日供给 | 原环境仅部分准备；日期、资质和隔离测试 scope 须重新核；不沿用过期供给 | W0/W2 配置与产品；普通角色实操及独立读取 |
| 前台患者、预约、到店、报到 | 门店关系、服务和合法供给 → 资格、到店、任务 | 有效供给及独立对象未确认；首页至跨对象上下文未验 | W1/W2 导航与受理；浏览器、容量及持久记录 |
| 医生工位、叫号、接诊和文书 | 合格医生、工位和任务 → 接诊、文书、执行与费库 | 无参数临床入口历史返回 422；正常业务入口及本候选完整链尚未验 | W1/W2 临床上下文；草稿、执行、确认、结束分别验证 |
| 前台、医生和检查 | 合法医嘱、工位与能力 → 外检任务、部分结果、直返或重分配 | 检查工位和资质未核；两条后继路径未在最终候选完整验 | W2/W3；浏览器与独立持久读回 |
| 医生、前台、药房、仓库 | 处方 → 待报到、叫号、4+2 发药 → 来源、余量、批次和费用 | 仓库批次、库存及合法工位未确认；BUG-002 对升级和并发的影响未消除 | W2/W3；新来源实际发药、缺货恢复及退药独立读回 |
| 收费与审批 | 实际来源费、会计及付款配置 → 账单、收款、审批与实退 | 模拟会计配置和独立费用来源未确认；历史可访问性失败保留 | W2/W3；普通岗位 740、分款、退款与跨账单核销 |
| 复诊、外加工、文书、报表 | 合法来源、角色、供方/成本及原件配置 → 后续待办和可追溯报表 | 测试来源、角色和入口未逐项确认；不启用真实通知或签署 | W3；跨岗浏览器、来源与原件持久核对 |
| 各岗位撤权、切店、响应未知 | 有权独立账号、两个会话与新对象 → 服务端实际拒绝或已提交结果 | 当前候选本环境的旧页、撤权与直接地址负例未验 | W3/W4；服务端响应及独立新连接读回 |

## R01—R26 需求映射

用例关联按原 49 个用例头部显式标注提取，属于现有手册的追溯线索，不保证覆盖该需求全文；未直接标注不表示无适用测试。需求原文以 #23 当前正文及有效增量为准。

| 需求 | 当前要求摘要 | 原用例线索 | 本包状态与下一步 |
|---|---|---|---|
| R01 | S00-T01—T09；各阶段安装升级/字典/翻译 | [UAT-EVD-001](../YD-UAT-R1/30-functions/rework-lab-evidence/cases/UAT-EVD-001.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R02 | S01-T05/T06；S03-T13 | [UAT-ACC-001](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-001.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R03 | S01-T01/T02/T08/T09/T10 | [UAT-ACC-001](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-001.md)、[UAT-ACC-002](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-002.md)、[UAT-ACC-003](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-003.md)、[UAT-ACC-004](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-ACC-004.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R04 | S01-T07/T11/T12/T13；S04-T05/T06；S08-T09/T16；S12-T06 | [UAT-ACC-002](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-002.md)、[UAT-ACC-003](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-003.md)、[UAT-RPT-002](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-RPT-002.md)、[UAT-PAT-001](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-PAT-001.md)、[UAT-ACC-004](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-ACC-004.md)、[UAT-ACC-005](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-ACC-005.md)、[UAT-PAT-002](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-PAT-002.md)、[UAT-PAT-003](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-PAT-003.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R05 | S01-T03/T04；S03-T12；S06-T01/T05/T14 | [UAT-ACC-001](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-001.md)、[UAT-ACC-002](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-002.md)、[UAT-ACC-003](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-003.md)、[UAT-QUE-001](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-QUE-001.md)、[UAT-ACC-004](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-ACC-004.md)、[UAT-SPC-001](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SPC-001.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R06 | S02-T01—T10；S03-T11/T12/T13 | [UAT-SCH-001](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SCH-001.md)、[UAT-SCH-002](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SCH-002.md)、[UAT-SPC-001](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SPC-001.md)、[UAT-SPC-002](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SPC-002.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R07 | S03-T01/T02/T04/T06/T14 | [UAT-SCH-001](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SCH-001.md)、[UAT-SCH-002](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SCH-002.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R08 | S05-T01/T11；S06-T02；S08-T14；E01 | [UAT-FUP-001](../YD-UAT-R1/30-functions/followup-lab/cases/UAT-FUP-001.md)、[UAT-INT-002](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-INT-002.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R09 | S03-T03/T07/T10；S05-T02/T06/T12 | [UAT-INT-002](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-INT-002.md)、[UAT-INT-004](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-INT-004.md)、[UAT-SCH-002](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SCH-002.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R10 | S05-T03/T04/T08/T12；S06-T03/T21；S09-T01 | [UAT-INT-002](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-INT-002.md)、[UAT-INT-003](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-INT-003.md)、[UAT-QUE-001](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-QUE-001.md)、[UAT-INT-004](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-INT-004.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R11 | S06-T04/T05/T09 | [UAT-INT-003](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-INT-003.md)、[UAT-QUE-001](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-QUE-001.md)、[UAT-QUE-002](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-QUE-002.md)、[UAT-INT-004](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-INT-004.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R12 | S06-T01/T05/T17/T18/T19；S08-T02 | [UAT-TRT-001](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-001.md)、[UAT-QUE-001](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-QUE-001.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R13 | S06-T06/T07；S09-T03/T07 | [UAT-EXM-001](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-EXM-001.md)、[UAT-EXM-002](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-EXM-002.md)、[UAT-EXM-003](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-EXM-003.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R14 | S06-T08/T16；S08-T05/T06/T14；S09-T04/T12 | [UAT-EXM-002](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-EXM-002.md)、[UAT-TRT-003](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-003.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R15 | S05-T05；S06-T09/T10/T11 | [UAT-QUE-002](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-QUE-002.md)、[UAT-INT-004](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-INT-004.md)、[UAT-SCH-003](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SCH-003.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R16 | S06-T12/T20；S09-T08；S11-T11；S13-T14 | [UAT-QUE-002](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-QUE-002.md)、[UAT-SCH-003](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SCH-003.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R17 | S08-T01/T03/T06/T10/T15/T16；S12-T03 | [UAT-TRT-001](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-001.md)、[UAT-TRT-003](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-003.md)、[UAT-DOC-001](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-DOC-001.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R18 | S08-T07；S09-T02/T04/T05/T06/T13 | [UAT-EXM-001](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-EXM-001.md)、[UAT-EXM-002](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-EXM-002.md)、[UAT-TRT-001](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-001.md)、[UAT-TRT-002](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-002.md)、[UAT-PHA-001](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-PHA-001.md)、[UAT-EXM-003](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-EXM-003.md)、[UAT-EXM-004](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-EXM-004.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R19 | S07-T01—T09；S08-T04 | [UAT-TRT-002](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-002.md)、[UAT-INV-001](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-INV-001.md)、[UAT-INV-002](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R20 | S08-T08/T13；S07-T05；S10-T08 | [UAT-INV-002](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-INV-002.md)、[UAT-PHA-001](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-PHA-001.md)、[UAT-PHA-002](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R21 | S05-T10/T13；S10-T01—T16；S12-T11 | [UAT-TRT-002](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-002.md)、[UAT-RPT-001](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-RPT-001.md)、[UAT-INT-001](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-INT-001.md)、[UAT-PHA-002](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-PHA-002.md)、[UAT-FIN-005](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-FIN-005.md)、[UAT-FIN-006](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-FIN-006.md)、[UAT-FIN-007](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-FIN-007.md)、[UAT-FIN-001](../YD-UAT-R1/30-functions/settlement/cases/UAT-FIN-001.md)、[UAT-FIN-002](../YD-UAT-R1/30-functions/settlement/cases/UAT-FIN-002.md)、[UAT-FIN-003](../YD-UAT-R1/30-functions/settlement/cases/UAT-FIN-003.md)、[UAT-FIN-004](../YD-UAT-R1/30-functions/settlement/cases/UAT-FIN-004.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R22 | S04-T01—T10；S12-T12 | [UAT-PAT-001](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-PAT-001.md)、[UAT-PAT-002](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-PAT-002.md)、[UAT-PAT-003](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-PAT-003.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R23 | S11-T01—T18 | [UAT-FUP-001](../YD-UAT-R1/30-functions/followup-lab/cases/UAT-FUP-001.md)、[UAT-FUP-002](../YD-UAT-R1/30-functions/followup-lab/cases/UAT-FUP-002.md)、[UAT-LAB-001](../YD-UAT-R1/30-functions/followup-lab/cases/UAT-LAB-001.md)、[UAT-LAB-002](../YD-UAT-R1/30-functions/followup-lab/cases/UAT-LAB-002.md)、[UAT-FUP-003](../YD-UAT-R1/30-functions/rework-lab-evidence/cases/UAT-FUP-003.md)、[UAT-LAB-003](../YD-UAT-R1/30-functions/rework-lab-evidence/cases/UAT-LAB-003.md)、[UAT-LAB-004](../YD-UAT-R1/30-functions/rework-lab-evidence/cases/UAT-LAB-004.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R24 | S08-T11；S09-T10；S10-T11；S12-T01—T12 | [UAT-EXM-001](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-EXM-001.md)、[UAT-DOC-001](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-DOC-001.md)、[UAT-DOC-002](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-DOC-002.md)、[UAT-RPT-002](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-RPT-002.md)、[UAT-FIN-005](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-FIN-005.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R25 | S06-T13；S12-T09；S13-T05/T10 | [UAT-RPT-001](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-RPT-001.md)、[UAT-RPT-002](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-RPT-002.md)、[UAT-ACC-005](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-ACC-005.md)、[UAT-EVD-001](../YD-UAT-R1/30-functions/rework-lab-evidence/cases/UAT-EVD-001.md) | 本包 NOT_RUN；核入口、前置、角色及最终候选证据 |
| R26 | S13-T08/T09/T15 | [UAT-EVD-001](../YD-UAT-R1/30-functions/rework-lab-evidence/cases/UAT-EVD-001.md) | 独立 50 会话、备份恢复等后续专项；本包不冒充完成 |

## 原 49 用户用例映射

每个链接保留原 ID、完整步骤、既有真实权限与前置。下表岗位和需求是原文首部线索；入口、测试对象及环境前置须由主控按本包独立确定并补记。所有行本包独立预验收与 HUMAN 均 NOT_RUN，不能以源码、页面 200 或历史候选结果代填。

| 原用例 / 场景 | 原参与岗位 | 需求线索 | 入口、对象和前置 / 结果 |
|---|---|---|---|
| [UAT-ACC-001｜门店和员工准备](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-001.md) | 具备相应授权的集团管理者或店长／人员授权者 | R02、R03、R05 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-ACC-002｜单项权限和模板预览](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-002.md) | 集团管理者、获准店长或人员授权者 | R03、R04、R05 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-ACC-003｜切店、撤权与旧页](../YD-UAT-R1/30-functions/access/cases/UAT-ACC-003.md) | 两个分别登录的合成人员：有权人员授权者及受测业务人员。 | R03、R04、R05 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-EXM-001｜检查实际执行及独立结果](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-EXM-001.md) | 检查医生（本例仅覆盖外部检查工位） | R13、R18、R24 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-EXM-002｜检查医嘱、保留原工位与返回](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-EXM-002.md) | 治疗医生、前台、检查医生 | R13、R14、R18 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-TRT-001｜医疗文书：编辑、保存与文字确认](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-001.md) | 治疗医生 | R12、R17、R18 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-TRT-002｜实际治疗项目及费库来源](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-002.md) | 治疗医生 | R18、R19、R21 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-TRT-003｜保存后交还、正常完成和待完善责任](../YD-UAT-R1/30-functions/clinical-exam/cases/UAT-TRT-003.md) | 治疗医生、具备授权的文书负责人或店长 | R14、R17 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-DOC-001｜预览并保存合成文书原件](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-DOC-001.md) | 治疗医生或被授权的文书使用者 | R17、R24 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-DOC-002｜请求打印已保存的合成原件](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-DOC-002.md) | 有来源读取权限的文书使用者 | R24 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-RPT-001｜按授权范围查询经营报表并回源](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-RPT-001.md) | 经营报表使用者、收费员 | R21、R25 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-RPT-002｜导出合成报表并审阅审计边界](../YD-UAT-R1/30-functions/documents-reporting/cases/UAT-RPT-002.md) | 经营报表使用者、授权导出人员 | R04、R24、R25 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-FUP-001｜创建复诊计划与记录模拟联络](../YD-UAT-R1/30-functions/followup-lab/cases/UAT-FUP-001.md) | 复诊联络 | R08、R23 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-FUP-002｜医生发起无时段跨店转诊并由目标门店接收](../YD-UAT-R1/30-functions/followup-lab/cases/UAT-FUP-002.md) | 治疗医生、目标门店前台 | R23 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-LAB-001｜查看供应商资质与门店合作](../YD-UAT-R1/30-functions/followup-lab/cases/UAT-LAB-001.md) | 集团管理、仓库负责人 | R23 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-LAB-002｜合成外加工工单、回货与入库](../YD-UAT-R1/30-functions/followup-lab/cases/UAT-LAB-002.md) | 治疗医生、仓库负责人、复诊联络 | R23 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-INT-001｜服务目录、门店映射及演示价版本](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-INT-001.md) | 集团主数据维护者、门店价目维护者 | R21 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-INT-002｜预约或现场登记资格](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-INT-002.md) | 前台 | R08、R09、R10 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-INT-003｜实际到店与任务报到](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-INT-003.md) | 前台 | R10、R11 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-PAT-001｜合成患者档案与门店关系](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-PAT-001.md) | 前台／患者资料维护者 | R04、R22 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-QUE-001｜工位进入、叫号与开始执行](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-QUE-001.md) | 治疗医生／检查医生／药房人员 | R05、R10、R11、R12 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-QUE-002｜过号与连接异常观察](../YD-UAT-R1/30-functions/intake-queue/cases/UAT-QUE-002.md) | 工位人员、前台 | R11、R15、R16 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-INV-001｜门店仓库、批次与入库](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-INV-001.md) | 仓库、环境负责人 | R19 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-INV-002｜库存来源与隔离退回](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | 仓库 | R19、R20 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-PHA-001｜医生开立并冻结合成处方](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) | 治疗医生、前台 | R18、R20 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-PHA-002｜药房报到与分次模拟发药](../YD-UAT-R1/30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 前台、药房 | R20、R21 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-ACC-004｜撤销写权限后使用旧患者编辑页](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-ACC-004.md) | 授权管理者、独立合成受限账号。 | R03、R04、R05 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-ACC-005｜查看有权范围内审计摘要](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-ACC-005.md) | 门店人员权限读取者或集团管理者。 | R04、R25 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-INT-004｜现场登记并分别记录到店与报到](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-INT-004.md) | 前台，后续队列工位人员。 | R09、R10、R11、R15 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-PAT-002｜两份合成身份的集团核验合并](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-PAT-002.md) | 门店患者管理人员与集团身份核验人员。 | R04、R22 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-PAT-003｜记录合成联系人验证依据](../YD-UAT-R1/30-functions/rework-access-patient/cases/UAT-PAT-003.md) | 患者资料维护者。 | R04、R22 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-EXM-003｜同工位检查与医疗继续](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-EXM-003.md) | 岗位见原用例 | R13、R18 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-EXM-004｜合成检查部分完成](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-EXM-004.md) | 岗位见原用例 | R18 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-FIN-005｜有据免单冲减未收应收](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-FIN-005.md) | 岗位见原用例 | R21、R24 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-FIN-006｜线下收款渠道更正](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-FIN-006.md) | 岗位见原用例 | R21 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-FIN-007｜财务解锁合成日结](../YD-UAT-R1/30-functions/rework-clinical-finance/cases/UAT-FIN-007.md) | 岗位见原用例 | R21 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-EVD-001｜专项技术证据审阅](../YD-UAT-R1/30-functions/rework-lab-evidence/cases/UAT-EVD-001.md) | 岗位见原用例 | R01、R25、R26 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-FUP-003｜医生发起有时段跨店转诊](../YD-UAT-R1/30-functions/rework-lab-evidence/cases/UAT-FUP-003.md) | 岗位见原用例 | R23 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-LAB-003｜已入库合成工单的免费返工](../YD-UAT-R1/30-functions/rework-lab-evidence/cases/UAT-LAB-003.md) | 岗位见原用例 | R23 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-LAB-004｜独立合成工单的戴用完成及成本来源查看](../YD-UAT-R1/30-functions/rework-lab-evidence/cases/UAT-LAB-004.md) | 岗位见原用例 | R23 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-FIN-001｜确认费用并生成账单](../YD-UAT-R1/30-functions/settlement/cases/UAT-FIN-001.md) | 收费员 | R21 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-FIN-002｜模拟线下收款并核销](../YD-UAT-R1/30-functions/settlement/cases/UAT-FIN-002.md) | 收费员 | R21 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-FIN-003｜模拟退款申请、独立审批及退款登记](../YD-UAT-R1/30-functions/settlement/cases/UAT-FIN-003.md) | 收费员、不同账号的财务审批人 | R21 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-FIN-004｜收费员合成日结](../YD-UAT-R1/30-functions/settlement/cases/UAT-FIN-004.md) | 收费员、必要时财务审批人 | R21 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-SCH-001｜员工排班与我的今日](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SCH-001.md) | 排班人员、被安排员工 | R06、R07 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-SCH-002｜工位容量及资格覆盖](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SCH-002.md) | 容量配置人员、合成测试员工 | R06、R07、R09 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-SCH-003｜报到区域营业日开接和停接](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SCH-003.md) | 容量配置人员、前台观察人员 | R15、R16 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-SPC-001｜楼层、区域和工位](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SPC-001.md) | 门店空间配置人员 | R05、R06 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |
| [UAT-SPC-002｜公共与门店空间资源](../YD-UAT-R1/30-functions/space-scheduling/cases/UAT-SPC-002.md) | 集团资源管理员、门店空间配置人员 | R06 | 原用例给出拟验入口与前置；本包实况、独立新对象及证据待核；NOT_RUN |

## 历史问题及证据边界

- **E2E-BUG-002 OPEN**：历史受控 `ydental_supply` 升级级联 inventory 后 mutex revision 13→0；10 项技术摘要缺少升级前逐行值，原因不能完整归因，也不以 SQL 恢复旧值。修复原提交 `411d6e6` 非当前产品祖先，但等效修复 `c483464` 已纳入候选，inventory XML 为 `noupdate=1` 且不显式重置 revision；历史仅隔离 scratch MODEL，真实目标再升级与真实并发未验。新库须以非零 revision 实测升级及独立真实并发；新库通过不关闭历史目标升级缺口。见 [历史登记](../../reports/s13-e2e-r1/w2-test-policy-record.md) 和 [最终报告](../../reports/s13-e2e-r1/w7-final-report.md)。
- **R3-BUG-001 定向 FIXED_VERIFIED，R3 整体 PARTIAL**：`f9c4778` 是候选祖先，其后 clinical/treatment 目录无差异；限定真实浏览器接续接诊、正常完成、防重及文书责任已有独立读回。原治疗和后续完成分别位于 interrupted 段与接续段，不能合称同一执行段；完成响应部分字段 UNKNOWN，权限负例不能外推。最终集成候选须以全新来源完成闭环。见 [缺陷登记](../../reports/s13-e2e-r3/bug-register.md) 和 [定向验证](../../reports/s13-e2e-r3/bug001-browser-verification.md)。
- **P14-V2 T09 FAIL**：WebKit、320×800 CSS px、根字号 200%、真正 JS-off，免单金额/原因焦点轮廓底部 803.59375px 超出视口 800px；不因本包工作抹除。见 [总结](../../reports/s13-dl-p14-v2/summary.md)。
- **P12 A04 FAIL/PARTIAL**：真正 JS-off 的原要求焦点可见场景仍失败，且旧 Native 139、Firefox 字形、WebKit 退出和 UNKNOWN 按原报告保留。见 [P12 总结](../../reports/s13-dl-p12/summary.md)。
- R1/R2/R3 整体 PARTIAL 与历史已提交治疗、库存、经济业务、原件、待完善责任及未知状态继续保护；未经独立确认不重放、不覆盖、不补 PASS。
