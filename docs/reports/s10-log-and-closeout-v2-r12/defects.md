# R1.2缺陷、首事实、修正及复核

旧R1.1两次普通修复、失败原始材料与STOP保持。用户R1.2解除普通轮数限制，不解除真实安全硬停；未为普通问题请求GPT逐项批准。

|ID|首事实及原因|补丁与实际复核|当前边界|
|---|---|---|---|
|R11-DEPENDENCY|scratch原exit255/no signal，受控路径漏既有s04-deps metadata。|launcher受控scripts+s04-deps，真实同子解释器metadata/import phonenumbers9.0.16通过；无安装。|正常续装/6框架测试NOT_RUN；不是新的Native或GPR失败。|
|GPR-02|原只外层traceback，缺cause/有效context。|7f7849c bounded链；最终P/T含精确LookupError→ValueError、context/fromNone、cycle/depth/frame、serializer与writer故障组合，15diagnostic纯测试PASS；原对象保持。|纯合成限定PASS，不代表真实业务/框架。|
|R12-RENDERER-SCHEMA|新增renderer三个int未入离线reader optional类型。|642a75b加非负int/null校验；1测试含18子边界PASS，拒bool/str/负数。|仅schema，不代表renderer真实退出消费。|
|R12-BROWSER-REDIRECT|旧未运行草稿误认为Firefox route可拦redirect；既有NetworkObserver183/450行反证。|逐上游route.fetch redirects0/retries0+预算，手动RAM Location freshGET逐hop守卫；POST307/308不重放。18fakebrowser/family+11fakeHTTP PASS。|旧草稿未运行无漏派；新真实Firefox/redirect层兼容NOT_RUN。|
|R12-BROWSER-SECRET|Playwright fill错误可带真实密码进异常message。|边界先结构primary后固定fromNone，密码sentinel纯fake覆盖，raw/最终error无泄露。|driver DEBUG等环境未guard；浏览器整体未准运行。|
|R12-FAMILY-ACL|patient clinical不是S04doc open；底层source/payment即manager也无readACL，空域不证明非空家族财务正例。|正常新对象family六步工具、nativeAccessError guard、family专属空域与name/id核同，fake断言通过。|真实family/alias/非空经济/finance混源分支NOT_RUN。|
|R12-PDF-HTTP|固定core minimal_layout含远程CSS/JS；Qt内部retry/redirect硬上界不明，不能推0或预扣任意50。|d30682a exactSettlementScope inline无资源正常addon extension，字体5s/wkhtml30s/私有temp/退出诊断；8purefake PASS。|新PDF/中文逐页/E均NOT_RUN；父renderer Native/REAP_FAILED→STOP消费仍待补。|
|R12-NATIVE-DBSYSTEM|core启动_create_empty_database先连db_system，默认postgres；同目标OperationalError仍可fallbackpostgres。|ownedCLI显式同目标为未运行工具候选；源码审揭示fallback仍需严证。|R1.1隐式system连接实际计数/库UNKNOWN；不改旧显式维护账本，不执行新应用试探。|
|R12-TOOL-SAFETY|12:52:28.744Z真实testeragent errored：possible cybersecurity risk；末工具/命令未公开。|原始事件SHA/时间/turn元数据保全，主控+acceptance各自list_agents观测，HARD-STOP新文件封存；全部应用执行冻结。|包级BLOCKED，不重述/换执行者/工具/人工转发绕过；非产品运行FAIL/Native。|

最终P d30682a6c9c12b47d8df16609100c1452d9207a7/T642a75ba0ad6b6c4eb795a9a2c9ca7f0406125ca，实际24纯离线断言PASS。源码AST27份前后同；历史51与开发期快照各自保留。不因本轮补报告重跑业务。

## 2026-10-17代码返工 TR-01—04（SOURCE_AND_PURE_OFFLINE_ONLY）

|ID|原缺口/首异常|实际修正与复测|剩余边界|
|---|---|---|---|
|TR-01|renderer已有CRITICAL事件未进入check/wait；STOP保存失败后实例关闭可丢内存冻结。|ProcessEvents+bounded incremental sealed reader；统一check/wait/close与预算前check；进程级首故障latch。最终100中的24guard/env及真实observer→consumer fake链通过。|真实进程、PID/reap、Native捕获及业务派发未运行；日志UNKNOWN不是Native猜测。|
|TR-02|正常业务拒绝也默认写完整chain/stack。|真正预期只短event；程序/证据或不确定包装及显式调查保primary-first boundedchain；9TR02+旧GPR02等在最终同一candidate重跑。|真实RPC/事务/审计仍NOT_RUN，不改原异常。|
|TR-03|202行customrenderer无真实兼容证据，fake未覆盖原生空recordset调用形状。|收缩为原生两方法委派/观测；同env、actualref/args/result/exception、负/正/unknowncode及property证据错误；原件不重生。|真实PDF/中文分页/MRO/内部HTTP/双E待原AC；正码1只保守暂停，不称产品FAIL，PID/reap UNKNOWN。|
|TR-03-FIXTURE|开发首次25纯测试有5例fake len/id接口不符。|修测试替身与固定core真实调用形状；原FAIL保留，开发25复跑PASS及后续3不拼最终统计。最终统一100候选全过。|这是测试替身问题，不写真实Odoo失败/通过。|
|TR-04|driver可继承DEBUG/PWDEBUG/DEBUG_FILE等；browser_phase改全局DEBUG。|启动前严格ambient白名单拒绝+Firefox localenv复制；移除adapter全局DEBUG；最终候选纯环境与fake运输回归通过。|未来coordinator需已在最小白名单env；driver真实运行NOT_RUN。|
|TR-04-CLI|原nativeCLI同target system连接失败会fallbackpostgres，且目标丢失可能CREATE。|固定core源码说明并列具体未来资源差异，未patch core、未放宽guard或实际连接。|运行前仍需明确system连接与禁止建库的合法准入；本轮不准运行。|

安全拒绝事实仅继承既有记录，不重复取证；代码缺陷与缺运行证据分列。最终P ad7d5311dbe7efe687a1dd00776eee8083879541/T984db5ab011602547405bd32f5c7c9c6b7d852bb，统一100/0skip/0forbidden，仅开发/主控pure自测，独立acceptance审代码与覆盖，原tester不替代。


## TR-01 框架调用者适配 / YD-S10-LC2-CODE-REWORK-20261017-02

父owner不跨解释器，原实际HttpCase.url_open在发送前无合法owner。现父路径保留owner，框架入口使用自身一次grant、固定身份/候选/用途、原共享账本及自身日志/STOP；不改Odoo或业务语义。P `cf5d63fe510b52ea150d07495bf3062f4ce0961d` / T `83e14b75e29aa49ceff26410236df13424f30163`，最终150纯检查全过，原100 IDs保留。开发142的1error系close重复原生冻结，保留失败并修正producer→Native→framework顺序，146开发及150固定候选区分。六项真实框架和S10仍NOT_RUN；SOURCE适配不代表应用准出。完整增量、边界和证据见acceptance-matrix.json::tr01_caller_adapter。
