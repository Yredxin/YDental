# DL-P12 A04 定向续办交付｜2026-10-27

技术：**PARTIAL — JS-on 的一次 Tab 焦点显现已修复，真正 JS-off 仍不满足原完整焦点门槛**。同步：**SYNC_PENDING（本地结果，传输另核）**。用户亲手效果：待确认。

继续同一 `YD-S13-DL-P12 / 1.0`，不是P13。原PARTIAL报告 `2399983f917587d0145d085fd72aca1e1b00e5cc`、全部旧失败/UNKNOWN/原截图/旧ZIP保留；以下旧报告全文作为2026-10-26历史，不反签过去。[原计划及续办授权](../../execution/S13_DL_P12_IMPLEMENTATION_PLAN.md) · [更新矩阵](acceptance-matrix.md) · [证据索引](evidence-index.md)。

最终产品 **78c3650e0eeb1fcd3a970ed0693cfe9354e51cbc**；实际最后运行 **78c3650e0eeb1fcd3a970ed0693cfe9354e51cbc**；工具发布 **e4569c50d8dfac204028b5429abe190c05a7dfa2**，实际每个客户端源/命令/退出另有原件，发布整合只做SOURCE/PURE，不冒共同运行来源。报告固定锚点由本文件Git提交及#37原唯一回执6422670245的续办段登记，不循环嵌自身未来hash。

## 原因、修复和受控例外

原A04严格重现：loaded非空pending组件、768×1024、704px表/668px局部client，原生横读保36后一次可信Tab进入原summary；双引擎立即、100ms、充分稳定及1s仍local36/left26/clipLeft50，原文字/外圈被裁。没有观察到先归位再被锚点滚回的过程。已加载的scroll-margin/scroll-padding未令这条原生路径补足完整外圈；不把这一观察扩张成浏览器内部算法根因的证明。

有界CSS诊断的flow-root list-item、focus-sticky、contain-layout均未通过；focus-snap虽令Tab回0，却使后续ArrowRight被锁回0，违反自由横读，未采用。没有继续堆大margin，也未改44rem最小宽度、列比例、cell padding、字段、summary或table语义。

新增 [fee_focus.js](../../../ydental_settlement/static/src/fee_focus/fee_focus.js)：原lookup费用scroll各一个原生Odoo Interaction，只在局部focusin后等待两帧，重新核原activeElement/连接状态与实际outline-width+offset、client裁切边，再写必要的一次scrollLeft差量。已完整可见/无overflow/超宽目标不反复写；focusout和destroy取消待帧，初始化失败移除已注册监听并保持原生降级。没有preventDefault、focus调用、tabindex/DOM改写、全局键盘、根或纵向滚动、网络/财务动作。

首增量294ea5e仅manifest注册了JS；真实目标使用web.layout且原t-js=false，只CSS，目标页未引用/启动增强。旧候选及其缺加载结果保留，不能以bundle曾在登录页生成冒目标页已loaded。78c3650补上模板head内核心原生session_info、minimal defer、lazy三项必要启动资源；保原CSS，不换整frontend_layout，不复制tz cookie/测试资产/字体。原body/main视觉页头、lookup、全部办理源码逐字节保留；**head资源确有增量**，精确剥除该块后整XML才与原ba3字节相同。此与manifest单JS一并属于用户本续办授权的唯一受控JS例外。

相对原产品ba3仅XMLhead资源、manifest单asset、新JS三文件；原P12两SCSS、共享mixin/SVG/许可、其它全部addon、后台/ACL/schema/业务规则保持。原XML装饰还原canonical350d824…和共享分页default-off合同承接。SOURCE清单593个其余既有addon文件逐bytes/SHA保持（inventory 3a295fda…）；原a161工具文件未改，5个新A04工具单独发布。

## 修复前后与真实层级

|层级/条件|Chromium|WebKit|
|---|---|---|
|原产品lookup-only组件，原seed/retained36→一次Tab|稳定36 / left26 / clip50，FAIL|同FAIL|
|最终normal frontend全页组件，pending open/closed，同横向条件|100/400/1100ms local6 / left56 / clip50 / ring6，PASS|同PASS|
|原lookup-only结构与原seed的补充同条件组件|rootY581 / y842.84375 / 尺寸不变，left26→56，PASS|rootY557 / y866.84375 / 尺寸不变，left26→56，PASS|
|最终真正JS-off（实际禁用、原inline均未执行）|open/closed稳定36 / left26 / clip50，FAIL|同FAIL|

