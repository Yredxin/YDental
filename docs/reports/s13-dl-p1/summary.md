# DL-P1：文书查询与选择区

`YD-S13-DL-P1 / 1.0`。实施中；技术总签、私有效果包、最终保护和同步尚待收口，不预报完成。用户亲手效果待确认。仅P1启用，P2—P6 NOT_AUTHORIZED；完整S13未完成，#37保持OPEN、#36保持CLOSED。

## 固定范围与候选

业务分支`codex/s13-dl-p1-documents-query-r1`正常承接`06c7a4639a107e70c3db6352f8f929db80e6f94a`。阶段准备/运行工具`31ef5d7bb8e181bdd044c9bd6d77db20f1dbd5ef`的addon字节仍为旧产品；首个产品及执行候选`63ae208b09e1c582ed2493f0cba78cc7a94731fb`（极长项真实缺陷，尚非最终候选）。后续只报告/路由差异，不重放业务。core锁定`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。没有reset/clean/强推、覆盖未知工作或产品合main。

用户ZIP原地保留，9个payload与manifest逐字节/SHA一致。ZIP SHA `c01b0e06736a59016aea4e0beb37bee19c73190bc5ba24fb013019f876fbdfbe`；82,200字节参考HTML SHA `85ccfba06dfdda594606619f32bc4074bbc671bec9910709e6fa539cdeb5cab6`。完整读取所有MD和HTML源码；不声称视觉运行了GPT包先前受限的file页面。[设计规范](../../design/YDENTAL_DESIGN_LANGUAGE_V1.md)和[完整计划](../../execution/S13_DL_P1_IMPLEMENTATION_PLAN.md)为原02/03逐字副本，来源U/R/W编号承接包中05；小样和原包均私有，不把示例患者/计数/虚拟类型筛选移入产品。仓库main路由、AGENTS、活动状态、S13-UX报告及#23/#37正文/有效增量已按现行WORKFLOW-V3读取。

产品仅5文件：

|文件|变化|
|---|---|
|`ydental_print/views/ydental_document_templates.xml`|仅GET q与preview两select/按钮的局部wrapper、标签、必要说明和状态|
|`ydental_print/static/src/documents_query/documents_query.js`|两处显式挂载共用单选增强；原native select为唯一提交字段|
|同目录`documents_query.scss`|局部A色tokens、Grid/相对尺寸、边界/焦点/弹层|
|`ydental_print/__manifest__.py`|前台bundle注册上述2资源|
|`ydental_print/i18n/zh_CN.po`|5条新增源字符串翻译|

页头/导航、列表/分页/追溯、generate/previous_id、模板管理、批量导出、PDF模板/布局/纸型、其他岗位、业务model/controller/ACL/schema/公式均未改。模板改区以外前缀952字节、后缀7372字节实际逐字相同。旧模板7/布局7保持，**本阶段新原件/新PDF/打印请求数均待最终保护核实，预期0**。

## 控件与设计映射

A色surface `#fffbf6`、paper `#fffefa`、正文`#382f28`、说明`#716359`、强调`#94513a`及hover `#7e432f`；控件边界`#9c8776`、焦点`#6c513f`，装饰分隔`#e5cdbd`。采用规范已有值，未擅改品牌。字体为规范系统/CJK回退栈；min-height 2.75em、间距rem/em、两列Grid可自然单列，没有重置body/html。Chromium实际14组computed rgba经未实现者独立复算，最小正文5.613、必要控件边界3.319、焦点7.061；不以实现者PURE计算代替浏览器结果。

复用锁定core `Interaction`生命周期/监听器、`reposition`定位/边缘收缩、`normalize`本地候选查找、`addLoadingEffect`提交反馈。既有SelectMenu/Dropdown的menu角色和Tab/active-confirm语义不直接符合本阶段select-only合同，故最小局部适配，不新增框架/平台。组件只读取页面已授权options，使用textContent，无新搜索接口、fetch、存储、自动preview/generate。

GET q与POST preview仍为独立表单。`selection=kind:id:version`、`template_id`真实ID或原空值，以及csrf/revision/operation/q/page原生成表达式保持。增强成功后才隐藏native select；触发器无提交name，值只提交一次，disabled字段沿原生规则省略。required错误聚焦可见触发器；active候选与已确认值分开；Enter/Space确认、Esc取消、Tab/ShiftTab确认并自然离开，外点不吞目标，滚动/resize可安全取消。有效提交后才busy，字段仍可正确序列化；关闭或单选不产生请求。

## 实证与限制

