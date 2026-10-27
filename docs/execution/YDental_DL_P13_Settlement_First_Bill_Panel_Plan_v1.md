# YDental / odoo-sd｜DL-P13 完整限定实施计划

计划 **YD-S13-DL-P13 / 1.0**，名称：结算首个出账办理面板——暖色动作、勾选项排布与响应式留白。用户2026-10-27在本会话明确启用；本文件保存完整启动提示与附件的执行合同。P13为P12-RWD后的独立限定阶段，不重开P12、不改整张结算页、不自动启用其他办理或P14。

## 1. 承接与入口

先读固定GPT_HANDOFF/AGENTS、main路由和活动CURRENT、#23/#37有效正文和增量、P5/P7—P12相关源/报告，核origin/HEAD/工作树/合法增量/唯一写者。P12业务分支`codex/s13-dl-p12-settlement-readonly-actions-spacing-r1`，报告锚点`4e3e3aa1027286de473044d23f54d5faa81c9384`，产品/运行`f3c63b6f2ec86f0518d6f0dae9b19de633085ac1`。新分支`codex/s13-dl-p13-settlement-bill-panel-r1`从实际业务基线正常建立，不从文档main重建，不reset/clean/强推。

P12整体 **PARTIAL / SYNCED（仅传输）/ STOPPED**：真JS-off A04原768×1024、横读36→一次Tab仍36/left26/clip50 FAIL，超高候选整圈同屏限制保；JS-on一次Tab增强保。P13通过不关闭/回填这些旧门槛；P5/P1—P12旧PARTIAL、两续办/RWD失败、UNKNOWN、原件/包/唯一P12回执#37/6422670245全保。

原唯一合成目标/filestore按现场重新核身份及准入，不重建/克隆/改名或复活旧STOP/时间；以当前完整清单核83附件引用/80唯一真实物理文件/3共享。正常私有provider可复用，凭据不进Git/Issue/聊天/原请求日志/截图/包。资源由主控调度，普通错误内部修复，不逐包等GPT或旧软额度批准。同OS不冒隔离，未实现者不签自己的产品或相应运行测试实现。

## 2. 目标与唯一产品边界

只改`/ydental/settlement`中直接位于P12 lookup之后的首个：

`details[name="settlement-operation"][t-if="can_write and (today or history)"]`

其原form为`method=post action=/ydental/settlement/action`、`operation=bill`，summary为Select fees to bill。正常流程为先选择已确认未出账费项→填写可选折扣及原因→确认出账或取消；打开面板不表示账单已生成，不增加业务操作方式。

可整理原details/summary、checkbox费项标签组、折扣金额/原因字段组、原“生成原生过账账单”submit和Cancel链接。只加独有局部标记/class/span/必要有限排版wrapper/SCSS和必要manifest资产，先核实际已安装合成QWeb/继承而非只猜文本。优先复用`o-ydental-actions`不改共享mixin；不需图标，若用只原Lucide固定子集/SHA/许可，不用完成图标暗示过账。确认primary、取消quiet、summary原生disclosure，费项为原生checkbox，无新增全选/清空/实时计价/下拉功能。

严格不变：原form/action/method、tokens t-call仍在form内、CSRF/revision/key/output、operation、每个fee_ids的name/value及默认未勾选、discount的number/min0/step.01/value0、reason maxlength300、submit type、cancel href、所有t-if/t-foreach/权限条件、DOM字段顺序、FormData/submitter/提交时机/错误处理、原字段标签/金额/单位来源。不得用禁用或删除合法确认能力凑零动作。

冻结P12 lookup的全部HTML/CSS/JS/media/表列/fee_focus.js；页头导航、其它店页面、首bill之后所有其它账单/收退款/免单/审批/日结/渠道更正/原件/PDF控件及其它岗位/网站后台。无产品JS、controller/model/service/ACL/schema/费用公式/核心/odoo-12/OS/防火墙改动。

## 3. DL-15—30呈现与尺寸

沿A“杏陶暖白”共享配色/字重/圆角，正常控件1rem、最小2.75rem、自然撑高、长中文换行。仅局部Grid/Flex和rem padding，窄屏/放大优先一列；保正常纵滚，不缩字/藏字段/固定高裁切/根overflow:hidden，不限制浏览器缩放，不设user-scalable=no/maximum-scale=1，不CSS zoom/transform缩页。

|空间关系|建议与唯一owner|
|---|---|
|summary→展开首组|约.75rem，closed无洞|
|标签→输入|.5rem|
|同组费项|.75rem|
|字段或提交组之间|约1rem|
|独立操作组|约1.5rem|
|≥1024/768—1023/481—767/≤480|按实际可用空间局部响应式padding，合格既有值保，不死套像素或父子重复叠加|

**仅P13新约定**：自身高于视口的极长内容/控件只要求内容和焦点顶末可正常分段滚动到达、无祖先非法裁切；不要求物理不可能同屏的整圈，不借此回填P12旧结论。native浏览器200与独立根字号200分开验证。

## 4. 业务和测试边界

本阶段禁止live提交operation=bill；原确认按钮合法功能保持，只验证显示/展开/焦点/取消及无网络FormData。不得真实出账、收/退款、免单、日结、治疗、库存、扫码、原件/PDF、打印、签署或发布补截图；不造新持久费用。新模块模板必要-u须完整即时pre→真实退出/日志→post及独立分类；纯CSS不重复-u。

