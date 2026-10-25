# DL-P6：仓库物料／批次查询与只读定位

[CODEX-FINAL] YD-S13-DL-P6 / 1.0

技术：TECHNICALLY_COMPLETE（限定P6软件；未实现者本地技术总签已实际完成）。同步：本轮SYNC_PENDING。用户亲手效果：待确认。P1—P5既有技术/同步结果、P5 PARTIAL历史/新旧包和所有失败/UNKNOWN保持，不重开历史全套。

## 固定候选、范围与分工

- 产品及实际后态运行：aec20359d6f0cdc0e7a1f1070bcc870fd0798b95；工具/准备/真实前态：539d147d659a6214d16e2796460728912f810ccf。私有测试工具按每次executed源/依赖/进程结果固定，不能用最终源码反签旧运行。报告草稿HEAD5c4bf27只三文档，最终报告锚点在本次实际同步回执固定。
- 从P5最终ede6205976f28f6367bcd2a33aa785d96f6aff21及产品beea6d3正常承接；core f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb、原合成目标/OID2171423/cluster7694897083368259627和原filestore保持。开工clean，未reset/clean/强推、重建产品、新建/复制/改名库、合并或部署。
- p6_product唯一addon写者；p5_resume_tester只实现私有测试工具并实跑浏览器/构造包；p5_resume_acceptance未实现产品或相应测试工具，独立原源/请求/原图/进程/新物理RO/包/总项验收；root唯一环境/状态/报告/同步主控。共享OS不冒权限隔离。已有正常团队实际响应，无新平台限额返回，不再调查旧额度或索要相同status。

|改区|实际边界与冻结证明|
|---|---|
|查询section|保留原not can_catalog or config；原q-only GET/max100。现有request.httprequest.path门控inventory_lookup，can_catalog不冒页面标识|
|批次标题/九列表|原visible_lots/table/锚点/data-flags/字段/顺序，局部标记与滚动；单份DOM，不跨进前方8办理区或目录管理区|
|来源标题/只读前缀|原article共同父不改；仅h3至Native movement包局部wrapper，在原can_write前闭合，13办理details原源保持|
|末尾来源nav|原scan标题/form/help后仅整理nav，原search_url/search_page/has_more不改，不包扫码|

仅限定XML/局部SCSS/manifest CSS/15独有PO。无产品JS、下拉、自动补全、统计、lot_id接口、controller/model/service/ACL/schema/财务政策或全局主题变更。集团目录没有P6 scope/help；原错误页、采购类型入口及P1—P5源码保持。

## 字段、查询与定位契约


|位置|原投影与保持语义|
|---|---|
|GET查询|q、maxlength100、原回显；不提交event_id/page，不自动选批次，输入/失焦不预请求|
|批次集合|visible_lots；term.strip().casefold()在product＋name中包含；不扩展编码匹配、不排序或分页|
|来源集合|原本店来源或当前店为target的transfer；product.name/default_code/lot.name的原ilike；合法目标调拨不被额外过滤|
|批次列1—3|l.product / l.name / kind_labels[l.kind]，原row顺序和lot锚点/data-lot保持|
|批次列4—6|l.on_hand / l.quantity / l.quarantine三种原值，不相加、不互代、不新建总量|
|批次列7—9|l.expiration / l.received_at原UTC；l.flags原顺序、data-flags及flag_labels，不补今日/0或“全部正常”|
|来源身份与状态|e.id原event锚点/data-event；kind_labels[e.kind]、e.product、state_labels[e.state]/data-state|
|来源内容|原e.quantity/lot/responsible/summary/synthetic/move_id；不推断单位或成本，实际负责人及待核对默认可见|
|状态|pending待核对；done库存已确认；observed盘点相符、无库存移动，不外推治疗/责任全部完成|
|来源链接|原/ydental/inventory?event_id=<id>#event-<id>，不带q/page，不改变批次集合|
|来源分页|id desc，每页30、第31条探测has_more_events；search_url只q/page，不保留event_id，不伪造总数|
|空态|批次与来源分别说明本范围/本页，均不推断无库存、无责任或已完成|

仓库13/store1为普通有权主路径；读取16/store1和无权17按真实HTTP另验。真实样本3批次/50来源，30＋20两页；代码S11V12-material的真实批次0/来源23与名称筛选差异已采。当前无带target的transfer记录，不能称真实HTTP incoming通过；原域SOURCE、未改产品循环及明确组件分别记录，不造库存事件。真实来源状态只有done，pending/observed及长值使用内存组件，不冒真实业务。


