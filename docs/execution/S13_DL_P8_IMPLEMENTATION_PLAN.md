# YDental｜文书主页面按钮与轻量 SVG 推广

计划：**YD-S13-DL-P8 / 1.0**  
制定日期：2026-10-26（用户附件原日期；执行时间使用现场 UTC，不改旧时间）  
本批名称：沿用 P7 按钮语言，推广到文书主页面动作控件  
仓库载体：`docs/execution/S13_DL_P8_IMPLEMENTATION_PLAN.md`

> 用户将本附件与启动提示交给 Codex，即仅启用本 P8。不是全站改造，不是重新开发文书业务，不把旧阶段技术完成当作用户亲手效果确认。P8 内连续实现、测试、普通修复、未实现者独立验收、最终同步；交付后停止。

## 1. 背景、依据与承接结论

用户已明确要求所有常用按钮最终使用协调、柔和、暖色的统一风格，适量使用开源 SVG，并逐阶段实施。P7 已在库存主页面验证 DL-15—DL-20 的按钮语言。本 P8 只把同一规范推广到 `/ydental/documents` 的动作控件，不重新选择主题、不重做页面布局。

P7 报告记载：43 个呈现节点、四种实际按钮变体、七种固定 Lucide 图标，适用 T01—12 与未实现者验收完成。产品为 `52d5422fa0083bf88cec4442ffcd45d35d27e9f7`；从产品到报告 HEAD 的差异只有状态、报告和工具 README，不含产品代码增量。[R1—R3]

本次 GPT 实际只读核对固定报告、矩阵、分支 ref、同一最终回执、按钮 SCSS、图标 SOURCE 与文书模板/查询 JS；实际核用户上传 P7 包：2,396,745 字节，SHA256 `6ddf2df5e54df61e898ea21fa553d125059c7a0366e43e30cdc1daa6cb356df6`，36 项 manifest 成员字节/SHA 全匹配，34 PNG 可解码（33 个不同 SHA），查看缩略总览与代表原图。未重新运行浏览器、登录业务库或重签现场完整保护；这些动态结论依据已有独立验收承接。P7 不重开，用户亲手效果仍待确认。

本计划的新约定与既有事实分开：第 3—9 节是本次 P8 的目标、允许修改面与验收要求，不是宣称文书页已经完成这些改造。旧 P1—P3 的局部冻结要求仅在本计划明确列出的动作节点呈现上被替代，其他冻结事实保持。后续报表、结算及其它页面尚未启用。

### 1.1 固定锚点（不是回退指令）