JS-on为“一次可信原生Tab＋受控JS显现增强”，不是纯UA自动滚动已修复。立即帧仍可保36；稳定帧才完成校正。原active summary/名称/标签/空href/tabindex、Enter/Space、Shift+Tab、自由左右横读/滚轮和idle不跳均实测；关键Tab到稳定窗口无网络请求。Chromium单次CDP EMULATED_TOUCH观察到可信start/11move/end且prevented=false，history局部0→165/max398，原DIV active、rootX0/rootY3133保持。它是协议仿真；WebKit触屏、实机触屏未测，源码无touch/pointer/全局keyboard拦截单列。

原baseline仅lookup的body与新全页正常启动组件纵向文档不同，不能把其rootY/viewport y直接当同位前后；各自水平条件完全相同，增强本身不改根/纵滚。补充paired组件按原body结构、原前置seed重建，仍正常HTTP head启动，不手动实例化修复；原seed的summary程序focus仅在critical之前，critical Tab后无重新focus/滚动helper或额外恢复键。

双engine各84有效焦点case（两明确loaded组件×三费用段×closed/open×五视口及两独立放大），合计168，另两empty。Chromium原有效前36层复用＋纠正后48层；WebKit84层逐actual viewport/DPR/rootfont核：native200根16、独立native100根32，非标签推测。原44rem/五列/cell12（root32为24）不改，真实Arrow/wheel、idle不跳及全文阅读分层保持。独签f1cf13d6…；普通真实五视口/两zoom/真noJS、原办理只读展开取消/他店和有限其它岗位另测。

真实岗位、loaded QWeb/BROWSER_FIXTURE、SOURCE/PURE、Colibri/iframe组件、已提交physical RO和包核严格分层。真实pending仍空；三段非空/长值不创建持久业务。Store1实际UTC，本轮跨到10-27后的自然today/history分类按原业务日核，不改clock、不强套10-26的1/26旧数量。本轮未选仍today1/history26/pending0；原fee88(10-26)从today进入history，既有fee89(10-27)从history进入today，计数巧合同，27行cells多重集合逐值保持；不把合并集合比较冒各段旧有序序列不变。实际selected655=0/1/0，lookup30控件与main连续32控件分开计，原办理2表单可用，仅展开取消；q/选择、金额/业务日/原来源值/权限合同保持。facts-r1中推测0/27的叙述已明确弃用，原文件保；仅facts-r2及原DOM行证据作为本结论。

本轮修正并保留全部新错误：WebKit禁JS rAF等待超时UNKNOWN及唯一已知owned browser正常回收；Chrome before-nojs1实际仍开JS的误标（撤回其noJS层，不改原件）；294目标缺前台引用；Chrome影响测试同origin原生zoom继承污染。仅有效前36层精确承接，受污染48+empty按每页native100/root16和实际viewport/DPR前置补采，不把旧wholeFAIL改PASS。续办32唯一actual browser：21 Node0、10 Node2、1 wrapper UNKNOWN；32 native0/context正常关闭。超时wrapper原null不改，后续browser正常回收/late日志另列，Node终码未观测不倒签。2次exclusive label拒绝exit1未启动Node，不重复计旧strict结果。357原PNG路径/334SHA、320执行源路径/24SHA逐件保，facts-r2 ca1f8989…、raw清单1797项/c2fbc628…；原P12全部1913原件和旧ZIP末次重核exact。

Chrome明确静态lazyJS缺失时，原中文/form/link/summary/EnterSpaceTab语义保持；原完整焦点native_pass=false、strictfailures=1且Node2/FAULT_FALLBACK…FAIL。旧collector末check的passed标签只是到达，不用作焦点PASS；公开工具仅改准该元数据标签，旧原件不改、不为标签重跑。真实loaded class＋Colibri/Scope各engine六组件分支核初始化第二listener失败清理、公开destroy、真实focusout取消及水平已完整0写/必要1写；这不是普通岗位浏览器或wholeviewport证明。normal bundle透传setter观察各一次真实reveal写6，未直接调用修复方法。

