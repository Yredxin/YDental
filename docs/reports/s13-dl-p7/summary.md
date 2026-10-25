# [CODEX-FINAL] YD-S13-DL-P7 / 1.0

统一按钮语言与轻量SVG——仓库页面试点。

技术：**TECHNICALLY_COMPLETE（限定P7软件）**。同步：**SYNC_PENDING**。用户亲手效果：**待确认**。完成范围：库存页按钮/图标，非全站。后续页面/完整S13/合并部署生产：未启用。

## 固定候选与真实分工

- 最终产品及实际运行候选：**52d5422fa0083bf88cec4442ffcd45d35d27e9f7**。首产品f3f8e6114bda27eabc18140d60bd9b8eb044e99e/运行工具d61200b保留；最终只补43个span的原生翻译边界，未改CSS、业务或原文。实际浏览器私有工具按各次executed源/依赖/command/退出固定，不拿最后工具反签旧运行。
- 从指定P6分支 **e31ea56d1ff903461eda86c08088c5f7e32aef7e** 正常承接；开工clean，无reset/clean/强推/从main重建。前态实际工具29bccc48e67878203369f66c0abacf38b243869b，产品仍P6。P6产品aec20359、工具539d147及唯一回执#37/6397824653不改，P1—P6技术交付承接，用户效果均分开。
- core **f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb**；唯一既有 `ydental_s11_synth_20261023_01 / OID2171423 / cluster7694897083368259627`及原filestore。没有新建、复制或改名数据库。
- root为唯一产品/状态/报告写者和环境调度；testing编写及执行浏览器工具；runtime适配运行、原生QWeb及包工具；acceptance未实现产品或相应工具，独立SOURCE、实际原件/图、物理保护、包及远端核验。同OS不冒隔离，未实现者不替用户签效果。

## 控件、权限及呈现映射

|原控件|模板定义数|变体/图标|保持的语义|
|---|---:|---|---|
|查询button|1|primary / search前图|原GET、q、maxlength、Enter，按钮仍按钮|
|办理确认button|13|primary / 无图|原submit、全部form/submitter属性，不把确认画成已成功|
|办理summary|13|disclosure / 无图|原生marker、details/name分组、开闭和权限，不加第二箭头|
|原取消a|10|quiet / 无图|原href；后3来源族原无取消，未新增|
|来源a|1（来源循环）|quiet / arrow-right后图|原event_id+anchor，导航仍链接|
|原前/后页a|2|secondary / chevron-left/right|原q/page helper，边界原文字无假链接|
|仅识别button|1|secondary / scan-line前图|原scan POST/字段/type，不表示已接收或入库|
|原批次/来源标题|2|package/list|原文字、数据和其它布局|

13办理族：can_write头部setup/policy/lot/receive/issue/inventory/transfer/lot_edit；can_catalog的product/product_edit；来源can_write中的return（replenishment/prescription且done）、verify（return）、recover（pending）。普通warehouse13/store1真实显示9族；余族及缺状态用明确loaded QWeb内存组件，未造业务。

共43呈现节点=15button+13summary+13a+2h2。SOURCE工具仅验证并还原许可的class/文字span/SVG/翻译边界后，**整个原XML canonical exact**。字段、可见条件、action/method/type/name/value/csrf/revision/key/operation/required/disabled、DOM顺序和原helpers不变。controller/model/service/ACL/schema、输入/select、九列表及其它页面不重做；无新增产品JS、自动提交、全局click或确认弹窗。

## 设计与资产唯一入口

`ydental_inventory/static/src/scss/inventory_actions.scss` 提供元素级tokens/变体。准确路径复用 `inventory_lookup`，元素opt-in `data-dl-actions="inventory-actions"`，不用can_catalog判页；无表单祖先字体/颜色、全局button/a/summary/.btn/:root覆盖。原P6仅删34行目标按钮/链接专属CSS。