|对象|承接值|
|---|---|
|当前业务线|`codex/s13-dl-p7-inventory-actions-icons-r1`|
|P7 产品／实际运行|`52d5422fa0083bf88cec4442ffcd45d35d27e9f7`|
|P7 报告／已核远端 HEAD|`9f5ce4626895cb8f3da0562d9170e79220728378`|
|P7 唯一最终回执|#37 / `6399387525`|
|建议 P8 分支|`codex/s13-dl-p8-documents-actions-icons-r1`|
|锁定核心|`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，不改|
|唯一既有合成目标|`ydental_s11_synth_20261023_01` / OID2171423 / cluster7694897083368259627，原 filestore|
|保护计数口径|83 个受保护附件引用，对应 80 个唯一物理路径／80 个不同 SHA；原有共享引用全部保全，现场核实际清单，不做去重或删改|
|原件与历史|65 内部＋2 外部原件、旧资金库存和未完成责任保持；旧 P5 PARTIAL、续办和全部旧包／失败不覆盖|
|阶段状态|#37 保持 OPEN，#36 保持 CLOSED；main 仅文档路由，产品未合入 main|

先读 main/GPT_HANDOFF.md、AGENTS.md、main/CURRENT_TASK.md，再按路由读活动 CURRENT、P7 三报告、P7 完整计划和 docs/design/YDENTAL_DESIGN_LANGUAGE_V1.md，核 #23/#37 相关有效增量及 #36 状态。P1—P7 旧计划不是新的重跑清单。

核真实 origin、HEAD、工作树和唯一主控；保存、理解并保留未提交增量。已有正确 P8 分支则继续，否则从合法业务线正常承接；不 reset、clean、强推或从文档 main 重建。不得假定工作树一定 clean 或旧额度信息仍是当前状态。

## 2. 目标与停止线

普通有权岗位能够沿原入口完成：搜索患者文书 → 原来源／模板选择 → 显式预览 → 阅读原件 → 明确查看／下载旧文件 → 原分页；各动作控件与库存 P7 属于同一视觉家族。

未改变的生成、打印请求、模板管理、导出入口，也在本页获得一致的按钮／折叠外观，但本批不执行生成、打印或模板写入来验样式。业务权限仍由原后端决定。

“本页动作控件覆盖”不等于重做全部 HTML button 元素：P1 JS 动态生成的两处 role=combobox 触发器是选择字段，保留现有外观、浮层和行为，不套提交按钮样式。清单应把它们明确列为本批排除的字段控件，不假称未改下拉已再次通过整套改造。

本批结束后停止。报表／结算按钮推广、其它页面、全站主题、完整 S13、负载恢复、实机和生产仍未启用，不自行制定并执行 P9。

## 3. 精确控件范围与变体映射

主模板：`ydental_print/views/ydental_document_templates.xml` 内 `ydental_document_page`。仅该主页面；不得把本模块其他文书入口、同意管理页、打印页、网站共用页头或实际 PDF 内容一并纳入。[R5]

渲染入口区别：正常 GET `/ydental/documents` 和 POST `/ydental/documents/action` 的预览回页都会渲染这一主模板。使用模板级、元素级 opt-in，不能照抄 P7 仅按 pathname 等于主路径的门控，导致预览后按钮失去样式；也不能因覆盖 action 回页而改变 controller、JSON 错误、二进制下载或 iframe 内文。返回 result 的分支可用明确 loaded QWeb 组件验证，不为触发它而执行写业务。

在已读基线，以下为 9 个静态 button 定义、7 个 summary 定义、7 个动作 a 定义，加最多两个现有区域标题。循环行会渲染多份，不能用运行时节点数与模板定义数混算。W0 核实际合法增量后记录清单，计数不是业务验收指标。

|控件族|模板定义数|P8 变体与图标|保留内容|
|---|---:|---|---|
|搜索文书|1 button|secondary；前置 search|原 GET、q、maxlength、Enter、P1 busy／恢复|
|预览所选来源|1 button|primary；不另加图标|原显式 POST preview、required、无来源 disabled、hidden 与 P1 loading|
|生成并留存 PDF|1 button|primary；不加“完成”或签署图标|原 generate／expected_digest／key／previous_id；本轮不提交|
|查看原件／下载原件|2 button（每行重复）|查看 quiet，可后置 arrow-right；下载 secondary 无图|原 pdf_view/download submitter、原件编号、POST、target=_blank；不将整行变成操作|
|请求打印原件|1 button（每行重复）|secondary 无图|原 print_request，说明默认规则保持；本轮不提交|
|创建未审核模板／记录审核动作|2 button|各自原表单内 primary，无图|原 template_create/template_review，review/publish 选择不改；本轮不提交|
|导出授权原件 ZIP|1 button|secondary 无图|原 export、原件列表输入和双权限；本轮不 live 提交|
|源／模板追溯、操作追溯、原件追溯、打印入口、模板管理、导出入口|7 summary|disclosure，无新图标|原 details 条件、name、marker、键盘开闭；不叠加第二箭头|
|五个页内工作区链接|5 a|quiet，无图|原 href、文字、两个分组及顺序；不改网站全局导航|
|原件前后页|2 a|secondary，chevron-left/right|原 search_url、q/page、首末条件；边界 span 仍不可点击|
|“查找患者文书”“当前授权范围已保存原件”两个区域标题|最多2 h2|各可前置一个 list；不改其它标题|原文本／层级／aria-labelledby 与内容不变|

控件主次：查询区预览是最高强调，搜索为次操作；重复原件行不再满屏实色主按钮。生成和管理表单的 primary 仅表示该任务的提交动作，不表示“已正式签发／已审核／已签署”。不根据模板选择值加 JS 改危险色。

没有真实危险动作需求就不把 danger 变体强行应用。disabled/busy 只表达现有真实状态；其它状态可在明确组件夹具展示，不能伪造业务状态。无新取消按钮、跳转能力或工具栏。

### 3.1 明确允许的变化

目标元素可增改专用 class、页面 opt-in、文字 span、静态 SVG 及必要原生翻译边界；允许目标按钮／链接／summary 自身尺寸随内容自然增长。允许清理旧 P1/P2/P3 SCSS 中只针对本次目标动作的冲突声明，不得连带删掉同组的 input、combobox、浮层、表格或其它字段样式。

P1—P3 已验外观不是本次动作节点的永久不可改约束。与此同时，原业务属性、字段来源、文本含义和能力保持；将仅允许的呈现变化剥离后，比较原结构和业务合同，不要求允许变化节点的原字节完全相同，也不得通过大范围忽略 DOM 来掩盖差异。

### 3.2 明确冻结

- 两处动态选择器的 JS、trigger/listbox/option、键盘、确认／取消、原生 fallback、composition、required 处理和原 native select 提交源。
- 原搜索和预览表单的字段与顺序，P1 prepareSubmission、addLoadingEffect、form aria-busy、status hidden、pageshow/reset 恢复机制。
- 所有 form 的 action/method/target、type/name/value、csrf/revision/key/operation、disabled/required、权限和条件；保留原隐式 submit 语义，不统一改成 type=button。
- 原件表格列、行、排序、分页口径、生成时状态、患者当前标签／冻结身份区别、UTC 时间、14 个追溯字段及值。
- 原 iframe 的 sandbox、srcdoc、尺寸、预览正文；原 PDF/QWeb 报告模板、纸型、模板版本、生成与保存机制和文件字节。
- previous_id、模板字段、审核发布政策、批量导出规则、输入框/select 的外观与行为；本次不解决后台内部数字 ID 配置入口等新需求。
- 关键用途、合成、待审／待签、未验证出纸、源读取／额外导出权限说明；不能为简洁删去。
- controller/model/service/ACL/schema、原件二进制访问与审计、其他页面和全局品牌。

自然高度变化导致后续区域纵向位移可接受；不要为按钮加图而重排整个布局。

## 4. 同一设计语言与最小资产复用

沿用 DL-01—DL-20，不重新定义一套近似主题。[R4]

|项目|沿用 P7 基线|
|---|---|
|primary|`#94513A` 白字，hover `#7E432F`|
|secondary／quiet 文字|`#7E432F`；浅杏 `#F6E6DC`、暖白 `#FFFBF6`|
|必要边框／焦点|`#8C7564` ／ `#6C513F`|
|圆角／字号／字重|`.625rem` ／ `1rem` ／ 600|
|最小高度／内边距／图文间距|`2.75rem` ／ `.625em 1em` ／ `.5em`，不是固定高度|
|层次|无厚阴影、大渐变、浮雕或装饰动画；最多沿用 140ms 颜色／边框过渡|
|可辨识度|实际普通文字目标 ≥4.5:1，识别必要边界／焦点目标 ≥3:1；装饰线不作交互边界；不宣称整站认证|

