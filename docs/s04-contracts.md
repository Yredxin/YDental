# S04 当前工程契约

唯一业务来源为[#23当前正文](https://github.com/Yredxin/YDental/issues/23)、[当前验收流程6110178328](https://github.com/Yredxin/YDental/issues/23#issuecomment-6110178328)、[#28当前正文](https://github.com/Yredxin/YDental/issues/28)及[GPT-ACTIVATE 6111275379](https://github.com/Yredxin/YDental/issues/28#issuecomment-6111275379)。[开工检查6111333171](https://github.com/Yredxin/YDental/issues/28#issuecomment-6111333171)已写回并逐字读回。S03最终技术PASS及状态同步分别为6111270280/6111303932；不要求重做S03，不把技术PASS称作用户验收。

## 身份、原生联系人及权限

产品模块`ydental_patient`直接依赖`ydental_access`、原生`mail`、`phone_validation`及`web`，不引入OCA。复用S01用户、门店、会话、分类授权、源模型审计及导出保护。S03的advisory lock加revision更新设计在本阶段以独立患者事务fence实现，不改S03容量算法。未建立真实预约、队列、治疗病历、检查、账款、PDF、门户或通知。

`ydental.patient`是集团统一行政身份；`res.partner`仅承载姓名/电话/邮箱，不承载临床文本，不使用委托继承或临床related字段。门店关系、临床背景、号码映射和合并申请分表。建档不会创建账号、门户授权、通知或签署状态。患者及联系人的partner由服务器创建，拒绝任意partner ID/x2many命令；普通Contacts写入、备注、chatter、删除和原生联系人合并不能修改受控患者联系人。

|对象/动作|授权与范围|
|---|---|
|患者行政资料、号码、门店关系、联系人读取|当前有效门店membership，patient/frontdesk/medical/exam至少一个read；只含行政资料，可集团检索统一身份|
|行政建档/维护/归档、门店关系、真实到店、联系人、申请合并|当前店patient或frontdesk write；S01重新验证账号、员工、会话revision及他店实际坐诊写入阻断|
|本店临床安全背景写入|当前店medical write；源store和patient均固定校验，不能借care改写他店|
|本店medical或exam源读取|沿S01相应业务大类；exam权限不自动授予medical字段|
|跨店临床读取|明确用途及真实患者身份，绑定服务器PatientCareScope；只扩展所选患者及相应medical/exam源，其他患者/类别不扩展|
|合并确认/拒绝/刷新身份版本、文书政策配置|上述行政write加S01集团管理员；合并确认覆盖全部受影响法人，店长/前台不能直接确认|
|导出|当前店export write和源read同时满足；前台即使可行政导出也不能导出临床资料|
|匿名、portal、无业务授权、已撤权|没有患者源读取/写入权；每次请求重验|

所有患者业务模型只有业务组read ACL，普通create/write/import/unlink不能作为状态入口。私有`_new/_save`仅接受服务器对象token；RPC JSON不能构造该token。历史业务不可物理删除。mutex无业务组ACL，只有私有服务固定SQL更新；sequence为集团单一范围加两层号码唯一约束。

原生附件未分型时无法证明其内容属于行政资料，因此患者行政模型及受控partner的附件读/下载/创建拒绝。临床附件沿源对象授权，public、普通access_token及原生限时字段HMAC都不能绕过。`ir.binary._find_record`补核验锁定源码先接受HMAC返回sudo的路径；`ir.attachment.read/fetch`补核验缓存命中的路径。没有放宽普通联系人全局ACL，没有把所有附件当医疗资料。

## 字段、电话与未发布项

完整字段表见[s04-data-dictionary.md](s04-data-dictionary.md)。姓名必填，出生日期可未知，另可记不确定出生信息；性别允许unknown/female/male/other。出生日期不得在未来；本阶段未设监护年龄、证件门槛或强制证件字段。

电话保留原值及明确提供的ISO地区。使用`phonenumbers==9.0.16`验证并生成E.164检索值；输入有`+`或明确地区时才尝试规范化。地区未知的本地号、无效号及分机均标`review`，不从服务器/门店/操作者国家猜国家码，不为完成建档强行改值。电话相同只提示。相同姓名+出生日期、患者或有效联系人的相同规范电话/原值/邮箱均形成疑似重复，列表有限展示，不自动确认身份。临床文本不参加行政搜索。

患者号使用原生标准sequence，初始技术格式`P`+8位padding，是可审查技术初值；生产格式可配置，但不能重编已有号码。无连续无缺号承诺。标准sequence允许事务回滚产生缺号，不允许重复编号。幂等键与展示编号分开。

真实临床字段、监护/证件政策、正式文书正文/签发须按#23第3.2节由业务负责人审核；本阶段的过敏/既往/用药只是安全背景草案，不是S08治疗病历。系统依赖、核心venv和既有服务没有修改；电话库仅解包到本仓库`.local/s04-deps`。wheel SHA256为`3c019f10305c311005672f3a0cea4139fef0b949319a60635ee803cfaef4a2e2`，代码声明外部依赖，正式部署另行安装发布。

## 到店与本店文书提示

建档或`relation`只建立门店关系；`ydental_first_arrival`保持空，不由预建档、预约或关系创建时间推断。`arrival`是有权人员确认真实到店的独立动作，默认记录当前UTC，也允许服务器补录参数，须实际时间非未来及原因；同时保留录入时间、实际操作者、门店当地业务日期。重复不会覆盖首次事实，不同补录时间拒绝，未实现未经审核的更正入口。

每个患者每个门店只有一条当前关系，合并遇到两店关系重叠时保留两条历史，以`superseded_by`指出当前关系；当前首次到店取已有真实事实的较早者，并保留其记录人/原因/当地业务日期，不伪造新到店。

`policy`按当前门店独立保存代码、名称、正文引用、集团批准人及版本。无政策、未批准或正文未配显示`pending_configuration`，行政建档仍可继续。有已批准正文则显示`pending_verification`。本阶段不会生成已签状态，不自动继承他店旧签署事实。私有`_document_facts(patient, store, policy)`为S12按同店已批准原件进行核验的扩展点；没有正式文书/签名/PDF生成。

## 动作及恢复

所有写动作通过`POST /ydental/patients/action`，auth=user、CSRF开启、最大32KiB；服务器会话SID绑定及数值revision校验，固定动作分发，字段白名单。GET仅查询/按用途留读取审计，不建立到店或改变合并状态。结果页面使用no-store。`key`长度1-160、按actor唯一；fingerprint覆盖operation/store/payload，不能跨店或换参数复用。

|operation|输入|前置/权限|原子副作用|失败/重试|
|---|---|---|---|---|
|create|values:name,birth_date,birth_note,sex,phone,phone_region,email；key|行政write，静态字段验证|sequence、行政partner、患者、初始号码映射、未到店关系、版本/业务日及审计/回执|同key同payload返回原ID；不同payload version_conflict；失败整笔回滚但序列可缺号|
|edit|patient_id/version/values|当前未合并active身份、行政write、版本一致|行政字段及partner受控同步，version+1，审计|旧版本拒绝，不覆盖临床或历史快照|
|archive|patient_id/version/reason|行政write、无活动业务|active=False、版本及审计，保留身份/号码/关系|有活动业务拒绝，必须由所属业务先处理|
|relation|patient_id|行政write、有效canonical患者|当前店关系存在则复用，否则新建；不记录到店|同店不重复；旧ID解析主档|
|arrival|patient_id/可选occurred_at及reason|行政write，真实UTC不晚于录入；补录要原因|首次真实时间/当地日/录入时间/actor；审计|重复保留首次；不同首次值拒绝|
|contact|patient_id/name/relation/relationship/phone/phone_region/email/verified/verification_note；维护加contact_id/version/active|行政write、联系人属于所选患者，核实标记需依据|创建或维护独立行政partner及关系，保留原始身份，版本审计|不设年龄/证件硬门槛；旧版本/其他患者联系人拒绝|
|clinical|patient_id/values:allergies,prior_history,medication；维护加record_id/version|当前店medical write，源属于本店及所选患者|安全背景、原始身份快照、actor、录入时间及版本；原快照不变|跨店写拒绝，不创建治疗执行/费用|
|policy|code/name/body_reference/approved/required|集团+行政write|本店政策版本、批准人、审计|正文空显示待完善，不能写签署结果|
|request_merge|source_id/target_id/reason|行政write、两有效未合并身份，至少一档与当前店有关|申请、两档版本、申请人；不迁移|失败保持所有关系；不自动合并|
|confirm|request_id/version/reason|集团+行政write、全部法人覆盖、申请未终结、申请/两档版本一致|fence内重查活动，冲突则保存blocked/清单；无冲突迁移当前引用、保留原档/号码/快照并保存前后数量/actor|有冲突先处理，不吞并活动；hook抛错整个合并及回执回滚；同key重试同结果|
|refresh_merge|request_id/version/reason|集团、未终结、两档仍有效|显式核实新身份版本，保留申请历史版本|不是绕过活动冲突检查；已合并须新申请|
|reject|request_id/version/reason|集团、申请未终结|有原因的拒绝事实及actor|不改变原患者及关系|
|export|patient_id|export write+行政源read|原生export_data及审计|无导出或源读取权拒绝；字段固定为行政白名单|

服务不手工commit；写动作、回执与审计在同一savepoint。HTTP失败在业务savepoint回滚后写脱敏拒绝事件；不记录临床文本、电话、token或拒绝目标ID。框架事务最终提交/回滚。代码内部错误仍交给框架，不将异常当accepted。

主要稳定结果：`accepted`、`already_accepted`、`version_conflict`、`access_denied`、`conflict_requires_resolution`。冲突结果保存原申请及有权用户可读的`patient_id/kind/reference`清单，源业务处理后按新request version重新确认；拒绝和异常不改变原业务，不删除失败证据。

## 合并、事务与下游私有契约

固定fence为`pg_advisory_xact_lock(28004)`加`ydental_patient_mutex`的revision UPDATE。repeatable-read下旧快照必须SerializationFailure后重开事务，不能等待锁后沿用旧活动集合。HTTP由Odoo框架重试，探针用独立游标有界重试；业务方法无手工commit。

|钩子|固定输入/输出|边界|
|---|---|---|
|`_business_patient(patient_id)`|原/当前患者ID→canonical recordset，仅服务器使用|下游先鉴权，再先取患者fence，后取自己的业务锁；每笔新活动使用返回主档ID，不能客户端context声称已锁|
|`_active_business(patient_ids)`|固定身份ID集合→`[{patient_id,kind,reference}]`|上层super追加权威源查询，不由请求提供活动列表；kind=reservation/queue/execution；无下游时默认空|
|`_migrate_business(source_ids,target)`|来源历史身份集合及主档→迁移计数dict|在同一fence/savepoint中只改当前活跃canonical引用；历史作者/已过账原单/快照不改；异常整笔回滚|
|`_get_patient_care_sources()`|固定model→patient字段路径映射|已安装上层显式注册，不能客户端提供model/field或探测未来registry|
|`_document_facts(patient,store,policy)`|当前身份/门店/已批准政策→状态dict|S12仅核实同店权威原件；本阶段默认待核验|

两档都有活动业务则blocked；任何实际执行均先阻断合并。只有一档非执行活动时允许在钩子中迁移当前引用；迁移失败原样保留。号码映射全量指向主档，origin_patient不变；原patient归档并记录merged_into，链式合并不产生环。旧号搜索返回主档并仍可追溯原身份。行政联系人保持各自原始partner，不调用原生partner merge重写历史。

`PatientCareScope`包含user/session/revision/current-store/canonical-patient/purpose，由私有`_patient_care`生成，purpose只允许diagnosis/history_review。每次源授权重新校验membership、权限、会话及canonical身份。字典、数值ID、`ydental_purpose`或allowed_company_ids无法构造该类型；跨用户/会话/版本复用无效。care只在read域扩展，财务/settlement源不扩展，写域仍固定当前店。

## 隔离与交付边界

只使用`scripts/s04.py`允许的新`ydental_s04_test_14位时间_8位hex`。逐动作校验本地创建记录/OID/端点/cluster/配置SHA/独立data_dir/端口及源码清洁，拒绝旧库/业务库/错端点/既有端口；loopback18106、精确dbfilter、list_db=False、cron=0、进程外发限制仅允许本库端点及预览端口。测试模块有pre_init_guard，不能当作生产依赖。Firefox使用已存在的本地浏览器/动态库，不关闭sandbox、不改系统策略。只停止经PID及配置逐字匹配的本次自建预览进程。

固定product/test/final版本和实际命令、失败/补交、截图及TC结论见[s04-report.md](s04-report.md)。S05/S06/S08/S09/S10/S12真实联调、生产参数/迁移/部署及S13负载仍NOT_RUN。合成保护通过不等于未来真实活动业务通过。交付评论写回读回后停止等GPT复核，不进入S05、不改Project/原生Status/workflows/Issue状态。
