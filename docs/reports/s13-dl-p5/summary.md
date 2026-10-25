# DL-P5：患者查询与只读费用概览

`[CODEX-FINAL] YD-S13-DL-P5 / 1.0`

技术：**PARTIAL**。同步：**SYNC_PENDING（最终远端读回后更新）**。用户亲手效果：**待确认**。

产品已限定实现；已完成的源码、Chromium、HTTP、QWeb组件和加载保护分项有真实证据。剩余缺口是成功的WebKit关键路径/双放大、浏览器长值三段组件、最终完整保护/私有包/技术总项的未实现者独立验收。测试线程触发平台用量限制后已退出，现无可用独立线程；不新建线程规避限制，不以主控自签补齐。旧owned窗口两小时正常到期后，30分钟独立准入已过期，原launcher真实拒绝重启；未放宽检查或伪造review。

本次按PARTIAL最终交付并停止，不将软件范围实现等同于P5全部验收完成。后续补验仍属P5，须恢复正常可用的独立验收能力与新鲜实际准入，不需重授业务范围或重跑已采历史全链。

## 范围与固定候选

用户完整启用的[P5计划](../../execution/S13_DL_P5_IMPLEMENTATION_PLAN.md)只覆盖 `/ydental/settlement` 的患者查询、已选患者和费用范围说明、原其他门店最小摘要入口、今日/历史未出账及待核对三段只读费用表。沿用杏陶暖白、相对字号与 Grid/Flex；费用保留单份原生 table、原生 details 和局部键盘横读。没有新增产品 JS、统计总额、自动选择或业务接口。