### 4.1 一份规范源，不做第二套近似颜色

当前 P7 的规范实现入口是 `ydental_inventory/static/src/scss/inventory_actions.scss`。[R4]

本批允许把其中通用 tokens／基础状态／变体机械提取为一个无顶层选择器输出的共享 SCSS partial／mixin，放在已存在、双方实际依赖的基础模块内（优先既有 ydental_access，开工核依赖）。库存保持原选择器和 opt-in，文书使用独立 actions opt-in 调用同一份规范。不得新增应用模块、前端框架或主题设置中心。

提取是有界复用工作，不是重开库存页：P7 DOM、图标 XML ID、实际 computed 风格、状态和行为不变；以受影响的源码和有限真实代表控件对照验证，不重跑全部 P7。编译器路径／选择器顺序不同不直接判失败，实际生效差异必须检查；不静默改变原 P7 token 值或变体规则。

允许的跨模块改动只限该纯样式提取及必要资源路径。具体 mixin 名称由 Codex 按锁定资产编译能力确定。新公共文件本身不输出 button/a/summary/.btn/:root 规则；全部目标元素显式 opt-in，无表单／页面祖先字体颜色污染。

文书 action class 与动态 `.o_ydental_print_query_trigger` 区分，新增样式不得匹配其浮层或其它模块普通按钮。清理旧 grouped CSS 时保持被排除控件的规则和值。

### 4.2 SVG 只复用 P7 既有五种几何

本批只需要 search、arrow-right、chevron-left、chevron-right、list，不下载新图标库，不增加独立的新图标种类。使用已固定 Lucide `0.468.0 / f12b0de177fbc2a6795e99be065887e72b237123`；P7 原文件及完整 ISC／适用 Feather MIT、SOURCE.json 均保持。[R6]

