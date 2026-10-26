# DL-P10 经营报表主页面动作、SVG与间距实施结果

[CODEX-FINAL] YD-S13-DL-P10 / 1.0

技术：TECHNICALLY_COMPLETE（限定P10软件；本地未实现者最终总签已实际完成）
同步：SYNCED（首两ref/31完整正文/唯一P10回执及旧11/Issue状态已直接独立实读；末元数据另有界读回）
用户亲手效果：待确认
完成范围：仅经营报表主页面动作控件、四种既有SVG及层级间距；非全站
后续页面、完整S13、合并部署生产：未启用

[完整用户计划](../../execution/S13_DL_P10_IMPLEMENTATION_PLAN.md) · [P10-T01—12矩阵](acceptance-matrix.md) · [完整脱敏证据索引](evidence-index.md)。

## 固定候选与范围

|项目|实际固定值|
|---|---|
|业务分支|`codex/s13-dl-p10-report-actions-spacing-r1`，从clean P9最终9ea71c63465ec3ab625f141dbbbe277edd436d90正常建立|
|前态/准备工具|`74d57eb5cfcf3cf62ed14f755a08a23b42746418`，产品仍P9|
|最终产品|**`8a1547a14f5647d6a49555c8ab7f9ceb658511e3`**|
|最终工具发布|**`2c18d3271b49ab1ba2d6622e1755ed9678a97997`**；机械整合实际执行的私有函数，最终合并CLI只作PURE检查，不冒36客户端皆用此源|
|实际XML加载|首次`913b7ab92d48b6e08bcaaeb2cb34c3c2afb61ce5`；原生call参数修复后第二次 **`b46c1e272803b047e73489520682f0cd98d8ada4`**；之后CSS/工具/报告均未再-u|
|实际最终运行|**8a1547a** / `20261026T041906Z-a460a85c90f1`；b46中间运行的数据/CSV/P4及未改压力区按精确影响面复用|
|报告|首技术报告`6a0ac1a44687e89cd3d85c9472ce431097de98d1`/main仅路由`09d368a8c42adbfaae0c57d21894e5e7c720bd3f`已实际读回；末同步元数据ref另读，不循环自身未来hash|
|锁定核心/目标|core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；既有synth OID2171423 / cluster7694897083368259627 / 原filestore，不建库/复制/改名|

产品仅4个addon文件：主XML、manifest、`report_actions.scss`、`report_spacing.scss`。主模板唯一`data-dl-layout="report-actions-spacing"`，动作逐元素opt-in；共享nav/scope仅主模板两处原生call局部参数，默认关。不新增wrapper/产品JS/后端/权限/schema/指标或主题；manifest恰新增直接access/inventory依赖及两末尾资产。实际五个原生主视图1622—1626、EN/CN均无已安装继承扩展，非只猜基模板。

root为唯一产品/状态/报告写者和运行调度；runtime_p10负责运行/保护工具及受控窗口，testing_p10负责测试工具/真实浏览器，复用未实现本次产品或相应工具的acceptance_p9独立核验。共享OS不冒隔离。P9产品5f8f154、实际加载7d02a16、最终9ea71c6/唯一6407140114，P1—P9、P5 PARTIAL、旧包/失败/UNKNOWN均保留；无reset/clean/强推/从文档main重建。

## 10个动作定义与冻结合同

|定义数/原控件|本次表现|原合同|
|---|---|---|
|1 查询submit|primary + search前图|原GET/revision/字段、原busy/addLoadingEffect/恢复，图/字/Enter单次请求|
|1 导出submit|secondary，无新图/假busy|原POST `/ydental/reports/export`、CSRF/revision、服务器hidden原字符串；独立form|
|3 原工作区导航a|quiet，无图|原href/顺序/链接语义；source/error不opt-in|
|1 行循环来源a定义|quiet + arrow-right后图|原source_url/生效过滤/页/来源再授权；不能把渲染行数冒定义数|
|2 条件分页a|secondary + 原左右chevron|原条件/previous_url/next_url，无假href；当前真实一页，双向与末页为loaded组件|
|1 时区/UTC summary|disclosure、原生marker|原details全文/条件/开闭，无重复SVG箭头|
|1 按店合计summary|disclosure、原生marker|原store_totals条件/顺序/值，无新请求|

只调用原P7 search/arrow_right/chevron_left/chevron_right，Lucide0.468.0/f12b0de…原几何、SHA及ISC/Feather MIT全部不变。无新库/CDN/字体/运行时、标题图或新统计卡片。共享纯mixin原字节、独立编译零全局输出；P7/P8/P9调用方不改。字体1rem/600、圆角.625rem、min2.75rem、内衬.625em 1em、图文gap.5em/18px SVG、140ms/reduced-motion/forced-colors沿共享规范。

