# DL-P8 文书主页面动作控件与SVG实施结果

[CODEX-FINAL] YD-S13-DL-P8 / 1.0

技术：TECHNICALLY_COMPLETE（限定P8软件）

同步：SYNCED（首业务/main两ref、30全文、唯一P8评论/旧9及Issue状态已真实独立读回；末元数据增量另实际核）

用户亲手效果：待确认

完成范围：文书主页面动作控件／轻量SVG，非全站

完整S13与后续页面、合并部署生产：未启用

## 固定候选和连续实施

- 活动分支`codex/s13-dl-p8-documents-actions-icons-r1`从现场clean P7报告`9f5ce4626895cb8f3da0562d9170e79220728378`正常承接，P7产品`52d5422fa0083bf88cec4442ffcd45d35d27e9f7`、唯一回执6399387525及P1—P7/旧P5 PARTIAL/旧包/失败/UNKNOWN保持。未reset/clean/强推或从文档main重建。
- 最终产品/主要最终工具/实际运行代码 **bd8411d4ef50014caddff7128f0c9cf4fe42f122**。首产品/唯一必要print加载a262238e0ba24f6020093cbc2c57eb8d3924b602；资产注册修复e81f65d7d4a1cfb104f5e42b626bd14bd4ba7264；最终busy补呈现bd841。before准备01590374c6306f66e03b2d2449971b363b2dd44c的产品仍P7。各真正执行的工具源/依赖/argv/退出单独归档，不谎称所有client都用同一最终generic文件。
- 最终owned run`20261026T002818Z-c952a86a2576`，唯一既有合成目标/OID2171423/cluster7694897083368259627及原filestore，core`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`不变。新scope为真实UTC 2026-10-25起8h，续绑定不延长旧期限，不改旧STOP/guard。没有新库/克隆/改名。
- root唯一产品/状态/报告写者与调度；testing_p8实际测试与工具，runtime_p8资源/加载/保护/QWeb适配，acceptance_p8未实现产品或相应测试工具的独立验收。同OS不冒隔离。工作包W0—W4连续实施，不等待逐包GPT签字，不向Issue发中间进度。
- 首技术报告与最终元数据报告固定锚点、main两路由和唯一P8回执按实际同步补记于本文末及同评论；不循环自嵌未来自身hash。

## 控件覆盖与原生合同

25个静态呈现定义=9button/7summary/7a/2h2。循环原件行产生多份实际控件，不混算。P1两动态combobox是字段，维持原trigger/listbox/键盘/确认取消/原生fallback/JS；已有`ydental_document_consent_page`继承的临床集合、设备故障、同意上传/核验入口及表格亦冻结，不套本轮scope。

|族|定义|变体/图标|真实执行边界|
|---|---:|---|---|
|搜索文书|1button|secondary/search前置|原GET q、文字/图标/Enter|
|预览所选来源|1button|primary/无新图|原POST preview读取已有HTML|
|生成并留存原件|1button|primary/无图|只焦点/内存合同，不generate|
|查看/下载旧原件|2button|quiet后置arrow-right / secondary无图|原pdf_view/download及_blank，真实旧bytes|
|请求打印原件|1button|secondary/无图|只焦点，不print_request|
|创建未审核模板/记录审核|2button|各表单primary/无图|只焦点，不template_create/review/publish|
|导出授权原件|1button|secondary/无图|只焦点，不export|
|两源追溯/操作追溯/原件追溯/打印/模板/导出|7summary|disclosure/不加图|原生marker/name/条件/Enter/Space|
|五工作区链接|5a|quiet/无图|原href、两分组、顺序|
|前/后页|2a|secondary/chevron-left/right|原q/page/首末span不可点|
|查询/原件两区域标题|2h2|原层级/list|原标题及aria-labelledby|

元素`data-dl-actions="documents-actions"`配`o_ydental_print_document_*`类，由同一主模板在GET和preview POST回页生效，不按pathname误门控。原button/a/summary语义及无显式type的默认submit均保。将精确允许的class/span/SVG/translation边界还原后整个原XML canonical exact，全部form、字段、t-if/foreach、action/method/target/type/name/value/csrf/revision/key/operation/required/disabled、权限与顺序保持。无新产品JS、自动提交、confirm或全局click处理；后端/model/ACL/schema/PDF模板均未改。

## 同一规范、SVG与许可