可通过已满足声明依赖的既有 QWeb 片段复用，或在文书模块建立只含所需几何的局部适配片段并引用同一固定来源清单；不得搬走／改名 P7 XML ID 使旧页失效。局部包装类可不同，但上游路径、viewBox、stroke、线宽2／round／currentColor/no-fill 几何与来源一致，记录适配映射。不能暗依赖“本机碰巧已安装”的模块。

尺寸沿用控件 1.125em、标题 1.25em，显式相对 width/height，aria-hidden=true、focusable=false。图文点击目标是同一原元素，无图标自己的事件处理／独立Tab／重复可访问名称。不用 t-raw、外部 href、script/on*、foreignObject、CDN、字体或运行时图标加载。

不向每个状态、数量或每一段正文加装饰；不把库存 package/scan 图用于文书以凑复用。图标或 CSS 不可用时可见中文、原生元素和原动作仍存在。

## 5. 业务触发分类：外观变化与真正执行分开

本页存在读取型 POST。不能笼统要求“零 POST”，也不能因为 POST 返回200就声称写入成功。

|类别|本批动态测试允许|限制|
|---|---|---|
|GET 查询／分页／原页内链接|允许正常有权读取，图文／Enter按原语义|不修改参数保留规则、不自动选择、不新增客户端缓存|
|POST preview|允许原显式预览既有合成来源，核原HTML/来源/模板|HTML预览不是生成PDF；不得提交generate或创建新来源集合凑测试|
|POST pdf_view、download|允许从现有合法原件行实际读取已保存原文件|读回实际旧bytes与原SHA；不得重新渲染补文件；两引擎内建viewer外壳不是PDF字节|
|POST generate、print_request|不在live页面提交|保留合法能力；源码＋loaded QWeb＋无网络内存FormData核合同，真实仅焦点／开闭|
|POST template_create、template_review（含publish）|不在live页面提交|不以新建／审核／发布模板证明按钮外观；条件缺样使用明确组件|
|POST export|本批不live提交|原选取/权限/submitter字段通过源码与无网络内存组件，原导出测试按未变源码明确复用|

“零新增原件／PDF／打印／经济库存”不等于禁止合法旧 PDF 下载或 HTML 预览。旧文件读取和本地校验副本不是新增业务原件。

涉及禁提交动作的验证：不在真实页面按确认按钮 Enter/Space 触发 submit；可Tab聚焦、summary键盘开闭。需要图标／文字命中与submitter序列化时，使用真实产品片段构建的断开 live 网络的内存组件，保留全部字段与按钮属性，秘密值只在内存比较；不得把拦截了网络的组件结果称为真实业务执行通过。

## 6. 正常流程与边界样例

**P8-F1 查询与预览：**普通医生正常登录选店 → 文书菜单 → 查询姓名／业务号 → 原两处选择器确认／取消 → 显式预览 → 查看已有HTML。未确认的候选移动不预览；未选择必需来源沿原规则提示；无来源禁用保持。添加图文不引发两次提交，busy后可按原pageshow/reset恢复。

**P8-F2 旧原件阅读：**当前授权列表 → 原追溯折叠开闭 → 明确查看／下载同一既有原件 → 回原页 → 原分页保q。行数、顺序、总数、原件版本／生成时状态／UTC、完整hash和文件bytes保持，不把原件已保存理解为已签／已出纸。

**P8-F3 写入口只验呈现：**已预览时显示生成按钮；原打印、模板管理、批量导出details正常可打开并聚焦按钮。真实页面不提交以上操作。不为凑状态新建患者／来源／原件／模板、不临时发布政策。

**P8-F4 共享样式隔离：**文书新控件有统一风格；P1两选择器/输入/浮层不改。库存P7代表查询、summary、确认焦点、来源、分页实际风格不变；其它文书页、报表和结算有限代表不匹配新文书scope。

非空长文字、原件循环、无来源／busy／disabled／管理按钮条件可按真实已有样本及明确组件分层。组件使用实际loaded QWeb/产品CSS，不加临时美化CSS；样本没有的真实权限、状态、页数或正式政策不补造PASS。

## 7. 连续工作包