T02/T03/T07的JS-on焦点子层已成立；跨JS路径完整焦点仍PARTIAL，T08保FAIL，阶段不能TECHNICALLY_COMPLETE。未影响的T01/T04—06/T09—11按原固定候选/源码和本轮必要影响证据承接，未重演经济/库存/PDF全链；详见更新矩阵，不以截图/客户端数量代门槛。

## 完整保全、私有包和停止

同原目标OID2171423/cluster7694897083368259627/原filestore/core f0c5a9b保持。续办唯一必要XML-u完整即时pre→native0/ERROR0/noNative→post已独审f5259527…，原P12第一次-u历史另保；之后无重复-u。最终root快照1e9a6fcd…，未实现者newphysical803220 RO/RR/rollbackclosed全145业务/13技术/九区exactroot；83引用/80完整实际路径及三共享逐bytes/size/SHA原初exact。完整分类独签 **9c7ece2d5e2e379b9bd8b7fc3b1d1b4104d3b74ea423577b27d0a2d0ec853409**。旧18818＋原P12新增7001共25819逐row保，再1854正常auth/read→27673；原142业务same，21原生权限元数据仅write_date，7技术表唯一必要-u字段已逐ID分类。相对loadpost除1586正常audit，其余144业务/13技术/七区same，六依赖same。派生65记录=46实际文件＋19既有empty，仅lazyJS15819→15839（1990039B/SHA fb8816308411dc8fa0bc9224bb14ab02dcc3639c3179def8b383fe67556c6543），其它64记录和有文件者SHA保，CSS6cb6bed2…同；不是业务原件变化或全库物理零diff。新经济/库存/治疗扫码/原件PDF/打印签署发布/CSV动作0。

新私有0400 `.local/dl-p12/viewing/S13-DL-P12-A04-view-only-20261027-r1.zip`：**8,598,186B / SHA256 1e3d5e02c9cd2ca6e93911ce243cb015859e13ed2d03319a0c5393599e0478bb**，98成员/94原PNG/14有限测量，README PARTIAL，含原生FAIL/JS增强PASS/真noJS FAIL/同位pair/长值zoom/普通岗位及明确仿真层。只读脱敏，不含凭据/session/profile/原请求/完整DB/PDF/字体/程序，不上传Public；包核另有未实现者旁签。旧r1 **9949005B / 9ecdf42f3567a32bd2316f7c89e9b7f06ab4a442fb5fab5e6b08489122a7660a** 末次字节保持。

真实分工：root唯一产品/报告/路由写者，runtime_a04运行保护，testing_a04测试工具/浏览器/包，acceptance_a04未实现者独审。同OS不冒安全隔离。已实际完成SOURCE/必要-u/严格双engine/真noJS/168case/paired与组件/32actual全源原图/完整physical/OS终态各独签；32原件核 **dd2312e9423aa3a44eb437c3e60441ca5e3796b6bc3fe269ca5817374a3f9e7e**。最终包/正文/总项和正常同步旁签在证据索引按实际增加，不能用保护/包PASS代焦点全通过。

本续办3owned全前台0/child0/signull/groupstopped，日志ERROR/CRITICAL0，3临时配置已移除。末run20261027T002613Z-7762e3996f14于 **2026-10-27T00:47:30.383544Z** 正常stop。32浏览器/context正常close；独立OS/knownPID/profile/marker/18411与12空、新RO803342其它targetconn[]/rollbackclosed，旁签 **a324a920767c660f6d77eaa4f1f69141b57c7df8cf7b5fb0e041adcbb3a067e9**。原6owned/70native保持，合计9owned/102native已关；共享主服务未动，无临时grant，之后不为报告/同步复开app/DB/browser。

## 普通岗位7步

1. 在正常新有效测试窗口登录有结算读取权的原岗位、选择授权店，从原菜单进入结算；交付后的本轮owned已停止，不能恢复旧scope/STOP。
2. 输入姓名/业务号以Enter或搜索按钮执行原GET，核q仅产生候选。
3. 点击原patient_id候选链接明确选择，核规范业务号和本店范围。
4. 依原序读今日、历史未出账和待核对；未出账非应收，确认金额非实收，空结果非结清。
5. 启用JS时聚焦原表格正常横读，再按一次Tab到来源summary，无额外恢复键即可完整显现；Enter/Space展开关闭。真正禁JS的保横读后Tab裁切仍是本批公开缺口，不借方向键恢复代通过。实际非空pending仅在明确组件中复现。
6. 用原分页/其它店最小只读摘要并正常返回；组件多页不冒真实业务页数，不获得他店办理权。
7. 有权时仅只读展开原办理面板并取消返回，不提交出账、收退款、免单、日结、治疗、库存、扫码、原件/PDF、打印、签署或发布。

