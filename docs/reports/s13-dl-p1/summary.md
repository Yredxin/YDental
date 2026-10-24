# DL-P1：文书查询与选择区最终结果

`[CODEX-FINAL] YD-S13-DL-P1 / 1.0`

- 技术：TECHNICALLY_COMPLETE（限定P1软件范围）。
- 同步：SYNC_PENDING；尚未将本阶段结果写入Issue，不冒已同步。
- 用户亲手效果：待确认；自动化浏览器不是已接手窗口。
- 仅文书查询与选择区。DL-P2—P6 NOT_AUTHORIZED；完整S13未完成，#37保持OPEN，#36保持CLOSED。不合产品main、不部署。

## 候选、来源和实际修改

分支`codex/s13-dl-p1-documents-query-r1`，正常承接`06c7a4639a107e70c3db6352f8f929db80e6f94a`。准备/公共运行工具`31ef5d7bb8e181bdd044c9bd6d77db20f1dbd5ef`的addon仍等于06c7；首版`63ae208b09e1c582ed2493f0cba78cc7a94731fb`有独立发现的极长项缺陷。**最终产品/执行`8dea2647760f6d6738abfc9db132cfa9d7feaee3`**只向前修局部浮层；执行时报告checkpoint`2dd06effea75d7e96039264f23ce77af59f12d8f`与产品仅3份报告差异，现有delta/clean-tree检查正常通过。后续只有报告/路由元事实。core锁定`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。最终完整报告HEAD见本阶段新#37回执及实际ref读回，不自嵌自身hash。

用户ZIP原地保留，9个payload字节/SHA均同manifest，完整读取全部MD与参考HTML源码。ZIP SHA `c01b0e06736a59016aea4e0beb37bee19c73190bc5ba24fb013019f876fbdfbe`；参考HTML82,200字节/SHA `85ccfba06dfdda594606619f32bc4074bbc671bec9910709e6fa539cdeb5cab6`。不声称在此重新视觉运行GPT包先前受限的file页面。原02/03逐字落入[设计规范](../../design/YDENTAL_DESIGN_LANGUAGE_V1.md)/[完整计划](../../execution/S13_DL_P1_IMPLEMENTATION_PLAN.md)，U/R/W编号承接包中05。main路由/AGENTS、活动S13-UX状态/报告与#23/#37现行正文/有效增量已读。没有reset/clean/强推、覆盖未知工作或从main重建产品；原ZIP仅确切文件名本地排除，不忽略整个tmp。

|产品文件|实际变化|
|---|---|
|`ydental_print/views/ydental_document_templates.xml`|GET q、preview两处select/按钮的局部wrapper、label/帮助和状态；2表单保持独立|
|`ydental_print/static/src/documents_query/documents_query.js`|两处共用单选增强、焦点/键盘/状态；空间不足的可读浮层fallback|
|同目录`documents_query.scss`|仅显式scope/portal的A色、相对尺寸和Grid|
|`ydental_print/__manifest__.py`|注册上述2个前台资源|
|`ydental_print/i18n/zh_CN.po`|5条英文源字符串的中文翻译|

页头/导航、已保存列表/分页/追溯、generate/previous_id、模板管理/发布、批量导出、PDF模板/布局/纸型、其他岗位、业务model/controller/ACL/schema/金额/状态机均未改。改区外XML前缀952字节、后缀7372字节逐字相同。内容模板7/布局7和所有旧原件保持；**P1新增原件/PDF/打印请求/经济或库存业务为0**。

A色surface `#fffbf6`、paper `#fffefa`、正文`#382f28`、说明`#716359`、accent `#94513a`/hover `#7e432f`、必要边界`#9c8776`、focus `#6c513f`，装饰线`#e5cdbd`，沿规范现有值。字体为系统/CJK回退栈，基准1rem、最小控件2.75em、Grid自然换行，无全局body/html重置或主题设置平台。真实14组computed rgba经未实现者独立复算，最小正文5.613、必要边界3.319、焦点7.061；不是全站WCAG认证。

复用锁定core Interaction/normalize/reposition/addLoadingEffect。原SelectMenu/Dropdown的menu及Tab/active-confirm语义不直接符合本计划，故最小局部适配。原native select始终是唯一提交字段；成功增强后才隐藏，触发器无name。csrf/revision/operation/q/page、`kind:id:version`、真实template_id/原空值不改。active与confirmed分离，Enter/Space确认、Esc取消、Tab/ShiftTab确认并自然离开，外点不吞目标；单选不发请求，只有明确有效submit才busy。JS禁用时原生表单仍能正常搜索/选择/预览。

最终fallback先保留core定位；当实际visualViewport空间不足3个普通控件行/当前项高度或越界时，浮层在视口边距内覆盖锚点并保留局部滚动。超高选项从首行开始，全文可滚读，不截字/缩字号。JS最终SHA `fd5e89476977d26484fbe9f6d07b88297a42a0183ff9144e772e4f543a27952d`。

## 实证、效果与影响面

