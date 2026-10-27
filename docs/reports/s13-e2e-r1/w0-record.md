# E2E-W0 阶段记录

计划：YD-S13-E2E-R1 / 1.1。状态：**原隔离阻断已解除，W0 限定准出由主控裁定；此前 W1—W7 NOT_RUN**。本记录汇总 C-W0 只读检查及 A、B 通过主控提供的现场事实，不代表 W1 账号登录或业务流程通过。下方阻断描述保留原时点。

## 用户确认后的隔离事实

用户明确确认本机是内网机器、不存在公网 IP、可以正常使用。主控据此解除此前因公网可达性未知而产生的 W0 隔离阻断；W0 限定准出由主控裁定。此前现场网卡显示全局范围 IPv6、code-server 认证端口代理、`unshare` 权限拒绝及普通用户无法执行 `ufw status` 的事实均保留；地址范围本身不能证明公网可达。此次确认不改变保护、凭据或外部通道限制，也不把未经实测项写成 PASS。

截至此前停机独核，本次自有服务已停，管理员真实表单登录及权限核对已完成，11 个指定账号不存在；保护及配置恢复见下方独立证据。管理员页面三项客户端拦截仍为 UNKNOWN；W1 登录及业务动作尚无通过证据。

## 仓库与需求事实

- 2026-10-27 06:25:19 UTC，实际活动分支为 `codex/s13-e2e-r1`，HEAD 为 `6b28f5ed4192610e9bbb535f6013d08f66ba85a6`；工作树中的 `CURRENT_TASK.md` 已被主控修改。此时本记录尚未创建。`origin/codex/s13-dl-p13-settlement-bill-panel-r1` 指向同一 HEAD，`origin/main` 为 `18791828f0318962cb130c7da5308ab208745cb0`。`git merge-base --is-ancestor 83d5a002ee29dbb10177c773a81f7c2acae8b583 HEAD` 退出 0；以上为本地引用，不能代替现场远端核验。
- 默认分支交接入口的当前 P13 路由及活动 [CURRENT_TASK](../../CURRENT_TASK.md) 记载：P13 首账单界面限定技术完成、同步且停止，产品候选为 `83d5a002ee29dbb10177c773a81f7c2acae8b583`；P12 整体仍 PARTIAL，A04 真 JS-off 失败保留。main 是交接路由，不是业务产品基线。历史各时点的“不启动下一阶段”不否定用户现已交付的本次限定 E2E 计划。
- #23 OPEN、#36 CLOSED、#37 OPEN。#36 的合成软件技术关闭不构成临床、财务、签署、实机或生产批准。#37 的完整 S13 还包括负载、恢复、实机和正式政策等；本次 E2E 的限定结论不能替代完整 S13 关闭或用户效果确认。
- #36 要求文书来源与版本可追溯、草稿不冒完整正式、旧件重印读取原快照；收款、退款、应收和在途分开，多账单分摊回源。#37 正文的 740、500、240、退款100及270＋200、收300的例子与本次计划一致。#37 增量 6246183094 保留旧 NOT_RUN 和用户效果，未实测不得改为 PASS。
- #23 增量 6246155405、6246356260 和适用 AGENTS 规则将计划内技术执行与独立验收交给 Codex；不要求逐批 GPT 审批，计划结束才同步最终结果。真实平台限制、未知提交和历史证据不因流程调整而解除。

## 历史保全线索

- P13 末次文档记录合成目标 OID `2171423`、cluster `7694897083368259627` 及对应 filestore；记录旧审计保全、83 附件引用、80 实际文件、三处共享及末次正常停止。它们是历史时点事实，不能证明当前目标身份、隔离或当前完整性。
- 旧 scope、STOP、账本、证据和受保护经济、库存、文书、原件、附件、审计及未完成责任不可覆盖或盲目重放。若拟复用历史环境，须先现场核身份、权限和当前保护基线，并以新独立 scope 管理本次运行。
- 活动 CURRENT_TASK 的 S11 历史段保存 G01/G03 原平台拒绝、后续限定补证及停止时点。应按当前具体请求和实际生效限制处理，不把历史时点错误地当成永久一律禁止，也不得清除或绕过真实限制。

