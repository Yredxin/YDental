# 已知限制与历史状态

本手册状态待最终审查；环境 **ENVIRONMENT_NOT_READY**，全部用户结果初始 NOT_RUN。以下是范围和历史事实，不是用户结果。

| 项目 | 状态与影响 |
|---|---|
| P14-V2 | PARTIAL；T09 FAIL。真实 WebKit 320×800、根字号200%、JS-off 的焦点轮廓超出视口；不得写成已修复。见[历史报告](https://github.com/Yredxin/YDental/blob/0df9d14275e1bb4bed971afc684ee513914b7081/docs/reports/s13-dl-p14-v2/summary.md)。 |
| P12 A04 和旧 P14/T09 | 历史 FAIL/PARTIAL 保留；P14先前两版均未满足 T09，既有失败不被新候选覆盖。见 [P12](https://github.com/Yredxin/YDental/blob/0df9d14275e1bb4bed971afc684ee513914b7081/docs/reports/s13-dl-p12/summary.md) 与 [P14](https://github.com/Yredxin/YDental/blob/0df9d14275e1bb4bed971afc684ee513914b7081/docs/reports/s13-dl-p14/summary.md)。 |
| R3 | 整体 PARTIAL；R3-BUG-001 是限定 FIXED_VERIFIED，仅所测接续、完成、防重及文书责任范围。其他 UNKNOWN、E2E-BUG-002 OPEN 保留。[R3](https://github.com/Yredxin/YDental/blob/0df9d14275e1bb4bed971afc684ee513914b7081/docs/reports/s13-e2e-r3/summary.md) |
| 用户效果 | #37 OPEN；技术证据或本手册源码审查不是用户 PASS。 |
| 入口缺口 | ACC-003 撤权旧页业务入口未固定，ENTRY_UNKNOWN/BLOCKED；RPT-002 审计合法读回入口未固定，审计部分 BLOCKED。 |
| 覆盖缺口 | 集团服务新增、现场登记完整步骤、患者合并/验证、同工位内检查、部分跨店/超时、免单/账单更正/渠道重分类/财务解锁/跨法人、有时段转诊、外加工戴用返工及完整采购成本等未在当前步骤全面覆盖；见[追溯](requirements-trace.md)。 |
| L4 | 50会话、持续备份恢复、断网及真实并发等不能通过阅读页面宣称通过；需对应固定版本和环境的专项证据。 |
| 政策和外部能力 | 正式临床/财务政策、税票、支付、签署、真实通知或供应商门户、真实患者资金、真实设备、生产部署未获本工作包授权。PDF或打印请求不证明纸张输出。 |
| 保护与未知 | 既有已提交费用、库存、退款、日结、原件、文书、审计和账号责任不重放或覆盖；旧 Session 和历史缺失前像等 UNKNOWN 不补 PASS。 |

缺失入口或需要特殊环境的用例必须保持阻断直到负责人提供真实证据与安全前置；不以计划目标或代码存在代替实际部署。
