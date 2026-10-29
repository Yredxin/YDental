# 1.1 手册修订与独立复核记录

状态 **HANDBOOK_PARTIAL**：本记录是文档制作和限定 SOURCE 复核事实，不是用户验收。环境准备及最终审查以 [环境就绪报告](environment-readiness.md) 和主控最终交付记录为准；最终远端 HEAD 在交付记录固定，不在提交内容中自嵌自身哈希。用户结果均为 NOT_RUN。

## 基线和分工

产品固定 `12f3f299b07ab324f7279413a928097b7ce858a8`，文档起点 `0df9d14275e1bb4bed971afc684ee513914b7081`，新分支 `codex/yd-uat-r1-handbook-v11`。W0 `w0_inventory_v11` 盘点，`review_w0_v11` 独立核对；W1 `author_route_v11` 编写，`review_route_v11` 独立复核；W2 `author_records_v11` 编写，`review_records_v11` 独立复核。审查者与作者均在共享工作区，不代表操作系统隔离；这些结论均限定 SOURCE 或文档，不是动态通过。

W3 A/B `author_gaps_ab_v11` / `review_gaps_ab_v11`：5 个新增用例及索引逐文件限定通过。C/D `author_gaps_cd_v11` / `review_gaps_cd_v11`：5 个新增用例及索引逐文件限定通过。E/F `author_gaps_ef_v11` / `review_gaps_ef_v11`：4 个新增用例及索引逐文件限定通过。W4 集成 `integration_v11`，由 `review_integration_v11` 独立复核并反馈修正；其结论限于已核文档和 SOURCE。W5 环境由 `environment_discovery` 准备、`environment_review` 独立核验身份、模块、部分岗位授权、对象和停止状态。W6 `final_review_v11` 已完成限定 SOURCE 与文档首审，环境停止及重新启动 NOT_RUN 的文字问题已修。ZIP 校验及冻结后独立复核仍待实际完成，不由本记录预签。

共 49 个用例：原 35 个 ID 保留；新增 14 个为 ACC-004/005、PAT-002/003、INT-004、EXM-003/004、FIN-005/006/007、FUP-003、LAB-003/004、EVD-001。业务依赖、入口和对象依 [唯一执行清单](execution-checklist.md) 与 [对象映射](scenario-data-map.md)，独立来源不得重放；逻辑编号不是数据库 ID。新增支线均为 DATA_NOT_READY，须按实际环境核对。病例保存与确认分支、外检先报到后执行、账单全付和欠款不同来源及日结责任在 W1 独立核对过。

## 保留缺口与历史状态

详见 [修订缺口](rework-gap-register.md)、[需求追溯](requirements-trace.md)及 [已知限制](known-limitations.md)。旧 ACC-003 入口仍未知，新增 ACC-004 是限定患者旧页负例；完整审计导出、自动身份验证、不同医生及历史超时接续、账单例外、跨法人和正式外部政策未完整覆盖。L4 六专项以 EVD-001 审阅已有证据，缺本次实证的部分保持 UNKNOWN，用户不做系统管理。

历史 P14-V2 PARTIAL/T09 FAIL、P12 A04 与旧 P14/T09 FAIL、R3 整体 PARTIAL、R3-BUG-001 限定 FIXED_VERIFIED、E2E-BUG-002 OPEN、Session 和历史前像 UNKNOWN 均保留。#37 OPEN。用户界面感受、生产部署、真实患者及资金、正式临床财务政策和外部通道未由本材料批准。

## 便携及环境

源码链接使用固定候选，历史报告使用已有固定提交；内部链接用于独立解压。ZIP 的完整性、内部链接、文件 SHA 与独立复核待实际完成，包的 CRC、解压校验和 SHA 将作为单独交付结果，不自嵌入包内内容。W4 `review_integration_v11` 和 W6 `final_review_v11` 的限定源码与文档首审已检查 107 份 Markdown、49 个用例、1289 条内部链接（缺失 0）及 77 个固定 Git 目标；这是静态审查，不等于用户验收。W6 对最终 ZIP 的独立复核仍待完成。

W5 限定结果为 **ENV_PREPARED_STOPPED（仅部分前置） / ENVIRONMENT_NOT_READY / USER_ACCESS_UNVERIFIED**：新隔离数据库已安装固定候选并有合成门店和部分基础对象；十个普通岗位账号由准备者验证本机网页登录，其成员及部分授权经独立连接核读。店长 POLICY_PENDING，库存与完整财务配置和多个业务前置未准备。医生测试供给截止 UTC 2026-10-29 10:53，用户开始前须重新核对时效与合法供给。用户终端访问未证，L1 与 L2/L3 均不准出；L4 按证据逐项审阅，不以历史结果外推。Odoo 已请求停止、监听及相关 PID 不存在，但进程退出码 UNKNOWN；数据库容器停止 exit 0，旧 Session 失效 UNKNOWN。详细实证范围、账号和对象状态见 [环境就绪报告](environment-readiness.md)，不能据此声称全部业务或用户验收已通过。

用户需使用私有副本、按 RUN 分开保存截图和记录；所有提交结果未知立即停止，不为复现重复已提交来源。
