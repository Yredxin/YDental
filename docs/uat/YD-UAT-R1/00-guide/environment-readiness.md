# UAT 环境状态：用户反馈更正与既有停机记录（2026-10-31）

## 2026-10-31 03:25 UTC｜Windows 登录页反馈

用户在重新启动后明确反馈 **“看到 Odoo 登录页”**；Windows 浏览器成功打开该页可推得本次 TCP 通路可达，但没有单独的 `Test-NetConnection` 测试结果。此前用户反馈无法访问及其更正均保留在下方；本次前台账号登录、当前门店和患者列表仍待用户实际反馈，不能据此标记 PASS 或 `UAT_L1_READY`。49 个完整用例保持 **NOT_RUN**。

状态检查显示 scratch 运行、登记的 Odoo 进程监听 `192.168.1.128:18776`；HTTP **不提供传输加密**。此为该时点状态，完成本次用户验证后须实际停止并独立核验；旧的停止记录不代表当前已停机。


## 2026-10-31 03:23 UTC｜重新启动时的历史状态

用户更正无法访问后，指定 UAT 实例已重新受控启动。状态检查显示 scratch 运行、登记 Odoo 进程监听 `192.168.1.128:18776`；独立 Reviewer 核实唯一指定 LAN 监听及 Ubuntu 本机登录页 HTTP 200。用户此前反馈无法访问；重新启动后的 Windows 访问仍待复测，用户登录、当前门店和患者列表仍待实际验证，`UAT_L1_READY` 尚未满足。此为该时点状态，最终停机与后像须实际执行和核验后再记录。


## 用户反馈更正与既有停机记录

此前记录曾记为“稍后测试”，又记有“登录、当前门店和患者列表均正常”的反馈；用户随后明确更正：**“不对，我没法访问，是不是服务没启动？”** 因此不把此前反馈作为成功证据：Windows TCP、登录、当前门店和患者列表均未获有效成功验证；重启后用户确认登录页可见，可推得该次 TCP 通路可达；没有单独的 `Test-NetConnection` 结果。49 个完整用例仍为 NOT_RUN，未代填 RUN/PASS。

本次只读后独立比较 117 张受检表，仅审计 **503→509**、会话 **129→130** 变化，其余 115 张摘要一致，不能外推全库。负责人正常 `stop` / `status` 均 exit 0；独立核实指定数据库容器 `exited` / exit 0 / `network none`，原 Odoo PID 不存在、端口无监听。Odoo 退出码和 Session 失效仍为 **UNKNOWN**。此前服务已受控停止；用户更正后于 03:23 UTC 已重新受控启动，实时状态以[本次用户会话](l1-user-session-current.md)及负责人现场核验为准。用户账号登录、当前门店和患者列表尚无有效成功验证，`UAT_L1_READY` 当前不成立。49 个完整用例均保持 **NOT_RUN**。

用户接受 Odoo 原生禁用页面；数据库管理 POST 未动态测试。HTTP 不提供传输加密，两项技术 POST 由测试器本地预拦，不是产品拒绝。本次结果不代表完整前端或 L2/L3 已验收。

[本次用户会话及后续操作](l1-user-session-current.md)。以下为较早时点历史记录。

---

# UAT 环境状态：启动时历史记录（2026-10-31 03:12 UTC；最新状态见顶部）

指定合成 UAT 实例已受控启动；本机状态检查显示 scratch 数据库运行，登记的 Odoo 进程监听 `192.168.1.128:18776`。Ubuntu 本机普通前台登录及患者页面 GET 已检查；这不代表 Windows 可达。用户已接受 Odoo `list_db=false` 的原生禁用页面表现，管理 POST 未动态测试，HTTP 不提供传输加密。

Windows TCP、用户登录、明确的当前合成门店和页面反馈均 **NOT_RUN / USER_ACCESS_UNVERIFIED**；已提供私有账号清单链接，但是否收到、打开及登录尚未确认。49 个完整用例用户结果仍为 **NOT_RUN**，不能签署 `UAT_L1_READY`。实时状态、用户操作和后续停机记录见[本次用户会话](l1-user-session-current.md)；后续停止后更新本段，不将此时点当作永久运行承诺。

---

# L1 只读环境接续状态（2026-10-29 历史记录；本次状态见顶部）

