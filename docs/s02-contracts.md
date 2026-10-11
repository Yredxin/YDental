# S02 空间配置工程契约

需求仅来自 [#23](https://github.com/Yredxin/YDental/issues/23)、[#26](https://github.com/Yredxin/YDental/issues/26) 当前正文及有效评论；前置固定到 [S01 最终收口](https://github.com/Yredxin/YDental/issues/25#issuecomment-6108974493)。本次用户启用、环境与边界已在 [开工检查](https://github.com/Yredxin/YDental/issues/26#issuecomment-6108999828) 发布并完整读回。本文记录已实现接口，不另立需求或批准生产参数。

## 模型与身份

`ydental_space` 直接依赖 `ydental_access`、`web`，许可证 LGPL-3，目标锁定本地 Odoo 20 fork。`ydental_space_test` 仅供新隔离库验证，不能安装到业务环境；其中的 in-use 标记只验证下层保护扩展点，不是排期、任务或租约。

|模型|职责|身份/归属|引用与删除|
|---|---|---|---|
|ydental.space.floor|楼层与布局聚合版本|原生 id；S01 门店|永久稳定 ID，仅归档|
|ydental.space.area|同店同层区域树、报到祖先、服务发现|原生 id；floor/store；parent_id|restrict；禁止循环/跨楼层；先归档有效子项|
|ydental.space.station|四类稳定工位|原生 id；floor/store/area|restrict；更名移动不换 ID；归档保留引用|
|ydental.space.item|资源图形摆放|原生 id；floor/store；可关联 station|restrict；独立几何；工位移动/缩放同步其有效图形|
|ydental.space.resource|集团公共或本店私有资源定义|store 为空是公共；不能直接迁移归属|restrict；只保留安全 SVG XML；归档保留历史|
|ydental.space.version|抽象配置版本/审计/变更保护|不建业务表|下层扩展契约|

公司与门店复用 S01，不复制公司或员工。所有实际空间模型有公司限制：门店公司属于原生 allowed companies；公共资源允许空门店。普通用户还必须绑定真实登录会话，拥有当前店 space 权限；写入逐请求重新鉴权并受 S01 异店坐诊写保护。公共资源可读，但修改还需集团维护权限及当前店 space 读写，不能借公共标识写他店私有记录。集团资源不是按 attachment URL 判定。

## 数据字典

共同原生字段 `id/name/active/create_uid/create_date/write_uid/write_date/display_name` 复用 Odoo：id 为数据库主键且不可客户端指定；name 必填；active 默认 true；创建/修改时间 naive UTC；元数据与 display_name 不接受人工覆盖。每张实际表继承 name/active/ydental_version；版本整数初始 1，不可复制旧版本。下列字段的默认及计算均在服务端，UI readonly 不构成授权。门店和楼层归属建立后不可直接更改，任何用户也不能用普通 write 写入派生字段。

所有非公共记录：读=当前店 space>=read；写/创建/归档=当前店 space=write；导出还需 export=write；无临床字段。公共资源写额外要求集团权；普通物理删除一律拒绝。所有 Many2one 使用 restrict 保历史，parent_id 为空表示根区域。store 为空仅对公共资源合法。

### ydental.space.area

|字段|类型/关系|必填/默认/计算|约束与保留|
|---|---|---|---|
|`ydental_store_id`|Many2one → `ydental.access.store (继承)`|必填；无默认|身份引用 restrict；同店同层校验|
|`ydental_category`|Selection|default='space'|有限几何/枚举/版本校验；修改留痕|
|`ydental_floor_id`|Many2one → `ydental.space.floor`|required=True|身份引用 restrict；同店同层校验|
|`parent_id`|Many2one → `ydental.space.area`|可空/无额外默认；继承字段保留原约束|身份引用 restrict；同店同层校验|
|`ydental_child_ids`|One2many → `ydental.space.area`|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|
|`ydental_station_ids`|One2many → `ydental.space.station`|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|
|`ydental_purpose`|Selection|required=True；default='care'|有限几何/枚举/版本校验；修改留痕|
|`ydental_reporting`|Boolean|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|
|`ydental_prefix`|Char|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|
|`ydental_missed_limit`|Integer|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|
|`ydental_queue_area_id`|Many2one → `ydental.space.area`|compute='_compute_queue_area'|只读派生；普通 create/write 禁止覆盖|
|`ydental_capability_ids`|Many2many → `ydental.access.capability`|compute='_compute_capabilities'|只读派生；普通 create/write 禁止覆盖|
|`ydental_shape`|Selection|required=True；default='rect'|有限几何/枚举/版本校验；修改留痕|
|`ydental_points`|Json|default=list|有限几何/枚举/版本校验；修改留痕|
|`ydental_x`|Float|default=20|有限几何/枚举/版本校验；修改留痕|
|`ydental_y`|Float|default=20|有限几何/枚举/版本校验；修改留痕|
|`ydental_width`|Float|default=300|有限几何/枚举/版本校验；修改留痕|
|`ydental_height`|Float|default=200|有限几何/枚举/版本校验；修改留痕|
|`ydental_angle`|Float|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|

### ydental.space.floor

|字段|类型/关系|必填/默认/计算|约束与保留|
|---|---|---|---|
|`ydental_store_id`|Many2one → `ydental.access.store (继承)`|必填；无默认|身份引用 restrict；同店同层校验|
|`ydental_category`|Selection|default='space'|有限几何/枚举/版本校验；修改留痕|
|`ydental_width`|Float|required=True；default=1000|有限几何/枚举/版本校验；修改留痕|
|`ydental_height`|Float|required=True；default=700|有限几何/枚举/版本校验；修改留痕|
|`ydental_area_ids`|One2many → `ydental.space.area`|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|
|`ydental_station_ids`|One2many → `ydental.space.station`|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|
|`ydental_item_ids`|One2many → `ydental.space.item`|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|

### ydental.space.item

|字段|类型/关系|必填/默认/计算|约束与保留|
|---|---|---|---|
|`ydental_store_id`|Many2one → `ydental.access.store (继承)`|必填；无默认|身份引用 restrict；同店同层校验|
|`ydental_category`|Selection|default='space'|有限几何/枚举/版本校验；修改留痕|
|`ydental_floor_id`|Many2one → `ydental.space.floor`|required=True|身份引用 restrict；同店同层校验|
|`ydental_resource_id`|Many2one → `ydental.space.resource`|required=True|身份引用 restrict；同店同层校验|
|`ydental_station_id`|Many2one → `ydental.space.station`|可空/无额外默认；继承字段保留原约束|身份引用 restrict；同店同层校验|
|`ydental_x`|Float|default=40|有限几何/枚举/版本校验；修改留痕|
|`ydental_y`|Float|default=60|有限几何/枚举/版本校验；修改留痕|
|`ydental_width`|Float|default=60|有限几何/枚举/版本校验；修改留痕|
|`ydental_height`|Float|default=50|有限几何/枚举/版本校验；修改留痕|
|`ydental_angle`|Float|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|

### ydental.space.resource

资源 name 覆盖为 translate=True；公共内置图形提供英文源与简体中文翻译。store 可空，无默认，空值明确表示公共定义。

|字段|类型/关系|必填/默认/计算|约束与保留|
|---|---|---|---|
|`ydental_store_id`|Many2one → `ydental.access.store`|可空/无额外默认；继承字段保留原约束|身份引用 restrict；同店同层校验|
|`ydental_kind`|Selection|required=True|有限几何/枚举/版本校验；修改留痕|
|`ydental_category`|Selection|required=True；default='space'|有限几何/枚举/版本校验；修改留痕|
|`ydental_capability_ids`|Many2many → `ydental.access.capability`|可空/无额外默认；继承字段保留原约束|只关联现有 S01 能力；禁止嵌套编辑字典|
|`ydental_svg`|Text|required=True|有限几何/枚举/版本校验；修改留痕|
|`ydental_upload`|Binary|compute='_compute_upload'|非存储上传输入；接受原生 filename/content；保存前移除，仅持久化安全 XML|

### ydental.space.station

|字段|类型/关系|必填/默认/计算|约束与保留|
|---|---|---|---|
|`ydental_store_id`|Many2one → `ydental.access.store (继承)`|必填；无默认|身份引用 restrict；同店同层校验|
|`ydental_category`|Selection|default='space'|有限几何/枚举/版本校验；修改留痕|
|`ydental_floor_id`|Many2one → `ydental.space.floor`|required=True|身份引用 restrict；同店同层校验|
|`ydental_area_id`|Many2one → `ydental.space.area`|required=True|身份引用 restrict；同店同层校验|
|`ydental_queue_area_id`|Many2one → `ydental.space.area`|related='ydental_area_id.ydental_queue_area_id'|只读派生；普通 create/write 禁止覆盖|
|`ydental_kind`|Selection|required=True；default='care'|有限几何/枚举/版本校验；修改留痕|
|`ydental_enabled`|Boolean|default=True|有限几何/枚举/版本校验；修改留痕|
|`ydental_callable`|Boolean|default=True|有限几何/枚举/版本校验；修改留痕|
|`ydental_item_ids`|One2many → `ydental.space.item`|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|
|`ydental_add_capability_ids`|Many2many → `ydental.access.capability`|可空/无额外默认；继承字段保留原约束|只关联现有 S01 能力；禁止嵌套编辑字典|
|`ydental_remove_capability_ids`|Many2many → `ydental.access.capability`|可空/无额外默认；继承字段保留原约束|只关联现有 S01 能力；禁止嵌套编辑字典|
|`ydental_capability_ids`|Many2many → `ydental.access.capability`|compute='_compute_capabilities'|只读派生；普通 create/write 禁止覆盖|
|`ydental_x`|Float|default=40|有限几何/枚举/版本校验；修改留痕|
|`ydental_y`|Float|default=60|有限几何/枚举/版本校验；修改留痕|
|`ydental_width`|Float|default=90|有限几何/枚举/版本校验；修改留痕|
|`ydental_height`|Float|default=70|有限几何/枚举/版本校验；修改留痕|
|`ydental_angle`|Float|可空/无额外默认；继承字段保留原约束|有限几何/枚举/版本校验；修改留痕|

### ydental.space.version

|字段|类型/关系|必填/默认/计算|约束与保留|
|---|---|---|---|
|`name`|Char|required=True|有限几何/枚举/版本校验；修改留痕|
|`active`|Boolean|default=True|有限几何/枚举/版本校验；修改留痕|
|`ydental_version`|Integer|required=True；default=1|有限几何/枚举/版本校验；修改留痕|

## 枚举与能力计算

区域用途：care/exam/pharmacy/settlement/waiting/toilet/sterilization/other；仅 care/exam/pharmacy 能开启独立报到。形状 rect/polygon，polygon 需3至100组有限坐标。工位类型 care/exam/pharmacy/settlement；settlement 禁止可叫号。资源类型 chair/imaging/pharmacy/settlement/door/wall/waiting；初始资源只有这些必要图形，不预建其他业务。

工位能力 = 有效摆放资源能力并集 + ydental_add_capability_ids - ydental_remove_capability_ids。手动移除优先于增加。区域能力递归汇总有效且启用的子工位/子区，仅作服务发现；不会反向授给区内每台设备。最近报到祖先从自身区域向上找第一个 reporting=true 的区域，子区开启后唯一归属子区；没有祖先时为空，不伪造合法报到资格。

## 动作与原子边界

|入口|前置/权限/版本|原子副作用/输出|失败与恢复|
|---|---|---|---|
|各模型 create|真实会话/当前店 space=write；公共定义另需集团权；初始版本1|校验归属和几何；配置 create 审计；更新布局聚合版本；返回原生新 ID|异常整笔回滚，不产生队列或名额|
|各模型 write/import/RPC|同店 space=write；必须提交当前 ydental_version；禁止写派生、系统元数据、门店/楼层归属|检查变更钩子；版本递增；工位几何同步有效关联图形；前后快照审计|access_denied/version_conflict/ValidationError；刷新后明确重试|
|floor.action_snapshot|当前店 space>=read；原生 RPC 带登录 revision|配置、能力、资源 ID、writable、未接入状态；无业务提交（S01 读取审计除外）|无源读权拒绝；不列他店私有资源|
|floor.action_save_geometry(version, changes)|space=write；匹配聚合版本；最多500项；固定 kind/model 白名单；每条归属该 floor|只改坐标、尺寸、方向和区域顶点；同事务全部成功；返回 accepted/新版本|旧版本 version_conflict；任一非法条目整批回滚，旧布局保留|
|floor.action_plan|当前店源读取权|返回原生 client action|无源读权拒绝|
|action_archive/unarchive|space=write；服务器当前版本；保护钩子|更改 active；保留 ID 与 restrict 引用；审计|楼层先归档内容、区域先归档有效子项；无强制删除|
|resource create/write 上传|本店 space=write 或额外集团权维护公共；写需版本|有界 Base64 解码、安全 XML 解析、白名单重建；仅保存 XML，不保存原件；SVG 获取经鉴权|Unsafe SVG/ValidationError；原内容和版本不变；不回显攻击正文|
|GET /ydental/space/resource/id.svg|auth=user；每次模型源读取权限|image/svg+xml；no-store；CSP default-src none + sandbox；nosniff|无权403；不使用 bearer/public URL 绕过|
|export_data|源读取 + export=write|S01 审计与原生导出|缺任一权限拒绝|
|unlink|无普通物理删除入口|无|要求归档，保留历史|

原生表单通过仅注册在本模块五个表单的 SpaceRecord，在生成保存载荷时追加页面加载的 ydental_version；不刷新版本后覆盖，不全局 patch 原生表单。只靠 readonly 或 force_save 不足以传递未修改的版本字段。列表不提供内联编辑。

配置修改先锁真实登录范围，再取事务 advisory lock 26002，再按 ID 锁楼层和对象。配置是低频工作，统一锁确保公共资源反向引用集合与并发摆放一致；没有宣称满足 S13 高并发性能。保存成功后必须读回新版本，旧版本只能刷新，不能自动覆盖。失败审计沿用 S01 机制；成功配置修改记录真实 actor 和前后 name/active/version、坐标、能力、关系 ID、用途、形状、资源类型、队列前缀和过号参数；SVG 只记安全结果 SHA-256，不记录 SVG 正文、原输入或业务正文。

## SVG 与配置

`ydental_space.svg_max_bytes` 明确技术初值 1048576 (1 MiB)，可配置允许范围 1024 至4194304。生产值未批准。输入/解码前均做尺寸限制；lxml resolve_entities=false/no_network=true/load_dtd=false/huge_tree=false，拒绝 DOCTYPE；最多5000节点，有限 root width/height/viewBox。仅 svg/g/path/rect/circle/ellipse/line/polyline/polygon/title/desc 及限定属性；脚本、事件、CSS、外链、use/image/foreignObject、实体、命名空间绕过、非法绘制属性一律拒绝。使用解析器而非正则解析 XML；属性值过滤是解析后的白名单补充。图形以隔离 SVG 响应和 image 显示，不插入 HTML。

`ydental_missed_limit` 当前初始0表示尚未发布有效生产过号参数；S02只保存显式非负值，S06决定并验证运行排序参数。不得把0或建议N=3解释为生产批准。时间和队列业务日期均由后续负责阶段使用 S01 门店时区计算；S02 没有日终服务。

状态主题集中在 plan.scss 的作用域变量，错误通知含可翻译文案。默认状态 not_connected / 尚未接入坐诊状态，不生成占用、空闲、叫号或保留的演示值。

## 下游扩展契约

S03 依赖稳定 station ID、active/enabled、floor/store/area、能力，不可由人员安排再造空间 ID 或容量。S05 消费区域服务能力和唯一报到祖先，不把工位资源或医生绑定到预约。S06 扩展 station._get_runtime_states 返回真实状态，并负责前端只读状态渲染和主题映射；本批画布仅显示未接入提示，不能只覆盖服务端钩子就宣称完整实时展示已接通；在 area/station/resource/floor 的 _check_space_change(values) 中查询实际排期/有效任务/租约，先 super，再按模型和值决定是否阻止。拓扑变化会向所有受影响后代工位转发 reporting_topology；资源定义及归属变化同样转发。下层不使用 registry 探测未安装模型。

未来上层创建/迁移真实任务或排期时必须在同一事务使用对应 floor._space_lock()，在锁后重读配置并校验。这样配置修改与新任务占用不能检查后竞态穿过保护。真实占用不得从客户端 context 读取；不能用 S02 测试标记判断真实任务。当前只能证明合成钩子拒绝及事务回滚；真实排期/队列/租约联调为 NOT_RUN，分别归 S03/S06。

门店和楼层迁移没有直接入口；显式禁止优于静默迁移。未来如确需带历史的迁移，须在所属阶段定义和验证受控流程。基础绘图没有高级对齐、多选、图层管理、撤销重做。

## 原生及开源核对

实际锁定核心 resource.resource 提供 Human/Material、公司、用户、工作日历、时区；没有诊所平面几何、报到祖先、资源图标权限或能力合成，且 calendar_id 必填。平面图不强建无用途日历、员工或库存。复用原生 ORM、web/Owl、原生列表/表单/权限、S01 业务授权和审计。

只读检索 [OCA resource_booking 18.0](https://github.com/OCA/calendar/tree/18.0/resource_booking) 是资源组合日历预约；[WOOWTECH internal_booking](https://github.com/WOOWTECH/Woow_odoo_internal_booking) 标明 Odoo 18 资源预约。未确认有直接适配本锁定20.0底座和 #26 边界的完整开源平面方案；未安装或拷贝。OCA 方案亦与本计划禁止引入 OCA 冲突。这是当前候选评估，不能声称互联网不存在任何方案。
