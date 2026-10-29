# YDental UAT 1.1｜包外交付与审查记录

**HANDBOOK_PARTIAL**；环境为 **ENV_PREPARED_STOPPED（仅部分前置） / ENVIRONMENT_NOT_READY / USER_ACCESS_UNVERIFIED**。本记录是技术与文档交付事实，不是用户验收结论。所有用户结果初始为 `NOT_RUN`；#37 保持 OPEN。

## 固定基线与交付物

- 产品候选：`12f3f299b07ab324f7279413a928097b7ce858a8`；原手册文档基线：`0df9d14275e1bb4bed971afc684ee513914b7081`；本次文档分支：`codex/yd-uat-r1-handbook-v11`。
- 用户手册：[总入口](YD-UAT-R1/README.md)、[1.1 修订报告](YD-UAT-R1/00-guide/handbook-v11-review.md)、[环境就绪报告](YD-UAT-R1/00-guide/environment-readiness.md)。
- [用户版 ZIP](YD-UAT-R1.1-user-handbook.zip)：302287 字节，SHA256 `05e070b6af38d487b4e69bbbfe3d2ad6e3bb247dd8d5ce77aad9788dad4bf047`。该值为包外校验值，ZIP 内容不自嵌自身哈希。
- 最终文档提交的 HEAD 及远端读回由交付消息登记；Git 提交不能在自身内容中嵌入自身哈希。

## 用例与职责

原 35 个用例 ID 保留并加入可重复 RUN 和问题记录；新增 14 个 ID：`UAT-ACC-004`、`UAT-ACC-005`、`UAT-PAT-002`、`UAT-PAT-003`、`UAT-INT-004`、`UAT-EXM-003`、`UAT-EXM-004`、`UAT-FIN-005`、`UAT-FIN-006`、`UAT-FIN-007`、`UAT-FUP-003`、`UAT-LAB-003`、`UAT-LAB-004`、`UAT-EVD-001`。保存与确认、检查任务接续和独立账单来源等原用例或路线已修订；具体依赖与未覆盖事项见[唯一执行清单](YD-UAT-R1/00-guide/execution-checklist.md)、[对象映射](YD-UAT-R1/00-guide/scenario-data-map.md)及[缺口登记](YD-UAT-R1/00-guide/rework-gap-register.md)。

| 阶段 | 作者或执行者 | 独立 Reviewer | 限定结论 |
|---|---|---|---|
| W0 盘点 | `w0_inventory_v11` | `review_w0_v11` | 原 35 ID 的所有权及风险盘点经 SOURCE/文档复核。 |
| W1 路线 | `author_route_v11` | `review_route_v11` | 场景、接续及停止条件经限定 SOURCE/文档复核。 |
| W2 记录 | `author_records_v11` | `review_records_v11` | 原 35 例及记录模板经限定文档复核。 |
| W3 A/B | `author_gaps_ab_v11` | `review_gaps_ab_v11` | 5 个新增用例及索引经限定 SOURCE/文档复核。 |
| W3 C/D | `author_gaps_cd_v11` | `review_gaps_cd_v11` | 5 个新增用例及索引经限定 SOURCE/文档复核。 |
| W3 E/F | `author_gaps_ef_v11` | `review_gaps_ef_v11` | 4 个新增用例及索引经限定 SOURCE/文档复核。 |
| W4 集成 | `integration_v11` | `review_integration_v11` | 链接、导航及说明经限定 SOURCE/文档复核；修订按审查意见复核。 |
| W5 环境 | `environment_discovery` | `environment_review` | 独立只读核实指定新环境身份、模块、部分授权和对象及停止状态；未证明用户端访问或全部业务前置。 |
| W6 总验收 | 主控整合及 ZIP 准备 | `final_review_v11` | 限定源码、文档及 ZIP 检查，结果如下；不代替真实业务或用户验收。 |

作者与 Reviewer 共享项目主机和工作区，角色分工不代表操作系统隔离。报告的 SOURCE 与文档结果不冒称浏览器、真实并发、业务提交或用户 PASS。

## ZIP 与静态检查

独立审查对冻结用户树与 ZIP 进行了限定检查：156 个成员的 ZIP CRC 完整；临时解压后逐文件 SHA256 与用户树一致。包内 107 份 Markdown、49 个用例和 49 个截图目录；1292 条内部链接缺失 0；Windows 路径检查通过。源码及报告引用使用固定 Git 目标，固定目标核查和常见秘密强模式检查均为限定静态检查，不证明所有潜在敏感数据绝对不存在。限定检查未发现实际账号密码、Session 或真实患者数据，包内没有截图；用户未来结果及截图应保存在私有副本。

## 环境、层级与收尾

新独立合成环境已安装固定候选并部分准备，现已停止；十个普通岗位账号保持 active，店长任命依赖的正式策略未批准，标记 `POLICY_PENDING`。医生供给截止 **2026-10-29 10:53 UTC**，未来开始时须重新核对时效与合法供给；库存、完整财务配置、部分工位资格及独立来源仍缺。用户访问未核实，L1、L2、L3 均不准出；L4 仅供审阅已有专项证据，未取得或不覆盖当前环境的内容保持缺口与 UNKNOWN。

数据库容器实际停止 exit 0；Odoo 已请求停止、进程与监听消失，但退出码 UNKNOWN；Session 失效 UNKNOWN。新版受控重启与停止流程尚未实测，均为 NOT_RUN；历史停止事实不能代替新版流程测试。环境、角色、权限和各用例状态的实际范围详见[环境就绪报告](YD-UAT-R1/00-guide/environment-readiness.md)。不据此声称用户此刻可登录。

用户开始前，环境负责人须核固定版本与身份、合法登录和用户端可达性、按岗位门店授予与资格、有效日期的排班供给及营业日、完整合成库存与模拟会计配置、各用例专用来源和一次性提交边界，并私下交付账号和对象映射；缺失项目保持 BLOCKED 或 DATA_NOT_READY。提交结果不明先停并核状态，不为复现重放历史或已提交来源。

## 历史及限制

P14-V2 PARTIAL/T09 FAIL、P12 A04 及旧 P14/T09 失败、R3 整体 PARTIAL、R3-BUG-001 仅限定 FIXED_VERIFIED、E2E-BUG-002 OPEN、旧 Session 与历史前像 UNKNOWN 保留。完整审计导出、自动身份验证、部分超时接续、账单例外与跨法人以及正式外部政策等缺口未因制作手册关闭。[需求追溯](YD-UAT-R1/00-guide/requirements-trace.md)逐项列出范围与限制。

本工作包未开始用户实际验收，未启用真实患者、资金、支付、通知、税务或签署通道；未合并产品、生产部署、关闭 #37 或启动 P15。