**L1_ENV_PREPARED_STOPPED（本机限定） / USER_ACCESS_UNVERIFIED**。本轮在已准备的独立合成 scratch 上两次受控启动和停止，并进行本机岗位登录与页面读取；当前服务和数据库已停止，用户现在不能登录。用户设备可达、私下凭据交付均未核，**不满足 UAT_L1_READY**。原 49 个用例用户结果仍为 NOT_RUN，不因页面读取成功改成 PASS。

固定产品 `12f3f299b07ab324f7279413a928097b7ce858a8`；两次新只读连接核实目标数据库身份。两轮本机浏览器均记录 10 个普通岗位及管理员登录成功、选择唯一授权合成门店返回 303；只有一个合成门店，跨店切换未验证。有限 GET 的最终路径和部分全页可见文字已核；页面含门店名称可能仅来自门店选择器，不能证明当前选店或 Current store，用户须另行核对；医生与外加工的无接诊参数临床入口实际返回 422。库存和结算页面的空态正则命中不证明特定正文或账单内容；具体可执行子步骤及限制见[首次体验](l1-first-session.md)。浏览器自动拦截器每轮阻止 6 个技术 POST，这些是客户端预拦截，不是产品拒绝；完整资产及交互不能据此视为通过。未发治疗、发药、财务、文书确认等业务 POST。

独立只读新连接对每轮 117 张受检表取前后逐行摘要：两轮累计审计 309→401、会话 74→96，其余 115 张摘要一致；这是受检范围，不代表全库无变化。正常登录、切店及读取带来的审计和会话增量保留。两次 `ops.py start`、`stop` 和 `status` 均报告退出码 0；独立核实指定数据库容器 `exited`、退出码 0、network none，目标监听消失。Odoo 进程退出码 UNKNOWN，Session 失效未测，停止不证明 Session 失效。

L2/L3 仍需库存、会计、检查工位、合法供给时效和独立来源等条件；店长政策为 POLICY_PENDING。历史 P14-V2 T09 FAIL、P12 A04 及旧 P14/T09 FAIL、R3 整体 PARTIAL 与历史 UNKNOWN 不因本轮改写，#37 OPEN。详细证据层级与命令见[L1 准出复核](l1-readiness-review.md)，访问和启动须由环境负责人按[说明](l1-access-and-startup.md)处理。

---

# UAT 环境准备与逐用例状态（1.1 交付时历史状态，2026-10-29；本轮增量见顶部）

状态：**ENV_PREPARED_STOPPED（仅已准备的部分前置） / ENVIRONMENT_NOT_READY / USER_ACCESS_UNVERIFIED**。本报告记录准备事实，不是用户验收；所有用户结果仍为 NOT_RUN。专用Odoo已正常请求停止，监听消失，非子进程退出码 UNKNOWN；新数据库容器正常停止、退出码0并保留数据。独立Reviewer只读确认两个本轮Odoo PID不存在、两个端口无监听，容器身份匹配且退出码0。旧Session失效未验证。登录地址、账号及凭据通过私有途径提供，不写入本公开文件。

产品安装候选 `12f3f299b07ab324f7279413a928097b7ce858a8`，Odoo 20.0，核心 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。新独立 PostgreSQL 18 集群与库经现场身份核对；数据库容器网络 none、Unix socket；Odoo 绑定本机回环，cron关闭，SMTP不可达，并使用进程级连接限制。进程级限制不证明操作系统级隔离或用户设备可访问。独立Reviewer以新只读数据库连接核身份、已安装模块、岗位成员和授权，以及部分准备对象；操作作者的实际登录与独立数据库读回属于不同证据层级。

管理员和十个普通岗位账号通过本机真实网页分别登录；普通账号按岗位分配部分能力，不具有统一超级管理员身份。前台、医生、检查、药房、仓库、收费、审批、复诊、加工及报表账号的门店成员状态和非none授权已由独立连接读回；账号登录依据作者的浏览器回执，用户端访问及逐功能权限仍待核。测试密码仅本机私有provider保存。店长身份需要同时发布明确批准的安全/任命策略；本包未获得该正式政策，**POLICY_PENDING**，不得以集团管理员冒充店长。