|工作包|工作|完成条件|
|---|---|---|
|P8-W0 承接与清单|固定真实基线、9/7/7控件族及动态字段例外、字段/submitter/翻译合同；必要前态与当前独立准入|不重新开一轮泛化规划；已有资料按候选适用性复用|
|P8-W1 最小复用与按钮|机械提取P7纯样式，文书元素opt-in/变体，定向消除旧按钮CSS冲突|同一token规范，P7风格保持，非目标输入／选择器不受影响|
|P8-W2 图标与原生翻译|五种以内既有SVG适配、原词边界、控制状态与焦点|当前中文实际加载和可访问名称准确，非PO存在即通过|
|P8-W3 固定候选验证|执行T01—12，普通问题按影响修补；源码/HTTP/浏览器/组件/独立保护分层|已过未受影响证据精确复用，不重复业务链|
|P8-W4 独立验收与收尾|未实现者核实际原件、全阶段保护、包和最终报告；同步读回并停止|技术／同步／用户效果分别表达，不自动下一页|

Codex主控统一写者、运行窗口及集成；产品、测试与未实现者独立验收真实分工，同OS不冒隔离。原可响应团队可复用；正常可用资源内组织必要团队，不重复索要历史/status或精确重置时区。平台实际新限制仍须遵守，不换入口规避。

工具、验收者及前态准备好后再启必要服务窗口，减少空等。按真实环境和候选产生新的有效准入，不能伪改旧期限/STOP或放宽检查。项目软性预算不自动变平台永久禁令；必要真实保护不可省略。

## 8. P8-T01—T12 验收

每项记录实际候选、角色、输入、预期、实际结果、证据路径／SHA／层级、独立结论。没有必要证据即PARTIAL，不以截图多、日志长或同步完成代替。

### T01 范围与合同

逐族映射9 button/7 summary/7 a及最多2标题，开工存在合法增量则明确调整清单；动态combobox为例外。允许呈现剥离后原字段、t-if、t-foreach、文本、链接与表单合同保持。无新JS/接口/数据库模型。主模板及其GET/POST预览回页均正确opt-in、共享partial无顶层规则；其它页无文书opt-in。

### T02 视觉、状态及层级

实际computed与代表原图核P7同token、相对尺寸、原生类型、normal/hover/active/focus、无几何跳动。搜索secondary/预览primary、重复行不满屏primary；必要对比度达到第4节目标。取稳定状态并保留过渡取样失败，不用永久关闭产品动效来证明正常效果。

真实无源disabled和既有busy分清；组件状态不当真实业务。支持引擎核forced-colors/reduced-motion，未支持明确列出，不伪报全站认证。

### T03 SVG来源、降级与名称

核固定上游commit、五种以内原几何／SHA／许可和实际QWeb映射；无额外运行时／外联。可见中文、可访问名称等价、SVG无重复Tab／重复名称。缺SVG／CSS组件仍有原文字和元素可操作，不用截图图标冒按钮。原native marker保持，无重复箭头。

### T04 翻译、事件与P1真实busy

实际Odoo提取、loaded中文、可访问名称均保留原术语。尤其避免SVG/新span令整个含markup字符串变成新翻译键而退回英文；最小t-translation边界按锁定版本处理，不覆盖共享旧词条。

真实图／字／Enter查询按原单GET；原预览显式一次POST，source required/无源disabled／两选择器确认取消保持。P1 form aria-busy与addLoadingEffect、恢复、原具名提交字段不丢。取得真实发生状态的有限证据；需要人为延迟／取消时明确组件层，不伪造提交成功、不新增loader逻辑。

### T05 原件读取与页内行为

普通有源角色从实际行分别查看／下载一个现有原件，原POST csrf/revision/original_id与name=operation值正确、target=_blank保持。对实际旧bytes计算SHA，对照既有记录及文件；不能以浏览器PDF壳或仅响应声明头替实际字节。无需重验全部历史PDF页面。

原追溯/分页/页内链接保持类型与参数；可用多页就取有限真实前后页，不造原件制造页数。既有临床草稿／摘录／完整来源差别不改。

### T06 不提交写入的合同证明

对generate/print_request/template_create/template_review/export逐项核原字段、隐式/显式type、submitter、权限条件、required和disabled。真实只开闭／聚焦；loaded QWeb/无网络内存FormData验证所有渲染分支，不把组件身份当真实授权。

