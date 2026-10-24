# DL-P1 独立验收矩阵

本表由未实现产品或测试工具的 `/root/acceptance` 维护，当前是**有限结果，非总签**。产品候选 `63ae208b09e1c582ed2493f0cba78cc7a94731fb`；真实旧产品/旧 CSS 前态候选 `31ef5d7bb8e181bdd044c9bd6d77db20f1dbd5ef`，其 addon 字节与 `06c7a4639a107e70c3db6352f8f929db80e6f94a` 相同。源码、HTTP、真实浏览器、显式组件夹具及独立物理只读保护分别记录，共享 OS 不构成隔离。

证据代号均指本机私有原始结果与其图片/正常进程退出，公共仓库只保留脱敏索引。`B`=before-v1；`A`=after-v5；`C`=Chromium complete-v5；`V`=Chromium popup-capture-v1；`E`=edges-v6；`T`=touch-v1；`N`=none-shell-v1；`J`=native-fallback-v2；`F`=Firefox controls-v5；`H`=HTTP-v5；`R`=revocation-v2；`U`=print-only product-v1-upgrade。每份使用实际记录的工具 SHA/运行 ID，不把此前失败进程改写为通过。

|TC|预期及实现位置|实际结果/证据层级|当前状态及限制|
|---|---|---|---|
|P1-T01 范围/复用|仅查询与两处预览选择器；`ydental_document_templates.xml`、`documents_query.js/.scss`、manifest、zh_CN|SOURCE 五文件差异；区域外 XML 前后缀及原选项表达式保持；两新增 frontend 资产。复用锁定 core 的 Interaction、normalize、reposition、addLoadingEffect；原 controller/model/PDF/其他岗位未改|PASS（限定 SOURCE）。无全局主题、后台整包/框架迁移、schema、权限或 renderer 改造|
|P1-T02 风格/文字|A 色、16px 基准/相对尺寸、必要中文和主次按钮；局部 SCSS|A 的17图及 V 的7张展开图已亲看。V 实际14组 computed rgba 由验收者独立重算：最小正文5.613、必要边界3.319、焦点7.061；合成/待签/源权提示保留|Chromium 范围 PASS；F 的中文缺字视觉 FAIL 尚待适用第二引擎补验。不得宣称全站 WCAG/全部平台字体通过|
|P1-T03 流式布局|1366×768、1440×900、768×1024、390×844、320×800；局部 Grid|B/A 同条件15对、查询区5视口及 V 浮层7图已亲看；根尺寸逐对相同。窄屏自然堆叠，标签/说明/按钮可换行|PASS（改动区/不新增溢出）。320px 根 client320/scroll345 是旧限制，未声称整页已移动端适配或扩大范围修旧列表|
|P1-T04 放大/长中文|真实浏览器200%缩放与独立200%根字号；不改库凑长数据|C/V actual tab zoom2、CSS viewport683×384；独立根字号32px/DPR1压力场景；已有授权长来源真实换行可读。长夹具新capture-v1六浮层及错误图已亲看：320px触发器813px，浮层仅14px；200%根字号浮层仅26px，均无可读候选内容区|FAIL（当前63ae长源可用性），待本组件普通修复与适用复验。长字段为明确组件文本夹具，不是DB患者/模板事实；工具bounds/expanded通过不替代文字可读。OS字号/物理移动端不冒已验|
|P1-T05 中文输入/提交|GET q、maxlength100，Enter只搜索，组合期间不误提交；查询 form 与 JS guard|C 真实菜单进入/普通doctor9，q=P00001313及浏览器协议组合输入、实际GET/回显/返回；可信 compositionstart/update/composing Enter与显式非可信compositionend分列。SOURCE maxlength/编码原服务不变|PASS（BROWSER_PROTOCOL_INPUT/HTTP）。不是物理 OS 输入法实测；方向键输入夹具另列组件层|
|P1-T06 单选值|原生 select 为唯一 name/value；空来源 required、空模板合法；不嵌套表单|C/E FormData selection/template_id 各一次、无嵌套；空来源无POST且焦点到可见触发器；空模板仍明确合成未审核；真实 preview 提交clinical:507:2及q/page；J原生字段可用|PASS。只改可见交互；不把业务标签当提交 key；已发布模板种类检查仍在后台|
|P1-T07 键盘/焦点|active与confirmed分离；上下/Home/End、Enter/Space、Esc、Tab/Shift+Tab|C/E 实际组件按键；移动不提交，取消不改已确认值，Tab确认后自然到模板/预览，外部焦点目标正常收到点击；滚动/resize安全关闭；reset同步|PASS（BROWSER）。不将 AX/模拟组合事件冒屏幕阅读器或真实OSIME|
|P1-T08 浮层|边缘/滚动/长项/缩放/触摸，活动项可见，portal只本实例|V 五视口及两放大普通浮层真实可见；E滚动/resize安全取消；T触摸模拟真实组件；SOURCE portal限定。长源capture-v1在320px/根字号200%被core reposition的上下剩余空间收缩成14px/26px细条；nativezoom长源69px底部图也不能证明候选可读|FAIL（长项浮层可用空间），待局部修复与真实视觉复验；普通场景已验部分保持。C旧full_page图不反签，长夹具工具passed状态也不冒本项PASS|
|P1-T09 ARIA/降级|可感知名称/关系/active/selected/error与可见required焦点；JS禁用**或**初始化失败分支|C原生AX293节点中两非ignored命名combobox、source listbox/controls/activedescendant/expanded/focused/required及option选中态已独立核；J禁JS仍以原生表单正常预览且图片清晰；SOURCE成功mount末尾才hide、异常destroy恢复|PASS（适用 AX/BROWSER/SOURCE）；计划OR分支以JSoff满足，额外初始化失败实测不设AND门槛。屏幕阅读器硬件NOT_RUN，不宣称全面无障碍|
|P1-T10 真预览|普通有权医生正常菜单→搜索→选择→单独预览，保留原正文/限制|C/A normal doctor9，clinical507/version2、空模板，HTTP200返回srcdoc；1366/320实际iframe元素裁剪可见正文/来源作者/未签含义；处理中按钮禁用但真实字段保留，返回可继续|PASS（HTTP+BROWSER+独立视觉）。未点generate/打印/签署。部分full_page截图iframe空白是采样观察，实际可见裁剪另列|
|P1-T11 边界拒绝|无源、非法源/模板、跨店、旧revision/撤权旧页仍由后端核|H 17类实际结果：源版本/格式/种类409，已有错kind模板403，无财务/跨店源403；无源页200空shell而直预览403；实际授权切店使旧revision409，回店新revision200；R manager正常撤权medical9，旧form/95下载403，精确复权后200|PASS（真实HTTP/工具另开物理RO提交读回）。数值不存在模板继承合成fallback200明示保留，非法格式409/错kind403不混称；未为P1修改原业务契约|
|P1-T12 无副作用|搜索/选择/预览/旧下载不生成新原件/版本/经济库存；全部83原件附件/责任保护|U即时145业务/13元数据/83文件前后已独立分类；只技术时间/视图变化，所有实际旧文件和非技术业务同。C/H只预览/旧308或95下载，R临时权限按正常机制恢复|PENDING 最终独立新物理RO/83文件及完整责任对照。正常读取审计、会话/资产元数据另分类，不要求物理零变化|
|P1-T13 未改区/旁路|页头/列表/生成/管理内部不改，其他岗位代表入口保持|B15与A17全图已亲看；原始15对 named outside regions/computed/后代控件逐字段相同、根尺寸同。结算/仓库/native214前后PNG实际同SHA；报表实收USD1300/3笔500+300+500和条件/样式同，仅真实query_at10:40:02→11:11:13|PASS（SOURCE+有限computed+BROWSER/视觉）；允许上区自然撑高造成y位移，不冒四旁路全DOM或全业务重验|
|P1-T14 多引擎|真实Chromium完整流程＋Firefox或WebKit之一同页面搜索/展开/选/取消/预览/缩放|C/V真实Chromium与F真实Firefox157.0均进程0、无信号，非UA替身；F正常请求/键盘/原生fullZoom2可用但7图中文tofu，JSON/AX文本不代视觉|PARTIAL / BROWSER_VALIDATION_PENDING。正待符合计划的第二引擎中文实际图片；Firefox缺字不反签，不降低门槛，不转做P2|
|P1-T15 候选/加载/回归|固定候选、即时适用pre→print-only-u→post，影响面验证|63ae U actualexit0/ERROR0/noNative；pre db39…→post cdb3…，独立e92b…分类145/13/83；25ir_access+1group仅write_date、原权限值/约束/PDF/全部文件不变。其余表单HTTP/浏览器继续绑定同产品|限定加载 PASS，最终未解决动态项仍在各行；未重派已完成39方法或经济链，不拿纯文档变更触发业务复演|
|P1-T16 独立收口|全部适用项、私有只读包、5—8步路径、同步、服务收尾；只签P1|未实现者已核SOURCE/上述原始结果/实际图片，有限私有回执均0600；尚无本阶段总签|PENDING：第二引擎/长夹具、最终保护、包/同步/停止。P2—P6 NOT_AUTHORIZED，#37保持OPEN/#36CLOSED，旧6382778460不得改作本阶段回执，不合产品main/部署|

流程覆盖：F1搜索到明确预览已有真实HTTP/BROWSER/可见iframe；F2键盘确认/取消已有实际组件证据；F3无源/旧页/撤权已有产品层拒绝及恢复；F4五视口前后及未改区已有限通过，最终无副作用保护仍待统一新物理只读连接。用户亲手效果始终待确认。

历史与限制：Chromium旧full_page截图触发浮层关闭，未冒展开视觉PASS；V补采只为当前同候选补证。Firefox当前中文tofu是实际缺口，即使随后另引擎通过也不称全浏览器一致。HTTP v1—4、边缘/长夹具早期工具错误和退出码按原件保留；缺失模板fallback200、ensure_db首次同路径302、同店切换不提升revision均按原契约分类。旧客户端Native139因果UNKNOWN，不由本阶段进程0反签根因。OS IME、屏幕阅读器、Safari/iOS及物理触摸设备NOT_RUN；用户未接手无头窗口。本阶段无新文书/PDF/库存/经济正例。