[独立逐项矩阵](acceptance-matrix.md)覆盖P1-T01—16和F1—4；[脱敏索引](evidence-index.md)保留实际命令结果、工具源SHA/归档、真实退出与私有原件定位。不能用辅助断言数代表业务用例完成。

|层级/对象|实际结果和边界|
|---|---|
|SOURCE/PURE|AST/XML/PO、锁定core transpiler/libsass/Node语法及7项运行边界PURE通过；无后端业务变更|
|HTTP|17类正常表单请求：有权搜索/显式preview200；源版本/格式409；已有错kind模板/无财务/无源/跨店403；真切授权店2使旧revision409，回店新revision200；旧95实际下载SHA核对。此后仅JS定位变化，后端断言SOURCE承接，不重复授权负例|
|真实撤权/提交|普通9原form200→正常manager5暂撤medical none，独立PG确认→同旧formpreview与95download各403→原write精确恢复且独立PG核→同form200。其他身份/公司/组/能力/成员/权限不变|
|Chromium|真实156.0.8078.4，最终8dea正常菜单/搜索/两select/取消/预览/键盘/AX/required/busy，pageerrors0；5视口、native zoom2及独立32px根字号、极长source/template/error和局部全文滚读。320 fallback高776px、根字号场景720px，399/399与261/261字符实际Range覆盖并逐图亲看|
|WebKit|真实27.2/revision2370，同最终候选普通9正常认证/选店/菜单/搜索/选择/取消/单独preview、1366/390/320、真实中文iframe/作者/待签含义、原生zoom2/根字号分列；应用及补图客户端和可观察主进程均0/signull、pageerrors0|
|缩放/模拟|Chrome tabs原生zoom、WebKit原生pageZoom实际CSS1366→683/root16/visualScale1/DPR1→2并复位；根字号32px/DPR1另列。可信CDP组合输入与非可信组合事件夹具分开；触摸是浏览器模拟；物理OS IME/屏幕阅读器/Safari/iOS/设备NOT_RUN|
|前后/旁路|15对真实同条件before/final-after，after另2个实际可见iframe裁剪。所有同页命名未改区域computed及后代控件逐字段同；结算/仓库/原生加工PNG前后同SHA，报表条件/USD1300/3笔/样式同，仅真实查询时点更新|

五视口为1366×768、1440×900、768×1024、390×844、320×800，100%基础缩放。旧320px整页scroll345/client320保持，改区不新增溢出；不把旧列表/整页改造成移动端算本阶段成果。长字段只用明示组件响应文本夹具、业务value不变、不写库凑样本；普通流程均来自真实授权页面。截图、真实浏览器、原生AX、组件模拟与独立物理RO分别分层，不冒用户亲手验收。

首版63ae仅`ydental_print -u`，即时完整pre db39…成功后实际执行0/ERROR0/无Native信号，post cdb3…逐项独立核。最终8dea只改JS，manifest/视图/PO/SCSS原样；未为凑数重复-u。完整即时pre d608…→正常服务实际新bundle加载→最终post ece0…；实际取回`/web/assets/2a18c63/web.assets_frontend_lazy.min.js`，1,969,552字节/SHA `7c94415b67645abf9157e2ec7c941be131b846990a543b329ee67cefcbc21771`，新模块/fallback/visualViewport实际内容与动态效果均核验。没有重派已结束S11/S12/S13-UX全链或经济链。

## 原件、资金库存和责任保全

唯一目标`ydental_s11_synth_20261023_01 / OID2171423 / cluster7694897083368259627`和同一filestore，无新增/复制/改名库。受限DB角色五项集群高权均false。当前完整65内部+2外部原件、83实际文件，不只旧17/20样张。

最终未实现者真实新libpq backend4077767，RO/RR、rollback idle/closed，145业务/13技术及全部83文件逐值同root最终后态；与最初基线/63pre/assetpre完整分类一致。独立回执`0b5d0d276abddfb740d6347529019b134d61e5e537cd26a42ce61d60cc99465c`。所有旧审计行、文件字节/SHA、关联/作者/价格/金额/库存/责任、schema约束索引/config保持。

全程正常差异明确列出：273条新登录/选店/查阅/预览/下载/拒绝/授权审计；25条ir.access、group69、grant47仅write_date；4个mutex各+2来自两次正常撤/复权限的既有_grant→_all_locks并发fence，非队列/患者/库存办理。原生元数据8表仅769个write_date单元及1个页面view arch_db/arch_prev，未增删行、未改PDF/paperformat语义。全程跨候选offline比较独立验证合法祖先/限定产品差异，与同候选同freeze的升级比较区分。

旧AR1073=63+1010不凑账；前批合法新230继续合1303，本阶段新增贡献0。原58/59/60/61不同历史、76/77/pay8分摊270+30、79确认600/目录620、93冻结draft与214当前sent、lot253收10用2余8及全部旧/新增未完责任（含455/508/880/215/281/282）均保持。没有重付款/退款/治疗/出入库、假完成责任或覆盖旧PDF。

## 私有包、团队与服务