完整XML只剥获准class/span/SVG及两个call参数后C14N严格同P9；原生术语86次/74独有全文顺序同。P4两个产品JS及两旧SCSS原字节、原native select唯一具名源、字段顺序/label关联/条件/hidden/required/disabled、两form边界/type/name/value/action/method/target/CSRF/revision、所有URL/权限/提交时机保持。原指标/统计/日期时区/分币种单位/去重/状态/分摊/CSV防公式语义与后端不改。

指标确认改变仍唯一metric/date_from/date_to导航，日期保留/当前店恢复/其它条件和页码按原规则清；自然Tab紧接Enter不重复GET。其它控件只草拟，明确Query后生效；每store_ids值恰一次、0店required不默补，不切工作店。旧结果/导出hidden/分页/来源链接不随草稿变化。页尾导出没有新增反馈状态。

## 间距责任表（普通root16，实际rem）

|layout box关系|唯一负责人|实际值/保持项|
|---|---|---|
|nav动作/分页同组|显式nav flex gap，旧上下margin清零|.75rem /12px，自然换行|
|nav→标题→首说明|标题上/下margin|1rem / .75rem；无父grid叠gap|
|首说明→查询；查询→结果标题|后组leading margin|1.5rem /24px，前组bottom0|
|label→自己的可见field/trigger|原field flex gap，双方margin0|.5rem /8px，内部控件保持|
|legend→原多选/checkbox列表|legend trailing margin|.5rem /8px，checkbox内部与field-error原归属保持|
|指标日期组→范围组|range leading margin；form rowGap0|1.5rem /24px；原并列grid gap1rem保持|
|最后field组→Query动作|actions leading margin|1rem /16px；不叠父gap|
|Query→帮助/busy|原actions flex gap|.75rem /12px；hidden不占位|
|结果标题→口径说明→scope|标题bottom /scope leading|.75rem /1rem；说明bottom0|
|scope三段/相邻summary；summary→展开第一正文|相邻块leading margin|.75rem /12px；正文ul/p原margin清零后单owner；closed无洞|
|scope→有内容totals、store独立组、export/table/pager|后明确组leading margin|1.5rem /24px；empty totals零高度且margin0，empty notice自己24px，unique说明16px|
|table→pager|wrapper外距，table自己的外margin0|24px；表格列策略/单元10px内衬不变|
|已有filter card内衬|原P4规则，现有45rem断点|桌24/窄16px，不新增断点/层层卡片|
|主表sourcequiet焦点尾部/末行底|仅链接外.25rem，max-inline扣同值；末行底同owner|root16为4px/root32为8px；原cell10px、shared ring+offset12px不改；不叠wrapperpadding|

目标动作/模块自然位移、可用宽度/换行与行高变化获准，不要求目标所有rect同。特别是来源链接为focus外缓冲自然换行，仍原表格，不加固定行高或逐行大卡片。没有全局margin/连续br/空段落/固定高度、缩字/隐藏列/overflow:hidden补洞。

## 真实验证与证据复用

真实Chromium156.0.8078.4 + WebKit27.2 WPE，两engine本轮before与最终五view均1366×768/1440×900/768×1024/390×844/320×800。实际computed/box和原PNG同时核；目标8/12/16/24/inset24-16及单owner成立，条件无币种/无状态、空结果、hidden busy/error与closed details无空洞。320根本轮Chrome346/WK332前后各same，旧根因UNKNOWN，不顺手改全页或宣称已修。

每engine分别真实native200(root16，CSS683×384)与独立root字号200(native100/root32)，nav3/export/source3及原两summary/四popup/loadedpager首末和完整focus圈可达。实际source右边界1241+ring6+offset6=1253≤clipper1259，末行底也完整。自然Tab/Shift返与显式seed起点分列；AX只证原生可访问名称，非屏读/实机/Safari/iOS。

两engine真实四变体default/hover/active/键盘focus；局部样本文字最低5.2016318344:1，secondary/disclosure必要边内外最低3.2401343224:1，焦点最低6.6998110379:1。实际trusted Query busy按钮156.015625×46前后同，spinner不碰label/留2px，具名字段始终enabled。真实normal pageshow及native form.reset有本轮证据；取消导航/15秒恢复等未改JS边界按固定P4/source精确复用，不冒本轮重新取消实测。

