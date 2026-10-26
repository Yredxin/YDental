# YDental / odoo-sd｜DL-P11 完整限定实施计划

计划编号：YD-S13-DL-P11 / 1.0  
名称：经营报表来源钻取详情页——暖色动作、只读层次与间距整理  
制定日期：2026-10-26  
仓库保存：docs/execution/S13_DL_P11_IMPLEMENTATION_PLAN.md

启用规则：本文件由用户与随附启动提示共同交给 Codex 时才启用；只启用 P11，不启用结算、全站或完整 S13。用户已在本次会话明确启用，以下保留交付计划的范围、标准和边界。

## 1. 项目背景与承接结论

YDental 基于锁定的 Odoo 20 Community 核心 f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb 与已验自研模块持续演进。DL-P1—P6 先后分区域完成文书、报表主查询、结算只读查询和仓库只读定位；P7—P10 逐页落实统一暖色按钮、轻量 Lucide SVG 和层级化间距。仍遵循“一个可见区域或页面一阶段；阶段内自主实施，阶段间不自动扩大”。

上一阶段 DL-P10 已交付 TECHNICALLY_COMPLETE / SYNCED，但限定于 /ydental/reports 主页面，不包含独立来源详情和错误页。当前可核对锚点：

|对象|已知承接值|
|---|---|
|活动业务分支|`codex/s13-dl-p10-report-actions-spacing-r1`|
|P10产品/实际运行|`8a1547a14f5647d6a49555c8ab7f9ceb658511e3`|
|P10工具最终发布|`2c18d3271b49ab1ba2d6622e1755ed9678a97997`|
|P10最终报告HEAD|`6d74bbe0b95fc1dbfbacd51e9d2475ee52749e36`|
|P10唯一最终回执|#37 / `6408631886`|
|新业务分支建议|`codex/s13-dl-p11-report-source-detail-r1`|
|合成目标（核真实身份）|`ydental_s11_synth_20261023_01` / OID `2171423` / cluster `7694897083368259627`，原 filestore|
|保全基线|83 个附件引用、80 个唯一物理文件/路径与 80 个不同 SHA；3 个既有共享引用不丢、不去重|
|Issue|#37 OPEN，#36 CLOSED；P10 之前唯一回执均保持|

本次计划制定时只读核对了 P10 报告/矩阵/远端分支与源码，以及用户提供的私有只读 ZIP。该 ZIP 4,433,215 字节，SHA256 feddb5fab4c00e0a462dee6faba5e5d7e061e668a0d82a0f041676a21f791dba，56 个成员，55 个 manifest 非自身项逐项 bytes/SHA 匹配、52 张 PNG 可解析；查看代表桌面/窄屏前后图。这是静态复核，不声称 GPT 本次重跑真实数据库、浏览器或重新独立签署数据保护，用户亲手效果仍待确认。P10 的旧 320px 根溢出、WebKit 无 JS 导出 native 文件/BOM 未观测，以及先前所有失败/UNKNOWN 继续保留。

本轮目标：让报表来源钻取详情页与已完成的主报表页面拥有同一套“杏陶暖白＋温和按钮＋适量图标＋组内紧组间松”的视觉语言，同时保持真实来源的只读再授权、金额/日期/状态、跨店提醒、来源链接和返回过滤条件完全不变。

## 2. 依赖、范围及冻结区

### 2.1 进入顺序与权威

先读固定入口 main/GPT_HANDOFF.md，main/AGENTS.md、main/CURRENT_TASK.md，按路由读 P10 活动 CURRENT_TASK.md、P10 完整实施计划/三份最终报告与 #23/#37 有效增量，再核实际 Git origin/HEAD/工作树、唯一主控和合法未提交增量。main 是文档路由，不是产品基线。锚点不是回退指令；不得 reset、clean、强推或覆盖未提交工作。

必须阅读当前原生模板/控制器及源合同：

- ydental_reporting/views/ydental_reporting_templates.xml：ydental_operating_report_source、共享 ydental_operating_report_navigation、ydental_operating_report_scope，与 P10 主页面、error 模板。
- ydental_reporting/controllers/reporting.py：source()、return_url、_query(..., all_rows=True)、源行再授权及 _failure()。
- ydental_reporting/static/src/reporting/reporting.scss、P10 report_actions.scss / report_spacing.scss 及 manifest。
- ydental_access/static/src/scss/_actions.scss 现有纯 mixin、P7 的固定 SVG 几何和许可记录。

需以当前实际合成 QWeb 视图、锁定核心与加载依赖为准，不猜旧版本接口。

