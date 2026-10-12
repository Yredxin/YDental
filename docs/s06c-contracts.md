# S06-C 工程契约

唯一业务来源：[S06-C 启用 6118760114](https://github.com/Yredxin/YDental/issues/30#issuecomment-6118760114)，结合 #23/#30 当前正文与有效评论。基线 `a32ab4c6bab76aaabc45e1917ad06444d6a2b71c`；不从旧计划补规则。本文与 S06-A/B 及返工契约、字典共同适用。技术结果及固定提交见本批报告。

## 营业与锁

复用 S03 `ydental.supply.business`，门店当地日期由 S03 `_date` 产生，没有第二营业来源。营业管理使用 S03 `_access(write=True)` 的真实 capacity 写权限、S01 当前门店/session、乐观版本及幂等事件；集团管理组本身不构成旁路。业务页面 POST 使用原生 CSRF；模型普通 CRUD/RPC 不提供修改入口。

|状态/动作|允许和拒绝|原子结果|
|---|---|---|
|open|普通 report；已有合法 call/start|沿用 S05 资格、当前患者关系、实际到店、容量与价格快照|
|open → draining|停止普通新 report；已有 waiting/calling 仍可 call/start/missed|不取消已受理 position、资格或占额|
|draining → closed|仅该区域所有仍 live 的 waiting/calling 为零|非零拒绝；不偷偷 void；serving/verify/hold 不阻止 close|
|closed → open|明确有权重开当前当地业务日|不改工位启停，不复活昨日队列|
|closed → draining|拒绝，需先明确重开|无事实改变|
|closed 的例外|当前业务日有效 task-bound append 可 report/call/start；B hold 直返|不改营业为 open；不借昨日 permit|

call/start 仍实时校验实际工作人员能力、执行类型、当前门店及 lease。已受理队列 start 使用不可 JSON 构造的 `StartPermit`，重验 calling/持有人/lease/当前患者关系/目标/held entitlement+claim 和 published slot；不再因报到后时段结束或进入 draining 拒绝清队。普通新 report 继续经过 S05 原资格校验，不采用该执行许可证。

固定锁序：S01 session → S04 patient mutex → S03 supply/space/business mutex → S05 intake mutex → S06 queue/day/push mutex。营业变更在进入 S03 动作前取得完整已有锁序；清理、report、append/revoke、call/missed/fault 共用同一组锁。RR 的 mutex UPDATE 使等待者旧快照产生 serialization retry，避免仅 advisory lock 排队后读取旧事实。HTTP 使用锁定 Odoo 的事务重试；真实探针有界重试，并记录独立 PID/barrier/交错及最终不变量。

营业补充审计 `queue.business_state`：actor、store、area、business_date、before/after、reason；沿用 S03 幂等与审计。管理屏凭证审计只记录凭证记录 ID/area，不记录 token。

## 当地日期、历史与清理

`_local_now(store)` 将 server UTC instant 投影到门店 IANA `ZoneInfo`；00:00 分日，00:10 到期。按 UTC instant 投影后比较当地日期与时分，不从操作者 context/UTC 日期猜门店日期。DST 前进/回退及 Shanghai、New_York、UTC 边界由合成时钟验证。既有 entry 的 timezone/date/number 不随门店配置变更重写。

00:00—00:09:59 昨日 waiting/calling 保留昨日语义，可合法 call/start；00:10 起 eligibility 拒绝未开始的旧段，即使清理 worker 尚未执行。已开始 serving、verify、active/verify hold 保持来源及原执行段，清理不消费、不完成、不强释。有效 hold 的恢复/现场保存仍用 B 原路径。

每 task 可有多个业务日段，同日唯一 `(task, business_date)`；waiting/calling 患者全局部分唯一、每 lease 一个 calling、每 store/area/date/number 唯一均保留。昨日段终态 `day_closed` 与人工作废 `void` 区分。`task/date/number/timezone` 即使受控 write 也不可改；unlink 一律拒绝。

第二日必须符合当前 S05 资格及实际到店规则，显式 report 才创建今日段。新段新 number/date、missed=0、opportunity_used=False；return 仅依今日已开始事实推导。旧段不改日、不删、不重用。旧 task 的 missed/opportunity 镜像仅服务当前日；历史真实 missed 存在各 entry。若显式今日 report 先于清理，先结束该 task 昨日 waiting/calling 和位置，再原子创建今日段，失败全部回滚。execution 的 entry 解析沿 resumed_from 追到来源，不依赖“一 task 唯一 entry”。

真实 upgrade：模型 init 检测并删除旧 `ydental_queue_entry_one_task`，把 task 的旧 missed 回填旧 entry，增加 task/day 唯一；旧记录 ID/date/number/引用保留。验证方式是全新 C 库内构造 B 约束/行形态，再真实 `-u`；不冒称完整旧 B 源码树安装升级。

`_cleanup_day(store,date)` 仅私有 server 调用：

1. 取得完整固定锁序，校验 date 已到当地截止。
2. 若 `(store,date,unstarted_v1)` 成功水位存在，返回原水位/ended，不重发事实。
3. 仅目标日 waiting/calling：关闭 active position，accepted task 回 pending，entry→day_closed、撤 calling lease 链接。
4. 保留 task、医嘱/资格/claim、原 number/missed/history、容量余额；不退款、不返容量、不标医疗完成、不物理删除。
5. 目标日 active append→expired；started/revoked 等历史保留，跨日执行不因 permit 过期中止。
6. 按 entry 记 system `queue.day_closed` 审计，最后建立成功水位。与最小推送/version 同一事务，失败无成功水位/事件。

周期 `ir.cron` 调用 `_cleanup_due()` 同一服务，扫描每店当地 cutoff 和更早未清 live entry/active permit 的日期，支持 00:30/停机后补跑且不误清今日。cron 提交由原生框架负责，产品不手工 commit。模块配置一分钟扫描；上线频率/worker 部署仍待发布，测试 max_cron_threads=0 并直接执行同一服务。

## 原生 bus 与客户端

已读取锁定核心 `addons/bus/models/bus.py` 的 `_sendone/_prepare_payload/_ensure_hooks/_ensure_notify_hook/_poll`、`addons/bus/websocket.py` 协议以及 `odoo/addons/base/models/ir_cron.py`。当前 WebSocket 版本取实际 `WebsocketConnectionHandler._VERSION`，不猜固定 API。

每 store/area 一份 scope/version；每次影响队列 snapshot 的 entry/lease/execution/hold 或营业变更在已有锁内增加 version，并写唯一 `(scope,version)` outbox。heartbeat/到期时间刷新不单独发队列变化。原生 bus `_sendone` 在 precommit 构造 bus 行，postcommit 通知；`QueueNotice(outbox_id)` 延迟 `_prepare_payload` 重验 outbox 存在，连 `savepoint(flush=False)` 回滚也不能留下幽灵成功消息。真实并发检查实际 `_poll` bus 版本与已提交 outbox 精确对应；整事务 rollback 亦无成功。

消息只有 `{store,area,version}`，类型 `ydental.queue.version`。DB 是唯一业务权威，消息不传姓名、电话、临床、金额、token。scope 使用随机 transport channel，只有最小版本通知；不能凭 channel 访问 snapshot 或写业务。bus 原生短期 GC 不影响 DB snapshot；outbox 保留本批证据，未引入删除业务历史的清理策略。

屏幕初载/重连/gap 拉授权 full snapshot；version<=当前忽略，连续版本拉新 snapshot，重叠慢响应不降低 version。原生 WebSocket 加两秒只读轮询用于撤销检测/补偿，十五秒全量校准；断线不重放 call 命令。语音可选，只有连续新版本出现的新增 calling 才播报 number/实际 station；初载、gap、重连不重播。文字/数据库状态不依赖语音能力。

## 区域屏

capacity-write 当前店管理员生成 32 随机字节 `token_urlsafe`，只返回一次；DB 仅 SHA256 摘要，字段 NO_ACCESS，无普通 ACL。凭证绑定 store+area、active/revoked。创建只允许 active clinical reporting area，拒绝 settlement；撤销即使跨请求也重验当前店，审计不存明文。员工会话/业务 write 不接受该凭证。

GET `/ydental/queue/screen` 仅空壳；token 放 fragment，浏览器移入 sessionStorage 并清 URL，数据请求 Authorization Bearer。GET `/screen/data` 只按摘要对应绑定 scope 读；no-store、页面 no-referrer、不从 query 接收 token。有效 token 每次请求重验；token row `FOR SHARE` 使 revoke-first 的旧 RR 请求重试，snapshot-first 完成后 revoke 才提交。scope row `FOR SHARE` 同样避免撤呼先提交后旧 snapshot 返回 calling。屏幕读路径不再获取患者/前级业务锁，无反向锁序。

snapshot 展示只含 queue number、脱敏姓名、状态、实际 calling lease.station.name；另含 store/area、version、business_date/business、bus cursor/随机 transport channel。无原始患者/task ID、电话、临床或金额。只取受理临床 service kind，settlement 不入 call/screen。过期 lease 不展示 calling/工位。

固定 masking helper：移除空白和 Unicode C 类不可见字符，仅第一可见字符保留，其余每字符 `*`；单字符为 `*`，空名为空，不猜名。DOM 全用 textContent，不信任 HTML。语音只 number/实际 lease station，不能取预约/容量来源 station。

## 边界

A/B 的默认 fail-closed 文书/目标来源 hooks、verify 现场保存、hold、restore、handover、continuation、append/revoke 全部继续适用。合成来源/保存/冻结时钟只在新 C 测试库 guard 内；JSON 不能构造 Python capability。

heartbeat/timeout/N 未生产批准；测试数值不当生产配置。WebSocket 代理、worker、50 会话性能仍属部署/S13 验证。S07 库存、真实 S08 文书/发药、S09 结果、S10 收费、生产发布均 NOT_RUN。
