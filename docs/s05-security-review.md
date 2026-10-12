# S05安全自复核｜YD-N1 R1

范围：`ydental_intake`最终产品及测试适配；按odoo-security SKILL的全部模式扫描和逐项判断。这是Codex实施方自复核，不是GPT独立复核或用户验收。最终固定SHA及实测结果见[s05-report.md](s05-report.md)。

## 判定与处理

当前自复核未留下已知阻断；以下缺陷在固定最终产品前修正并回归：

|发现|修正与证据|
|---|---|
|原生受管产品/价目可成为普通CRUD旁路|模板/变体/价目/item共享private mutation保护；原生RPC绑定SID，受管读取加入实时来源scope；测试原生改单/复制受管目录均拒绝|
|新业务源未注册S01 RPC binding，合法读被拒、负向检查可能停在缺绑定层|真实_get_sources注册全部S05业务对象，合法HTTP RPC读成功后再测试批量状态write/伪context拒绝|
|换区旧active写未flush即新INSERT，触发唯一约束|target接受后撤旧并flush，再插入新position；数据库唯一索引保留；换区与多连接报到回归|
|旧版UoM API假设、reserved `_register` 方法名不可用|核对实际round/compare和registry保留属性，改为_register_walkin；真实登记/合并登记报到回归|
|只读价目角色可确认演示快照，超出只读授权|snapshot动作实时检查本店price-write；只读页面隐藏确认表单，真实HTTP伪造确认403；最终全套重跑|
|保护原生marker的判定过宽，普通产品复制携带False默认值也被阻断|False非受管默认可保留；已受管对象仍基于真实marker拒普通改写/复制；普通产品/价目复制专项回归|

无借扩大sudo/放松权限来通过测试；没有关闭浏览器sandbox、安全控制或修改系统服务。

## 完整扫描判断

|模式|判断|
|---|---|
|security CSV/ACL|只给入口内部组read，无普通create/update/delete；模型层source domain再次限制门店/业务类。catalog必要集团读取，业务源本店必要角色，price/snapshot本店price；operation仅actor本人。mutex无普通ACL。无public/portal写权限。|
|sudo/with_user/with_company|服务_model仅拼接服务器固定entity字面量；_get校验正整数ID与可信store，控制动作提前鉴权。_native仅固定原生模型和白名单字段，不接受客户端模型/字段/command。native sudo只读取marker/归属判定。merge来源ID来自S04锁定canonical映射；转诊permit是服务器dataclass而非可伪造dict。controller sudo只在price read后读取固定字典和当前店area选项，只输出必要名称。没有产品with_user/with_company。|
|SQL|只有固定advisory锁和mutex UPDATE，两处参数化，表/列不是请求参数；ORM事务内无业务commit/rollback。原生models.UniqueIndex/Constraint用于唯一性。测试探针手工commit只用于其自行打开的cursor。|
|domain injection|不接受客户端domain；服务内部domain全为固定字段和校验ID。source/native读取权限用Domain组合，不能由请求OR扩大。server permit校验完整payload hash，目标store不由客户端context授权。|
|公开方法/RPC|业务动作private；CRUD/export继承公开方法仍做模型权限/token/state校验。native CRUD/copy继承均受marker保护；变体/item不能换到普通父记录绕过。HTTP仅固定动作表，start/derived不能由普通action调用。|
|routes/CSRF|两GET仅业务读取；POST auth=user，保留CSRF，限制32KiB。表单隐藏csrf/key/revision；json payload只作为同一受控动作参数。原生dataset覆写沿用鉴权，不信任客户端binding。|
|XSS|QWeb使用t-out/t-att或原生表单，不用Markup/t-raw/innerHTML。动态患者/目录名称和错误文本按框架输出转义；没有任意HTML、脚本或图形上传入口。|
|敏感字段/related|无认证secret字段，没有跨模型sudo相关字段把患者私有数据带入宽权限模型；显式身份快照保存在有门店必要行政权限的业务来源。原生产品、价目不存病历。|
|附件/内容接口|S05患者行政业务全部加入S04未分类附件拒绝表；公开附件flag/token不能带出患者任务附件。目录价格来源沿S01受保护源内容下载鉴权，不把患者资料塞到产品附件。|
|open/file access|产品不读写客户端路径，不使用open；runner/探针/浏览器只处理新隔离run固定私有路径，校验symlink、创建记录、配置哈希和PID。|
|eval/exec/safe_eval/pickle|产品无命中。JSON解析仅dict；未知参数由签名bind拒绝，不运行表达式。|
|getattr/setattr|产品无动态访问记录属性；没有用户字段选择或富对象返回。|
|token timing|产品不比较认证token字符串；内部mutation对象用`is`判定不可JSON伪造能力，容量permit类型/actor/hash校验。认证和CSRF继续原生处理。|
|默认可变参数|产品无list/dict可变默认参数。|
|返回rich objects|HTTP业务结果只含JSON基本值/ID/状态/版本/演示金额；私有hook可返回record但不暴露RPC。QWeb仅受控来源。|
|撤权/旧页/跨店|每个动作实时S01_check，版本/revision检查；S05业务与原生读取重新绑定SID。真实HTTP覆盖撤权下一请求、只读、跨店取消、源临床任意目标写拒绝及旧revision。|
|合并/事务|patient→supply→intake统一锁序；merge真实活动冲突/迁移不是合成hook替代。位置部分唯一索引，claim来自唯一S03账本。13组真实多连接验证serialization retry和无死锁。|
|价格不可变与恢复|发布区间冲突、原生rule一致性、正价/精度、缺价失败、demo标识和不可变source快照均实测；没有正式费用或隐含生产政策。|

## 实际验证边界

模型/真实HTTP/真实PostgreSQL竞争与适用Firefox均用合成数据、S05专用新库和进程本地外发限制。公开证据不含login/password/token/cookie、业务病历、原始日志或备份。Firefox保持默认sandbox，无关闭安全设置；首次缺本地GTK加载路径的启动失败保留，后用已存在进程本地库完成运行，不安装系统依赖。

正式S06队列/工位、S08/S09临床来源、S10费用和S12文书均NOT_RUN；无生产价格锁价政策。S05全局串行锁未经过S13容量目标验收；不把本轮并发正确性当性能/生产验收。
