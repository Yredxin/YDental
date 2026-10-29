# 1.1 治疗检查与结算补充

所有新增用户用例默认 NOT_RUN；环境仍以真实环境准备报告为准。使用独立合成对象，每个持久来源只能提交一次。

- [UAT-EXM-003 同工位检查](cases/UAT-EXM-003.md)
- [UAT-EXM-004 部分完成检查](cases/UAT-EXM-004.md)
- [UAT-FIN-005 有据免单](cases/UAT-FIN-005.md)
- [UAT-FIN-006 收款渠道更正](cases/UAT-FIN-006.md)
- [UAT-FIN-007 财务解锁日结](cases/UAT-FIN-007.md)

以下不冒充可执行：不同医生接续文书已有 [UAT-TRT-003](../clinical-exam/cases/UAT-TRT-003.md) 中合法负责人转派与接手，但旧接诊超时后的现场接续专门操作仍 ENTRY_UNKNOWN；不得伪造超时或重试。多账单收款、账单更正例外及跨店权限的独立来源与可见核验尚未固定，DATA_NOT_READY；跨法人正式交易政策 POLICY_PENDING。既有 [FIN-001](../settlement/cases/UAT-FIN-001.md) 与 [FIN-002](../settlement/cases/UAT-FIN-002.md) 不证明这些新分支已完成。跨店摘要入口存在，但当前用户可重复且可安全观察的独立负例数据未准备。所有代码发现仅 SOURCE，不是用户通过或动态证据。