唯一共享规范为`ydental_access/static/src/scss/_actions.scss`中的`o-ydental-actions`；单独编译输出空。通过access已有frontend资产清单先声明，库存和文书随后调用，不使用本地import、不改编译安全检查。库存原选择器/opt-in/DOM/XMLID不动，机械提取编译输出7519B与P7同；新scope不向表单祖先放字体/颜色，不全局覆盖button/a/summary/.btn/:root。print显式声明access/inventory实际依赖。

统一1rem/600、.625rem圆角、min2.75rem、padding .625em 1em/gap .5em；primary #94513A白字/hover#7E432F，secondary浅杏#F6E6DC/深陶土字/边#8C7564，quiet下划线，focus#6C513F。控件自然撑高，保留原grid/flex/局部表格读法，无厚影/大渐变/装饰动画，仅140ms色彩过渡。真实busy保留P1 addLoadingEffect、aria-busy/status、widgets及pageshow/reset；仅两个querybutton的原spinner占已有padding槽，真实两engine正常→busy宽高严格同，label不被挤或遮盖。

P8只调用P7五个既有静态QWeb片段`p7_icon_search/arrow_right/chevron_left/chevron_right/list`；不复制/搬走/改名原7种资源。Lucide固定0.468.0 / f12b0de177fbc2a6795e99be065887e72b237123，原SVG SHA/完整ISC及Feather MIT保留于`ydental_inventory/static/lib/lucide/SOURCE.json`及LICENSE/ LICENSE-Feather，分别SHA1e7290b35280a048667bbf0ebabac1c7fd52a75300e8b2946ac165715997f2bc、308028e93fcf84972523cdf6e616f73168546b4953895f516d01287f16fe7bee。MIT固定Feather v4.29.2/1b002399e8758fb2bccea4d07312dc9e0f43dcb8。

24网格/线宽2/round/currentColor/no-fill、控件1.125em/标题1.25em，装饰aria-hidden=true/focusable=false，无独立Tab/重复名称。原术语123occ/116unique提取顺序同；25目标术语24unique实际native export/loaded中文/内存render均同原PO。无新术语markup回退、t-raw/脚本/on*/外href/foreignObject/runtime/CDN/字体。

## 真实验证与精确复用

[12项矩阵](acceptance-matrix.md)与[完整脱敏索引](evidence-index.md)列实际候选/层级/原件SHA。真实Chromium156.0.8078.4与WebKit27.2 WPE：1366×768、1440×900、768×1024、390×844、320×800；各原生200%（zoom2/root16/DPR2）及独立根字号200%（native1/root32/DPR1）、各真正javaScriptEnabled=false桌面/320、自然Tab/summary Enter+Space均按层级合证。原native200 Chrome白图不作视觉PASS，3个真正CDP viewport新图补齐；WK native/root原图清晰。长中文首末Range/实际clipper与可达、无SVG/无CSS/CSS缺失但SVG仍在、原生焦点/属性、明确组件busy分别采齐。Chrome真实forced-colors/reduced-motion，WK只声称支持的reduced-motion。

27个实际client=21×0/5×2/1×130，27个native主进程全退出0；165唯一原PNG路径/148不同SHA全部原字节、尺寸与解码核。客户端读POST记录preview9/pdf_view9/download6（含4真实拒绝与Chrome额外正常旧fileHTTP），禁止业务POST/预拦截guard均0；26次logout200，旧WK130的一次TargetClosed保留。raw请求层不替代下述独立数据库审计/提交保护。

普通doctor9/store1有医疗来源而无exportwrite，真实47授权原件/30+17两页及14追溯值，图/字/Enter各单GET、原选择器确认取消、source required、显式一次preview、GET/POST回页同scope成立。5写按钮只自然Tab聚焦不激活；13种库存业务未重演、文书生成或模板管理未执行。原业务正向实证仅按未变源码复用P1 8dea2647、P3 b72bcd6d/首产品2873的对应固定权限/原件断言，不称本轮重新办理成功。UX/S12仅承接适用历史证据与旧原件来源，不声明S12全部后台与最终same或整套全链重签。

旧309→attachment15810→独立真实原文件与实际下载副本均57306B/SHA b2d813eb1e4477aeb40810550f7fbd184a524aabc8be1cd1599441d70fe4a4e3。Chrome view601B是内建HTML壳，另明确正常same-session旧文件HTTP取真bytes；download同次native文件。WebKit补尾两操作均同次native Download真bytes，旧读体等待130不改PASS。读取旧PDF/本机校验副本不是新增业务原件。

真实normal/hover/active/focus的正文min5.2016318344、必要边min3.2401343224、focus min7.0613212442，仅局部实际样本，不冒整站认证。两engine default矩阵来自e81有效分项，busy-only bd841无影响源码证明后复用；最终两engine trusted submit严格实测busy尺寸不变。自然Tab与矩阵keyboard-modality+programmatic focus分开，不以AX冒屏读。

