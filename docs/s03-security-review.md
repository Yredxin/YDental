# S03 作者安全自查

按已读 odoo-guidelines 与 odoo-security 对本次产品、测试适配器和工具逐项扫描。这是作者自查，不冒充独立 GPT 复核。最终版本与实际运行结果见 s03-report.md。

|检查项|判断与证据|
|---|---|
|ACL/记录域|仅YDental内部组r；源域每次检查当前门店/有效人员/capacity；没有everyone/portal/public写权限。private mutex无权限授予。法人由已核实门店及employee.company_id关联，不依赖浏览器公司选项放宽源域|
|CRUD/状态/导入|supply.record create/write需object token；JSON true/dict不能伪造；unlink拒绝，event拒绝_save。测试含原生HTTP write/context伪造及撤权下一请求|
|公开方法|产品服务只有私有方法；无公开容量消费动作；HTTP控制器固定operation白名单。原生read/export仍经源鉴权。测试适配器同样只有私有方法|
|sudo|固定supply/space/access/native员工假期模型的已授权门店/本人或配置反向引用读取；_new仅服务端构造字段/已校验ID；没有sudo.write(post)、任意模型、任意域或客户端关系命令。event独立保留真实actor|
|SQL|仅固定advisory锁和固定mutex ID参数化UPDATE。S02稳定floor/station锁沿用。没有SQL字符串插值/动态客户端标识或业务commit|
|事务|动作savepoint包括账本/回执/资格及新占旧取消；SerializationFailure整事务重试。probe自己创建独立游标并明确提交，不能套用生产env.cr提交|
|HTTP|所有路由auth=user；写仅POST，CSRF开启，大小上限65536；旧页revision绑定SID；readonly/跨店/旧页/私有RPC/CSRF模型HTTP验证|
|XSS|QWeb t-out，常量模板；无Markup/t-raw/innerHTML/eval/exec/pickle/getattr动态字段，无产品JS新代码|
|导出/附件|登记S01来源；原生export需export写与源读取，不单独创建匿名下载路由。原生公共审计不允许普通改删|
|演示隔离|生产source adapter默认拒绝；生产allow_demo_supply=False；测试适配器库名+runner环境双检查。测试模块不得部署生产，不把合成消费/清队计作真实联调|
|工具/凭据|runner端点/集群/OID/config hash/dbfilter/port/egress保护；未用系统依赖安装、服务重配或业务库。随机访问凭据私有0600；仓库仅合成截图/摘要/哈希，不含原始日志/cookie/token|
|外发|SMTP拒绝端点，cron0，Python进程网络只允许已批准PG和独立HTTP；浏览器只放行本预览端点；没有测试短信/正式邮件送达声明|
|复杂对象|私有模型函数内部返回record是Odoo内部用法；HTTP返回JSON基本类型或渲染响应，不暴露crypto/backend/file句柄|

已重点复查取消与consume互斥、动作幂等与来源唯一、共享能力最后份额、改期/重配失败原值、配置丢失后暂停新增保留资格、演示配置真实销售门禁。未发现尚未处理的本阶段阻断；仍须GPT针对固定提交独立复核。

能力边界：真实源对象鉴权、真实预约与报到、队列空检查、执行资格/租约和跨日清理尚未接入，NOT_RUN。S03只有服务器契约与合成数据库/HTTP/UI验证，不以这些测试替代S05/S06真实集成。
