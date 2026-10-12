# S07 定向修正工程契约

唯一修正依据为 [GPT-REVIEW6121445246](https://github.com/Yredxin/YDental/issues/31#issuecomment-6121445246)。原 [S07契约](s07-contracts.md)继续适用，下列补充替代其恢复路径中按当前批次可用性拒绝历史补账的描述。没有建设真实S08来源或S10费用凭证。

来源类型必须在私有可信来源、当前会话和 medical/pharmacy-write 验证之后，event/native move 创建之前匹配真实产品：treatment→material；chairside/prescription→medicine。prosthesis没有已授权的临床耗用组合。上层hook/UI不能替代该校验。非法组合报 `source_category_mismatch`，整个savepoint回滚，没有event/move/quant/audit副作用。

新执行继续经 `_usable` 检查当前产品启用、门店batch启用和当前UTC效期。普通issue、临床新执行、transfer及退回release未改变。可信 already-performed 来源不能因此消失：不能即时记账时仍保留原pending事实，不自动补记。

`recover(event_id, reason)` 仍须当前店warehouse-write、可信S01会话/版本/实时授权与库存事务fence。仅原pending且kind合法、非warehouse来源命名空间、存在必要来源摘要、原价快照及不在未来的原时间，才可历史补账。pending在现有模型中只能由可信already-performed路径产生；普通RPC不能创建/改写它。旧格式pending无需重新造来源或改价格。不能确认时保留原pending及负责人，通过工作台人工核查原来源、数量和实际纠正证据后再重试。

可用物理余额必须足够；必须存在本店、本lot、目标为原耗用库位的实际done receipt或正向inventory纠正，原生move也必须done，纠正来源库位非internal，纠正事件ID大于原pending且创建时间不早于原pending。库存fence保证创建顺序；仅时间比较不足以排除同秒旧收货。服务按ID倒序选择最新符合条件的纠正并固定关联，不把自由文本当作库存。缺证据报 `recovery_evidence_required`；来源不能确认报 `recovery_unconfirmed`；缺余额仍报 `insufficient_balance`。

只有该原pending历史补账路径不调用当前 `_usable`。不改lot效期、不启用batch、不新造治疗或入库。原event ID、来源、批次、数量/换算、价格版本/金额、费用引用、原actor/responsible和actual_at保持。native move在补记时实际完成，`ydental_reconciled_at`记录补记时间，`ydental_correction_id`固定真实纠正事件；S01 `inventory.recovery`同时记录actual_at/reconciled_at/correction_id/move_id及当前操作者。价格不重取。

已done重试返回原event/move；并发恢复在既有advisory+mutex fence内重试，唯一原move。任何native异常回滚move/quant/状态/纠正关联/补记时间/审计/请求receipt；原pending不丢失。没有伪造费用单，S08/S10联调NOT_RUN。

|新增字段（ydental.inventory.event）|类型/约束|含义|
|---|---|---|
|ydental_correction_id|Many2one自身；readonly；restrict删除|恢复时自动固定的真实入库/正向盘点纠正事件|
|ydental_reconciled_at|UTC Datetime；readonly|历史库存补记时间；与原actual_at分开|

两字段受原模型服务token和S01 CRUD域保护，普通管理员/RPC也不能伪写。升级只新增可空字段，不回填或重写历史业务事实；持久数据真实升级验证另见报告。降级/卸载须先审查新纠正关联，不通过删流水/改quant抹账。
