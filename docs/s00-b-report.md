# 交付验收申请｜YD-N1 R1｜S00｜S00-B

任务：[S00 #24](https://github.com/Yredxin/YDental/issues/24)，总计划[#23](https://github.com/Yredxin/YDental/issues/23)。来源：用户在本次新会话明确接续已获授权的S00-B；既有授权交接见[GPT-RELAY](https://github.com/Yredxin/YDental/issues/24#issuecomment-6106434172)。本报告由Codex提交，不代用户验收或GPT技术复核。

**本批最小入口、翻译、全新隔离库安装/升级、访问鉴权和真实中文PDF已完成本地验证，申请技术复核与用户效果确认。自动浏览器截图BLOCKED；Project/T05独立BLOCKED；整个S00未完成。**交付后停止，不关闭#24、不创建/合并PR、不进入S01、不发布生产。

## 依据和固定版本

2026-10-11 UTC先完整读取#23/#24当前R1正文及#24全部4条既有评论，包括[S00-A固定交付](https://github.com/Yredxin/YDental/issues/24#issuecomment-6106275677)、[技术复核](https://github.com/Yredxin/YDental/issues/24#issuecomment-6106335585)及恢复交接。没有回读旧四份文件或撤销需求补业务规则，没有重做S00-A全量核查。

衔接检查：实际pwd与Git根均为`/home/redxin/code/odoo/odoo-sd/code/sd-addons`，origin为Yredxin/YDental；初始分支`codex/s00-a-r1-20261011`、HEAD `57f4838c90db8d7e3f719a5b81fc5a217e402791`，工作区干净。由该基线新建`codex/s00-b-r1-20261011`，保留原分支，未reset/覆盖/强推。

最终运行采用固定实现提交`f957313`（完整SHA、addon tree及各轮退出码在[summary.json](evidence/s00-b/summary.json)）。最终报告/证据提交是其后续提交，未再修改addon或运行工具；最终固定SHA及远端读回由#24交付评论给出，避免提交内自引用。

本批改动：入口文案/翻译、固定合成PDF与渲染鉴权、9个HttpCase方法、当前隔离运行/探针/护栏/HTTP工具、当前批次入口文档和脱敏证据。模块目录、现有外部标识、LGPL-3及历史资料保留；没有新增未来业务模型、患者/预约/临床/费用/库存功能。

## 新会话执行条件与保护

[预检评论](https://github.com/Yredxin/YDental/issues/24#issuecomment-6106532401)已写入并读回；[运行进度/失败补交记录](https://github.com/Yredxin/YDental/issues/24#issuecomment-6106625341)已写入。没有沿用上次会话只读/工具拒绝作为本次事实。

|检查|本次实际结果|证据与范围|
|---|---|---|
|Codex/权限|CLI 0.162.1；会话提供danger-full-access/approval never|未改全局Codex或安全配置；权限声明与操作实测分别记录|
|仓库写能力|唯一临时文件独占创建、写入、读回、移除PASS，退出0|文件名及结果见preflight.json|
|测试端点|127.0.0.1:5432 TCP及维护库postgres连接成功，退出0|仅查维护库和catalog；不读既有业务表|
|GitHub|正文/评论读取、预检及进度评论写入可用|预检评论已读回；最终交付另读回确认|
|底座|Yredxin/odoo@f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb；源码声明20.0；Python3.12.15；PG18.6|fork无父根快照，不证明精确官方上游SHA相同；未换版本，最小运行实际通过|
|既有资产|核心tracked状态、父AGENTS/既有odoo.conf哈希不变；既有库名/OID保持；原业务PID42433仍在|protection.json；不是既有库逐行审计；未连接其业务表|
|现有DB发布|Docker仍映射0.0.0.0/::的5432|记录差异，未改变容器/服务，也不据此推定公网可达|
|本批本地依赖|只写sd-addons/.local/s00-b-deps|不改系统包、核心venv或既有服务；核心解释器不加本地PYTHONPATH时找不到新增验证包|

本批仅结束过自己创建的中间预览进程，核对其PID命令行和独立config后发送SIGTERM，为最终空库验证释放18079。没有停止初始业务服务或odoo-12。

## 实际隔离与依赖

最终库：`ydental_s00b_test_20261011073303_8137af81`。首次失败库`ydental_s00b_test_20261011071424_475acace`、中间验证库`ydental_s00b_test_20261011071740_fb7a15f9`连同创建记录、原始日志均保留，不删除或复用历史库。

[runtime-redacted.json](evidence/s00-b/runtime-redacted.json)给出最终创建时间/OID/cluster、配置哈希和无凭据选项。运行器在任何Odoo操作前验证：固定核心SHA；固定`127.0.0.1:5432/odoo`及cluster system_identifier；全新允许库名；本地创建记录与当前OID；配置哈希；精确端口及独占锁。没有删库、重置、接管旧库动作。

- 私有资源：`.local/<本轮库>/odoo.conf`、`data/`、每次独立日志、`access.json`；目录0700，配置/访问文件0600。
- 插件路径明确为核心`odoo/addons`、核心`addons`及本仓库；db_name为唯一库、dbfilter为`^唯一库名$`、list_db=False。
- HTTP只监听127.0.0.1:18079，workers=0、cron=0；SMTP指向127.0.0.1:1；没有配置短信/支付/生产外发集成。合成PDF内联布局不请求远程资源。
- 第一成功升级的connect系统调用跟踪仅观测到127.0.0.1的5432/18079，见upgrade-network.json。这是本次观测和应用外发关闭配置，不宣称已部署操作系统全局出口防火墙。

PDF依赖采用进程局部方案：从[官方wkhtmltopdf下载页](https://wkhtmltopdf.org/downloads)对应release获取wkhtmltox 0.12.6.1-2 jammy amd64，仅`dpkg-deb -x`解包；实际启动版本为`wkhtmltopdf 0.12.6.1 (with patched qt)`。从[Noto官方仓库](https://github.com/notofonts/noto-cjk/tree/Sans2.004)取得Noto Sans CJK SC Regular及OFL许可。PATH/FONTCONFIG_FILE/缓存只传给本批子进程，字体查询实际匹配中文字体。下载来源、哈希和初次许可证404补交保留于dependencies.json。Jammy包在本机Ubuntu26.04的本轮最小场景可运行，不泛称全平台兼容。

PyMuPDF1.28.2、Playwright1.63.0及Chromium build1243放在`.local/s00-b-deps/`；浏览器缺少的6个Ubuntu动态库同样只下载/解包于browser-libs，通过进程LD_LIBRARY_PATH使用，未安装到系统。补齐库后Chromium在`chromium_sandbox=True`下报`No usable sandbox`、SIGTRAP，启动命令退出1。未使用`--no-sandbox`、未变更AppArmor/用户命名空间或全局安全配置，自动浏览器截图到此停止。具体宿主安全策略来源未进一步证明；不扩大该阻塞到HTTP/PDF测试。

回滚这些依赖只需在本批进程结束后移除对应本地解包/缓存目录；保留失败证据、下载来源及报告。当前无需系统级依赖安装授权。

## 需求完成情况与API

|#24条款/功能|实际完成|实现/限制|
|---|---|---|
|B：唯一牙科入口|完成本地实现/验证|保留/ydental及原菜单/动作/组；去除旧P00和“基线就绪”验收暗示；中文菜单牙科、英文Dental|
|C：最小安装升级/访问|完成本地验证|最终全新库安装11、升级9项框架测试，均退出0；含非管理员、无权、portal、匿名及撤权下一请求|
|C：中文PDF|完成电子样张验证|A4及80×200mm，真实下载/尺寸/字体/文本及图像核验；不含实体打印/临床正式文书|
|F：英文源/本模块中文|完成本地验证|i18n/zh_CN.po；原生i18n导出24项源串全部有译文；含QWeb复合文本、模型/菜单和Python错误|
|G/F：日期/编号公共工具|完成限定验证|原生fields/ir.sequence，4真实连接并发100次；不建立自研未来编号服务|
|H/I：字典/动作/证据|完成本批文档|见下表和contracts；没有假称公共业务审计已经实现|
|D/E：Project/T05|BLOCKED，范围独立|本批Project读取/写入均未执行；不改字段、卡片、视图或自动化|
|浏览器截图|BLOCKED|沙盒启动拒绝；PDF渲染图已提供，页面截图/录像未生成|

调用依据核对固定核心源码：`ir.actions.report._get_report`、`_render_qweb_pdf`、`_get_layout/_get_pdf_engine`与base_report_wkhtmltox的实现；纸张orientation实际默认Landscape，本批明确Portrait；`fields.Date.context_today`/Datetime.context_timestamp取环境时区；`ir.sequence.next_by_id(sequence_date=...)`用于合成分配。精确位置在api-and-source.json。未新增旧式ACL CSV，未照搬旧group字段/API或改核心。

翻译导出曾使用当前核心已不支持的`--i18n-export`而退出2，随后读取`odoo/cli/i18n.py`，改用实际`odoo-bin i18n export ...`并退出0；失败日志保留。这项CLI纠正没有更换底座。

## 流程实际回放

|示例|合成前提/操作|实际|证据|
|---|---|---|---|
|S00-F1|S00-A衔接/Project|仅核实Git衔接及保留保护；不重做A、不执行Project同步|preflight.json；S00-A固定三表|
|S00-F2|最终唯一空库→安装→普通授权/无权/匿名→升级→中文样张|安装/升级成功且非零测试；授权200、无权/portal403、匿名303；唯一菜单；A4/窄纸下载成功|summary.json、http-pdf.json及两份PDF/PNG|
|S00-F3|UTC 2026-10-10 16:30；合成Asia/Shanghai→原生序列并发→双语/升级|门店合成日为2026-10-11，UTC日为10-10；4连接100次+预热1次共101唯一编号；升级后保存在原生测试快照中的旧编号/内部码及菜单动作ID不变；新号不重号|native-before.json、probe-before_upgrade.json、probe-after_upgrade.json|

Asia/Shanghai仅是本轮合成前提，未发布生产门店时区。编号以原生ir.sequence为被测公共工具，使用合成日期前缀；不是患者号/门店业务单据/叫号的已实现或集团唯一验收。

## TC及运行计数

|TC|结果|真实命令/角色|测试数/退出码|证据与限定|
|---|---|---|---|---|
|S00-T01|PASS，衔接/保护范围|git pwd/root/remote/status/HEAD；配置哈希与维护库catalog|核查退出0|protection.json；不重做A的50463文件全量核查|
|S00-T02|PASS，本地运行|s00_b.py install/upgrade，最终新空库|安装0 failed/0 errors/11 tests、退出0；升级0/0/9、退出0|9个HttpCase方法及框架汇总分别记录，入口一个；最终运行实现f957313|
|S00-T03|PASS|HttpCase普通授权/无权/portal/匿名/撤权；真实HTTP合成账号|包含在上述Odoo运行；HTTP检查另计22，退出0|匿名303登录；无权403；原生报告和自研下载都拒绝|
|S00-T04|PASS，电子PDF|真实HTTP下载→PyMuPDF→图像查看|A4/窄纸各1页，检查退出0|PDF/PNG、字体/文字/边界、原生下载权限；没有实体出纸或浏览器截图|
|S00-T05|BLOCKED|Project同步不在本批操作|Project mutation=0；本批同步NOT_RUN|沿用A的独立详情读取阻塞，不能报看板完成|
|S00-T06|PASS，已测护栏|s00_b_guard_tests.py，真实子进程及connect跟踪|14项拒绝用例均退出2；套件退出0|guards.json；错误端点无INET connect；OID/已有库检测仅访问维护catalog；前后catalog一致|
|S00-T07|PASS，已报告差异与最小API验证|锁定fork/版本，源码及本轮安装升级|检查/最小运行退出0|未证明官方同SHA；未静默换版本；后续模块兼容仍归责任阶段|
|S00-T08|PASS，原生公共工具限定|原生翻译提取、双语HTTP、时间工具、4连接序列及升级快照|24/24提取词条覆盖；100并发分配；探针退出0|translation-coverage.json、两阶段probe；不涵盖未实现业务编号|
|S00-T09|PASS，当前契约/证据|命名映射、字典/动作/删除保护文档；语法/XML/PO/凭据扫描|检查退出0|contracts.md、checks.json；业务审计/业务删除保护实现仍NOT_RUN|

计数按每次框架汇总报告；14护栏、22HTTP检查与原生探针另计，浏览器测试0（BLOCKED）。原始日志留0700私有运行目录；GitHub仅放脱敏摘要、日志哈希和合成样张。

最终命令由核心`.venv/bin/python`执行：

```text
scripts/s00_b.py install --db ydental_s00b_test_20261011073303_8137af81 --port 18079
scripts/s00_b.py probe   --db ydental_s00b_test_20261011073303_8137af81 --port 18079
scripts/s00_b.py upgrade --db ydental_s00b_test_20261011073303_8137af81 --port 18079
scripts/s00_b.py probe   --db ydental_s00b_test_20261011073303_8137af81 --port 18079
scripts/s00_b.py export  --db ydental_s00b_test_20261011073303_8137af81 --port 18079
scripts/s00_b_guard_tests.py --db ydental_s00b_test_20261011073303_8137af81
scripts/s00_b.py serve   --db ydental_s00b_test_20261011073303_8137af81 --port 18079
scripts/s00_b_http.py    --db ydental_s00b_test_20261011073303_8137af81
```

HTTP/PDF验证器额外以进程PYTHONPATH指定本仓库`.local/s00-b-deps/verify-lib`；不用该路径改核心环境。安装命令创建全新库，再次install会拒绝，不把本报告库名当可重建库。复现新安装需另生成匹配格式的唯一新名，沿用固定批准端点，不能复用当前/历史库。

## 失败及补交链

|失败/阻塞|实际结果|补交/当前处置|
|---|---|---|
|首轮安装|退出1；3 failed/0 errors/11 tests|修复语言激活、Portrait、无HTTP资源回调布局；失败库/日志保留；最终新库安装/升级通过|
|首轮原生探针|退出1：普通账号无权直接read原生URL动作|未扩宽原生ACL；翻译字段用管理员探针，普通账号经真实HTTP测菜单；后续探针通过|
|旧翻译导出CLI|退出2：no such option --i18n-export|核对实际i18n子命令后导出退出0|
|预览端口探测|退出2：TIME_WAIT被误报占用；ss无监听|SO_REUSEADDR排除TIME_WAIT；真实占用端口仍被14项套件中的用例拒绝；最终预览成功|
|HTTP文字断言两次|均退出1：CJK兼容部首/全角标点的抽取差异|同时记录原始和NFKC规范化文本；语义检查对预期/实际均规范化；PDF内容未为断言伪造，实际字形可读|
|浏览器|缺库退出1，局部补齐后No usable sandbox/SIGTRAP|BLOCKED；不绕过安全策略，未生成页面截图/录像|

Qt生成的ToUnicode映射将部分汉字提取成兼容部首；规范化前后文本均保留在http-pdf.json。视觉字形检查通过；正式文书/搜索导出对精确Unicode和辅助功能的要求仍须S12实测。样张只有固定合成文本，不是正式临床文书或可靠电子签名。

## 字典、动作及配置

完整公共模板仍在[contracts.md](contracts.md)，本批实际复用如下，没有自研业务字段：

|原生对象/字段|用途/本批值|来源、权限与保留|
|---|---|---|
|ir.actions.report：name/model/report_type/report_name/paperformat_id/group_ids|两份样张，model=res.company、qweb-pdf-wkhtmltopdf；无binding/attachment|模块XML；直接动作字段读保持原生管理员ACL；渲染另验内部+入口组；模板不读公司/患者字段|
|report.paperformat：format/page_width/page_height/orientation/margins/dpi|A4及80×200mm；Portrait；96dpi|演示纸张，仅技术配置，不发布生产设备参数|
|ir.ui.view/ir.ui.menu/ir.actions.act_url/res.groups|原入口ID不变，新增ydental_sample_*模板|英文源/zh_CN；组只控制技术入口，不是S01业务权限矩阵|
|res.users/ir.sequence/ir.config_parameter（仅测试数据）|随机密码合成账号、日期前缀序列、升级快照|仅新隔离库；无真实患者/员工/费库款；私有访问文件不上传|

|动作|前置/权限|输出与副作用|失败/恢复|
|---|---|---|---|
|GET /ydental|登录、内部账号且入口组|200双语静态入口；no-store；无业务提交|匿名303；无权AccessError/403；恢复需合法授权|
|GET /ydental/sample/a4或narrow|同上，纸张仅白名单|实际PDF附件下载；无数据库attachment/费用库存副作用|无权403；未识别纸张404；依赖失败保留日志后修复重测|
|原生/report/pdf、/report/html及私有报告方法|同一报告身份检查|本模块两份样张均受控|仅菜单group不可替代此检查；后续文书权限不由本组自动授予|
|runner install/upgrade/probe/serve|固定核心/端点/cluster/创建记录OID/配置/端口/锁|只运行本轮合成库；install独占创建；无删库动作|拒绝退出2；查看创建记录，不接管或重建已有库|

AccessError/HTTP状态承载本批框架拒绝；稳定结果词汇与未知结果恢复仍是contracts的业务动作契约。没有实现S01公共审计或未来业务事件，也未变更费用、库存、资金、正式PDF快照。

Project专项三表继续引用[S00-A固定报告](https://github.com/Yredxin/YDental/blob/57f4838c90db8d7e3f719a5b81fc5a217e402791/docs/s00-a-report.md#project前后核对)：Issue→item、阶段/状态、读回/二次核对。#24的历史item为`PVTI_lAHOA3_tu84BmcLJzg_8jDA`，当时物理Todo；这不是本批实时读回。当前执行状态以Issue启用/交付评论为准，本批Project三表均未刷新，不声称同步成功。

## 用户效果验证

入口：**Ubuntu本机 `http://127.0.0.1:18079/ydental`**。最终预览在报告交付时保持运行，仅监听回环；重启入口见上方serve命令。原业务8069不作为本批入口。

合成角色凭据仅在本机0700运行目录内0600文件：`.local/ydental_s00b_test_20261011073303_8137af81/access.json`。使用其中authorized_zh、authorized_en、unauthorized、portal条目；不把文件内容贴到GitHub。

1. 用新浏览器会话打开入口，未登录应进入Odoo登录页。
2. 用authorized_zh的本机凭据登录，再访问/ydental；应见「牙科」、欢迎语及两份样张下载按钮。
3. 从应用菜单进入牙科；同一语言下只见一个牙科入口。
4. 下载A4样张，应为1页纵向、中文标题/虚拟患者/12行/结束语完整；可对照仓库sample-a4.pdf/png。
5. 下载窄纸样张，应为80×200mm、1页，中文内容无明显缺字裁切；对照sample-narrow.pdf/png。
6. 另开独立会话，用authorized_en登录；入口/菜单为Dental，文案英文；旧P00文案消失。
7. 用unauthorized或portal的独立会话访问/ydental及两份下载URL，应403；直接原生报告URL同样403。
8. 退出后再次打开下载URL，应要求登录。用户在#24确认当前固定提交、步骤和实际/预期；Codex不代签。

仓库PNG为真实PDF的渲染图，已查看两张；没有自动浏览器页面截图/录像。临床正式模板、实体打印、浏览器兼容/辅助功能和用户实际效果仍待相应复核/确认。

## 回滚、未解决项与复核申请

代码回滚在工作分支revert本批提交，保留失败证据与报告历史，不reset/强推。结束预览时先核对`.local/<最终库>/serve.pid`对应命令行确为本批独立config，再仅结束该进程。三个新库和日志长期保留，不提供自动删库/清理历史失败证据的操作；原服务/核心/odoo-12无需回滚。本地依赖目录在本批进程结束后可移除，不涉及系统包卸载。

未解决事项：Project/T05仍需完整自动化配置读取能力，且本批禁止相关写入；自动浏览器截图需要支持Chromium沙盒的执行环境，当前不请求关闭安全控制；精确官方上游SHA映射未证明；未来业务、正式文书/打印、生产参数、持续备份恢复均未启用。

申请GPT复核本批固定提交及真实证据，再由用户按上述入口确认效果。当前不需要系统依赖或既有服务变更授权；如要求自动浏览器截图补交，需另提供支持沙盒的浏览器执行环境。交付评论写回并读回后停止，不自动继续其他批次。
