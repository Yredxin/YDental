# YDental / odoo-sd｜DL-P12 完整限定实施计划

计划编号：**YD-S13-DL-P12 / 1.0**。名称：结算患者查询与只读费用区域——统一按钮、轻量SVG、层级间距。制定与用户启用：2026-10-26。

授权依据为本会话用户完整附件及启动提示。本文件保存其执行要求，不扩P13、完整S13、写入办理区、生产或合并；包内不逐批等待GPT批准。

## 1. 承接与W0入口

业务基线分支`codex/s13-dl-p11-report-source-detail-r1`，产品613fb33bb4fecdb23eff3c46a2d3a1de2a4c1780，实际运行7b0601effe6ee2b3cc670087589865b7528a3f18，工具1fa0ac89827bc0d4400fa53e45c7bd63e4c43d01，报告bd0f73a99eb6f49c27d99a5db4cc6d4f8dedf008，唯一#37/6414490185。新分支`codex/s13-dl-p12-settlement-readonly-actions-spacing-r1`。锁定核心f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb。

读main AGENTS/GPT_HANDOFF/CURRENT路由、活动CURRENT、P11三报告、P5计划报告、P7/P8动作图标、P9间距、#23/#37有效正文及增量。main非产品基线；核origin/HEAD/分支/工作树/唯一写者，保留未知增量，不reset/clean/强推。

既有目标`ydental_s11_synth_20261023_01`，OID2171423，cluster7694897083368259627，原filestore；现场核，不复制/重建。保全83附件引用/80唯一物理文件/三共享。P1—P11交付、历史PARTIAL、原失败和UNKNOWN保持，不重跑历史经济库存PDF全链。

P11私有ZIP9328107B/SHA7e1c32e45aff99eb34613abf918378eb57401a9a869f1161dd183c7513c58773，用户计划记录GPT只读核85manifest/86SHA/83PNG，不是GPT动态测试/物理保全/用户签署。P11原生Tab部分显现、可信方向键恢复及旧根溢出UNKNOWN保持。

## 2. 精确范围与冻结合同

唯一正常页面`/ydental/settlement`；模板`ydental_settlement.ydental_settlement_page`，文件`ydental_settlement/views/ydental_settlement_templates.xml`。唯一根`div.o_ydental_settlement_lookup[data-dl-scope="settlement-lookup"]`，在首`details[name="settlement-operation"]`（Select fees to bill）前完全闭合。

只含原搜索、候选和搜索分页、已选患者/本店范围提示、其它门店最小摘要链接、today/history/pending三段费用、三段Source trace与原分页、至多两标题图标。只增精确局部class/data-dl-actions、必要SVG和文字span、spacing属性；不改DOM业务节点层次、循环/条件/继承位置。

|既有控件|动作语言|冻结|
|---|---|---|
|Search for a patient|primary+已有search|原GET q/Enter/maxlength100，不自动搜索|
|候选链接|quiet，不逐行图标|仅patient_id、姓名业务号顺序，不自动选首人|
|候选前后页|secondary+左右chevron|patient_search_url及边界文字，不造总数|
|其它店摘要|quiet，arrow_right可选|仅已选患者、原规范patient/store/权限/URL|
|三段Source trace|原生disclosure，不叠第二箭头|details/summary、原值、无AJAX、row/td|
|三段来源分页|secondary+左右chevron|page_kind/pages/page_counts/page_url、每页50及独立参数|
|最多两标题|可选既有list|无新动作，不每行/每h2堆图|

共享`ydental_settlement_page_links`如用局部原生call参数须默认关闭，真实loaded QWeb证明其它办理调用输出全保持；不得全局改按钮/URL/条件。

全部冻结：lookup前页头导航/门店/feedback；首出账details起到页末全部出账/收退款/免单/日结/内部票据/原件字段表单和合法能力；其它店摘要目标、集团目录、错误页、其它岗位/PDF；P5输入、五列表格列宽/单元内衬/状态颜色/数量日期币种/单DOM与横读。无产品JS、controller/model/ACL/schema/财务库存或核心改动。