统一1rem/600、.625rem圆角、min2.75rem、padding .625em 1em、gap .5em，自然换行增高。primary陶土白字，secondary浅杏/深陶土及必要边，quiet下划线/轻底，summary原生list-item。default/hover/active/focus实测；disabled/busy/danger仅明确组件，产品没有伪造这些状态。仅140ms颜色/边框过渡，reduced-motion关闭；无厚阴影/大渐变/装饰动画。两引擎五视口actual computed最小正文 **5.2016318344:1**、必要边界 **3.2401343224:1**、焦点 **6.9537654008:1**；仅本scope，不称整站WCAG认证。

Lucide固定 **0.468.0 / f12b0de177fbc2a6795e99be065887e72b237123**。七个原SVG、完整ISC及完整Feather MIT在 [static/lib/lucide](../../../ydental_inventory/static/lib/lucide/SOURCE.json)。Feather许可固定v4.29.2/1b002399e8758fb2bccea4d07312dc9e0f43dcb8，Lucide原版权声明同时保留。SOURCE.json记录每个原文件SHA/来源/修改。QWeb几何与上游逐项相同，仅加局部类、装饰属性和相对width/height：24网格、线宽2、round、currentColor/no fill；控件1.125em、标题1.25em。无runtime/CDN/字体/外链/on*/script/foreignObject/t-raw，中文可见，SVG无独立Tab/重复名称。

## 实际分层验证

|层级|真实结果及复用边界|
|---|---|
|SOURCE/PURE|完整原合同还原、43节点/7图/官方来源和许可独立核；11 runtime PURE边界不冒产品实测|
|真实Chromium156.0.8078.4|main-v2：五视口、54唯一PNG、图/字/Enter各单GET、原来源/真30+20页/取消、9可见族开闭和确认焦点、中文/可访问名称及内存FormData|
|真实WebKit27.2 WPE|v2已成8读取分项＋controls-v5五视口/54唯一图＋独立13步自然Tab轨迹，同52候选合证；旧v2整client仍FAIL。矩阵focus明确真实键盘模态+programmatic focus；自然Tab另证，不混层级|
|两种放大|两引擎各native200（原生page zoom2/root16）和独立root200（root32/native100）分别实测，各20原图，不用改viewport冒缩放|
|真实无JS|两引擎javaScriptEnabled=false，同context正常CSRF/password认证；有限原GET/来源返回/真实分页、1366及320两代表视口、summary Enter/Space、query原生Tab、confirm directfocus分别标；各5真实native viewport图。全五view/hover矩阵另由JSon实证，不重复混称|
|原生QWeb内存|actual loaded zh_CN 13族/10取消、20翻译occurrences=18唯一原词、原字段/submitter/分组及空内存token；RO/RR275925/rollback、0业务创建；不冒真实授权或办理成功|
|浏览器组件/故障|Chrome fixture-v1前10有效分项＋faulttail-v1后5项；其原client2保持。WebKit fixtures-v1完整PASS：五视口长字、disabled/busy/danger、13族FormData、原错误main、SVG/CSS缺席、reduced-motion；forced-colors仅支持的Chromium实际核|
|读取前后/旁路|7共同main投影严格同；catalog/P1/P4/P5/none有限所采fields+computed严格同，reader无write-details，分类动态字段0、无归一化。none真实403与库存action-error明确区分，后者仅未改SOURCE+loaded main组件，不发POST造错误|

五视口：1366×768、1440×900、768×1024、390×844、320×800。原三数量、行集/顺序/状态/flags、q/event_id/anchor/page与九列表保持。未影响算法、P6原26响应/权限与缺样边界按相同源码明确复用，不重跑旧经济链。原incoming/pending/observed等无真实样本不冒实测；组件不证明重新办理成功。原生AX/可访问名称不冒屏读、真实OS输入法、Safari/iOS或实机。

## 完整保护及正常收尾

初始独立physical266501与最终新physical **288600** 均READ ONLY/REPEATABLE READ、rollbackidle/closed，完整145业务/13技术与root九区逐值同；P6末→P7初始→两次必要加载pre/post→最终全阶段独立分类通过。

