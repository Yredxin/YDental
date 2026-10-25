# DL-P3：已保存原件列表、状态、分页与只读追溯

`[CODEX-FINAL] YD-S13-DL-P3 / 1.0`

技术：**TECHNICALLY_COMPLETE（限定P3软件，未实现者本地技术总签已实际完成）**；同步：SYNC_PENDING（尚未执行最终远端收口）。
用户亲手效果：待确认；P3启用不代表P1/P2已获亲手验收。
P1/P2保持TECHNICALLY_COMPLETE / 原交付SYNCED，不重开、不重跑历史全套。完整S13未完成；#37保持OPEN，#36保持CLOSED。P4—P6、生产及产品合并未启用。

## 范围与固定锚点

按用户本会话交付的[完整计划](../../execution/S13_DL_P3_IMPLEMENTATION_PLAN.md)连续实施W0—W4，沿用[杏陶暖白设计语言](../../design/YDENTAL_DESIGN_LANGUAGE_V1.md)。仅改文书页已保存原件列表至分页/空态。单份语义表格、Grid/Flex局部框架、舒展相对字号、暖色、长值换行、键盘局部横读、原生details追溯、明确查看/下载及首末页边界已实现；无新筛选、统计、排序策略、批量能力或JS。

活动分支`codex/s13-dl-p3-documents-originals-r1`从现场合法P2报告HEAD `1d3fe088c029e0d9562325b2895a64ac31945b71`承接，初始工作树干净，incoming diff私有保存为0字节。P2已同步当时P1复核补记，没有把它误称当前仍未提交；无未知增量、reset/clean/强推或从main重建。main只必要文档路由。

|对象|实际固定值|
|---|---|
|P2原产品/旧回执|a0b33c14c121f2a489fdcf7abc529999fd15c1dd；#37 / 6391318665，保持|
|P1原产品/报告/旧回执|8dea2647760f6d6738abfc9db132cfa9d7feaee3；d421842c9b26de9988be3f7e4c46cd5626cb67ca；6384111913，保持|
|准备/公共阶段工具|2cfd141adb04b3929af411d9a835fa4165d1bb72；3a30457a8e0f7b3e491e8446f4e04b1284aa47ff修正独立发现的tuple.exists，未放宽旧owner检查|
|真实before执行|d4a94d0eee832cadf82d3c089afd53308b4096b2；addon仍P2|
|首产品/前后对照|2873a3b6d9ac77b7d55fb0da6311c65534df8a11；2处实际旧译文复用已保留|
|最终产品/执行|**b72bcd6d125aad45bf8e62fb7596d5bb5725ac13**；仅在首产品上改2英文源和P3新增PO键，字段/请求/SCSS/manifest相同|
|锁定core|f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb，未改|
|报告HEAD/同步|后续仅同CURRENT与3份报告；以最终回执实际ref/正文读回为准，不当新产品候选|

全阶段产品恰4文件：`ydental_document_templates.xml`、新增`documents_originals.scss`、manifest一条资产注册、25条新PO项。原P1 JS/SCSS/字段/帮助/ARIA、P2页头/5导航/3类重要说明和SCSS、preview/iframe/生成/previous_id及Operation提示前缀、管理/导出后缀逐字保持。既有打印details子树190字节，SHA `d8a87b1d1ca0811f39707abfe7c844bd1e7e167a81867e3a4bb6efb7a2a4ffb8`逐字保持；不对其内部设新样式或父级字体色。后台model/service/controller/ACL/schema/PDF/其他岗位和共用网站页头未改，未全局覆盖主题。

真实团队：root环境/运行/集成/报告/定向HTTP；documents唯一产品写者；tester私有工具/真实浏览器；acceptance未实现产品或测试工具，独立源码、原图/请求/字节、新物理完整RO、包与同步验收。同OS共享，不冒隔离。实际命令、源码SHA、退出与证据位置见[索引](evidence-index.md)，适用断言见[14项矩阵](acceptance-matrix.md)。

## 字段、状态与文案映射

SOURCE来自冻结`ydental_print_original_service._original_workbench/_original_snapshot_status`和controller。原件模型`_order='id desc'`，不是另按生成时间排序；授权后真实计数，30/页，保持原页码钳制与`search_url`的urlencode(q/page)。