前后initial/page1/page2业务投影strict同（只明确秘密标记）；preview非iframe字段strict同。Chrome q input及label width各-34px，对应目标Search自然宽+34px，原grid minmax(0,1fr) auto未改，其他所采字段字体/边框/颜色/padding/选择器/表格样式same，不称所有computed字节同。iframe完整raw仅原生提取UTC一处变化，attrs及其余prefix/suffix全字节同；该时戳为采后精确分类，不伪称before预声明，也不称全文/宽泛归一化same。WK无自身before computed；跨engine3个cell.width小数精度差原值保留，不把它们归一化。Chrome320根345与真实同engine before345相同；WK当前333、same-engine before与整document具体元凶UNKNOWN，不能称已找到旧元凶或根差值为0。两engine五view目标均fit原parent/无目标client-scroll溢出，非目标compiled45/12/44规则原值同、无祖先/global规则及P7编译exact，独立据此判本P8动作区无新增spill成立，不冒整页零溢出或全页已移动适配。

有限旁路：库存全部所采computed（含全部rect）和fields strict exact，原P1popup及print exact；doc仅目标scope_count从0到165，继承forms/computed同。reports仅4处today date_from/to（含hidden）随午夜25→26，前态已声明日期回显例外且原值保留。settlement27个fee_ids中88由第7移首、其余26相对顺序同，actual_utc为各实际请求时点；测试首观察UNKNOWN原样保，后独立用冻结service today/history分组及pre event88日期2026-10-26精确解释午夜自然重组，不排序伪same、不重旧结算。其余采样attrs/styles/值同，其他页新scope0。

## 加载、全阶段保护与独立验收

唯一必要print-u实际exit0/ERROR0/noNative，真实freeze/pre→actualexit→post并独立c98d6a55…全核。后续纯资产freshregistry通过实际Manifest读取机制及真实bundle核验，不重复-u。25ir_access及group69只write_date；8技术类精确分类，39旧view归print8/exam4/settlement7/lab14/clock1/report5，唯主1618 arch_db变化，其余38 active arch同；无新view/XMLID。依赖表旧2行保持，仅增加inventory/access两条显式声明。原生更新不冒全库物理零diff。

最终未实现者新physical440896，RO/RR/rollbackidle/closed，完整145业务表/13技术表/九区逐值同主控最终f66d61f1c5bdd31930091f862abeeab535be87d22293f94da0987be7ec619382。同一新事务补核4依赖、83附件引用逐一真文件字节/尺寸/SHA，对应80唯一路径/80不同SHA，65内部+2外部原件及3处既有共享引用全部保全，无去重/删改。独立完整保护 **0357de136027bcec599d28b159844c7f5036bbcb4f4db54f487cdb943f72cdc8**；独立新physical snapshot **97de1cd48254f62f0c502f1030029021b816fe8afa25650f3299c07e3aac6c6b**。

旧17631审计（P7前17431+P7新增200）逐行全保；新181=177accepted+4旧PDF读取denied，最终17812。accepted为login/scope/switch各27、document.view9/pdf_view7/download4、inventory.view6、report.view2、settlement.source_view54/invoice_view14；4 denied沿原handler记document.action/categoryexport，实际是pdf_view/download读拒绝，绝非执行bulk export。其余原资金/库存/身份作者价源/未完责任/原件/配置schema无增改删；应收1303、lot253收10/用2/余8按现有保护事实保，不硬编码所有未来查询。新增业务原件/PDF生成/打印请求/签署/模板创建审核发布/经济库存/治疗/扫码均0，无临时授权。

最后owned于 **2026-10-26T00:53:00.708240Z** 正常child0/signull/groupstopped；独立OS **411a43420df798a2be8a7e9de1ca35ff1cb9ae17c5bc507e7ff25fb1973e0174** 核4owned退出、27native全0、已知PID/profile/owner和18411/12空，另一freshRO/RR442472核其它target连接[]，未动共享主服务、不为报告复开。

## 失败、私有包和限制

产品a262离线libsass缺Odoo sanitizer层核验，本地import被native拒绝，HTTP200返回旧CSS；e81正常asset注册修复，不改检查。e81新inline-flex使原P1 static spinner busy宽+32px，bd841仅局部CSS槽修复，原JS/字段不改，旧测量保留。早期工具main th8误期望4（继承核验表）、preview selector误含2combobox、角色路由403预期200、DOM undefined与持久JSON表示差、WK读体等待130/最后TargetClosed与logout失败、native200白图、普通辅助检查错误等均按实际原件/退出保留，补验只覆盖受影响未成断言。首独立view归属/跨engine精度审查假设错误是离线审工具失败，未重-u或改业务。

