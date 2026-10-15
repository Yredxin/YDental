# S10-E2E-W5：真实 Web 现金 500/240 已入账，脚本断言在第二笔提交后阻断

## 授权与结论

唯一授权是 [#34 评论 6186596167](https://github.com/Yredxin/YDental/issues/34#issuecomment-6186596167)，W4 GPT 独立复核是 [6186530230](https://github.com/Yredxin/YDental/issues/34#issuecomment-6186530230)。执行前读取 #23、#29—#34 当前正文和全部有效评论，#35 为 OPEN、0 评论；#34 最新正式授权为 W5。原分支起点与远端均为 `79417da9043478501ffae586f93eebc1e5d7105d`，Odoo20 core 为 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，没有并行 W5 进程。

**本批状态：`BLOCKED_SCRIPT_ASSERT_AFTER_SECOND_COMMITTED_PAYMENT`。** 唯一 W5 合成库中，经真实 Firefox 原生 HTML 表单按钮各提交一次现金 500、240 元；两次均观察到 HTTP 303、可信成功反馈及对应的原生已过账付款和 partial reconcile。第二笔之后，固定浏览器脚本的 `validate_money()` 将 `account.payment.state` 只允许为 `in_process` 或 `paid`；实际两笔在全额核销后都转为 `reconciled`，故断言失败、浏览器进程 exit1。第一笔后脚本确认成功；第二笔的请求、响应和独立只读账务快照均已先落盘，之后才触发断言。没有更改脚本、重发付款、重跑浏览器或再建库。正式完整执行器和最终审计没有完成，因此不申请 W5 有限技术 PASS。

## CREATE 前预检

只读来源 `ydental_s10_test_20261015064000_d41e7b62` / OID2100301 / cluster7694897083368259627，marker SHA256 `82aaa9c49144987eaa2bf08268db145b62bb55f3ebd5fb373d94dfbd4e101b4a`，config SHA256 `464f29204afd03c63d1450db442f4d42454e1d164243ca6bb1dbe8eb787b10ba`。来源 92 个已安装模块，38 张业务、原生财务、药房和权限表逐行签名与 W4 证据一致，152 个 filestore 文件和 164 个附件指针 SHA 一致；有效 en_US 安装态结算 token SHA256 `f454d4e36da804a2ff87a7519c680d59c33ff38e92e40ef296e2be6e1e49db3d`，含 `output=html`。唯一原生发票1 posted740、余额740，费用600/80/40/20、检查和库存1/4/2均保全，原生付款/partial及 S10 payment 为0。来源无业务连接。

W5 六份实际脚本的完整路径离线演练和 29 个场景通过；模拟覆盖唯一克隆、视图/模块/经济不变量、真实表单合同、两次付款、响应丢失后停止、第二笔重复与跨账。Odoo20 实际 CLI parser 确认 HTTP 命令无 install、update、init 或测试，workers0、cron0。固定预检 SHA256 `bb26dea5188ae9147aa11b85f45a530e6124487141f326c0b99238eed93479b4`。事前 [#34 检查点 6187223122](https://github.com/Yredxin/YDental/issues/34#issuecomment-6187223122) 已发布、API 逐字读回并由真实 checkpoint 验证，此时 CREATE0、Odoo0、Firefox0。

## 唯一实际执行

新库 `ydental_s10_test_20261015073500_e50f4a71` / OID2100310 / loopback18280，从 W4 模板一次 CREATE。独立 data_dir、filestore、dbfilter 和 marker；克隆后来源/目标 38 表、模块元数据、安装态视图及 filestore 全同。本批未安装、升级模块或启动 Odoo shell。Odoo HTTP PID3400717 启动一次，退出码0、运行9.28秒、无 signal11；Firefox/Playwright PID3400801 启动一次，退出码1，因上述测试断言，非原生崩溃。二者均已退出。

经理自身全新 Web 会话使用门店1。两次工作台实际渲染的付款表单均只有发票1，`operation=pay`、`output=html`、`channel=cash`、金额及实际UTC/凭据、有效自身 CSRF、新 key 和当前 revision，`checkValidity()`为 true。每笔事前 intent 单独落盘，浏览器原生按钮各点击一次；POST 请求 Content-Type 为 `application/x-www-form-urlencoded`，两次真实响应均 HTTP303，Location 为本地工作台带 notice，GET 均显示“操作已受理，请核对下方业务记录。”，页面错误0。两笔请求/响应及只读账务快照分别保存于私有 W5 目录。

| 时点 | 发票1 | 原生付款 | 原生 partial | S10付款/凭据 |
| --- | --- | --- | --- | --- |
| 克隆前与克隆后 | posted740，余额740 | 0 | 0 | 0付款，原 bill 凭据1 |
| 500 后 | posted740，余额240，payment_state=partial | ID1，500，现金 journal8，move2 posted，当时 state=paid | ID1，500，invoice receivable line5 → payment line7 | ID1，现金500，pay receipt2，S01 accepted |
| 240 后 | posted740，余额0，payment_state=paid | ID1=500、ID2=240，move2/3 posted，两笔最终 state=reconciled | ID1=500、ID2=240，均指向 invoice receivable line5 | ID1/2，pay receipt2/3，S01 accepted 两条 |

两笔原生付款均关联法人1、现金日记账8；S10付款均为门店1、患者1、实际收费员用户5、现金渠道、本店业务日2026-10-15。两笔付款分录各自借贷余额为0；S10 receipt 明确记录对应 native payment、partial 和发票1。原生收款为合成环境内线下确认，不代表现实现金或外部平台到账。

## 停止与只读保全

第二笔 `pay-2-observed.json` 在断言前已保存真实 303 响应及已提交账务。固定脚本第69行的 `native['state'] in ('in_process', 'paid')` 未考虑全额核销后 `reconciled`。这是一项测试判据缺口；现有只读证据没有显示产品错账。按授权立即 STOP：未修改固定脚本、未再发送 240、未重新启动 Odoo/Firefox、未执行 final_audit，也未截图第二笔。私有 `post-stop-readonly.json` 只读核对：W4来源的38表、资金、模块元数据、视图及 filestore 未变；W5 的31张应稳定业务表与付款前相同，来源 S01 历史行逐行不变；两笔付款和 partial 与 posted740→余额0 一致，原有价格快照和库存行不变。该只读审计不能替代未完成的正式执行器终态。

资源消耗：CREATE1/1、Odoo HTTP1/1、Firefox1/1、Odoo shell0、模块 install/upgrade0，成功资金POST仅500和240各一次，退款/日结/重复 bill/诊疗/检查/发药0。W3/W4来源业务写入0。私有日志、截图、配置、marker、响应和账务快照保留；脱敏机器索引见 `docs/evidence/s10-e2e-w5/verification.json`，预检见同目录 `preflight.json`。脚本 SHA 在付款后复核与预检完全相同。

S10 整阶段技术及生产继续 BLOCKED，#34 保持 OPEN，#35 S11 未启动。等待 GPT 独立复核裁定后续边界；本批不修脚本并重跑已付款库，也不修改产品源码、Project/Issue状态或生产环境。