q只搜索候选，唯点击patient_id形成实际患者上下文，新搜索按原行为清旧选择。费用集合/行序/待核对原因/实际执行人/业务日/精度/分页追溯不变。未出账非应收、确认金额非实收、空结果非结清。禁止任何出账/收退款/免单/日结/库存/扫码/打印提交；办理仅只读展开和取消，不删除/禁用合法能力。

## 3. 设计与间距责任

沿用DL15—20与`ydental_access/static/src/scss/_actions.scss`的`o-ydental-actions`。主陶土#94513A/hover#7E432F、杏陶暖白、浅杏次操作、柔边框、.625rem圆角、1rem/600、最小2.75rem、图文.5em；自然撑高、中文可读/对比，无厚影/强渐变/多动画。只目标根逐元素opt-in，不全局button/a/summary/.btn/.table或整页覆盖，不改共享mixin/P7—P11输出。

仅Lucide0.468.0固定子集commit f12b0de177fbc2a6795e99be065887e72b237123，原几何/SHA/QWeb/ISC及适用FeatherMIT保。currentColor/相对尺寸/aria-hidden=true/focusable=false，不额外Tab或重复朗读；保button/link/summary语义。无CDN/runtime/font/framework。核manifest真实依赖闭包，无则最小直接依赖无环，正常frontend assets加载。源文与zh_CN native extraction/loaded一致，span防翻译回退。

DL21—26：组内紧/组间松、内容不贴边、展开不粘连，rem+Grid/Flex；已有合格间距保留，每空隙一个owner。

|关系|目标与唯一责任|
|---|---|
|label→input|.5rem/8px，原label gap|
|input↔Search|1rem/16px，原form flex gap|
|查询行→帮助|.75rem/12px，form末距或帮助leading择一|
|帮助→候选/空态|1rem/16px，候选或空态leading，不留条件洞|
|候选之间|原li分隔+链接内padding，不大卡片|
|候选→搜索分页|1rem/16px，nav leading|
|搜索→范围→费用|1.5rem/24px，原lookup grid gap，无叠margin|
|三段费用之间|1.5rem/24px，原fee_overview gap|
|标题→help→表/空态→分页|.75–1rem/12–16px，逐空隙单owner，表格内部冻结|
|summary→展开正文|.75rem/12px，正文leading，closed无占位|
|动作内衬/图文|共享mixin，不替代组间距|
|lookup内衬|桌1.5rem/24px，窄1rem/16px，原padding|

不固定高度/空段/br/缩字号/隐藏列/复制移动DOM/overflow:hidden。每关系报告before/after box/computed及选择器，不机械放大所有margin。

## 4. 原使用流程

F1 普通读取岗位登录选授权店→原菜单→姓名/业务号GET搜索→候选不自动选择→原链接明确选择→服务规范patient及业务号。候选空不冒费用空。

F2 未选看授权店范围，选中看本店规范患者和合并来源→依原序today/history/pending禁止出账→原trace→字段/日期/actor/原因/币种精度不变。

F3 候选页只q/search_page；三费用页各page_kind保当前patient及其它页码→集合不变→其它店最小摘要原只读GET并返回，不获得办理权。

F4 同页首bill及有限办理仅展开/取消，字段提交权限保，不提交经济动作。

## 5. W0—W4连续实施

|包|工作|完成条件|
|---|---|---|
|W0|合法状态/唯一写者/目标/fresh准入，合成模板与t-call/CSS/mixin/许可闭包，普通岗位同条件前态，动作清单/间距owner|root在bill前闭合，查询分页权限数据可比|
|W1|各动作族/静态SVG/局部参数/翻译|真实页面原点击AX名称/HTML语义保|
|W2|只校正指定间距，保合格P5 Grid/Flex与表格|无叠加/空洞/新根溢出/焦点裁切|
|W3|固定候选定向T01—12，双引擎/5view/两zoom/noJS/权限/组件/有限冻结|无经济库存写，分层失败/修复/复用|
|W4|未实现者独立源码/执行/原图/physical保护/包/总签，正常同步实际读回，owned收尾|一份最终#37 OPEN/#36 CLOSED，结束即停|