同步与唯一回执：本地固定资料正常提交/推送和全文独立读回尚在收口；只追加原唯一评论6422670245并保其原PARTIAL全文，不新增第二份P12回执。#37保持OPEN、#36 CLOSED、旧P1—P11回执不改；main只必要文档路由，不合产品、不部署。续办交付后停止；P13/完整S13/负载恢复/实机/正式政策/S11组合扫码/真实患者资金和外部通道/生产均未启用，用户亲手效果待确认。

新包独核已实际PASS（不代技术通过）：`new-viewing-package-independent.json` **b6a1a3edc2097d566bf80578c059ef6345bcc6891203b75edd03728cf641923f**，98成员/94原PNG逐sourcebytes/manifest96/SHA97/14有限测量及隐私全核。原r1ZIP末次exact。最终正文/总项及正常远端同步仍待本次实际封口。


---

以下完整保留2026-10-26原PARTIAL报告；其候选/统计/同步/停止均是原时点事实。

# DL-P12 结算患者查询与只读费用区域交付

`[CODEX-FINAL] YD-S13-DL-P12 / 1.0`

技术：**PARTIAL — A04 原生横向焦点门槛未通过**。同步：**SYNCED（仅传输，技术仍PARTIAL）**。用户亲手效果：待确认。

仅 `/ydental/settlement` 原 `div.o_ydental_settlement_lookup[data-dl-scope="settlement-lookup"]`，在首个“Select fees to bill”办理 details 之前闭合。完成动作/SVG/间距实现，保留一项未关闭的原生焦点问题；不重开P11、不扩结算办理区或全站。

[限定计划](../../execution/S13_DL_P12_IMPLEMENTATION_PLAN.md) · [T01—12矩阵](acceptance-matrix.md) · [证据索引](evidence-index.md)。

## 候选与实施边界

从clean P11最终 `bd0f73a99eb6f49c27d99a5db4cc6d4f8dedf008` 沿业务基线建立 `codex/s13-dl-p12-settlement-readonly-actions-spacing-r1`；没有reset/clean/强推/从main重建。P11产品613fb33、运行7b0601e、工具1fa0ac8、唯一#37/6414490185及P1—P11历史PARTIAL/失败/UNKNOWN保留。

最终产品 **ba3a5b0da4f3a8d2b27c3c5f84fbf533896f104f**；实际最后运行 **0f1deb837ed469deb9d5e2e8dcb819863ad59a0d**。首产品7c3e2fe，密度修正4cf0b15，空态单owner c61e060，竖向焦点留白5522126，双轴留白ba3a5b0逐次保留，不反签旧候选。 普通患者完整同条件五视口布局末次实采在40d8cf0（产品c61e060）；随后仅scroll-margin焦点落点CSS，XML/manifest/布局声明同源精确复用。当前ba3/0f1另实际采常规双engine键盘/noJS/两zoom、四组件五view及严格A04诊断，不冒所有旧截图均由最终ba3产生。唯一必要settlement-u候选2df168f，native0/ERROR0/noNative；原生级联下游模块有实录，其后纯CSS/工具/文档不重复-u。

只有3addon文件：原XML、manifest最后单SCSS资产、局部 `settlement_readonly_actions.scss`。原P5 SCSS、共享mixin、固定Lucide资源/许可、全部产品JS、controller/model/ACL/schema、财务和库存逻辑原字节保持。原main页头前缀与首bill details起完整文件后缀byte exact；全XML只还原获准class/span/SVG/三call标记后canonical SHA `350d824a74b262c894dfe7a65a1037ecb33152fb6069f03986a7176537bfcb8f` 同基线。native source terms231→233仅两个共享分页重复标签，unique set同，实际zh_CN/AX名称保持。

