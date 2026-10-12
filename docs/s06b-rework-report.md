# S06-B定向修正交付报告

本次只处理[GPT-REVIEW6118213551](https://github.com/Yredxin/YDental/issues/30#issuecomment-6118213551)的三个BLOCKER。沿用分支`codex/s06-b-continuation-r1-20261012`，原B最终`ebaeec101bf2df76c26f91202deba01a88220f09`与全部历史成功/失败材料保留。以下为Codex自测，不代表GPT技术复核、用户验收或生产批准。

## 固定版本

- 原A基线：`e13eaa2d48f11dd1193080a40ae2f31f58ddfa15`。
- 原B product/test/final：`7816d8ab5872f7e6e56edcc366b461049ae9ac9d` / `a9bcf1c426274ad75e14dc6bada3e6cf333727d9` / `ebaeec101bf2df76c26f91202deba01a88220f09`。
- 修正product：`f0710bf89da396f580fe11564ebee4c51f655178`。
- 修正test：`ba9eae8367cf598e7367ad439a5a5ec81be91a20`。
- 修正final：固定于#30修正交付评论，不在本文件自引用。

product→test只有测试及验证脚本；test→final只有AGENTS、文档与脱敏证据。原A21/B12/A36/B29验证源码保留，除证据目录外没有改原逻辑，见`docs/evidence/s06b-rework/continuity.json`。产品tree在固定测试后不漂移。

## 三个修正

1. verify execution支持显式现场确认、可信保存后接手：旧段interrupted、新serving链接旧段并绑定新lease；verify hold支持显式现场确认、保存后交还并创建唯一续诊。业务write/当前店/active员工/精确能力/可信资质均重验，无管理员force-release；旧actor/lease/history永久保留，竞争只允许一次成功。实际执行与保留分开处理，不伪造治疗完成。
2. active/verify hold限制report/call/start：普通Care/source task拒绝，初始可信exam/pharmacy正常，额外target必须经过可信server hook，客户端context/dict无效；hold终态后普通资格恢复。
3. revoke仍原子撤号码且closed当下不能start，entitlement/claim保持held；区域后来open时同一task可普通report/call/start，历史revoked不永久污染资格，无新permit及重复扣返容量。

与第1项直接相关的两个收口：工位switch只阻断未解决段；新链段再超时时按task同步entry显示为verify。没有重写S05 start、A/B锁序、queue/position/lease/token、continuation或追加双权限。

## Project同步

实施前完整分页读取21字段、15条目及全部fieldValues、6视图、7公开workflow。只执行两次单字段mutation：#30执行状态进行中→返工；#29执行状态返工→待用户验收。两次完整读回相同，深差异仅两个字段的name/optionId四个叶值，原生Status均Todo、阶段S06/S05及Issue OPEN不变，所有其他字段/条目/视图/workflows不变。证据在`docs/evidence/s06b-rework/project`。复用只读S00快照工具的历史scope标签，不代表实施S00；查询内容为本次真实Project完整元数据。交付后#30保持返工，不自行改待复核。

## 最终隔离运行

全新库：`ydental_s06b_test_20261012053943_5c4370e3`；仅合成数据，未接管旧库。复用`scripts/s06b.py`，端点/cluster/OID/创建记录、独立配置/data/log/dbfilter、端口18129、精确preview PID/config hash、外发guard均校验。核心固定`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，本地声明20.0；无官方同SHA上游核对声明，无核心/系统依赖/既有服务修改。

|验证|固定test的新库结果|
|---|---|
|install|84项，0 failed / 0 errors|
|upgrade|82项，0 / 0；实质62模型 + 20真实HTTP/RPC|
|A原真实双连接|21/21 PASS|
|B原真实双连接|12/12 PASS|
|新增真实双连接|4/4 PASS：verify execution两人、verify hold两人、Care vs可信外检报到、reopen vs普通report后start|
|竞争总计|37/37；deadlock=0；backend PID不同，有界RR重试记录保留|
|Firefox A|36/36，14图，pageerror=0|
|Firefox B原路径|29/29，10图，pageerror=0|
|Firefox新增|18/18，9图，pageerror=0；默认全部4场景，新增三类视觉路径齐全|
|guard|5/5 PASS|
|真实导出翻译|230/230；missing=0，invalid code metadata=0|
|迁移|A形态旧约束/旧行 + 真实模块upgrade PASS|

最终83项Firefox/33图；新增9图已逐一人工目视核对。预览仅停止本次精确PID，旧服务未动；新库、失败库及日志保留。`final-results.json`汇总、`model-http-counts.json`实数拆分、`blocker-matrix.json`映射新测试、`concurrency-summary.json`/原始脱敏probe结果及三批browser summary对应完整证据。原始日志只留本机，提交日志hash。

A形态迁移fixture在新库内制造旧lifetime约束与旧execution空task/snapshot，再运行真实模块upgrade及迁移检查；不是打开历史A库或冒称安装完整A tree。额外的open/closed输入仅guard内合成现有S03状态，不实现S06-C营业状态机。

## 失败链

首个中间新库`ydental_s06b_test_20261012052753_3abef9ad`与所有私有日志留存；脱敏行动记录/日志hash在`runtime-history`，原始日志/config/access不提交。

- install 82项：1 failed，负向能力夹具用[]未真正清空Many2many；改用明确set空集合。
- 首次upgrade 80项：1 error，旧队列行夹具复制了原号码，触发正确的号码唯一约束；改为独立合成号码。
- 修正后中间upgrade 81项通过，A21/B12+新增4组竞争通过；中间结果不充当最终固定版本的新库证据。
- 提前调用probe被全局runner锁拒绝，未接管/停止服务；随后正常执行。
- 新Firefox首次5项/1图后失败：把position连接状态当作serving执行状态，修正断言为实际queue row；失败summary/截图保留。剩余场景独立诊断12项/7图通过；最终要求默认全部场景重跑。

历史`docs/evidence/s06b`及所有更早失败完全保留，不覆盖为PASS。

## 工程材料与停止边界

补充契约/字典`docs/s06b-rework-contracts.md`、安全自查`docs/s06b-rework-security-review.md`、本报告及`docs/evidence/s06b-rework`共同适用；原A/B契约中被本修正明确覆盖的描述成为历史。

保存和额外外检来源在产品中仍默认fail-closed；真实S08文书/医嘱/发药没有接入，只用guard内冻结server来源验证。不声称医疗完成。生产心跳、超时、N未批准；测试2秒/20秒/N=2不当正式政策。S06-C、S07库存及真实S08/S09继续NOT_RUN。

固定版本推送本分支，#30写`[CODEX] S06-B修正交付与复核申请`并逐字读回后停止。没有自动合并、强推、关闭#30、启用下一批或生产发布。