新库有供环境准备使用的合成门店、基础空间和工位、隔离测试供给策略、合成目录映射与演示价格、三名无真实联系方式的合成患者；上述来源已由独立新连接读取。示例医生排班与供给仅适用 **2026-10-29 16:43–18:53 Asia/Shanghai（UTC 08:43–10:53）**，受当前日期和时间限制。用户开始时须由环境负责人重新核查实际时段、营业日、合法供给及对象分配；过期后不能把旧时段当成可用，也不能重放既有业务来源。独立只读连接核查的到店、任务、capacity claim、queue execution、治疗event/fee、库存event及原生stock_move、账务move/payment、结算payment/receipt/refund均为0；不将此范围扩大为全库所有经济对象均为0。queue scope和outbox各1（版本1）实际存在，不能称全部队列记录为零。未为准备提前完成用户的治疗、发药、账单、收退款或日结。库存、完整会计配置及多个跨岗位前置尚未准备；原生第二仓库涉及全局库存组设置，当前未修改权限规则。

## 岗位准备状态

以下登录指本机真实浏览器登录；任何一项都不代表用户终端可访问或该岗位的所有用例已就绪。资格、工位和对象须按用例复核。

| 岗位 | 状态与限制 |
| --- | --- |
| 环境管理员／集团管理 | 本机登录已验；有集团和技术配置组及部分环境准备能力，不等于全部业务授权。 |
| 店长 | POLICY_PENDING：没有任命，不能以集团管理员冒称。 |
| 前台 | 本机登录已验，frontdesk/patient write已授予；实际步骤和对象仍须核。 |
| 医生 | 本机登录已验，medical write与基础能力已授予；排班供给限所列时间，接诊尚未创建。 |
| 检查 | 本机登录已验，exam write已授予；检查工位和资格 DATA_NOT_READY。 |
| 药房 | 本机登录已验，pharmacy write已授予；工位、库存和处方 DATA_NOT_READY。 |
| 仓库 | 本机登录已验，warehouse write已授予；新门店仓库和批次 DATA_NOT_READY。 |
| 收费 | 本机登录已验，settlement write已授予；会计和账单前置 DATA_NOT_READY。 |
| 财务审批 | 本机登录已验，settlement read及finance_approval write已授予；需独立申请人和审批来源。 |
| 复诊联络 | 本机登录已验，followup write及medical read已授予；来源及责任 DATA_NOT_READY。 |
| 外加工 | 本机登录已验，medical/followup write已授予；采购、供应商、库存和适用资格 DATA_NOT_READY。 |
| 报表 | 本机登录已验，settlement read/export write已授予；仅对应已授予的来源，报表数据 DATA_NOT_READY。 |

## 层级启动状态

- L1：当前不能向用户宣布可开始；本机登录有实证，但用户端访问未核实，最终服务默认停止。
- L2/L3：DATA_NOT_READY；岗位资格、时间有效性、源对象、仓库和财务等须按各例检查。
- L4：专项证据逐项准备与审阅；历史技术结果不代替用户验收。

以下为环境准备状态，不是结果。`READY` 须在用户开始时核实时前置均成立后才可使用；所有未核条件均保持未就绪。不同的测试轮次和业务对象必须独立登记。

