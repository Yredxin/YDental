# DL-P5：患者查询与只读费用概览（定向续办）

`[CODEX-FINAL] YD-S13-DL-P5 / 1.0`

技术：**TECHNICALLY_COMPLETE（限定P5软件，未实现者本地技术总签已实际完成）**。同步：**本轮SYNC_PENDING**；13bdf549原PARTIAL交付的SYNCED保持。用户亲手效果：**待确认**。

本次只补原P5的第二引擎、非空长值浏览器组件、全阶段独立保护及新包/技术总验收，没有重新设计产品。原PARTIAL历史见[13bdf549固定报告](https://github.com/Yredxin/YDental/blob/13bdf549dcb43cfe4d8b44b72de6eba55115cd31/docs/reports/s13-dl-p5/summary.md)，原失败/UNKNOWN及旧包不覆盖。

## 完成范围、候选与真实分工

- 产品仍为 **beea6d3dc9223fa06d298984b80cb463f2fcafea**，四产品文件实际SHA与原独立SOURCE回执逐值同；原页头前缀2150B、首bill起完整后缀22764B、共享分页、25个t-out/各foreach及URL helpers保持。没有新JS、统计、产品修复、后端/权限/schema或全局样式改动。
- 原准备/运行适配工具 **9f4cfa46be547ce014436fa064ef9f789aa2ed35** 不变；续办真实运行绑定 **bad6f7f071daac997a2af53f7958fcc7429a18d6**，其相对13bdf549仅CURRENT文档。私有测试工具实际新版本按逐次executed源/SHA/退出归档，不能冒同一旧源全通过。
- 既有分支codex/s13-dl-p5-settlement-lookup-r1正常续行；原P4/P1—P3结论保持。core **f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb**、同一原合成目标/OID2171423/cluster7694897083368259627及原filestore未改，没有reset/clean/强推、重建产品、新建/复制/改名库或重复settlement-u。
- root统一环境、真实准入绑定、停机、主控RO、报告和同步；原p5_product的产品保持，p5_resume_tester只实现私有补验工具并执行，p5_resume_acceptance未实现产品或对应测试工具，独立审源码/原图/请求/进程/新physicalRO/包/总项。共享同OS，不冒权限隔离。
- 当前可用额度证据来自用户提供的CLI /status，主控没有冒称API独立取得；时区未注明不推测。正常新线程已实际执行，并不表示资源无限。原接口UNKNOWN与旧用量失败仅历史，新scope/准入不放宽。

## 四组缺口的实际关闭依据

|缺口|实际补验与独立结果|边界|
|---|---|---|
|A 第二引擎|WebKit27.2正常CSRF登录/uid14/store1/菜单、业务号和姓名查询、明确patient655/P00000655及范围、browserBack、trace、窄屏键盘右/左端、五视口、native200(root16/DPR2)及root200(root32/DPR1)；18检查、child0/native4091782 exit0/signull，独立审31PNG/源/请求并实看代表原图通过|真实引擎，不改UA/认证/安全，不冒Safari/iOS。旧preauth404仍UNKNOWN|
|B 三段长值|实际产品QWeb三段内存片段进入Chrome156浏览器，五视口＋native683×384/root16/DPR2＋独立root32/DPR1，共176检查；105项文本/追溯、210个首末字符正尺寸Range坐标、42次键盘横滚两端；actor/患者号/项目/原因/trace全文与末端实读、24PNG独立核|明确COMPONENT/BROWSER_FIXTURE；无修饰CSS、0ORM创建、隐藏live字段只在内存比较布尔不出值。fixture money只验显示，不冒真实币种精度|
|C 全阶段独立保护|新physical215272/RO-RR/实际0/rollback闭，完整145业务/13技术/现场83文件bytes/size/SHA；九段exact主控最终a19f22...。从P5开工、原加载后、原PARTIAL末态、续办前态到最终的全部差异独立重算|没有补造原PARTIAL旧时点独立连接；原949审计保留，本轮320正常accepted读取审计单列|
|D 新包与总项|新包01eb5b6f.../2263458B/35成员/30原PNG，13旧必要图＋17新图；独立全manifest/bytes/sourceSHA/PNG/privacy通过，旧421fd...包不变；本地技术总签已实际完成，远端同步单列|截图数量非门槛，实际scrollY分别存，非逐像素；同步及用户效果独立列|

[14项矩阵](acceptance-matrix.md)逐项标明原候选/范围、本次影响和复用/新增依据；[证据索引](evidence-index.md)只含脱敏指针。11类原独立SOURCE/字段/HTTP/contrast/Chromium普通路径/放大/无JS/QWeb/唯一加载等由新未实现者逐件SHA与未变代码核后复用，不重跑历史全链、不外推到新夹具或旧失败客户端。

## 查询、身份、字段与分页映射

|对象|保留的来源与语义|
|---|---|
|q|原GET搜索框，maxlength100；只查本店授权候选，不决定下方费用或已选身份；输入/失焦/焦点移动不预查询|
|搜索提交|原form只提交q，无patient_id hidden；提交后回到未选患者的门店费用范围|
|明确选择|原候选链接只带patient_id，不保留q/search_page/费用页码；以服务返回的规范patient及其业务号显示选中上下文|
|候选|原关系查询，按patient/id顺序、每页30及第31条has_more探测；没有总人数，不自动选第一项|
|候选分页|原patient_search_url保留q/search_page/patient_id语义，首末边界使用文字，无假链接|
|费用范围|未选为当前授权门店；选中为本店的规范患者及其已合并来源。无匹配候选不代表无费用或结清|
|today/history|原已确认、未出账费用；当前门店当地业务日等于/不等于今日分别分段，history不擅自解释成仅此前日期|
|项目/患者号|fee.event.catalog.name / fee.patient.ydental_number，原顺序与值保持|
|确认金额|原money(fee.amount, fee.currency)，原币种/精度/正负号；未出账非应收，确认金额非实收，无跨币种合计或当前页求和|
|业务日|原event.ydental_business_date，不替换为浏览器日期或录入时间|
|费用追溯|fee.id/name及event.id，原t-out转义和值保持|
|pending|原pending event的项目、患者号、业务日、实际actor.name、pending_reason或“待核对”；默认显示“待核对，禁止出账”|
|pending追溯|原event.id/name，原值/转义/只读含义保持|
|三段费用分页|原id desc、每页50、page_counts/pages/page_url；当前patient_id、q/search_page及其他分类页码保持；共享模板逻辑不改|
|其他店入口|原条件、规范patient.id和原地址；只读最小摘要，不授予他店办理权|

现场普通结算 UID14/store1：候选27条，未选时 today0/history27/pending0；选中既有患者655后history1。真实数据均为一页。三段非空、长值及多页边界的补验使用明确组件夹具，不能称真实患者非空或真实多页。

## 准入、全阶段保护与正常收尾

原主控续办前态b9526abe...与13bdf549末态134612cb...的九段完全同，原949审计不清零。新未实现者physical212237实际RO/RR核当前状态/角色/原文件及五时点分类，形成新review4d6c676c...；现有binder按当前probe/runtime/checkpoint精确SHA绑定。旧admission原字节归档，旧时间/STOP/guard不改，原scope到2026-10-25T16:30:53.891107UTC不延长。工具及独立审均READY后才正常start。

最终主控snapshot SHA **a19f22c007687de5a3ec932e75adda5dec592170bd2489fca3c3d6bde1df52f1**；未实现者新physical215272 snapshot SHA **067ef204c338731503971f9cd0e1c036a4f755bc4b44e310d0d35b7465d11162**，九区段逐值同。独立保护回执SHA **3cf43ee11b48457800cab9a7b2a7ac01521839f6babc8d1dfe8f24c247ebe9f6**。

全阶段仅新增1269条正常accepted读审计，包含原949＋续办320。续办为3login/3login.scope/3store.switch/248source_view/63invoice_view，其他业务/技术元数据无续办变化；原加载20 ir_access/group69的write_date及7技术类既有变化另分类，权限值不变。全部旧audit无改删，65内部＋2外部原件、现场83保护文件、金额库存/身份作者价源/未完责任/配置/schema保持。新原件、PDF、打印、签署、模板发布、出账/收退款/免单/日结、治疗与经济库存动作均0。固定1303与lot253收10/用2/余8是保护锚点，不硬编码未来查询。

owned run20261025T095230Z-5d77f24f9b3a于 **2026-10-25T09:58:48.758607UTC** 正常stop_requested，child4090021 exit0/signull/groupstopped/noNative。全部browser及profile已正常关闭删除，独立OS核known owned PID无/18411与12离线/active无，主控新RO核其他目标连接[]，无临时grant。未动共享服务，不承诺当前在线，不为报告复开。

## 原失败、层级与限制

原WebKit-v1 preauth404/client2/native0、同URL后来200/已有39819B技术文件并存保持UNKNOWN；此次正常登录成功不说明旧根因已修。续办v2已成功认证/选店/菜单，但Node的函数表达式未调用导致提取TypeError/client2/native0；只修私有IIFE调用，v3实际完整通过，原源/退出均保留。原querytop清理API失败exit1及后最小v2通过、原路径/解释器/翻译提取/取景错误亦保持。

真实today/pending为空、history27、候选27/一页（所选655历史1）；组件非空/多页不冒真实数据。原生AX不等屏读、键盘协议不等真实OS输入法、WebKit不等Safari/iOS/实机。历史Native139/Firefox字形/旧WebKit等UNKNOWN不追溯倒签，正式政策/负载/备份恢复/实机/完整S13仍未验。

## 新旧私有包与7步复现

新0400包 `.local/dl-p5/viewing/S13-DL-P5-view-only-20261025-continuation-r1.zip`：**2,263,458B / SHA256 01eb5b6fceb68a259b04b54f32c5105f64618a5ac8e23e17d880974921fe569d**。35成员/manifest34非self/30原PNG；实际候选/日期/角色/视口/scrollY/fixture与旧新来源明确。全成员/源bytes/SHA/PNG/privacy独立回执SHA **97c08a78dc27b7835bcc8bf0ce05b8567fe4b1bb28d0d82d59e5715bd6531cea**。无凭据、会话、配置、原请求、数据库投影、程序、字体、备份或PDF；只本机和授权会话查看，不上传Public。

旧PARTIAL包 `.local/dl-p5/viewing/S13-DL-P5-view-only-20261025.zip` 的3,071,325B及SHA **421fd23fe5b0878fffd665596722a95be099674a6625db584f752e9409f38c83** 原字节保留。包核/图不能替独立数据库保护，新包外独立回执绑定A/B/C，不覆盖旧包。

正常复开后七步，不承诺当前在线：

1. 使用普通有结算读取权岗位正常登录，选择授权门店，从原菜单进入结算。
2. 阅读查询说明，输入姓名或业务号，用搜索按钮或原生Enter提交。
3. 从候选链接明确选择患者，核对服务显示的患者业务号及本店范围。
4. 依次阅读今日、历史未出账及待核对三段；空段不解读为无欠款或已结清。
5. 键盘展开费用追溯，阅读原编号/名称/事件；窄屏聚焦表格后左右横读。
6. 有适用分页时按原链接前后翻页；浏览器返回并选择另一个既有患者。现场真实一页，组件分页不冒实际业务多页。
7. 只读查看原其他店最小摘要再返回；可展开原办理面板后用原取消返回，不填写或提交经济动作。

原PARTIAL历史与当前续办状态分列，最终只在原评论6395137158后追加带实际时间及新锚点的结果，保留整个原PARTIAL正文；不新发第二份P5回执、不改P1—P4评论，#37 OPEN/#36 CLOSED。main仅必要路由；P5完成后停止，P6/完整S13/合并/部署/生产继续未启用。


未实现者本地技术总验收已实际完成：`acceptance/continuation/technical-total-local.json`，SHA **c747a2c29c3af0dce09166e298401e4234cbfd17df3c1388476eb5b6c2314f3d**，状态LOCAL_TECH_ACCEPTANCE_PASS_REMOTE_PENDING；14项适用软件/全阶段保护/新包/正常收尾已PASS，无剩余软件缺口。此签名不预签后续远端同步，用户亲手效果仍待确认。报告内容/60项实际SHA/12client原源及退出已被未实现者全文核。本轮最终report HEAD/main路由与同一评论续办追加将在真实同步读回后记录，不重启服务或重采数据库。
