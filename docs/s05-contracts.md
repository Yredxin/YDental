# S05工程契约｜YD-N1 R1

唯一需求来源为#23当前正文/有效评论、#29当前正文及GPT-ACTIVATE6115298923；前置#28技术复核6115295633及状态同步6115318214。开工检查6115339128已逐字读回。本文只记录#29工程落地，不另立需求计划。S06及真实临床/费款未启用。

## 原生复用与边界

`ydental_intake`直接依赖patient/supply/access/space/product/web。集团目录关联原生`product.product`和模板、原生UoM；每一门店项目/单位/币种/有效区间价目版本关联一个原生pricelist和固定价item。单项目版本粒度是当前实现选择，不改变集团编码和门店维护权限。药品/义齿目前只是目录类别，原生产品是service；S07真实库存尚未接入。

核对底座f0c5a9b实际API：`_get_product_price_rule(product, quantity, uom=..., date=...)`返回单价和规则ID。必须先找唯一published且`start <= t < end`版本，再验证原生返回规则及金额吻合；不用原生缺规则时的默认价回退。有效区间按左闭右开处理，原生日期规则边界由版本预筛选限定。

当前UoM无旧版`rounding`字段，使用`uom.round/compare`与原生`Product Unit`精度。数量须正且符合精度；币种用原生round/compare_amounts，基础价舍入后仍须正。快照保存数量精度、币种舍入、单位ID/名称、项目名称、数量、单价、金额、币种、价目版本、取价时间、来源和操作者。没有费用/折扣/收费/退款对象；零基础价被拒，真实免单以后走明确折扣。

价目draft→reviewed→published；同门店/项目/单位/币种的published区间不重叠。替换要求匹配条件和旧版本，从当前或未来时点截短旧版，再发布新版；两者原子提交。发布/审核均保存操作者、原因与版本，当前没有新增“审核人与发布人必须不同”的未授权业务要求。发布后的单价不修改。原生模板、变体、价目、规则受同一不可JSON伪造的mutation对象保护，普通sudo也不能直接改受管数据；普通非S05产品沿用原生权限。

唯一可选择的快照策略`demo_confirmation`明确是演示确认时取价，正式生产锁价/承诺价政策待业务负责人发布。相同来源恢复原快照，即使价目已改变；来源参数不同拒绝。S08/S09未来须通过固定服务器集成消费快照，S10不得重定已确认费用；当前不宣称这些真实阶段已联调。

## 对象与容量

|层次|当前真实对象|含义|
|---|---|---|
|身份|S04 patient/number/relation|统一canonical患者；建立目标门店relation不制造first_arrival|
|接收资格|intake.entitlement→S03 claim|预约、电话池或现场资格；内部容量来源station仅在S03记账，不绑定医生/实际接诊工位|
|到店|intake.arrival + S04首次到店语义|明确实际到店；患者/门店/当地日幂等；不报到也可存在|
|服务任务|intake.task|明确项目、能力、报到/执行映射；pending不是排队|
|受理位置|intake.position|S05前置对象；只有active/撤销及关联任务，无waiting/calling、号序、叫号或租约|
|未来队列|固定queue hooks|S06尚未接入；测试模块单独模拟waiting/calling，不能安装业务库|

所有容量获取/取消/开始/改期只调用S03 `_capacity_action`，保留policy/slot/claim/event/operation账链，不建立第二账本。服务器创建`CapacityPermit(actor, store, action, payload digest)`，适配层验证类型、发起人、动作、精确参数和目标门店；请求context字典不能伪造授权。

预约/电话代约选明确映射和真实S03时段，渠道服从S03 policy；现场只限门店当天。已有资格报到验证原claim held、槽未过期且供给有效，不再检测余额或售卖截止，也不再扣额。可早到，仍用原时段。任务必须有实际到店事实后才报到；现场登记本身不自动制造到店或排队，`walkin_report`才原子合并登记、真实到店和报到。合并任一步失败回滚新关系/资格/claim/任务/到店/位置；已存在的独立预约保持。

