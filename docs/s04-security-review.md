# S04 安全复核

复核对象为`ydental_patient`，固定产品`eb607750a4b35885f37acfb07d504f758b877b73`；固定测试`a35af92ef89465dbbf71cb6f88297e4c097b43c7`。按本机`odoo-guidelines`及`odoo-security`技能逐文件检查；实际测试及失败链见[s04-report.md](s04-report.md)。这不是外部渗透测试或生产批准。

|检查面|代码与结论|验证|
|---|---|---|
|ACL/写入口|普通YDental用户只有产品源read ACL；mutex无用户ACL。raw create/write即使sudo也需服务器对象token，unlink拒绝；HTTP写由权限/版本/白名单服务执行，管理角色不能通过普通RPC直接写医疗字段|T03/T05/T08，HTTP前台/只读/集团角色|
|行政/医疗分层|patient/contact/partner只存必要行政信息；clinical独立源继承S01域，medical/exam按类别判断；无动态字段权限系统|前台read/search/name_search/count/group/export负向|
|sudo|用于固定ID的存在性、受控partner/身份写、冲突/迁移和审计，不将sudo源直接返回HTTP。service先验scope/membership/角色/归属，持锁重查版本；care路由读附件元数据后按请求用户检查源及所选患者|T05/T06、其他患者附件403、撤权后403|
|partner旁路|owner字段group_no_one，无clinical related字段；普通Notes/write/chatter/unlink阻断。创建不能显式写owner或使用default_owner伪造；受控新建清除default_*，关闭tracking和订阅|T05普通联系人读取/反向导出/默认context负向|
|附件/原生下载|行政患者和其partner的无类型附件不可建立/读取/搜索/下载/改挂；clinical附件按源鉴权，缓存数据read/fetch也重新鉴权。public/access_token不覆盖源权限；原生limited-field HMAC返回sudo后重新绑定请求用户检查，允许的受保护下载补记source.download|T05普通、公有、HMAC路径；医疗允许下载与审计、其他scope/撤权拒绝|
|可信care|不可由JSON构造的PatientCareScope包含真实canonical患者、user/session/revision/store/purpose；每次重新核实权限和患者。仅read域扩展，settlement不扩展；外店医疗write永不扩展|T06伪context、另会话、撤权、跨店写及合成财务负向|
|SQL/事务|两条SQL均固定语句并参数绑定，仅 advisory lock 和mutex UPDATE，无用户标识符拼接。revision写迫使旧RR快照重试；服务无手工commit；回执与业务同savepoint。合并钩子异常整笔回滚|7组真实连接竞争、T04迁移中途抛错及引用/回执核验|
|公共RPC/反射|服务及hook均以下划线私有；唯一公开业务adapter使用固定动作dict，无客户端model/method/field路径反射，无eval/getattr任意调用|raw CRUD/context负向及HTTP白名单|
|HTTP/CSRF/XSS|auth=user，POST保留CSRF，32KiB，数值revision与SID绑定；QWeb使用转义输出，无Markup/t-raw。GET不建关系/到店/合并；care GET留审计。响应no-store|实际HTTP CSRF400、权限403、stale409、无效用途422及Firefox|
|外发/隐私|建档无res.users/mail.message/mail.mail副作用；运行cron0/list_db False/精确dbfilter及进程socket/DNS外发限制；凭据/config/log仅.local私有。截图前检查页面可见凭据及浏览器cookie，不发布原始日志|T08、隔离guard5项、截图哈希清单|

本轮先后发现并修复：附件已缓存raw读取、原生HMAC早退、default上下文及附件改挂路径。原失败结果保留，不将早期失败版本称为通过。最终适用用例结果以最终运行证据为准。

边界：插件开发者/超级用户/服务器代码不是不可信客户端，可调用私有服务；未来上层必须先鉴权、先取得患者fence再取业务锁，并注册固定来源，不允许用客户端活动清单替代权威查询。尚未安装S05/S06/S08/S09/S10/S12，真实活动、医疗原件/财务/PDF的安全复验为NOT_RUN。测试模块包含仅供隔离库的合成活动/签署/财务模型，不得用于生产。
