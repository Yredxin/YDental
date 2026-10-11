# S04 定向返工契约

唯一返工依据为[#28 GPT-REVIEW 6114781429](https://github.com/Yredxin/YDental/issues/28#issuecomment-6114781429)及本次用户明确授权。继续原`codex/s04-patient-r1-20261011`分支；原产品/测试/证据`eb60775/a35af92/3b74b33`不覆盖。本补充替代原S04文档中没有限定patient-owned partner读取和care relation前置的描述，其他契约继续适用。

## BLOCKER-1：原生患者联系人记录级边界

`ydental_patient_owner_id != False`的主联系人、监护/其他联系人均受同一模型层读控制，包含合并后保留的旧partner。字段groups只用于隐藏内部反向关联，不作为读安全边界。

|路径|本轮行为|
|---|---|
|private `_can_read_patient_partners()`|复用patient workspace `_access()`：当前有效user/session/store/membership/employee，patient/frontdesk/medical/exam至少read。没有有效绑定、旧revision或权限不足返回False；不改变普通Contacts可用性|
|partner `_access_domain('read')`|与原生domain取AND。无上述资格仅允许owner=False，search/search_read/name_search/count/read_group同域过滤；不缓存资格|
|partner `check_access('read')` / `fetch`|每次重新验证受保护记录读取，不让原生access/cache复用覆盖撤权；普通非患者联系人仍走原生ACL|
|partner export|先受同一live read保护，患者联系人还要export write；export资格单独不能授予患者读取|
|partner image/content|正常content hook按请求者检查；limited-field HMAC提前返回sudo后，ir.binary重新绑定请求者检查，不能以token放宽患者读取|
|native Contacts RPC|Dataset会替换请求context，因此由继承controller根据真实SID查找当前用户会话，清除客户端binding再注入服务器binding；没有应用组/会话的账号仍可读普通partner，不能读患者partner|

普通联系人写规则、患者partner受控行政写/禁止Notes/chatter/unlink、附件分型保护不改。将来确需其他岗位的必要行政读取，由服务器继承固定hook，不能由context或客户端model/field扩权；本次不预开settlement。

## BLOCKER-2：当前门店关系是care/clinical最小前置

新增固定私有`_current_relation(patient, store, required=True)`：先解析canonical，只认canonical patient + current store + superseded_by=False。没有current relation时默认AccessError；required=False只返回空，不创建关系。

|入口|前置/行为|
|---|---|
|`_patient_care`|医疗/检查资格及用途通过后、签发可信scope前检查current relation|
|`_get_care_domain`|每次继续验证用户/session/revision/权限/canonical患者和current relation；旧scope遇到合并或relation失效不扩域|
|`_clinical`新建/维护|医疗write、当前店/患者/版本检查之外，必须已有current relation；不偷偷建立关系|
|原生clinical read/query|在S01来源域上再AND canonical current relation子查询，包含本店直接RPC及已缓存源读取|
|relation/arrival行政动作|沿用原授权入口显式建立关系；relation不产生first_arrival；不要求真实到店才能合法预建关系和care|
|合并后|旧patient ID先canonical；target current relation可用，source/superseded历史relation不能独立授予care|

B-only患者在A无relation时：A医生care/clinical拒绝，关系数量不变；A前台显式建立relation、首次到店仍为空；之后A医生可按用途读B历史/既有C历史并写A安全背景。跨店写/finance/forged context/other session/撤权继续拒绝。测试中的关系失效仅由隔离库私有fixture模拟，不新增生产撤销关系功能。

## 不变项及交付

患者编号、统一身份、旧号、phone规范化、疑似重复、合并版本/幂等/锁/事务、活动冲突钩子、历史快照/作者、政策提示均不重写。历史clinical fixture由测试准备阶段显式调用原行政relation动作，避免测试通过临床入口隐建关系。

只在全新`scripts/s04.py`允许的S04库安装/升级和合成验证。新增Firefox证据写`docs/evidence/s04-rework`，旧`docs/evidence/s04`及3b74b33失败链原样保留。实际版本/结果见[s04-rework-report.md](s04-rework-report.md)。真实S05/S06/S08/S09/S10/S12仍NOT_RUN。

本次唯一Project写是#28自定义执行状态→返工，已在实现前完整读回及二次核对；其他条目/字段/原生Status/Issue状态/workflows未改。修正评论读回后停等GPT，执行状态不再自行变化，不进入S05。
