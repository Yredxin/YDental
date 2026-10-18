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


## FRAMEWORK6 原生集成验证 / YD-S10-LC2-FRAMEWORK6-20261017-01

TR01源码接受后在现scratch第一次真实运行五TransactionCase+一HttpCase，共6/0fail/0error/0skip、exit0，native请求确实到达并返回原生AccessError。原六测试及断言未改，不重开TR01源问题。必要新profile把旧epoch/授权/root和新两小时/单scratch/局部预算分开，累计计数继承，旧STOP不动；静态审修正canonical构造及deadline后保primary，不重跑150。后处理一次hash域前缀假设错误已修并保存第一回执，不算原生测试FAIL/不补跑。原生依赖WARN保留不宣称无warning，本限定任务不扩产品维护。全GPR UI/403/409/303、A—E、PDF及S10仍NOT_RUN/BLOCKED。


## MAIN-A限定执行 YD-S10-LC2-MAIN-A-20261018-01

- 取证后处理datetime序列化TypeError：仅RO关闭后发生，保留首次脚本/失败，改为ISO8601后第二RO保存PASS。消耗两条RO，不伪称一次或业务失败。
- LOGIN_INPUT_UNAVAILABLE：未提供当前正常授权登录/provider；旧被拒账户材料不接手。A-STATE通过有限基线，A-EDITOR/A-ORIGINAL仍BLOCKED/NOT_RUN，工具静态准备不替代真实验收。


## MAIN-A DEV-TEST-AUTONOMY / YD-S10-LC2-MAIN-A-20261018-02

- 已解决LOGIN_INPUT_UNAVAILABLE：标准ORM准备必要既有用户7/5，用户7正常原登录表单真实HTTP认证成功；没有改业务资格或读取旧被拒材料。
- 入口已整理为MAIN-A-DEV-AUTONOMY-1.0，旧AGENTS原字节归档。150纯测试/六框架既采不重跑。
- 普通preflight猜login前缀失败已保留，使用当前非敏感合成显示名/权限及克隆来源确认，不猜权限。
- 首服务SOCKET_READY_BEFORE_RUN_START导致提前隐私证明失败；清理SIGINT/-2后二级缺日志STOP。修复3dc91ed等待真实start/level并保留60s边界，四小型合成边界及后两服务准出支持。仅本轮误触STOP原字节归档，有明确回执；旧STOP不动。
- A-EDITOR具体阻断：私有HTTP runner错误断言switch.result=accepted，而现控制器仅返回revision；在acquire前失败。团队可避免断言错误，已修私有源码但四Odoo额度耗尽，NOT_RUN，旧editor7/session109仍过期未release。不得归因密码/产品权限。
- A-ORIGINAL具体阻断：唯一Firefox launch Error，context/工作台点击/原件GET/下载/视觉均0，具体原因/内部PID退出UNKNOWN；启动Error文字未留是工具可诊断性限制。Firefox1额度耗尽，不换浏览器/工具或直接GET替代。
- 实际隐私缺陷：base res_device INFO在本轮normal login记录一次session标识前缀；raw0700/0600私有保全，未公开值/行/摘要。http.server CRITICAL证明不足覆盖该logger，不称绝无token日志；未见密码输出证据，不称外传。抑制修复和运行回归NOT_RUN，当前无应用额度。
- 终核60表1034行/93模块、旧1178审计、正文/版本/作者/费库账款/原件及四mutex同基线；新增认证配置、native登录/device各1、session110及3个S01认证/切店审计明确分列。A组/S10/生产不通过。


## MAIN-A ENGINEERING CLOSEOUT / YD-S10-LC2-MAIN-A-20261018-03

