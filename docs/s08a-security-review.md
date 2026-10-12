# S08-A 安全自审

Codex 自审，使用 odoo-guidelines / odoo-web-guidelines / odoo-security。不是 GPT 独立复核或用户验收。范围为新 `ydental_clinical` 及其来源/队列/附件继承；既有 S01—S07 只核对调用边界，不改核心/既有产品。最终测试和证据见 [报告](s08a-report.md)。

## 扫描与判定

按 odoo-security 全部模式逐项扫描：sudo/with_user/with_company、SQL/字符串插值、输入domain、公有方法、routes、HTML输出、秘密字段、related、open、eval/exec/safe_eval、pickle、getattr/setattr、秘密比较、可变默认值、复杂返回对象。

|模式/实际位置|判定及控制|
|---|---|
|service `_model` sudo|仅服务端固定 document/version，不接受公共模型名；动作前当前权限/连接，锁内复查，`_document` 约束来源/患者关系；私有 sentinel 后写。读取先检查来源，然后才允许该文书历史的固定域查询。不是直接任意 sudo CRUD|
|acquire env.user.sudo；transfer res.users.sudo|只读目标资格/公司，目标ID先校验；不能把 sudo 身份当责任作者。真实env.uid单独审计|
|controller membership.sudo|固定当前门店/active域；候选还须当前 medical-write、公司、来源能力/可信资格。没有授予权限|
|document init静态SQL|仅本新增表 NULL current_execution 回填为 immutable origin；无客户端值/插值，不碰上游历史；核心 init 的 MRO api.private 禁RPC|
|客户端document/user/execution ID|先强类型ID，固定模型；来源/当前关系/原lease均重新校验；signature白名单拒绝额外参数；不接收客户端 domain|
|公有 create/write/unlink|document普通写全拒绝，version全拒绝改删；只能私有对象sentinel建/改。RPC伪造context bool不能构造对象|
|GET/POST|auth=user；写仅POST且原生CSRF，100000字节限额；no-store；没有 auth=public 或 sudo通用动作路由|
|HTML/JS|QWeb t-out转义，DOM textContent/value/createElement；没有 innerHTML、Markup、t-raw、eval。存储script测试真实HTTP确认转义|
|editor/session/connection/token字段|groups=fields.NO_ACCESS；随机token仅当前取得动作返回，数据库仅摘要；consteq比较摘要，不用==比较秘密|
|related跨模型|本模块无 related 字段；已有 source继承按当前S01/S04授权|
|附件|临床document/version加入原统一阻断模型集合；禁止借ir.attachment/public/bearer导出来源，HTTP/RPC负向覆盖|
|原生查询/导出|复用source当前权限域、缓存重查、目的性care；export同时要求export-write和source-read，成功/拒绝审计|
|文件/反序列化|产品无open/file IO、pickle、eval/exec/safe_eval；JSON仅限定字段数据，禁止可执行上下文|
|getattr/setattr/默认参数|没有动态记录属性名、可变默认值。inspect只绑定私有固定handler签名|
|返回对象|公开HTTP只纯JSON；dataclass/recordset只私有服务端，RPC不能调用 `_` 方法|
|人员/公司撤权|独立文书当前公司、医疗级别、成员/员工active、来源能力/资格、会话版本及lease每次重验；旧token不能继续保存，原生读取也须当前公司范围|
|经济与来源|文书动作无库存/收费派生；S07临床来源及S09外检来源继续默认拒绝，假JSON不能生成真实来源|
|审计隐私|动作区分actor/门店/文书/版本/责任变化；不写临床全文/token。原生source导出保留审计。报告只合成/脱敏材料|

## 负向与并发

实际测试包含 medical-read/无权/跨店/公司丢失/旧门店revision/旧连接、失效租约、当前能力撤销、普通RPC及context伪造、秘密字段、附件/export、CSRF、非法FDI/牙面、存储脚本、编辑者强抢。真实并发用不同 PostgreSQL backend PID、barrier、有限 serialization retry；没有顺序内存调用冒充竞争。保存失败和续诊失败检查文书/接诊/编辑/后继整体回滚。

没有新增管理员 force-release；待完善移交只允许责任人/本店店长同时具备medical-write，目标仍合格，不能抢有效编辑。新作者只签自己能核实的文字，旧作者历史不可替换。正式临床签发资格未批准，本批 confirmed 仅文字确认。

## 隔离与残余风险

测试模块pre_init仅新S08A名字/创建marker/进程环境；runner核对PG端点、cluster、OID、配置SHA、独立data_dir/dbfilter/端口/PID及进程外发限制。测试模块只适用于隔离合成库，不能装业务库。S03演示capacity授权仅该guard模块；一个hold/restore测试显式补合成外检前提，不冒称真实S09。库存回归在rollback测试内设置原生多库位前提，防止原生配置向导归档其他合成价目；没有改动上游产品。

S07历史SIGSEGV根因未知，生产部署继续BLOCKED。本批没有崩溃不证明根因修复/生产稳定。正式字段/签发、阈值、50会话负载、反向代理/WebSocket部署、真实医疗数据与生产发布均未验证。B/C及S09+未启用。
