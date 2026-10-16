# S10-P0-03：历史退款驳回已提交，事前财务门禁触发 BLOCKED

**判决：`BLOCKED_AFTER_ONE_COMMITTED_REFUND_REJECT_UNLISTED_COMMAND_METADATA`。** 唯一授权为 [#34/6191916076](https://github.com/Yredxin/YDental/issues/34#issuecomment-6191916076)，事前检查点 [#34/6205549655](https://github.com/Yredxin/YDental/issues/34#issuecomment-6205549655) 已通过 GitHub API 逐字读回。新克隆库中，Firefox 真实到达退款第 2 页，user6 对历史 requested 退款 ID14 的一次原生 HTML 驳回已提交并返回 HTTP303。紧接着只读比较发现结算互斥 revision 和幂等命令收据两类变更未列入事前字段级白名单，浏览器 exit1 并停止。日结第 2 页、日结 ID9 解锁及两次无权请求均 **NOT_RUN**；不能申请 P0-03 限定技术 PASS。

## 来源与 CREATE 前归因

开工完整获取 #23 当前正文及 3 条有效评论、#34 正文及 181 条有效评论，#35 OPEN/0；最后授权仍为 #34/6191916076。原分支本地/远端从固定 `47922cf78de2c2266b9015b56684e68d32d50df8` 起，工作树干净，Odoo20 core 为 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。R3 只读库 OID2056451 与 P0-02 停止库 OID2100311 的 marker/config/filestore SHA、历史经济与权限状态重新核实；两源无活动连接。R3 的 265 张受管表、schema、模块、视图、附件和184份文件等于 P0-02 原始快照；P0-02 停止库265张受管表签名等于既有 BLOCKED 证据，643张 public 表在事前固定，194份文件及1075附件指针核对。门店1退款63、日结55，退款14仍 requested、日结9仍 confirmed 且为同收费员/日期/渠道最新周期，user6本店结算和财务审批均 write 且非申请人。安装态 tokens 的全部有效语言含 `output=html`，模块702/installed92及五个结算视图身份一致。

P0-02 新附件1072—1076分别为两份 woff2 字体、frontend minimal JS、frontend CSS和frontend lazy JS：逐ID的 `ir.ui.view/res_id0/public binary`、本地URL、MIME、文件头、大小、SHA1/文件指针均核对。新10文件中的另5份恰为 `checklist/<同一store_fname>` 零字节标记；Odoo20 `assetsbundle.save_attachment` 调用 `ir.attachment._file_write`，再由 `_mark_for_gc` 生成该标记。邮件1832/1833仅为 `res.users/6` 和 `hr.employee/2` 的内部 tracking/subtype2，无收件关联、待发邮件或通知新增，正文只在私有原件保留。原生 `res.users._update_last_login` 创建用户登录日志，`auth_signup.state` 从受邀变为已确认，HR关联员工 user_state 同步；浏览器时区 UTC 另经 user→partner/employee→hr.version/resource 同步写时间/写人。user6的设备日志、S01 login/login.scope/store.switch 审计及会话177均与自身会话哈希匹配。643张表的逐表签名、每个资源文件SHA和头部、字段变化、源码SHA见[固定预检](evidence/s10-p0-03/preflight.json)，SHA256 `4a75a4f440a73e28f87eb1b0192037bb4a651f564f190c24fd6e97423572fddd`。

同一控制路径的离线模拟为资产/cache正例 1 个 `SIMULATED_PASS`、29个负例 `FAIL_CLOSED`；原生Odoo20 CLI parser确认HTTP无更新、安装、init或test。预检脚本与控制、浏览器、snapshot、CLI及offline程序SHA全部在事前评论固定，之后未改。

## 新隔离克隆与真实 Web 停止点

唯一 `CREATE DATABASE ... WITH TEMPLATE` 从 P0-02 停止库克隆 `ydental_s10_test_20261016_p003_75c1e9b2`，新 **OID2100319**、loopback **18286**、独立 config/data_dir/dbfilter/marker；复制194份文件并核对1075附件指针，克隆后643张 public 表及265受管表/schema/702模块/全部视图逐行全等。没有对两座源库或新库执行 `-u`、init、install、prepare、shell。

唯一 HTTP PID3987149 正常启动/停止 exit0；唯一 Firefox PID3987222 exit1（断言停止，未见 signal11）。Firefox 使用 user6自身会话，在原生结算页实际点击 `/ydental/settlement?refunds_page=2`，旧退款14可见，页面错误0，私有截图 SHA256 `1269b1fb9f81b5ba2d93223f06ce065e7e59b40c539786ac40a10b1006cb6fab`。退款表单自身CSRF/key/current revision、`output=html` 和 HTML5必填检查均通过；先写私有 intent，再只点击一次原生 `refund_reject`。HTTP日志只有这一条结算 action POST，状态303；页面反馈为“操作已受理，请核对下方业务记录。” 随后的独立只读快照先落盘，再做门禁断言。退款14已 **requested→rejected**，approver user6、合成原因和 S01 `settlement.refund.reject` 审计存在；原生 outbound payment、credit note 均为空。此为真实已提交驳回，不能重发或在另一库重做。

事前Web门禁要求所有非白名单表完全不变；本次目标643表中只有7表变化：用户设备日志+1、登录日志+1、S01审计+4、访问会话+1、退款14状态，以及 **`ydental_settlement_mutex` revision 242→243** 与 **`ydental_settlement_receipt` +1（ID242）**。源码 `ydental.settlement.service._operate` 为每次合法操作先递增互斥 revision 并在成功后写入幂等命令收据；ID242 `operation=refund_reject`、actor6/store1、结果 `refund_id=14/state=rejected/actually_refunded=0`。这不是新实收或实际退款，但它们属于实际数据库变化，且事前白名单没有放行。浏览器准确在 `('unauthorized_table', 'ydental_settlement_mutex')` 断言处 exit1；停止后只读取证又确认命令收据。不能在已发表检查点之后放宽门禁或继续日结/负例。

独立只读后置：原R3源265表/schema/module/view/filestore不变，P0-02来源643表及marker/config/194文件不变，均无活动连接。目标旧日结9仍 confirmed；附件、filestore、mail、模块、全部视图及schema无变化。原生 `account.move/line`、`account.payment`、partial/full reconcile、stock move/line/quant，以及YDental付款、费源、更正、交易、库存事件和治疗费用等14张关键经济表签名均不变；**幂等命令收据新增及互斥 revision 的事实另列，不能用“经济表全等”掩盖**。详细逐表前后SHA、审计与资源账本见[脱敏阻断索引](evidence/s10-p0-03/blocked.json)，SHA256 `f16f8de11aea3bd70884aeda76bf7f4c45c7a7da3c77a1feed9ec2a12e8a689a`。原始请求/响应含会话凭据，仅留700权限私有目录，不进入Git。

预算实耗：CREATE **1/1**、HTTP **1/1**、Firefox **1/1**、退款驳回 **1/1**；升级/install/init/shell **0**、日结解锁 **0/1**、无权POST **0/2**；新实收、实际退款、贷项、原生过账和库存写 **0**。#34保持OPEN、#35未启动，Project/产品addon/Odoo20 core/旧库/历史证据零修改。S10全阶段技术与生产继续BLOCKED，旧native SIGSEGV根因UNKNOWN。按授权正常提交推送并在#34发布BLOCKED复核申请，API逐字读回后停止，等待GPT独立裁定；不合并、强推或部署。
