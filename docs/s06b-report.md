# S06-B交付报告

本批唯一边界为[GPT-ACTIVATE6117541343](https://github.com/Yredxin/YDental/issues/30#issuecomment-6117541343)。开工检查[6117569945](https://github.com/Yredxin/YDental/issues/30#issuecomment-6117569945)已写回逐字读回后实施。S06-A最终技术PASS6117519348及原失败/补交证据全部保留。以下为Codex自测，不代表GPT技术复核或用户验收，不代表生产政策批准。

## 固定交付

- 分支：`codex/s06-b-continuation-r1-20261012`。
- S06-A基线：`e13eaa2d48f11dd1193080a40ae2f31f58ddfa15`。
- 产品：`7816d8ab5872f7e6e56edcc366b461049ae9ac9d`。
- 测试：`a9bcf1c426274ad75e14dc6bada3e6cf333727d9`。
- 最终文档/脱敏证据SHA以#30本次交付评论固定，避免文档自引用提交号。
- product→test仅浏览器验证脚本和药房取消资格补强测试；test→final仅工程文档、AGENTS执行记录和脱敏证据。

## 实现与验收对应

|#30条目|实现和证据|
|---|---|
|第一前置|serving/verify参与patient/lease部分唯一；entry终身唯一；resume段另具唯一历史来源。旧行回填和真实-u迁移夹具保留旧execution后可同患者/椅新start，不删除历史|
|T06|可信来源保留、独立hold、原医生不能call；外检合法报到；查询hint_only不造号/资格/容量；失效hold现场核实|
|T07|医生明确确认restore，waiting/calling原子撤回后恢复；serving/verify拒绝；恢复不发号、不消耗新容量；两种start提交顺序及calling/timeout竞争|
|T08|默认fail-closed保存hook；成功保存才同事务交还/释放患者文书/唯一pending continuation；失败与重试保留执行和文书；多结果并发复用同一后继|
|T09|本店frontdesk write与独立追加group双权限；closed输入下task-bound permit；过号、故障、重报不重复追加、不刷新排序/机会|
|T10|revoke与start共享锁序；两种真实双连接提交顺序；撤销不取消资格、不退款、不返容量；start先提交拒绝普通revoke|
|T16|继承原门诊catalog/精确capability/非空qualification/区域快照；无原医生/椅；外检能力不污染；不同catalog需新S05资格；同catalog改方向必须原因|
|T21 B适用|exam/pharmacy保持精确能力和统一queue/患者互斥；作废号与资格取消语义继续S05；真实发药NOT_RUN|
|A回归|原48方法全部保留；46个AST不变，两个只将全库计数限定到当前合成门店；原21并发及Firefox全路径独立回归|

动作、字段与安全边界详见[s06b-contracts.md](s06b-contracts.md)、[s06b-data-dictionary.md](s06b-data-dictionary.md)、[s06b-security-review.md](s06b-security-review.md)。

## 隔离与验证

最终全新库：`ydental_s06b_test_20261012045322_4fb99b9b`，独立HTTP端口18127。固定测试提交的安装已通过73项（含2项原生安装测试）；升级已通过71项（54模型+17真实HTTP/RPC）；A形态旧约束/行夹具的真实-u迁移验证通过，旧历史保留后同患者/lease新执行合法。真实双连接A 21组+B 12组全部通过、0死锁；每组保留backend PID与交错/重试证据。Firefox A 36项/14图、B 29项/10图全部通过，两套均0 pageerror；guard 5项、实际导出翻译219/219及代码元数据全部通过。见[固定最终结果](evidence/s06b/final-results.json)。

所有新增运行仅`ydental_s06b_test_14位时间_8位hex`新库；以`scripts/s06b.py`核对127.0.0.1:5432/odoo、固定cluster、创建记录/OID、配置哈希、精确dbfilter、自有data_dir/log、独立18126/18127端口与预览PID、SMTP禁用和进程网络guard。只用合成数据，不接管A或S00—S05库。复用的夹具名称仍显示S06A Synthetic，指本次B新库内新建的合成门店/人员，不是历史A库。核心f0c5a9b及既有依赖/服务不改。

迁移验证是新B库中的A形态旧行和两条旧终身唯一约束，再实际模块升级；不是完整安装A源码树再升级，不把该夹具冒称真实旧库迁移演练。

## 失败链与限制

完整失败/补交链见[运行链](evidence/s06b/runtime-history.json)及各attempt目录。初次安装6个测试错误来自合成夹具缺少既有版本参数；probe后升级2个失败来自A全库计数断言，已只限定当前门店。首轮并行Firefox的A换椅/B后续叫号导航等待超时保留，根因未充分确定；顺序运行和关闭已完成上下文后这些点通过。A后续后台组件即时count失败，经真实Firefox诊断证实初始0随后可见，验证脚本改为等待实际Owl组件可见。各失败浏览器均0 pageerror。原始日志、访问凭据、session/token、配置和私人来源marker留在.local，不进入Git/GitHub。

合成心跳2秒、超时20秒、N=2；部分竞争用600秒超时避免测量干扰。这些值未获生产批准。目标来源和保存hook在产品默认拒绝；真实S08/S09接入未做。A已列后续的原生账号logout整合继续不提前实现。独立文书锁是受新库guard保护的测试事实。

S06-C营业状态机/清队/跨午夜/日终/推送/区域屏，S07库存，S08真实病历/医嘱/发药/治疗完成，S09真实结果接入和生产发布均NOT_RUN。hold verify只保留现场核实围栏，不提供抢占或无来源接管。

## Project和交付停止点

本次唯一Project写为#30自定义执行状态返工→进行中。实施前完整读取21字段/15条目/6视图/7公开workflow元数据，一次mutation后两次完整读回深比较只有此值变化。原生Todo、阶段S06、其他条目/字段/视图/workflows和Issue状态未改；交付后保持进行中，不自行转待复核。

固定最终提交后在#30写`[CODEX] S06-B交付验收申请`并逐字读回，随后停止等待GPT技术复核；不自动启用C/S07、不关闭/合并/强推/生产发布。