S05到店按S03门店时区计算当地日，并调用S04到店语义更新首次到店。merge后历史arrival保留原身份/日期，通过S04全部identity IDs查找和复用当天原事实，不覆写真实历史。页面明确UTC输入；营业日按门店IANA时区，不按操作者/服务器日期。

## 统一锁序与并发

固定：**S04 patient fence 28004及其UPDATE → S03/S02 supply/space锁26002及supply mutex UPDATE → S05 intake锁29005及mutex UPDATE**。

每个S05动作在框架savepoint内按此顺序取得全部锁，再重验授权；下游使用S04 `_business_patient`返回canonical患者。重复取得已经持有的patient/supply锁不会新增逆向等待。S04 merge在已有patient fence下，其真实`_active_business/_migrate_business`按supply→intake顺序取得后续锁。

S03单独营业/供给动作只取supply锁，不从supply反向请求patient；报到在同supply边界重验open，因此先报到可留下合法待清位置，先draining则普通报到失败。合成队列空校验只在测试模块覆盖；生产closed仍继承S03未接入队列时的fail closed行为。

全局串行栅栏是当前正确性实现，未声明S13的50活动会话容量或吞吐已验收。PostgreSQL repeatable read下通过UPDATE让旧快照抛serialization failure，框架整个事务重试；不能仅用advisory lock后继续使用旧快照。独立并发探针真实建立多个旧快照，只重试serialization，deadlock直接失败。

换区在target queue hook接受后才撤旧位置/旧合成呼叫，并将旧任务pending；撤旧active在新位置INSERT前flush，数据库部分唯一索引保证同canonical患者最多一个active位置。任何后续失败回滚新旧双方。跨店既有位置必须在原店明确处理，不能由目标店任意撤旧。任务missed_count不会被重报、作废、换区清零；真实排序/优先级归S06。

## 状态、版本与动作

所有入口经`_operate(action,payload,key)`，key为1—160字符且actor范围唯一；fingerprint包含动作/当前门店/完整参数。重复同key返回原receipt，异参数拒version_conflict。新增动作无需既有对象版本；维护动作必须带该源对象整数version。私有downstream入口另外要求固定服务器授权，HTTP普通action不能执行start/derived。每次动作实时校验S01会话revision、门店、权限和实际坐诊限制；菜单隐藏与字段readonly均不作为授权。

|动作|前置及权限|原子副作用/失败恢复|
|---|---|---|
|catalog/catalog_edit|本店price write+集团主数据；维护校验version|原生产品+集团目录；只能受控建项/名称/启停；失败无半目录|
|mapping/mapping_edit|本店price write；明确活动能力和本店报到/执行区|建立或启停映射，不把全景换成CBCT；已选映射失效时报到拒绝并保留原对象|
|price/review/publish|本店price write；draft→reviewed→published及version|原生固定规则与版本一体；冲突/替换失败完全回滚|
|snapshot|本店price write；写会话检查；显式demo策略与唯一来源|不可变演示快照及receipt；无有效价失败；原来源恢复不重算|
|reserve/register|本店frontdesk write；patient/mapping/真实槽/渠道|受控relation、claim、资格和独立任务；失败全部回滚；不自动到店|
|arrive|本店frontdesk write；canonical patient|实际当天到店与S04首次到店；重复复用历史事实|
|report|本店frontdesk write；task version/未开始/有效资格/已到店/区域open|受理位置+固定队列hook，成功才撤旧；相同任务返回原位置|
|walkin_report|同上，现场只限当天|register+arrive+report一体，任何失败无半扣/半建|
|void|本店frontdesk write；task version/未开始/原因/明确取消标志|仅撤位置和呼叫→pending；保留资格、未做来源和过号；取消标志另触发cancel|
|cancel|本店frontdesk write；entitlement version/held/原因|撤位置、取消资格和任务，经S03仅返一次；重复key或新key当前取消版本无重复释放|
|reschedule|本店frontdesk write；held/version/同服务/明确新槽和原因|S03新占+旧取消成功才改变资格/任务并撤旧位置；目标满额留原全部值|
|refer_timed|来源店medical/exam write；实际S05源任务/version/current relation/目标法人范围|受控取得目标预约claim、relation和任务；失败不改变来源接诊、无半转诊；到店不重扣|
|refer_untimed|同来源授权；明确未来有效期|只建目标待受理转诊，无claim/到店；7天只是合成值|
|accept_referral|目标店frontdesk write；pending/version/未过期/区域open/现场额|取得当天目标现场资格和任务，记录真实到店；无额/停接/过期不变，不静默延期|
|start（private hook）|未来可信临床服务器授权；accepted task/version/位置持有|唯一资格consume→started，撤受理位置；随后不可返额/普通作废；当前仅合成适配实测|
|derived（private hook）|未来可信真实接诊来源；started/done source/version|同接诊续诊保留原服务能力；外部派生明确目标，不重扣原门诊容量，报到仍检查目标open；相同父任务/映射/类型复用未结束后继|

