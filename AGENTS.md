# YDental 当前执行入口

- 当前需求 YD-N1 R1。唯一来源是 [总计划 #23](https://github.com/Yredxin/YDental/issues/23)、[S00 #24](https://github.com/Yredxin/YDental/issues/24) 至 [S13 #37](https://github.com/Yredxin/YDental/issues/37) 当前正文和有效评论。先读取 GitHub，再执行明确启用范围；代码、卡片及历史验收不授权开工。
- S00 已按 [GPT-CLOSEOUT](https://github.com/Yredxin/YDental/issues/24#issuecomment-6107583497) 最终收口，#24 CLOSED/completed；固定技术交付 `6dbf0a0a8be966bee7b2250b2a77e5b4d70540d8`。历史失败和补交证据保留，不重做 S00。
- 本次用户在新会话启用 #25 / S01：先读 #23、#25 全部有效评论与 #24 最终收口，完成开工核对并向 #25 发布、完整读回 [CODEX S01开工条件检查](https://github.com/Yredxin/YDental/issues/25#issuecomment-6107613041) 后实施。需求只来自当前 Issue，不继承旧聊天或撤销计划。S02 未启用；不修改 workflow、原生 Status、Issue/PR 状态，不发布生产。
- 当前同一 S01 会话仅按 [GPT-REVIEW 6108433241](https://github.com/Yredxin/YDental/issues/25#issuecomment-6108433241) 修 BLOCKER-1～4 和 COMPANY-SCOPE；用户明确授权 Project #25 自定义“执行状态”改为“返工”，已完整读回。除这一次单字段修改外不授权 Project 写；既有 e55f823 证据不覆盖。修正契约见 [docs/s01-rework-contracts.md](docs/s01-rework-contracts.md)。
- 不从撤销任务、四份旧文档、旧计划、旧 AGENTS 或历史验收补业务规则。文档仅记录当前 Issue 的工程落地与证据，不另立计划。工程约定见 [docs/contracts.md](docs/contracts.md)，事实与阻塞见 [docs/s00-a-report.md](docs/s00-a-report.md)。

## 工作区和保护

- 核心 Git 根 `/home/redxin/code/odoo/odoo-sd/code`；本仓库为其独立 Git 根 `sd-addons/`，远端 Yredxin/YDental。每次仍核实实际路径、远端、分支、HEAD 和未提交改动。
- 不改 Odoo 核心、odoo-12、既有未提交内容、既有业务库，不停止/重配既有服务。本批只实现和验证 #25；新增运行只在全新隔离 S01 库中使用合成数据。系统依赖安装和既有服务变更需具体授权。
- 父目录 AGENTS.md 是既有未跟踪文件，保留原样；其中 sd-addons 为空、仅本机数据库映射等描述已陈旧，不作为实际现状或本批运行授权。
- 底座锁定 Yredxin/odoo@f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb，本地声明20.0；Python 用核心 .venv/bin/python。此为 fork 无父根快照，不能冒称已核对同 SHA 官方上游。调用 API 前查实际源码；兼容性需所属批次实测。

## 后续工程和交付

- 原生+自研，不引入 OCA，不创建未来空壳、不机械改名或重授权许可证。命名、依赖、翻译、时间、编号、字典与动作契约见 docs/contracts.md；生产参数按 #23 第3.2节和责任阶段发布。
- 修改 addon 前读取适用 odoo-guidelines；static/ 使用 odoo-web-guidelines；安全审计用 odoo-security。技能不替代当前需求和授权。
- 本批及未来获启用的运行批次仅使用全新隔离允许范围数据库与合成数据。先验证端点/唯一库名/创建记录及OID/独立配置、data_dir、日志/精确dbfilter/端口/外发禁用；拒绝业务库、历史库与错误端点。S01 使用 scripts/s01.py 和 `ydental_s01_test_14位时间_8位hex`，S00 工具/库仅历史保留，不接管。
- 仓库和 GitHub 只放虚拟/脱敏材料，不发布凭据、患者资料、签名、备份或原始运行日志。长期保留失败与补交证据，未执行记 NOT_RUN，能力/权限阻塞记 BLOCKED。
- 独立分支提交；S01 PR 如需创建用 Refs #25，不强推、不自动合并/关闭任务/启动下一阶段。Project 写前完整读取条目、字段、视图与自动化元数据；边界不明停止相关写入，写后读回和二次同步核对。本批只授权上述 #25 自定义字段单次修改，后续 Project 写入未授权；禁止修改任何 workflow、原生 Status 或 Issue/PR 实体状态。不得导出 token/cookie 或关闭安全控制。