- SOURCE/PURE：AST/XML/PO、锁定Odoo资源transpiler、libsass及Node语法检查通过；运行边界7 PURE通过。普通unittest模块路径调用曾ImportError，直接脚本入口7通过，非产品失败。
- 加载：固定63ae、完整即时pre成功后仅`ydental_print -u`，真实退出0/ERROR0/无Native；完整post及未实现者逐行核。25条原生ir.access和1group仅技术write_date变化，界面arch/元数据日期属预期；原权限、全部原件/经济库存/作者/价源/责任及约束索引保持。无重复旧经济链。
- 真实正常HTTP最终v5：17类，child0/signull。有权搜索/显式preview200；源版本/格式409；错类型现存模板/无财务源/无源/跨店403；真切授权store2后旧revision409，正常回store1新revision200；旧95下载实际SHA校验。空shell200明确无源且disabled，不冒403。
- 不存在模板ID沿**既有**后端resolve-empty→合成样式fallback200；非法格式409、存在但不适用类型403实测。未将200冒拒绝、未在P1改变模板政策。v1错误预期缺失模板拒绝、v2默认HTML switch303被工具误期望200、v3误期望同店switch增revision、v4原生ensure_db首次302被工具误期望200，原失败及实际非零保留。最终按原core真实路由和跨店revision修工具，产品不改。
- 正常撤权一次：doctor9原form200→group_manager正常medical write→none，独立PG确认→同旧formpreview403及旧95download403→原write精确恢复且独立PG确认→同form200。用户/公司/组/能力/员工/成员和其他权限语义完全恢复。实际child0；新增正常授权审计和write_date另分类。初次仅RO连接建立前遇角色连接数上限，未HTTP/授权提交；正常stop-owned释放自身池，fresh同角色probe/独立review/bind后复开，不改角色/集群或换DB凭据。
- 修改前后15对真实页面：5视口查询+preview各1、无结果1、四旁路各1。after另2个实际iframe裁剪，独立17图亲看。所有同页命名未改区computed/后代控件逐项相同，结算/仓库/原生加工PNG前后字节SHA完全相同；报表只有真实查询时点10:40:02→11:11:13，范围/3笔合计USD1300/样式保持。320px原整页scroll345/client320仍345/320，改区无新增横溢；不冒全页面移动端重做。
- Chromium/Firefox真实同页核心流已执行，实际原生浏览器zoom2与根字号32px测试分开。Firefox初次缺GTK正常项目私有依赖补齐；未装系统包/桌面/服务。headless Ctrl+=未产生真zoom的原失败不冒通过；Chrome tabs.setZoom/getZoom及原生metrics、Gecko同owned Page.setZoom/fullZoom metrics确认2并复位，未改UA/DPR冒引擎/缩放。Firefox登录bootstrap fetch曾被工具过早提交导航中断，按锁定core body is-ready等待后pageerrors0。
- 独立审阅实际发现Chrome full_page截图关闭浮层、Firefox中文tofu，二者原图不能签视觉PASS；正常viewport补图/项目既有CJK环境修复后证据待最终列明。长来源/模板/错误只用明示组件响应夹具，业务value不变、未写库凑名字。IME可信CDP组合与人工dispatch夹具分层，物理OS IME未验。真实Safari/iOS/移动设备/屏幕阅读器、用户亲手效果NOT_RUN，不宣称完整WCAG认证或全部浏览器一致。

## 数据与交付

唯一目标`ydental_s11_synth_20261023_01 / OID2171423 / cluster7694897083368259627`、同一filestore，从当前65内部+2外部原件/83实际文件及145业务、13技术投影完整承接；未新增/复制/改名库。旧1073+合法前批230=当时1303；所有旧账/分摊/价源/退款、label93draft与lab214sent、lot253收10用2余8、旧和455/508/880/215/281/282未完成责任须逐源保持。查询/preview/download审计、登录/选店和原生资产/会话元数据正常分类。最终root及未实现者独立物理只读后态尚待收口。

主控/root运行/集成/报告；documents唯一产品写者；tester实现验证工具/浏览器；acceptance未实现产品或测试工具、审源码/原始结果/逐张实际图片并独立核保护。共享OS如实披露，角色名不冒隔离。历史Native139根因UNKNOWN保持；本阶段目前无新Native信号，旧异常未反签。

私有效果包、最终全保护、独立总验收、服务正常停止与同步读回稍后在本文件和[矩阵](acceptance-matrix.md)/[索引](evidence-index.md)更新。不得据当前部分证据宣称TECHNICALLY_COMPLETE。

## 普通医生7步复现（软件测试，不是用户已亲手验收）

1. 正常复开后，用已授权doctor别名登录并选择门店A（本机127地址只对服务器本机有效，非其他电脑直达地址）。
2. 从当前门店/权限正常菜单进入“文书与已保存原件”。
3. 输入已有合成患者业务号`P00001313`，点击“搜索文书”或Enter。
4. 点击“来源”，用方向键/Home/End移动候选；先Esc验证取消，再选病历文字并Enter确认。
5. 选择现有适用正文模板，或保留“明确合成测试样例／未经审核”原空值选项。
6. 明确点击“预览所选来源”，查看真实预览正文、来源/作者/合成待签说明；到此不点生成或打印。
7. 返回或重新搜索，按需只读查看旧原件；可从私有包对照同条件前后图及5视口。用户效果意见仍由用户确认。

P1交付后停止。P2—P6、完整S13、负载、备份恢复、实机、正式政策、扫码组合、生产和产品合并均未启用；S11一次扫码接收并入库仍待产品决定。

## 尚在修复的真实长项缺口

未实现者实际亲看新长夹具7图后发现63ae在320px/200%根字号场景的浮层只有14px/26px，无法读候选；工具actual0与几何contained不构成通过。独立失败回执`long-fixture-visual-failure-independent.json` SHA `5eef89bd40da8f5b4286877e33b759267b728c3a4f45b56c29d84b06223be428`。已正常停止owned服务，正修本组件在空间不足时的viewport内可读定位；旧长夹具PASS语句不得反签视觉。Firefox中文tofu经正常字体环境诊断仍UNKNOWN；不改安全prefs/broker/共享OS，按计划允许的WebKit进行普通另一引擎能力补验。

修复已固定产品/执行候选`8dea2647760f6d6738abfc9db132cfa9d7feaee3`，仅JS open/setActive改变，其余4产品字节完全同63ae。正常空间保留core定位，空间不足才使用visualViewport边距内可读overlay；任意超高项首行开始且全文可滚读。Node/core transpiler/diff检查通过，尚待真实新候选效果。先成功采即时145/13/83 pre d608…，将正常启动并核实际新bundle字节；不为JS-only重复模块-u，原63ae-u与未变视图/PO/manifest/布局的适用范围已由未实现者SOURCE复核。此为正常报告checkpoint，尚未总签/发布。