作废位置不是医嘱取消、临床完成、费用退款或自动返额；取消资格才调用S03。未开始取消按S03开始前原池、开始后同槽现场、过期/不可售释放到unavailable，已consume不返。患者返回时未取消有效资格复用，已取消/过期需明确新受理。真实医嘱/退款系统没有提前实现。

任务状态：pending→accepted→pending（作废/换任务/成功改期），未使用资格取消令task cancelled；private start令accepted→started。done仅为未来下游终态契约，当前没有真实完成入口。资格held→cancelled或started。位置只active→false并保留原因；不物理删除。未取消但过期资格保持历史held记录，报到按槽结束时间拒绝，取消可显式释放而不造未来供给。

## S04真实merge联动

`_active_business`返回真实S05资格held/started、task pending/accepted/started、active位置及未过期pending转诊；started task用execution类别，阻断合并。双方各有活动业务阻断；仅单方未执行活动可以迁移。

`_migrate_business`只更新这些live对象的canonical patient和乐观版本；origin、作者、身份快照、claim、映射及真实arrival不重写。目标没有冲突才迁移，任何写失败回滚整次S04 merge。过期不定时转诊保留历史，不继续作为live对象。测试模块通过super同步自己的合成队列canonical引用；它不代替真实S05活动hooks。

## 错误、审计、下游复验

正常结果accepted/already_accepted；S05位置基础输出queue_status=NOT_RUN，合成适配输出synthetic_waiting，不能当真实S06入队。业务错误含access_denied/version_conflict/insufficient_balance/missing_price/reporting_closed/referral_expired/handover_required；框架ValidationError或UserError的文本可翻译，稳定前缀保持。恢复用原key/来源/对象；版本冲突刷新，不覆盖旧页。controller权限拒绝403，其他受控业务冲突409，CSRF400；未预期程序异常不会伪成功。

成功动作在同事务保存receipt和S01审计，actor是真实发起人，转诊受控派生不改成目标管理员身份；HTTP失败在业务savepoint回滚后另留denied审计。模型层没有手工commit。读取/导出继续S01源权限与export write双校验；原生RPC绑定真实SID而不接受客户端binding对象。S05患者行政任务禁止未分类附件承载病历；无正式文书附件/患者账号/通知渠道。

S06真实waiting/calling、过号排序、租约、保留/直返/交还/追加、日终：NOT_RUN。S08真实医嘱与发起转诊、S09真实外检、S10真实收费和退款：NOT_RUN。正式生产价格政策、S03生产渠道参数和容量策略未由演示发布；以后所属阶段按当前批准参数复验。
