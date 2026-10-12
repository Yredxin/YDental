# S06-B定向修正安全自查

Codex自查，适用odoo-guidelines、odoo-security、odoo-web-guidelines；不是GPT复核或用户验收。唯一修正边界为#30评论6118213551，原B安全审计继续适用。

|检查|结果与限制|
|---|---|
|现场处理授权|固定两个私有handler；HTTP固定签名、auth=user、POST、CSRF、16KiB；当前店scope、业务write、active员工、精确station/capability/可信资格重验；ID仅用于定位旧execution，station从旧lease派生。没有admin force接口|
|确认与来源|confirmed精确True及必填原因；explicit现场声明不等于远程定位证明。两个出口先默认fail-closed save hook；context/saved字典不可替代冻结来源。合成适配器仅新库guard允许|
|历史与新身份|旧actor/lease不改；execution interrupted→新serving引用旧段，hold保留原引用并另外记录新resolution lease；新token只返回新持有端，数据库仍hash；旧token/其他连接不可复活|
|事务与并发|完整原锁序及RR锚点；保存/文书释放/旧段终态/新lease/新段或continuation/audit同一savepoint；没有产品commit。唯一索引及来源unique不变；两个合格现场人员只允许一次提交|
|患者目标|report/call/start共同检查active/verify hold，来源Care无法普通报到，其他门诊拒绝。初始目标已在reserve服务器确认，额外exam/pharmacy要求可信server hook；客户端不能声明target关系|
|资格与容量|revoke只撤追加例外及号码，open后普通资格恢复；closed仍必须当前有效active permit。没有资格取消/退款/返容量、重复消费或新permit要求|
|sudo/SQL|沿用固定服务器模型及本店过滤；新增字段restrict，历史unlink保护不变；没有新增动态SQL。_service_eligibility只拆出原资格检查供明确现场动作/restore使用，普通_eligibility仍检查actor与patient占用|
|前端|QWeb t-out、JS textContent、显式checkbox/原因表单，操作列表固定；新租约按enter同样存sessionStorage，没有跨连接复制；无innerHTML/t-raw/任意模型执行|
|运行/证据|同scripts/s06b.py新库/OID/cluster/config/dbfilter/PID/端口/外发guard；没有改既有服务/系统安全；新证据独立目录，历史材料只保留。公开只有脱敏事实/哈希/合成截图|

对实际执行verify选择“保存后现场接手”，对hold verify选择“保存后交还续诊”。真实S08保存尚无集成时产品拒绝，两类成功流程由guard保护的server测试来源验证，不声称医疗文书完成。未来真实provider必须在同事务完成保存/释放契约。营业重新open仅测试已有S03合成输入，不扩展S06-C状态机；生产参数、S07库存及真实发药仍未启用。
