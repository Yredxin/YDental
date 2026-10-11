# YDental 当前执行入口

- 当前需求 YD-N1 R1。唯一来源是 [总计划 #23](https://github.com/Yredxin/YDental/issues/23)、[S00 #24](https://github.com/Yredxin/YDental/issues/24) 至 [S13 #37](https://github.com/Yredxin/YDental/issues/37) 当前正文和有效评论。先读取 GitHub，再执行明确启用范围；代码、卡片及历史验收不授权开工。
- 当前用户只启用 #24 / S00-T05 / Project #4 专项，边界见 [GPT-NEXT](https://github.com/Yredxin/YDental/issues/24#issuecomment-6107029151)。S00-A、S00-B及浏览器补证已技术复核，不重做；S01未启用。自动化条件/动作完整读取前不得Project写入；本轮事实与登录前置见 [docs/s00-t05-report.md](docs/s00-t05-report.md)。交付报告后停止，不称整个S00完成。
- 不从撤销任务、四份旧文档、旧计划、旧 AGENTS 或历史验收补业务规则。文档仅记录当前 Issue 的工程落地与证据，不另立计划。工程约定见 [docs/contracts.md](docs/contracts.md)，事实与阻塞见 [docs/s00-a-report.md](docs/s00-a-report.md)。

## 工作区和保护

- 核心 Git 根 `/home/redxin/code/odoo/odoo-sd/code`；本仓库为其独立 Git 根 `sd-addons/`，远端 Yredxin/YDental。每次仍核实实际路径、远端、分支、HEAD 和未提交改动。
- 不改 Odoo 核心、odoo-12、既有未提交内容、既有业务库，不停止/重配服务。当前批次仅处理Project安全核对与整理、必要只读工具及脱敏证据；不重跑运行验证。系统依赖安装和既有服务变更需具体授权。
- 父目录 AGENTS.md 是既有未跟踪文件，保留原样；其中 sd-addons 为空、仅本机数据库映射等描述已陈旧，不作为实际现状或本批运行授权。
- 底座锁定 Yredxin/odoo@f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb，本地声明20.0；Python 用核心 .venv/bin/python。此为 fork 无父根快照，不能冒称已核对同 SHA 官方上游。调用 API 前查实际源码；兼容性需所属批次实测。

## 后续工程和交付

- 原生+自研，不引入 OCA，不创建未来空壳、不机械改名或重授权许可证。命名、依赖、翻译、时间、编号、字典与动作契约见 docs/contracts.md；生产参数按 #23 第3.2节和责任阶段发布。
- 修改 addon 前读取适用 odoo-guidelines；static/ 使用 odoo-web-guidelines；安全审计用 odoo-security。技能不替代当前需求和授权。
- 本批及未来获启用的运行批次仅使用全新隔离允许范围数据库与合成数据。先验证端点/唯一库名/创建记录及OID/独立配置、data_dir、日志/精确dbfilter/端口/外发禁用；拒绝业务库、历史库与错误端点。scripts/p00.py 仅为历史保留候选；本批使用 scripts/s00_b.py，证据和剩余事项见 docs/s00-b-report.md。
- 仓库和 GitHub 只放虚拟/脱敏材料，不发布凭据、患者资料、签名、备份或原始运行日志。长期保留失败与补交证据，未执行记 NOT_RUN，能力/权限阻塞记 BLOCKED。
- 独立分支提交；PR 如需创建用 Refs #24，不强推、不自动合并/关闭任务/启动下一阶段。Project 写前完整读取条目、字段、视图与自动化；边界不明停止相关写入，写后读回和二次同步核对。当前API仍只暴露自动化元数据，正常浏览器需GitHub登录/二次验证；不得导出token/cookie或关闭workflow绕过，不能声称看板整理完成。
