# S07 返工字段、动作与错误增量

全量原生映射、产品/单位/库位/批次/来源/权限字段仍见 [原字典](s07-data-dictionary.md)。本轮仅 `ydental.inventory.event` 新增以下两字段，没有另建余额、临床事件或费用单。

|字段|实际类型|必填/默认/删除|写入者及边界|
|---|---|---|---|
|ydental_correction_id|Many2one(ydental.inventory.event)|可空，默认False，ondelete=restrict|仅受控recover，原pending之后本店同lot/目标库位的done receipt或正向inventory；普通CRUD拒绝|
|ydental_reconciled_at|Datetime（UTC）|可空，默认False|仅受控recover，记录补记时服务时间；不覆盖ydental_actual_at|

`ydental_actual_at`、`ydental_actor_id`、`ydental_responsible_id`、`ydental_price_snapshot`、`ydental_source_*`、批次、数量及换算快照均沿用原字段，在恢复中不修改。原native move是数量事实，move执行时间与原actual_at各自保留。原记录需新的纠正关联时只通过合法恢复产生；升级不批量回填/更改原事实。

|动作|鉴权/状态|新增检查与效果|幂等/异常|
|---|---|---|---|
|_source_action（私有）|可信hook、当前店、medical-write或prescription的pharmacy-write|treatment→material，chairside/prescription→medicine；event/move创建前强制|不匹配完整回滚；同合法来源返回原event；无public来源入口|
|recover（固定操作）|当前店warehouse-write；原pending临床事件|摘要/原价/原时间/类别确认，余额足够，真实纠正事件顺序/店/批次/库位/native状态匹配；只该历史补记不检查当前启停效期|原event唯一move；done重试返回原move；事务失败原pending无半账|
|issue/新临床执行/退回release|原固定权限及当前有效批次|继续_usable，禁止过期/停用新执行|本轮不放宽|

|错误码/HTTP（原controller）|结果及人工出口|
|---|---|
|source_category_mismatch /409|来源类别错误，无库存副作用；核查真实来源，不从UI绕过|
|recovery_unconfirmed /409|原事实不能确认，保留pending/负责人，人工核查来源与数量|
|recovery_evidence_required /409|无合格真实纠正，保留pending；先凭证据实际入库/正向实盘|
|insufficient_balance /409|物理余额不足，保留pending；不伪造入库|
|lot_expired、lot_disabled /409|新执行/退回release仍拒绝；历史补账不改效期或启用标识|
|access_denied /403|无当前门店warehouse-write或来源业务写权，原权限边界继续|

`inventory.recovery` 审计after补充 correction_id、actual_at、reconciled_at，保留event/move和当前操作者，原记录不可普通改删。请求receipt继续记录reason及参数fingerprint；S07不解释自由文本为患者/临床/入库真实性证明。
