# W7 独立复核与收尾记录

复核范围为活动候选 `dca4e1d2821b20df7b4b940d28d461270c310225`、产品 tree `4c09b0c5207f5a5c342ad3ccb63f2a51db2e5bad`，以及本机隔离测试库 `ydental_s11_synth_20261023_01`、OID `2171423`、cluster `7694897083368259627`。本复核采用新的只读、可重复读物理事务和已有网页回执；不重放已提交的经济、库存、检查或文书动作。

## 实际来源与未完成责任

独立读回账单 169 为 740 USD、余额 0，账单 174 为 270、余额 0，账单 175 为 200、余额 170；退款贷项 172 为 100，收款分录 170、171、176 分别为 500、240、300。原生银行匹配、外部支付及真实资金不在本次范围。药批 278 原生库存流水显示入库 10、发药 4 和 2、退药 1 至隔离区；药房、患者和隔离区分别为 4、5、1，退药出入库完成不代表核查责任完成。

文书 509–514 均为 pending；任务 888、895、897、900 为 pending，899、901、903 为 accepted，三个实际队列 558、559、560 均 waiting，902 cancelled。复诊 283 仍为 to_notify，内部 activity 215 active，既有未完成责任没有被测试自动完成。1550/B 前台权限恢复有效 none、医疗 read，原组恢复 `[17]`；1544/A 临时复诊权限恢复有效 none、医疗 write 保持。11 个测试账号均仍 active，**登录停用未完成**。

本次独立只读回执均保存在本机 `.local/s13-e2e-r1/`：

- 资金回执 `b-w6-final/physical-w7-independent.json`，SHA-256 `592a8cd31d28c265238f569908d797dc8cf67526314bc0fce66042a25aea0692`；库存及部分责任 `b-w6-final/pending-w7-independent.json`，SHA-256 `b15428c57e54008519754cc6dcc958436fb9d1aa6240b2e29e7a6df5b300d3be`。
- 最终任务／队列／角色 `b-w6-final/append-w7-final-after.json`，SHA-256 `512063be66028e0841dd95ff4b48e39721693643a1ea70e8ede767b2aee05bac`；复诊／通知 `b-w6-final/followup-w7-final-after.json`，SHA-256 `a5ef77173e491b4574e7f9e25c370764c767dcdfe8b4bfb8c2ea3919f553feef`；加工及通知 `b-w6-final/lab-w7-final-after.json`，SHA-256 `5ed0f239c615b26a560aee4d98d2cefec0d081dae7b0958c4d9d9181bbc3b883`。
- 文件清单 `b-w5/original-files-w7-independent.json`，SHA-256 `e6c754e1a9ef3d0f3b53159441e382fbf1842f542b3f814433a9b337a2c84ac3`：479 附件中 459 个文件引用全部存在且 SHA-1 与附件 checksum 符合；与目标升级后的 476 附件基线逐项一致。这不能补出缺失的升级前技术对象完整前像。

## 账号停用尝试及回滚

一次工具启动使用系统 Python 缺少 psycopg2，exit 1，未连接数据库、未创建运行目录；随后的项目虚拟环境执行到 ORM 事务内保护断言时退出 1，只有 `PRECHECK_OK`，没有 `COMMIT_STARTED`。独立读回确认 11 账号仍 active、URL 仍为 18511、连接和预备事务为零；原始失败不删除。另两次严格回滚诊断确认，正常 `res.users` 的 `active=False` 会在事务内影响 10 个供给槽 1229–1238 的状态、原因和版本，删除 12 个讨论成员，并写入测试账号 partner 元数据及 11 条审计。因此该停用未提交：不能以保护历史和未完成责任为代价，声称所有账号已经停用。

两次诊断都记录 `ROLLBACK_RETURNED`，其后独立读回相关待办、角色、通知任务及邮件投影与诊断前一致；12 个被事务内暂删的讨论成员真实存在。回滚不会撤回 PostgreSQL 序列使用，不能声称数据库各序列完全未变化。日志中 YDental `scope` denied 的捕获调用栈是 `res.users.search` → partner access domain → patient 可读性检查 → `_scope`；没有构造绑定或改动授权来绕过该拒绝。日志不证明停用操作整体获得了范围授权。

源码显示正常密码 `write` 会创建账户安全通知并调用发送，现场 11 个账号的 partner 邮箱字段均非空；本次没有执行密码轮换。现场原生 API key 数为 0，LDAP／OAuth 模块未安装，passkey、signup 和 TOTP 模块已安装；其他登录或重置途径未完整核查。因此不能将“服务已停”或潜在密码轮换等同于所有账号登录能力已停用，也不能以账户 active 状态推断既存会话实测结果。

## URL 和资源

由另一测试 Agent 执行一次 UID 2、非 sudo 的正常 Odoo ORM，将 `web.base.url` 从本次回环 18511 恢复为原 18411。其执行回执记录 `PRECHECK_OK`、`COMMIT_STARTED`、`COMMIT_RETURNED` 和 exit 0；事务内断言其余配置参数及 freeze 未变。独立读回确认 URL 18411，freeze 未设，11 账号仍 active，目标库其他连接和预备事务均为 0，18511 未监听，活动 lease、hold 和执行均为 0。最终只读回执 `b-w5/idle-w7-final-after.json` SHA-256 `8bdb72b2ff0c1c06d77f8b0e67cf1b1af0c21a6c7c98377448a9f502e5d13585`。独立复核未拥有其他配置的完整独立前像，其一致性仅以执行事务内断言为证。

本复核不能补齐历史旧件重印、16 个技术对象升级前完整前像、全部角色的最终候选复测、真实压力并发或账户登录停用；这些均须保持未完成或 UNKNOWN，不得将不同版本的证据拼成完整通过。