有源reader16实际实收/实退/当前应收/唯一患者/lab_pending五指标before/final完整JSON只`filters.query_at_utc`一确定原生字段不同，保原两值，其余typed整个JSON同，不排序/删所有时间。12原key/授权选项/字段money/state/timing及15loaded QWeb组件实际覆盖；其余未改公式/通用revision与撤复权组合按固定P4及当前未改后端精确复用，不重跑旧全经济链。当前真实一页，分页组件不冒真实多页。

UID5原source+export WRITE真实读取CSV：实收旧生效3源行2349B、新显式空范围0行683B；唯一患者旧生效28源行8645B、新空0行704B。两结构四完整原文件全BOM/四头行/11列/filters/totals/单位/源集合顺序和值/原序列化/防公式前缀严格同原JSON，只有query_at分类。28是来源行数，不拿它冒去重患者总量。导出时草稿日期已改，旧hidden仍导旧生效范围；新Query后才导新范围。

Chrome真无JS同context正常CSRF认证后原生字段/GET/details/键盘及原CSV2349B完整。WK真无JS相同UI层有效；原下载事件超时，另正常原form单独补采取得同次200/textcsv/attachment及2346B decoded完整CSV正文，与同scope JSON全11列严格同。**没有WK wire BOM/native文件实证，不补BOM、不声称OS/native下载行为，旧两个Node2不反签**；与Chrome两种真实原文件分层合证满足本次CSV读取及无JS合同，独立f9c7b688…已确认，不额外创造每engine自动化download事件门槛。

reader16真实有源GET200/export403、无源none17 GET403无候选/export403、非法currency409等正常后端拒绝，无临时授权。doctor9的collections实际403是原无settlement source权限，工具误期待200的整client保Node2，没在该case试导出/扩权；正常reader是独立既有授权对照，不将其数据转给doctor。

明确长中文/混排、时区/金额/导航/两summary正文五view首末和clipper实测；用户覆盖line1.6/段后2em/字距.12em/词距.16em在代表1366/390/320实测，中文无词空格说明适用性。b46未改区精确复用，8a当前source缩宽另在两engine三view补长值/压力/无行叠，table实际桌1152/窄min760。压力只测试、无repairCSS。无SVG、仅P10 marker缺失保P4、全CSS缺失三个无网络组件分别留中文/原字段/可编辑日期/自然Tab焦点/原summary与内存submit；不冒真实业务。Chrome实际forced-colors、各engine reduced-motion通过；WK不支持项不冒通过。

P7库存/P9文书有限只读旁路所有所采forms/fields/actions/computed同；P5仅pay表单`actual_utc`原now_utc渲染默认一字段确切时间差，其余whole样本同，未付款/退款。来源详情和error实际无P10 marker，所采内部样式/表单/导航/行/原参数同；独立另对保存SOURCE整个main只精确scope第三p单原生UTC尾文本不同，其余C14N同，ERROR整个main exact，不广删时间或冒原全文字节相同。所有保护原件/PDF/打印/签署/发布/经济库存/治疗扫码新增0，不执行来源业务。

## 必要加载、最终完整保护与收尾

两次必要reporting XML加载各即时完整pre→实际exit0/ERROR0/noNative→post。第一次原生技术5类/新增access与inventory两直接依赖；第二次只原生日期、main call参数及3个arch_prev分别精确等前次实际EN arch，非覆盖用户内容。源、权限/业务/全部83引用文件不改；第二load后4deps同至最终。不为纯CSS/工具/报告再次-u。

主控侧最终完整snapshot `d3467905790b4e14d3ec1e45c271447718a7b8855987b3451a697d32c85496e2`；未实现者独立新physical **496534** RO/RR/rollbackidle/closed，完整145业务/13技术/九区与root逐值exact，同事务4deps+83引用/80真实路径/80不同SHA逐引用原路径、bytes/size/SHA保持，3原生共享引用不删。全stage独立 **0961969329266976a2f359f7b6f1aa4d465d7d7a612f26bc03772269b9c664b9**。旧金额库存/身份作者价源/原件/未完成责任/schema/config保持，旧AR1303与lot253收10用2余8仅保护来源事实，不硬编码今后报表结果。

旧18017audit逐行保，最终18406；新389均accepted：login/login.scope/store.switch各36、report.view184、report.drill20、report.export7、inventory.view2、settlement.invoice_view14/source_view54。`category export`并不等于执行CSV，7次按report.export真实事件计。权限拒绝原_denial走native emit_event，不虚构新增DB denied audit。其它144业务及配置/schema/附件区同，技术仅两load已独立分类的5表，非全库物理零diff。

