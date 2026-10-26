# DL-P11 经营报表来源详情页实施结果

[CODEX-FINAL] YD-S13-DL-P11 / 1.0

技术：TECHNICALLY_COMPLETE（限定P11软件；T01—12适用项和独立验收已实际完成）

同步：SYNCED（首两ref/30完整正文/唯一回执及Issue状态已实际独立读回；最终元数据增量另正常核）
用户亲手效果：待确认  
范围：仅 `/ydental/reports/source/<metric>/<source_id>` 正常 GET 的来源详情呈现。

[用户完整计划](../../execution/S13_DL_P11_IMPLEMENTATION_PLAN.md) · [T01—12矩阵](acceptance-matrix.md) · [脱敏证据索引](evidence-index.md)。

## 候选与实现

|对象|固定值与实测边界|
|---|---|
|业务分支|`codex/s13-dl-p11-report-source-detail-r1`，从 clean P10 最终 `6d74bbe0b95fc1dbfbacd51e9d2475ee52749e36` 正常承接|
|P10继承|产品/实际运行 `8a1547a14f5647d6a49555c8ab7f9ceb658511e3`；工具 `2c18d3271b49ab1ba2d6622e1755ed9678a97997`；唯一回执 #37 / 6408631886|
|P11最终产品|`613fb33bb4fecdb23eff3c46a2d3a1de2a4c1780`；相对首产品 f235c649 仅来源分摊wrapper的局部scroll-padding修正|
|首产品/必要XML加载|`f235c649df0f58403ae3ce50a666ec2c377787a2`，仅 `ydental_reporting -u` 一次；native 0 / ERROR 0 / 无 Native 信号；最终XML字节保持，不重复-u|
|最终实际运行|`7b0601effe6ee2b3cc670087589865b7528a3f18` / `20261026T100710Z-f7eda0f7b9af`；产品同613fb33。此前16e1234/0afca56等客户端各自executed源另固定，不冒同源|
|公共工具最终发布|`1fa0ac89827bc0d4400fa53e45c7bd63e4c43d01`；仅SOURCE/PURE整合核，实际38客户端逐executed源归档，不冒发布后重跑|
|锁定核心|`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，没有修改|
|唯一目标|既有 synth `ydental_s11_synth_20261023_01` / OID2171423 / cluster7694897083368259627 / 原 filestore；无建库、复制、改名|

只改三个 addon 文件：原模板 XML、manifest 末尾单个资产、新局部 `report_source_detail.scss`。源详情独有 `data-dl-layout="report-source-detail"`，动作逐元素 `report-source-actions` opt-in；共享 nav/scope 仅详情两次原生 call 的 `report_detail_actions=True`。P10 的主页面分支、主 marker、主 SCSS、两个 P4 JS、旧 SCSS、共享 mixin、P7 SVG 与全部后端/ACL/schema/指标/CSV冻结。error 不 opt-in，不复制导航或范围业务节点。

root 为唯一产品/状态/报告写者及运行调度；`runtime_p11` 实现运行/保护工具，`testing_p11` 实现定向浏览器、合同和包工具，`acceptance_p11` 未实现产品或相应工具，独立核源码、当前准入、原件、完整保护和交付。同 OS，不冒权限或进程隔离。

## 控件、SVG与空间责任

共 8 个链接、2 个 summary 定义，无新增提交按钮。循环渲染数与定义数分开；本次实际单卡/两分摊为 9 个链接、2 个 summary。

|原控件|P11动作/图标|保持的合同|
|---|---|---|
|3条页内导航|quiet，无图|原中文、href、顺序；仅 source 局部调用启用|
|首尾2条返回|secondary + 原 chevron_left|两处完全同一原 `return_url`，生效过滤、原页码保持|
|循环分摊账单链接1定义|quiet，无图|原单据号和 allocation URL；4列/顺序/金额/当前应收/原单元内衬不变|
|业务页面1链接|quiet + 原 arrow_right|原 business URL 和中文标签，不自动切店或办理|
|原生单据1链接|quiet，无第二个拥挤图标|原 native URL 和权限重检标签|
|scope/技术追溯2个summary|disclosure，无 SVG 箭头|原生 marker、details、完整范围/时区/模型ID/pre文本|

动作直接复用 `o-ydental-actions`，未重新定义动作颜色。表面/分隔/提醒复用 P7 的低饱和暖色，未改变全局主题。SVG 仍为 Lucide0.468.0，固定 commit `f12b0de177fbc2a6795e99be065887e72b237123`；原几何、SHA、ISC/Feather MIT 字节不变。装饰 `aria-hidden=true`、`focusable=false`，相对 em，无独立 Tab、CDN、字体或运行时。

|布局关系|唯一owner|root16参考值|
|---|---|---|
|导航、业务/native链接组内|各组容器 gap|.75rem / 12px|
|顶部返回→标题；标题→只读说明|标题上/下 margin|1rem / .75rem|
|说明→scope；scope→首卡；相邻卡；末尾返回|后模块 leading margin，前模块 bottom0|1.5rem / 24px|
|卡标题→患者；患者→金额状态→业务日|患者/数量/日期各自 leading margin，卡 reset 无 parent gap|.5rem / .75rem / .75rem|
|业务日→facts→分摊→可选跨店提醒→来源链接→trace|存在的后组 leading margin，条件缺席无占位|1rem / 16px|
|dt/dd对应、相邻事实行|原 dl grid column/row gap，双方 margin0|.5rem / .75rem；列 minmax(0,…)防长值撑宽|
|scope段落/展开summary→首段；trace正文|正文 leading margin，关闭无正文洞|.75rem / 12px|
|容器/卡片内衬|main/card各自原容器 padding，无新嵌套卡|桌1.5rem / ≤45rem 1rem|
|分摊表周边|wrapper margin和border，table自身外margin0|1rem；原760px列策略/单元10px保持|
|分摊链接焦点缓冲|链接外侧各.25rem、末行底.25rem，max-inline扣相同两侧值|保护root32共享12px外圈，不改cell/overflow|
|分摊区域滚动落点|wrapper唯一scroll-padding-inline|.375rem / root16为6px、root32为12px；只保共享outline+offset净空，不改表格实际内衬|

仅业务/native两个动作之间原装饰“·”由组 gap 替代；全 XML 比较只在该唯一原位置恢复，原 quantity、scope、facts 中的点不变。原生翻译术语86→85次、独有74项保持；只分类这一邻接两原标签的独立装饰项，其余全文/顺序不变，没有全局文本归一化。

## 原值、授权与页面隔离

完整 XML 白名单还原后 C14N 严格同 P10；manifest 恰新增单资产，其它 addon 原字节冻结。实际 loaded 五模板 EN/CN 和四个明确内存 QWeb 分支逐项核原字段、条件、所有 href 和完整 trace，不能替代真实身份/授权。两处 return、原 source/business/native/allocation URL 均沿服务器原值，控制器仍 `_query(..., all_rows=True)` 后重新查找授权来源，没有新增参数或业务快捷操作。

真实原收款来源只读：实收300；原账单270/分摊270/当前应收0，与原账单200/分摊30/当前应收170；这是既有两分摊，不重做收款。患者/金额币种精度/业务时间/状态/facts/完整 trace 按原投影对照。动态 query_at 只分类 scope 第三段唯一原生字段，保留前后原值；不删除其它时间或排序。

实际Chromium156.0.8078.4与WebKit27.2 WPE，driver1.64.0-beta-1791568591000。SOURCE/loaded/真实浏览器、内存组件、故障组件分列。多卡和长中文/连续哈希/60行追溯只用有【P11夹具】标识的 loaded QWeb 与原产品 CSS，未创建持久业务。四分支双engine共52实际投影、每engine26批完整文本首末Range与342次焦点观察已独立逐值核验；五view、长值native200/root32、文字间距和缺CSS/SVG故障均注明组件。首末字符以真实普通window/local滚动补读，不改CSS/文本/可见阈值；不能把组件冒真实多来源、真实授权或真实多页。

当前真实普通uid5/16的source8读200，none17、无源、非法店过滤真403，无临时提权。既有followup55/store2来源读200且默认跨店提醒可见；原business GET实际200，只显示当前StoreA范围、与该店2来源交集为空，既有控制器行为，不写成403、不自动切店。P10主页面/error双engine原computed/fields/status严格同，error整个main HTML exact，主页面只分类唯一query_at文本节点后全C14N same。三有限旁路原字段/样式保持，结算仅原pay.actual_utc默认now单字段保两原值，不办理。

## 保护、失败与限制

开工未实现者新 physical513239 RO/RR/rollbackclosed，完整145业务/13技术/九区与主控及P10末态逐值同；83引用/80实际路径/80不同SHA逐bytes/size/SHA，三处共享引用保。两个 before 窗口仅新增95正常 accepted 认证/读取审计，其它144业务、13技术、文件/配置/schema同。必要加载即时完整 pre→实际0→post业务和文件保持，5原生技术类、3arch及main旧EN backup与4直接依赖精确归类。最终未实现者另新physical **588513** READ ONLY/REPEATABLE READ、rollback/connection closed，完整145业务/13技术/九区与root最终逐值同；83引用/80实际路径/80不同SHA及三共享逐个真实打开完整bytes/size/SHA保持。全阶段独立 **5ad9a5dfd827df8e75817842fcd38f75fe2ccfbf672ca06cecfddef52ad84b16**。旧18406审计逐行保留，最终18818，新412全为正常认证/读取；其它144业务/配置/schema保持，技术只唯一-u已分类5表，4依赖同。web/assets派生附件65→65仅旧15832替换为15833 CSS缓存，其余64元数据/实际文件SHA同，单列于83业务引用/80原件之外；不称全库物理零变化。原金额库存、身份作者价源、已提交原件与未完成责任保持；新增经济/库存/文书原件PDF/打印/签署/模板发布/治疗扫码/CSV 0。

实际38客户端=32Node0/6Node2，全部38 native0/context正常close；277原PNG路径/196不同SHA、377执行源归档全部独核。6个Node2：before Chrome双层main选择器、首glyph Range未存失败几何、doctor JS undefined/持久JSON省字段比较、长值组件390焦点clip、该原序列/settled两次定向focus诊断。原生内存组件首缺输出目录native1、单装饰术语PURE断言及typed query_at/path工具错误也保首因与修正；有效子层不反签整client，无未知业务提交或产品原生崩溃。

P11-A01在分摊组件横读→缩窄后实证：native Tab等待两帧+250ms仍部分可见；原nearest落点也裁6px焦点环。最终只增加本source wrapper的.375rem滚动净空，正常滚动后完整环实测保持。原生Tab仍不保证自动完整显现，保留该限制：同一真实source8在768先ArrowRight至92、缩窄390保留位置后Tab，Chrome3次/WebKit2次trusted ArrowLeft可保原链接active与全文/外圈可见，rootX0/href不变；恢复段无helper或scrollLeft赋值。按计划内“局部横读与焦点可达”验，不冒自动滚动或新增JS；未实现者限定闭合收据 **b1344f9a33b7f90d8b4805b5460bd4ceff6a6c23be489b341a70e1510c00322e**，原OPEN/confirmed/各失败均保原字节。

此前主控实际capacity错误时第三after尚未启动，独立interim保护和收尾、current-partial收据保持；本次用户“继续”后同入口/原团队正常恢复，重新获取现时准入，没有换模型或恢复旧时间。旧Node2、原glyph首次未存失败Range与后续新诊断、doctor的undefined/JSON省字段比较错误均保留，后者原两JSON独核exact不重读业务。

本 source 本轮Chromium390/320前后根宽各393；WebKit390前后390、320前后377，其余三个视口各same。未新增root溢出，不宣称修复外壳根溢出。P10主页面320旧346/332、WK无JS CSV wireBOM/native文件未观测、P9旧wrapper/Node UNKNOWN、P5历史PARTIAL与此前所有旧失败/原件保持，不重跑历史全链。WebKit不等同Safari/iOS，AX不等同屏读，用户效果、实机和全站认证均未代签。

## 私有效果包与正常收尾

最终0400只读包 `.local/dl-p11/viewing/S13-DL-P11-view-only-20261026-r1.zip`：**9,328,107B / SHA256 7e1c32e45aff99eb34613abf918378eb57401a9a869f1161dd183c7513c58773**。87成员/83未编辑原PNG（83不同SHA）/6有限测量；manifest85数据项/SHA表86非self项及整体ZIP均独立全核。每图保actual capture candidate/uid5/viewport/rootFont/DPR/scroll/场景，真实同一source8前后与fixture/fault、native Tab partial/普通ArrowLeft恢复分层。构造时manifest PENDING保原字节，最终外部独立签 **e399ad9387eb0d1824dafb02d4d803a62263abaffc827f3a713ac1ac536f567c** / 隐私与视觉 **3b13e2845ecede3bf26f1970743ec61d2072da10b6f8bf3e5ccd0fb2d2296892**，不循环回写未来签名。无凭据/Cookie/profile/原请求/配置/完整DB投影/原件PDF/CSV/字体/程序，不Public上传；旧包原字节保持。

5个owned窗口全部正常foreground/child0/groupstop；最终run `20261026T100710Z-f7eda0f7b9af` 于 **2026-10-26T10:35:51.660196Z** 正常stop。38原生浏览器正常退出，全部owned profiles/known PID/marker/18411和12空，独立另新physical588563其它target连接[]。未改/未停共享主服务，无临时授权需撤回。独立收尾 **eb2c025c64b2cbff0cb9170c9f7e635ee351da28df87c2fa397e72d23ae1464c**；之后仅离线工具/报告/包与正常同步，不为报告复开DB/app/browser。

## 普通岗位7步复现

1. 在正常新有效运行窗口，用原有报表来源读取权的普通岗位登录并选授权门店；不要恢复旧scope/STOP或把localhost当远端入口。
2. 原菜单进入经营报表，选“实收（线下确认，非收入）”、2026-10-01—2026-10-26、授权StoreA，明确查询；只读查看生效范围。
3. 从既有PB0001/2026/00003（source8，实收300）的原“查看来源与分摊”进入详情，核暖色导航、顶部返回、原标题和只读说明。
4. 阅读已生效范围与查询时点，原生展开/收起时区；核来源卡的患者、金额/数量、状态、业务日和facts原值。
5. 有原分摊则逐项核账单及四列值；跨店来源默认显示操作权限提醒，保持当前工作店，不办理来源业务。
6. 用键盘展开技术追溯并阅读完整模型、ID、原文本；窄屏先聚焦分摊区域用左右键横读，缩窄后若首账单部分可见，保持链接焦点按ArrowLeft至全文/外圈可见；核两种200%和首尾焦点。
7. 分别使用顶部/底部原返回，核同一生效过滤和页码；不生成、打印、签署、发布、收退款、库存、治疗或扫码。

## 同步与停止

未实现者本地最终总签 **53c9d259cac5f685338761c1e1cb7195dabccde247bde60f385e1f7e3e145330** 已实际PASS（LOCAL_TECH_ACCEPTANCE_PASS_REMOTE_PENDING，66817固定审查候选）；T01—11及T12本地适用项成立，原REMOTE_PENDING时点保持。首报告 **b328c5f5b2cb7607a976b699fadeeba059061c47** / main仅两文档路由 **8fb40bd3e2ee82197007f460ecf7d2bd11efede3** 正常push0；未实现者直接正常GitHub插件读取两ref、30完整UTF8/bytes/SHA/Gitblob及[#37唯一P11回执6414490185](https://github.com/Yredxin/YDental/issues/37#issuecomment-6414490185)全文，旧12 id/body、37OPEN/36CLOSED及title/body均exact。首远端独立总签 **87db0b06012510e66fcefbcaa4691e934c837b24e2d5393020abbcd96f23122e** 已实际PASS，T01—12适用项成立，限定P11 **TECHNICALLY_COMPLETE / SYNCED**。最终仅#37一份P11回执，保持OPEN；#36 CLOSED，旧12评论不改。main仅必要文档路由，不合产品、不部署。P11交付已停止；P12/其它页面、完整S13/50活动负载/备份恢复/实机/正式政策/S11组合扫码/真实患者资金和外部通道/生产均未启用。用户亲手效果继续待确认。

本次最后提交只记录已发生的SYNCED/停止元数据，最后4业务文档+2main路由与同一P11评论增量另正常读回；报告自身SHA不循环，不复开软件/DB/包。旧评论created_at/updated_at在API均为null，真实时间NOT_OBSERVED；只声明旧id/body保持，澄清收据 `e193ff5e5cb8ec52a5b1ea9792b947bac119e2dd00bc0112d6494a91685af5bb` 保留首原件。P11交付已停止，用户亲手效果待确认。