### 2.2 唯一主页面

允许的呈现范围：/ydental/reports/source/<metric>/<source_id> 正常 GET 详情页面所渲染的 ydental_reporting.ydental_operating_report_source。本批可以只对该源详情页面进行以下工作：

1. 页内三条原导航链接：适配既有 quiet 动作风格；仅本来源详情页生效。
2. 顶部和底部两处 Return to the same report filters and page：同一返回语义，适配 secondary/返回箭头，保留原 return_url。
3. 标题、只读说明、已生效过滤/时区/查询时点摘要：梳理视觉优先级与上下间距；原 scope 字段、顺序和文字不删。
4. 每条源详情 article：仅调整背景/边框为低饱和暖色、容器 padding、标题与患者标签、金额／状态／业务日期与 facts 的垂直节奏；不新增总额或隐藏原字段。
5. 原有 dl（facts_display）：保持 dt/dd 对应、原值/顺序/转义，只可局部调整 Grid/Flex 组间/换行，避免长中文、混排和哈希撑宽整页。
6. 有分摊时的原 table：保留原 4 列、行、数值与内层操作链接，允许对账单链接做轻量 quiet 样式、表格外框与其周边留白；不改表头、列逻辑、单元 padding/宽度语义及局部横读。
7. requires_store_switch 的跨店操作提醒必须原位默认可见、保持信息准确；可用暖色提醒底/边，但不得弱化为普通装饰文字。
8. “Open the source business page”“Native source document” 两个原链接：只改外观、轻量 arrow_right（如确有助于识别，避免双图拥挤）；保持原链接和权限重检，不自动切门店。
9. “Technical trace and complete source facts” 原生 details/summary：统一 disclosure，保留原 marker、不加重复箭头，展开后完整原模型名、ID 和 pre 文本可读但不抢占正文。

本轮明确不做：P10 主报表查询区、指标结果/分页/CSV、报表 error 页、结算、仓库、文书、共享网站导航、PDF、数据库结构、后台权限、全局主题、Odoo 后台迁移、实机、正式政策。此次不允许以业务优化理由修改 controller/model/service/ACL、指标字典、分摊公式或来源链接目标。不要顺带全面重做来源详情排版或引入另一套 UI 框架。

### 2.3 共享模板隔离

当前 P10 在主模板用 data-dl-layout="report-actions-spacing" 和仅主模板 opt-in；共享导航/范围模板存在 report_main_actions 局部传参，默认不开。P11 必须采用详情页独立 data-dl-layout 和元素 opt-in，并对 source 目标单独传递局部上下文（如 report_detail_actions，按实测 QWeb 可用方式落地）。保留 P10 的 report_main_actions 及主页面编译结果、字段和焦点表现不变；error 页不 opt-in。

若实装采用不用改共享片段的局部后代选择器，仍须保证真正复用既有 mixin、没有全局按钮/链接/summary 污染，且写明独立隔离证明。不得复制另一套共享 nav/scope 的业务节点，也不得通过更改控制器来传视觉参数。源详情 GET 有/无分摊、跨店提醒有/无的条件分支都需保持。

## 3. 设计语言与可量化实现约定

本阶段沿用已认可的 DL-01—DL-26，特别是：

- DL-15—18 统一动作族与状态矩阵：primary、secondary、quiet、disclosure。详情页以 secondary 返回、quiet 来源链接为主；只读页面不需要新增实色主业务按钮，不得把“打开原生单据”画成“已执行”。
- DL-19—20 单一线性 SVG、图文视觉平衡：只调用 P7 既有 Lucide chevron_left / arrow_right，确有需要可用既有 list 作为唯一页标题图，不强迫每行图标。保持 0.468.0 固定上游 commit/SHA、ISC 与适用 Feather MIT，使用 currentColor、相对 em、aria-hidden/focusable=false，可见中文标签不移除。无额外图标、CDN、字体或 JS runtime。
- DL-21—26 层级化间距与单一归属：标签紧随值，组间有呼吸感；不靠全页 margin 放大、不用固定行高/空段落/全局裁切凑留白。保持按内容自然撑高，窄屏局部横读。

默认间距参考基线，以 16px 根字号换算，真实使用 rem：

