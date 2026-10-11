# [CODEX] S04交付验收申请｜YD-N1 R1

本批由用户明确启用#28，申请GPT技术复核；用户效果验收留待最终统一验收。执行边界为[GPT-ACTIVATE 6111275379](https://github.com/Yredxin/YDental/issues/28#issuecomment-6111275379)。2026-10-11 16:46 UTC完整读取#23当前R1正文/全部有效评论、#28正文/全部有效评论和#27最终技术复核/状态同步；[开工检查6111333171](https://github.com/Yredxin/YDental/issues/28#issuecomment-6111333171)先写回逐字读回，再实施。交付前再次读取#28正文/全部2条评论，启用边界没有变化。未回读撤销计划、旧四份文件或上一聊天补需求。

## 固定版本和实际环境

|项|实际值|
|---|---|
|独立仓库/远端|`/home/redxin/code/odoo/odoo-sd/code/sd-addons` / `Yredxin/YDental`|
|分支|`codex/s04-patient-r1-20261011`；未创建PR，不自动合并|
|开工基线|`a8c0d5a2f5963e1f3dd2c31e4d363115453d2be3`，开工工作区干净|
|固定product|`eb607750a4b35885f37acfb07d504f758b877b73`|
|固定test|`a35af92ef89465dbbf71cb6f88297e4c097b43c7`；较product只修改测试/探针，无产品变更|
|固定final|包含本报告、契约、字典、安全复核、证据及AGENTS的最终文档提交；完整SHA固定于#28交付评论。较test不改产品/测试|
|Odoo核心|`Yredxin/odoo@f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，本地声明20.0；fork无父根快照，不冒称已核对同SHA官方上游|
|Python|核心`../.venv/bin/python`；不改核心或系统依赖|
|最终隔离库|`ydental_s04_test_20261011173847_fa641b13`；创建记录/OID/配置SHA见[隔离证据](evidence/s04/final-isolation.json)|
|运行范围|合成身份；127.0.0.1:5432/odoo，cluster7694897083368259627；独立配置/data_dir/log，18106，精确dbfilter、list_db=False、cron=0、外发限制。既有服务/业务库/历史库不接管|
|依赖|原生+自研，无OCA。phonenumbers9.0.16仅`.local/s04-deps`；wheel SHA256已固定。复用既有进程本地Firefox155/字体/动态库，默认sandbox，无系统安装|

## 需求完成情况

|需求/功能|完成情况|实现位置及边界|
|---|---|---|
|R01命名、时间、翻译、字典、动作、证据|本批完成|`ydental_patient`、本报告、[契约](s04-contracts.md)、[字典](s04-data-dictionary.md)；原生导出224/224中文|
|R22集团身份/号码/门店关系|本批完成|独立patient/number/relation；唯一sequence与数据库约束；归档、旧号canonical解析、真实首次到店；没有预约/报到任务|
|行政联系方式/联系人/监护/疑似重复|本批完成|独立contact及行政partner；按显式地区规范化，无法确认保留原值；姓名+出生/患者及联系人电话邮箱提示，不自动合并；不设监护年龄/证件门槛|
|门店申请、集团核实合并|本批完成|merge/service，申请及身份版本、actor-key回执、固定fence和事务迁移；拒绝/冲突/失败可恢复，旧身份与历史快照保留|
|R04行政/医疗隔离及真实患者care|本批完成|S01source/access/audit扩展，可信PatientCareScope；跨店医疗只读留痕、跨店写及财务源拒绝；partner、查询/导出/附件旁路保护|
|本店文书政策提示|本批完成|policy及私有document hook；未批准/无正文待完善，批准正文待核验，不继承旧店已签，不阻断无关建档|
|活动业务/原单/PDF真实联调|NOT_RUN|仅固定server hooks及合成测试保护；不创建S05/S06/S08/S09/S10/S12业务模块或空壳|

## 流程实际回放

|流程|合成前提/操作|实际结果|证据|
|---|---|---|---|
|F1跨店查档与新关系|B/C背景的同一患者，在A行政查档/建A关系/记录实际到店；A医生无B/C工作membership|同主档、同店关系不重复；提前建档无到店；医生按用途读C安全背景留痕，外店写403；前台不见医疗链接/内容|T01/T06、HTTP、Firefox01/04|
|F2共电话与集团合并|两合成身份共用保留测试电话；前台新增联系人/声明监护、改名；门店申请，集团确认，按旧号查询|只提示疑似重复；前台无确认控件；集团确认后旧号回主档，原身份/联系人/快照不改写|T02/T03/T07、Firefox02/03/05|
|F3活动冲突与恢复|两档都有合成有效queue/execution；集团确认；关闭活动后按新申请版本再确认；迁移hook中途抛错|先blocked列患者/类型/引用；活动处理后可确认；中途异常不留半迁移或幂等回执|T04/T10、final-probe merge_samples|
|F4本店文书|B有合成signed_fact，A无政策/批准但无正文/批准且有正文|A依次待完善/待完善/待核验；不产生A签署事实，仍可行政建档|T09；不使用真实签名/PDF|

## 测试结果

命令统一从独立仓库用核心Python运行，`--db ydental_s04_test_20261011173847_fa641b13 --port 18106`。实际时间、固定test SHA、退出码、测试数及私有日志SHA见[runtime-history.json](evidence/s04/runtime-history.json)，不公开原始运行日志。

- `scripts/s04.py install`：exit0，0 failed/0 error，30 tests（S04模型20+HTTP8及底座2）。
- `scripts/s04.py probe`：exit0，7/7真实多连接竞争，独立RR快照/有界重试；[final-probe.json](evidence/s04/final-probe.json)包含实际schema100字段、引用前后数、冲突、unique/canonical/account断言。
- `scripts/s04.py upgrade`：exit0，0 failed/0 error，S04模型20+HTTP8=28 tests。probe持久化的号码/关系仍由随后浏览器访问与旧号查询验证。
- `scripts/s04.py export`：exit0；原生224terms，zh_CN224/224，无缺失/模糊条目；[translation.json](evidence/s04/translation.json)。
- `scripts/s04_browser.py`：真实Firefox155、22/22 PASS、5幅合成截图、无pageerror；完整固定提交/截图SHA见[final-browser.json](evidence/s04/final-browser.json)。
- `python -m unittest discover -s scripts -p test_s04_guard.py -v`：5/5 PASS，exit0；错库、错端点、既有端口、外发DNS、其他本机服务均拒绝。Python AST及git diff空白检查通过。

|TC|本批结果|实际断言/角色/证据|未来真实回归|
|---|---|---|---|
|S04-T01|PASS|跨店同档/关系幂等、预建无到店、真实首次UTC/当地业务日；前台/集团；模型与HTTP/Firefox|S05预约不能伪造到店：NOT_RUN|
|S04-T02|PASS|共电话、同名生日、联系人phone/email只提示；有地区E164/无地区不猜/无效及分机保留人工；模型/前台Firefox|无|
|S04-T03|PASS|门店确认拒绝；集团确认旧号可查、原partner不合并、历史快照保留；模型/HTTP/Firefox|无|
|S04-T04|PASS（基础及合成）|同key/异payload/旧版本/拒绝恢复、迁移中途回滚；7组真实数据库竞争；集团/前台|S05/S06真实新业务互斥NOT_RUN|
|S04-T05|PASS|前台read/search/name/count/group/export/attachment/public/HMAC、partner Notes/chatter/反向字段、defaultcontext/附件改挂负向；医疗合法token下载留痕；模型/HTTP|正式临床及PDF附件源后续复验NOT_RUN|
|S04-T06|PASS（实际patient scope）|A医生无C membership按真实patient+purpose读C、audit；伪context/另会话/撤权/其他患者附件/跨店write拒绝；合成settlement拒绝；模型/HTTP/Firefox|S08/S09真实源、S10原生凭证NOT_RUN|
|S04-T07|PASS（合成历史）|更名及合并后origin/author/snapshot原样；关系重叠保留最早真实到店及被替代历史|S08/S10/S12真实原件NOT_RUN|
|S04-T08|PASS|全新install及upgrade、稳定唯一号、8连接发号、重复create、rawCRUD拒绝、不创建患者账号/mail或签署；reader/前台/集团|生产迁移/部署NOT_RUN|
|S04-T09|PASS（政策提示及合成签署事实）|B已有合成signed_fact不迁到A；无配置/空正文待完善，有批准正文待核验；建档仍成功；集团/前台|S12正式签署/PDF NOT_RUN|
|S04-T10|PASS（合成保护）|reservation/queue/execution双活动阻断并列清单；单活动执行亦阻断；活动处理后可确认；先业务/先合并两种真实连接顺序无丢引用|S06唯一真实队列/执行与S08真实临床NOT_RUN|

### 合并及并发专项

真实连接探针不是单事务模拟：8路发号分别执行6/8/2/4/5/7/1/3次（含RR重试）仍得到8个唯一号；2路同建档key只建一档；同合并key只合一次；同申请异key一成功一版本拒绝；业务先提交时合并返回冲突；合并先提交时后续重复活动拒绝；双向合并一成功一拒绝且无环。

最终probe：21原始身份、21号码映射，号码唯一且全部指向canonical，无患者登录。request17的source72→target73，来源号码1→0；保留superseded关系1→1；合成活动引用迁移1；request16保留source70/reference9及target71/reference10两条queue冲突，状态blocked。这里`source_after.relation=1`是有意保留的被替代历史，不是第二条当前关系。完整计数及状态见final-probe；真正未来模块未安装，不宣称实际队列已通过。

### 失败及补交保留

[失败说明](evidence/s04/failures.md)和runtime-history保留完整尝试链及日志SHA：初装CSV字段不匹配、测试适配/预期错误、缓存附件读取缺口、探针幂等键碰撞、探针种子导致重复候选顺序假设、Firefox读取只读页面CSRF前提错误。最终均有对应修正及后续通过；失败不被覆盖。浏览器每次独立目录，首轮FAIL后已完成18项检查及后续PASS证据均保留。缺GTK路径的启动失败和停止自建预览后端口仍在退出中的guard拒绝另记录，未接管服务或绕过保护。

## 字段、动作与配置

[数据字典](s04-data-dictionary.md)列出各字段类型、来源、必填/验证、关系/默认及行政/医疗边界；[契约](s04-contracts.md)列各动作权限/状态/事务副作用/重试恢复与server hooks；[安全复核](s04-security-review.md)说明权限旁路及原生API检查。实际解析后的继承metadata见final-probe.schema。

技术初值：原生standard sequence `P`+8位，无缺号承诺；phone明确ISO地区或人工确认；用途只允许diagnosis/history_review；单字段长度及32KiB为入口保护。只有测试集团在合成门店批准合成正文引用，未发布任何生产政策。真实临床字段、监护/证件政策、文书正文/签发、号码生产格式须业务负责人审核；无年龄/证件示例数字或自动合法性认定。没有自动发送/登录/签署。

## 用户效果验证

入口`/ydental/patients`，先在`/ydental/access`选当前门店；菜单位于YDental“患者”。下列已由Firefox在最终隔离库回放，凭据只在该库私有`access.json`，不放仓库/GitHub。

1. 以前台选择A，打开已有合成患者：显示统一患者号、本店关系和文书待完善，医疗入口不可见。
2. 查看共电话疑似重复链接：两个身份保留，没有自动合并。
3. 点“记录实际到店”：首次真实时间出现；提前建档本身不生成到店。
4. 新建未知出生/无地区电话患者，保存声明监护及核实依据：允许建档，电话标人工核实；重新打开资料仍在。
5. 修改行政姓名后回读，新增门店合并申请：前台看到申请，没有集团确认按钮。
6. 以A医生按诊疗用途打开原患者：显示C合成背景及只读提示；读事件留痕，试写C失败。
7. 以集团有权用户确认已核实申请：主档不变，原身份归档及旧号映射保留。
8. 用来源旧号搜索：返回选定主档，仍显示旧号追溯。只读用户没有写表单，伪造写请求403。

5幅图及各步检查见final-browser。页面按功能可用提供中文及基本布局；统一美化仍属于S13。

## 数据、审计与回滚

新增产品模块和专用测试模块，没有修改底座模块、核心、既有业务库或已有服务。患者行政资料只在受控partner维护，临床背景、原始身份快照另存；合并只迁当前canonical引用，原始身份/作者/历史已过账对象及文书不批量覆盖。无费用/库存/资金动作。

复用S01审计记录patient.create/edit/contact/arrival、合并request/blocked/refresh/reject/confirm、source.view/query/export/download、patient.care.open及HTTP拒绝事件；审计只记录动作、目标、版本/数量/用途，避免临床文本、电话及凭据。跨店care不授予B/C工作权；撤权下一请求生效。

回滚范围是本次独立分支及隔离资源：停止经PID和完整配置路径匹配的本次自建预览；无生产部署可回滚。产品合并错误走新事务/人工核实，不提供破坏历史的“拆回”或原生partner merge；失败事务原样回滚。不要卸载产品来删除历史身份，不自动删除测试库/日志或失败证据。预览进程收尾及公开文件隐私/哈希检查见final-checks。

## 复核申请

申请GPT复核固定product/test/final范围和上述证据。S04工程交付适用检查通过不等于GPT已通过或用户已验收；#27/#28保持OPEN，本次未写Project、workflow、原生Status或Issue/PR状态，未自动合并、生产发布或启用S05。#28交付评论写回读回后停止等待GPT。