|字段|原实际来源与呈现语义|
|---|---|
|patient_name / patient_number|original.patient_id当前name/ydental_number；不是冻结PDF身份声明|
|title|kind_labels按原件kind投影用途；不是frozen_title|
|version|原件自身version，明确“原件版本”，不冒来源版本|
|status|原件冻结source_facts经原_snapshot_status投影；中性全文，不解析翻译字符串上色，不重查当前工单反写|
|generated_at|str(original.generated_at)，明确UTC；非就诊/治疗时间、当地时间或文件mtime|
|synthetic|原template_facts['synthetic']；原合成/适用审核签署警示全文默认可见|
|id|原表单original_id与追溯原件编号；不新增需用户记ID的操作|
|trace|原服务14键原序原值，友好静态标签加机器key；完整hash只视觉换行，复制值不插字|
|分页|既有total/page/page_count/previous/next与search_url；总数仍当前授权查询结果|

trace顺序：pdf_sha256、original_id、previous_original_id、source_model、source_id、source_version、source_sha256、template_sha256、layout_version、template、template_version、frozen_title、details、versions。QWeb转义保留，无t-raw/innerHTML、执行链接、新接口或加载全部患者历史。原False值仍空文本；新固定DD容器避免空值与下一键串联，不转成0或字符串False。

文案变化：表头明确原件版本/生成时状态与查阅原件；增加当前患者标签和历史状态区别、局部键盘横读提示；分页明确“当前授权查询原件总数”“当前页”“已到首页/末页”，边界为非链接文字；空态仅“当前查询与授权范围内没有可显示的已保存原件”。两处源词最终为`Original internal number`→原件内部编号、`Pagination for authorized originals`→已保存原件分页，避免原生旧近似译文复用。实际loaded25新词与map-v2逐节点/属性匹配，不以PO存在冒动态翻译一致。完整映射在私有包copy-map.json。

旧93生成draft与工单214当前sent分属历史与当前；旧95/96/99原范围、版本、生成时间和文件事实保留。已保存、草稿、部分摘录、列明范围内完整和已签署不混称；未为截图改患者、模板、旧状态或业务数据。

## 实际软件验证与复用边界

|层级/场景|实际结果及准确边界|
|---|---|
|SOURCE/PURE|原生xml_translate/PO/libsass和锁定core数据库外QWeb的14DT/DD、False空文本、完整hash与转义通过；未实现者独立重复。7个阶段运行边界PURE不冒业务测试|
|真实前后|doctor9/store1/q空/page1及5视口真实对照；47授权原件两页30+17、ID降序/全集同；47×14原键序/值、患者用途/版本冻结状态/UTC、表单及打印子树逐字核；10页P1/P2/生成管理导出/共用页头内部computed和字段同；3代表旁路PNG同SHA|
|候选复用|上述严格完整对照/定向权限/颜色在2873完成；b72精确仅2静态源词/新增PO键，SCSS/所有字段/请求/后台全同，按影响复用。b72另采同条件最终五视口、正确标签与余缺路径；旧图不冒最终2词已修|
|预览全文|本次before和after实际保存srcdoc与fulltext。独立逐字核实际generated_at渲染时间各只出现一次，仅替换该一次后完整HTML和全文完全同；不回签P2缺before全文的旧限制|
|Chromium|真实156.0.8078.4。正常菜单/搜索、P1选择取消确认与显式preview；q=S真实两页/返回、trace原生键盘开合与hash选择文本、最终五视口、旧95实际行查看/下载、原生200%与独立根字号200%、空态与JSoff、长字段分层完成。早期整个客户端非零保留，已过片段和后续有限补验分别签，不伪称一个旧core全程0|
|查看/下载|保留POST/action、target=_blank、唯一csrf/revision/original_id和submitter operation。Chrome native查看response.body为601B内建PDF shell，不能冒原PDF；该200/inline声明SHA与trace、真实正常HTTP原字节及浏览器下载严格同。WebKit真实点击view取得原PDF，download明确读同次实际Download事件文件；不同内建查看器不强求同渲染|
|旧文件|原95两操作61870bytes，实际SHA/声明头/trace/保护记录/独立filestore文件同：`ceec281451958f0b50fc4ded9a1cbe6b516883605987c436b42fd1fb2130274c`。全部是旧文件读取/复制，无重新渲染或另存新业务原件|
|无JS|同一自有禁JScontext正常认证/原表单查询、q保留真实分页、native details/hash及实际旧下载通过，无Cookie复制或开启JS。Tab能聚焦下载但320右侧约27.6px未自动全显；一次真实ArrowRight使local671→708/rootX0，整按钮完整可达，再Enter真实下载。按原计划局部横读验，不宣称Tab自动全部滚入|
|WebKit|真实27.2，同原厂MiniBrowser/driver/普通角色入口。首轮已采trace/1366/390/320键盘/焦点原图但退出受控失败，未签整轮0；补普通私有appsink插件后，实际旧view字节、正常download、两类zoom左右图、Previous/q/顺序及API语义快照完成。最终client0、实际主进程3794525=0/signull、context/browser正常close、cleanupErrors空。view明确复用前次已保存真字节，不重复发请求|
|字号/语义|两实际引擎原生zoom2与root32压力分列；WebKit实际CSS683×384/root16/DPR2/visualScale1、page viewport1366×768无locatorclip。Chrome真实CDP Accessibility.getFullAXTree在改夹具前采，table1/4列头/两个动作/trace披露/分页名正确；WebKit ariaSnapshot按其API层级列，不冒屏幕阅读器/实机|
|局部视觉|杏陶暖白、相对字号、自然高度与局部横滚。16个实际computed采样文字最低5.613、必要边界最低3.319、焦点最低7.061；独立公式复核和代表原图视觉核，不冒全站WCAG认证。长中文/业务号/状态压力明确为DOM文本组件夹具，不是新增患者或真实业务改名|
|320限制|当前整页scroll345/client320仍在；本区容器有明确横读提示、tabindex焦点/真实方向键及动作可达，无新增根溢出。不称整页移动端完成|

