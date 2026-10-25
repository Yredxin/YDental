# DL-P2：文书页页头、页内导航与用途/范围提示

`[CODEX-FINAL] YD-S13-DL-P2 / 1.0`

- 技术：TECHNICALLY_COMPLETE（仅P2限定软件，已获未实现者本地技术总签）。
- 同步：SYNCED；首完整业务报告/main两路由ref、11份实际正文及唯一新P2最终评论全文与状态已实际读回；本提交只补同步元事实。
- 用户亲手效果：待确认；P2启用不等于P1已获用户亲手验收。
- P1保持TECHNICALLY_COMPLETE，其原交付SYNCED，不重开；P2交付后停止，P3—P6 NOT_AUTHORIZED。完整S13未完成，#37保持OPEN、#36保持CLOSED，不合产品main、不部署。

## 候选与真实修改

用户完整附件逐字保存为[本阶段计划](../../execution/S13_DL_P2_IMPLEMENTATION_PLAN.md)，沿用[设计语言](../../design/YDENTAL_DESIGN_LANGUAGE_V1.md)，不改写旧P1计划/结论。2026-10-24开工，正常跨UTC午夜于2026-10-25收尾，不改旧时间。分支`codex/s13-dl-p2-documents-header-r1`从实际合法P1报告HEAD `d421842c9b26de9988be3f7e4c46cd5626cb67ca`正常承接；P1产品`8dea2647760f6d6738abfc9db132cfa9d7feaee3`、旧#37回执6384111913保持。原工作树仅CURRENT_TASK两条GPT限定复核补记，先保存diff并原样纳入P2准备文档提交。此补记开工时未同步，与P1原交付SYNCED分开记；不reset/clean/强推或从文档main重建产品。