root为唯一产品/报告/状态/路由写者；runtime_p12负责运行保护和加载工具，testing_p12负责合同/浏览器/包工具，acceptance_p12未实现产品或对应工具者独立审源码、原件、新physical、包和结论。同OS不冒隔离。capacity中断和普通工具错误保原记录，在同团队同入口正常接续；实施过程未向Issue发中间问题或等待GPT签字。

## 动作、静态SVG与共享调用

|原控件|局部族与图标|保留合同|
|---|---|---|
|Search for a patient|primary / search|原button/GET q/Enter/maxlength100，不自动搜索或选首人|
|患者候选|quiet / 无逐患者图标|原patient_id链接、姓名·业务号及顺序|
|候选前后页|secondary / chevron_left、chevron_right|原patient_search_url与边界文字|
|其它店最小摘要|quiet / arrow_right|仅已选患者原链接，真只读GET不切店办理|
|today/history/pending Source trace|disclosure / 原生marker，无第二箭头|details/summary与原追溯字段/条件|
|三段费用分页|secondary / 左右chevron|原page_kind、pages、page_counts、page_url、每页50|
|标题|0个图标|未使用可选的最多两个标题图标|

复用原 `o-ydental-actions`，同一杏陶暖白/陶土色、1rem/600、适度圆角和自然高度；无第二按钮配色。只逐元素 `data-dl-actions="settlement-readonly-actions"` opt-in，全部新规则限定lookup root。SVG为P7固定Lucide0.468.0/f12b0de…原几何/原SHA，ISC/Feather MIT保持，aria-hidden=true/focusable=false，无独立Tab/重复读名，无CDN/图标runtime/字体/框架。真实图、字、空白点击均原控件同一事件；组件分页点击的preventDefault另标，不冒真实多页HTTP。

共享模板 `ydental_settlement_page_links` 仅三处原生call参数 `settlement_readonly_actions="True"`。源码另4处实际办理调用不传参数，原settled区为自有nav未改；loaded两语言×8kind×6边界×3模式=288渲染，其中192 missing/false原HTML逐字同。父序列3True后5missing是明确内存场景，证明flag不泄漏，不能冒5处真实办理调用。无新增source权限或临时grant。

## 间距唯一责任与实际差异

16px根字号，实际rem/Grid/Flex；root32测量另列，原表格最小44rem、28%/18%列与cell .75rem保。

|关系|唯一owner|before → after（px）|
|---|---|---|
|label→input|原search_label gap|8→8|
|input↔button|原search_form gap|16→16|
|form→首帮助|form末距|16→12|
|两帮助段|后一help leading|12→12|
|帮助→有候选|候选UL leading|16→16|
|帮助→空态|零高UL恒leading16；empty DIV margin0|32→16|
|候选→搜索分页|nav leading|16→16|
|搜索→范围→费用|原lookup grid gap|24→24|
|三段费用|原overview grid gap|24→24|
|分段标题→帮助/空态|fee_section grid gap；直接子margin0|16→12|
|帮助→表格；表格→分页|同section grid gap|12；分页明确组件另验|
|summary→展开正文|trace_body leading|after12；旧匿名文本不伪造独立BOX|
|lookup内衬|原padding|桌24/窄16保持|
|焦点落点|action/disclosure/region scroll-margin|8，root32为16；不占布局间距|
|表格横读焦点净空|fee_scroll scroll-padding|6，root32为12；不改横读策略|

A01初共享summary横16导致窄列折两行，row103px；只summary横8后单行46px/row79，原row约70.594px、summary约37.594px。剩8.406px为共享操作高度/边/行高的自然增量，未设row高或增cell内衬。A02空UL因QWeb空白文本不匹配:empty，与空态各16形成32px；移除无效规则、让UL单owner修成16。A03正常GET进入态的竖向fit控件最终两engine即时/settled完整，原100ms-only样本不冒持久根因或CSS单因修复。

## 未关闭A04与分层验证

**A04仍OPEN。** 在明确loaded非空pending组件、768×1024，先可信ArrowRight把表格横读到36，再Tab首列原summary；当前正常CSS双轴scroll-margin8已真实加载，Chromium/WebKit充分settled后仍left26 < table clipLeft50。原标签/焦点左侧被裁，严格原生Tab完整门槛FAIL。两engine一次可信ArrowLeft可各回local1/0，使原active summary/全标签/全圈/rootX0恢复；它是键盘恢复实证，不能代原生Tab PASS。同序before未观测，不能冒新回归或借P11旧限制豁免。本轮没有已验证且符合冻结边界的修复，不引产品JS、不改表格策略、不降标准。