|关系|参考值|责任与允许调整|
|---|---|---|
|同一导航/链接组内|12px（.75rem）|组容器 gap，与链接自身 padding 不重复|
|返回链接 → 页面标题|16px（1rem）|标题/相邻组之一单独负责，不叠 margin|
|标题 → 患者/概述|8—12px|由 source card 内 grid/flex gap 负责|
|总说明 → 已生效范围；范围 → 第一来源卡片|24px（1.5rem）|由相邻模块之一负责；缺结果不留空洞|
|源卡片：身份→金额状态→业务日期|12px（.75rem）|内层布局 gap，原内容及顺序不变|
|日期/概要 → facts；facts → 有分摊表|16px（1rem）|分组外间距唯一负责人|
|dt 与对应 dd|8px（.5rem）或既有可读值|不得把一条 key/value 拆成无关两组；已有格局合格则不机械修改|
|有权跨店提示与操作链接；操作链接与技术追溯|16px（1rem）|只有对应节点存在才留间距|
|展开 summary → 首段内容|12px（.75rem）|仅展开时生效，关闭不留洞|
|相邻两个 source card；尾部返回与前段|24px（1.5rem）|组边距，卡片上下不双加|
|卡片内部 padding|桌面24px，≤45rem窄屏16px|保持 P10 已验页面的视觉基调，不产生嵌套双卡片|

鼓励新建局部 report_source_detail.scss 并用同一 @include o-ydental-actions 及 report-source-actions opt-in；实际依赖和打包顺序与 P10 已验实现协调。可以仅清理详情页明确冲突旧 CSS，不改共享 _actions.scss、P10 main CSS 或 P4 两 JS。所有实现落正常资产与真实 QWeb，不能临时注入效果图样式。

## 4. 业务合同、操作语义和安全边界

1. 报表钻取只读：现有 source() 根据 metric/source_id 和相同显式过滤调用 _query(..., all_rows=True)，再从授权范围中寻找来源；无源、无权或越界按原接口返回拒绝，不能因页面风格跳过后端再授权。
2. 页面标题、业务来源名称、患者、金额/数量、单位、领域状态、业务日期、facts_display 和分摊来自服务器原投影；不得改变名称、排序、过滤、精度、UTC/本地日期或动态 query_at 的语义。
3. 当前应收只表示查询时点余额，不能将日期筛选改称历史截至日；实收不是营业收入，贷项不是现金退款，已批准退款与实际退款不同；跨店去重和币种/单位不能混算。
4. 两处 return_url 必须仍是同一实际目标：返回同一过滤及页码，来源列表已生效条件与草拟条件仍分开，不自行添加 revision/门店会话/patient_id 等参数，不因样式为已选来源额外改URL。
5. row['requires_store_switch'] 提示必须可见；报表能看某店来源不等于在当前门店有权操作。row['business_url']、row['native_url'] 和 allocation['url'] 的 href 原值、标签和源服务器权限保持，不能自行替成无权限控制的附件链接或自动切店。
6. 技术追溯保持原模型名、原 ID、源 SHA/文本/完整 pre；只是视觉层级后移，不删、截断、原地重新生成或静默改写。源码中 t-out 的转义保持；图标装饰不能代替中文业务标签。
7. 本轮普通岗位只允许原 GET 查询/来源详情/返回和明确受控的只读源单导航（如果当前正常权限允许）。不运行任何结算、退款、库存、治疗、接收/入库、文书生成、打印、模板发布、组合扫码或外部通道动作；不为照片新造原件/PDF。不以删除合法链接或隐藏警示换取“安全”。
8. P10 所有主页面字段、多店选择、指标切换、真实 busy、已有 CSV 导出与钻取合同保持；不为了本次截图重跑它们的完整负载/经济链。报告登录、读取和拒绝审计按实际分类，不声称数据库物理零变化。

## 5. 文字化使用流程（F1—F5）

F1 有权来源钻取与返回：普通有相关来源读取权角色正常登录/选店 → /ydental/reports 已生效的日期、门店和指标 → 点“查看来源与分摊” → 详情标题、授权范围与查询时点 → 来源事实/必要分摊 → 页面首尾两处返回 → 核原过滤/页码；未进行收款/库存操作。

F2 双来源与长追溯：同一详情可有多个 display['rows'] 或长 facts_display 时逐卡显示 → 使用键盘打开技术追溯，完整 pre/长值可局部阅读；没有这样的现场真实样本时只使用明确 LOADED_QWEB / BROWSER_FIXTURE，不创建新来源。

F3 分摊与跨店提醒：当前有 row['allocations'] 的合法来源 → 保留每一项账单、原金额、分摊、当前应收；当前跨店来源仅按既有 requires_store_switch 显示提示。链接保持原地址，未授权不能因为有报表权限直接办理。

