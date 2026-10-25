# YDental｜按钮与 SVG 设计补充及首批实施计划

计划：**YD-S13-DL-P7 / 1.0**  
日期：2026-10-25  
本批名称：统一按钮语言与轻量 SVG——仓库页面试点  
启用来源：用户在本会话交付本完整附件及启动提示，明确按W0—W4连续实施。

用户把本附件与启动提示交给Codex，才启用本批实施。最终目标是逐步覆盖YDental常用页面的按钮与动作控件；本次只实施 `/ydental/inventory`。不是全部页面同时改造，也不是库存业务开发。

## 1. 背景、承接与证据边界

用户新增需求：所有按钮应适应所在页面，质感柔和、配色协调，适量采用开源SVG。“重写”明确为统一表现与组件样式，不重写权限、提交或业务处理逻辑。P1—P6按当时限定范围完成，不因新设计要求被倒判失败。P6搜索按钮已为陶土色，来源与分页已有暖色链接；办理和“仅识别”此前冻结，仍存在原生或旧样式，这是分阶段范围留下的差异，不是新资金或库存错误。

计划制定时GPT已读P6固定报告、矩阵、最终评论、当前分支及库存模板/SCSS，核用户上传r2包2,360,375B、SHA256 `b7db94f37dd540eedefac890863efa01d2fba0a7eef887cc5650d408f87eb430`；37项manifest字节与SHA一致，33PNG可完整解码，查看查询、来源、分页代表原图。该检查不是重新运行浏览器/数据库、重签83文件现场保护或用户亲手验收。原P6技术交付承接，用户效果待确认。

|对象|已核锚点（开工核合法增量，不是回退指令）|
|---|---|
|业务分支|`codex/s13-dl-p6-inventory-lookup-r1`|
|P6产品/运行|`aec20359d6f0cdc0e7a1f1070bcc870fd0798b95`|
|P6工具/前态|`539d147d659a6214d16e2796460728912f810ccf`|
|P6报告|`e31ea56d1ff903461eda86c08088c5f7e32aef7e`|
|P6唯一回执|#37 / `6397824653`|
|锁定core|`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`|
|既有合成目标|`ydental_s11_synth_20261023_01` / OID2171423 / cluster7694897083368259627及原filestore|
|承接保护|83实际文件、65内部+2外部原件；数量现场完整清单核，非永久硬编码|
|建议P7分支|`codex/s13-dl-p7-inventory-actions-icons-r1`|

先按main/GPT_HANDOFF、AGENTS、main/CURRENT_TASK路由，读活动CURRENT、P6三报告、现有设计规范、#23/#37正文及相关有效增量和#36状态。核origin、真实工作树、增量和唯一写者，保留未提交工作；不reset/clean/强推、不从文档main重建产品。

## 2. 分批路线与本次停止线

|批次|范围|状态|
|---|---|---|
|本批DL-P7|按钮/图标规范；仓库主页面全部既有按钮、取消/来源/分页动作链接、办理折叠入口呈现；极少标题图标|本次用户明确启用|
|后续A|同规范推广到文书、报表、结算的查询/只读区域|未启用，届时独立完整plan|
|后续B|结算等岗位办理/危险动作分页面整理及其它常用页|未启用|

“所有按钮最终一致”是覆盖目标，不是同一种颜色、同一操作或本批全站替换。后续复用已验证规范，不各做一套。P7完成后停止，不自行编造P8或开始其它页面。

## 3. 设计术语：续接DL-01—14

以下是新增设计约定，不声称P6已经实现，不另画全站UI架构图。

|编号|名称|定义与检查点|
|---|---|---|
|DL-15|统一按钮组件体系|一组颜色/圆角/字号/间距/状态变量，按任务选变体，同类同尺度，文字/图标/边框有唯一规范来源|
|DL-16|柔和扁平与轻层次|暖底、圆角、薄边、小面积重点，无厚阴影/浮雕/黑框/大渐变/发光/玻璃；不能用低对比换柔和|
|DL-17|语义化强调层级|主/次/轻量/危险分层，同一区域一个最高层级；查询突出，重复来源克制，不掩危险|
|DL-18|完整状态矩阵|default/hover/active/focus/真实disabled/busy明确；不跳尺寸，无真实busy不伪装提交|
|DL-19|单一线性图标语言|同一家族小子集、统一网格/圆角/线宽/颜色；不混emoji、不同库或实心卡通，保留必要文字|
|DL-20|光学对齐与视觉重量平衡|小图辅助、文字为主，尺寸/间距/视觉中心协调；少重复，不用图填空，长标签窄屏放大可用|

### 3.1 按钮层级与配色

沿用杏陶暖白，不再选主题，不全局覆盖Odoo配色。