## 实际验证与证据层级

[14项逐项矩阵](acceptance-matrix.md)与[脱敏证据索引](evidence-index.md)分列SOURCE/PURE、原生QWeb内存、BROWSER_FIXTURE、真实HTTP/BROWSER/nativeAX及独立已提交物理RO，不用截图或附件hash代权限/提交证明。

- Chromium **156.0.8078.4**：原普通角色菜单、六查询、编码差异、来源GET/返回、真实30＋20分页和五视口已实际前后采；11原查询投影/字段/ID顺序/三数量/flags/全部URL helpers严格相同。五视口1366×768、1440×900、768×1024、390×844、320×800，原/后根宽均视口宽（320实际320）。
- Chromium原生200%为683×384/root16/DPR2/CDPzoom2，与独立根字号32/DPR1分别实测；zoom41、无JS108、HTTP28、焦点/hover/nativeAX4、长值组件268及单张长尾2各自实际client0/driver0。noJS是在同一自有禁JS context用正常CSRF/password认证，不复制会话，不修登录层既有JS依赖。
- WebKit **27.2**：v1已成六查询/源码契约/四视口、v3已成正常认证选店/菜单→姓名查询→来源定位/返回→原form清q→真实page2→320全九列/原生两横端23分项；两者旧client2如实保留。新zoom-only39分项实际client0/native MiniBrowser4180293 exit0/signull，原生200%root16/DPR2与根字号200%root32/DPR1、各控件和九列/来源首末实际可达。根据同产品/后端/断言未受影响合证，不声称某个旧失败client全程成功或UA替代引擎。
- 五视口及两种压力的长值实际浏览器组件使用已加载产品QWeb/CSS，7条件、210首末对=420正尺寸可见Range、14原生横端、三状态/五flags/四分页边界/False move及转义通过。0ORM业务创建/0修饰CSS；hidden原值仅内存相等布尔。仅显示压力，不代表真实pending/observed/incoming、真实可同现告警组合或单位精度/业务状态机证明。
- 实际已安装MRO：clock仅_now，lab/exam/treatment各业务扩展真实在链，_dashboard来自原inventory基类；legacyclock未启，正常UTC_now。原生trans_export及当前loaded zh_CN arch逐15新增词一致。该native shell实际RO/RR PID235294/rollback/exit0，不冒普通角色业务授权实证。
- HTTP28是断言数，**26目标响应=8×200/16×400/1×403/1×匿名303**，另2非空投影断言。warehouse13含read、reader16真read正例，none17原403；当前门店无关180和合法格式-1原200空，未泄漏，不冒403。原域允许incoming transfer但现场无记录，按未改SOURCE/组件及数据流证明不额外过滤，不宣称真实HTTP incoming通过。通用撤权/revision按未改源码及固定历史复用，不重放库存办理。

## 冻结、对比度与真实取景

原13办理details/scan/title/help/header/error/全部原投影/循环及URL独立SOURCE保持。core-v2在五视口逐一对9个可渲染办理面板作45次只读原生开闭（该数不含core-v1及noJS另有的原记录开合），无提交；同UID13/store1/q默认/page1/1440×900的完整9对象及内部computed strict exact，五视口原字段/scan/header与可见bounds、三代表控件CDP实际匹配/继承规则无P6选择器/主题祖先。其它条件下闭合隐藏子树cold computed原采样不一致，原FAIL/raw真假全部保留，不归一化、不称五视口所有隐藏computed字符串同，也不追溯诊断引擎永久原因。

四旁路catalog/P5结算/P4报表/文书正常角色菜单只读，同条件已采节点/字段/computed exact；P4只对源码确定query_at单p真实时点分类。目录原main text因空白不称全文byte同；无P6 scope、原元素/字段/内部样式及权限入口保持。无PDF、原件、预览生成或旧经济全链重跑。

实际329正文computed对比度最低 **5.6130**；必要输入边界 **3.3191**，焦点最低 **7.0613**；原按钮普通/hover文字6.0047/7.6894、来源链接5.8279。只本四片段，不冒全站认证。原生AX不冒实际屏读/OS输入法/实机。

