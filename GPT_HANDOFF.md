# YDental / odoo-sd｜GPT 交接

2026-10-18 · YD-N1 R1 · YD-COLLAB-V2.0 / WORKFLOW-V3

## 1. 你的职责与协作方式

你负责与用户沟通完整需求、业务方向和验收标准，制定下一份给 Codex 的完整 plan，并在 plan 结束后审查最终结果、安排后续方向。

用户把 plan 交给 Codex 后，直接与 Codex 沟通“继续”、技术问题和实施调整。Codex 主控负责多 agent 调度、实现、测试、普通修复及独立验收；plan 内不逐批返回 GPT，不等待中途 GPT 评论。意外、需求或重大方向需要决策时，用户才提前回来。

plan 结束时，Codex 提交一份最终结果，由用户交给 GPT。当前 plan 之外的下一份计划不由 Codex 擅自扩展。

## 2. 接管入口

仓库：[Yredxin/YDental](https://github.com/Yredxin/YDental)。先读默认分支 [AGENTS.md](https://github.com/Yredxin/YDental/blob/main/AGENTS.md) 和 [CURRENT_TASK.md](https://github.com/Yredxin/YDental/blob/main/CURRENT_TASK.md)，再跟随路由读活动分支同名状态，核对 HEAD、[#23 总计划](https://github.com/Yredxin/YDental/issues/23)、当前阶段正文和有效增量。

当前阶段为 [S10 / #34](https://github.com/Yredxin/YDental/issues/34)，活动分支为 `codex/s10-settlement-finance-r1-20261013`。分支和执行事实以接管时仓库为准，不从文档 main 重开业务开发。

最新协作决定：[完整 plan 闭环](https://github.com/Yredxin/YDental/issues/23#issuecomment-6246356260)。当前旧 Codex 任务：[收尾及 AGENTS.md 调整](https://github.com/Yredxin/YDental/issues/34#issuecomment-6246363733)。

GitHub Projects 仅为可选展示；字段、视图、GraphQL 权限和同步状态不构成开工或验收前置。Issue、仓库需求、用户交付的 plan 与 CURRENT_TASK.md 继续承载需求和实施记录，普通同步失败不得冒称成功。

## 3. 新 GPT 的第一项工作

核对旧 Codex 的收尾回执：AGENTS.md 是否已移除 Projects 硬依赖并同步，CURRENT_TASK.md 是否保存最新事实，旧主控及子任务是否已停止或交接。收尾指令已发布不等于执行完成；没有回执就列明尚缺，不重发同一任务，也不假称旧团队已结束。

核对后直接给出供新 Codex 持续实施的完整 plan，优先围绕 S10 剩余功能和真实验收收口；未完成的所有权交接列为实际实施前置，不用另一轮泛化规划代替 plan。复用已有 `docs/execution/S10_REMAINING_CLOSEOUT.md` 中仍有效的需求和验收内容，不重写项目需求或照搬旧审批流程。

接管时需核实的存量：S02—S09 已按技术完成关闭，最终用户效果归 #37；S10 尚未技术完成。B 离线 revision1/2 已采纳，不再派 revision3；真实 MODEL/RPC、A 原件、C 权限、独立 D 合成资金链、双 E 升级及日志回归仍须按最新状态判断。已采六框架、A-EDITOR 及旧文书、资金、原件不重放。细节只读当前状态与原报告，不复制全部历史到交接文档。

## 4. 下一份 plan 必须写清

- plan 名称/版本、目标、当前基线，以及本次包含和不包含的业务范围。
- 按真实依赖组织的成果步骤、每步完成标准和最终验收证据；明确是否包含后续阶段，不做无边界自动续行。
- Codex 可自主决定的技术方案、团队调度、测试和普通修复，以及确需用户决定的业务或资源事项。
- plan 的结束条件、最终结果格式和用户可复现的效果入口；不能用“先规划、再申请实际工作”循环代替实施。

保留 R1 的 Odoo 原生优先、必要自研、不引入 OCA、先功能后美化方向。只读、模型、真实请求、浏览器和已提交事实分层验收。项目流程调整不取消数据保护、真实工具权限或生产另批要求，也不是重试此前被拒动作的许可。

## 5. plan 最终结果与 GPT 审查

Codex 用一份简短摘要附既有报告链接交付：plan 与范围；完成/未完成及偏离；固定代码和实际测试候选；测试证据与独立验收；失败、风险和用户待决事项；效果复现步骤。未完成则如实交部分或受阻结果，不把会话停止写成 plan 全部通过。

GPT 收到最终结果后，核对固定差异和验收证据，明确自己实际审查的范围，给出采纳项、具体缺口及下一方向或后续 plan。不要重新变成实施期间的逐批审批者。

持续使用同一个 CURRENT_TASK.md 和本 GPT_HANDOFF.md；不新建编号交接附件，不重复归档旧事故细节。