## 未决与准出前需核实

- 当前远端 refs 和 Issue 正文及有效增量是否仍与本次读取一致；实际 Odoo、依赖、数据库、cluster、filestore、网络隔离和所有权；历史数据当前保护基线。
- 管理员登录已见下方记录；仍需核实初始化操作及其范围，新数据命名范围与业务对象写入边界。
- 适用范围外的全部网络外发路径仍未证明禁用；W1及后续须维持本机隔离与外发禁止，并在启用任何新的发送能力前核实。W1 账号创建及登录、任何业务提交和用户效果均尚未测试，不能记为 PASS。

## A、B 现场只读结果

- B 报告实际目标 OID `2171423`、cluster `7694897083368259627`，145 业务、13 技术、83 引用／80 文件和 7 项附加保护投影与所比历史基线一致；目标无其他连接，11 个计划账号均不存在。这是 B 的现场只读结果，不代表全部数据库物理内容不变，也不证明新业务写入安全。
- B 报告 SMTP 配置数为 0、两条通知策略 disabled；其他 202 个数据库存在继承 CONNECT，其他数据库对象访问未核。网络隔离及全部外发路径尚未证明；没有为单一角色修改全局 ACL。
- A 初查正常岗位 provider 的 14 用户均非直接 system 管理员；其后找到既有 UID 2 管理员的合法私有 provider（历史线索见 `docs/reports/s11/summary.md` 310–313、1606–1607 行及 prepare receipt），实际通过正常网页表单登录 UID 2，正常 RPC 确认 system 组及 `res.users` 创建权限为 true。未创建账号。私有证据 `.local/s13-e2e-r1/w0/admin/result.json` SHA-256 `44584cedadeacc86007e7b92e3f2df058863bf07c48e6d2d3ec0ae2fd8695ed5`；C 核对文件 SHA，登录和 RPC 事实来自 A。客户端拦截三项未知请求，不能称产品拒绝，也不能宣称整页通过。
- A 的新 scope 实际浏览器 stdout 记录 `GET /web/login` 返回 HTTP 200，用户名和密码框及按钮可见，字段为空，独立 Context 已关闭；浏览器和服务退出码均为 0，临时配置已移除。这只证明无凭据表单可见和资源收尾，不证明账号登录或隔离。原始结果顶层 `browser: NOT_RUN` 是采集器标签错误，保留原值；判断依据是实际 browser stdout 和退出记录。私有原件 `.local/s13-e2e-r1/w0/result.json` SHA-256 `90d9c669771b14d3c2fc676ad2950a6774a4305e4d8b58076959ba940c35b890`；C 核对了文件 SHA，运行事实由 A 通过主控提供。
- B 原始私有证据：`.local/s13-e2e-r1/b-w0/protection-baseline.json` SHA-256 `53b0331d0e94daa9f343b7dfda6abf355e35e2d9030ea64d76f2830bb386d568`；`technical-and-config.json` SHA-256 `d137bdec1414676809f44e79d6e9918f52c8d137473ad2bc61fe58b48e5fde34`；`omitted-columns.json` SHA-256 `6f8eedc54eac413849af311e69d97af979d6cf5bd1a071cf77aacaa67479bfda`。这些路径均在上述同一私有目录；C 只核对文件 SHA，现场查询和结论来自 B。
- B 登录后独立复核报告：旧业务保护、13 技术投影及附件一致，新增 3 条 UID 2 正常认证／门店审计；本次进程正常停止。当时 `web.base.url` 已自动变成本次 loopback，尚未恢复；后续恢复及复核见下，不能将这次运行写成全库无变化。合成前缀 `E2ER1-20261027` 在核查的 89 个适用列无冲突，仍需对实际创建对象维持来源和所有权控制。
- 上述复核原件位于 `.local/s13-e2e-r1/b-w0/`：`after-admin-protection.json` SHA-256 `c75e9b1b0a2b79e1aa3dd3fc91864f56734dfed4e6fe197e08e436129c46547b`；`name-and-audit.json` SHA-256 `c5e66b42dd84ae8787614fe4316af0a3bd9f9d741e07417162197bdef0a40311`。C 已独立计算文件 SHA，查询结论来自 B；W0 尚未正式准出。
- B 的原生外发配置补查：25 条支付 provider 的 code 为 `none`，IAP 0、SMS 0、SMTP 0，邮件无 outgoing；这不证明所有网络外发路径已禁用。旧版字段查询返回 PostgreSQL `42703`，原失败保留；使用实际字段的新查询成功。私有证据 `.local/s13-e2e-r1/b-w0/outbound-native-flags.json` SHA-256 `c5ace36e4870e3de10cf9d60d4bd5fac86ed114683de5abc14d4ae804326adaa`；C 已独立核对文件 SHA。
- `web.base.url` 历史值为本机 loopback 端口 18411，管理员登录后自动变为本次 loopback 端口 18511，会影响生成的绝对链接。A 已经正常管理员 ORM 恢复，B 独立核实与 P13 原值一致、freeze 未设；保留曾发生的变化，不称全程配置未变。
- 主控现场核查到 code-server 监听 `0.0.0.0:19999`，启用需要认证的本机端口代理，且与测试服务处于同一网络命名空间；其公网可达性未知，不能据此假定可达或不可达。尝试 `unshare -Urn` 失败，原提示为 `write /proc/self/uid_map: Operation not permitted`；普通用户执行 `ufw status` 返回需要 root。未绕过权限或修改平台控制。W0 隔离边界尚未满足准出，固定 UAT 账号密码及依赖动作暂停。
- 恢复后 B 独核：145 业务表中仅正常认证／门店审计新增 6 条，旧行不变；13 技术、7 附加保护及 83 引用／80 文件与基线一致；11 个指定账号不存在，本次服务已停止。原件 `.local/s13-e2e-r1/b-w0/after-restore-protection.json` SHA-256 `931aa8e2c7a566e439757f9a6ce1d814694208e29b0be15165080ce953fc15e9`；`after-restore-independent.json` SHA-256 `641af8019a96e31c1570cd28b23940763ab041fa804c2fc7313132428a25fddc`。C 已独立核对文件 SHA，保护查询和运行结论来自 B。

