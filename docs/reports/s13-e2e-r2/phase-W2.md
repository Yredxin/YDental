# R2-W2 治疗、检查和交还

状态：**PARTIAL，证据整理时资源与账号收尾仍待主控完成**。真实治疗和全景检查、不同医生接手、原稿补记、耗材和不足库存服务端负例取得下列限定证据；D2 治疗后交还而不是本段终结，两份及后续文书均未确认，过期及资质不足负例未在本阶段取得。不能将这部分结果扩大为 W2 所有要求通过。

## 环境与身份

先建新独立 scratch：cluster `7701481100419571743`、OID `16384`，真实安装 exit 0；五账号各用独立 Context 正常表单登录并核 UID。由于最终产品的 `isolated_test` 仅允许指定历史合成库／店，而 demo 供给不可售，未伪造正式政策批准或改产品边界。该 scratch 仅完成准备，未执行临床链。五账号按原生流程停用：B 核 inactive、员工／会员／grant／资格保持，5 条本轮受限讨论成员移除，5 个私聊保留；Session 失效未验。其自建服务与容器停止，B 回执 `07bb353c680588fe4c367ec43dc57b18253b822b750156a7b268fde0d2713a35`。数据库 network none 不证明宿主全部出站隔离。

随后仅在身份核实的历史合成库 OID `2171423`／cluster `7694897083368259627` 新建 R2 身份与业务对象，未升级库或恢复旧账号／时段。创建六账号 UID1553–1558 并分别正常网页登录，B 核各登录及当前店空 `ea840b88d72c9f1a51728ac6f8cbe8b5979086e776fb1e3010c93e398ed877c8`；岗位授权及员工会员 B 读回 `8978679a1d3f159ff0015272bab239cd65b5aa94a12065b8e677d8144026cd9c`。初始化用新楼层、区域、工位、资格及 mapping，合成价及已授权 isolated_test 供给；旧对象逐项对照见本机私有索引。新 slot1239 发布后容量3，B `6cd0d399916018a59a5f7451c6cff431ec75dc9f1286211e0629ca1c6ec7f2e8`。新耗材 lot282/product1140 实际入库3，event759→move758，B `0575aa2d2999e3283347d2c3bc65e2aa6876a0a131714c7c03a96bf428164dfc`；入库不等于患者耗用。

## 浏览器动作与独立物理读回

- 前台创建新合成患者1651；D1 1555 接诊 execution550，建立草稿515，签发检查 order34、line54/55、task907/908，主动交还。文书 pending、责任1555、editor空，续接909 pending，费用0；B `07d35356009446d6f00ee3e6399ff110756fecf9b36662765ff894676be0b6d1`，lease退出 `2451d0425d920cae1926a6aebb9acc31eb817e52c4d67b383ba222352c090f35`。
- 前台报到全景907，检查员1557 实际执行并确认 result31/v2；event359 唯一 fee357／snapshot389 为80。CBCT line55／task908 保持 issued／pending。B `ebf14611a1e44bedbdb4d6fd3b1968c7123edd672fd0d5424d517ba1793517c3`；finish 后检查 execution551、queue562、task907 完成，lease556 holder_exit，续接909与D1待完善责任保留，B `f5148de8f70621fa2e3504c0484202a565b01f0c7963b716e1687a4d90367f29`。
- 前台报到 continuation909，D2 1556 通过区域队列接手 execution552；真实治疗 event360 confirmed，consumption258→inventory event760→native move759/line1208，lot282 实耗1，门店3→2；fee358/snapshot390 为600，全景费仍唯一。B `aeb6f959fd78776d475a82ce8552d570b426eef2e8220fef0579672812d6454f`。D2 随后交还产生 continuation910；doc516 pending/责任1556，不是文书确认或整个诊疗结束。B `7f6bbe0e80a326da0748f7b3e1745234112fd21d819c1cfbc43e95def4356a19`。
- D1 正常登录无工位租约情况下取得自己的待完善 doc515，单次保存合成占位形成 v3/version979，release 后 editor空、责任1555；两费各一、库存2及未完成任务保持。B `e5892532bf1e3133a7ebb93e9af1cf6c788b6bd7d9d9a956fca1746a5549d633`。保存不等于确认或签署。
- 新 continuation910 报到后，A 在 execution553/doc517 请求 lot282 数量3（库存2）得到 HTTP409，但未采正文；B 核无新治疗事件、无费库副作用，首拒因 UNKNOWN。Context关闭后租约自然到期，受控单次原生 timeout 后 execution553/queue564 verify，B `417fcf9e909f9a5ebdfc2d56c5af05027eb71c4b28b0af7fd1afe8ae1562da87`。B 新 Context 正常现场接续 execution554/doc518，独立请求同短缺场景获得真实 HTTP409 `insufficient_balance`，A 独核无新 event、库存2及两费不变 `4ab9f384915dfaadfcaaf6d252cfab45d9291297379852864b44e61818f0237e`。B 正常交还和退出；A 核 558 timeout／559 holder_exit inactive、doc515–518 pending 且责任保留/editor空、CBCT908及新 continuation911 pending，`e7a7f4c8b4a39f3ac497cb7456b3dcccba38826ab801ec758d6f22a293bc0134`。独立复现不能补写第一次响应正文。

