# E2E-W6 阶段记录

计划：YD-S13-E2E-R1 / 1.1。状态：**PARTIAL；仅完成不依赖预约资格的限定负例**。本记录由全新 C-W6 维护；未实测的场景不记 PASS。

## 承接与边界

- 产品候选 `181c8619fe11e97fddc710991a97f84d804fe2a4`，活动分支 `codex/s13-e2e-r1`；目标为现场核实的隔离合成库，W6 每个账号使用新浏览器 Context 与正常 Odoo 登录表单，不继承先前 Session。
- [W1](w1-record.md) 为 PARTIAL，[W2](w2-record.md) 为 BLOCKED。两名独立合成患者的真实预约均返回 409，B 复核未创建资格或扣容量。现有 demo 策略不可售与计划内真实预约路径存在需求歧义；仅隔离测试店发布策略的用户决定仍待回复。本阶段不得以测试替身、伪造批准或正式业务政策绕过此边界。
- A／B 测试店 ID 541／542，跨店账号 UID 1550 在 A 有 medical write、B 有 medical read；无业务权限账号 UID 1551。W1 的权限配置和菜单访问不代替本阶段服务端负例。
- 患者 1644／1645 无到店；患者 1646 已有独立到店 1438，均不得盲目重放。药品批次 278 的合成接收 event／move 754 已提交，药房 +10、来源 -10，禁止重放；历史经济、库存、文书、附件、审计及未完成责任继续保护。
- W1 的 panorama 页面 `PlaywrightError` 与排班原 `Error` 首因均 UNKNOWN；W1 升级时结算 NULL 约束警告、历史技术元数据变化与客户端拦截已按原证据保留，不能由本阶段回填历史通过。

## 场景状态

| 场景 | 初始状态 | 证据要求及限制 |
|---|---|---|
| A／B 门店权限差异和当前门店 | PARTIAL | UID 1550 真实切 A／B、两治疗页 200，A 显示写标识、B 缺写标识；授权与 session 独立读回。尚未取得 B 店实际服务端写拒绝。 |
| 旧页面切店和撤权后的服务端拒绝 | PARTIAL | 旧 A 页切 B 后实际服务端 409；前台撤权后同一 session 的下一 GET 和原有效患者创建表单 POST 均真实 403，其他岗位／动作未验。 |
| 无业务权限及无资质人员入口／动作 | NOT_RUN | 必须是适用真实前置与服务端拒绝；客户端或测试工具拦截不能冒产品拒绝。 |
| 合法历史读取与跨店写分离 | NOT_RUN | 仅在已有合法合成对象与读取目的可验证时执行；若依赖未生成的医疗历史则记 BLOCKED。 |
| 发起退款不得自批 | BLOCKED | 需要 W5 合法测试账务与退款申请；不得伪造或重放经济状态。 |
| 患者双执行、过号、故障撤呼、人工追加及取消返额 | BLOCKED | 依赖合法资格、队列或执行状态；不直接改数据库制造条件。 |
| 待办、文书、库存核对、未知事务、复诊与加工、断网 | NOT_RUN | 仅选择已有合法前置且不依赖受阻链的场景；其余逐项记 BLOCKED 或 NOT_RUN。 |

## 发现、复核与缺陷