普通已选患者655的32原控件正常GET主路径，双engine JS-on/noJS与两种200%已经实测；未选患者27候选、today1/history26/pending0，选655为0/1/0，前后同。Store1实际UTC，不按Asia/Shanghai推测跨日，时钟未改。真实权限：普通uid14正常读/明确选择/其它店摘要200，none17主页面及摘要403，非法输入400、未知及真实不相关patient60（仅Store2）403，非预拦截、零提权。

缺真实非空pending/多页使用四个明确loaded-QWeb内存组件；fake IDs/名称/金额标【P12夹具】/FIXTURE，不创建持久业务，不冒真实身份/权限或币种精度。真实原金额/日期/行序/来源以原DOM值逐项比较，fixture只验呈现。超高链接如934px大于844px视口，不强塞同屏：fit控件仍整圈强核，超高者以保持原active/href、横向圈、可信键上下边/全文分别可达取证。Range/helper阅读样本与纯键恢复分层，不拿关闭的trace正文当可见末字。A04按case保FAIL，其它无依赖字段/4states/分页/fault继续强核，overall不能变PASS。

原失败与UNKNOWN逐client/source/command/exit留存：禁JS监听器无记录、固定24方向键不足（442/468→24）、旧右移起点未保存UNKNOWN、页底程序focus与CtrlHome未到页首、超高同屏断言、closed trace末字选择、WK几何前置误推、A04实际失败均不倒签。新普通GET进入路径不代表任意滚动状态自动归位。原生AX非真实屏读，WebKit非Safari/iOS，未测实机/OS输入法/用户亲手效果；P1—P11历史限制保持。

## 普通岗位7步

1. 正常新有效运行窗口登录普通有结算读取权岗位，选择授权门店，从原菜单进入结算；交付后owned已停，不恢复旧scope/STOP或承诺localhost远端可达。
2. 输入姓名或业务号，以Enter或搜索图标/文字执行原GET；候选不自动成为已选患者。
3. 点击候选原链接，核服务返回的业务号与本店/合并来源范围。
4. 依原序读今日、历史未出账及待核对三段；未出账非应收，确认金额非实收，空结果非结清。
5. Enter/Space展开和关闭来源；窄屏先聚焦原表格，用左右键读全列；横读后Tab首列追溯可能出现A04，原ArrowLeft可恢复，但本批门槛仍未通过。
6. 有实际分页时用原链接独立翻页；当前真实一页，不把组件页数冒业务数据。只读查看原其它店最小摘要，再正常返回。
7. 原办理面板若有权可见，仅只读展开/取消，保原字段和合法能力；不提交任何出账/收退款/免单/日结/库存/扫码/打印。

P12交付后停止；#37保持OPEN/#36 CLOSED，P1—P11旧回执不改。main只必要文档路由，不合产品、不部署。P13/结算办理美化/其它岗位全站/完整S13/50活动负载/备份恢复/实机/正式政策/S11组合扫码/真实患者资金/外部通道/生产未启用，用户亲手效果待确认。


## 完整保全、只读包与实际停止

公共工具发布 **a161aa3f956d16eb24dc4255955202db002f5857** 是实际私有变体的机械整合；仅SOURCE/PURE/compile/Node syntax检查，不冒70历史客户端全部出自相同最终源。actual逐次700执行源路径/29不同源SHA，全部原source/命令/退出保。70actual=56Node0/14Node2：12个strict wholeFAIL与2个COMPLETE_WITH_OPEN_A04；70native browser均0/正常context关闭。1003原PNG路径/607不同SHA逐源bytes/size/PIL解析。测试数不是通过门槛，A04仍FAIL。

锁定core **f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb**，原目标ydental_s11_synth_20261023_01/OID2171423/cluster7694897083368259627与原filestore，无新库/克隆/改名。最终root完整snapshot SHA **ba64b9c6a5624e68e6c97db013d73c39c02a790da878c299c085ec9668f650b6**；未实现者新physical **683138** 真实RO/RR/rollback/closed，完整145业务/13技术/九区逐值exact。83附件引用/80真实路径/80不同SHA逐完整bytes/size/SHA保持，三组原共享引用保持；独立全阶段保护 **4a38c2999f96af9b45548f29570f0d01d15d4ac7037e2a080cf2618ec7e39f63**。