|对象|实际固定值及边界|
|---|---|
|分支|`codex/s13-dl-p5-settlement-lookup-r1`|
|合法起点/P4报告|`d2dfec3d7e0bde6e76005c7bba2865a22b4774ea`，开工本地和远端一致，工作树干净|
|承接P4产品|`85b62b43cf7cda889e20663662ae86484a55f032`，原最终评论6393235980保持|
|P5准备/运行适配工具/before|`9f4cfa46be547ce014436fa064ef9f789aa2ed35`；私有浏览器/HTTP/组件工具按逐次实际执行源SHA归档|
|P5产品/运行绑定|`beea6d3dc9223fa06d298984b80cb463f2fcafea`；后续仅状态/报告不作为新产品|
|core|`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，未改|
|唯一既有合成目标|`ydental_s11_synth_20261023_01` / OID2171423 / cluster7694897083368259627及原filestore|

仅四个 addon 产品文件：限定区域 XML、一个局部 SCSS、manifest 一条 CSS 资产、zh_CN 新增18词。完整用户计划落约定路径。未 reset/clean/强推、未从 main 重建产品、未合并或部署。

页头前缀2150B、首 bill 办理 details 起完整后缀22764B及共享分页定义与原字节一致。25个原 t-out、各 t-foreach、原URL表达式及顺序保持。wrapper在首办理 details 前闭合。原页头/导航/门店演示声明/feedback/全部办理能力、后端、权限、schema、原件/PDF、P1—P4及其他页面保持。18个独有英文源经真实 Odoo 提取及已加载中文逐项核验；未覆盖共享旧词条。

主控 `/root` 负责环境、固定候选、模块加载、HTTP/组件验证和报告；`p5_product` 是唯一产品写者；`p5_tester` 实现测试工具并执行真实浏览器；`p5_contract_review` 未实现产品或测试工具，独立审源、原图、请求及新物理只读保护。共享同一OS，不冒权限隔离。

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

## 实测层级与适用回归

详见[14项矩阵](acceptance-matrix.md)及[脱敏索引](evidence-index.md)。SOURCE/PURE、内存QWeb组件、正常HTTP、真实浏览器/nativeAX、独立已提交RO分别记录，不互相替代。

- Chromium156.0.8078.4真实普通角色正常登录/选店/菜单、业务号和姓名查询、明确patient-only选择、三段读取、键盘追溯、原bill展开后取消、原其他店最小摘要200。before/after五视口175项作者比较、独立290项字段/链接/内部computed重算全同；仅确切actual_utc动态值另列，未宣称归一化全文一致。
- 五视口1366×768、1440×900、768×1024、390×844、320×800；本页根宽前后均等于视口宽，320实际为320，不借用文书345/报表346旧限制。表格44rem下限只在本区局部横读，正文1rem/约1.6，标题1.125rem，不缩字号或隐藏列。
- 独立重算实际computed文字最低4.7563:1、必要控件边界3.3191:1、focus7.0613:1；结合实际原图，非全站认证。
- 16项真实HTTP为4×200/3×403/9×400：既有reader16只读正常、none17无源、既有跨店不相关患者60、非存在目标、非法患者/页码/超100字符、中文特殊字符安全回显、显式patient与q独立参数。无临时授权，后台真实拒绝，不以浏览器预拦截充当403。
- Chromium原生200%缩放使用实际native zoom2/root16/DPR2证据；独立根字号200%为root32/DPR1。原生AX及DOM语义不冒真实屏幕阅读器。无JS在同一禁JScontext经正常CSRF/密码表单认证后走原菜单/GET/候选/原生details；不复制会话，登录层已有无JS显示限制另列。
- 19项实际锁定QWeb分页组件断言直接使用共享模板/原候选导航及原controller AST提取的URL helpers，核50门槛、各首中末页和参数。三段内存显示夹具核转义、待核对空原因回退；事务READ ONLY/rollback、0 ORM业务记录创建。组件money使用明确FIXTURE格式，只验显示，不替代真实币种精度实证。
- P4定向检查保留单选确认/取消及多店草拟不改已生效结果；P1—P3只读旁路，不预览、下载PDF或重跑历史12指标/CSV/经济全链。通用撤权/revision/财务办理按未变源码和原固定证据复用，不称本轮重授/撤复或新正向财务实测。

## 加载、完整保护与限制

P5开工fresh RO baseline145业务/13技术/83实际文件与P4末态九区段全同；未实现者新physical132590独立复核。唯一必要settlement加载在beea6d3完成，即时完整pre→实际exit0/ERROR0/noNative→post。独立fresh134332全九区段与root post逐值同。

加载变化仅20条native ir_access及group69的write_date、7类技术元数据的时间、本页view1602 arch_db及report view1623的arch_prev；后者当前arch_db不变。无行增删/实际权限值变化，其他业务、配置/schema和83文件保持。正常读取审计及认证/资产技术元数据须另分类，不称全库物理零diff。

最终主控新RO/RR probe backend182076及完整末态snapshot已实际完成：145业务/13技术/83实际文件，snapshot SHA `134612cb6e0d1ccba91f3381ef92eac3d861efdd955359e75b1d82b8b07a3d07`。相对开工只新增949条accepted审计（13 login/13 login.scope/13 store.switch/726 settlement.source_view/182 settlement.invoice_view/1 other_store_summary/1 report.view），原审计无改删；native权限时间和7技术类变化沿唯一加载分类，其余业务/原文件/配置/schema保持。主控完整比较SHA `f0b4da4474c86caddb987dd8fe0de3232acfcf2563bd5b55d986fb6dc27e5db2`，这是工具作者观察，**最终未实现者独立保护尚缺**。

末owned run20261025T044950Z-9f131a95d41e于2026-10-25T06:49:51.346268UTC因bounded_runtime_expired正常退出，child0/signull/groupstopped。前两次owned也正常stop。全部已执行browser正常close，原querytop失败轮由测试者核清profile后正常收尾；末主控核无browser/node进程、无owned profile、18411/12离线、active无、目标其他连接[]。无临时授权或待恢复grant。停止态SHA `19b929b6172d5809efb802e9d1f5861f818166638170042fa2a58b7d0af0ad3f`。未操作共享主服务。65内部+2外部原件、实际完整文件、身份/作者/价源、金额库存、旧审计和未完成责任均受保护；固定旧来源1073+前批230=1303、本阶段贡献0及lot253收10/用2/余8是承接锚点，不把未来查询总数硬编码为1303。

保留首次普通路径/解释器/翻译提取错误及修正。内存QWeb组件的原生safe_eval callable WARNING保留，没有关闭检查。原search区域很长，scrollIntoView初图落在候选中段；这些原图只作候选/布局证据，补采真实query-top，不伪造历史before或声称同scrollY逐像素。

历史Native139、Firefox字形、WebKit初始化/翻译等UNKNOWN保留，不借本轮成功倒签根因。真实OS输入法、屏读、Safari/iOS和物理设备未验；WebKit引擎不是Safari实机。自动化窗口不冒用户接手或亲手效果确认。

## 私有包、复现与结束

私有0400包 `.local/dl-p5/viewing/S13-DL-P5-view-only-20261025.zip`：3,071,325B / SHA256 `421fd23fe5b0878fffd665596722a95be099674a6625db584f752e9409f38c83`。39成员=34实际PNG（32不同SHA）+5说明/派生，manifest38非self；主控全成员回读/源字节SHA/PNG全解码通过。**独立包验收未完成**，不由构造者代签。只含必要原图、README、字段映射/截图索引/限制和manifest；无秘密/session/profile/配置/raw请求、备份、程序/字体、PDF或完整DB投影，不上传Public。包和截图不能重签完整数据保护。

9次实际浏览器client：7次exit0，querytop首轮清理对象API用错exit1、WebKit首轮登录前minimal资源404后等待超时exit2。querytop-v2只补取图与草拟/另选返回，实际0/driver0/profile清理；旧v1不反签。WebKit27.2 native主进程0，未填凭据/进入结算。root后验同URL实际HTTP200、已有attachment222/39819B/同SHA cef8327be567721cdd09c79d4543715931e84ec836fa5540b5bfb08222265ad6，正常owned生命周期已重开过，但第二轮未运行，根因仍UNKNOWN。旧源/原错误/退出保留。报告准备fb2ace5只CURRENT/summary，不是新产品；首次重开因root自有报告dirty被clean guard拒，正常提交文档后启动，不修改guard。

正常复开后七步，不承诺当前在线：

1. 使用普通有结算读取权岗位正常登录，选择授权门店，从原菜单进入结算。
2. 阅读查询说明，输入姓名或业务号，用搜索按钮或原生Enter提交。
3. 从候选链接明确选择患者，核对服务显示的患者业务号及本店范围。
4. 依次阅读今日、历史未出账及待核对三段；空段不解读为无欠款或已结清。
5. 键盘展开费用追溯，阅读原编号/名称/事件；窄屏聚焦表格后左右横读。
6. 有适用分页时按原链接前后翻页；浏览器返回并选择另一个既有患者。现场真实一页，组件分页不冒实际业务多页。
7. 只读查看原其他店最小摘要再返回；可展开原办理面板后用原取消返回，不填写或提交经济动作。

P1—P4保持原技术交付和同步结论，用户亲手效果仍待确认。完整S13未完成；#37保持OPEN，#36保持CLOSED。P6、负载/备份恢复/实机/正式政策/S11组合扫码/真实患者资金及外部通道、产品合并/部署/生产未启用。P5最终交付后停止。