**现场计数澄清：83个受保护附件文件引用，对应80个唯一物理存储路径、80个不同SHA；三处为既有原生共享存储引用。83引用及80文件全部存在、尺寸/SHA/字节保持。没有丢3文件，也没有本轮去重或删除。** 旧P6报告/回执及原raw不改，本P7按现场唯一清单表述；65内部+2外部原件及旧责任保持。

|必要加载|候选/原因|实际及独立保护|
|---|---|---|
|product1|d61200b；初次模板/7SVG注册|exit0/ERROR0/noNative；7新view+7XMLID、1583 arch/prev及10技术类分类|
|product2|52d5422；43span保留原翻译术语|exit0/ERROR0/noNative；无新业务/视图，1583 arch/prev和7SVG原生arch_prev备份刷新及9技术类分类；7SVG active arch不变|

没有为纯CSS重做-u。两次业务差异都仅49 ir_access、group69、inventory_mutex1的write_date（revision仍0），权限内容不变。全阶段 **17,431条旧audit无改删；新增200条accepted**：login/login.scope/store.switch各34，inventory.view94、settlement.source_view2、report.view2。其余业务无新增/改删，原金额/库存/作者身份价源/未完责任及配置/SMTP/schema/约束/索引保持。新增原件/PDF/打印/签署/发布/scan/收退款/治疗/经济库存动作 **0**。

最后owned run20261025T135854Z-3a6a00c1da8f于 **2026-10-25T14:48:28.068882Z** 正常stop，child0/signull/groupstopped；独立OS/端口18411/12、browser/node/profile/active及其它target连接空，无临时grant，未动共享主服务。旧scope/STOP/guard/时间与UNKNOWN保留，P7新scope未延长，不为报告复开。

## 私有效果包

本机授权会话只读包 `.local/dl-p7/viewing/S13-DL-P7-view-only-20261025-r1.zip`：**2,396,745B / SHA256 6ddf2df5e54df61e898ea21fa553d125059c7a0366e43e30cdc1daa6cb356df6 /0400**。37成员，34原PNG/33不同SHA（catalog前后原图同字节）＋README/截图索引/manifest；逐图候选/层级/真实视口/DPR/scrollY，缺图时身份明确UNKNOWN，不拿client末尾uid猜每图身份。无裁切/重采样/美化，不称前后像素对齐。前后/展开/hover/focus/窄屏/两种放大/无JS/明确组件和故障图齐。

不含凭据/session/profile、连接配置、raw请求/日志、完整DB投影、原件/PDF、程序或独立字体。不上传Public，旧P6/P5包保持。独立包已逐37成员/36manifest、源字节/SHA、34PNG解码/尺寸、实际候选/退出/隐私全核，回执 **aaa9e1141fb9ac09b4c326e5a8ca2ba42734d57247137f5e6229e23fd9d0f7eb**；旧P6包SHA仍b7db94…。构造者不自签，最终总签及远端读回按实际发生后记录。

## 失败保留与限制

22实际浏览器客户端：**13×0、7×2、2×130**；每次actual source/依赖/command/退出/native/raw均单独固定。最终各适用分项按同52产品合证，不称所有client整轮通过。