| 来源 | 身份、前置及实际观察 | B 独立复核／归因 | 主控裁定与后续 |
|---|---|---|---|
| W6-CROSS-01 | UID 1550 正常表单登录，同一真实 Context 切 A／B；两治疗页均 HTTP 200，A `data-write=1`、B 无该属性，均无 execution。两项测试客户端请求拦截另列。 | B 新 RO/RR 核 active 会员：A medical write／B medical read；session 3975 从 A 切 B，revision 2，accepted audit 77431–77434；其他目标连接 0，进程／端口已停。 | 页面呈现和授权读回成立；实际 B 店服务端写拒绝与医疗执行均未验，不冒 PASS。 |
| W6-OLD-SCOPE-01 | UID 1541 正常登录、在旧 A 店人员授权页填写 UID 1550 的 medical:none；同 Context 切 B 后提交旧页，服务端返回 HTTP 409／`version_conflict`。两项客户端拦截另列。 | B 独核 session 3976 当前为 B／revision 2，UID 1550 的 A medical write／B medical read 均未变；accepted audit 77435–77438 及 denied audit 77439 存在，资源已停。 | 旧页面切店后的 scope 拒绝成立；不代替跨店医疗写或撤权测试。 |
| W6-REVOKE-01 | UID 1543 在独立 Context 打开 A 店 intake 为 200；UID 1541 在另一 Context 通过正常 UI 将该账号 A 店 frontdesk write 改为 none。原 UID 1543／session 3977 重新加载旧页，服务端返回 403；随后 UID 1541 通过 UI 恢复 write。四项测试客户端拦截另列。 | B 在撤权后独立只读确认 none／audit 77496；拒绝后确认 session 仍属 A，患者 1646 与 arrival 1438 无副作用；末次独核 member 2529 已恢复 write／audit 77497。未观察到单独 denial 审计。 | 撤权对下一 GET 生效且授权已恢复；旧表单 POST 和其他岗位撤权尚未验。 |
| W6-REVOKE-POST-01 | UID 1543／A 的旧患者创建表单在撤权前真实有效，CSRF、revision 和 key 存在；UID 1541 正常 UI 撤 frontdesk write 后，前台同 session 点击旧表单，服务端返回 403／`access_denied`；管理员正常 UI 恢复 write。四项测试客户端拦截另列。 | B 撤权中间核 session 3979 仍在 A、grant none／audit 77536；拒绝后核唯一新合成目标患者、号码和 create operation 均为 0，原 patient 1646／arrival 1438 保持；恢复后核 grant write／audit 77537。未观察到单独 denial 审计，资源停止。 | 该患者创建路径的撤权后旧 POST 拒绝及恢复成立；其他岗位、其他动作未验。 |

- B 现场只读前置 `.local/s13-e2e-r1/b-w6/preflight.json` SHA-256 `4cafa44f4c8e06ea5bdae1ec3389ddb8681f8514b14f491e98bca940bad546ed`：UID 1550 的两店会员共 employee 1506，UID 1543 在 A 有 frontdesk write，UID 1541 两店有 personnel write；患者 1646 与 A 店到店 1438 的归属已核，事务回滚并关闭。首次只读查询误用到店表名导致 PostgreSQL `42P01`／退出 1，finally 回滚并关闭，没有 DB 写；更正后退出 0，原失败保留。
- W6-CROSS-01 独立回执 `.local/s13-e2e-r1/w6/step-20261027T105350-ca0871eb798f/independent.json` SHA-256 `9475858fc8ba9f4dae9dda24aa59edf466760f7dc0272950740181781080d160`。C 已核对两份文件 SHA；浏览器事实来自 A、数据库读回与进程核查来自 B。
- W6-OLD-SCOPE-01 独立回执 `.local/s13-e2e-r1/w6/step-20261027T105500-b5a897be082c/independent.json` SHA-256 `0e4910201f42d71421e76ea5ca5a4fcf97d6c855af12e50b5ce5f242bd88d32b`；C 已核对 SHA，实际浏览器结果来自 A、数据库及停机核查来自 B。
- W6-REVOKE-01 的撤权中间读回 `.local/s13-e2e-r1/w6/step-20261027T105654-f86d963164c3/revoked-independent.json` SHA-256 `c3fa3bfa3b31dd514ba034bb2b15d9c8b06963d4a134491dc54f03044ecdf055`，拒绝后的中间读回 `denied-independent.json` SHA-256 `adde4f1e3e38affb0481afb96e0cf3a472a788b219e5e6e50672a596864cd6ca`，最终读回 `independent.json` SHA-256 `abee1393309b7ffbff0a10be08a386c8c69b2b39a03528999710fa4b73946081`；C 已逐份核对 SHA。实际浏览器操作来自 A、三次数据库读回来自 B。
- W6-REVOKE-POST-01 的撤权中间读回 `.local/s13-e2e-r1/w6/step-20261027T110021-ba295910fc7a/revoked-independent.json` SHA-256 `e5c1351a8425bc3b83fd21f98f28e1ef5c31c823ac980e3b690b910cd323182b`，拒绝后 `denied-independent.json` SHA-256 `4f1cb8f73bbe58f95d2db7538dc554cd6a1bb2fe89e7a4e0be875dd7dd35e7f8`，最终 `independent.json` SHA-256 `8fbcb4ebee69ae2df771d0d8aed92928943f1841f13ee95daad5f6f313801525`；C 已核对三份 SHA。前述 GET 场景中的“旧 POST 未验”为历史时点。