root统一写者和环境，真实开发/测试/验收分工；未实现者不签自身实现，同OS非隔离。必要窗口先准备测试者/独立验收者和当前准入；旧额度UNKNOWN不要求重问用户，真实平台限制遵守。

## 6. T01—T12必需适用验收

各行记录固定候选/依赖/实际角色输入/层级/预期实际/原命令退出/证据SHA/独立判断/限制。SOURCE/PURE、loaded QWeb、内存组件、HTTP/BROWSER/AX、独立已提交RO及包核不可互冒。

|ID|目标|
|---|---|
|T01|wrapper bill前闭合；prefix/完整suffix/共享其它调用/字段form条件循环URL权限冻结；剥获准class/span/SVG/call标记XML可比；无产品JS/backend/ACL/schema|
|T02|全部动作/SVG/中文逐族；default/hover/active/focus；loaded中文AX同原；原几何SHA许可；图字空白同原事件；正文样本≥4.5:1，必要边/焦点≥3:1，不冒全站认证|
|T03|8/12/16/24/内衬24-16真实box/computed单owner，条件缺失/closed无洞，无全行放大/重叠/新根溢出|
|T04|Enter/按钮各一GET；q只候选，patient_id明确选择，新搜索清旧选择；空候选非费用空；每页30/第31has_more/原URL不改|
|T05|三段原集合/顺序/每页50/币种精度/当地日期/actor/reason/trace逐原值；原金额含义/pending禁止出账；三页参数独立。真实空段与组件非空分层|
|T06|其它店入口仅已选出现；普通角色真GET原只读权限；无结算源/既有不相关跨店患者/非法输入真后端响应，预拦截非403，零提权|
|T07|真实Chromium+WebKit或Firefox，各1366×768/1440×900/768×1024/390×844/320×800；长姓名号项目原因/横读末端完整达，原表/焦点保持|
|T08|每引擎native200%与独立root200%分别记；自然Tab/summary Enter Space/候选页码焦点顺序；noJS正常认证原GET/候选/details。AX非屏读/OS输入法/实机|
|T09|页头/首bill后全部办理账单退款日结原件、其它店目标/目录/错误、P7库存/P9文书/P10P11报表有限代表无污染；合法字段可用不删禁，仅展开取消；原time/key/scrollY差异精确分类|
|T10|缺SVG/CSS/长字/空候选/noJS优雅保中文控件权限操作；相同最终候选未改业务/通用权限精确复用旧证，不重演经济库存，旧失败UNKNOWN不倒签|
|T11|必要模块加载完整即时pre→实际0/log→post；纯CSS不重复-u。未实现者真实原目标新physical RO/RR/rollbackclosed核145业务13技术（现场为准）、83ref/80原路径逐bytes/size/SHA及三共享；旧审计逐行保、正常读新增分类、技术派生缓存另列；旧金额库存身份作者价源未完责任保，新经济库存原件PDF打印签署发布扫码0|
|T12|独立总签/固定产品工具运行报告/私有原图manifest/sourcebytes/SHA/正常owned与browser停；#37唯一P12最终和旧评论/正文状态实读回，37OPEN36CLOSED；用户亲手效果待确认|

真实pending/多页缺样可明确loaded QWeb/浏览器组件，不持久创建业务凑样本。已采未受影响业务按固定候选/源码复用，不为补报告重放。

## 7. 交付、成功与停止

全部适用T01—12及未实现者独立全保护/总验收成立才TECHNICALLY_COMPLETE；SYNCED/SYNC_PENDING单列不可代验收。缺必需验证真实PARTIAL/BLOCKED。

