# DL-P4：经营报表查询与过滤区

`[CODEX-FINAL] YD-S13-DL-P4 / 1.0`

技术：**TECHNICALLY_COMPLETE（限定P4软件，未实现者本地总签已实际完成）**；同步：**SYNCED**。首业务/main两ref、13份完整正文与唯一P4评论及旧内容/Issue状态已实际读回；本提交仅同步元事实，不是新产品或业务重跑。
用户亲手效果：待确认。P1—P3保持原TECHNICALLY_COMPLETE / SYNCED，不重开、不重跑历史全套。完整S13未完成；#37 OPEN、#36 CLOSED。P5—P6、产品合并、部署、生产、负载/恢复/实机、正式政策、S11组合扫码及真实患者资金/外部通道仍未启用。

## 完成范围与候选

依据用户完整[P4计划](../../execution/S13_DL_P4_IMPLEMENTATION_PLAN.md)连续W0—W4，仅整理`/ydental/reports`原查询form。完成局部杏陶暖白、相对字号/Grid/Flex，指标/法人/适用币种/状态同一单选实现，原生日期输入，以及默认可见的授权门店原生勾选列表、必填/焦点/忙碌/原生降级。没有新指标、筛选维度、公式或业务能力。

开工实际本地/远端P3报告均`aa04988be1d39d6dbcc20f24e023542b57a66ee7`，工作树clean、incoming.diff0B；P3产品`b72bcd6d125aad45bf8e62fb7596d5bb5725ac13`、旧回执6392314778保持。正常承接分支`codex/s13-dl-p4-report-filters-r1`，未reset/clean/强推或从文档main重建。旧P1/P2回执6384111913/6391318665不改。

