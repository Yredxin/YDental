# S06-C 安全与事务自审

按 odoo-guidelines、odoo-web-guidelines、odoo-security 实际材料自审。范围为固定 B baseline 后 C 改动；这是 Codex 自审，不能替代 GPT 技术复核/用户验收。需求来源仅 [C 启用](https://github.com/Yredxin/YDental/issues/30#issuecomment-6118760114)。结果证据见本批报告及 evidence/s06c。

|检查面|实现与实测结论|
|---|---|
|营业权限/跨店|真实复用 S03 capacity-write+S01 session 当前门店，无 group-manager sudo 旁路；HTTP 未授权/旧版本拒绝，普通 CRUD/context 不能伪造 Python mutation capability|
|锁序/RR|营业入口在 S03 动作前完整 patient→supply→intake→queue；queue/report/cleanup共用原锁；所有业务失败savepoint回滚；真实多backend/barrier/先后锁竞争，deadlock=0|
|跨日历史|同task/day唯一，旧身份字段不可变，unlink拒绝；新日显式资格+到店报告，旧entry独立保留；execution追原段；真实 -u 检查旧约束移除、missed回填、旧identity保留|
|清理持久性|只结束目标日未开始段；资格/claim/余额不变，serving/verify/hold不动；唯一水位最后同tx写；失败/两worker/delayed今日保护实测|
|bus事务性|读取锁定原生 precommit bus行/postcommit notify；typed QueueNotice延迟重验outbox；flush=False savepoint与整txrollback实测无成功事件；实际bus版本精确对outbox|
|最小推送|payload仅store/area/version；随机channel不授予snapshot/员工登录/业务写；不含患者全名/电话/临床/金额/凭证|
|screen credential|32随机字节，digest唯一，NO_ACCESS无普通ACL；明文一次返回，fragment清URL、Authorization header、no-store/no-referrer；不写Git/截图/审计；跨store管理拒绝|
|撤销/撤呼RR读|真实竞争暴露旧快照问题后已加token/scope FOR SHARE；revoke-first/retract-first令旧RR请求重试，下一授权请求按当前DB；screen读不再申请前级锁，避免反向锁序|
|脱敏/XSS|helper去空白/不可见C类，只保留首可见字符，单字符*；snapshot白名单无raw patient/task ID；DOM textContent，无Markup/innerHTML；语音number+calling lease station|
|实际工位/settlement|呼叫/语音来自有效lease.station；测试容量来源station与实际calling不同；service kind白名单和业务call类型校验，settlement screen credential拒绝|
|HTTP/CSRF|业务POST auth=user原生CSRF，screen仅public GET只读；不从query收token；错误generic403；scope完全由digest绑定，不能请求任意area|
|凭证存储/附件|沿用A/B租约NO_ACCESS/受控附件边界；新摘要/channel禁止read/export；private .local访问文件0600，截图先检查可见凭证，不提交原始运行日志|
|时钟/合成来源|生产用server UTC投影门店IANA；冻结时钟/保存/目标来源均测试模块 guarded frozen对象，JSON/context无法构造；新C库guard先验证记录/OID/cluster/config/PID/端口/外发|
|A/B连续性|原A/B资格/能力/hold/verify/lease/history/append核保持；真实A21+B16与Firefox原83项连续回归；默认保存仍fail-closed，不伪造真实医疗完成|

两类读fence的线性化语义：snapshot先获得SHARE可先返回，其后撤销/撤呼才提交；撤销/撤呼先提交，旧snapshot重试且不能返回旧calling。对撤销前已取得的最小版本channel，后续可能仍收到不含患者信息的scope/version；每次snapshot/events仍必须凭active摘要重新授权，客户端下一轮询拒绝后清屏/断开。channel不是可读队列凭证。

本批不新增 raw SQL 注入入口：新增固定 SQL 仅升级旧missed回填、固定表主键 FOR SHARE；ID用参数绑定，不拼客户端表名/字段。私有 `_model(entity)` 的实体均server literal。无eval、pickle、动态getattr、文件下载路径、任意模板执行、任意store/context信任。test脚本独立游标commit属于其自己创建的合成事务，产品无手工commit。

遗留部署边界：生产heartbeat/timeout/N尚未批准；上线WebSocket代理与worker/cron频率/50会话性能未验证；S07库存、真实S08保存/文书/发药、S09结果、S10收费、生产发布 NOT_RUN。以上是启用范围明确排除，不将合成测试称为生产通过。
