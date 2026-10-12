# S08-A 文书与牙位字段草案

来源为 [#32 A1/A2/A3](https://github.com/Yredxin/YDental/issues/32#issuecomment-6122378640)。`clinical-draft-v1` 是本批合成演示字段草案版本，不是已批准临床标准。业务负责人仍须审核正式字段、签发资格及同意书。英文 source + zh_CN；没有自动“无/正常/已告知”值。所有时间为 Odoo UTC，页面明确 UTC；临床文字不自动补齐语义。

## 临床 JSON：ydental_content

全部 8 个键每次保存都提交，服务端拒绝未知/缺失键。7 个文字字段为 string，单位不适用、每项≤10000字符。空串代表未填写/未知，允许保存草稿；不推定阴性或正常。由真实当前编辑者逐字录入，版本记录实际作者/时间。确认要求至少一项非空文字或明确牙位记录；仅文字确认，不等于临床签发。

|source key|中文|类型/单位|选项/必填|来源/未知处理|版本/确认|
|---|---|---|---|---|---|
|chief_complaint|主诉|string/无|键必填，值可空|编辑者；空=未填|clinical-draft-v1；无自动结论|
|history|病史|string/无|同上|编辑者；空=未知/未采集|同上|
|findings|所见|string/无|同上|编辑者；空=未填|同上|
|diagnosis|诊断|string/无|同上|编辑者草案；不自动生成|同上|
|treatment_plan|治疗计划|string/无|同上|文字计划，不是实际项目事件|同上|
|suggested_materials|建议耗材|string/无|同上|文字建议，不绑定批次或扣库|同上|
|follow_up|后续建议|string/无|同上|文字建议，不生成医嘱/处方|同上|
|teeth|结构化牙位|list/无|键必填，0–53行|空列表=未记录；不能推定全牙正常|同上；服务端验证每行|

## FDI 与牙面

每行严格为 `{tooth: int, state: string, surfaces: list[string]}`，不接受 bool 当整数、不接受重复牙位/牙面或额外键。每颗牙只有一个当前草稿记录；历史版本保留全部旧记录。

|牙列|合法范围（全部）|枚举数|
|---|---|---|
|恒牙|11–18、21–28、31–38、41–48|32|
|乳牙|51–55、61–65、71–75、81–85|20|
|无对应牙位|0，只配 not_applicable|1特殊表达，不算 FDI 牙位|

恒/乳牙个位1/2/3为前牙，合法牙面 M（近中）/I（切缘）/D（远中）/B（颊或唇侧）/L（舌或腭侧）；其余牙位为 M/O（咬合面）/D/B/L。前牙拒绝 O，后牙拒绝 I。服务端规范化排序存储，不改变原始临床语义。

|state|中文|允许 tooth|允许 surfaces|未知处理|
|---|---|---|---|---|
|present|存在|52个合法FDI|对应合法集合，可空|可明确存在而尚未记牙面|
|missing|缺失|52个合法FDI|必须空|必须显式选择，不由空白推断|
|unknown|未知|52个合法FDI|必须空|不自动变存在/正常|
|not_applicable|不适用/无对应牙位|仅0|必须空|明确表示不对应牙位|

UI 52个可点击牙位、状态选择、合法牙面选择、独立无对应牙位按钮；非法牙位（如99）、混用 I/O、缺牙带牙面等在后端拒绝。乳牙边界55/85及恒牙18/48纳入模型验证；Firefox展示11/I、55/O、48缺失、51未知、0不适用。

## ydental.clinical.document

继承 S01 `ydental.access.source`：`ydental_store_id` 来源门店，`ydental_category=medical`；原生 id/create_uid/create_date/write_uid/write_date 为技术元数据，真实贡献者以版本作者为准。

|字段|类型|必填/默认|事实与修改规则|
|---|---|---|---|
|name|Char|必填|来自真实 execution.name|
|ydental_patient_id|Many2one patient|必填/restrict|真实 canonical 患者；当前关系前置|
|ydental_execution_id|Many2one execution|必填/唯一/restrict|不可改写原始接诊段；历史来源|
|ydental_current_execution_id|Many2one execution|必填/唯一/restrict|初始同原段；合法 restore 仅改链接到新 resumed 段|
|ydental_author_id|Many2one users|必填/restrict|初始创建作者，不随责任交接改名|
|ydental_responsible_id|Many2one users|必填/restrict|当前待完善责任；合法移交才改变|
|ydental_version|Integer|0，非负|服务端连续版本号，CAS 权威|
|ydental_content|Json|新建完整空草稿|最近不可变版本内容；仅受控追加动作更新|
|ydental_saved_at|Datetime|未保存为空|服务端实际保存UTC；不由客户端回填|
|ydental_template|Char|clinical-draft-v1|字段模板版本；每个历史版本同时冻结|
|state|Selection|draft|draft/pending/confirmed，仅受控状态转换|
|ydental_editor_id|Many2one users|可空|当前独占编辑者，NO_ACCESS|
|ydental_session_id|Many2one access.session|可空|真实 S01 登录绑定，NO_ACCESS|
|ydental_session_revision|Integer|0|选店/会话版本，NO_ACCESS|
|ydental_connection_hash|Char|可空|服务端绑定连接摘要，NO_ACCESS|
|ydental_editor_hash|Char|可空|随机token SHA256，NO_ACCESS；不存原token|
|ydental_editor_expires|Datetime|可空|服务器编辑期限，NO_ACCESS|
|ydental_editor_lease_id|Many2one queue.lease|可空|活动接诊原工位lease；pending独立编辑为空，NO_ACCESS|

## ydental.clinical.version

继承同一来源授权，`ydental_store_id/category` 冻结为文书来源。所有普通 write/unlink 拒绝，create 仅服务端 sentinel。

|字段|类型/必填|语义|
|---|---|---|
|ydental_document_id|M2O document/是/restrict|独立文书|
|ydental_patient_id|M2O patient/是/restrict|冻结对应患者|
|ydental_number|Integer/是|该文书连续号；document+number唯一|
|ydental_content|Json/是|完整规范化文字/牙位快照|
|ydental_author_id|M2O users/是/restrict|该版本真实提交作者；永不改为新责任人|
|ydental_recorded_at|Datetime/是|服务端实际UTC时间|
|ydental_kind|Selection/是|save/confirm/correct，动作分别审计|
|ydental_reason|Char/否|更正原因必填，≤300；保存可空|
|ydental_previous_id|M2O version/否/restrict|前一版本；首版为空|
|ydental_request_key|Char/是|16–128稳定请求标识；文书内唯一，不是权限凭据|
|ydental_request_digest|Char/是|expected_version/content/kind/reason摘要，不是token|
|ydental_template|Char/是|该版本模板冻结值|

## 关联与审核边界

D1 document→origin/current execution→S05 task/service快照；D1 version→实际贡献者；D1 handover→S06唯一 continuation→新 D2 execution→另一 document。责任移交只改 D1 responsible，审计保存原/新人员和原因，不改任一旧版本。D1 与 D2 独立编辑，不自动互相确认。

没有处方/用量/临床事件/费用/耗材批次/PDF字段空壳。已有 S05 演示价格快照不是收费单；A 不创建或重算它。正式临床签发、实际项目、药房、打印以及检查结果分别由后续获授权批次负责。