|对象|固定事实|
|---|---|
|准备/公共阶段工具|`9b5325fe0c23bac9af96d6496cb23a8ca17f57d8`；addon仍是P1，作为本批真实before|
|最终产品/执行|`a0b33c14c121f2a489fdcf7abc529999fd15c1dd`；此前93ad的旧紫导航缺陷已前向修正|
|只文档checkpoint|`5d3a25686472ef32239242bc19ff44b9bf1aa044`；仅CURRENT，非新产品|
|core|`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，未修改|
|私有工具|tester v1—v7源码按各自实际SHA归档；每次真实父子退出和native主进程另列，不能由工具作者签独立通过|

addon产品恰4文件：文书页XML、新`documents_header.scss`、manifest的一条资产注册、zh_CN.po新增7项。另有本阶段限定运行适配/纯边界测试、完整计划、CURRENT及3份报告；它们不是业务产品扩展。P1选择器JS/SCSS、表单、帮助/错误/ARIA和preview以下完整XML后缀逐字保持。model/controller/ACL/schema/PDF/纸型/原件机制及其他岗位产品无改动；无新JS、后端路由、公开API、类型或迁移。

页头只有本页主标题与用途；五个原导航目的不变，按临床/治疗药房/检查与权限/结算分两组，语义列表、自然换行及可见键盘焦点。三类指定静态说明默认可见，不新增details、主按钮、假统计、假门店名或业务动作。“预览所选来源”仍是P1任务区主动作。全站网站页头/品牌/Your logo及列表等旧区保持，自然纵向位移不称越界改造。

## 原文→新文→位置与含义

|原文/旧位置|新文|新位置与保持的含义|
|---|---|---|
|Documents and saved originals；原本页h1|Documents and originals → 文书与原件|仅可见h1，菜单/action/template名不改|
|原无简短用途|Find patient documents, select a source to preview, or read saved originals. → 查找患者文书，选择来源预览，或查阅已保存原件。|页头标题下，只描述现有搜索/明确预览/原件查阅|
|Patient labels identify the source patient record. Saved PDFs retain the identity and state at generation.；原搜索区说明|英文及既有中文逐字保留：患者标签用于识别来源患者主档；已保存PDF保留生成时的身份和状态。|页头“来源患者与历史身份”；实时来源标签与历史原件身份/状态分开|
|Synthetic software demonstration documents carry an explicit test label. A generated or printed consent is awaiting signature. A print request has no verified physical paper output.；原P1警告|英文及既有中文逐字保留：软件合成演示文书均有明确测试标识。已生成或打印的同意材料仍待签署；打印请求不代表已核实实际出纸。|页头“合成、签署与出纸”，默认可见暖色警示；不暗示正式批准/已签/已出纸|
|Single authorized copies require current source access. Bulk export additionally requires report export permission. Saved originals always return the stored file; current names, prices and templates cannot rewrite it.；原P1说明|英文及既有中文逐字保留：单份查阅须具备当前源读取权；批量导出另需报表导出权。已保存原件始终返回存储文件，当前姓名、价格与模板不会重写旧文件。|页头“读取权限与原件”；不缩成仅当前门店、不扩大为所有患者；源读取与额外导出权分开，旧价格/模板/文件不重写|

另新增2个ARIA名称：Related work areas → 相关岗位入口、Document scope and limits → 文书用途与范围限制；3个组标题同上。连同标题/用途共7新翻译项，旧译文不改。5个链接的旧英文/中文及href均保持：`/ydental/clinical`、`/ydental/treatment`、`/ydental/exam`、`/ydental/access`、`/ydental/settlement`。完整机器映射在私有包copy-map.json，不含业务数据。

## 实证、P1衔接与视觉

[逐项矩阵](acceptance-matrix.md)与[脱敏证据索引](evidence-index.md)区分SOURCE/PURE、真实HTTP/BROWSER、独立已提交RO和未验层级。

|层级|实际结果与界限|
|---|---|
|SOURCE/PURE|原生Odoo xml_translate/PoFileReader、polib、libsass及作用域/字节核通过；7个运行边界PURE通过，不冒7个业务用例|
|Chromium|真实156.0.8078.4，正常doctor9登录/选店/菜单/search、两select选择确认/Esc、导航Tab焦点、required/ARIA/唯一真实提交字段/无自动请求、390/320浮层、显式preview200真实可见正文。core/fallback/none客户端全部0，pageerrors0|
|无JS/无源|JSoff在同一新context正常HTTP认证后使用原生查询/select/显式preview；非复制会话，层级明确。none角色真实shell200/disabled/空状态说明，不冒后端403|
|WebKit|真实27.2，正常doctor9菜单/search/取消与Tab确认、五视口页头、390/320浮层、显式preview200及原生zoom2/根字号32分列；客户端及可观察主进程0/signull。只补正确zoom视口图，不重跑全链|
|五视口|1366×768、1440×900、768×1024、390×844、320×800。标题/导航/关键说明自然换行，无新改区溢出；320仍client320/scroll345，不签整页移动端完成|
|真实缩放|两引擎原生200%与单独根字号200%分别实际验证。WebKit原生CSS1366→683、root16/DPR1→2/visualScale1；正确1366×768视口图scroll0/280重叠覆盖214/214实际字符Range；根字号32是单列压力条件|
|实际颜色/对比度|surface #fffbf6、正文#382f28、说明#716359、link #94513a/hover #7e432f、focus #6c513f；14组实际rgba文字独立复算最低5.613，5焦点最低7.061，符合本区4.5/3门槛，不冒全站认证|
|前后/旁路|真实11对同条件页面；所有P1表单/帮助、列表、generate/管理/export和网站共用页头字段/computed逐项同，只排除绝对纵向位置及经源码验证的随机hidden32hex key值。3旁路结算/仓库/原生加工PNG前后同SHA|
|iframe限制|前后全文SHA不同，预览原生含每次生成/提取时间；before没存全文，未实测证明差异仅限时间，不能称归一化全文同。严格同源/版本/模板及expected_digest，renderer源码不变；独立亲看前后实际可见600px正文/作者/状态/范围一致，不称整篇逐像素验完|
|权限|后端源读取/门店revision/拒绝契约和相关源码逐字保持，复用P1固定17类HTTP/正常撤复授权证据。P2定向有源/无源真实显示及正常显式预览，不机械重跑撤权/经济链，不用测试guard冒产品拒绝|

首版93ad已限定`ydental_print -u`实际0/ERROR0/无Native，带即时完整pre/post及独立新物理RO。最终a0b只SCSS色值修正，manifest/XML/PO逐字同，不重复-u；以正常新资产的实际computed与两引擎操作补验。没有重跑S11/S12/S13-UX/P1整套历史业务。

## 数据保护与服务

唯一目标`ydental_s11_synth_20261023_01 / OID2171423 / cluster7694897083368259627`及原filestore；五项集群高权false，无新增/复制/改名库。P2初始145业务/13技术/83实际文件与P1最终逐值同，无未知增量。最终root post的真实文档checkpoint与产品分列，跨候选只文档，不冒同一升级freeze。

独立最终新物理RO/RR backend65787、rollback idle/closed，145业务/13技术及全部83实际文件与root最终9保护区段逐值同；独立保护SHA `13919577641929e042b7f6c94ac96eb1b7ce0cf463a9d695ea2a0e5b4f7adcf0`。65内部/2外部原件及全部SHA、原金额/库存/作者价源/身份/未完责任、schema/index/配置保持，P2新增原件/PDF/打印请求/经济库存业务0。固定旧来源1073＋前批230＝1303，P1/P2贡献均0，不当作后续全部查询永远1303；lot253仍10/2/8及历史未完责任不重演、不假完成。

非物理零diff：64条正常访问审计新增（16login、16scope、16switch、8document.view、2结算、2库存、4source.view），旧审计无改删；25条ir.access和group69仅write_date；原生8表769行技术日期及本页view1618 arch_db/arch_prev另分类，无PDF/纸型语义变化。认证/session/secret列按既有保护投影排除，不宣称全库每字段物理不变。

最后owned run`20261025T000521Z-bb3b2337d358`于2026-10-25T00:07:21UTC正常child0/signull/group stopped，无active，目标其他连接=[]；此前所有本批owned run及浏览器均正常关闭，未触共享主服务。原P2 scope到2026-10-25T09:42:38UTC，不表示在线。正常复开须核目标/filestore/权限/owned冲突、固定候选/fresh准入/有效资源记录，不改旧scope/STOP、不复制会话。127.0.0.1仅本机，未声称用户接手窗口。

## 失败、普通修复和未验限制

- 93ad真实导航旧紫：页面既有inline重要声明压过局部色，a0b仅header链接default/hover局部同权修正，原93ad图/失败保留，不改全局主题/P1。
- 首after-v1在320选择helper退出2，未发该次preview POST。新页头使自动scroll触发P1原有取消；同入口最小事件trace确认，工具仅先显式滚动+双rAF稳定，原断言保留，不改P1 JS。
- 随机hidden key是在实际执行比较前由SOURCE主动发现并分类，未实际产生key比较FAIL；只分类经源码核实的唯一hidden32hex值。首实际comparison-v1 FAIL仅2份iframe全文SHA，全文不可比与独立可见正文检查明确分列，原FAIL不反签。
- WebKit首登录等待超时2和GET-only诊断2：minimal JS404导致原生表单隐藏，未发认证POST；同时同URL普通HTTP200/asset记录及文件存在，首因UNKNOWN。正常同候选owned stop/start后，同原厂入口GET脚本200/表单原生ready，再真实完整流程通过。未修改driver/context/prefs/automation、安全、认证或入口，原厂warning/旧失败保留，不以恢复成功解释为永久稳定。
- WebKit原生zoom的首header locator图clip错误，独立亲看不通过；正确普通page viewport两图补齐并从PASS包主图排除旧错图。DOMfit或工具0不替代视觉，原件仍在私有证据。
- 静态checker误判line-height、独立reviewer误用audit表名、首Chrome版本命令缺私有loader、root包guard误按共同basename拦有效Chrome图均为普通工具错误，原非零留存并定向修复，无业务重放。
- Firefox中文tofu、历史Native139根因UNKNOWN继续保留；WebKit不冒Safari/iOS。屏幕阅读器、真实OS IME/设备/用户亲手、正式政策和生产均未验/未启，不以本次成功倒签历史。

## 私有效果包、角色与复现

私有0400包[下载](../../../.local/dl-p2/viewing/S13-DL-P2-view-only-20261025.zip)：9,156,502字节/SHA `a2aeab3c365d1ba60f92157587371d05cac4bc3e529511d3771de365df5217f8`，60成员=55真实PNG+README/copy-map/screenshots.csv/preservation/manifest，0PDF。全部成员原始字节重读，manifest不自引用；无凭据、Cookie/session/profile、连接配置、原始请求日志、备份、独立字体/程序或83原文件字节，未上传Public。图片数量不是完成门槛；旧93ad图标明已修，错clip图不作最终视觉。包内SHA证明材料一致，不单独证明业务正确。

真实团队：/root主控/环境/集成/报告；/root/documents唯一4产品文件写者；/root/tester测试工具与浏览器；/root/acceptance未实现产品或测试工具，独立源码、实际图/色值、原始退出、新物理RO与最终包核验。同OS共享，不冒权限隔离或实现者自签。独立总签与同步另见索引；本地总签不替代后来实际远端读回。

普通医生7步：

1. 正常复开后用获准doctor别名登录，选择门店A；凭据只取正常私有provider。
2. 正常菜单“文书与已保存原件”进入，看到本页“文书与原件”及简短用途。
3. 阅读三组默认可见说明，Tab检查五个原岗位入口焦点/分组，按需返回本页。
4. 搜索既有合成业务号P00001313，不手填内部数据库ID或扩大授权范围。
5. 滚动到来源，先Esc取消，再方向键/Enter确认；模板选既有适用项或原合成未审核空值。
6. 明确点击“预览所选来源”，查看实际正文/作者/状态/限制；不点生成/打印。
7. 返回/重新搜索，按同视口before/after图比较；窄屏自然滚动，旧列表溢出单列。

## 同步与停止

本地技术总签实际完成，SHA `4e4b6b2cdf70dccd35c3dd278920a69657902278052bf14926ee9bf2a6b0db9a`；独立包核验SHA `0d609dbbdba653c01247669706866b8b2235b17cc481d7e343136a0537f334ab`。技术总签原先不预签未来同步；现已正常push首完整报告HEAD `ba794d4d0b4b296ebd38e992fced73ce2e912f30`及main仅两文档 `af0541bc0be9771cf29ab711ad576072c9404d80`，11份实际正文逐bytes/Gitblob同。仅新增[#37 P2最终记录6391318665](https://github.com/Yredxin/YDental/issues/37#issuecomment-6391318665)，全文读回一致；#37 OPEN/4评论、#36 CLOSED/2评论，全部旧评论及两Issue正文同。首实际同步回执SHA `64d20d0bad2e7160b330b132f6787917a27058c6cb2ae08419e633edf53ad7b6`。此后只补同报告/CURRENT的同步元事实及同一新评论最终报告HEAD，不新增评论、不重复业务；最终ref与独立同步结果以该评论实际读回及私有final-sync-independent记录为准。#37只新增本P2一份最终记录并保持OPEN；旧6384111913及全部旧评论不改，#36保持CLOSED。网络失败单列SYNC_PENDING；不因本地报告产生就冒同步成功。

P2交付后停止，不自动P3—P6。完整S13、负载、备份恢复、实机、正式政策、S11组合扫码、真实外部通道/患者资金及生产仍未启用，不合产品main、不部署。用户带最终结果回GPT审查。
