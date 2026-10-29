# Windows 局域网直连：L1 测试记录

**当前：服务已停止，USER_ACCESS_UNVERIFIED；UAT_L1_READY 未满足。** 本轮未取得 Windows 用户的 TCP 连接、登录、当前门店确认或页面体验结果，均为 **NOT_RUN**；49 个完整用户用例仍为 **NOT_RUN**。此前的本机页面证据不代替用户结果。

## 目标与实测范围

- W0 `lan_w0` 和独立 `lan_w0_reviewer` 核实 Ubuntu 内网接口 `ens18` 的实际 IPv4 为 `192.168.1.128/24`；本次独立 UAT 目标端口为 `18776`。不是其他 Odoo 实例端口，也不是 Docker 内部地址。
- 本轮候选产品为 `12f3f299b07ab324f7279413a928097b7ce858a8`。独立 Reviewer 从新只读连接核实了指定 scratch 的数据库名、OID 和集群身份；数据库容器使用 `network none`，无端口发布。产品代码未修改。
- 本次 UAT 实例专用私有配置由回环改为绑定 **`192.168.1.128:18776`**；控制工具同步调整监听冲突、进程身份和停止检查。W1 `lan_config_w1` 实施，`lan_reviewer_w1` 独立完成限定源码和模拟检查；未改系统防火墙、代理、认证或其他实例。
- W2 `lan_runtime_w2` 受控启动后，`lan_runtime_review_w2` 独立看到唯一目标监听为该内网 IP 和端口，属于指定 Odoo 进程；因此 **LAN_LISTENER_READY 仅在本轮监听期间成立**，不代表现在仍在监听或 Windows 已可达。Ubuntu 使用该地址访问登录页得到 HTTP 200；执行者使用普通前台账号登录、选择门店并只读患者页面，未代替用户确认当前门店。前台页面中有合成门店名称，不能单凭此证明当前门店选择状态。另有 2 个技术 POST 被浏览器测试器本地预拦，服务端未收到；这不是产品拒绝，也不能据此外推完整前端交互。
- 此次使用的协议为 **HTTP 明文，不提供传输加密**。没有取得已有获准 HTTPS 入口的证据；这并非证明其他 HTTPS 入口一律不存在。绑定指定内网接口不证明仅有用户的 Windows 能连接。

## 数据库入口阻断与收尾

独立实例保留固定数据库约束、`list_db=false` 和禁止数据库列表配置。执行者的事后观察摘要记录：未认证的 `/web/database/selector` 和 `/web/database/manager` 均返回 HTTP 200，HTML 含隐藏管理表单；原始 HTTP 响应未保留。独立 Reviewer 的 selector GET 仅证实 HTTP 200、显示管理禁用提示且响应中未见目标数据库名，并未独立保存完整响应证明全部表单。固定 Odoo 核心源码 `addons/web/controllers/database.py:145–152`、`addons/web/static/src/public/database_manager.qweb.html:35,47–87` 与 `odoo/modules/db.py:242–250` 分别支持管理模板渲染、隐藏表单及 `list_db=false` 的检查；管理 POST 未发送，因此 **没有动态验证其拒绝行为**。由于工作包要求避免用户访问数据库选择入口，发现上述情况后停止内网监听；不能声称这些 URL 不存在或入口已关闭。

执行者正常停止 Odoo 和指定数据库容器；独立 Reviewer 核实端口无监听、指定容器 `exited` 且退出码 0。为核实本次登录和读取的影响，Reviewer 随后仅受控启动同一隔离数据库、以新只读连接复核身份并采集后像，再正常停止该容器；没有重启 Odoo。117 张受检表中审计记录 **401→407**、会话记录 **96→97**，其余 115 张表的逐行摘要一致；这是受检范围的只读比较，不证明全库零变化。Odoo 退出码与 Session 失效仍为 **UNKNOWN**。

## 限定独立审查与证据

W4 `lan_final_review` 独立核查记录与证据范围；结果仅限源码、文档与本机回执，不证明 Windows 访问或动态管理请求拒绝。原始 HTTP 响应未保留，以下 SHA256 对应本机私有文件，不能补作响应原件：

| 证据 | SHA256 |
|---|---|
| 本机前台只读执行脚本 | `6924b52d95579f725be7aac95e28174e0ef49108752115e21b18fbb999b3dbe9` |
| 本机前台只读结果 | `ce8991fd493712f7c867ff5b1fa3d194deedd8b0874c1fed426659bfd0bd6b90` |
| 执行者事后 selector/manager 观察摘要 | `ceb49ae1ac9f97011190fef35d38c91d166a011d97e21c4f7b5b6f8473ceacac` |
| 受检表前像 | `7bfbf169484804d4c8b8df3d6fa277639214c5aaa9d2a7f64659c95147d960be` |
| 受检表后像 | `c28633df523db8801e1b376a6343201763ff44a834de7c38a25f1e8d0bf6a686` |

## Windows 用户验证尚未执行

目标地址曾在 Ubuntu 本机实测：`http://192.168.1.128:18776`。**当前服务已停止，请不要把它当作现在可连接的地址。** 只有数据库选择入口的阻断得到处理、负责人再次核实身份并受控启动，且账号经获准私有渠道交付后，才可由 Windows 用户实际打开地址、登录、核实明确的当前合成门店，并只读查看患者列表。不得发送密码、Cookie、Session 或认证信息到聊天或公开仓库；当前私有账号交付方式尚未确认。

若后续负责人确认可安全启动而 Windows 浏览器仍无法连接，可在 Windows PowerShell 使用以下命令检查 TCP；它只证明端口连通，不能证明 Odoo 登录或用户验收通过：

```powershell
Test-NetConnection -ComputerName 192.168.1.128 -Port 18776
```

本轮不采用 SSH 转发、VPN 新部署或公网映射；未修改系统防火墙。任何额外网络或安全配置须按实际授权和具体问题决定。

| 验收状态 | 本轮事实 |
|---|---|
| LAN_LISTENER_READY | 历史瞬时成立；现已停止，当前不成立。 |
| LAN_TCP_REACHABLE | Windows 未测，NOT_RUN。 |
| USER_LOGIN_VERIFIED | Windows 用户未登录，NOT_RUN；Ubuntu 前台登录仅为本机技术验证。 |
| CURRENT_STORE_VERIFIED | 用户未确认当前门店，NOT_RUN。 |
| UAT_L1_READY | 未满足；用户端页面及安全前置尚未核实。 |

保留 P14-V2 PARTIAL / T09 FAIL、P12 A04 及旧 P14/T09 FAIL、R3 整体 PARTIAL 与历史 UNKNOWN；#37 保持 OPEN。未执行 L2/L3、P15、产品合并或生产部署。此前步骤与技术证据见 [L1 准出记录](l1-readiness-review.md)；用户连接的历史及本轮状态见 [用户端连接记录](l1-user-access-record.md)。
