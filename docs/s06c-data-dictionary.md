# S06-C 数据字典与动作表

来源为 #30 [S06-C 启用](https://github.com/Yredxin/YDental/issues/30#issuecomment-6118760114)。本字典补充原 A/B 与返工字典，不复制已有字段。模块 `ydental_queue` 版本 `20.0.1.2.0`，直接依赖新增原生 `bus`，许可证保持原样。实现/事务细节见 [契约](s06c-contracts.md)，固定提交与证据见 [报告](s06c-report.md)。

## 公共字段与权限

新增四模型都继承 `ydental.queue.record` → `ydental.access.source`：`name` Char 必填；`ydental_store_id` 必填当前事实归属门店、restrict；category 默认 medical（cleanup 明确 capacity）；`ydental_version` Integer 必填默认1、受控 `_save` 增加；create_uid/date/write_uid/date 为原生审计元数据。法人由既有 store 关联，不创建第二法人来源。无患者字段、金额/单位/币种字段。

新模型没有普通 ACL，所有普通 create/write/import/RPC 拒绝；服务固定实体 sudo 读取/受控 mutation capability 写入。普通 unlink 拒绝历史删除。digest/channel 为 `fields.NO_ACCESS`，不允许普通 read/export；页面 DTO 手工白名单，不把 record/read 全量返回。普通匿名/portal 无模型读写，唯有效屏凭证可取绑定区域最小 DTO。

## 新模型字段

|模型/字段|类型/关系/默认/空值|来源/归属/敏感性|唯一、保留与更正|
|---|---|---|---|
|ydental.queue.cleanup.ydental_business_date|Date，必填，有索引|门店当地待清理日，server cutoff 选择|与 store/type 唯一；成功事实保留|
|cleanup.ydental_timezone|Char，必填|执行水位时门店 IANA 时区快照|不回写旧 entry 时区|
|cleanup.ydental_cleanup_type|Char，必填，unstarted_v1|固定服务版本|store/date/type 唯一；不是客户端策略|
|cleanup.ydental_completed_at|Datetime，必填，naive UTC|server 实际处理时间|与清理同事务成功，失败无水位|
|cleanup.ydental_entry_ids|Many2many queue.entry，readonly，可空|本水位结束的 waiting/calling ID 集|历史引用保留；空日也可记水位|
|ydental.queue.scope.ydental_area_id|Many2one space.area，必填 restrict|固定业务事实门店所属区域|store/area 唯一|
|scope.ydental_channel|Char，必填，NO_ACCESS|32字节随机 channel，不是业务/屏凭证|仅版本通知 transport，模型普通不可导出|
|scope.ydental_version|复用受控 Integer|同 scope 已提交版本|单调递增，rollback 不推进已提交值|
|ydental.queue.outbox.ydental_scope_id|Many2one queue.scope，必填 restrict|发生变化的 scope|历史保留|
|outbox.ydental_scope_version|Integer，必填|本次 scope 版本快照|scope/version 唯一；与事实/bus 同事务|
|ydental.queue.screen.token.ydental_area_id|Many2one space.area，必填 restrict|当前店 active clinical reporting 区|绑定门店+area，不接受读请求覆盖|
|screen.token.ydental_token_hash|Char，必填，NO_ACCESS，copy=False|高熵 token 的 SHA256，明文仅创建返回|摘要全局唯一；不存可还原明文|
|screen.token.ydental_actor_id|Many2one res.users，必填 restrict|真实创建者|撤销审计保留真实 actor|
|screen.token.ydental_revoked_at|Datetime，可空|server UTC 撤销时间|active 空，revoked 写入，不复活|
|screen.token.state|Selection，必填 active 默认；revoked|有 capacity-write 的当前店受控动作|撤销后下一请求拒绝，记录保留|

## 既有模型变更与原生复用

