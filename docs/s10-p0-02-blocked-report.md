# S10-P0-02：历史退款/日结 Web 分页在首笔 POST 前阻断

**结论：`BLOCKED_WEB_READONLY_GATE_ASSET_AND_LOGIN_METADATA_DRIFT_BEFORE_POST`。** 本批在独立克隆上完成一次原生结算模块升级；退款第 2 页已由 Firefox 实际点击并渲染，退款 ID14 可见。HTTP 页面加载后，目标库的原生 Web 资产附件及 filestore 发生预检合同未放行的变化，浏览器脚本在首笔业务 POST 前执行只读门禁时停止。退款驳回、日结第 2 页/解锁和两项负向请求均 `NOT_RUN`。不能申请 P0-02 限定技术 PASS，S10 整阶段技术和生产仍 BLOCKED。

## 授权、固定身份和预检

唯一授权是 [#34/6191214820](https://github.com/Yredxin/YDental/issues/34#issuecomment-6191214820)。开工通过 GitHub API 读取 #23 正文/3条有效评论、#34 正文/177条有效评论及 #35 OPEN/0，并复核 P0-01 授权/预检/阻断、W4 严格范围裁定和 GAP-01 矩阵。原分支本地/远端固定 `021ff462bfc2bd739871e99e4c4472eb389b3001`，开工树干净，Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。产品 addon 和 core 均未改动。

R3 只读源 `ydental_s10_test_20261014020300_8b6c1d4e` / **OID2056451** / cluster `7694897083368259627` 的 config SHA `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`、marker SHA `96d261798a4b4370772d5700ba8516dd7677d2568f2b3fda80d3572b94a644e6`、184份 filestore 清单 SHA `b325817771a580474b632108ea11f373b319567626c5d434e72a047bc556b549` 均重新匹配。265张适用 YDental、权限、价源、库存、原生会计及系统元数据表逐行签名、3495列/3019约束/909索引 schema、702模块/92 installed、25592条 `ir_model_data`、1600条 `ir_ui_view`、1070附件文件指针完成只读核验；P0-01的7张关键表旧签名7/7相同。

门店1实际服务域退款63、日结55：退款第2页含 requested ID14，申请人user5，金额1，无原生退款付款/贷项；日结第2页含 confirmed ID9，cashier5、2026-07-15、card、cycle1且为最新，原收/实退/在途均0。user6在本店有结算及财务审批write且非申请人；user10无两项授权，user14相关权限在门店3。R3安装态 `ydental_settlement_tokens` en_US SHA `7160c6c9d525cc4c7790079a944baa052a25bd488b23cbd77db90ad69b4cf0bc` 缺 `output=html`；现行源码具有该字段，controller只对 form-urlencoded + `output=html`给HTML 303。仅源码存在不替代安装态核验。

实际Odoo20 CLI parser确认升级argv只更新 `ydental_settlement`，HTTP argv不更新模块，dbfilter/data_dir/loopback/cron0/workers0一致。预检脚本编译通过，同一流程的离线模拟1正例 `SIMULATED_PASS`、28负例全部 `FAIL_CLOSED`，包括源/克隆漂移、QWeb语言缺字段、模块/视图/schema/经济/权限越界、HTML5/CSRF/key/revision、HTTP 200/403/409、提交后响应丢失、资金局部变化。**任何 CREATE 前**在 [#34检查点6191642977](https://github.com/Yredxin/YDental/issues/34#issuecomment-6191642977) 发布全部SHA、目标与预算，并经 GitHub API 逐字读回，正文 SHA `0c97f2573b5237e71c171bfba5072d186f70e581860199b80b9cfbe873fab61c`。固定预检 JSON SHA `7de64a8da531818f0909f7c7b0c988b6ee0916d7579d4b1756edd3128b24971d`。

## 唯一新克隆与模块更新

一次 `CREATE DATABASE ... WITH TEMPLATE ...` 从唯一R3源克隆 `ydental_s10_test_20261015_p002_6d84a2c1` / **OID2100311** / port18285。独立配置、data_dir/filestore/dbfilter与 marker 绑定源OID、HEAD、core和脚本SHA；无患者、费用或资金夹具写入。CREATE 后265表、schema、全部模块/view行、附件与184文件逐行全等源库。

唯一 Odoo20 原生 `-u ydental_settlement --stop-after-init --no-http` 进程 PID3554221，exit0、无 signal11/超时；升级日志 SHA `968422c43eada064fe3ab688101d4992633438b56482ce50dc5430f83db9ccbf`。升级后只读门禁通过：265表中仅 `ir_module_module` 与 `ir_ui_view` 改变；模块702条中682条**仅 `write_date`**变化，均在预检W4只读导出的682名有界集合内，state/version/安装集合及其它字段不变；变更的view恰为预先列出的5个 `ydental_settlement.*` key，非目标view、全部ID和 `ir_model_data` 不变。tokens全部有效语言仅en_US，安装态现含 `output=html`，SHA `f454d4e36da804a2ff87a7519c680d59c33ff38e92e40ef296e2be6e1e49db3d`。全部经济/权限/库存/价源、附件/filestore、schema与源库相同。原生日志若加载测试依赖模块，不能将整个加载过程描述为只加载目标；本批只指定升级目标模块。这些事实只支持合成克隆上的安装态同步，不证明生产升级安全。

## Firefox 到达的真实边界与停止原因

唯一 HTTP PID3554360 loopback 启动200、正常停止exit0，日志 SHA `3a765d672e29384622740abb6b83df4d185ff86831d864c2b514d903feb76e9`。唯一 Playwright Firefox 进程 PID3554432 在新user6会话以原生登录/切店表单进入门店1，真实点击退款「下一页」链接，URL含 `refunds_page=2`，页面渲染了退款 **ID14** 及旧记录表单；私有整页截图 SHA 固定于机器证据。此为 `NEW_REAL_WEB_PAGE2` 的**退款GET子项**，不等于真正提交成功或日结第2页已测。

首笔 `refund_reject` 的 intent 写入之前，浏览器执行升级后基线对第2页GET后状态的只读全表比较，发现 `ir_attachment` 已改变，抛 `('web_table_drift', 'ir_attachment')`，Firefox exit1。没有请求/响应不明的业务POST，也没有重试。事后仅只读取证：源库265表、schema、模块/view/附件/filestore、config/marker逐行与预检相同；目标库新增附件ID1072—1076，均为 `ir.ui.view` Web JS/CSS/字体资产，filestore **184→194** 文件，其中新增10文件中5被新增附件指向、5未被指向，生成链未完全查明且原样保留。另观察目标 `mail_message` +2、`res_partner` ID7 的tz/write元数据变化、`res_users` ID6写元数据变化、S01审计+3、访问会话+1。它们与HTTP登录/加载同一窗口出现；本批不把时间相关性冒称完整成因，也不事后放宽已发表的附件全等合同。

目标退款ID14仍 `requested`、原生退款/贷项空，日结ID9仍 `confirmed`；15张资金/库存关键表逐行签名保持来源值，账单、原生收付款/partial、库存与费源均无新业务变化。HTTP模式可能正常生成资产，但这次新资产和登录元数据属于预检未放行的目标变化，因此按 STOP 保全库、文件及日志。旧 Native SIGSEGV 根因仍 UNKNOWN，本次无新 signal11 不等于根治。

## 证据与预算

脱敏机器索引：[预检](evidence/s10-p0-02/preflight.json)、[阻断及最终只读审计](evidence/s10-p0-02/blocked.json)。私有完整数据库行快照、682条模块时间旧新值、HTTP/browser原日志、请求边界和截图仅在权限受限的 `.local/s10-p0-02/` 与独立新库目录，未提交账号、患者资料或私有原件。证据层级：`HISTORICAL_R3`源只读PASS；`NEW_NATIVE_ODOO_MODULE_UPDATE`同步门禁PASS；`NEW_REAL_WEB_PAGE2`仅退款第2页GET；`NEW_HTML_ACTION`/日结第2页/两项负向POST `NOT_RUN`；`NEW_READONLY_SQL`最后核验PASS；`SIMULATED_PASS`仅离线29例。

预算实际消耗：CREATE **1/1**、升级 **1/1**、HTTP **1/1**、Firefox **1/1**；退款ID14驳回 **0/1**、日结ID9解锁 **0/1**、无权POST **0/2**，Odoo shell/sudo/新收款/实际退款/贷项/出账/发药退库均 **0**。所有旧库、卷、filestore、事故日志和W5证据保留；产品addon/Odoo20 core/Project/Issue状态零修改，#34仍OPEN，#35未启用。不合并、强推、部署或自行进入下一批，等待GPT独立复核与新的正式授权。