F4 无授权或过期条件：无源/无权限/旧筛选或篡改 source_id → 服务端按原后端拒绝或原错误页；P11 局部样式不覆盖该错误页、不泄漏受保护字段。界面不得把无结果误称账务结清。

F5 响应、缩放与降级：五个指定视口、两种 200% 与文本间距压力下 → 中文换行/操作对齐/键盘焦点完整可见 → 表格只在局部横滚 → 无JS时仍可原生展开详情/导航/返回；SVG/CSS 缺失时仍以原文本与原链接可达。

## 6. W0—W4 持续实施工作包

|工作包|具体工作|完成条件|
|---|---|---|
|P11-W0 定界与前态|读取路由/合法HEAD/当前目标；核 source/main/error 实际渲染、条件分支、原 href/字段与局部样式；建立各角色/来源候选，准备未实现者与读保护前态|精确基线/白名单/原始错误已固定；不用用户反复找密码/新SSH或泛化方案|
|P11-W1 来源页视觉层|仅 source 模板动作、图标与可选局部 warm card/note/facts 样式；复用既有纯 mixin 和固定 SVG；共用片段仅来源上下文 opt-in|真实原入口加载而非静态 mock；main/error 无新增 P11 marker/样式污染|
|P11-W2 间距/可达|按责任表整理导航/return/标题/scope/每条 source card/facts/分摊/跨店说明/链接/追溯与末尾 return；只在 source scope；不增加重复内外 margin|五视口、两种放大、真实与组件长值、原生 table 与 details 无裁切粘连|
|P11-W3 定向回归|执行 P11-T01—12，含真实浏览器/HTTP/权限/无JS/旁路/必要资产加载；普通修复内闭环|真实层级区分；未影响项按原证据/源码影响精确复用，不重跑历史全链|
|P11-W4 独立验收与交付|未实现者核源码/浏览器/完整业务保护与唯一文件/许可/效果包/最终候选；格式化报告、正常同步读回和 owned 收口|提交唯一P11最终结果，#37仍OPEN；P11完成立即停止|

上述 W0—W4 是一个阶段内部连续工作包，不是五次 GPT 审批。Codex 可自行多agent安排、测试、普通修复与独立验收；独立验收者不得为自己实现的产品或对应测试工具自签。主控统一写者、服务和证据归属，不把角色名冒称操作系统隔离。

## 7. P11-T01—T12验收矩阵（预期与证据）

实际测试须记录候选/实际作用域、普通角色与筛选、真实命令/退出、预期与实际、证据层级、失败与独立结论。基线不变化的部分可精确引用固定证据，不为增加数字重采。

|编号|要验证的内容和具体通过条件|必要证据层级|
|---|---|---|
|T01 精确范围|source模板和局部shared nav/scope opt-in；main P10及error无 P11 marker；form/字段/源标签/URL/条件/顺序/授权恢复后和此前一致；无 JS、backend、schema/ACL/指标改动|SOURCE/PURE + loaded QWeb 与前后真实DOM|
|T02 动作与SVG|3导航、两处返回、每条业务/原生来源链接、分摊原链接、scope/trace disclosure逐族映射；同一按钮 tokens/中文/图文视觉平衡、focus/default/hover/active及必要状态；Lucide原 SHA/许可原样|SOURCE+CSS/BROWSER；无图标 runtime/独立Tab|
|T03 间距与容器|实测来源详情 8/12/16/24px 层次、桌24/窄16内衬，卡片/导航/链接/展开内容不粘连；每一空隙单 owner，缺分摊/跨店提示/关闭 details 时不留洞|真实 COMPUTED/BOX + 前后原PNG/责任表|
|T04 业务投影原值|title、scope/query_at、患者/状态/单位/金额/业务日/facts_display/分摊4列原顺序和值保持；动态查询时点只按原字段分类，不作全局时间归一化|SOURCE/真实 HTTP/DOM；必要时 JSON 或原投影定向对照|
|T05 来源地址与返回|两 Return 保留同 return_url；业务、native、allocation原href/条件值一致；来源再授权且返回到已生效过滤+页码；不变更工作门店，不执行业务|普通身份真实 GET 链/服务端记录；组件只用于欠样分支|
|T06 权限与跨店|已授权来源确可只读；无源/非授权/篡改来源/跨店业务URL仍按原权限拒绝或提醒；错误页不受样式影响，无升级读写或参数泄露|真实 HTTP 后端负例 + SOURCE影响复用，0临时提权|
|T07 五视口响应|1366×768、1440×900、768×1024、390×844、320×800；长中文/编号/trace/分摊单元完整可读，焦点可达；不新增本source root溢出，已有其它页面历史根溢出单列|Chromium/WebKit实际前后、明确组件长值/分摊分支|
|T08 两种放大|两engine分别原生200%和独立root32，重点双返回、links、table水平阅读、展开全文及完整focus外圈；不把缩视口冒放大|真实浏览器/原PNG/计算位置|
|T09 键盘/无JS/降级|自然Tab/ShiftTab/Enter/Space、原生summary、链接点击正常；禁JS后仅原生导航、read；缺CSS/SVG有完整中文与原链接，AX不冒屏幕阅读器|实际浏览器、正常登录的JSoff和明确 fault 组件|
|T10 主报表/旁路冻结|P10主页面已生效/草拟分离、控件/样式/P4 JS与原CSV格式源码保持；文书/库存/结算有限只读旁路不污染；详情/error显示与原条件结构不冲突|SOURCE/编译CSS隔离+必要真实页面采样；不重跑经济链|
|T11 资产与完整保护|若需必要模块加载按真实pre→exit→post保护；最终未实现者新物理只读核145业务/13技术/现场完整83引用-80唯一路径实际 bytes/size/SHA，旧金额库存/身份/价源/审计/责任保持；新增PDF/原件/经济库存/打印等0|实际 MODEL/HTTP 日志 + 独立新 physical READ ONLY/REPEATABLE READ + 文件，normal audit单列|
|T12 最终独立交付|固定产品、工具、运行、报告候选，含失败/UNKNOWN；验收矩阵、效果包SHA/manifest与5—8步复现；真实远端ref/报告/comment与Issue状态读回；owned/browser资源正常停止|未实现者独立SOURCE/包/运行/同步复核；技术与SYNC状态独立|