不得因测试只读而隐藏或禁用合法入口。无新生成/打印/审核/发布/导出业务请求，无假“成功”反馈。PDF旧读取与新生成分类。

### T07 五视口、长文与表格衔接

1366×768、1440×900、768×1024、390×844、320×800。图文保持完整、自然高度／换行、原表格可局部横读，操作区不新增根溢出或重叠。旧文书页320/345限制若仍存在按前后实测单列，不要求本批修整页，也不强制保持旧宽度。

长中文按钮、链接、summary、低频管理按钮用明确组件压力，不改真实文案；首末字符与全部必要文字实际可达。单份DOM，不复制一套移动表单／重复token。

### T08 双引擎、两种放大、键盘与无JS

真实Chromium＋WebKit或Firefox执行代表正常查询/预览/旧原件/分页/summary路径；两引擎各自原生200%与独立根字号200%分列。不是User-Agent伪装，实际主进程退出与每次命令归档。

真实Tab轨迹覆盖代表操作，summary Enter/Space开闭；业务写按钮只Tab聚焦不提交。programmatic focus与自然Tab分别记录，不以一种冒另一种。无JS时以原native表单/两select/details/旧文件读取验证；登录层沿既有正常认证，不复制Cookie、不修改登录。无JS只需代表桌面/窄屏，不重复整份hover矩阵。

### T09 权限与未改规则

原普通有源无exportwrite可按原契约读单份；无源／跨域实际旧原件拒绝，不用空壳页面200冒403。复用已固定且后端未改的完整撤权／门店revision／批量双权限证据，明确复用候选和边界；不为了本批重授／撤权全链。

模板管理按钮的显示不代表有权限，后端规则保持；不因按钮美化扩大普通岗位模板发布权。正式政策未批准仍未批准。

### T10 最小复用与旁路

库存P7实际代表normal/hover/focus/summary开闭及查询来源GET在公共提取后保持，字段和原件／scope不变；不重跑13族全历史业务。文书两combobox/input/listbox、iframe正文、14追溯原值和表格单元内部样式保持；其它同意／打印入口和报表／结算各有限代表不被新样式污染。

已改变的目标控件可自然位移，不用整页像素相同作为新门槛。动态时间／nonce等事先明示字段归档；未保存before全文就不声称归一化全文同，不大范围删字段比较。

### T11 必要加载和全阶段独立保护

固定最终产品/工具/运行/报告；有模板或注册变化才做必要模块加载，各有即时pre→实际退出→post及独立差异分类；纯样式编译以真实bundle/computed核，不为报告或CSS重复-u。

最终未实现者新物理RO/RR完整核当前业务/技术投影、83引用与80唯一文件（按现场实际清单）字节／尺寸／SHA及全阶段变化。共享引用不删除、不将引用数与物理文件数混称。旧审计、金额库存、身份作者价源、责任全部保留；新正常访问审计和必要模板／资产技术元数据分类，不宣称全库物理零diff。

P7原17431及其新增200条审计都属于后续历史保护，不清零。新SVG技术view、bundle不是业务原件，不因新增技术资产误判金额库存变化。

### T12 独立交付、包、同步与停止

未实现产品或测试工具者核实际原始结果/源码/图/字节/完整保护。全部适用T项成立才TECHNICALLY_COMPLETE；必要第二引擎、保护或独立验收缺项则PARTIAL，列具体缺口，不转做下一页。

私有效果包使用唯一文件名和截图编号，防止P7前态同名覆盖问题重复发生；真实before/after、候选／角色／视口／scrollY、组件／缺证据分列，不重建旧截图冒历史。所有成员/源字节/SHA/PNG独立核，截图数量不是门槛；无凭据/session/profile/raw请求/完整DB投影/程序字体。纯截图包不代完整保护。

正常owned服务／浏览器收尾，最终同步ref和必要完整正文/评论实际读回；不循环把读回本身的hash嵌入自身导致无限文档提交。最后元数据提交只按实际增量读回，不触发重新测试。

## 9. 数据、资源及真正停止条件

复用唯一既有合成目标与filestore；不新建／克隆／改名库，不修改Odoo核心、odoo-12、共享OS／防火墙／集群策略。正常私有凭据和测试身份按现有授权使用，不让用户找旧密码或桌面作为计划实施前置。

当前固定应收保护事实1303（1073旧来源＋前批230）、lot253收10/用2/余8与全部未完成责任保持；不是未来查询的硬编码期望。旧PDF标签draft、当前工单sent、草稿/摘录/完整等状态不能为展示改写。