同一活动CURRENT和三报告：docs/reports/s13-dl-p12/{summary,acceptance-matrix,evidence-index}.md。含plan/真实分支/产品工具运行报告候选/合法增量；动作图标翻译AX与共享opt-in；间距owner及双engine5view两zoom原图box；T01—12层级失败SHA独判；全stage逐ref/物理/业务/审计分类；5—8步普通岗位复现；旧失败UNKNOWN和缺样限制；终态运行权限与同步。

.local/dl-p12/viewing/只读脱敏ZIP/README/manifest/独立包核，不含凭据/session/profile/原请求/完整DB/旧PDF/font/program，不上传Public，旧包不覆盖。正常同步实际读回；计划结束才#37新增唯一P12，37OPEN36CLOSED，P1—P11旧回执不改。main只必要文档路由，不合产品部署。

交付后立即停止。P13/结算写入办理美化/其它岗位全站/完整S13/50负载/备份恢复/实机/正式临床财务政策/S11组合扫码/真实患者资金/外部通道/合并部署生产未启用。自动化不代用户亲手效果签署。


## 8. 2026-10-27 原P12 A04定向续办授权

用户明确继续同一 `YD-S13-DL-P12 / 1.0`，仅修复原三段费用表局部横读后的A04与直接影响项；原T01—T12门槛不变。不是P13，不重新设计P12，不重开P1—P11。原PARTIAL报告2399983、失败原件、UNKNOWN、全部旧截图和旧r1 ZIP均保留。

原条件先复现：真实loaded pending组件、Chromium/WebKit、768×1024，可信横读保留36后一次Tab进入原首列summary，充分稳定后测必要文字和完整焦点圈；额外方向键、重新focus或切换目标不能代通过。

先做有界原生CSS诊断，保44rem/五列比例/单元padding/原table和summary语义。用户仅本次有限允许一个只读焦点增强：采用锁定Odoo前台Interaction，在原lookup费用表局部focusin后等待正常焦点转移，再依实际目标/焦点圈与client裁切盒几何，仅修正必要scrollLeft。不得preventDefault Tab、改focus/tabindex/根或纵向滚动、复制DOM、绑定全局键盘、拦方向键/滚轮/触控、发业务请求或改金额状态；已完整可见不跳动，初始化失败和销毁须正常降级清理。

必要正常前台资源注册属于该唯一受控JS例外：manifest单JS资产；结算原 `web.layout` 的head内增加核心原生session_info、minimal defer、lazy资源调用。保原CSS调用，不换整页layout，不复制可选时区cookie/测试资产/字体，不改视觉页头导航、body/lookup业务DOM或办理控件。该head资源增量必须显式登记，不能宣称整个head原字节未变；精确剥除资源块才可与原完整XML比较。必要XML加载须完整即时pre→真实退出/日志→post和未实现者独核，纯CSS/工具/报告不重复升级。

正常JS-on的“一次可信原生Tab＋局部JS增强”与纯UA自动滚动、真正JS-off分别验收。任一原适用必需门槛仍缺失，阶段继续PARTIAL，不能改断言、拿方向键恢复或SYNCED替技术通过。五视口、两种200%、today/history/pending、长值/空态/首末边界及有限旁路按实际影响定向验证；无真实pending继续明确loaded QWeb/BROWSER_FIXTURE，不创建业务事件。

同一活动CURRENT与三报告续写；83引用/80原物理文件/三共享逐路径bytes/size/SHA、全部原审计（含原P12新增7001）继续保，新读取审计另列。新私有效果包独立命名，不覆盖或上传旧包。最终只在#37原唯一评论6422670245保留原PARTIAL全文后追加有真实时间和新锚点的续办结论，#37 OPEN/#36 CLOSED，P1—P11旧回执不改。main仅必要文档路由，不合产品、不部署，续办交付后停止；用户亲手效果待确认。