原对照图角色/条件/视口固定，scrollY分别记录，不冒逐像素。四张after-only真实query/source-prefix顶部图完整单视口；原source-ending组件图实为link-focus取景不称摘要尾，另补一张320真实末Range后的summary尾图（scrollY3001/最后“摘要末端<&>”可读），不重跑268链。

## 全阶段完整保护与正常收尾

P5末态→P6初态九区逐值同；原1269及更早全部audit保留。root初态2e227924…与新physical228803独立核；新候选physical232577与即时pre dd6cd60d…精确绑定。唯一inventory加载实际0/ERROR0/noNative（2ff56f02…）→完整post33b1c264…→physical233360独立94a43ad7…通过，不重复-u。

最终root完整snapshot **21660b079407fccb0c4624986c087c4c0f80c25d29a9770f0ee81e5b645d2752**；未实现者新physical **251350** RO/RR/rollbackclosed完整145业务/13技术/现场**83**文件bytes-size-SHA，snapshot **aaa1921058d2834f218f6fd5955d99563ab7b1b184cd851fa61c725de9e66de2**，九区与root逐值同。全阶段独立保护回执 **db91f7261a2d3795768cc39445443f1512c58470d8e99332e148e5b088ada9ce**，覆盖P6起点/加载pre/实际exit/post/最终，不用主控摘要或包核代保护。

P6新增 **217 accepted审计=before65＋after152**：inventory.view76、settlement.source_view56、settlement.invoice_view14、login23、login.scope23、store.switch23、report.view2。旧audit无改删；实际没有新增持久拒绝audit，不把HTTP403冒审计提交证明。加载仅49 ir_access/group69/mutex1的write_date（revision0保持），九技术类逐值分类；inventory1583当前arch按计划更新，settlement1602/print1618仅arch_prev技术值，current arch_db保持；postload→final除audit新增外所有完整区/技术元数据同。身份作者价源/金额/库存/未完成责任/原65内部＋2外部原件及83文件、schema/配置保持；1303与lot253收10/用2/余8是保护锚点，不硬编码未来查询。

新增原件、PDF、打印、签署、模板发布、收退款、出账/免单/日结、治疗、扫码及经济库存动作均 **0**。新临时权限0。

最后owned run20261025T111857Z-82afd15585b3于 **2026-10-25T12:19:33.567280Z** 正常stop_requested/child0/signull/groupstopped。所有browser/profile、active、18411/12及其他目标连接为空，独立OS收尾d60822b9…通过；未动共享服务。之后只有离线报告/包及正常GitHub同步，不为报告复开服务。旧时间/STOP/准入原字节保持，本scope expiry未延长。

## 原失败与限制

15实际client **7×0/8×2**，全部实际命令/PID/source/依赖/日志/退出在索引，不把非零整轮倒签。非零包括before重登录等待/poll API、after driver在with内None、隐藏cold样式断言、focus定位器重focus工具错误、WebKit左端等待/登录前资源404/native200取景预检。对应成功分项按准确固定候选复用，剩余定向补证单独成功；未记录的旧driver/left/bbox仍UNKNOWN，不事后补造。

WebKit-v2原minimalJS/font404及Chrome组件初始CSS404保留。root11:55:15UTC同URL当前200只说明当时健康；v3恰一次正常reload后认证并走链不证明旧404根因。新zoom当前y=-0.1484/-0.2969仅该次原geometry，不倒推v3缺失bounds，不缩字/改CSS/响应/认证来迁就。旧Native139、Firefox字形及所有旧UNKNOWN不追溯诊断。

准备期系统解释器缺依赖、首源码基线读到短暂overlay后改从固定Git对象、私有构造Path而非bytes、v1包缺WK320选图等原尝试均留档；未实施业务/未预签PASS，不以附件自报代实测。真实来源仅done，policy未配警示保留；flags/pending/observed/incoming长值分层不冒普通角色实数据。真实OS输入法/屏读/Safari/iOS/实机/正式政策未验。

## 私有效果包

最终候选 **.local/dl-p6/viewing/S13-DL-P6-view-only-20261025-r2.zip**：**2,360,375B / SHA256 b7db94f37dd540eedefac890863efa01d2fba0a7eef887cc5650d408f87eb430**。38成员/37非self manifest/33原PNG，实际角色/视口/scrollY/fixture/候选和原失败上下文完整标注，首版v1原字节另保留；P5两旧包不覆盖。包构造时报告5c4明确草稿，最终报告以回执固定，避免zip/报告自hash循环。

