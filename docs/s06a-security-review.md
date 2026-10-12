# S06-A 安全自复核

这是Codex按odoo-security技能完成的工程自复核，不代表GPT独立技术PASS或用户验收。范围：ydental_queue及其test-only adapter、HTTP/JS/runner；原S01—S05固定底座仅核对依赖API与锁行为。

|扫描类别|逐项判断与实际控制|
|---|---|
|ACL/多门店|新增lease/entry/execution仅内部入口组r；来源域进一步限制当前有读取权门店，不能跨店源读取/导出。无portal/public权限、无普通c/u/d。门店包含法人归属，S01 membership/session门店为读取与动作边界。token/session绑定字段NO_ACCESS，导出还需既有export write。mutex和测试document无普通ACL。|
|sudo/with_user/with_company|产品sudo仅固定queue entity、字典/工位/配置读取、原生sequence、真实merge适配及受控服务内部写。输入ID先校验当前店与实际holder；所有写值为服务器白名单，不传任意model/domain/vals/x2many。UI读取sudo只列当前店工位及必要队列元数据；不含患者姓名/敏感资料/token。产品无with_user/with_company切换。|
|SQL|产品仅常量advisory锁和常量RR锚点UPDATE，ID参数化；患者/队列读写使用ORM。并发脚本的固定表不变量SQL使用SQL.identifier，业务代码不手工commit/rollback。|
|RPC/状态绕过|业务方法均私有，固定POST适配绑定服务器SID和revision；CRUD由object身份MUTATION拦截，即使sudo不能普通直接改。普通dict/context不能构造Connection/StartPermit；真实HTTP/RPC负向覆盖伪token、另一session/connection、跨店工位、旧revision、直接write、私有方法及敏感字段read。|
|token与时序|token为secrets.token_urlsafe(32)，仅SHA256持久化，consteq比较。actor/session/revision/station/connection共同校验；只读页面不发自动heartbeat，另一登录不获token。超时先处理后返回connection_expired，避免异常回滚导致旧呼叫存活。旧token及旧lease不可复活。|
|撤权/员工/能力|每个持有写动作重验S01业务write、员工active、人员active能力覆盖工位；grant和队列共享RR锚点，锁后重读。grant先提交则下一动作拒；动作先提交只保留已经合法的历史。员工/能力变更沿S03 supply fence失效旧快照。有效lease不构成授权。|
|route/CSRF|GET仅只读；所有动作POST auth=user、CSRF默认开启、16KB上限；不提供强抢/管理员释放动作。实际HTTP包含CSRF缺失400及权限拒绝403。|
|XSS/DOM|QWeb t-out；JS只用textContent输出服务器错误，未使用innerHTML/Markup/t-raw。用户输入未拼接为HTML/JS。静态脚本同源，无外部依赖。|
|附件/文件|queue sources全部加入既有附件阻断源清单，没有任意文件入口。产品无open/eval/exec/pickle/getattr/setattr、动态字段/模型或复杂对象返回。私有server contracts仅返回普通结果或fail-closed。|
|连接失效|只有holder_exit/timeout两类释放原因；calling故障回waiting，不抹更早missed；serving进入verify，execution与旧工位核实仍保留，无自动完成/另一处执行。后台cron不接受目标ID，无远程强抢语义。|
|独立文书|真实文书hook默认fail-closed。Synthetic DocumentSource和编辑锁表仅test模块，库名+环境guard。不能将其冒称真实S08文书联调或生产权限。|
|外发/证据|runner逐次端点/cluster/OID/配置hash/精确dbfilter/PID/端口校验；本进程外发限制、0 cron、SMTP loopback禁用；浏览器仅同源默认sandbox。公开仅合成截图/摘要和hash；密码、login、cookie、token、原始配置/log/备份不提交。|

审计结论：截至当前实现，未发现需要新增业务授权的强抢、跨店写或文书空壳。验证结果与未通过链在本批报告逐项列出。全局串行锁仅证明正确性，性能留S13；真实生产参数与B/C流程仍未批准/启用。