|对象/字段|变更|来源/不变量/迁移|
|---|---|---|
|queue.entry.ydental_missed_count|Integer 默认0 readonly|每业务日真实 missed；旧 task missed 在旧唯一约束检测到时回填|
|queue.entry.state|新增 day_closed（Business day queue ended）|日终/显式新日 report 结束昨日未开始段；区别 void，永不同日复活|
|queue.entry task/date 约束|旧 UNIQUE(task) → UNIQUE(task,business_date)|保留原 ID/date/number 引用，跨日新段；患者 waiting/calling 与 lease calling 部分唯一不变|
|entry task/date/number/timezone|新增 write 不可变保护|受控代码同样不能更改历史身份|
|append.permit.state|新增 expired|昨日 active permit 日终失效；started/revoked 历史不重写|
|intake.task missed/opportunity|既有字段镜像保留|新日新 entry 时清当前日镜像，旧日值在旧 entry 保留|
|supply.business|原生项目 S03 既有事实复用|唯一营业来源；已有日期/area/state/version/key 权威；C 不加同义字段|
|bus.bus|继承 `_prepare_payload`，无新字段|仅 `QueueNotice` 延迟读 outbox，丢弃 rollback 消息；其他消息 super 不变|
|ir.cron|新增 XML ydental_queue_cleanup_cron|model queue.service，code model._cleanup_due()，一分钟扫描；test禁用worker|
|queue.number sequence|沿用既有 ir.sequence|不 max+1，不重编昨日号；store/area/date/number 唯一继续保障|

## 动作表

|入口/输入|权限/前置|原子变更/结果|失败/恢复与副作用|
|---|---|---|---|
|supply `_operate('business',area_id,state,reason,version,key)`；队列管理 POST business|S01当前session/store + S03 capacity-write；前后版本；closed先draining|S03业务事实/幂等审计，补before/after/reason/date审计，scope/outbox；accepted/already_accepted|队列非空/旧版本/越权拒绝；刷新后重试；不改患者、容量、工位配置|
|queue `_cleanup_day(store,date)` 私有|server selected due local date，固定全锁序|旧 waiting/calling→day_closed、position关闭/task pending、active permit expired、水位、system审计、scope；accepted/already_accepted|00:10前拒绝；失败全回滚，同日可重跑；无退款/返容量/完成/删除|
|cron `_cleanup_due()`|原生 scheduler 私有入口|扫描当地截止及更早遗漏日，逐日同一清理服务|停机后补跑；框架 RR retry，水位成功才成立|
|intake report(task,version,key)|S05真实权限/当前资格/当地到店；ordinary需open，append当前日合法例外|今日 entry 新建或同日有效段恢复；显式新日受理原子结束旧未开始段|失败无半 position/entry；不重用昨日number/missed/permit|
|queue screen_create(area_id)|capacity-write 当前店 active clinical reporting 非settlement|token32随机字节仅一次返回，DBdigest+审计；accepted,credential_id,token|其他store/area/无权拒绝，无凭证写旁路|
|queue screen_revoke(credential_id)|capacity-write 当前店|active→revoked及时间+审计；重复accepted|跨店拒绝，旧token下一请求拒绝；不清业务队列|
|GET /queue/screen/data Authorization Bearer，optional last_id|每请求hash+active+area校验，token SHARE/scope SHARE只读fence|无last_id最小snapshot，有cursor最小events+last_id；200|无效/撤销403 generic；RR冲突框架重试；no-store|
|WebSocket /websocket?version=actual|原生 Odoo channel subscription|仅store/area/version，客户端再拉授权snapshot|旧版本忽略、gap/reconnect fullsnapshot；非业务执行命令|

测试专用模型 `ydental.queue.test.day.clock` 仅 `ydental_queue_test`，无普通 ACL；store唯一、clock UTC，frozen `DaySource` 私有能力写入，所有实际入口先验证新 C 库/创建记录/端点/OID/config/data_dir/dbfilter/port/外发保护。运行证据中时钟为合成值；产品无客户端时钟 override。原 A/B test adapter guard 仅增加 C 新库前缀，原 A/B 源码及证据不覆盖。