|对象|实际锚点与证据边界|
|---|---|
|准备/公共阶段工具、真实before执行|`fb9ccaa2c10a77a17d90f322989af102a76ed6c4`；addon仍P3|
|首次必要加载及12指标原对照|`f0f2898db80276114b7c24d96e490631502db475`；独立提前发现的两个隐藏inline翻译词条已修后才加载|
|指标重复导航修复/真实事件回归|`fa26944d2482e832064197264ee9366768f0da45`；Tab确认紧接Enter由双GET改为唯一原3参数GET|
|窄屏间距/双引擎正常功能|`409e9aa1f6177c84a9c70e852b2aa5a9547b1fe5`；media优先级修正，真实WebKit17项及正常退出另核|
|原生勾选框默认边界修复|`61d044d5a986c0f9f10263424c995eb92f8c5494`；随后真实hover仍2.812:1失败，未作最终通过|
|最终产品/运行绑定|**`85b62b43cf7cda889e20663662ae86484a55f032`**；仅在61d把普通checkbox轮廓换既有accent色，焦点/原生语义/JS/尺寸不变|
|文档运行checkpoint|`b586d55`只CURRENT，满足既有clean启动检查；不是新产品或测试结果。最终85b为其正常前向后继|
|锁定core|`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；实际无core diff|
|报告HEAD|后续仅同CURRENT及三报告；以最终远端ref和唯一P4评论实际读回为准，不当新产品|

六个addon产品文件：原form XML、manifest两资产、7新PO、原reporting.js最小幂等/导航保护、新report_filters.js与SCSS。最终与P3相比，整个模板排除唯一filter form后其余原字节完全同；原reporting.scss未改。报表页头/导航/结果/范围/汇总/明细/分页/export hidden/钻取/错误模板，P1—P3及后台controller/service/model/ACL/schema/字典/PDF/其他岗位/全局品牌冻结。只允许form自然增高产生纵向位移。

root统一环境/运行/集成/报告，report_filters唯一产品实现，p4_tester私有工具/真实浏览器，acceptance未实现产品或测试工具，独立核实际请求/原图/原文件/新physical RO/包与同步。同OS共享，不冒隔离。

## 字段、文案与事件契约

|字段|来源及保留语义|
|---|---|
|metric|原`_options()`授权choices/原顺序与controller既有优先级；native select唯一具名值|
|date_from/date_to|原values、type=date、required；当地业务日期，未转换UTC输入/改成治疗日或历史余额截止日|
|store_ids|原`_selection_options()`active/company/source权限筛选及原label/timezone/order/selected；multiple为唯一提交源，checkbox无name，每选值恰一次GET repeated参数；不切工作门店|
|company_id|原授权法人候选，空值仍所选授权法人范围，不扩大集团|
|currency_id|只在原money条件渲染；空值分币种合计、不汇率折算|
|state|只在原states条件渲染；保留领域key/标签，不解析翻译文本或统一成完成|
|revision/查询|原scope revision唯一hidden，普通GET带原字段；指标change仍仅metric及两日期，认证/参数策略不改|

新增7条中文实际loaded逐节点匹配：至少一家及不切工作店帮助、至少一家错误、当前指标无可选店、指标重查/重置说明、其他草拟条件与上次生效范围说明、正在查询、通用可用选项错误。原字段/选项/业务说明不删除，重要提示默认可见。完整映射在包内copy-map.json。

候选移动/hover/Home/End不提交；Esc及外部点击取消，选项点击/Enter/Space/Tab确认。指标确认不同值只派发一次旧change导航，保留日期并由服务器恢复当前店/清法人币种状态页码；pending期间阻止旧页紧接Enter覆盖导航及重复change，pageshow/reset/有限超时恢复。其他字段和门店仅草拟，明确查询才生效；原结果/export hidden/分页及钻取链接始终按上次服务器结果，不被草拟控件改写。0店由原required拦截并聚焦可见控件，不默补默认店。busy只禁无name控件/按钮，具名提交字段保持enabled。

## 真实软件证据与影响复用

见[14项矩阵](acceptance-matrix.md)、[脱敏证据索引](evidence-index.md)。以下层级不混用：SOURCE/PURE、DOM组件夹具、正常HTTP、真实浏览器、native AX、独立已提交RO。

- reader16真实授权店1/2，12指标普通HTTP均200。固定店1/2026-10-01..25的before与f0完整JSON逐原字节核，仅typed `filters.query_at_utc`精确一次不同，其余所有源行/数值/单位/状态/日期界限同；当前全部真实一页。不把源行数当去重患者数，不硬编码1303证明公式。85b后端/字段字节相同，明确按影响复用；未冒最终重跑12指标。
- fa269实际core/edge覆盖各单选确认取消/Tab/ShiftTab/Space、0店错误焦点、两店真实GET每值一次、实收/实退/应收三USD查询及原钻取返回、非金额字段缺席、busy/历史返回。最终85b实际五视口native字段/FormData/授权候选/旧生效结果及内部computed对照同，新增样式仅局部；已生效export/分页/drill参数不混草拟条件。
- UID5既有source+exportWRITE正常导出实收2349B/3源行、到店8181B/27源行，两CSV全11列/原序/值与固定before完整JSON逐项同，仅query_at分类。只读派生，不是新业务原件；CSV不进效果包。原钻取/返回范围同；实际一页不冒多页。
- root实际11后端例：1×200、7×403、3×409，包括普通源正例、无源、医生越财务域、既有店142越界、无效店、旧revision、非法法人组合、过长state、非金额带币种、reader只有exportREAD无WRITE拒绝、真实无源HTML不渲染filter/candidates。未改授权。export-only无源及通用撤复权完整矩阵明确复用[固定S12 T06](https://github.com/Yredxin/YDental/blob/aa04988be1d39d6dbcc20f24e023542b57a66ee7/docs/reports/s12/acceptance-matrix.md)及未变源码，不冒P4重授/撤复全验或新测export-only。
- 真实Chromium **156.0.8078.4**及WebKit **27.2**原厂引擎。WebKit409实际17功能/正常退出，最终85b又真实核勾选default/hover/focus、Space/Tab、多店GET、390/320、原生zoom2/独立root32及长值本地阅读。最终两engine边界真实像素最低：普通5.950、hover4.938、keyboardfocus7.209；实际帮助等文字最低5.613。未拿UA computed0px冒边界证明，不宣称全站WCAG认证。
- 五视口1366×768、1440×900、768×1024、390×844、320×800；最终root16宽padding24/窄16px。Chrome/WebKit原生200%zoom与独立root字号200%分列。Chrome新capture-only真断言aria-expanded与listbox在CSS683×384内，再采原viewport；旧focus-only图仅布局，不当popup PASS。原生CDP AX不冒真实屏读/设备。
- 长文字、无候选、额外required及初始化插入失败均明确DOM组件夹具，未改DB/业务值/授权。禁JS同一自有禁JScontext通过正常HTTP表单/CSRF认证及真实UID16后正常菜单和原生form查询，不复制会话/开JS；不宣称原生登录页无JS可见输入已修。初始化失败真实native回退查询另列。
- 文书P1—P3原字段/区域及结算/仓库computed/代表PNG对照保持；普通doctor双选择器取消/确认和显式preview实际200，无新原件。preview后全文/时间保存，但P4没有before全文，不声称本轮归一化全文同；源/模板与代码冻结，P3完整已验事实不回签为P4新测。

## 完整保护、加载与停止

唯一既有合成目标`ydental_s11_synth_20261023_01 / OID2171423 / cluster7694897083368259627`及原filestore。初始独立新physical104731的145业务/13技术/83实际文件与P3最终九区段完全同。没有新增/复制/改名DB、改变五项高权、core、odoo-12或共享OS/网络/集群策略。

唯一必要`ydental_reporting -u`在f0执行，即时完整pre→实际exit0/ERROR0/noNative→完整post；业务145表和83文件全同，仅5技术表差异。后续JS/SCSS按实际新bundle/computed验证，未重复-u或重放旧业务。普通报告提交不重执业务。

末服务停止后root完整snapshot SHA`7624755f5e8a7a594cf8da5da0021cbf53826028934da23583a5a6c4f246b101`；未实现者新physical **122676**/RO-RR/实际0，145/13/83与root九区段逐值同，独立保护SHA`e326304d2f9a211cf9b12ea5cbdeebd17e29d501ca8a51f36c0893f24140ea5b`。65内部+2外部原件、作者/身份/价源/金额库存/旧审计/未完成责任与83实际bytes/size/SHA保持。P4新增原件/PDF/打印/签署/发布/经济库存0。固定旧来源1073+前批230=1303、P4贡献0；lot253仍收10/用2/余8，不把以后全部查询硬设1303或假结旧责任。

非全库物理零diff：225条正常新增accepted审计（112report.view、10drill、各32login/scope/switch、2export、2inventory、2invoice、1document），旧行无改删，其他144业务表同。HTTP拒绝请求的真实状态另证，不虚构新增denial审计数量；无临时授权/恢复fence。5技术表仅write_date及view1623本页arch_db，无行增删。配置/schema/index/其余文件区段同；正常web资产与认证/session技术材料不混成新业务原件。

末本人owned run`20261025T034737Z-fb5ad29edd87`于 **2026-10-25T03:50:49.493448UTC**正常child0/signull/进程组停止。全部browser正常关闭、P4新profile空，active absent、18411/18412无监听、目标其他连接[]（独立另physical122886核）。未操作共享主服务。P4新scope至14:40:45UTC未延长旧scope/STOP；不是在线承诺。正常复开须核真实目标/权限/owned/固定候选/fresh准入和有效scope，不复制会话，也不为交报告重新启服务。

## 原失败、修复与限制

真实失败和普通错误均留原source/command/exit，不以29个有限客户端或截图数量代表完成：

1. SOURCE预审发现外部高亮被误确认，改为P4外部取消；两个hidden inline词条与Odoo真实提取不匹配，最小block节点修后7新词全部匹配，尚未-u前修正。
2. f0真实Tab确认后Enter双GET使旧导航ERR_ABORTED；pending guard修后fa真实一次原3参数GET通过。旧client2不反签。
3. 窄屏padding被specificity压住24px，409最小media修为16；WebKit UA未选边界原1.591失败、61d默认轮廓hover真实2.812失败，85b最小accent修后两engine三态真实像素达标，旧图/失败不抹。
4. JSoff旧helper等待隐藏原生login form超时，原owned日志仅GET200/无auth；同禁JScontext正常HTTP表单认证后原生查询通过。不是无源后台拒绝，也未改登录或安全。
5. WebKit首及85b一次minimalJS真实404/空body，均pre-auth且native0；同URL技术asset真实存在/39819B SHA`cef8327be567721cdd09c79d4543715931e84ec836fa5540b5bfb08222265ad6`。只变正常owned进程生命周期后同原入口恢复并完成实测，原因仍UNKNOWN，不声称清缓存或已修永久根因。
6. WebKit旧轮17功能完成但全局原生boot翻译错误使Node2；旧错误无phase，具体原因UNKNOWN。最小同入口probe抓到旧/login期间正常/odoo导航被测试goto取消；只修私有post-login导航绑定/原后台就绪等待，原入口/账号/UA/driver/CORS/security不变，之后真实功能client/native0，不以此倒签旧translation根因。
7. Chrome原nativezoom取图浮层已被scroll关闭，旧图只证明布局；同产品最小capture-only settle+展开/bbox断言补齐，不改产品scroll取消。首次evidence目录775、比较/索引schema KeyError、E2BIG、未dispatch工具返回等普通问题原事实保留，未放宽检查或换入口绕拒绝。

320报表整页scroll346/client320仍为旧限制，文书旧345另来源；本区不新增根溢出，不称整页移动端完成。WebKit不等Safari/iOS；日期仍原生日历，跨OS弹层未统一。nativeAX不等屏读，自动化浏览器不等用户可接手窗口/亲手验收。Firefox中文字体、Native139、历史WebKit初始化404及其他UNKNOWN保留；正式经营/临床政策、完整S13/负载恢复与生产未启。

## 私有包与普通角色复现

私有0400包`.local/dl-p4/viewing/S13-DL-P4-view-only-20261025.zip`：**3,563,718B / SHA256 `c13f03f417b9ea39476c9064714175dd7e60ca67c9405c4192e862050b948a72`**。44成员=39原PNG（37不同SHA，不冒39业务场景）+README/copy-map/screenshots.csv/preservation/manifest43非self；0PDF/业务CSV，无秘密/session/profile/raw请求/配置/程序/字体/备份/83原文件bytes。全部成员bytes回读、PNG全解码及原源SHA同；五对前后相同角色/条件/视口，但scrollIntoView取景不同且before未存scrollY，非像素对齐或整页逐像素审计。包不是完整数据库保护重签材料。

正常复开后8步（不承诺当前在线）：

1. 获准普通读取岗位正常登录、选择店A，从报表菜单进入。
2. 选实收及既有当地日期，阅读合成/口径声明。
3. 展开指标，用方向/Home/End移动、Esc取消；确认新指标核日期保留及其他条件按原规则重置。
4. 勾选两家授权店，不切工作店；清空后查询见错误，再恢复合法范围。
5. 设适用法人/币种/状态并明确查询；草拟前不把旧结果/export/drill当新范围。
6. 原入口钻取旧源并返回原生效条件；当前真实一页，不冒多页。
7. 仅有源且有exportWRITE岗位从原入口导出CSV；只读源权限不是导出WRITE，不生成原件。
8. 用390/320、键盘和放大读完整标签/浮层，参考明确标注的原生降级图；不提交打印、生成或经济库存动作。

未实现者本地总签已实际完成，SHA`15c3770c2736735518f9e1878a9df9b3185d2ceb3ebca0dc5182643b371df62c`，T01—14适用本地技术通过；其签名当时remote NOT_RUN保留，不预签未来。独立包/总签与随后真实远端同步分别留证。首业务99e31246ca596fb2297eda2391bd0a4677392402/main d093bc65cb623b8c65f4bff786a0c627281c7266及13正文bytes/Gitblob已核；仅新增[#37 P4最终评论6393235980](https://github.com/Yredxin/YDental/issues/37#issuecomment-6393235980)，全文读回/旧内容/两Issue状态同，首完整同步SHA`e6f22cdea753f8641e13c3c6d9b80980a0a638d9aeac1ace0748571313cecb0b`。本次仅4文档元事实，最终报告HEAD/同评论与独立远端另实际核，不由旧本地总签预签。阶段只在最终正常push/正文/状态读回；#37仅一份P4结果保持OPEN，旧回执及#36不动，main只必要两路由文档，不合产品、不部署。交付后停止P4，不自动P5—P6。