## 原始失败、保护与边界

首次浏览器启动无首异常，后续缺系统库诊断不反签原因；楼层、区域守卫漏放原生字段及 UTC 表单误填经 B 独立复现分类 AGENT_OPERATION_ERROR，主控分别亲自定向复验，原失败保留。D1 首个 runner stdin关闭、未发业务 POST，B 复现并经主控定向复验；原 Context 正常关闭仍 UNKNOWN。检查阶段主动 stop 触发 runner guard exit2，非服务端拒绝。B／A 若干只读采证路径、Python依赖及 stdout 序列化错误不作为产品缺陷；回执和实际提交状态分开记录。历史新用户回滚探针推进六条非事务 sequence，266 个 NULL 序列状态未知；库存 mutex 从26到29未逐次采样，部分原因 UNKNOWN，不据锁值推断库存数量。

本轮新前像覆盖158张选定表的非敏感字段及459附件引用，非全库；旧历史缺失的升级前像和旧 Session 仍 UNKNOWN。新合成患者、文书、检查、库存移动、费用、任务、供给和审计均须保留；尤其 doc515–518、CBCT908、continuation911 不得自动完成或删除。未实施正式临床政策、真实诊断／签署、外部通知或生产部署。历史库新账号及测试服务的最终收尾以主控后续独核为准；本阶段团队共享主机，不冒 OS 隔离。原始工具、日志及逐次 SHA 索引留在 `.local/s13-e2e-r2/`，不公开凭据或 Session。

W2 阶段末 B 独立保护读回：纳入的158表旧行零删除，仅5个技术 mutex 行变化，其余旧行的非敏感字段摘要不变；459个旧附件文件字节哈希保持，当前519个文件零缺失，SHA `3e5ef8f407098b589e402e4bd0735ce0dd8ac9d1cc690555866ec6a1142ea4fc`。原 UID1541–1551 均 inactive、slot1229–1238 均 suspended、处置45–55 均 pending，SHA `eabc456cf712fbc1928bc004d6b53c45cd6853340f35583a427328b072774a0e`。敏感字段、未纳入表及历史缺失前像仍属 UNKNOWN；这不是全库零差结论。

## 医疗完成入口的待复测线索

D2治疗event360已 confirmed；handover已终止当前execution552并创建续办910，不能由此证明整个诊疗任务最终完成。对普通医疗独立完成入口的源码检索未发现明确入口，但A未实际尝试该入口、B未作对应动态复现；这是需优先复测的线索，不是已确认的新产品BUG，也不能据此断言入口不存在。