P3定向HTTP实际10例在2873执行并按b72纯静态词增量复用：doctor9 medicalwrite/exportnone读95两次200及真字节；无源none17读95、财务approver15读医疗95、doctor读财务58各view/download403；既有alias无exportwrite且无medical/exam组合，按计划允许经group_manager5普通管理路径仅把none17/store1现有exportnone临时write，新物理RO确认medical/exam仍none，两旧95请求继续403，再正常恢复并RO核全部grant原语义同。2次授权审计保留，未改产品ACL；技术session不冒全部物理复原。门店/revision/撤权未改后台，明确复用[P1固定验收](https://github.com/Yredxin/YDental/blob/d421842c9b26de9988be3f7e4c46cd5626cb67ca/docs/reports/s13-dl-p1/acceptance-matrix.md)，不称P3重跑全部撤复权限。无源shell200不是后台403。

## 全部旧数据、必要加载与运行收尾

唯一既有目标`ydental_s11_synth_20261023_01 / OID2171423 / cluster7694897083368259627`及原filestore。未新增/复制/改名库，五项集群高权false；未改core、odoo-12、共享OS或集群策略。起始完整145业务/13技术/83实际文件与P2最终九区段同，未实现者新物理RO/RR backend77211独立全采确认。

两次必要限定`ydental_print -u`：首次加载新列表，第二次只为实际2词修复；各带即时完整pre→实际exit0/ERROR0/noNative→完整post及独立分类，无i18n-overwrite或旧业务重放。第一次独立完整backend80347，第二次实际25译文新RO82786；1618有效en arch最终=b72、arch_prev=2873，其他view arch/active保持。

最终停机后root完整post与未实现者新物理RO/RR **backend93247**逐值九区段全同：145业务、13技术、83实际文件，65内部+2外部原件、作者/身份/价源/金额/库存/历史和未完责任全部保持。83是现场承接和本阶段实际数量，不永远硬编码。P3新增原件/PDF/打印请求/签署/模板发布/资金库存业务0；固定旧来源1073＋前批230＝1303、本阶段贡献0，lot253收10用2余8保持，不把未来全部查询强设1303或假结旧责任。

非物理零diff：108条正常新增审计（26login、26scope、26switch、2document.view、2invoice_view、2inventory_view、4source.view、6pdf_view、4download、8拒绝document.action、2authorization.change），旧审计无改删。25ir_access/group69仅write_date、临时恢复grant4999仅write_date；intake/patient/queue/supply四个原生mutex1各revision+2，对应既有_grant→_all_locks授权fence，不是实际队列/供给/金额库存动作。8技术表日期和1618 arch另分类，配置/schema/索引和全部文件无变化；新web bundle属于技术资产，不计新业务PDF。认证秘密/session材料按既有排敏投影排除，不声称全库每字段物理不变。

末owned服务`20261025T011527Z-3f1616e009ac`于**2026-10-25T01:54:50.645926UTC**正常child0/signull/owned group stopped，所有browser context关闭，18411/18412无监听、active absent、目标其他连接=[]，共享主服务未动。独立最终RO rollback idle/closed。P3自有scope至12:51:43UTC，未改旧scope/STOP；期限不是在线承诺。正常复开须核当前目标/权限/所有权/固定候选/fresh准入和有效资源，不复制会话或改旧期限。

## 原失败、普通修复及未验证边界

- 运行适配初系统Python缺psycopg2、新父目录775触发原private检查、tuple.exists、clean启动要求、CLI大正文E2BIG/工作目录未建等均按实际修复，原非零/事实留存；未放宽原检查。两次主控pre-dispatch abort首因UNKNOWN，同入口恢复，未取得安全/权限拒绝提示。无被平台拒绝的动作改名转发。
- before首工具匹配旧第二table失败；10个False previous值误取下一DT。原result保留，以后取RO14源事实+原47行raw-cell逐字建立纠正派生，不冒before重新采DOM；新DD仍原值。翻译两词旧值实际漂移，经局部新源键及必要加载修好，不全局覆盖旧译文。
- Chrome首view body断言失败且未存首raw，首因UNKNOWN；后b72实际601B shell与真PDF分层，不倒签首原因。私有Observer误把精确本机chrome://resources/内建PDF extension当外域，总客户端2保留；只修测试本地资源分类，其他外网阻断和driver/认证/平台原样；最小viewprobe0。
- JSoff工具双rAF Promise等待经受控SIGINT实际client-2/driver0，traceback及rAF不回调probe定位；保持JSdisabled改有限原生等待/取图。随后helper模式/语法及新增“Tab自动全显”强假设错误分别保留，不把额外门槛当产品返工要求；最终真实键盘横读/旧下载/可见空态0。首空态取景在P1/P2顶部，不作可见空态证据，已只补正确区域。
- WebKit首轮等待后一次受控SIGINT，Node1来自后续logout TargetClosed二次清理异常，原native退出码UNKNOWN但进程已离开，不冒0或Native crash。日志appsink缺件已核：私有API库存在但app工厂插件缺失；按[官方说明](https://gstreamer.freedesktop.org/documentation/app/appsink.html)及Ubuntu签名索引SHA，仅P3私有目录补同1.28.2普通app插件，两个独立native factory旧false/新true。只加进程local GST_PLUGIN_PATH/私有registry，原引擎/driver/prefs/sandbox/automation保持；这不证明旧等待根因。
- 后续WebKit已获真view字节后仅popup初始空URL诊断TypeError；再一次APIRequest身份探测缺result未存原body，原因UNKNOWN。server登录303/access200及独立RO uid9 accepted已核；等待原生access可见后，用既有正常page同源fetch同endpoint严格核uid9，不换账号、复制Cookie或改鉴权。最终只补download/zoom/Previous，正常主进程0；所有首异常与清理取证错误分别留档。
- 历史Native139、Firefox中文tofu、WebKit初始化404及其他UNKNOWN保持，不追溯确诊或以新成功倒签。WebKit不等于真实Safari/iOS；真实屏幕阅读器、OS输入法/设备、用户亲手、正式临床/财务/签署政策、全S13负载恢复与生产未验/未启。

## 私有包、复现及同步停止

私有只读包`.local/dl-p3/viewing/S13-DL-P3-view-only-20261025.zip`：**3,330,880字节 /0400/SHA256 `885317dfb014a5542eecbdb5aed0d2226694fdcb567b622e41701a2d36934c60`**。36成员=31原PNG（31不同SHA，不冒31业务场景）+README/copy-map/screenshots.csv/preservation/manifest，manifest35项不自引，0PDF。全部实际bytes/SHA重读、31PNG可解析且与选用源字节同；五对真实同条件前后、夹具和WebKit部分旧失败图均按候选/场景/限制标识。无凭据/token/Cookie/session/profile、原始请求、连接配置、备份、程序/独立字体或83原文件bytes，不上传Public。包证明材料一致，不能单独重签业务或完整数据库保护。

普通医生7步（正常复开后，不承诺现在线）：

1. 用获准普通doctor身份正常登录、选择门店A，从文书菜单进入。
2. 搜索既有合成业务号P00000524，读当前患者标签/历史原件说明及原件版本、生成时状态、UTC。
3. 对照草稿、已确认部分摘录、列明范围内完整的旧行，不修改来源或生成新版本。
4. Tab到原生追溯，Enter开合，读完整原件/来源/模板校验值；机器key与原值完整可达。
5. 从同一行明确查看/下载旧原件，再回原页；不点打印请求最终提交、生成或导出。
6. 搜索S，按现有上下页核q保留、原排序与首末边界；本次47/两页，不硬编码未来数量。
7. 320/390窄屏按提示聚焦局部表格、方向键横读/到下载；另用无结果查询核准确空态。

本地软件与保护/包已获未实现者总签，SHA `188c0db20a8a9e8cb70933f391f916e7282f615fa34cd4aece9a82e374a94dfc`，T14local已通过，remote当时NOT_RUN。下一正常commit/push、实际读回两ref/正文和必要Issue状态；仅#37新增一份P3最终结果，旧P1/P2评论不改、#36不改，main只必要两路由文档。当前同步尚待实际执行，不预签未来回执。P3最终交付后停止，不开始P4—P6，不合产品main、不部署。
