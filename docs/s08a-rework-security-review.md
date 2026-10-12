# S08-A 定向返工安全自审

Codex使用odoo-web-guidelines、odoo-guidelines和odoo-security自审；不是GPT独立复核或用户验收。产品增量限 document.js、原QWeb模板和zh_CN PO；未修改Python、ACL、S01—S07产品或数据库事务。

原 [安全审查](s08a-security-review.md) 的模型/source/RPC/CSRF/附件/导出/当前授权实现未改。本轮中间提交在新库重跑过21模型、7HTTP/RPC及16组双连接；调试Firefox实际验证响应丢失/请求未发送/409及本地保留、服务器状态。**新的固定test最终安装因PostgreSQL共享内存分配失败，运行时权限与全量安全回归BLOCKED，不能把中间通过作为最终通过。** 逐项提交和数据库见返工报告。

按技能要求再次扫描完整clinical addon的sudo、SQL、domain、公有方法、route、HTML sink、secret/related、文件、eval/pickle、动态属性、秘密比较、可变默认值、复杂返回；全部命中及判断见 [security-sweep.json](evidence/s08a-rework/security-sweep.json)。既有固定私有模型和当前权限守卫没有放宽。

新增状态提示仅textContent，文书ID转Number后形成固定同源地址；不存在HTML拼接/XSS或客户端提权。核对链接GET只读且仍须原来源读取权限，noopener/noreferrer不向新页传编辑token，不复制正文到URL/日志/浏览器持久存储。待核对原页只读保留文字可复制，用户自主核对再走原合法动作；不增加管理员强抢、回滚已交还或网络异常自动重发。

普通save保留输入及追赶语义；终态冻结内容，提交后再次比较generation和完整内容，不能标记新增未提交文字已保存。不明响应与实际提交成功分开提示，不能把网络错误当事务回滚。原服务器幂等/CAS、独占、作者链、D1/D2在中间模型和浏览器回放覆盖；最终固定test的审计、经济签名及业务升级不变性尚未运行，不能声称成立。

所有数据库及预览限本轮新建S08A合成库；完整marker/端点/cluster/OID/config/data_dir/dbfilter/PID/外发guard不变。所有原失败保留，仓库不提交凭据、token、原始日志或真实病历。S07 SIGSEGV根因未知，生产部署继续BLOCKED；S08-B/C、S09—S13及生产/50会话均未启用。
