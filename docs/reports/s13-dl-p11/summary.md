# DL-P11 经营报表来源详情页实施结果

[CODEX-FINAL] YD-S13-DL-P11 / 1.0

技术：IN_PROGRESS（尚待最终独立验收）  
同步：SYNC_PENDING  
用户亲手效果：待确认  
范围：仅 `/ydental/reports/source/<metric>/<source_id>` 正常 GET 的来源详情呈现。

[用户完整计划](../../execution/S13_DL_P11_IMPLEMENTATION_PLAN.md) · [T01—12矩阵](acceptance-matrix.md) · [脱敏证据索引](evidence-index.md)。

## 候选与实现

|对象|固定值与实测边界|
|---|---|
|业务分支|`codex/s13-dl-p11-report-source-detail-r1`，从 clean P10 最终 `6d74bbe0b95fc1dbfbacd51e9d2475ee52749e36` 正常承接|
|P10继承|产品/实际运行 `8a1547a14f5647d6a49555c8ab7f9ceb658511e3`；工具 `2c18d3271b49ab1ba2d6622e1755ed9678a97997`；唯一回执 #37 / 6408631886|
|P11产品|`f235c649df0f58403ae3ce50a666ec2c377787a2`|
|必要XML加载|同 f235c649，仅 `ydental_reporting -u` 一次；native 0 / ERROR 0 / 无 Native 信号|
|after工具/运行|`16e1234a61674f60b9c90a36fd0e8e2dfbc3fa4c`；相对产品仅工具及状态，产品字节相同；实际运行材料另逐件固定|
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

仅业务/native两个动作之间原装饰“·”由组 gap 替代；全 XML 比较只在该唯一原位置恢复，原 quantity、scope、facts 中的点不变。原生翻译术语也只分类这一邻接两原标签的独立装饰项；其余业务标签全文/顺序不变，没有全局文本归一化。

## 原值、授权与页面隔离

完整 XML 白名单还原后 C14N 严格同 P10；manifest 恰新增单资产，其它 addon 原字节冻结。实际 loaded 五模板 EN/CN 和四个明确内存 QWeb 分支逐项核原字段、条件、所有 href 和完整 trace，不能替代真实身份/授权。两处 return、原 source/business/native/allocation URL 均沿服务器原值，控制器仍 `_query(..., all_rows=True)` 后重新查找授权来源，没有新增参数或业务快捷操作。

真实原收款来源只读：实收300；原账单270/分摊270/当前应收0，与原账单200/分摊30/当前应收170；这是既有两分摊，不重做收款。患者/金额币种精度/业务时间/状态/facts/完整 trace 按原投影对照。动态 query_at 只分类 scope 第三段唯一原生字段，保留前后原值；不删除其它时间或排序。

SOURCE/loaded/真实浏览器、内存组件、故障组件分列。多卡和长中文/连续哈希/60行追溯只用有【P11夹具】标识的 loaded QWeb 与原产品 CSS，未创建持久业务。浏览器、权限、缩放、隔离和最终完整保护的实际结论在矩阵/索引追加，不预签尚未取得的证据。

## 保护、失败与限制

开工未实现者新 physical513239 RO/RR/rollbackclosed，完整145业务/13技术/九区与主控及P10末态逐值同；83引用/80实际路径/80不同SHA逐bytes/size/SHA，三处共享引用保。两个 before 窗口仅新增95正常 accepted 认证/读取审计，其它144业务、13技术、文件/配置/schema同。必要加载即时完整 pre→实际0→post业务和文件保持，5原生技术类、3arch及main旧EN backup与4直接依赖精确归类。最终新的独立 physical 与全阶段结论尚待，不把这些局部证据冒最终保全。

首内存组件缺输出目录 native1、首 Chrome layout 双层 main 选择器 Node2、术语单装饰点 PURE 断言与 typed query_at/path 遮蔽工具问题均保留首因与修正；有效子项不反签整轮。before 8 actual clients=7Node0/1Node2、8 native0、43原PNG已逐件独核。无未知业务提交或产品原生崩溃。

本 source 本轮Chromium390/320前后根宽各393；WebKit390前后390、320前后377，其余三个视口各same。未新增root溢出，不宣称修复外壳根溢出。P10主页面320旧346/332、WK无JS CSV wireBOM/native文件未观测、P9旧wrapper/Node UNKNOWN、P5历史PARTIAL与此前所有旧失败/原件保持，不重跑历史全链。WebKit不等同Safari/iOS，AX不等同屏读，用户效果、实机和全站认证均未代签。

## 普通岗位7步复现

1. 在正常新有效运行窗口，用原有报表来源读取权的普通岗位登录并选授权门店；不要恢复旧scope/STOP或把localhost当远端入口。
2. 原菜单进入经营报表，明确查询原指标、日期和授权门店；只读查看生效范围。
3. 从原“查看来源与分摊”进入详情，核暖色导航、顶部返回、原标题和只读说明。
4. 阅读已生效范围与查询时点，原生展开/收起时区；核来源卡的患者、金额/数量、状态、业务日和facts原值。
5. 有原分摊则逐项核账单及四列值；跨店来源默认显示操作权限提醒，保持当前工作店，不办理来源业务。
6. 用键盘展开技术追溯并阅读完整模型、ID、原文本；窄屏只在表格局部横读，核两种200%和首尾焦点。
7. 分别使用顶部/底部原返回，核同一生效过滤和页码；不生成、打印、签署、发布、收退款、库存、治疗或扫码。

## 同步与停止

当前尚未最终技术签署或正常推送读回，不能称SYNCED。最终仅#37一份P11回执，保持OPEN；#36 CLOSED，旧12评论不改。main仅必要文档路由，不合产品、不部署。P11完成立即停止；P12/其它页面、完整S13/50活动负载/备份恢复/实机/正式政策/S11组合扫码/真实患者资金和外部通道/生产均未启用。用户亲手效果继续待确认。