旧**18818**audit逐行保→最终**25819**，新**7001**均正常认证/读取。初态其余142业务完全same；ir_access的20行及res_groups的id69一行仅原生唯一-u的write_date变化，权限值/成员same。7技术表逐ID/field/native provenance分类，reporting三arch_prev是此前P11原EN架构；所有config/schema/原身份作者价源/未完责任保持。相对loadpost除新6341正常audit，其余144业务/13技术same。六原生依赖same；65派生asset仅CSS15833→15838，余64 metadata和实际文件SHA同，与83业务原件分开。当前正常bundle600729B/SHA6cb6bed2502ce823fa7b228356d10e46c8ecaa9556d81b264f042d9af64b71b4。新经济/库存/文书原件PDF/打印/签署/发布/治疗扫码/CSV动作0；不冒全库物理零差。

六owned窗口全部正常foreground0/child0/signull/groupstopped。末run **20261026T162536Z-58003ecdb36a** 于 **2026-10-26T16:51:12.497554Z** 正常stop。独立终态 **c148f336f2b0edeaa5e9ea3404f992c375c3d15de20e93a02afec57556290c3e** 核knownPID/supervisor/browser/node/markers/profile与18411/18412空，另新RO683713其它targetconn[]/rollbackclosed；共享主服务未动，无临时权限需撤。之后不为报告或同步复开app/DB/browser。

私有0400 `.local/dl-p12/viewing/S13-DL-P12-view-only-20261026-r1.zip`：**9,949,005B / SHA256 9ecdf42f3567a32bd2316f7c89e9b7f06ab4a442fb5fab5e6b08489122a7660a**，94成员/90原PNG，README首行PARTIAL/A04OPEN。before/精确复用布局/最终native/A04严格FAIL与可信恢复/超高分段/intermediate分层，全部原图不编辑。无凭据/session/profile/原请求/配置/DB/PDF/CSV/font/program，不上传Public；旧P11及更早包不覆盖。ZIP内部independent PENDING保构造时原字节，最终外部旁签另列，不循环回写自身hash。

运行事实 `379a451517203852a6703a1e632376131fcd545536a1148aa2ebc94eb5ccf7f7`；完整客户端/PNG/执行源事实 `76e5a116be9ba6462b3b0e7749e1a06e989fb0bfe9c867f096d9ee03de579527`。SOURCE/PURE、loaded QWeb、内存组件、真实HTTP/BROWSER/AX、独立已提交physical RO与包核分别记录，不能互冒。最终本地独立交付总项与正常同步读回在后续已发生元数据段登记，不能把SYNCED代技术通过。


## 已发生的独立组件与包核

独立逐层核40字段场景、44首末Range批、22纯键超高分段、两engine四族×四态颜色阈值、每engine8分页×图字空白24可信事件；压力/fault8分支及empty两zoom均有实际记录（root32 empty gap32px，无before不补造）。普通fit native A04仍WK6/Chrome4个组件场景FAIL，overall保持COMPLETE_WITH_OPEN_A04/exit2，不能用各子层成功代总项。70actual的12 strict wholeFAIL中8个工具/准备/几何失败，4个实际A04门槛失败；另2个COMPLETE_WITH_OPEN_A04是独立层完整且A04未闭。

私有r1包已实际全成员/sourcebytes/PNG/manifest92/SHA93/24有限measurements/隐私核PASS，旧P11ZIP原bytes/SHA保；该PASS不代表阶段通过。最终产品按odoo-review双pass和对应XML/manifest/SCSS/assets/稳定版/注释/core原生call与消费者复核，无open SOURCE finding；不冒全模块安全审计。用户限定计划优先于泛化stable/直接depends建议，未增审批。

