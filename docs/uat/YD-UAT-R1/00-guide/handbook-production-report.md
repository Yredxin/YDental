# 手册生产报告

状态：**HANDBOOK_PARTIAL（已完成限定全局复核，仍有覆盖及环境缺口）**。本报告是制作事实，不是用户验收报告。最终文档分支在下方登记，固定提交及读回值在交付消息记录；不得自嵌尚不存在的提交值。

## 基线和盘点

- 产品候选：`12f3f299b07ab324f7279413a928097b7ce858a8`。文档起点 `c6cd8cbb6bef956ab05d7b9c7ecfd6d4d150cb0a`；主控已核候选为祖先且 addon 内容无差异。main交接P13为历史路由，不是本次业务代码基线。
- 文档分支 `codex/yd-uat-r1-handbook`；最终提交由该分支的 `git rev-parse HEAD` 确定，实际提交及远端读回值在交付消息记录。提交不能包含自己的哈希值。
- W0源码盘点 `w0_inventory`；需求盘点 `requirements_inventory`；独立 `w0_review` 对35个ID分工及入口**条件通过**，每个操作仍需W1审查；源码不证明部署或用户验收。
- 16业务权限类别与等级见[矩阵](role-permission-matrix.md)，功能与源码见[索引](source-index.md)；岗位名不构成授权。

## W1分工与限定审查

每组1份功能README及下列用例，各有截图目录；作者与审查者是独立Agent，共享同一工作区，不代表操作系统隔离。结论仅SOURCE与文档，不是浏览器或提交验收。

| 块 | 作者 / 独立Reviewer | 用例数 | Markdown 数 | 审查情况与保留缺口 |
|---|---|---:|---:|---|
| A 员工权限 | author_a / review_a | 3 | 4 | 限定通过；ACC-003入口 UNKNOWN/BLOCKED。 |
| B 空间排班 | author_b / review_b | 5 | 6 | 限定通过。 |
| C 患者前台队列 | author_c / review_c | 6 | 7 | 限定通过；集团服务新增、现场登记完整步骤等缺口。 |
| D 治疗检查 | author_d / review_d | 5 | 6 | 限定通过；同工位检查未覆盖。 |
| E 库存药房 | author_e / review_e | 4 | 5 | 限定通过；实际来源不可唯一辨认时阻断。 |
| F 结算 | author_f / review_f | 4 | 5 | 限定通过；免单、更正、重分类、解锁及跨法人未完整覆盖。 |
| G 复诊加工 | author_g / review_g | 4 | 5 | 限定通过；有时段转诊、戴用返工及完整成本未覆盖。 |
| H 文书报表 | author_h / review_h | 4 | 5 | 限定通过；审计合法入口未固定。 |

各组4–7份 Markdown（README加用例），共35用例；逐文件反馈及修正由对应Reviewer完成。角色由 `author_roles` 编写、`review_roles` 逐目录独立复核：12 个岗位 README 限定 SOURCE 文档通过；场景由 `author_scenarios` 编写、`review_scenarios` 逐目录独立复核：10 个场景 README 限定 SOURCE 文档通过。W3 由 `author_guide` 编写、`review_guide` 逐文件独立复核：00-guide 10 份及 40-results 7 份限定 SOURCE 文档通过。复核发现并修订权限、交接、来源及阶段登记问题；均未运行系统。W4 全局独立复核由 `review_global` 执行，范围和结果见下；其审查不代表操作系统隔离或业务运行。

## 覆盖及未测试

[需求追溯](requirements-trace.md)列 R01—R26 与 S00—S13 对应用例和缺口；[限制](known-limitations.md)保留 P14-V2 PARTIAL/T09 FAIL、P12 A04、旧 P14/T09 和 R3整体PARTIAL。R3-BUG-001仅限定 FIXED_VERIFIED；#37 OPEN。用户环境未准备，所有用户结果初始 NOT_RUN；正式政策、外部通道、真实资金及生产未获授权。

## 独立集成、环境与交付

- 当前覆盖：8 个功能组、35 个用例、12 个岗位、10 个场景；83 份 Markdown、35 个用例截图目录（占位文件），总计 118 个文件。
- `review_global` 初检：非示例相对链接 759 条、缺失 0；35 个ID唯一，用户填写字段及 NOT_RUN 齐全，35个图片目录存在；R01–R26 与 S00–S13 均有映射或明确缺口。未见图片/PDF/ZIP及常见凭据强模式命中；这些是静态检查，不是对所有潜在秘密的绝对保证。最终独立复核及固定提交的读回见交付消息。
- 用户开始前须按[环境清单](environment-and-data.md)准备固定候选、合法独立数据和私下账号、门店/能力/测试策略及一次性动作保护；本工作包没有启动服务或业务。
- 最终文档分支与 HEAD：见上述分支及交付消息；不合并、不部署、不关闭 #37。
