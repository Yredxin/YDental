# S08-A 文书、编辑和交还契约

唯一业务授权：[GPT-ACTIVATE6122378640](https://github.com/Yredxin/YDental/issues/32#issuecomment-6122378640)。本契约只记录 A 批工程实现；临床字段及正式签发标准仍待业务负责人审核。

## 权威与事务

患者及当前关系复用 S04；坐诊、接诊段、唯一患者位置、续诊任务和租约复用 S06；价目、演示价格快照复用 S05；数量事实复用 S07 原生 move/quant。新建的 document/version 只承载文字及责任，不是诊疗执行/费用/库存账本。工作台链接现有 S05 服务价目页，仍须其独立 price 权限；A 批文书没有选价或费用绑定。

所有写动作必须经过当前 S01 medical-write、服务端绑定的登录 session/revision 和连接，调用签名只接受固定参数。复用 S06 `_locks`：登录会话锁在先，patient→supply→intake→queue，不更改上游锁序。CAS 和编辑占用在共同 fence 内检查。动作 savepoint 内任一步失败，全动作回滚；外层 HTTP 提交成功才算保存。

`DocumentLock`/`SaveIntent` 是仅 Python 服务端可构造的 frozen dataclass。客户端 dict/context、普通 create/write、管理员身份不能冒充它们。原生 ORM 写使用私有对象 sentinel；RPC 序列化无法构造 sentinel。

## 状态和动作

文书：draft（草稿）→pending（原段交还/现场接手后待完善）→confirmed（仅文字确认）；draft 也可直接 confirmed。confirmed 的更正追加新版本并保留 confirmed。确认不结束真实 serving 段；D2 的操作不自动确认 D1。

|动作|条件|成功副作用|失败出口|
|---|---|---|---|
|open|本人当前 serving medical 段、有效持有人 lease/token、当前关系|创建/复用本段唯一文书，取得编辑权；初始 version=0，字段空白|无真实接诊/旧连接/撤权拒绝|
|acquire|当前活动段由原 lease 持有人；交还后由当前责任人且具备来源服务能力/可信资格|独立编辑随机 token，仅存摘要，记录 session/revision/连接摘要/到期时间|有效编辑者存在 editor_busy；verify 不允许旧端重获|
|heartbeat|同人/会话/连接/token，权限和来源资格仍有效|延长文书到期时间|失效不续租|
|release|同编辑者；UI 先同步|清空该文书编辑占用，审计|旧连接拒绝，不释放其他文书|
|save|有效编辑，非 confirmed；完整字段，expected_version/key|追加不可改写作者版本，版本+1，最近内容/时间更新|CAS 冲突/非法牙位/事务失败无半保存|
|confirm|draft/pending，有效编辑，非空临床文字或牙位；原请求精确重放仍幂等|追加 confirm 版本，state=confirmed|空白/旧版本拒绝；不签临床事实|
|correct|已 confirmed，有效编辑，必填原因|追加 correct 关联前版本，保留原作者和经济事实|普通 save 不能改已确认文字|
|handover|当前真实段、原 lease，最新完整草稿/版本|同事务保存→核对不可变版本→S06交还原段→释放编辑→唯一 pending continuation；未确认文书变 pending|内容/保存/方向/续诊失败，保存与段/工位一起回滚|
|transfer|当前段 handover/interrupted，责任人或本店店长且 medical-write；目标仍有效、具备来源能力/资格；原因必填|改责任人、清失效编辑、保留所有贡献版本、审计前后人员|不得强抢有效编辑；旧版本/不合格目标拒绝|
|read|medical-read、当前患者关系、来源范围；跨店历史显式 history_review/diagnosis 目的及 S04 care 授权|返回纯 JSON 快照，clinical.view；原生读取另记 source.view|跨店任意读/无当前关系/撤权拒绝|
|export|来源读取 AND export-write，含合法目的性共享历史|原生 export_data，source.export|附件、公链、普通 RPC 不能旁路|

每个动作返回原生 JSON 标量/字典/列表，不向公网返回 recordset、私有 dataclass 或编辑摘要。只在 acquire/open 返回当前编辑者的随机 editor_token；字段层 NO_ACCESS 禁止读取持久化秘密。

## 幂等、离线与版本

保存 key 为 16–128 字符；签名覆盖 expected_version、规范化完整内容、kind、reason。相同 key/作者/内容返回已保存版本及当前快照；相同 key 不同内容拒绝。新 key 必须匹配当前版本。数据库唯一 `(document,number)` 与 `(document,request_key)` 是最后约束。

在线输入静默等待 900ms 串行自动保存；显示服务端版本与 UTC 保存时间。输入时立即显示未同步。网络/权限/CAS 失败停止自动写，不宣称成功；用户刷新比较服务端版本后重新取得独占编辑。页面未保存离开有浏览器提示。内容仅驻留该页面内存，刷新明确丢弃未提交演示文字；没有离线病历缓存。token 留在该 tab sessionStorage，服务端只存 SHA256；旧 tab 不能转借。

心跳/租约复用 S06 明确配置。合成模型测试 2秒/20秒，双连接和 Firefox夹具 2秒/600秒；均非生产批准阈值。过期或人员撤权/离职/资格丢失/旧 session 的编辑失效，后续合法取得或责任交接记 editor_invalidated/transfer 审计；管理员无 remote force-release。

## 真实 S06 链

工作台 handover 在 `_append` 后构造 SaveIntent，调用真实 queue handover。`_save_before_handover` 比对 actor/execution/document/version，检查已落库 immutable version 等于最新内容并 flush。S06 创建或复用原区域/方向/能力/资格快照的唯一续诊，原段保留，`_release_execution_documents` 清编辑并保留负责人。旧 handover 请求不能再保存；需要查询原 S06 后继结果，原 S06 重试只返回一个后继。

verify 现场接手仅在旧 lease 已失效、无有效文书编辑且有已持久化版本时使用最后提交草稿；不代签旧作者。S06 新接手人、新 lease 和原历史继续保留。外检 reserve 默认仍拒绝没有可信 S09 来源的目标。测试中只有一个受新库 guard 保护的场景临时提供外检前提；文书、reserve、restore 均走真实产品。restore 只把同一文书 current_execution 链接新 serving 段，origin_execution 永不改写；再次交还释放同一文书。

D1待完善编辑不报到、不进队、不取得诊椅、不创建治疗事实。D2经前台明确续诊报到→其他合格工位/人员领取→真实 start 后创建另一文书；D2实际项目完成属于 B，A 不模拟完成。后继只沿原门诊能力，不复制检查设备能力，不指定原医生。

## 错误与权限

|错误码/类型|含义和恢复|
|---|---|
|access_denied / HTTP403|当前权限、来源门店/公司、患者关系、工位持有人或目标责任资格不足；恢复授权后重新登录/选店|
|editor_expired / HTTP403|编辑租约/连接/token失效；刷新比较版本，合法重新取得|
|editor_busy / HTTP409|已有有效编辑者；等待本人释放或真实到期，无管理强抢|
|version_conflict / HTTP409|旧版本、旧门店revision、请求key冲突；读回服务端版本后核对|
|invalid_content / invalid_tooth / invalid_surface / HTTP409|完整字段、长度、FDI/状态/牙面不合法；修正输入|
|invalid_action / invalid_version / HTTP409|动作签名、版本或稳定请求key不合法|
|correction_required / HTTP409|确认文字只允许附原因追加更正|
|content_required / HTTP409|不允许确认空文书|
|save_required / HTTP403或409|没有真实已持久化文书/当前版本不一致；先同步；现场恢复只能用真实已保存草稿|
|上游 UserError / HTTP409|工位、续诊方向、当前营业和资格约束失败；不扩大权限自动重试|
|缺 CSRF / HTTP400|会话页面刷新；不取消 CSRF|

GET `/ydental/clinical` auth=user、no-store；POST `/ydental/clinical/action` auth=user、原生 CSRF、100000字节限额。没有公开写 RPC、导出公链、富 HTML 病历或上传通道。技师/exam-only 不能编辑治疗文书；普通 medical-read 只能读取，店长仍须 medical-write 且不能强抢。来源导出仍遵循 S01/S04 当前权限。

## 审计与未启用接口

clinical.create/view/edit_acquire/edit_release/editor_invalidated/save/confirm/correct/handover_save_verified/handover_edit_release/document_return_restored/responsibility_transfer 分开；原生 source.view/query/export、clinical.action 拒绝审计沿用 S01。审计记录真实 actor、来源门店/文书、版本/责任变化、原因，不复制全文或 token。

没有实际项目、费用、处方、检查单、药房、转诊或 PDF 新空壳。S07 `_authorize_source` 未接 B 时继续 fail-closed；外检合法来源由 S09 负责。正式签发/临床字段审核、经济更正、跨店转诊正式入口及打印均未启用。
