# DL-P12 结算患者查询与只读费用区域交付

`[CODEX-FINAL] YD-S13-DL-P12 / 1.0`

技术：**PARTIAL — A04 原生横向焦点门槛未通过**。同步：SYNC_PENDING。用户亲手效果：待确认。

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
