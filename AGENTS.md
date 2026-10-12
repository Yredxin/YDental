# YDental 当前执行入口

## 当前 S08-A交付 / #32

- 用户正式启用S08-A，唯一边界为[GPT-ACTIVATE6122378640](https://github.com/Yredxin/YDental/issues/32#issuecomment-6122378640)。完整读取#23/#32正文及全部有效评论、S07最终技术PASS6122197570与状态同步6122311778；[开工检查6122503237](https://github.com/Yredxin/YDental/issues/32#issuecomment-6122503237)写回逐字读回后实施。交付前再读原正文/有效评论无变，仅本次开工评论。
- 固定S07 baseline `a5f53ac72d6d43901932adedc64c56cf6f97c675`，全新分支`codex/s08-a-clinical-doc-r1-20261012`。固定product `a69ac8bc431adb412341cd2fbff508d69ca0b84a`、test `be5f28ef336295633fd0d753c3e97051a2dc457d`；final完整SHA固定于#32交付评论。product→test仅模型/HTTP测试和审计验证，test→final仅AGENTS/文档/脱敏证据，无产品漂移；全部中间提交/失败证据保留。
- 实施前完整读取Project #4的21字段/15条目/6视图及字段/7公开workflow，唯一一次mutation #32执行状态待启用→进行中；两次读回仅name/optionId两叶差异。交付前两次全读回深比较无变化。#32保持S08/进行中/Todo/OPEN，#31待用户验收，其他阶段/workflows不变，不自行转待复核。
- 只交付真实medical接诊工作台、独立document/version、52恒乳FDI/牙面/缺失未知与0不适用、7项结构化草稿、真实自动保存/CAS/独占编辑/断线未同步、文字确认和附原因更正、作者历史、S06真实同事务保存交还/编辑释放/唯一续诊、D1待完善责任交接与D2合法新接诊。保存/确认/补记不生成治疗事实/费用/库存；确认后不能再用confirm绕过原因。
- 仅新增ydental_clinical及guard测试/脚本；S01—S07核心事实/锁序沿用，无反向依赖。临床无测试替身；测试模块仅允许本批新库的S03演示capacity前提，一个reserve/restore场景显式补合成外检前提，真实S09入口继续fail-closed。S07临床库存来源仍默认拒绝；正式字段/签发/阈值未批准。
- 最终全新合成库`ydental_s08a_test_20261012113731_3d646c4f`，固定test install30/upgrade28/带业务upgrade28（21模型+7真实HTTP/RPC，安装额外2原生资产初始化），16/16真实双连接、deadlock0，Firefox28项/11图全部目视核验/pageerror0、中文150/150、guard5，8类SQL0、10组升级签名及6组纯文书经济签名相同。完整结果见docs/s08a-report.md与docs/evidence/s08a/final-tests.json。全部均Codex自测，不代表GPT亲测或用户验收。
- 仅scripts/s08a.py及本批全新隔离S08A库，端点/cluster/OID/创建marker/configSHA/dbfilter/data_dir/PID/端口/外发guard继续。未改历史/业务库、Odoo核心、odoo-12、既有服务/未提交内容/系统依赖；预览只停止精确匹配本次config/PID的进程。原始日志/凭据本机受控保留，仓库仅合成截图/脱敏摘要/hash。
- 初始夹具/HTTP方法名、工位native版本保护、D2展示断言、离线英文错误、原生库存多库位测试前提、4项翻译Python标记、公司负向前提等失败链保留。最终加入文书当前公司范围、未同步重开不伪成功、确认后必须更正等保护；早期PASS不得当最终固定验证。
- S07历史SIGSEGV根因仍未知，生产稳定性/部署继续BLOCKED。本批再次崩溃须立即留证停止，不重装/改核心或掩盖重跑。S08-B实际治疗/经济/药房/4+2/正式转诊、S08-C PDF打印及S09—S13/生产均NOT_RUN；D2实际项目完成未模拟。
- 工程材料docs/s08a-contracts.md、s08a-data-dictionary.md、s08a-security-review.md、s08a-report.md及docs/evidence/s08a。#32发布`[CODEX] S08-A交付验收申请`逐字读回后立即停止等待GPT独立技术复核；不自动启用B/C、不关闭Issue、不改Project/workflow、不合并/强推/生产部署。

下方S07及更早“当前/本次”均为历史记录，本轮以本节及最新S08-A GPT-ACTIVATE为准。


## 当前 S07定向返工交付 / #31

- 用户仅授权[GPT-REVIEW6121445246](https://github.com/Yredxin/YDental/issues/31#issuecomment-6121445246)两项代码缺口和SIGSEGV证据。完整读取#23正文/全部有效评论、#31正文/全部有效评论，沿用原分支`codex/s07-inventory-r1-20261012`；固定baseline `f23ad62b20aa298b74adc993781863961946aec3`，原交付/失败/SIGSEGV证据保留。
- 新product `eb826219b008e8ebdf2073fc020a813f88764ecc`、test `12730d0f69ddbbd4e21c5df76e0bc9e0c0480061`；final完整SHA固定于#31修正交付评论。product→test仅测试断言/Firefox角色隔离，test→final仅AGENTS/文档/脱敏证据，无产品漂移。
- 只修可信临床来源类别（treatment=material、chairside/prescription=medicine）与原pending历史补账。仅已真实发生的不可普通改写来源，经当前店warehouse-write、原摘要/价格/时间/类别、足够余额及原pending之后本店同lot/目标库位的done真实入库/正向盘点证据，补原event唯一move；保留原价/责任人/实际时间，固定correction_id/reconciled_at及审计。普通issue/临床新执行/退回release继续禁过期停用，不改lot效期或假启用。
- 最终两个全新S07库`ydental_s07_test_20261012094527_249b480f`及`ydental_s07_test_20261012094527_bbbbcece`，各install50、upgrade48及带业务再upgrade48（模型34+真实HTTP/RPC14；安装额外2资产初始化），各22/22独立双连接、deadlock0；各Firefox63项/12图/pageerror0、全部24图目视核验；中文223/223、guard5，46个committed event/8类SQL0错误，五组账本签名升级前后相同。均Codex自测，非GPT/用户验收。
- 16aef9c先复现6个类别失败/2个恢复错误；c193bae暴露同秒旧入库误选，eb82621增加ID顺序；2535699 Firefox测试前台权限改变原仓库负向前提，12730d0分离医疗只读比较账号后另两新库重跑。全部失败保留，不冒称旧PASS为最终验证。
- SIGSEGV原日志/故障证据保留，新干净进程完整回放无再现；原固定be4a282另提取274个addon源文件与Git字节核对，在新库/独立进程诊断install42/probe12/Firefox36项10图均PASS，未再现。根因仍未确认，环境/运行风险与正式部署BLOCKED继续，不称已修复或生产稳定性通过，不改核心/依赖。
- 本轮Project 0 mutation，完整读回21字段/15条目/6视图/7公开workflow，交付前两次深比较无变化；#31 S07/进行中/Todo/OPEN，#30待用户验收，后续待启用，不自行转返工/待复核。
- 继续S07端点/cluster/OID/创建marker/config/dbfilter/data_dir/PID/端口/外发guard；仅新增隔离库和自己匹配PID的预览，历史库/核心/odoo-12/既有服务/系统依赖不动。补充docs/s07-rework-{contracts,data-dictionary,security-review,report}.md及docs/evidence/s07-rework。
- #31写`[CODEX] S07定向修正交付与复核申请`逐字读回后立即停止等待GPT。真实S08/S09/S10/S11及生产NOT_RUN；不启动S08、不关闭Issue、不改Project/workflows、不合并/强推/生产部署。

下方原S07及更早“当前/本次”均为历史记录，本轮以本节及最新GPT-REVIEW为准。

## 原 S07交付 / #31

- 用户正式启用S07，唯一边界为[GPT-ACTIVATE6119956887](https://github.com/Yredxin/YDental/issues/31#issuecomment-6119956887)。已完整读取#23正文/全部有效评论、#31正文/全部有效评论、S06最终技术PASS6119723325和状态回执6119803450；[开工条件检查6120104358](https://github.com/Yredxin/YDental/issues/31#issuecomment-6120104358)写回逐字读回后实施。交付前正文/有效原评论不变，仅本次开工评论；完整Project再读深比较相同。
- 固定S06-C基线`46833f0ac4bd37b778f3a5a80d51be430e4ebde6`；新分支`codex/s07-inventory-r1-20261012`。固定产品`916492719e5d299fa0326330ac798cd6cda237bd`、测试`be4a282dc0ebb54fc32dfafa7ac05cfa7535d939`；final完整SHA固定于#31交付评论。product→test只有原生单位修改负向测试，test→final仅文档/AGENTS/脱敏证据；原失败与中间提交全部保留。
- 实施前完整读取Project #4的21字段/15条目/6视图/7公开workflow，仅授权一次#31自定义执行状态待启用→进行中，两次完整读回深差异仅该name/optionId。第一次TLS读超时未重复mutation。#31保持S07/进行中/Todo/OPEN，#30 S06/待用户验收/Todo/OPEN，#29待用户验收；其他条目/字段/视图/workflows不变，不自行转待复核。
- 只交付原生product/stock/uom/product_expiry与自研受控库存：本店warehouse/三类业务库位/真实quarantine、store×native lot生命周期、单位精度/批次效期启停、实际收发/盘点/同法人调拨、来源和请求幂等、实退核查、原事件pending恢复/原价保留、最小工作台/预警/审计和扫码fail-closed。原生quant/move为数量唯一事实，无平行余额；不重写S01/S03/S04/S05/S06。
- 最终新库`ydental_s07_test_20261012085648_03913c2a`，固定test install42/upgrade40/带已提交业务再upgrade40（S07模型29+真实HTTP/RPC11；install额外2原生资产初始化，不冒称完整JS测试）。12/12真实双连接竞争、deadlock=0，Firefox36项/10图且全部目视核验、pageerror=0，guard5、实际导出中文218/218；最终29个已提交事件及7类SQL不变量均0，event/batch/move/move_line/quant五组升级前后签名相等。均为Codex自测，非GPT或用户验收。
- 仅`scripts/s07.py`及本次全新S07合成库；创建记录/端点/cluster/OID/config/data_dir/dbfilter/PID/端口/外发guard继续，旧库不接管/重置/删除，核心/odoo-12/既有服务/系统依赖不改。只停止匹配本次专属config/PID的预览。工程材料为docs/s07-contracts.md、docs/s07-data-dictionary.md、docs/s07-security-review.md、docs/s07-report.md及docs/evidence/s07。
- 默认产品临床来源hook拒绝；测试适配器只认本次guard库+进程+冻结Python来源。S05真实演示价格重价99后恢复仍原20；合成费用引用不是实际费用单。真实S08文书/治疗/分次发药、S09检查、S10收费退款/跨法人交易、S11加工单、生产阈值/50会话/发布均NOT_RUN。演示near60/wait0/low3不是生产批准；采购订单/应付未建设。
- 早期ACL/native建议行/负向及价格时间夹具/Firefox303误判、证据脚本误记核心SHA均保留；最终新库修正重跑。原生单位factor/祖先路径不可普通修改，observed盘点不得走pending执行恢复，batch是门店批次生命周期唯一权威。历史S00—S06全套UI/并发本批未重跑，不冒称全项目验收。
- 最终Firefox首次在登录选店后、本次库存动作前遇专属预览SIGSEGV；只读仍10份、无出库事件。仅重启本次预览后36项/10图通过，原失败/runner245/恢复摘要保留；底层原因未确定，不称根因已修复或生产稳定性通过，交GPT复核裁定。
- #31发布`[CODEX] S07交付验收申请`并逐字读回后立即停止等待GPT独立技术复核，不称已验收/生产通过，不启用S08、不关闭/合并/强推/生产部署。

下方S06-C及更早“当前/本次”均为历史记录，本次授权以本节及S07启用为准。

## 当前 S06-C交付 / #30

- 用户明确启用#30/S06-C，唯一边界为[GPT-ACTIVATE6118760114](https://github.com/Yredxin/YDental/issues/30#issuecomment-6118760114)。已完整读取#23当前总计划/有效评论、#30正文/全部有效评论、S06-A最终技术PASS6117519348及S06-B原复核6118213551/修正技术PASS6118669357；[开工检查6118793557](https://github.com/Yredxin/YDental/issues/30#issuecomment-6118793557)写回逐字读回后实施。交付前重读正文/原评论未变，仅新增本次开工评论。
- 固定B基线`a32ab4c6bab76aaabc45e1917ad06444d6a2b71c`；全新分支`codex/s06-c-day-push-r1-20261012`。固定C产品`776d4dfb67ccdb61d4fa98f7dbf09ac943b091d9`、测试`cce0aa2ec04ac590fc182f7279b36812e4e4760a`；最终文档证据SHA固定于#30交付评论。product→test仅测试；test→final仅文档/AGENTS/脱敏证据。原A/B及本次失败链全部保留。
- 实施前完整读取Project #4的21字段/15条目/6视图/7公开workflow。#30已是S06/进行中/Todo/OPEN，按本次条件授权0 mutation；#29保持S05/待用户验收/Todo/OPEN。实施前及交付前完整读回深比较无差异，不改workflows/其他条目，不自行转待复核。
- 只交付复用S03 capacity-write的open→draining→closed、合法已受理清队、closed append/hold例外、门店当地00:00/00:10与幂等水位/延迟补跑、跨日历史queue segment真实升级兼容、原生bus事务最小scope/version、DB snapshot校准及可撤高熵摘要token区域屏。serving/verify/hold不强终止，旧号/日期/missed/permit不复活，不退款/返容量/标完成/删除。保存hook继续默认fail-closed，无管理员remote force-release。
- 最终全新库`ydental_s06c_test_20261012070143_6a254bfc`。固定test install103/upgrade101（78模型+23真实HTTP/RPC）；原A21+B16+新增C16=53/53真实双连接、deadlock=0。Firefox A36/14图+B29/10图+B返工18/9图+C34/9图共117项/42图，pageerror=0；新增最终9图已目视核验。guard5、翻译282/282、B形态约束/行夹具+真实-u迁移均Codex自测通过，不代表完整旧B源码树安装升级、GPT或用户验收。最终只读核对682个committed outbox各恰有一条实际原生bus消息，live互斥/水位/清理审计无重复。
- 仅`scripts/s06c.py`及本次全新C隔离合成库；创建记录/端点/cluster/OID/config/data_dir/dbfilter/PID/端口/外发guard继续。旧库不接管，核心/既有服务/系统依赖不改；只停止了匹配config/PID的本次预览。工程材料为docs/s06c-contracts.md、docs/s06c-data-dictionary.md、docs/s06c-security-review.md、docs/s06c-report.md及docs/evidence/s06c。
- 心跳/超时/N未生产批准，00:00/00:10按确认业务语义实现；cron频率/worker/WebSocket代理部署/50会话性能仍待责任阶段验证。S07库存、真实S08文书/保存/发药、S09结果、S10收费、生产发布均NOT_RUN。
- #30写`[CODEX] S06-C交付验收申请`并逐字读回后停止等待GPT技术复核，不称用户验收或生产通过，不启用S07、不关闭/合并/强推/生产发布。

下方S06-B及更早“当前/本次”均为历史记录，本次授权以本节及最新C启用为准。

## 当前 S06-B定向返工 / #30

- 用户明确只修[GPT-REVIEW6118213551](https://github.com/Yredxin/YDental/issues/30#issuecomment-6118213551)三个BLOCKER，继续当前S06-B会话/分支`codex/s06-b-continuation-r1-20261012`。原最终`ebaeec101bf2df76c26f91202deba01a88220f09`及全部历史失败证据保留。
- 本次单独授权Project #30执行状态进行中→返工，并补执行#29旧授权返工→待用户验收。实施前完整读取21字段/15条目/6视图/7公开workflow，仅两次字段mutation后两次完整读回深差异仅两个字段四个name/optionId叶值。原生Status均Todo、阶段S06/S05、Issue OPEN及其他字段/条目/视图/workflows不变。#30保持返工，不自行转待复核。
- 只修verify现场处理出口、active/verify hold的可信exam/pharmacy目标限制、revoked permit在open后普通资格恢复。实际verify保存后现场接手：旧段interrupted/新serving链接旧段；hold verify保存后交还续诊。旧actor/lease/history不改，新持有人新server-bound lease，两个合格人竞争只能一次成功，无管理员remote force-release；保存hook默认fail-closed，不伪造医疗完成。
- 修正产品固定`f0710bf89da396f580fe11564ebee4c51f655178`，测试固定`ba9eae8367cf598e7367ad439a5a5ec81be91a20`；最终文档证据SHA固定于#30修正交付评论。补充docs/s06b-rework-contracts.md、docs/s06b-rework-security-review.md、docs/s06b-rework-report.md及docs/evidence/s06b-rework，原字典与新增interrupted/resolution_lease补充共同适用。
- 最终新库`ydental_s06b_test_20261012053943_5c4370e3`，固定test install84/upgrade82（62模型+20真实HTTP/RPC），A原21+B原12+新增4真实双连接37/37、deadlock=0，Firefox A36/14图+B29/10图+新增18/9图共83项/33图、pageerror=0，guard5、翻译230/230及A形态真实upgrade迁移均Codex自测通过；不代表GPT/用户验收。新增9图已目视核对；中间模型/夹具/视觉失败链完整保留。
- 继续scripts/s06b.py及新库/端点/cluster/OID/config/dbfilter/PID/端口/外发guard；旧库不接管、核心/既有服务/系统依赖不改。生产心跳/超时/N未批准；真实S08保存/文书、S07库存/真实发药、S06-C日终/推送均NOT_RUN。
- #30写`[CODEX] S06-B修正交付与复核申请`并逐字读回后停止等待GPT复核，不称用户验收/生产通过，不启用C/S07、不关闭/合并/强推/生产发布。

下方S06-B原交付及更早“当前/本次”均为历史记录，本次授权以本节及最新review为准。

## 当前 S06-B交付 / #30

- 用户明确启用#30/S06-B，唯一业务边界为[GPT-ACTIVATE6117541343](https://github.com/Yredxin/YDental/issues/30#issuecomment-6117541343)。已完整读取#23正文/最新有效评论、#30正文/全部有效评论及S06-A最终技术PASS6117519348；[开工检查6117569945](https://github.com/Yredxin/YDental/issues/30#issuecomment-6117569945)写回逐字读回后实施。交付前重读边界未变。
- S06-A最终`e13eaa2d48f11dd1193080a40ae2f31f58ddfa15`及全部失败/补交证据保留。新分支`codex/s06-b-continuation-r1-20261012`；固定产品`7816d8ab5872f7e6e56edcc366b461049ae9ac9d`、测试`a9bcf1c426274ad75e14dc6bada3e6cf333727d9`，最终文档证据SHA固定于#30交付评论。
- 本次单独授权Project #30自定义执行状态返工→进行中；已完整读取21字段/15条目/6视图/7公开workflow元数据，仅一次mutation后两次完整读回深比较仅此值改变。原生Todo、阶段S06、其他字段/条目/视图/workflows及Issue状态不变；保持进行中，不自行转待复核。
- 只交付历史execution保留/未解决部分唯一、外检独立hold、查询提示/原医生确认恢复、默认fail-closed保存前置交还、唯一门诊continuation及显式双权限task-bound追加permit/撤销与start原子竞争。S03/S04/S05/S06-A内核沿用；不删除历史，不把hold当actual execution，不复制外检能力到门诊。
- 仅`scripts/s06b.py`及全新`ydental_s06b_test_14位时间_8位hex`隔离合成库，端点/cluster/OID/config/dbfilter/PID/端口/外发guard继续成立。S00—S06-A工具/库只历史保留、不接管；核心及既有服务/系统依赖未改。迁移验证仅新B库A形态约束/行夹具+真实-u，不冒称完整旧A源码树升级。
- 最终全新库`ydental_s06b_test_20261012045322_4fb99b9b`，固定test安装73/升级71（54模型+17真实HTTP/RPC）、A21+B12真实双连接、Firefox A36项/14图+B29项/10图均0 pageerror、guard5及翻译219/219全部Codex自测通过，不代表GPT或用户验收。
- 工程材料为docs/s06b-contracts.md、docs/s06b-data-dictionary.md、docs/s06b-security-review.md、docs/s06b-report.md及docs/evidence/s06b；失败链全部保留。产品目标来源/保存hook默认拒绝；合成文书和来源受新库guard保护，心跳/超时/N未生产批准。
- 交付评论写回逐字读回后停止等GPT技术复核。Codex自测不代表GPT或用户验收。S06-C/S07/真实S08/S09及生产发布NOT_RUN；不关闭/合并/强推，不自动启用下一批。

下方S06-A及更早“当前/本次”均为历史记录，本次授权以本节及最新B启用为准。

## 当前 S06-A定向返工 / #30

- 用户明确只修[GPT-REVIEW6117074066](https://github.com/Yredxin/YDental/issues/30#issuecomment-6117074066)四个BLOCKER，继续原S06-A会话及分支`codex/s06-a-queue-r1-20261012`。原`840df8921cfb5a70c601e6e8ed81fb7d03aacd5b`及全部原失败/补交证据保留。
- 用户本次单独授权Project #30自定义“执行状态”→“返工”。实施前完整读取21字段/15条目/6视图/7公开workflow元数据，仅一次mutation将待启用改返工，两次完整读回和差异检查仅此值改变。原生Status=Todo、阶段S06、其他字段/条目/视图/workflows及Issue状态不变；保持返工，不自行转待复核，未来其他Project写仍需单独授权。
- 只修verify未解决execution继续约束原actor/执行门店/全局位置、S05 execution area与非空qualification可信server eligibility、call前N发布与mixed missed原rank/机会、统一system timeout审计。原queue/lease/token/S05 start和position内核保留；不实现B接手/交还/追加或C日终/推送。
- 修正产品固定`dfc6ff4a08e3ed80977e114042f08a0491d5ca0b`，测试固定`fe0df66f7ffb55f3895d192f381d9dc7448d2b50`；最终文档证据SHA固定于#30修正交付评论。补充docs/s06a-rework-contracts.md、docs/s06a-rework-security-review.md、docs/s06a-rework-report.md及docs/evidence/s06a-rework；新增两项entry排序字段，原字典及补充契约共同适用。
- 最终全新库`ydental_s06a_test_20261012034435_fa34a4e9`，仅合成数据及受guard保护的测试资质来源。固定test安装50/升级48（37模型+11真实HTTP/RPC）、原16+新增5真实双连接竞争、Firefox36项/14图、guard5、翻译144/144及原32方法连续性均为Codex自测通过，不代表GPT或用户验收。PO metadata、跨店夹具及Firefox失败链全部保留。
- 继续`scripts/s06a.py`及原新库/端点/cluster/OID/config/dbfilter/PID/端口/外发guard；S00—S05及原S06-A库只保留、不接管。心跳/超时/N未生产批准，S08文书hook仍默认拒绝。review提示的execution历史部分唯一和原生账号logout整合仅留后续，不提前实现。
- 修正交付评论写回逐字读回后停止等待GPT复核，不称用户验收/生产通过，不进入S06-B、S06-C或S07，不关闭/合并/强推/生产发布。

下方S06-A原交付及更早“当前/本次”均为历史记录，本次授权以本节及最新review为准。

## 当前 S06-A交付 / #30

- 用户明确仅启用#30/S06-A；唯一边界为[GPT-ACTIVATE6116491783](https://github.com/Yredxin/YDental/issues/30#issuecomment-6116491783)。已完整读取#23正文/有效评论、#30正文/全部有效评论、#29最终S05技术PASS6116482005和状态同步指令6116491290；[开工检查6116516335](https://github.com/Yredxin/YDental/issues/30#issuecomment-6116516335)已写回逐字读回。交付前重读确认正文/启用未变，#29没有另一个同步完成回执，不代写Project。
- S05固定最终`50ac95ac368c8c53bc264d8360c9daa94c0e362b`及全部失败/补交材料保留。新分支`codex/s06-a-queue-r1-20261012`；S06-A产品固定`a2638afc637795a9dc148299f2075e0413b32f0e`、测试固定`8d0b347be18574c75d96673ce1264923bd98bcec`，最终文档证据SHA固定于#30交付评论。
- 只交付真实S05队列hook、waiting/calling全局唯一位置、工位lease、无排班合法坐诊、空闲原子换椅、精确能力/回诊/真实过号、最小真实serving及掉线verify互斥、心跳/session/token/撤权、班次提醒和全局坐诊显示。S03/S04/S05原权威通过上层继承复用，不重写账本/merge/价格快照。
- S08真实文书未建；产品固定server hook默认fail-closed，独立文书锁仅新库guard下合成测试。心跳/超时/过号N未生产批准；测试2秒/20秒/N=2不能当正式配置。B/C保留交还/人工追加/日终/推送、S07及真实S08/S09均NOT_RUN。
- 仅`scripts/s06a.py`和全新`ydental_s06a_test_14位时间_8位hex`隔离合成库。最终库`ydental_s06a_test_20261012025405_2fd04bd7`安装34、升级32、真实双连接16组、Firefox26项/10图、翻译135/135全部Codex自测通过；不冒称GPT或用户验收。原S00—S05工具/数据库只保留，不接管；端点/cluster/OID/config/dbfilter/PID/端口/外发guard不能绕过。
- 工程材料为docs/s06a-contracts.md、docs/s06a-data-dictionary.md、docs/s06a-security-review.md、docs/s06a-report.md及docs/evidence/s06a。失败链保留；product→test仅测试脚本，test→final仅文档/脱敏证据。#30交付写回读回后停止等GPT复核，不进入B/C/S07；无Project写、强推、自动合并/关闭、生产发布授权。

下方S05及更早“当前/本次”均为历史授权记录，不覆盖本节的S06-A范围。

## 当前 S05定向返工 / #29

- 用户本次明确只修[GPT-REVIEW6115823569](https://github.com/Yredxin/YDental/issues/29#issuecomment-6115823569)三个BLOCKER；沿用当前S05会话与分支，原`76335d9902cee8e8c24173f0b01fd9ba8b606a5c`及全部原失败证据保留。
- 用户单独授权本次Project #29自定义“执行状态”→“返工”。实施前已完整读取21字段、15条目、6视图、7公开workflow元数据，唯一字段mutation后完整读回及差异核对；原生Status=Todo、其他字段/条目/视图/workflows和Issue实体状态均未改。执行状态保持返工，不自行转待复核；未来其他Project写仍需单独授权。
- 只修集团catalog维护与门店price-write分离、独立资格report的门店当地营业日边界、默认fail-closed可信转诊server hook/跨法人目标/真实来源审计。无新字段，不重写S03账本、S04 merge、价格快照和position事务。
- 产品修正固定`754cc331386e8294225c6579c9b4daa555160f92`、最终测试固定`68cbcdc3c5a7c0e16a8389e89a6ba44e9086bfc2`，完整链记录于docs/s05-rework-report.md及#29修正交付评论；最终文档证据SHA固定于评论。补充契约docs/s05-rework-contracts.md、安全复核docs/s05-rework-security-review.md、证据docs/evidence/s05-rework。
- 仅全新隔离S05库、合成permit与队列；不补来源医生目标company_ids/membership，不引入真实S08来源。修正交付写回读回后停止等GPT复核，不称用户验收/生产政策通过，不进入S06。

下方“当前S05”记录为原交付基线；本次三个修正和Project唯一字段授权以本节及最新review为准。

## 原S05交付 / #29

- 本次用户明确启用#29/S05；唯一当前边界为[GPT-ACTIVATE6115298923](https://github.com/Yredxin/YDental/issues/29#issuecomment-6115298923)。已完整读取#23当前正文/有效评论、#29当前正文/全部有效评论、#28最终技术复核6115295633及状态同步6115318214；[开工检查6115339128](https://github.com/Yredxin/YDental/issues/29#issuecomment-6115339128)已写回并逐字读回。
- S04修正最终`174a70df2cf8de515d0e781c59e6ce3825146313`已GPT技术PASS，#28保持OPEN/待用户验收，不重做S04。
- S05独立分支`codex/s05-intake-r1-20261011`；固定产品`6818bc35c35e030976df71558b188844d4de1082`、最终测试`90d1a41f8559542aed36f4fc0ff22897c17fb392`，完整SHA及最终文档证据固定于#29交付评论。交付后停止等待GPT技术复核，不能冒称GPT或用户验收通过。
- 当前只实现目录/服务区域、版本化价目与演示不可变快照、预约/现场资格、真实到店、任务/受理位置、资格复用/取消返池/改期/换区、转诊双分支和S03/S04真实联动。容量只有S03账本，患者canonical/current relation和merge fence只有S04；统一锁序patient→supply→intake。
- S05受理位置不是正式队列；S06真实waiting/calling、叫号、号序、租约及真实下游临床/检查/费用仍NOT_RUN。仅固定server hooks和受新库guard保护的合成队列契约。生产锁价/承诺价政策未批准，只有明确demo_confirmation，缺有效价失败，不能默认为0或冒称生产收费。
- 当前运行仅`scripts/s05.py`及全新`ydental_s05_test_14位时间_8位hex`、合成数据；端点/cluster/OID/配置哈希/dbfilter/端口/进程外发保护均必须通过。S00—S04工具和数据库只历史保留，不接管。依赖仅复用已存在进程本地资产；不改核心/odoo-12/业务库/既有服务或系统依赖。
- 工程交付见docs/s05-contracts.md、docs/s05-data-dictionary.md、docs/s05-security-review.md、docs/s05-report.md和docs/evidence/s05。保留失败与补交链；product→test只有测试变更，test→final仅文档/脱敏证据。无Project写授权，不改字段/workflows，不关闭Issue、不强推/自动合并/生产发布、不进入S06。

## 已完成阶段与历史会话记录

以下原S04“本次/本批”指其历史会话，不覆盖上方当前S05授权与运行边界。

- 当前需求 YD-N1 R1。唯一来源是 [总计划 #23](https://github.com/Yredxin/YDental/issues/23)、[S00 #24](https://github.com/Yredxin/YDental/issues/24) 至 [S13 #37](https://github.com/Yredxin/YDental/issues/37) 当前正文和有效评论。先读取 GitHub，再执行明确启用范围；代码、卡片及历史验收不授权开工。
- S00 已按 [GPT-CLOSEOUT](https://github.com/Yredxin/YDental/issues/24#issuecomment-6107583497) 最终收口，#24 CLOSED/completed；固定技术交付 `6dbf0a0a8be966bee7b2250b2a77e5b4d70540d8`。历史失败和补交证据保留，不重做 S00。
- S01 已按 [CODEX 收口完成](https://github.com/Yredxin/YDental/issues/25#issuecomment-6108974493) 收口，#25 CLOSED/completed。固定产品修正 `740c42bbf611baa8713758fba38c1411d6b966c9`，产品与最终测试 `f1ce22df7002e40391ce16fd59093d60c4522b2e`，最终文档证据 `37ccd3af4c6af390506eb9229e2f1cc145e951b9`；原证据与失败链保留，不重做 S01。
- S02 已按 [GPT-REVIEW 6110161675](https://github.com/Yredxin/YDental/issues/26#issuecomment-6110161675) 技术复核PASS，固定产品 `9653ca2d25fde16ac791dd499197703c18ef18ce`、测试 `00c76b55f205ee032534b7a3b8cda27bd1d7764d`、最终证据 `e97f721270a991bd4a737c15808896b286e488e9`。按[最新流程决定](https://github.com/Yredxin/YDental/issues/23#issuecomment-6110178328)和[状态同步完成](https://github.com/Yredxin/YDental/issues/26#issuecomment-6110222109)，#26保持OPEN/待用户验收，最终统一验收，不重做S02。
- S03已按[最终技术复核6111270280](https://github.com/Yredxin/YDental/issues/27#issuecomment-6111270280)与[状态同步6111303932](https://github.com/Yredxin/YDental/issues/27#issuecomment-6111303932)技术PASS，#27保持OPEN/待用户验收。固定产品`ac34c247c35e531567871ae2d8da065826833fe9`、测试`31d69ccaf2ef4e7ce7c49c7d8e0acce3c5f903d6`、最终`a8c0d5a2f5963e1f3dd2c31e4d363115453d2be3`。原S03及返工失败证据保留，不重做。
- 本次用户明确启用#28/S04，唯一边界为[GPT-ACTIVATE6111275379](https://github.com/Yredxin/YDental/issues/28#issuecomment-6111275379)。已完整读取#23当前正文/有效评论、#28当前正文/全部有效评论及#27最终技术复核/状态同步；[开工检查6111333171](https://github.com/Yredxin/YDental/issues/28#issuecomment-6111333171)写回逐字读回后实施。
- S04原固定产品`eb607750a4b35885f37acfb07d504f758b877b73`、测试`a35af92ef89465dbbf71cb6f88297e4c097b43c7`、最终`3b74b33987252d59033ae4b9d6757ad609818216`及docs/evidence/s04全部保留。[GPT-REVIEW6114781429](https://github.com/Yredxin/YDental/issues/28#issuecomment-6114781429)要求仅修patient-owned partner原生读取旁路和canonical current relation作为care/clinical前置，不重写患者号/合并/并发内核。
- 本次在原S04会话/分支定向返工。产品修正固定`887d0a9772a9ee165992ccd77af87fbb2c287d93`、最终测试`f3dc3dcb188511b19f9f2d898f45fbfdd6280663`；最终文档证据SHA固定于#28修正交付评论。补充契约docs/s04-rework-contracts.md、报告docs/s04-rework-report.md、安全复核docs/s04-rework-security-review.md、证据docs/evidence/s04-rework；原字段字典继续适用，无新增字段。写回读回后停止等GPT技术复核；不能冒称GPT或用户验收通过。
- S04只做统一患者/旧号/门店关系/行政联系人监护/重复提示/真实首次到店/本店政策/集团确认合并及并发事务/真实患者care只读审计和跨店写拒绝。S05/S06/S08/S09/S10/S12真实业务尚未启用，下游只有固定私有服务器契约与合成验证，真实联调NOT_RUN。不进入S05。
- 不从撤销任务、四份旧文档、旧计划、旧 AGENTS 或历史验收补业务规则。文档仅记录当前 Issue 的工程落地与证据，不另立计划。工程约定见 [docs/contracts.md](docs/contracts.md)，事实与阻塞见 [docs/s00-a-report.md](docs/s00-a-report.md)。

## 工作区和保护

- 核心 Git 根 `/home/redxin/code/odoo/odoo-sd/code`；本仓库为其独立 Git 根 `sd-addons/`，远端 Yredxin/YDental。每次仍核实实际路径、远端、分支、HEAD 和未提交改动。
- 不改 Odoo 核心、odoo-12、既有未提交内容、既有业务库，不停止/重配既有服务。当前批次只实现和验证 #29；新增运行只在全新隔离 S05 库中使用合成数据。系统依赖安装和既有服务变更需具体授权。
- 父目录 AGENTS.md 是既有未跟踪文件，保留原样；其中 sd-addons 为空、仅本机数据库映射等描述已陈旧，不作为实际现状或本批运行授权。
- 底座锁定 Yredxin/odoo@f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb，本地声明20.0；Python 用核心 .venv/bin/python。此为 fork 无父根快照，不能冒称已核对同 SHA 官方上游。调用 API 前查实际源码；兼容性需所属批次实测。

## 后续工程和交付

- 原生+自研，不引入 OCA，不创建未来空壳、不机械改名或重授权许可证。命名、依赖、翻译、时间、编号、字典与动作契约见 docs/contracts.md；生产参数按 #23 第3.2节和责任阶段发布。
- 修改 addon 前读取适用 odoo-guidelines；static/ 使用 odoo-web-guidelines；安全审计用 odoo-security。技能不替代当前需求和授权。
- 本批及未来获启用的运行批次仅使用全新隔离允许范围数据库与合成数据。先验证端点/唯一库名/创建记录及OID/独立配置、data_dir、日志/精确dbfilter/端口/外发禁用；拒绝业务库、历史库与错误端点。S04使用scripts/s04.py和`ydental_s04_test_14位时间_8位hex`；S00—S03工具与库仅历史保留，不接管。演示策略不能用于生产容量分配，测试模块不得用于业务库。
- 仓库和 GitHub 只放虚拟/脱敏材料，不发布凭据、患者资料、签名、备份或原始运行日志。长期保留失败与补交证据，未执行记 NOT_RUN，能力/权限阻塞记 BLOCKED。
- 独立分支提交；S04 PR如需创建用Refs #28，不强推、不自动合并/关闭任务/启动下一阶段。本次用户明确覆盖初次S04的Project禁写边界，仅授权#28自定义“执行状态”→“返工”：已在实施前完整读取字段/条目/视图及公开workflow元数据，唯一字段mutation后完整读回及二次核对。原生Status、其他字段/条目、workflows、Issue/PR实体状态未改；执行状态保持返工，不自行转待复核。#27仍待用户验收，#28修正交付后等待GPT复核。未来独立Project写授权仍须完整读取元数据并读回；不得导出token/cookie或关闭安全控制。
