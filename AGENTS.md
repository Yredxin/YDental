# YDental 当前执行入口

- 当前需求 YD-N1 R1。唯一来源是 [总计划 #23](https://github.com/Yredxin/YDental/issues/23)、[S00 #24](https://github.com/Yredxin/YDental/issues/24) 至 [S13 #37](https://github.com/Yredxin/YDental/issues/37) 当前正文和有效评论。先读取 GitHub，再执行明确启用范围；代码、卡片及历史验收不授权开工。
- 本次用户仅启用 #24 / S00-A：现状核实、当前入口、工程约定。交付报告后停止，等待技术复核和用户确认；S00-B、S01 及其他阶段未启用，不称整个 S00 完成。
- 不从撤销任务、四份旧文档、旧计划、旧 AGENTS 或历史验收补业务规则。文档仅记录当前 Issue 的工程落地与证据，不另立计划。工程约定见 [docs/contracts.md](docs/contracts.md)，事实与阻塞见 [docs/s00-a-report.md](docs/s00-a-report.md)。

## 工作区和保护

- 核心 Git 根 `/home/redxin/code/odoo/odoo-sd/code`；本仓库为其独立 Git 根 `sd-addons/`，远端 Yredxin/YDental。每次仍核实实际路径、远端、分支、HEAD 和未提交改动。
- 不改 Odoo 核心、odoo-12、既有未提交内容、既有业务库，不停止/重配服务。本批不改业务代码，不安装升级模块、不运行 Odoo/PDF/数据库测试。
- 父目录 AGENTS.md 是既有未跟踪文件，保留原样；其中 sd-addons 为空、仅本机数据库映射等描述已陈旧，不作为实际现状或本批运行授权。
- 底座锁定 Yredxin/odoo@f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb，本地声明20.0；Python 用核心 .venv/bin/python。此为 fork 无父根快照，不能冒称已核对同 SHA 官方上游。调用 API 前查实际源码；兼容性需所属批次实测。

## 后续工程和交付

- 原生+自研，不引入 OCA，不创建未来空壳、不机械改名或重授权许可证。命名、依赖、翻译、时间、编号、字典与动作契约见 docs/contracts.md；生产参数按 #23 第3.2节和责任阶段发布。
- 修改 addon 前读取适用 odoo-guidelines；static/ 使用 odoo-web-guidelines；安全审计用 odoo-security。技能不替代当前需求和授权。
- 未来获启用的运行批次仅使用全新隔离允许范围数据库与合成数据。先验证端点/唯一库名/创建记录及OID/独立配置、data_dir、日志/精确dbfilter/端口/外发禁用；拒绝业务库、历史库与错误端点。scripts/p00.py 仅为保留候选，不是本批运行指令或当前已验收工具。
- 仓库和 GitHub 只放虚拟/脱敏材料，不发布凭据、患者资料、签名、备份或原始运行日志。长期保留失败与补交证据，未执行记 NOT_RUN，能力/权限阻塞记 BLOCKED。
- 独立分支提交；PR 如需创建用 Refs #24，不强推、不自动合并/关闭任务/启动下一阶段。Project 写前完整读取条目、字段、视图与自动化；边界不明停止相关写入，写后读回和二次同步核对。当前自动化配置读取受阻，不能声称看板整理完成。