主控与未实现者分别实际读回；全成员/manifest/源bytes/PNG/privacy独立回执 **512acbe8569c3db4a406629be8b82ed605f4e980e755728d919e791e3301638e**。不含凭据/Cookie/session/profile、连接配置、原请求、完整数据库投影、备份、程序、字体或PDF；只本机和授权会话查看，不传Public。

## 普通岗位7步复现

正常复开后执行，不承诺当前在线或自动化窗口可接手：

1. 普通仓库岗位正常登录，选择授权门店，从原菜单进入库存。
2. 输入物料或批次名称，用查询按钮或Enter明确提交，阅读两集合范围说明。
3. 阅读九列原值，区分“账面实存”（在手）、“可发数量”（可用）和“待核查”（隔离），注意UTC日期/告警；空集不解释为零库存。
4. 窄屏聚焦表格后用左右键读全部列，无告警不推断全部正常或可发放。
5. 阅读来源类型、库存状态、数量、负责人和摘要，点击实际“查看本条来源”定位原锚点。
6. 浏览器返回；按原来源上一/下一页翻页，核批次不受来源页码影响，源定位不保留q/page。
7. 原权限显示办理入口时，仅展开/收起或取消，不填不提交；不扫描、不生成PDF或原件。

完整S13仍未完成；P6完成不等于所有UI统一或用户效果通过。#37 OPEN/#36 CLOSED，只新增一份P6最终结果，P1—P5旧回执不改；main仅必要路由，不合产品、不部署。P6交付后停止，下一计划、全链/50活动负载/备份恢复/实机/正式政策/S11组合扫码/真实患者资金外部通道、合并部署生产未启用。

## 独有文案与实际翻译映射


原PO完整前缀保持，仅新增以下15词；已用原生trans_export实际提取并逐项核当前loaded zh_CN arch，非手工词表冒加载。状态/flags仍用原controller稳定key及原翻译，不重定义规则。

|新增英文源|实际中文|限定位置|
|---|---|---|
|Lots match product or lot names. Source records also match product codes. Only source records are paginated.|批次按物料或批次名称匹配；来源记录还可按物料编码匹配。下方翻页只针对来源记录。|search|
|Submit the search to update the displayed results. Typing alone does not apply a new query.|点击查询或按 Enter 后更新结果；输入中的文字尚未生效。|search|
|On hand, available and quarantine are separate values. Dates are shown in UTC. No alert does not confirm that stock is issuable.|在手、可用和隔离分别显示，不可合并理解。日期为 UTC；没有告警不代表可发放。|lots-help|
|Focus the lot table and use the arrow keys to read all nine columns.|表格可局部横向滚动；聚焦后使用左右方向键阅读全部九列。|lots-help|
|No lots are displayed for this name query in the current authorized scope.|当前名称查询和授权范围内，没有可显示的批次。|lots|
|Opening a source only locates its record. It does not receive, issue, verify or recover stock.|查看来源仅用于定位记录，不会接收、发出、复核或恢复库存。|sources-help|
|No source records are displayed on this page for the current query and authorized scope.|当前查询和授权范围内，本页没有可显示的来源记录。|sources-empty|
|Inventory source quantity|来源数量|source-summary|
|Inventory source lot|来源批次|source-summary|
|Inventory source responsible person|负责人|source-summary|
|Inventory source pages|库存来源分页|pagination|
|This is the first source page.|当前为首个来源页。|pagination|
|Current source page|当前来源页|pagination|
|There is no next source page for this query.|本查询没有下一来源页。|pagination|
|Pagination applies only to source records, not to the lot table.|此处翻页仅针对来源记录，批次表不分页。|pagination|


## 实际本地技术总签

2026-10-25T12:42:06.913403+00:00，未实现者完成实际14项本地技术总验收：acceptance/technical-total-local.json SHA **d5f60e25649e7d7aec71f13684f0c98c95717e12bc49ae864bcbc652b2d50ccc**，LOCAL_TECH_ACCEPTANCE_PASS_REMOTE_PENDING。软件、冻结无新增回归、完整阶段保护、新包和owned收尾齐，无剩余本地技术缺口。原签时间远端尚未执行，不预签GitHub；本轮SYNC_PENDING，用户亲手效果待确认。最终正常push/ref/全文/唯一新P6评论与Issue状态在实际读回后记录，不复开服务或重采业务。