- 实际runner契约已修并入版本：switch仅revision，刷新access后用原生session_info核uid7/store1/revision1；错误/过期revision或身份/店铺不匹配不acquire。15项相关离线回归执行真实controller/service片段和原生JS查询生成函数，PASS；仅该范围，不与旧150/六原生结果叠加。旧失败runner及未运行修正版保留。最终T `f90ad2ab48e922f3e45caff6fe95d1f3d4470bb5`，实际编辑执行T `24f9e84156a1c4c9deee7a2d2d13b71000f7508e`；后续仅翻译边界/相关测试改变，编辑与日志源码相同。
- 无凭据诊断首失败是supervisor注入PYTHONFAULTHANDLER=1与诊断worker局部环境契约不一致，在driver/Firefox前退出；保留首异常并保守计一次诊断尝试。另离线核真实DEBUG退出格式并修parser，Firefox子进程定向接项目既有库目录（不改driver全局白名单、不安装依赖）。第二次空白页诊断PASS，实际Firefox PID1526959退出0/signal null且已不存在，0业务网络/0provider。旧-02仅Error的根因和内部PID/退出仍UNKNOWN，不能把本次配对/库加载观察倒填成历史根因。
- res_device真实logger为 `odoo.addons.base.models.res_device`；本任务本地配置WARNING，合成敏感INFO抑制而ERROR/普通日志/审计保留。两真实owned服务在run.start、socket及actualPID/logger30/configSHA证明齐备后才准入；实际用户7登录新增native device记录，两个新native日志敏感marker均0。core、设备及S01认证逻辑未改，旧受控日志不删、不公开原行/标识/凭据摘要，不宣称历史绝无泄漏或已外泄。
- A-EDITOR已真实完成：用户7正常HTTP登录，合法新连接acquire后用本次返回令牌release（令牌仅RAM），两HTTP200。独立RO确认旧过期editor失效审计、acquire/release共三条，文书编辑字段合法清空，四mutex各+2；正文confirmed/v4、作者/负责人7、版本9→10及费库账款/库存/原件保全。未重复编辑、改正文/负责人/权限或密码。
- **A-ORIGINAL仍未完成，团队测试工程遗漏：** UI1 Firefox/context成功但用户名fill超时，本地MAIN_A_BROWSER_REQUEST_FORBIDDEN/pageerror，6GET200、尚无认证POST/原件GET。首次修复只核LocalizationPlugin的默认 `/web/webclient/translations`，窄接hash/lang后离线及交叉审通过。UI2再次出现用户名fill超时，同时有GET/OTHER_ROUTE/同boundary拒绝且upstream_attempted=false；再核发现已装http_routing通过get_frontend_session_info实际覆盖translationURL为 `/website/translations`，原生插件优先此配置。未保留两次被拒确切URL，故具体route仍为源码执行链支持的推断，不能冒实测；UI1表单hidden同为源码支持推断，实测仅fill超时等。修复漏审动态配置，验收准出也未覆盖该继承链，不能归因用户密码、业务权限、产品拒绝、Native或平台安全拒绝。
- 两次真实UI额度耗尽，服务均正常退出，不第三启动、不热改/换工具或直接GET冒UI。原件点击、GET、下载、完整性与逐页查看均0；仅留存原件继续同27665B/application/pdf/固定SHA。未来最小源码修正应同时覆盖03专用和generic浏览器GET两层的exact `/website/translations` 及真实hash/lang形状，不能泛放 `/website`/RPC；本轮未生成未经运行替代候选。最终独立验收仅接受STATE/EDITOR及工具修复的实际层级，整A/S10/T12/生产不通过。


## MAIN-A ORIGINAL-UI / YD-S10-LC2-MAIN-A-20261018-04

- 有效模块覆盖与两层白名单：共享main_a_get_rule，真实http_routing覆盖和JS producer/最终_request_allowed相关9项离线PASS；实际Firefox /website/translations已准入两层并尝试上游，response未观察。旧03确切被拒URL仍UNKNOWN，不倒填根因。日志仅静态路径/模板、键/形状/阶段/状态，未采完整query/DOM/HAR。
- 首失败 TESTER_PRIVATE_INITIALIZATION_OMISSION：私有初始化漏建run/diagnostics，既有敏感日志证明handler按预期拒绝路径，PID1558643 exit255，未加载凭据/浏览器/HTTP。原STOP/初始化/approval保留，目录唯一最小修复和失败后独立RO通过，不清账或设通用ignore。属于普通配置错误，不冒Native/工具安全拒绝。
- 第二失败 NEW_READINESS_OBSERVER_TREATED_CONSUMED_BOOTSTRAP_AS_INVALID_CONFIGURATION：原生session.js导出后delete全局bootstrap，新observer仍读该全局并误判缺失语言；空HTML lang本为正常布局。首失败发生在fill前，页面6个响应200/0pageerror，translation请求未获response；后续route异常不能冒白名单首因。团队含前置验收漏审生命周期，属于可避免测试错误，不是用户密码/权限/产品拒绝。
- 两Odoo额度耗尽并均退出；后修只能离线审查，不声称真实浏览器已过。实际执行T ee73081c09f06e7bae5bc5660061d6391ef977f5。用户5 provider程序读取1但fill/POST0，用户7和编辑动作0；原件点击/GET/下载/文件核验/逐页全NOT_RUN，不用旧副本或HTTP替代。
- 末次独立RO39域750行及93模块、身份权限/文书版本作者/费库账款/原件/编辑清空/六已采审计保持，新增认证/会话/审计0。新增资源2/5/7/1/0，累计10/30/32/6/0，A/S10/T12/生产继续BLOCKED。

- 后修工具T `4ff3ccf754f30abab25451d085e65d1a79f4d219` 仅OFFLINE_ONLY：通过原生已导出模块读取白名单配置，未观测等待、空html lang正常，非法lang/route仍在最终gate拒绝。新增8项+受影响原9项=17离线PASS；没有额度作原生/UI复验，actualT ee730及NOT_RUN下载状态不变。
