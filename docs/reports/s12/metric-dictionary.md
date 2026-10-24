# S12 指标字典 / 软件口径 v1

这是可审查的软件统计契约，未代替正式经营口径发布。查询只读原业务，不生成费用、库存、收退款或第二套账本。时间条件是门店当地业务日闭区间；页面显示各店时区和对应UTC半开区间。币种、项目和数量单位各自分组，无汇率合计、收入确认或完整毛利。

|指标key / 单位|公式、来源模型及字段|事件日期 / 状态与排除|范围与钻取|
|---|---|---|---|
|unique_patients / 人|实际arrival对应patient沿ydental_merged_into_id取canonical后distinct|ydental.intake.arrival.ydental_date；只真实到店，不用预约/任务|每店独立及所选授权门店联合distinct；不能相加门店人数。钻到构成arrival，当前合并影响当前统计，旧PDF不变|
|arrivals / 次|count(ydental.intake.arrival.id)|ydental_date，保存的ydental_timezone/occurred_at可回源；跨区域同arrival一次|前台/医疗/检查源读取，按授权选店、法人、当地日期；钻arrival|
|executions / 执行事件及项目单位|confirmed treatment.event，按catalog/uom/kind分别sum(quantity)和count；correction单列符号数量|ydental_business_date；排除pending、订单/草稿；prescription显示实际发药，不能当治疗项目|逐店实际medical/exam/pharmacy类别源读取，页面和导出明示纳入类别；钻实际事件/来源文书/价格快照|
|original_billing / 币种金额|所选店settlement.source引用posted out_invoice去重后sum(amount_total)|account.move.invoice_date，原出账正数；不扣冲销，不重定价|settlement；钻原生invoice及source/fee/charge|
|credits / 币种金额|posted out_refund的amount_total正数单列；由本店source、实际refund关联或实际native partial.reconcile连到本店原账单确定；origin文本只在已获权候选内精确定位，不能作为授权|invoice_date；排除draft/cancelled，贷项不冒实退|settlement；钻credit及原bill关联，输出显式original_bill_ids|
|collections / 币种金额|sum(settlement.payment.ydental_amount)，必须有posted原生付款分录|ydental_business_date，actual_at/entered_at/cashier/channel回源；不把生成凭据当收款|settlement；钻offline确认及原生payment/所选invoices|
|refunds / 币种金额|sum(settlement.refund.ydental_amount)，state=done且native_payment实际posted|ydental_refund_business_date优先；历史NULL用actual_at当地日并逐行标来源；两日期都无则明确拒绝完整统计，actual_at/executor/channel；跨日不改收款日|settlement；钻refund及payment/credit|
|approved_pending / 当前币种金额|当前approved/failed/unknown且未done的refund金额|查询时点快照，按requested_at当地日筛选可追溯请求；历史NULL用create_date当地日并逐行标来源；requested/rejected/cancelled与done排除|settlement；批准待执行不是实退；钻refund|
|receivables / 当前币种余额|posted本店out_invoice当前amount_residual，逐单核receivable与partial.reconcile|查询时点快照；日期仅限定原账单群，非历史截至日余额|settlement；钻原bill及核销；不用期间收款相减替代|
|consumption / 产品-批次-单位数量|inventory.event state=done、kind=treatment/chairside/prescription且move.state=done，sum(input_quantity)按product/lot/uom分组|actual_at按门店时区；排除receipt/replenishment/transfer/return/inventory/verification|warehouse；钻event、native move、lot及原执行关联；返还与损耗不混|
|lab_pending / 当前单数|lab.order当前sent/processing/received/available/rework_returned，按状态分列；父周期被非cancelled child承接后不再计父责任；child的done/exception不使旧父重新待交付；取消child时保留真实返厂父责任|查询时点快照；planned_at当地日期限定来源群；draft/done/cancelled/exception排除|medical源读取（warehouse单独权限不授予完整工单统计）；钻cycle与父子关系|
|followups / 当前待办数|followup.state in planned/to_notify/notified，按状态/负责人/lab_contact_stage分组|查询时点快照，planned_at当地日期；done/closed排除，waiting明确“待加工库存”，不冒可联系|followup；钻plan/来源event/预约真实状态|

页面、分页、钻取和CSV使用同一个过滤结果和公式。每个请求重新核活跃内部身份、会话revision、公司、每一选店的membership/employee/对应业务类别；跨店报告是有逐店源读取授权的必要投影，原业务页面仍需按正常门店选择后读取，不能凭报表链接绕过。无源读取即使有export也拒绝。币种筛选仅适用金额指标，其余指标明确拒绝，不能默变0。CSV再要求各选店export write；单纯浏览报表不授予导出。拒绝未授权选店，不静默缩小成假集团范围。

分页不改变聚合。为保护交互请求，每个来源集合上限50000条，超限明确要求缩短日期或门店，不能返回截断总数。此界限须以明确合成规模核验，不构成50并发/生产性能承诺。查询日期、门店、法人、币种、状态和快照时间随页面/导出保存。