真实普通有权角色仅只读显示/选择，缺权/无today-history按原条件不显示；不能以隐藏或loaded组件推断后端拒绝。适用正常HTTP只读负例独立写层级；不直接POST以“验证权限”突破本次禁止经济提交。缺具体分支用明示loaded QWeb内存组件，不冒真实身份/数据/授权；disabled/empty真实或明示组件，不产品造状态。

两真实engine Chromium/WebKit，五视口1366×768、1440×900、768×1024、390×844、320×800；正常/native200/root200、JS-on/真正off；长中文/空态/开合/键盘Tab/ShiftTab/EnterSpace/边界/焦点/原FormData、默认hover/active/focus和对比度。使用正常CSS加载后的computed/BOX/裁切祖先/原PNG，不以退出0或截图数代验收，不冒屏读/Safari/iOS/实机/用户效果。

## 5. 普通文字流程

F1：正常读取岗位→原菜单/当前授权店→阅读患者及三段费用；有写权且有today/history时出现首办理入口，打开不表示出账。

F2：聚焦原summary，Enter/Space开合；读原checkbox/折扣/原因，Tab到原确认但不按Enter/Space提交；原Cancel正常返回。只在无网络层序列化原字段，账单/付款/库存事件零新增。

F3：320/390及两放大展开，长中文/checkbox/字段/确认/取消自然单列/换行且完整可达；超高按本P13分段可达，不缩字藏输入。

F4：can_write false或today/history都空则面板不显示；权限、当前店、修订保护不变，组件/预拦截不冒真实后端拒绝。

## 6. 连续W0—W4

|包|内容与结束判断|
|---|---|
|P13-W0|核入口/基线/目标已加载QWeb/唯一details、字段权限、真实before、无网络FormData、独立测试与保全，准确圈定不泛化|
|P13-W1|原生details/checkbox/字段局部warm actions+spacing、最小asset；其它办理无CSS影响|
|P13-W2|五view/两zoom/双engine/键盘焦点/真off与有限普通修复，本P13完整可达；P12旧记录独立保|
|P13-W3|有权/无权只读、无网络序列化、P12/P11有限对照、保护/审计；无bill/经济提交|
|P13-W4|未实现者源/真实浏览器/新physical/原图包/同步独核，更新同CURRENT与三报告，只发一份P13结果，结束停止|

包内连续推进，不逐批返回GPT；重大需求/方向/真实资源或不可确认持久结果才提交具体事实决策，普通工具错误/代码修复内部闭环。

## 7. P13-T01—T12

|项|验收要求与层级|
|---|---|
|T01|仅首bill opt-in，lookup/root/完整后缀/其它页冻结；白名单剥呈现后原业务模板exact。SOURCE+合成QWeb|
|T02|primary/quiet/disclosure和共享色/圆角/字重同，真实中文/对比/焦点，若SVG则许可SHA同。loaded+computed|
|T03|标签/费项/字段/提交取消/展开间距单owner，空态/closed无洞。computed/BOX|
|T04|双engine五view当前办理控件/长中文完整自然换行，目标不添根横溢出。BROWSER|
|T05|双engine native200/root200独立，最小操作高度/文字/盒/圈可达；超高分段并明确原限制。BROWSER/明确夹具|
|T06|原summary EnterSpace、checkbox/number/text/确认/取消自然Tab/ShiftTab、可访问名、真实或明示disabled/empty。真实+loaded|
|T07|全部FormData/fee_ids/discount/reason/tokens/operation/action/type/权限条件逐值同，不提交实际POST。SOURCE+真实DOM无网络序列化|
|T08|有权有费合法显示，无权/无费条件同；原后端权限保，组件不冒真拒绝。普通有权只读+SOURCE/适用HTTP|
|T09|真实两engine/两JS本面板原生读取交互；P12 A04真offFAIL单列，不作为P13自动PASS/新重跑目标|
|T10|P12查询/三费用/已有增强/原A04记录、P11源、库存/文书/报表/其它办理代表有限旁路不改；时间审计精确分类。前后+SOURCE|
|T11|未实现者新RO/RR事务完整业务保护、83/80/3真文件bytes/SHA、旧审计与正常新读分类，零经济库存/原件/PDF/打印/签署/模板发布|
|T12|固定产品/工具/运行/报告、旧失败/12矩阵/独立总签、真实前后图/私有SHA包/5—8步复现、正常收尾、GitHub正常push/readback；技术与同步分别写|

任何适用失败/无独立结果，P13如实PARTIAL/BLOCKED；不因P12旧PARTIAL排除P13验收，也不因P13通过推翻旧失败。按候选/源码影响复用未受影响P1—P12证据，不重跑历史全链。

## 8. 交付和停止

维护同一个活动CURRENT及`docs/reports/s13-dl-p13/{summary,acceptance-matrix,evidence-index}.md`，含实际改动、动作映射、padding/间距owner、12项实证、固定源/actual命令退出/原PNG/SHA/独立保护/失败UNKNOWN/未验证事项和5—8步复现。新私有PNG/ZIP/manifest/SHA包独立命名，不覆盖任何旧包、不上传Public，不含provider/凭据/session/完整请求/DB/PDF/程序/字体。

计划结束才#37新增一份P13最终结果并全文读回；P12唯一6422670245和全部旧14评论全文不改，#37 OPEN/#36 CLOSED。main只必要CURRENT/GPT_HANDOFF路由，不合产品/不部署。同步失败保本地固定结果标SYNC_PENDING，不冒SYNCED。

必要正常owned窗口及browser正常收尾，独立技术验收与同步后停止；不改第二结算办理，不启动P14/完整S13/50负载/备份恢复/实机/正式政策/组合扫码/真实患者资金/外部通道/生产/合并部署。用户亲手效果待确认。
