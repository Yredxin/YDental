# YDental 当前执行入口

- 当前需求 YD-N1 R1。唯一来源是 [总计划 #23](https://github.com/Yredxin/YDental/issues/23)、[S00 #24](https://github.com/Yredxin/YDental/issues/24) 至 [S13 #37](https://github.com/Yredxin/YDental/issues/37) 当前正文和有效评论。先读取 GitHub，再执行明确启用范围；代码、卡片及历史验收不授权开工。
- S00 已按 [GPT-CLOSEOUT](https://github.com/Yredxin/YDental/issues/24#issuecomment-6107583497) 最终收口，#24 CLOSED/completed；固定技术交付 `6dbf0a0a8be966bee7b2250b2a77e5b4d70540d8`。历史失败和补交证据保留，不重做 S00。
- S01 已按 [CODEX 收口完成](https://github.com/Yredxin/YDental/issues/25#issuecomment-6108974493) 收口，#25 CLOSED/completed。固定产品修正 `740c42bbf611baa8713758fba38c1411d6b966c9`，产品与最终测试 `f1ce22df7002e40391ce16fd59093d60c4522b2e`，最终文档证据 `37ccd3af4c6af390506eb9229e2f1cc145e951b9`；原证据与失败链保留，不重做 S01。
- S02 已按 [GPT-REVIEW 6110161675](https://github.com/Yredxin/YDental/issues/26#issuecomment-6110161675) 技术复核PASS，固定产品 `9653ca2d25fde16ac791dd499197703c18ef18ce`、测试 `00c76b55f205ee032534b7a3b8cda27bd1d7764d`、最终证据 `e97f721270a991bd4a737c15808896b286e488e9`。按[最新流程决定](https://github.com/Yredxin/YDental/issues/23#issuecomment-6110178328)和[状态同步完成](https://github.com/Yredxin/YDental/issues/26#issuecomment-6110222109)，#26保持OPEN/待用户验收，最终统一验收，不重做S02。
- 本次用户明确启用 #27 / S03；边界为 [GPT-ACTIVATE 6110183188](https://github.com/Yredxin/YDental/issues/27#issuecomment-6110183188)。已读取#23/#27当前正文及全部有效评论、#26最终技术复核/状态记录；[开工检查6110252817](https://github.com/Yredxin/YDental/issues/27#issuecomment-6110252817)已写回完整读回后实施。只做人员安排/周排期/我的今日/安排反馈/默认建议/未来处置和共享容量/返池/转换/改期重配/临时开诊加额/营业。工程契约见docs/s03-contracts.md，字段见docs/s03-data-dictionary.md，实际证据见docs/s03-report.md。
- S04患者、S05预约业务、S06真实队列/坐诊租约均未启用；下游仅私有服务器扩展契约与合成验证，真实联调标NOT_RUN。完成固定产品/test/final提交并写回#27后停止等待GPT技术复核，不进入S04。后续阶段须独立启用，不将技术通过冒称用户已验收。
- 当前同一S03会话按[GPT-REVIEW 6110896380](https://github.com/Yredxin/YDental/issues/27#issuecomment-6110896380)与用户明确授权定向返工，只修完整能力建议、assignment级冲突待办、DST周窗口/当地输入三个BLOCKER；不重写已通过容量/返池/转换/并发/营业/离职设计。原d652026及docs/evidence/s03保留，新增契约docs/s03-rework-contracts.md、报告docs/s03-rework-report.md、证据docs/evidence/s03-rework。唯一授权的Project动作#27自定义执行状态→返工已完成并两次完整读回；后续不再写Project。交付修正评论读回后停止等待GPT复核。
- 不从撤销任务、四份旧文档、旧计划、旧 AGENTS 或历史验收补业务规则。文档仅记录当前 Issue 的工程落地与证据，不另立计划。工程约定见 [docs/contracts.md](docs/contracts.md)，事实与阻塞见 [docs/s00-a-report.md](docs/s00-a-report.md)。

## 工作区和保护

- 核心 Git 根 `/home/redxin/code/odoo/odoo-sd/code`；本仓库为其独立 Git 根 `sd-addons/`，远端 Yredxin/YDental。每次仍核实实际路径、远端、分支、HEAD 和未提交改动。
- 不改 Odoo 核心、odoo-12、既有未提交内容、既有业务库，不停止/重配既有服务。本批只实现和验证 #27；新增运行只在全新隔离 S03 库中使用合成数据。系统依赖安装和既有服务变更需具体授权。
- 父目录 AGENTS.md 是既有未跟踪文件，保留原样；其中 sd-addons 为空、仅本机数据库映射等描述已陈旧，不作为实际现状或本批运行授权。
- 底座锁定 Yredxin/odoo@f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb，本地声明20.0；Python 用核心 .venv/bin/python。此为 fork 无父根快照，不能冒称已核对同 SHA 官方上游。调用 API 前查实际源码；兼容性需所属批次实测。

## 后续工程和交付

- 原生+自研，不引入 OCA，不创建未来空壳、不机械改名或重授权许可证。命名、依赖、翻译、时间、编号、字典与动作契约见 docs/contracts.md；生产参数按 #23 第3.2节和责任阶段发布。
- 修改 addon 前读取适用 odoo-guidelines；static/ 使用 odoo-web-guidelines；安全审计用 odoo-security。技能不替代当前需求和授权。
- 本批及未来获启用的运行批次仅使用全新隔离允许范围数据库与合成数据。先验证端点/唯一库名/创建记录及OID/独立配置、data_dir、日志/精确dbfilter/端口/外发禁用；拒绝业务库、历史库与错误端点。S03 使用 scripts/s03.py 和 `ydental_s03_test_14位时间_8位hex`；S00/S01/S02 工具与库仅历史保留，不接管。演示策略不能用于生产容量分配，测试模块不得用于业务库。
- 仓库和 GitHub 只放虚拟/脱敏材料，不发布凭据、患者资料、签名、备份或原始运行日志。长期保留失败与补交证据，未执行记 NOT_RUN，能力/权限阻塞记 BLOCKED。
- 独立分支提交；S03 PR 如需创建用 Refs #27，不强推、不自动合并/关闭任务/启动下一阶段。Project 写前完整读取条目、字段、视图与自动化元数据；边界不明停止相关写入，写后读回和二次同步核对。本次返工唯一授权的#27自定义执行状态→返工已完成，其余Project字段不改；#26现为待用户验收，#27保持返工等待GPT复核，不因交付自动进入其他状态。禁止修改任何 workflow、原生 Status 或 Issue/PR 实体状态。不得导出 token/cookie 或关闭安全控制。