|变体|适用|基线|
|---|---|---|
|primary|查询；已展开办理表单最终确认|陶土#94513A白字，hover#7E432F；不让来源行全实色|
|secondary|上一/下一页、辅助动作|浅杏#F6E6DC或暖白，深陶土#7E432F，细边|
|quiet|查看本条来源、取消返回|无大块实色，深陶土、必要下划线/轻底hover，仍清晰可点击|
|disclosure|原summary|暖字/柔和边界/焦点，原生标记与行为，不叠第二箭头|
|danger|以后确有不可逆/破坏语义的固定动作|独立受控危险色+文字；本批只定义，不臆断所有确认危险，不按select加JS|

其它参考：正文#382F28，次要#716359，局部表面#FFFBF6，焦点#6C513F。次按钮在浅杏底需边界时可用#8C7564；不可照搬白底通过但hover浅底失败的组合。

圆角建议.625rem，字1rem/500—600，min-height2.75rem随字号内容撑高，padding约.625em 1em，gap.5em，inline-flex及换行/min-inline-size约束，不固定中文宽高。动作组Flex可换行，不绝对定位图标。默认无阴影，必要仅一层很轻辅助，不能作唯一边界。仅约120—160ms颜色/边框过渡，无移动缩放弹跳装饰循环，尊重reduced-motion。普通字实际对比≥4.5，必要控件边界/图形/焦点≥3；装饰分隔线不强迫，不称整站WCAG认证。[W3][W4]

### 3.2 原生语义与状态

- button/a/summary各保留原生元素；链接不加role=button。保留type/name/value/form/action/method/target/t-if/disabled、表单归属、DOM顺序和原无显式type的默认行为。
- 无自动提交、防抖、通用业务回调、全局click监听、新产品JS；Enter/Space/Tab沿原语义，焦点清楚不裁切。
- 页面无异步busy，不新增；busy/disabled只明确组件演示，产品仅原真实状态，不强禁用合法按钮满足只读。
- 多语言原文/含义不变；可包文字span和静态SVG，仍由Odoo提取翻译，实核loaded中文/access name。
- 不以大面积红代危险确认，不让“确认”像已成功，不给查看/识别加完成勾。

### 3.3 SVG采用方式

Lucide线性图标，实际版本完整版权ISC及适用Feather MIT随资源保留。[W1]最多七种唯一图形，按需不充指标：search查询文字前（输入不重复）；arrow-right来源文字后；chevron-left/right翻页文字旁（边界无链接保留原边界文本，不造点击）；scan-line仅识别文字前（不表示接收入库）；package批次标题前；list来源标题前，不每单元格/状态/数量重复。

固定上游版本/commit、来源/原始SHA/许可/修改记录，核实际文件名，等义替代仅同语义并记录，不混库。不整包数千图标/runtime/icon-font/React/Vue/CDN/外部字体。

静态QWeb片段/明确白名单helper；24网格、统一上游线宽通常2、round端角、fill=none/stroke=currentColor，尺寸优先1.125em、标题约1.25em，width/height防CSS失败撑满。官方静态路径，不从患者/来源拼SVG、不t-raw未知内容。[W2]

可见中文旁图aria-hidden=true/focusable=false，不重复朗读/独立Tab；无纯图标业务按钮，失败文字原动作可用。仅受控几何，无script/on*/foreignObject/外部href/图片跟踪，运行无需互联网。不在报表/PDF/标签/患者内容顺带加图。

## 4. 精确范围与历史冻结例外

### 4.1 本次允许

只在主路径生效，复用 `inventory_lookup = request.httprequest.path == '/ydental/inventory'`，不能用can_catalog判页。

- 搜索、原来源链接、前后分页/边界呈现。
- 本页全部既有办理确认、取消返回、details summary，先清权限/状态控件族；基线13个details定义，单角色不必同时渲染13个。
- 原“仅识别”外观及指定图标，不改扫码输入说明。
- 两个现有区域标题图标，文字数据其它布局不改。
- 必要局部CSS、静态SVG/QWeb、资产注册/许可、最小翻译和定向测试文档。

P7明确覆盖P6的13办理details及scan整段字节冻结：只允许按钮/取消/summary的class、文字span、静态SVG变化，业务属性、字段、条件、动作和权限合同仍不变，其它字段/表单/控制器/服务继续冻结。必须逐项映射，不能只改Search；未显示状态用SOURCE及明确组件，不伪造真实状态。允许定向整理旧按钮专属CSS，避免两套冲突，不重构P6其它样式。

### 4.2 本次不变