无现场可用的多分摊/跨店/多行卡片/长追溯数据，以明确内存QWeb和真实产品CSS的 BROWSER_FIXTURE覆盖显示，不向原合成数据库制造新经济或来源链凑样。不得用组件冒真正授权或真实多记录。Chrome viewer壳不能当旧PDF原字节；本轮通常无需下载PDF，若进入原生单据只读下载须真实权限及文件校验，不能因为“视觉验证”调用生成/打印。

## 8. 完成标准、交付格式与停止条件

只有本批 P11-T01—12 的适用软件断言、范围隔离、真实双引擎、无业务副作用、未实现者独立完整保护与效果包核验成立，才能标 TECHNICALLY_COMPLETE；否则 PARTIAL 并准确列缺项。GitHub 同步单独记 SYNCED / SYNC_PENDING，不能拿同步充当技术验收。用户亲手效果继续待确认。

必须输出：

1. docs/reports/s13-dl-p11/summary.md：目标、实际范围/差异、候选、前后视觉、字段/URL语义、独立证据和保留失败、5—8步真实普通岗位复现。
2. docs/reports/s13-dl-p11/acceptance-matrix.md：T01—12逐项条件、预期/实际、源码位置、层级、原件及独立结论。
3. docs/reports/s13-dl-p11/evidence-index.md：私有只读原图、运行、权限、保护、包来源与 SHA 的脱敏索引。
4. 私有只读效果 ZIP：同角色/指标/过滤的前后图片、真实5视口与两种放大、至少一个详情卡/分摊或明确组件、长追溯/折叠/返回；真实浏览器截图不编辑；完整manifest/SHA与隐私检查。不上传Public，不含凭据/Cookie/profile/原请求/完整数据库投影/原件PDF/CSV/字体。
5. 当前活动 CURRENT_TASK.md 记录已发生事实、测试限制和新旧候选，不覆盖早期PARTIAL与UNKNOWN。
6. 阶段末按现行 WORKFLOW-V3 正常提交推送、真实读回 ref、全文与唯一最终 P11 回执；#37保持OPEN、#36保持CLOSED，P1—P10原评论不改；main仅必要路由文档，产品不合main、不部署。
7. owned服务、浏览器、临时测试身份/权限正常收尾。历史STOP与到期不修改，缺新的必要准入只按现行正常机制核，不把旧额度UNKNOWN当开工前置；真实当次平台限制仍须遵守。

阶段完成后立即停止。P12或后续结算/其它岗位、整站样式统一、完整 S13 的50活动会话/全链/持续备份与恢复、物理打印和扫码、正式医疗/财务/税务/电子签署政策、S11一次扫码接收并入库、外部支付/真实患者、生产、合并与部署均不在本批自动授权范围。