## W0 限定准出与交接

已获得现场目标身份、保护投影、无冲突数据前缀、正常登录表单及合法管理员入口的分层证据；历史保护和用户指定的业务边界继续适用。管理员页面客户端拦截的三项未知请求保留 UNKNOWN，不写成服务端拒绝或页面全通过。阻断交接时网络隔离尚未确认，W0 BLOCKED，W1—W7 NOT_RUN；随后用户确认及主控处理见上。不能据本记录推定任何 W1 登录或业务测试成功。此次阻断交接没有向 GitHub 发布阶段最终报告。

## 读取来源与执行层级

- 只读命令：`git status --short --branch`、`git rev-parse`、`git merge-base --is-ancestor`、`git show origin/main:GPT_HANDOFF.md`、`git show origin/main:CURRENT_TASK.md`、`sed`/`rg` 读取活动状态；`gh issue view` 读取 #23、#36、#37 正文和状态；`gh api` 列出及读取上述评论。命令成功并不证明浏览器、模型或业务提交测试通过。
- 引用：[总计划 #23](https://github.com/Yredxin/YDental/issues/23)、[S12 #36](https://github.com/Yredxin/YDental/issues/36)、[S13 #37](https://github.com/Yredxin/YDental/issues/37)、[P12 结果](https://github.com/Yredxin/YDental/issues/37#issuecomment-6422670245)、[P13 结果](https://github.com/Yredxin/YDental/issues/37#issuecomment-6434515450)。
- C-W0 未登录 Odoo、未启动服务、未连接或写入数据库、未执行业务动作，也未发 GitHub 消息。此记录不含账号密码或私有凭据。