- 原input/select/数量单位/证据原因/policy，不改弹层，不把P4迁入办理。
- 全局导航品牌、catalog、原错误页、文书报表结算；相同模板目录呈现原样，不被全局asset污染。
- POST action/csrf/revision/key/operation/name/value/required/min/step/验证/默认submit、can_write/can_catalog、状态表达式、13details name分组语义。
- 库存事件/权威数量/来源责任、九列批次/两集合搜索/告警算法/event_id/q/page和原责任。
- controller/model/service/ACL/schema、PDF/原件/core/数据库filestore/业务政策。

不把GET换POST、不整行隐式点击、不增confirm弹窗，不改标签含义动作。

### 4.3 资产复用

现模块一份按钮tokens/变体和静态SVG子集，报告唯一入口，不建UI平台/模块。明确元素局部类+页面opt-in，禁止全局button/a/summary/.btn/.btn-primary/:root；共享asset可注册，但无opt-in不匹配，不给包含所有表单祖先暖色字体连带改input/table。复用暖色，不逐按钮HEX。后续推广再抽最小公共资产，本批不重构P1—P5，沿Odoo QWeb/资产机制。

## 5. 无业务副作用的正常流程与测试

F1：普通仓库正常登录选店→原菜单→文字/Enter/查询图标→原列表→来源文字/图标原event锚点→返回→前后页。同动作原GET，不重复/错参。

F2：有权角色只展开details、读原字段、Tab确认焦点、取消或收起；不点live确认、不填新证据。只读身份仍无原无权控件。

F3：明确组件覆盖长字/disabled/busy/danger/实数据缺样条件，真实产品CSS/QWeb、无业务写入、无修饰CSS，组件和产品分别标。

F4：核POST form/submitter；序列化仅内存或不派submit不发网FormData，token仅内存比对不进包/日志。不在真实页拦POST后声称成功；正向业务依冻结源码和已有实证复用，不重入库/退货证明换色安全。

## 6. 连续实施工作包

|包|工作|完成条件|
|---|---|---|
|W0|承接基线、控件/语义/样式清单、静态前态、独立准入、固定SVG|允许控件与冻结字段清楚，不泛化规划等GPT|
|W1|DL15—20、tokens/变体、全部目标按钮/链接/summary|原能力合同保持，同一规范|
|W2|最小SVG/许可/映射、相对尺寸/对齐/状态|无纯图标/重复焦点/外部runtime|
|W3|固定候选、真双引擎/响应/读取/合同/旁路/保护及修复|按影响补验，不重旧全链|
|W4|未实现者独立核、私有包、最终报告、同步并停止|适用断言完成，技术/同步/用户分开|

主控统一多agent、唯一写者、环境，工具与验收者就绪再开窗口。不逐包GPT签。旧额度UNKNOWN非前置，不索旧/status/时区；当前真实限额权限仍遵守。未实现者形成当前真实准入，不改旧时间/STOP/guard，不借账号/模型/入口绕限制。

## 7. P7-T01—12验收

|项|必需断言与准确层级|
|---|---|
|T01 覆盖边界|清单逐映search/POST确认/取消/summary/scan/来源/page；仅主路径；catalog/error/P1—5不变，无新业务JS/backend|
|T02 风格状态|同类tokens/尺寸；default/hover/active/focus实查，disabled/busy/danger按真实或组件；字≥4.5、必要边/焦点≥3，actual computed+图，装饰线不强迫|
|T03 来源安全|固定上游/commit/原SHA/完整ISC和适用MIT；最小子集、无runtime/CDN/script/外链/on*/字体交付|
|T04 语义操作|button/a/summary、中文/access name/焦点序保持；SVG无Tab/名称、不挡点击；查询图/字/Enter原GET，导航仍链接|
|T05 响应|1366×768、1440×900、768×1024、390×844、320×800，长字可读可点、不挤字、新根溢出0、九列表读法不改，自然撑高不藏字段|
|T06 引擎放大|真实Chromium+WebKit或Firefox关键路；各native200%与独立root200%分层；无JS视觉/查询/导航/details可用，AX不冒屏读/实机|
|T07 读取|有限代表查询/定位/真实前后页，q/event_id/anchor/page/行集顺序/三数量/flags不变；复用P6算法/26响应等未影响项，缺样标组件|
|T08 办理|13族可见条件/全部字段/type/name/value/action/method/token来源/required/disabled/operation不变；取消/summary真键盘开闭无业务POST，序列化只内存，不冒真实办理|
|T09 角色旁路|普通读写已有能力及原无源拒绝，未改权限明确复用；catalog/error/P1/P4/P5有限代表无scope/CSS继承污染，旧hidden computed未知不归一化|
|T10 故障|缺SVG/无CSS明确组件中文和原元素可用；native focus/forced-colors/reduced-motion按支持核，不因缺图disabled，不冒真实设备|
|T11 加载保全|必要加载即时pre/真实exit/post分类，纯资产核实际新bundle不重复-u；最终未实现者新physical完整业务和现场全部83文件、旧audit保持/新访问技术分类；新原件/PDF/打印/scan/经济库存0|
|T12 独立交付|未实现产品/相应工具者核固定源/真实请求图/原结果/保护包；失败保留、逐候选复用透明；技术/同步/用户分开、owned收尾、最终同步读回|

