# P14 产品回退与正式收口 / 1.0

2026-10-29，用户与 GPT 裁定不采纳 P14 原版及结构版，撤回 P14 产品改动。两版均未满足 T09；P14 的历史技术结论保持 **PARTIAL**，T09 保持 **FAIL**，原报告和失败证据不改写。此产品取舍不是用户效果验收或生产批准。

## 固定代码与独立源码核验

从原分支 `codex/s13-dl-p14-settlement-unpaid-waive-r1` 的 `d05864510987b4b0b4236938a5ccd1386f9431cd` 正常建立本分支 `codex/s13-dl-p14-revert-closeout-r1`，保留旧分支及其历史。产品回退提交 `b5b1770d65a2f4f6f22ddfc5692eaf98639757aa` 仅将结算模板和 manifest 恢复到 R3 报告基线 `c663557eeb30b9bb43f07f3ff8130c8cd3bc4382`，并从有效产品树删除 P14 新增 `settlement_unpaid.scss`；其历史仍在 Git。未修改其他 addon、Odoo 核心或共享设施。

未参与实施的 B 在固定提交独立执行以下 SOURCE 检查：

- `git diff --exit-code c663557 HEAD -- ydental_settlement`：exit 0，完整结算 addon 与 R3 报告基线一致。
- `git diff --exit-code f9c4778 c663557 -- . ':(exclude)CURRENT_TASK.md' ':(exclude)docs'`：exit 0；R3 报告基线的产品树与 R3 产品候选 `f9c4778e584e0513bcaf46cee3a76fd6883b76af` 一致。另核回退提交未改变结算以外的产品文件。
- `git diff --check d058645 HEAD`：exit 0；回退差异限指定三个产品文件。manifest 通过 Python AST 解析，8 个 data 文件及4条本 addon 资产引用均存在，P14 SCSS 无残留引用；QWeb XML 标准库解析 exit 0。
- P14、P14-T09 与 P14-STRUCTURE 代表性报告可读；历史报告目录相对 `d058645` 无差异。上述均为源码及文件检查，不代表真实 Odoo 升级、浏览器、财务操作或数据库保护验证。

P14 原版引入的 WebKit 768 裁切回归随该产品代码撤回，不再属于本分支有效新代码。P14 前基线在 320px 原生 200% 下输入宽于滚动框的问题仍存在；本次没有新的浏览器验收，不称其已修复。

## 历史保护及停止边界

原 [P14 总结](summary.md)、[T09 增量](t09-addendum.md)、[结构调整结果](structure-summary.md) 和各独立证据继续保留。历史合成库 UID1564/1565 的文书责任与唯一店长责任、R3 独立 scratch UID6/7 的合法责任，以及 P14-T09 scratch 已提交 event1/fee1/invoice1 和该库独立岗位 UID6/7 按各自数据库保留，不跨库混用或重放。历史经济、库存、原件、附件、审计与待办不被本次操作；没有连接数据库，因此不以此断言数据库物理零变化。

STRUCTURE 受检附件摘要变化的具体行和原因仍 **UNKNOWN**；正常审计增量、原浏览器结果文件哈希差异、历史缺失前像及 Session 未测均依原记录保留。E2E-BUG-002 OPEN，R1/R2/R3/P12 的既有 PARTIAL 不变。

本工作包未启动测试服务、浏览器或数据库，未执行经济 POST、模块升级或历史 Session 恢复。#37 保持 OPEN，不启动 P15、不合并、不部署、不重新开始 P14 设计；后续用户集中体验计划由用户与 GPT 决定。