4 owned窗口全部正常foreground/child0/groupstop；最终8a run于 **2026-10-26T04:30:58.070478Z** 正常收尾，36native浏览器0/全部context/browser正常close。独立quiescence **33c4bc4b32d098a73569031061819ba5fe7e5a81381b5823078fb97fa396636e** 核known PID/owner/18411和12/profile空，freshRO496968其它target连接[]/closed；共享主服务未动，之后不复开DB/app/browser，不为同步重验软件或包。

## 私有包、失败与限制

最终只读r1 `.local/dl-p10/viewing/S13-DL-P10-view-only-20261026-r1.zip`：**4,433,215B / SHA256 feddb5fab4c00e0a462dee6faba5e5d7e061e668a0d82a0f041676a21f791dba**，56成员/55非self清单/52原PNG/38测量。独立逐源字节/SHA/解码/候选角色scroll/隐私/15获准秘密值scan0，收据 **f85d224a4ef5c2fcc137bcb5c3a86818b4df63c797c0d72a3eada14486ced971**。只原PNG/脱敏说明及测量，不含CSV/PDF/原请求/session/配置/DB/程序/字体，不Public上传。P9r2/P8r1原ZIP bytes/SHA保持。前后scrollY分别记录，不冒像素对齐。

实际36clients=28Node0/8Node2，36browser native0；314唯一原PNG路径/273不同SHA全核，数量不是完成标准。旧24c0两baseline虽client0，只保已成子项，缺nav/scope族的整页不通过。8个Node2原样保：文书双main选择器、无JS同名测量wx、doctor权限预期错误、WK下载事件、WK decoded体被native BOM verifier拒、Chrome zoom真实2px裁圈及其诊断、空组件遗留>=7断言。另原生内存组件首英文aria-label被中文翻译导致assert exit1、preflight dirty拒绝、离线比较缺省title key、打包前manifest key拼写SyntaxError均保原源/退出；普通工具修正不冒产品通过，不重试未知经济提交。

A01原call正文lazy t-set不执行：按锁定core原生call局部属性修，未改core/后台，严格每族补验，独立闭合56badb21…；A02root32来源focus被裁2px：仅本页链接外缓冲，不改cell/sharedfocus/overflow，新双engine双zoom及压力复验，独立闭合66174681…。新根/焦点差异不靠旧UNKNOWN豁免。WK下载wire未证、320旧根因UNKNOWN、P5 PARTIAL和P9旧wrapper UNKNOWN等保持分层；用户效果/实机/OS IME/屏读/Safari/iOS/正式政策/完整S13及生产未验。

## 普通岗位7步复现

1. 在正常新有效运行窗口，用有报表来源读取权的普通岗位登录并选授权门店；本次owned服务已停，不恢复旧scope/STOP。
2. 从菜单进入“经营报表与原单钻取”，核暖色导航与原合成、指标口径说明。
3. 选原指标与日期；指标确认改变按原三参数唯一重查，其它条件只草拟。
4. 勾授权店和适用法人/币种/状态后明确查询，阅读生效范围；0店仍原required，不切工作店。
5. 开合时区/UTC边界及按店合计，沿原来源链接钻取并返回原生效过滤/页；不办理来源业务。
6. 仅有source读取+export WRITE岗位从原入口导CSV；改草稿仍导旧范围，明确新Query后才更新。
7. 用320/390、键盘及两种200%看分组、弹层、表格局部横读和完整来源焦点外圈；不提交经济库存/文书动作。不把localhost当远端入口或承诺旧浏览器可接手。

## 同步与停止

未实现者本地最终总签 **84420335db5e4948b7c74f4e59084ce22cfd313aaded7df4fe13f56f057479b8** 实际PASS，原LOCAL_REMOTE_PENDING时点保。首技术报告6a0ac1a/main仅两路由09d368a正常push；未实现者直接正常connector读两ref/31 FULL UTF8 bytes/SHA/Gitblob、[#37唯一P10回执6408631886](https://github.com/Yredxin/YDental/issues/37#issuecomment-6408631886)全文及旧11逐id/body/37OPEN36CLOSED/titlebody全exact，远端独立总签 **6682d0c377f049fffbbd79bc41453609c4ca4ffaedb7f95bd9bcdb95babca7e0** 已实际PASS。T01—12适用项成立，限定P10 **TECHNICALLY_COMPLETE / SYNCED**，用户亲手效果待确认。

本次仅记录已发生的SYNCED/停止元数据；最后4业务报告状态文档+2main路由以及同一own评论增量再正常读回，不循环自嵌未知自身hash、不重验软件/DB/包、不复开服务。未实现者最后metadata收据独立保本机，不以旧签预签未知未来。

P10交付后停止。详情页、结算/其它页面推广、完整S13、负载恢复/实机/正式政策/组合扫码/真实患者资金外部通道/合并部署生产均未启用。