所有 A 原始发现保留 `OBSERVED`，B 独立复测后分类为产品、操作、数据、环境、需求歧义或 UNKNOWN；无法复现不自动认定 A 错误或产品通过。需要时主控定向重新验收。仅经独立确认及必要裁定的真实产品问题进入正式 BUG 清单；原始失败与实际工具退出记录不得删除。

## 交接与证据

记录产品及实际测试工具版本、账号 UID／门店、操作前状态、真实步骤、HTTP／RPC／浏览器和独立已提交读回层级、资源停止与历史保护。不得输出密码、Cookie、Session 或认证材料。测试账号暂保留供后续计划使用；最终结束时按计划停用登录并保留身份与审计。

本记录初稿依据用户计划、活动 `CURRENT_TASK.md`、W1／W2 阶段报告及本地 `git rev-parse HEAD`；C-W6 尚未登录、启动服务、连接数据库、执行业务或发送 GitHub 评论。实际结果以 A／B 证据及主控裁定为准。

## W6 当前阶段交接

主控裁定 **PARTIAL**：跨店页面与权限呈现、旧页面切店 409、前台撤权后 GET 403 和已有效旧患者创建表单 POST 403 及权限恢复分别有实际证据；跨店医疗写、无资质实际医疗执行、自批退款、队列和其他依赖预约或资金的场景仍未执行。W2 容量策略决定待用户回复，不借上述负例宣称 W6 或完整 E2E 通过。

- A 摘要 `.local/s13-e2e-r1/w6/a-w6-summary.md` SHA-256 `1c3ca63b15b6db44e93ea045226906d81fa4246e31280d6a7274ef1ea4a24217`；B 终验 `.local/s13-e2e-r1/b-w6/w6-final-independent.json` SHA-256 `8d705b55adb2842d3514e1285020a4e63d1b8e415c2c8b136784b7eb52d86cfd`。C 已核两份文件 SHA；实际操作与独立查询分别来自 A、B。
- 11 账号仍 active 供后续验收；前台 1543／A 的 frontdesk write 已恢复，跨店 1550 的 A medical write／B medical read 保持。患者 1646 的 arrival 1438、药品 event 754 及批次 278 来源 -10／药房 +10 保持，耗材批次 279 无 quant。测试 URL 已恢复至 18411，freeze 未设置；不得重复已提交业务。
- 145 表逐行保护快照 `.local/s13-e2e-r1/b-w6/protection-w6final.json` SHA-256 `fee7f320284554eb1e4236b9c22a6ee6c97ffcf05fd2de37699cb15985a83ee5`；与 W2 对比 `.local/s13-e2e-r1/b-w6/w6-final-protection-comparison.json` SHA-256 `a8167f72d03c13d7661154a9730548c6cdfd701db07d6ce5880e3cb998f73cde`。B 报告无旧行删除；新增 110 条正常审计，grant 5014 的写入元数据与四个 mutex 各 revision +4 分列；13 技术表、七附加保护区和 83 引用／80 文件一致。C 已核两文件 SHA，不能把正常增量写作全库零变化。
- 五次自有服务均 exit 0、配置移除且服务进程组消失；四次主要浏览器组独核消失。URL 恢复阶段的浏览器 PID 未采，关闭仅有 A 报告，不能冒独立证明；18511 端口无监听、目标库无其他连接。既有原始失败、UNKNOWN 和客户端拦截继续保留。