私有0400包 `.local/dl-p8/viewing/S13-DL-P8-view-only-20261026-r1.zip`：**3,709,241B / SHA256 8afb9922a4a0e0cd339b81b5a126580fa12a4bfc7d88d0f164780bf76aca8ba3**；40成员/37原PNG/35不同SHA/39非self manifest，全成员/sourcebytes/SHA/解码/隐私独核 **5d985066526d13abbba94d9dd69fe3812af45f2679bc2856db0d8b56f1d1feb8**。无裁切/重采样/修图，不冒像素对齐；原before/after/引擎/实际uid/候选/视口/rootFont/DPR/scrollY/组件层级逐图记录。

两张WK main旧130图仅选择已独立37101c…通过的UI分项，原wholeFAILED/client130、依据和actual candidate保留，不当整轮成功；原生200真正展开追溯和JSoff展开有清晰代表，不用名为expanded却未滚到正文的图片。后续图片取消实际UI文本selection有metadata，PNG本身未编辑。包无凭据/session/profile/raw请求/配置/完整DB投影/程序/字体/原件PDF，只本机和用户授权会话查看，不上传Public。P6r2和P7旧包SHA实际保持。截图数量不是完成门槛。

未实现者T01—11及T12_LOCAL独立总索引 **a2bde74279fc36bba99c686e35ea19d584ec354d9089f55d6fc2276efda3a20d** 已实际PASS，REMOTE_PENDING是当时事实不改；最终本地正文/状态/README及索引已实际未实现者总签 **80ae088d0a45eb6338f6f3ab4b5d12265d8b4cd5c99f99c36be8ac29f6d26692**（LOCAL_TECH_ACCEPTANCE_PASS_REMOTE_PENDING）；远端正常同步后另按实际记录，不改原时点。

真实OS IME、屏幕阅读器/实机/触摸设备/正式临床财务政策、完整S13/负载恢复/组合扫码/真实患者资金与外部通道均未启用。用户亲手效果仍待确认。原生时间/小屏未改区限制、实际客户端失败不被后续成功反签。

## 普通医生7步复现

1. 在正常有效运行窗口，普通医生正常登录、选原授权门店，从原菜单进入文书与原件。
2. 用患者姓名或业务号搜索；用查询图标、文字或Enter执行原GET。
3. 在原来源/模板选择器确认或取消候选，再显式预览已有HTML；不生成原件。
4. 阅读原预览正文与来源/模板追溯，用Tab聚焦生成按钮即可，不激活。
5. 展开旧原件追溯，明确查看/下载同一旧文件，核原SHA；不请求打印。
6. 使用原前后页与五工作区链接；模板/导出入口仅开闭和焦点，不提交。
7. 检查窄屏与两类200%压力下的中文、图文、焦点；原长表按原局部横读。owned服务已按最终记录收尾，复现需正常新准入，不恢复旧时间/STOP。

## 同步与停止

首技术报告 **0e4e1d4037e4ff77ced8669f2be5a2e66a4debb1** 与main仅两路由 **68727492bbb23429cb42443747edcd56df2b719f** 已正常push。正常GitHub connector实际读30完整UTF8正文，bytes与Gitblob逐一exact；唯一新P8回执 [6406133603](https://github.com/Yredxin/YDental/issues/37#issuecomment-6406133603) 全4511chars与预期全文同，旧9逐id/body全保，#37 OPEN/#36 CLOSED及原title/body同。未实现者首远端同步独立总签 **547b0cee9db2aa745039f13643104433969c75991b87119275eedc39df00dc9e** 已实际PASS，结合80ae088d…本地总签，T01—12本批适用项成立，**TECHNICALLY_COMPLETE / SYNCED**，用户亲手效果待确认。原本地REMOTE_PENDING时点保留。

最后四文档只更新这些已发生的同步与停止事实；其最终ref/完整正文和同一评论增量另外实际读回并保私有收据，不预签未知SHA，也不把该末回执hash循环嵌入自身。产品/运行bd841、完整保护与私有包不变，没有新HTTP/DB/浏览器/业务动作。

P8交付后停止。#37仅本一份P8最终记录，旧9评论及P5历史不改；#36保持CLOSED，main只必要路由，不合产品、不部署，不自动开始后续页面或完整S13。