- 前态截图50索引/45唯一PNG；5次同名末次覆盖，其中3初索引SHA已不可核。旧结果保留，包只选当前可核末次字节，后态所有shot拒覆盖，不重跑GET补图。
- 首产品新span变成含markup翻译术语，真实中文回归；原生导出/独立窄读定位后仅加t-translation=on，原词/PO/语义不改，最终43中文恢复。原失败不反签。
- 140ms过渡中即时采样曾得3.1249；真实180/400ms稳定白字/陶土为6.0047。稳定等待不降门槛，原失败与曲线均保留。
- WebKit登录前minimal JS404与当前同URL200分开；当前精确404才一次普通GET重载，原引擎/认证/guard不变。快速连续Tab回跳工具假设失败保留，以真实逐键轨迹和明确键盘模态状态分层补验；不诊断旧404永久根因。
- 两次JSoff通用异步等待受控结束client130；原callback晚记录browser native0/正常close，与当时UNKNOWN原文件并存，不改旧时点，不冒产品或Native崩溃。专用NOJS工具不用rAF/hover等待，记录真实native截图和每步边界。
- Chrome缺SVG组件错误比较整textContent内的SVG缩进空白；仅比较原label精确文本及tag/type/href/disabled后补故障项，未归一化中文/隐藏字段、未改CSS。部分鼠标active探针原图有原生拖选高亮，保留原图并明示，包选必要清晰原图。
- Native QWeb最初环境/翻译断言失败与最终严格PASS分开；29条safe_eval lambda WARNING来自明示RO内存取值，不冒产品lambda或权限证明。普通解释器/路径及启动clean guard拒绝均未派发业务，未放宽guard。

缺真实incoming等样本、真实OS输入法/屏读/实机/正式政策仍未验。P7只证明冻结实现＋原提交合同＋已有实证复用＋本次只读/组件，不证明重新执行入库/退货等成功。

## 普通岗位7步复现

需正常受控复开，不承诺当前在线或自动化窗口可接手：

1. 普通仓库岗位正常登录，选授权门店，从原菜单进入库存。
2. 输入原物料/批次名，分别点查询文字、search图标或按Enter，执行原GET。
3. 阅读九列批次及三种数量；窄屏聚焦原表格横读，无告警不解释为可发放。
4. 点“查看本条来源”文字或箭头到原event锚点，再浏览器返回。
5. 用原来源上一/下一页，核q/page及批次不随来源分页；边界只是文字。
6. 有权办理仅Enter/Space开闭、Tab确认焦点、原取消返回；不填新证据、不点确认、不提交扫码。
7. 在窄屏/浏览器200%下读图文和焦点；独立根字号200%的技术场景另标，不与原生缩放混称。

#37保持OPEN，只新增一份P7最终结果；P1—P6旧评论/P5 PARTIAL历史不改，#36保持CLOSED。main仅必要路由文档，不合产品、不部署。P7完成后停止，不自动推广其它页面，不启完整S13/50活动会话/负载恢复/实机/正式政策/组合扫码/真实患者资金外部通道/生产。

## 已发生的独立交付核验

最终全阶段保护 **f0e59116c7170ee2c842701a6de6e23f2aef493215082f99b1ab1c52b217d1f0**、83引用/80路径现场计数澄清 **51c70abbf481ed552e68a17151a672abf91ca0b98a8bfac2339b3d2f8f1e4550**、正常OS/目标连接收尾 **c96d82a00f44878bec31dea7235e4fec53e616d10b47cb2244b79dcc41ad1e30** 均已实际完成。最后旁路/22真实退出总核 **4c481db235dcd6b7ad7da3766bb7773415de8dd517e460e13956513052cacd9b**，剩余双引擎/组件分层 **587d7528538cac7c89cabe4beb9916569a60215322c8d47d3c08efc8a31df4a1** 已签。未实现者本地12项总签已实际完成（见下），正常远端同步仍待实际完成，用户效果仍待确认。

## 实际本地总签

2026-10-25T15:10:42.517232+00:00，未实现者完成12项本地独立技术总验收，`acceptance/technical-total-local.json` SHA **204b21aaa02b40cda64d0dab8384313990ed12e7899a63c39fed74f3411dde6b**，LOCAL_TECH_ACCEPTANCE_PASS_REMOTE_PENDING。T01—11及T12本地交付/保护/包/正常收尾PASS，无本地技术缺口；T12远端ref/完整正文/唯一P7评论及旧8评论保持/37OPEN36CLOSED尚PENDING，因此此时**TECHNICALLY_COMPLETE / SYNC_PENDING**，用户亲手效果待确认。原签时间不改，最后元数据及远端实际读回后续记录，不复开服务或重测业务。