|独立旁签|SHA256|
|---|---|
|`acceptance/final-component-sublayers-independent.json`|`c928dcafb650ab466f1cb82bf602c25e4c3a768f795304f3b868449a7913694d`|
|`acceptance/final-component-additional-layers-independent.json`|`70e369be21d833f8f89022b708c728e7c7a1ce05614ffdbe45e2128dbf4726b1`|
|`acceptance/final-viewing-package-independent.json`|`2e83a4b4a9104d19e2c8dc98f7d69866c24c1205665506c10389b8a205c0e6bd`|
|`acceptance/final-complete-protection-independent.json`|`4a38c2999f96af9b45548f29570f0d01d15d4ac7037e2a080cf2618ec7e39f63`|
|`acceptance/final-quiescence-independent.json`|`c148f336f2b0edeaa5e9ea3404f992c375c3d15de20e93a02afec57556290c3e`|
|`acceptance/finding-P12-A04-confirmed-unresolved.json`|`8ed0e3040679b5dbaab1b4b6fa7c0d1dec92fad3b244283cfb8f08079ce1c89d`|
|`acceptance/product4-house-guidelines-review.json`|`caa144925b550cfa618ebf6934e385c4a1650e2160007bd8193e5f5bd8c7e055`|

本地文稿首固定e7924ad0b9df76c13b7fbf05e27ca1798242e373、main仅两文档路由准备ce52cb9065c06d7aaa27d51b33b4b018c1613ac2；当前还未正常push/回执/独立读回，故SYNC_PENDING。最终文字总项明确PARTIAL，固定正文独核与远端实际结果后续只登记已发生元数据，不循环自嵌未来hash，也不再打开服务/DB/browser。


## 最终本地独立交付审计（仍为PARTIAL）

未实现者审固定文稿 **e33c05f3f8ebce7599bbaf31d410f12b7b6b5a17**、工具a161aa3、main仅两路由ce52cb9，全部70实际客户端的700执行源/1003PNG/210收据和原命令/退出完整核。`final-all70-fullsource-integrity-independent.json` SHA **f4f569d646ab0fb66f52a8473d5d83fa21b96fbc243154152b8a80b5bdb365e7**。

最终本地总项 `final-technical-partial.json` SHA **3d3d982f938ff5d0fec4db8f9e5a4fa6ca7a2e9a159ba8d7e4c18243ec4bbf88** 已实际接受PARTIAL交付记录：T08 FAIL/A04 OPEN，T02/T03/T07完整焦点子项PARTIAL，未签TECHNICALLY_COMPLETE。公开交付审查 **a5399dfd5ddd15426c04c476d38a473ee1e9b8b4a5503f4ff90c676fd66a530c**：全部56新可达Git blobs以正常获准provider秘密值仅在内存比对，0命中，无值或摘要输出；71个公开证据行的实际bytes/SHA已重核。后续只加入这些已发生元数据，最终refs/唯一回执和完整远端读回尚待真实操作；原SYNC_PENDING时点保留。


## 实际同步与最终停止

正常push首业务 **9cf8057923516df89dc6ccfc14022688b1c29644** / main仅两路由 **abef497bdfb6f5b925736999cb23d351f69bfd3b**，root经正常GitHub插件33完整UTF8/bytes/SHA256/Gitblob exact（3fbaf2efa9250f53375c423b8deeab86636ad4440c035a830299cc54494d5cd4）。#37只新增唯一P12 [6422670245](https://github.com/Yredxin/YDental/issues/37#issuecomment-6422670245)，root全文与旧13 id/body及37OPEN36CLOSED/titlebody实读exact（af4bbb3177c999e43febb847cbe54ea75e4f7d06e5e6819ef54f1ec336677b78）。

未实现者独立直接plugin两ref/33全文/本唯一评论完整正文/旧13/#23/#36/#37 title/body/state逐项exact，`final-sync-independent.json` SHA **e4ef772ad7df6a7fd836a2bad657bad54e4e526f84c3b73aa72867d6560d2455** 已实际成立；新增metadata blobs和comment秘密值内存比对0hit。评论API真实created/updated未观测，不用null相等冒时间证明。当前 **PARTIAL / SYNCED（仅传输）/ STOPPED**；A04/T08原生横向焦点FAIL仍在，不能TECHNICALLY_COMPLETE，用户亲手效果待确认。

原首发SYNC_PENDING及本地总项时点保留。最后仅加入这些已发生元数据，最终ref/六文档/同一回执增量再正常读回，不循环自身未来hash，不新增第二P12，不改旧13，不复开app/DB/browser，不合产品或部署。P12交付即停，后续未启用。
