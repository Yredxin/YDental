# S07 工程契约｜YD-N1 R1

唯一需求/授权：[总计划#23](https://github.com/Yredxin/YDental/issues/23)、[#31正文及GPT-ACTIVATE6119956887](https://github.com/Yredxin/YDental/issues/31#issuecomment-6119956887)。技术上游固定S06-C `46833f0ac4bd37b778f3a5a80d51be430e4ebde6`；不得以本文另立业务计划。最终提交及真实结果见[s07-report.md](s07-report.md)。

## 原生事实、门店和单位

新增真实模块 `ydental_inventory`，直接依赖锁定底座的stock/product/uom/product_expiry及现有access/intake/queue。核心固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，源码声明20.0；这是fork，不冒称已核对同SHA官方上游。未引入OCA、purchase或account；本批实际采购收货用有证据的入库动作，未建设采购订单或应付账款。

库存数量唯一事实是 `stock.quant` 和已完成 `stock.move`/`stock.move.line`，效期使用原生 `stock.lot.expiration_date`。业务事件仅关联原生移动、来源、单位快照、责任人和恢复状态，不维护可手工改写余额。调用实际API为 `uom._compute_quantity(round=False)`、`uom.compare/round`、`stock.move._action_confirm(merge=False,create_proc=False)`、`_do_unreserve()`、显式lot/quantity的move.line及 `_action_done()`。原生确认可能建立未指定lot的建议行；只撤销本次未完成建议/预留，再填实际批次，既有已完成流水不删。

每店单独原生warehouse，company来自门店法人；药房、耗材、义齿待取、退回待核查为互不相同的internal库位；另有该店supplier/customer/inventory虚拟来源/损失去向。所有动作由类别选择固定库位，不接受任意location/company/model/domain输入。退回待核查不进入可发量。

同法人调拨是一条真实native move，保留厂家lot ID；`ydental.inventory.batch`只记录store×native lot的启停、首次实际入库时间和预留稳定加工来源引用，没有余额字段。目标门店建立自己的batch生命周期；目标启停不影响源店。入调拨流水可在目标店工作台读必要信息；源店业务变更仍受源店动作限制。跨法人调拨直接拒绝，真实成对交易留S10。

Odoo20该fork的UoM是relative_uom_id树、factor和Product Unit全局decimal.precision，没有旧版本uom.rounding/category_id。库存与领用单位必须同一单位树，执行只接受这两个明确配置单位；先不舍入换算，再校验原生精度和产品最小粒度，不能表达的数量报precision_error，禁止截断。已引用单位及祖先换算/停用不可普通修改。历史event冻结输入数量、输入单位、factor、库存单位、digits、stock_step。产品单位/类别/粒度建立后不提供普通改写入口；需要不同物资定义时另建主数据。

## 权限与范围

- 集团产品主数据：现有group manager + 当前可信登录门店/允许公司；不要求price或warehouse授权，也不授予库存数量读取。catalog专页仅投影产品必要字段。
- 本店warehouse read/write：本店工作台/数量批次动作；price、medical、pharmacy和warehouse相互不继承。原S05价格动作保持原权限。
- 治疗/椅旁耗用：可信来源hook + 当前medical-write；处方带走药：可信来源hook + pharmacy-write。不用给医生/药房通用stock或结算管理组。本批只有严格隔离合成适配器，未建设真实临床/处方/药房任务。
- 所有写动作检查server-bound session、旧页revision、实时membership/员工启停和S06全局执行门店fence。同法人跨店也检查目标warehouse-write。撤权下一请求生效。
- 工作台投影必要执行摘要，没有患者ID、完整病历、附件或任意来源文书。库存源附件及原生批次/流水附件封闭；patient/partner原生读取继续受S04保护。
- YDental用户不得通过原生stock RPC、search/read/export、库存盘点向导或stock manager组旁路工作台。受管product原生读取也封闭，避免sudo计算全集团库存/预测量泄漏。其他原生库存使用者只能访问未受管对象；受管对象及关联库位/产品写入还需不可由JSON构造的服务器object token。
- 源模型有group-less法人restriction及当前门店动态domain，普通create/write/unlink/import拒绝。export额外需要S01 export-write和原对象读取；业务历史不可普通删除。

## 来源、幂等和事务

请求回执唯一范围为store×key，保存操作/参数指纹；相同请求返回already_accepted，参数不同version_conflict。来源事件另有store×namespace×source_key数据库唯一约束；不同请求键指向相同来源仍只一个事件/移动。来源一旦冻结，数量、批次、种类、原价格、费用关联不得换参。部分收货/发出应使用对应真实部分事件的稳定source_key，不能把总单号重用为不同数量的请求。

统一库存事务顺序：可信session写锁→inventory advisory fence→mutex UPDATE→重新读取实时授权→来源/原生库存。mutex UPDATE使REPEATABLE READ竞争者得到serialization failure，框架重试整请求；探针用独立cursor有界重试，不在业务方法commit。此阶段采用单一库存fence以简化原子性；50会话吞吐与生产锁粒度调优未实测，不作性能承诺。无S01/S03/S04/S05内核重写。

每个普通动作在savepoint中完成原生流水、事件、回执及S01审计。库存不足/非法批次/下游原生动作失败回滚整动作；不存在半move、半quant、半成功审计。失败的HTTP动作返回错误，不把失败描述为已入账。审计查看/导出继续使用S01。

临床来源使用私有 `_source_action(source)`→`_authorize_source(source)`。产品默认AccessError，客户端context/payload不能启用。S08未来必须继承私有hook，验证实际来源对象、actor、store、来源分类、实际是否发生、确认批次/用量、原价格快照及稳定执行事件唯一键，再返回服务端payload。该接口不创建临床事实/处方/费用。合成适配器要求不可由RPC构造的frozen SyntheticSource、匹配actor/store及严格S07新库/进程guard；命名空间固定s07_synthetic_execution。椅旁和带走处方同一来源换kind被不可变指纹拒绝，不能把椅旁已用量再派生待领处方。

## 退回和恢复

实物退回仅可关联实际已完成的补货领用/带走处方来源，累计不得超过已出量；治疗耗用及椅旁已用药属于已消耗，不能作为未用实物退回。退回第一步仅移动customer→quarantine，可发量不增加；核验按实际release到业务库位或discard到损失去向，累计不得超过退回剩余。release要求当前有效产品/本店批次和效期；退款无库存动作，不能自动回库或新增处方余量。

可信already_performed来源库存不足/批次停用或过期时，原事件保留pending、原作者/原价格/费用引用/责任人，无虚假入库和移动。责任人查核后，仓管用有证据的receive或inventory修正真实原生账，再recover原event；stock满足且批次可用才补一组移动，done后重试原ID/原move。恢复不调用新治疗来源，不取当前价，不造费用或退款；S07只冻结应有费用关联，真实S08/S10费库款联调NOT_RUN。原批次仍不适用时继续待核对，不强行释放。

## 动作表

所有库存动作基于当前store，key为必填短字符串；HTTP写入口 `/ydental/inventory/action`，POST/CSRF，业务方法私有 `_operate`；原生RPC不得调用私有方法。

|动作|主要输入|权限/前置|原子结果与审计|失败与恢复|
|---|---|---|---|---|
|setup|code≤5字符|warehouse-write；门店有效|唯一warehouse/config/七类去向；inventory.setup|已有返回原配置，不接管其他仓库|
|policy|near_days/wait_days/low_quantity/reason|warehouse-write；配置存在|显式非负策略/版本；inventory.policy|未配置不默认预警数字|
|product|code/name/kind/stock_uom_id/issue_uom_id/step/specification/suggested|集团主数据权限；唯一code；兼容单位|原生storable product、lot追踪/效期；inventory.product|定义不合法拒绝，不影响价格|
|product_edit|product_id/name/active；可选specification/suggested|集团主数据权限|受控主数据启停/说明；inventory.product_edit|不能换类别/单位/余额|
|lot|product_id/name/expiration UTC|warehouse-write；本店已配置|原生lot + 本店batch；inventory.lot|厂商lot唯一由原生约束；无入库数量副作用|
|lot_edit|lot_id/enabled/reason|warehouse-write；当前store有batch|只改本店batch；inventory.lot_edit|不改他店状态和原效期|
|receive|lot_id/quantity/uom_id/source_key/reason|warehouse-write；真实来源证据|supplier→类别internal，首入时间；inventory.receive/movement|来源重复返回原事件；不制造临床完成|
|issue|同receive|warehouse-write；有效批次/足量|补货领用internal→customer；inventory.issue/movement|不足/过期/停用全回滚|
|inventory|lot_id/counted/uom_id/source_key/reason|warehouse-write；无reservation/owner/package冲突|实际数差额→原生is_inventory move；无差额observed来源；inventory.inventory|不伪造采购入库；原count重试不重置后来的余额|
|transfer|lot_id/quantity/uom_id/target_store_id/source_key/reason|两店实时warehouse-write；同法人不同店|一组native move及目标batch；inventory.transfer/movement|跨法人或目标无权拒绝；事务内无半调拨|
|return|event_id/quantity/uom_id/source_key/reason|warehouse-write；未消耗实际issue；累计限额|仅实退→quarantine；inventory.return/movement|不自行增加可发量|
|verify|event_id/quantity/uom_id/disposition/source_key/reason|warehouse-write；真实return剩余；release批次有效|quarantine→业务库位/损失；inventory.verify/movement|累计核验互斥；不能超退或把过期药放回可发|
|recover|event_id/reason|warehouse-write；本店pending；真实修正后足量|原event绑定唯一native move，原快照不变；inventory.recover/recovery/movement|不足仍pending，无半成功；done重试只返回原move|
|_source_action|服务器可信来源对象|hook验证+medical/pharmacy-write|新执行入账；已发生缺料持久pending；inventory.pending/movement|HTTP字典、错误actor/store、来源换参拒绝|
|scan|code+revision|warehouse-read；POST/CSRF|仅识别：unsupported_source/received=false|S11未接入不得报告入库成功；识别码不授予操作权|
|dashboard/catalog|当前可信session|warehouse-read / 集团master|scope投影、inventory.view|无权/撤权拒绝，无临床/附件读取|

## 状态、错误与配置

|代码|含义/副作用|恢复|
|---|---|---|
|accepted / already_accepted|已受理 / 同请求原结果|继续原来源，不再扣库|
|pending / done / observed|待核对 / 原生库存确认 / 实盘相符无移动|pending找到原事件；observed保留实盘证据|
|access_denied|角色、门店、来源或原生旁路被拒|有权人员从合法入口操作|
|version_conflict|旧页或幂等参数/来源冲突|刷新或恢复原来源参数|
|configuration_required|未配置本店仓库|合法setup，不接管旧仓|
|precision_error|数量不符合换算/粒度|按实际单位和精度确认，不能截断|
|insufficient_balance|可发不足，无新执行移动|核查真实库存；已发生事件仍pending|
|lot_disabled / lot_expired|本店批次/产品停用或到期|停止新执行；有证据核查原事件|
|inventory_conflict|reservation/owner/package未解决|先处理真实预留/代管事实再盘点|
|inventory_error|原生移动未成功结束|整事务回滚；原来源重试|
|return_invalid / return_limit|不是可退来源或超过实物限额|查原实退/出库，不自动退款/增库存|
|unsupported_source|上层加工来源未接入|留S11真实来源适配；无入库副作用|
|Recovery requires an original pending execution event.|observed盘点等非pending临床事件不能恢复；本地化消息/409|选择原待核对执行事件；无库存副作用|

预警默认未配置；近效期/待取天数、低库存数量须显式填写并保留reason。工作台演示near=60天/wait=0天/low=3（产品库存单位）；当地日期边界另测wait=1天/low=0，不是生产批准。低库存按本店该产品所有有效批次可发量汇总判断；工作台区分实存、可发、待核查。义齿待取从本店第一次真实入库/调入UTC瞬间转换门店当地日期开始，不使用临床完成日；已有时间不被重试重写。停用/过期批次实存仍可见，但可发显示0。

扫码接口、费用关联及稳定加工来源引用是S07实际接口边界；未装真实S08/S10/S11来源时默认失败/unsupported，不能用合成适配器作为生产集成。回滚方式及验证限制见报告。