本轮新增业务原件/PDF生成/打印请求/签署/模板创建审核发布/经济库存/扫码动作均0。允许HTML预览与旧文件读取产生正常审计。实际未知持久提交、权限/完整性异常或当前工具安全拒绝，只停止受影响动作并保留准确事实，不绕过；普通路径/选择器/翻译/等待错误内部修复，无依赖工作继续。

历史额度UNKNOWN和旧准入过期不是当前开工理由；无需再次索要剩余额度及重置时区。正常模型任务实际返回新限制才按事实处理。阶段内合理安排人员和有界运行，旧记录不伪改。

## 10. 最终交付格式

维护同一个活动 `CURRENT_TASK.md`；本计划落指定execution路径。

三报告：

- `docs/reports/s13-dl-p8/summary.md`
- `docs/reports/s13-dl-p8/acceptance-matrix.md`
- `docs/reports/s13-dl-p8/evidence-index.md`

交付应包括完成/未完成/偏离、固定产品/工具/运行/报告、控件族/变体/图标映射、共享提取前后库存证明、原字段/submitter/翻译契约、读取／非提交组件分层、保护和失败/UNKNOWN、普通角色5—8步复现。公共只放代码、计划、许可与脱敏报告索引；原图和效果包不上传Public。

私有包建议 `.local/dl-p8/viewing/S13-DL-P8-view-only-<实际日期>-r1.zip`；不覆盖P7或更早包。旧PDF实际下载证据留本机校验即可，效果包无需再复制全套原件。

最终摘要：

```text
[CODEX-FINAL] YD-S13-DL-P8 / 1.0
技术：TECHNICALLY_COMPLETE / PARTIAL / BLOCKED
同步：SYNCED / SYNC_PENDING
用户亲手效果：待确认，或仅列真实确认的具体范围
完成范围：文书主页面动作控件／轻量SVG，非全站
完整S13与后续页面、合并部署生产：未启用
固定产品／工具／运行／报告：实际值
保护：实际引用数、唯一物理文件数分别列，业务新增0及正常技术差异分类
```

最终正常commit/push并读回；仅#37新增一份P8最终结果且OPEN，P1—P7旧评论及P5 PARTIAL历史不改，#36 CLOSED。main只必要路由，不合产品、不部署。服务正常收尾，交付后停止；后续报表/结算推广另由用户交付限定计划。

## 11. 固定来源说明

以下为本计划事实基线；新规范范围见正文，不把来源中的已完成声明扩大成用户亲手或生产批准。

- R1 [P7固定报告](https://github.com/Yredxin/YDental/blob/9f5ce4626895cb8f3da0562d9170e79220728378/docs/reports/s13-dl-p7/summary.md)
- R2 [P7矩阵](https://github.com/Yredxin/YDental/blob/9f5ce4626895cb8f3da0562d9170e79220728378/docs/reports/s13-dl-p7/acceptance-matrix.md)
- R3 [P7唯一回执](https://github.com/Yredxin/YDental/issues/37#issuecomment-6399387525)
- R4 [P7按钮唯一实现](https://github.com/Yredxin/YDental/blob/9f5ce4626895cb8f3da0562d9170e79220728378/ydental_inventory/static/src/scss/inventory_actions.scss)；已交P7设计补充/完整计划及DL-01—20术语。
- R5 [文书实际模板](https://github.com/Yredxin/YDental/blob/9f5ce4626895cb8f3da0562d9170e79220728378/ydental_print/views/ydental_document_templates.xml)；同ref ydental_print/controllers/documents.py、ydental_print/static/src/documents_query/documents_query.js、ydental_print/__manifest__.py。
- R6 [固定图标来源](https://github.com/Yredxin/YDental/blob/9f5ce4626895cb8f3da0562d9170e79220728378/ydental_inventory/static/lib/lucide/SOURCE.json)；该目录已保存的原SVG与完整许可。
- R7 现行路由与协作：main/GPT_HANDOFF.md、AGENTS.md、CURRENT_TASK.md及活动分支同名状态；开工再次核合法新增量，不将本文锚点当回退要求。
- U1 用户本会话确认的暖色、弹性布局、统一控件、适量开源SVG和分阶段交付要求；本计划只将按钮推广到下一页。
