# [CODEX-FINAL] YD-S13-DL-P7 / 1.0

统一按钮语言与轻量SVG——仓库页面试点。当前报告为验证中草稿，最终结论须以实际总验收和同步读回为准。

技术：验证中，尚未总签。同步：SYNC_PENDING。用户亲手效果：待确认。范围仅库存主页面按钮/图标，非全站；后续页面/完整S13/合并部署生产未启用。

## 候选与真实分工

从指定P6业务分支的 `e31ea56d1ff903461eda86c08088c5f7e32aef7e` 正常承接，无未提交工作、无reset/clean/强推/从main重建。P6产品aec20359、工具539d147及唯一回执#37/6397824653保持；P1—P6技术交付与用户待确认分开。

- P7准备：e2e1d3392f8755801ddc598c8f0cbb8d657406d4；前态实际执行：29bccc48e67878203369f66c0abacf38b243869b，产品仍P6。
- P7产品：f3f8e6114bda27eabc18140d60bd9b8eb044e99e；后续纯测试工具候选另按实际运行归档，不把报告HEAD当新产品。
- root唯一产品、状态与报告写者及环境运行调度；testing编写/执行浏览器工具；runtime适配运行与原生QWeb/包构造工具；acceptance未实现产品或相应工具，独立审固定源码/原件/新physical保护/包/最终同步。共享OS不冒隔离。
- 锁定core f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb；既有 `ydental_s11_synth_20261023_01` / OID2171423 / cluster7694897083368259627及原filestore；不新建、复制、改名数据库。

## 控件族、变体与语义映射

|原控件族|数量（模板定义）|呈现|权限/状态和保留合同|
|---|---:|---|---|
|原查询button|1|primary + search前图标|原GET/action/q/maxlength/Enter，未新增字段|
|办理确认button|13|primary，可见原中文文字span，无成功勾|原type=submit及全部表单/submitter合同|
|办理summary|13|disclosure、原生marker|原details/name分组/可见条件；未加箭头/JS|
|原取消a|10|quiet、下划线|原href；原后3来源族没有取消，未新增|
|原来源a|1（按来源循环）|quiet + arrow-right后图标|原event_id+anchor，不隐式保留q/page|
|原上一/下一页a|2|secondary + chevron-left/right|原search_url/q/page；无链接边界仍原文字|
|原仅识别button|1|secondary + scan-line前图标|原type=submit、scan POST/字段/权限不改；本轮不提交|
|原批次/来源标题|2|package/list图标|原文字/数据/布局保持|

13办理模板权限/状态分支：can_write头部setup、policy、lot、receive、issue、inventory、transfer、lot_edit；can_catalog的product、product_edit；来源can_write的return（kind为replenishment/prescription且done）、verify（kind为return）、recover（state为pending）。单角色不同时渲染全部13；真实普通仓库前态显示9族，缺样用明确原生QWeb内存组件补验，不造状态。

43个允许呈现节点=15button+13summary+13a+2h2。SOURCE工具只验证并还原获准class/文字span/静态图后，整个原XML canonical exact；原输入/select/字段/条件/action/method/type/name/value/csrf/revision/key/operation/required/disabled/DOM顺序及控制器/服务/ACL/schema保持。原catalog和error模板不加scope，不新增产品JS。

## 样式与SVG唯一入口

`ydental_inventory/static/src/scss/inventory_actions.scss` 是元素级token/变体入口，准确路径opt-in为 `data-dl-actions="inventory-actions"`，复用原 `inventory_lookup` 判定，不用can_catalog判页。原P6仅删34行旧按钮/链接专属规则，避免冲突；input/table/其它区域未重做。未把暖色或字体放到表单祖先，无全局button/a/summary/.btn/:root覆盖。

