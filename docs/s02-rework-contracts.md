# S02 定向修正契约

本次唯一修正依据为 [GPT-REVIEW 6109759130](https://github.com/Yredxin/YDental/issues/26#issuecomment-6109759130) 及当前用户明确授权；沿用当前 S02 分支。本文仅替代原 [S02工程契约](s02-contracts.md) 中对应四项行为，原文档、通过证据和失败链作为历史保留，不另立需求、不进入 S03。

## 公共和私有资源授权

所有路径仍要求 active 内部 YDental 用户、真实 server-bound session；维护请求还需有效页面 revision。匿名、portal、伪造 Binding 或旧 revision 不能维护资源。公共定义 store=False；集团维护身份不由 space 业务级别替代，也不依赖选店。

|对象/动作|授权|无授权结果|
|---|---|---|
|公共 read/create/write/archive/unarchive|集团管理员 + 受控内部会话；不要求任何门店 membership、选店或 space 级别|拒绝|
|公共 read（普通门店用户）|当前有效门店 membership + space>=read|拒绝|
|公共 create/write/archive（普通 space=write）|普通业务写权限不足以维护公共主数据|拒绝|
|私有 read|当前店有效 membership + space>=read，且源记录属于当前店|拒绝；集团身份不能代替私有源权限|
|私有 create/write/archive/unarchive|当前店有效 membership + space=write，且源归属当前店|拒绝；集团公共维护权不能写他店私有资源|
|资源 export|仍需原有 export=write 加源读取权|没有扩大导出授权|
|unlink|普通物理删除仍拒绝|归档保稳定引用|

create 先解析实际 store 默认值，再分别检查公共/私有权限，不能用 context.default_ydental_store_id 绕过；混合批次仍同事务验证和回滚。模型 access domain、显式 check_access、真实 HTTP 和原生资源表单走同一规则。既有版本锁、SVG白名单、CSP、审计、公司规则均保留。

集团公共维护不执行门店业务 `_check('space', write=True)`；内部身份及 session/revision 校验仍由 `_scope(write=True)` 完成。私有维护继续执行原门店 `_check`，包括其异店坐诊写保护；没有修改 S01 服务或权限模板。

## active 恢复与历史引用

station 的约束触发字段加入 active；action_unarchive 和直接 write(active=True) 同样重新验证 floor/area 有效性及门店/楼层归属。先 station归档→child area归档，再恢复station会被拒绝；失败事务不能递增版本或更改 active、ID、历史图形引用。正确恢复次序为 floor→父区→子区→station。

item 同类约束触发加入 active，恢复时重新检查有效 floor/resource 和原归属。area 原已含 active，并验证有效 floor/parent；floor 是空间树根，其归档仍要求先归档全部有效内容，恢复还受 S01 当前有效门店写权约束。没有级联物理删除或静默恢复子项。

图形 item 的有效性仍表示摆放图形有效，不等价于关联工位 active/enabled：归档 station 可保留图形与历史引用。没有新增“工位归档必须删除/归档图形”的业务规则。item 恢复必须符合既有 floor/resource 约束，不通过 active-only 写绕过。

## rect 顶点规范

polygon 仍需3–100组有界有限坐标；NaN/Inf、超长、畸形点集拒绝。rect 的 points 必须为空。对 rect 的非空列表、嵌套对象、字符串等直接 create/write/几何 RPC 拒绝；切换 shape=rect 时在写入/审计前明确清空旧 polygon points。

实际锁定 ORM 的 Json.convert_to_cache 会把 JSON 假值（0/false/null/空列表/空对象/空字符串）转换为数据库空值，读出 False；这属于安全规范化为空，不声称此类输入被拒绝。非空大/嵌套结构不能被持久化或进入成功配置审计。rect→polygon 必须同时提供合法点集，polygon→rect 后 snapshot 保持规范空值。

本批不接管、重写或清理历史库；升级只在本批全新隔离库运行。旧已安装库如曾有人通过历史漏洞存入脏值，不在本批越权批量迁移；显式切回 rect 可清空该记录，其余修正路径仍执行同一服务端约束。

## 停用能力的新关联与清理

继续使用 S01 能力字典，所有三类可写关系适用：resource.ydental_capability_ids、station.ydental_add_capability_ids、station.ydental_remove_capability_ids。

|命令|行为|
|---|---|
|LINK|不存在于当前关系的新 ID 必须存在且 active；已有停用 ID 的 no-op LINK 可保留|
|SET|完整替换集合；新增 ID 必须 active；显式保留的历史停用 ID 可留；不在目标集合的旧值清除|
|UNLINK/CLEAR|允许清理旧停用关联；清理后再次关联属于新增，必须 active|
|嵌套 create/update/delete|仍全部拒绝，不能从空间配置修改字典|

校验按记录、按命令顺序模拟当前集合；create 的既有集合为空。字典停用本身不主动改写任何既有空间关系；普通更名/几何写也不自动删除旧关联。

实际 fork 的 Many2many 默认会保留 active_test 过滤隐藏的关联，因此仅在明确提交能力命令的底层 ORM write 中使用 active_test=False，保证 UNLINK/CLEAR/SET 真正清理。不是 sudo，不跳过权限，不改变其他写入的 active-test 语义；成功审计记录完整存储关系，包括被明确移除的历史停用 ID。

## 验证与运行边界

新增4个模型方法与4个真实 HTTP 方法，原 T01–T10 适用测试保留。新增无任何 membership/space grant 的独立集团账号和 portal 反向账号；真实浏览器额外验证该集团账号不选店而通过原生资源表单创建/修改公共定义，以及普通读、普通写拒绝、私有写拒绝。

本次全部证据写入 `docs/evidence/s02-rework-20261011/`，不覆盖原 S02 目录。新运行仍用 scripts/s02.py 和全新 `ydental_s02_test_14位时间_8位hex`，使用新空闲端口18103，不停止或重配原18102预览及其他旧服务。实际最终提交/库OID/测试数/失败补交见本次交付报告。

Project #26 自定义执行状态仅按本次用户授权单次改为返工，已立即读回和二次同步；原生Status仍Todo、Issue仍OPEN，workflows公开元数据未变。用户未授权任何后续Project写入。真实排期/患者任务/队列/租约联调仍 NOT_RUN，归 S03/S06；没有生产参数批准、生产发布或S03启动。