接受冻结业务实现+提交合同不变+已有业务实证复用+本次只读/组件组合。不证明重新执行成功；缺必需动态/独立证据交PARTIAL，不降低门槛、不转下一页。

## 8. 数据保护与不启用

原目标filestore，不新建/复制/改名库，不改core/odoo-12/共享OS/防火墙/集群策略。旧文件及提交金额库存、身份作者价源、权限、未完责任保护。P5原1269、P6原217和全部早期audit保持，本批新读取另列，不删除旧行，不要求物理全库零diff；83是现场数量，技术asset非业务PDF。应收1073+前批230=1303、lot253收10用2余8为承接事实，不硬编码未来查询、不重放补图。

不提交库存action/scan，不生成PDF/原件、打印、签署/发布、收退款/日结/治疗。“仅识别”美化不启S11一次扫码接收入库，不改扫码合同。历史失败/PARTIAL/UNKNOWN保留，当前异常按实际影响处理，不无限历史排障。

## 9. 交付与结束

完整计划落本路径，现规范追加DL15—20及链接，保留旧阶段启用历史，不改为以前已实现。同一CURRENT维护，三份报告：

- `docs/reports/s13-dl-p7/summary.md`
- `docs/reports/s13-dl-p7/acceptance-matrix.md`
- `docs/reports/s13-dl-p7/evidence-index.md`

报告含实际控件/变体/图标、来源许可、前后、候选环境层级、全部适用验收和复用、独立保护/验收、风险、5—8步角色复现。私有包需前后/展开/hover/focus/窄屏/两种放大/明确组件图、README/索引/manifest；数量非门槛，缺图/disabled组件不冒产品失效。无凭据/session/profile/raw请求/连接配置/完整DB投影/备份/独立字体。P6旧包不覆盖，只用户授权会话看，不上传Public。

最终正常commit/push及ref/正文/必要Issue状态读回；#37仅新增一份P7结果并OPEN，P1—P6旧评论/P5 PARTIAL续办历史不改，#36 CLOSED。main仅必要文档路由，不合产品/部署，失败SYNC_PENDING。

```text
[CODEX-FINAL] YD-S13-DL-P7 / 1.0
技术：TECHNICALLY_COMPLETE / PARTIAL / BLOCKED
同步：SYNCED / SYNC_PENDING
用户亲手效果：待确认（或只列真实确认范围）
完成范围：库存页按钮/图标，非全站
后续页面/完整S13/合并部署生产：未启用
```

适用验收、保护及未实现者独立验收后交付，正常结束owned服务浏览器。完成后停止，不推广/重美化数据区域，不启全链/50活动会话/备份恢复/实机/正式临床财务政策/组合扫码/真实患者资金外部通道/产品合并部署生产。

## 10. 依据

项目事实与本次设计约定分开：

- R1：[main/GPT_HANDOFF](https://github.com/Yredxin/YDental/blob/main/GPT_HANDOFF.md)、[AGENTS](https://github.com/Yredxin/YDental/blob/main/AGENTS.md)、[CURRENT](https://github.com/Yredxin/YDental/blob/main/CURRENT_TASK.md)及本会话用户新要求。
- R2：[P6固定summary](https://github.com/Yredxin/YDental/blob/e31ea56d1ff903461eda86c08088c5f7e32aef7e/docs/reports/s13-dl-p6/summary.md)、[矩阵](https://github.com/Yredxin/YDental/blob/e31ea56d1ff903461eda86c08088c5f7e32aef7e/docs/reports/s13-dl-p6/acceptance-matrix.md)、[#37回执6397824653](https://github.com/Yredxin/YDental/issues/37#issuecomment-6397824653)、同固定候选的inventory XML/SCSS。
- W1：[Lucide许可](https://lucide.dev/license)；实际固定版本完整ISC和适用Feather MIT随采用资源保留。
- W2：[W3C内联SVG尺寸/对齐/装饰语义](https://design-system.w3.org/styles/svg-icons.html)，不采用其另一图标库。
- W3：[WCAG文字对比](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)。
- W4：[WCAG必要非文字/焦点](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)。

外部材料只支持许可与可访问规则；圆角/配色/数量/页面/包是本次项目设计约定，不由外部或P6验收自动给出结论。