primary陶土#94513A白字，hover/active#7E432F；secondary浅杏/深陶土，必要边#8C7564，active边加深；quiet下划线/轻悬停底；summary原生list-item。统一1rem/600、.625rem圆角、min2.75rem、padding .625em 1em、gap .5em，自然换行撑高，无固定中文宽高/厚阴影/渐变/装饰动画。仅140ms颜色/边框过渡，减少动效关闭；forced-colors使用系统色和焦点。danger、disabled、busy仅定义并由明确组件演示，产品不新增这些状态或逻辑。

Lucide **0.468.0 / f12b0de177fbc2a6795e99be065887e72b237123**，七个原SVG及完整ISC位于 `ydental_inventory/static/lib/lucide/`，来源、每原文件SHA、修改记录在SOURCE.json；Feather完整MIT采用v4.29.2固定commit1b002399e8758fb2bccea4d07312dc9e0f43dcb8一并保留（Lucide原ISC中的Feather版权声明同时保留）。QWeb只复制官方几何，增加局部class/data-icon/aria-hidden=true/focusable=false及相对width/height，24网格、线宽2、currentColor/round/no fill不改。无runtime/CDN/font/外链/事件/script/foreignObject/t-raw。

独立SOURCE回执e1a65a0e491ecf44e825cba379ef623584570badf92b8757af7daf6c5017305f已实际核43节点、原合同及七几何、官方tag/原文件/许可bytes与SHA；动态和最终总签另列，不由SOURCE冒充。

## 实际验证、保全与失败

详细逐项结论见[矩阵](acceptance-matrix.md)，原件位置/SHA见[索引](evidence-index.md)。SOURCE/PURE、原生QWeb内存、浏览器组件、HTTP/真实浏览器、独立提交状态均分层。本轮不重新执行旧入库、出库、盘点、退货或恢复，不以只读测试证明业务重新执行成功。

前态Chromium main-v2和六旁路bypass-v1实际client0/native0/signull/logout200。首before-v1在正常后台UI已ready后错误等待networkidle超时（client2/native0），工具前向修、不反签旧失败。前态截图result有50索引/45唯一PNG，5次同名末次覆盖，其中3初索引SHA已不可核；只采末次可核图，缺口保留，不重跑GET链补图。后态shot使用唯一名称且拒覆盖。

新P7初次create因新私有根目录775被原guard拒绝，未连接DB；将本阶段私有目录收紧700后正常创建新scope，旧scope/STOP/guard未改。早期python解释器/原Feather annotated tag对象404等普通准备错误保留事实，不归成产品失败。旧UNKNOWN和历史Native/旧失败不改。

独立初始newphysical266501，RO/RR/rollbackidle/closed，完整145业务/13技术/现场83文件bytes-size-SHA，九区与P6最终投影逐值同。before后完整checkpoint保持全部旧行/原件/金额库存/身份作者价源/责任及旧audit，仅正常accepted读取/认证审计另列。后态加载、最终完整保护与独立结论待实际发生后填写。

## 普通角色7步复现

正常受控复开后使用，不承诺当前在线或自动化窗口可接手：

1. 普通仓库岗位正常登录，选择授权门店，从原菜单进入库存。
2. 输入原物料/批次名，点击查询文字或search图标，也可按Enter，确认只进行原GET查询。
3. 阅读原九列批次及三个不同数量；窄屏聚焦原表格后横向阅读，不把无告警解释为可发放。
4. 阅读来源原状态/数量/责任，点击“查看本条来源”文字或右箭头到原event锚点，再浏览器返回。
5. 用原来源上一/下一页，核原查询参数及批次不随来源分页，边界仅文字。
6. 有权办理入口只用Enter/Space展开收起、Tab确认焦点、原取消返回；不填新证据、不点确认、不提交扫码。
7. 检查窄屏、浏览器200%或根字号200%时文字图标和焦点可读；识别按钮只看外观和焦点，不执行POST。

本批完成后停止。#37保持OPEN，仅一份P7最终结果；P1—P6旧回执/P5 PARTIAL历史保持，#36保持CLOSED。main仅必要路由文档，不合产品、不部署。用户效果、实机/屏读/真实OS输入法/正式政策与完整S13均非本次技术签字。