私有只读包：[S13-DL-P1-view-only-20261024.zip](../../../.local/dl-p1/viewing/S13-DL-P1-view-only-20261024.zip)，**11,672,801字节，0400**，SHA `b125f3440e43e2dc5fa5526b898fa90ec1b2266ce3bc61f43c834d13e6864ff8`。82成员=78实际PNG+README/派生截图CSV/83文件保护摘要/manifest；0新PDF。包含同条件前后、两引擎实际选图、降级/空状态，以及标明已修的63长项失败和未通过的Firefox字体观察；不把重复同SHA图片计新业务。所有成员已实际读回，未实现者独立包核验回执`93821599c06abadc384fe0321565cfe8fb6ac828b10d1c40805ecc415e9aab40`。无凭据/Cookie/session/profile/连接配置/原始请求日志/备份/独立字体/可执行代码，未上传Public。

主控/root运行/集成/报告与普通HTTP；documents唯一产品写者；tester实现浏览器工具/验证；acceptance未实现产品或测试工具、独立审源码/原始进程/实际图片/公式并新物理RO。共享OS不冒隔离，工具作者不签独立通过。

末owned run`20261024T113302Z-ca515f78a9f8`已于12:01:36UTC正常停止，Odoo child3278994=0/signull、owned process group stopped/no active。所有浏览器客户端退出，临时medical授权精确恢复，无新测试身份或未释放业务租约。原P1 scope18:32:42UTC未改，不表示永久在线。复开必须正常核当前目标/filestore/权限/无冲突owned进程、fresh只读probe/独立准入/clean候选及有效scope；过期创建正常新查看scope，不篡改旧期/STOP，不复制会话。127.0.0.1仅服务器本机，不承诺用户其他电脑直达或可见窗口已接手。

## 失败与保留限制

- 63ae长项浮层14/26px的真实FAIL已由8dea普通局部修复，原工具0不能代替原视觉通过。旧full_page弹层关闭、Chrome原nativezoom白图、WebKit错误clip半图均保留，最终以同候选viewport/原生截图补证；没有重绘图片或注入产品样式凑效果。
- Firefox157.0实际键盘/请求/原生zoom可用，但本机私有字体环境中文tofu原因UNKNOWN，未签其中文视觉；计划要求的第二引擎由真实WebKit满足，不称所有浏览器/OS通过。
- WebKit首次data TargetClosed缺主进程取证，首因仍UNKNOWN；同环境唯一DEBUG诊断见无EGL平台，main正常0而renderer退出未知。正常私有官方Mesa vendor补齐后明确缺GLES，再按该事实补官方libgles2；所有非零原件保留。只增加普通项目私有库/原厂vendor JSON搜索，未改host/sandbox/security/prefs/认证/driver/引擎/入口。最终DATA和实际应用正常；不能反签旧轮renderer无Native。原`automation is not allowed in the context, falling back to default session`警告原文保留，未为消警告修改任何控制或共享会话。
- 先前历史Native139首因UNKNOWN保持。本阶段最终可观察客户端、引擎主进程和Odoo正常退出，不用新通过反签旧异常。HTTP早期模板/重定向/revision预期、工具分支/选择器、模块路径和跨freeze比较误用均按实际非零保留，未改产品契约、改guard或补造PASS。
- 不存在数值模板ID沿既有后端回退合成200；非法格式409、存在但错kind403已实测。P1未借界面改变模板政策。屏幕阅读器、真实OS IME/移动设备/Safari、用户亲手效果、实机打印扫码均未验；生成/打印请求不等于签署/出纸，本阶段甚至未请求生成或打印。

## 普通医生7步复现

1. 正常复开后，用获准doctor别名登录，选择门店A；凭据只用现有私有provider。
2. 从当前门店/权限正常菜单进入“文书与已保存原件”。
3. 输入已有合成患者业务号`P00001313`，点“搜索文书”或Enter。
4. 展开“来源”，方向键/Home/End移动；先Esc取消，再选病历文字并Enter/Space确认。
5. 选现有适用正文模板，或保留“明确合成测试样例／未经审核”原空值。
6. 明确点“预览所选来源”，查看真实正文/作者/状态/合成待签提示；到此不点生成/打印。
7. 返回/重新搜索，按需只读旧原件；与私有包同视口前后图比较。无须手填数据库内部ID。

## 同步与结束

本地完整独立技术总签`7286c7ad8fd7af8774da6dfb671826843c26cbbad7cd471bfff9ff3e7ff56b9c`；正常Git/main文档/新#37唯一结果评论及实际读回待收口，未冒SYNCED。旧6382778460保持，#36不写、不重开，#37不关闭。Public仅5文件产品代码、必要工具/计划/设计、脱敏报告和索引，原始截图/样张/ZIP/凭据私有。

本阶段结果交付后停止。DL-P2—P6、完整S13全链/50活动会话、备份恢复、实机、正式临床/财务政策、真实患者/资金/通知、生产和产品合并未启用；S11一次扫码接收并入库仍待产品决定。用户带结果回GPT最终复核，不自动继续下一计划。