| 用例 | 环境状态 | 尚需核实或准备 |
| --- | --- | --- |
| [UAT-ACC-001](../30-functions/access/cases/UAT-ACC-001.md) | DATA_NOT_READY | 需核对独立合成对象、具体入口及该用例全部前置。 |
| [UAT-ACC-002](../30-functions/access/cases/UAT-ACC-002.md) | DATA_NOT_READY | 需核对独立合成对象、具体入口及该用例全部前置。 |
| [UAT-ACC-003](../30-functions/access/cases/UAT-ACC-003.md) | ENTRY_UNKNOWN | 旧页撤权负例的具体业务入口仍待固定。 |
| [UAT-EXM-001](../30-functions/clinical-exam/cases/UAT-EXM-001.md) | DATA_NOT_READY | 检查/治疗工位资格、接诊及相应独立来源尚未准备。 |
| [UAT-EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md) | DATA_NOT_READY | 检查/治疗工位资格、接诊及相应独立来源尚未准备。 |
| [UAT-TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md) | DATA_NOT_READY | 检查/治疗工位资格、接诊及相应独立来源尚未准备。 |
| [UAT-TRT-002](../30-functions/clinical-exam/cases/UAT-TRT-002.md) | DATA_NOT_READY | 检查/治疗工位资格、接诊及相应独立来源尚未准备。 |
| [UAT-TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md) | DATA_NOT_READY | 检查/治疗工位资格、接诊及相应独立来源尚未准备。 |
| [UAT-DOC-001](../30-functions/documents-reporting/cases/UAT-DOC-001.md) | DATA_NOT_READY | 需核对独立合成对象、具体入口及该用例全部前置。 |
| [UAT-DOC-002](../30-functions/documents-reporting/cases/UAT-DOC-002.md) | DATA_NOT_READY | 需核对独立合成对象、具体入口及该用例全部前置。 |
| [UAT-RPT-001](../30-functions/documents-reporting/cases/UAT-RPT-001.md) | DATA_NOT_READY | 需核对独立合成对象、具体入口及该用例全部前置。 |
| [UAT-RPT-002](../30-functions/documents-reporting/cases/UAT-RPT-002.md) | BLOCKED | 来源导出及审计部分需分别核入口、权限和证据。 |
| [UAT-FUP-001](../30-functions/followup-lab/cases/UAT-FUP-001.md) | DATA_NOT_READY | 任务来源、转诊/加工条件、采购协作及负责人须逐项准备。 |
| [UAT-FUP-002](../30-functions/followup-lab/cases/UAT-FUP-002.md) | DATA_NOT_READY | 任务来源、转诊/加工条件、采购协作及负责人须逐项准备。 |
| [UAT-LAB-001](../30-functions/followup-lab/cases/UAT-LAB-001.md) | DATA_NOT_READY | 任务来源、转诊/加工条件、采购协作及负责人须逐项准备。 |
| [UAT-LAB-002](../30-functions/followup-lab/cases/UAT-LAB-002.md) | DATA_NOT_READY | 任务来源、转诊/加工条件、采购协作及负责人须逐项准备。 |
| [UAT-INT-001](../30-functions/intake-queue/cases/UAT-INT-001.md) | DATA_NOT_READY | 有时效的供给与用户实际开始时间须重新核验；相关任务尚未创建。 |
| [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md) | DATA_NOT_READY | 有时效的供给与用户实际开始时间须重新核验；相关任务尚未创建。 |
| [UAT-INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md) | DATA_NOT_READY | 有时效的供给与用户实际开始时间须重新核验；相关任务尚未创建。 |
| [UAT-PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md) | DATA_NOT_READY | 已建立基础合成患者；本例专属身份与关系数据尚未分配核实。 |
| [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md) | DATA_NOT_READY | 有时效的供给与用户实际开始时间须重新核验；相关任务尚未创建。 |
| [UAT-QUE-002](../30-functions/intake-queue/cases/UAT-QUE-002.md) | DATA_NOT_READY | 有时效的供给与用户实际开始时间须重新核验；相关任务尚未创建。 |
| [UAT-INV-001](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md) | DATA_NOT_READY | 仓库、批次、实际库存和处方等前置尚未准备。 |
| [UAT-INV-002](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md) | DATA_NOT_READY | 仓库、批次、实际库存和处方等前置尚未准备。 |
| [UAT-PHA-001](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) | DATA_NOT_READY | 仓库、批次、实际库存和处方等前置尚未准备。 |
| [UAT-PHA-002](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | DATA_NOT_READY | 仓库、批次、实际库存和处方等前置尚未准备。 |
| [UAT-ACC-004](../30-functions/rework-access-patient/cases/UAT-ACC-004.md) | DATA_NOT_READY | 需核对独立合成对象、具体入口及该用例全部前置。 |
| [UAT-ACC-005](../30-functions/rework-access-patient/cases/UAT-ACC-005.md) | DATA_NOT_READY | 源码可见人员页面审计入口；合规读回范围与导出仍需逐项核实。 |
| [UAT-INT-004](../30-functions/rework-access-patient/cases/UAT-INT-004.md) | DATA_NOT_READY | 有时效的供给与用户实际开始时间须重新核验；相关任务尚未创建。 |
| [UAT-PAT-002](../30-functions/rework-access-patient/cases/UAT-PAT-002.md) | DATA_NOT_READY | 已建立基础合成患者；本例专属身份与关系数据尚未分配核实。 |
| [UAT-PAT-003](../30-functions/rework-access-patient/cases/UAT-PAT-003.md) | DATA_NOT_READY | 已建立基础合成患者；本例专属身份与关系数据尚未分配核实。 |
| [UAT-EXM-003](../30-functions/rework-clinical-finance/cases/UAT-EXM-003.md) | DATA_NOT_READY | 检查/治疗工位资格、接诊及相应独立来源尚未准备。 |
| [UAT-EXM-004](../30-functions/rework-clinical-finance/cases/UAT-EXM-004.md) | DATA_NOT_READY | 检查/治疗工位资格、接诊及相应独立来源尚未准备。 |
| [UAT-FIN-005](../30-functions/rework-clinical-finance/cases/UAT-FIN-005.md) | DATA_NOT_READY | 模拟会计配置和可用的独立费用/账单来源未准备。 |
| [UAT-FIN-006](../30-functions/rework-clinical-finance/cases/UAT-FIN-006.md) | DATA_NOT_READY | 模拟会计配置和可用的独立费用/账单来源未准备。 |
| [UAT-FIN-007](../30-functions/rework-clinical-finance/cases/UAT-FIN-007.md) | DATA_NOT_READY | 模拟会计配置和可用的独立费用/账单来源未准备。 |
| [UAT-EVD-001](../30-functions/rework-lab-evidence/cases/UAT-EVD-001.md) | DATA_NOT_READY | 专项证据需逐项提供并审阅；不要求用户运行系统管理操作。 |
| [UAT-FUP-003](../30-functions/rework-lab-evidence/cases/UAT-FUP-003.md) | DATA_NOT_READY | 任务来源、转诊/加工条件、采购协作及负责人须逐项准备。 |
| [UAT-LAB-003](../30-functions/rework-lab-evidence/cases/UAT-LAB-003.md) | DATA_NOT_READY | 任务来源、转诊/加工条件、采购协作及负责人须逐项准备。 |
| [UAT-LAB-004](../30-functions/rework-lab-evidence/cases/UAT-LAB-004.md) | DATA_NOT_READY | 任务来源、转诊/加工条件、采购协作及负责人须逐项准备。 |
| [UAT-FIN-001](../30-functions/settlement/cases/UAT-FIN-001.md) | DATA_NOT_READY | 模拟会计配置和可用的独立费用/账单来源未准备。 |
| [UAT-FIN-002](../30-functions/settlement/cases/UAT-FIN-002.md) | DATA_NOT_READY | 模拟会计配置和可用的独立费用/账单来源未准备。 |
| [UAT-FIN-003](../30-functions/settlement/cases/UAT-FIN-003.md) | DATA_NOT_READY | 模拟会计配置和可用的独立费用/账单来源未准备。 |
| [UAT-FIN-004](../30-functions/settlement/cases/UAT-FIN-004.md) | DATA_NOT_READY | 模拟会计配置和可用的独立费用/账单来源未准备。 |
| [UAT-SCH-001](../30-functions/space-scheduling/cases/UAT-SCH-001.md) | DATA_NOT_READY | 基础空间已准备；本例专属对象和用户岗位授权须逐项核定。 |
| [UAT-SCH-002](../30-functions/space-scheduling/cases/UAT-SCH-002.md) | DATA_NOT_READY | 基础空间已准备；本例专属对象和用户岗位授权须逐项核定。 |
| [UAT-SCH-003](../30-functions/space-scheduling/cases/UAT-SCH-003.md) | DATA_NOT_READY | 基础空间已准备；本例专属对象和用户岗位授权须逐项核定。 |
| [UAT-SPC-001](../30-functions/space-scheduling/cases/UAT-SPC-001.md) | DATA_NOT_READY | 基础空间已准备；本例专属对象和用户岗位授权须逐项核定。 |
| [UAT-SPC-002](../30-functions/space-scheduling/cases/UAT-SPC-002.md) | DATA_NOT_READY | 基础空间已准备；本例专属对象和用户岗位授权须逐项核定。 |

## 结束和重新启动

由环境负责人使用本机私有操作记录，在启动前核产品与核心HEAD、库名/OID/集群、当前有效测试范围、服务监听、凭据及外联状态；检查业务对象、未完成责任和磁盘余量。本机私有操作记录提供受控状态、启动、停止说明及真实身份核对；本轮实际停止已由独立Reviewer核实；后续修订的受控工具仅状态检查已实测，新版停止和重新启动均未实测（NOT_RUN）。按实际状态先检查再启动，避免重复启动或重放。准备结束后按进程身份正常停止Odoo及该scratch数据库，保留对象和账户，不以停止服务证明Session失效。停止后重新启动和用户端连接须另作实际核实；不得自行变更OS防火墙、认证或共享代理。
