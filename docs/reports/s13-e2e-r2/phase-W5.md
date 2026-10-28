# R2-W5 历史保护、原件与 UNKNOWN

**PARTIAL：新保护基线与合法原件310–312的限定核验完成；旧店65份和账单原件1本轮合法读取权限受阻，311/312本轮打印请求 NOT_RUN，历史缺失前像继续 UNKNOWN。** 本阶段 A/B/C 为新线程，共享同一主机，不冒操作系统隔离；不升级历史目标、不生成或替换旧原件、不重放业务。

## 历史前像与现时基线

- R1 一次真实 `-u ydental_supply` 后库存 mutex revision 13→0，旧 XML 为可更新且指定零、加载日志支持原因，但无逐 SQL 捕获；10 个技术表摘要变化缺紧邻升级前逐行值，具体字段及影响 UNKNOWN：`ir_act_report_xml`、`ir_act_url`、`ir_act_window`、`ir_actions`、`ir_cron`、`ir_model_data`、`ir_module_module`、`ir_ui_menu`、`ir_ui_view`、`report_paperformat`。C 直接比较 R1 私有 pre/post 的 technical 投影得此清单，文件 SHA 分别 `aa7b7ebde8e3b125698b396fd3d85db724f8a63c024e83e885c30cf9bd3b490e` / `ae4698fd8bfcc4d3cfd36deaece509b6aff14075766b2848d69ffc04c146902d`；这些是摘要比较，不是行级前像。相关 settlement source NULL 约束告警按原日志保留；不以新快照补旧前像。[R1 记录](../s13-e2e-r1/w2-test-policy-record.md)。R2 W1 新 scratch 真实升级 3→3 与真实双连接 MODEL 竞争为限定通过，不冒历史目标已升级，BUG-002 仍 OPEN。[W1](phase-W1.md)
- R1 另有 16 个旧 URL／menu／view 的升级紧邻完整前像缺失、26 项复杂字段未直接逐值规范化；35 项时区选择序列及部分元数据的 MD5 重建只能作为辅助，不是原始前像。旧 Session 失效未实测。R1 停用后至 R2 新讨论成员基线前的全表差异亦 UNKNOWN；指定12条移除事实已记录。
- R2 W2 在目标 OID 2171423、cluster 7694897083368259627 的 RO/RR 事务建立新前像：选定158表全部行非敏感字段、459个 filestore 引用，回执 `58b2aa52b844b4d186b04b39e90034081dc5f7eaeb611b45d825ebaebad2b3e3`；敏感列及未列入表排除，不称全库或升级前完整。W4末 `f58252e52458073088b936c4e2cdeca376cd9c57756f226861577b0574194706` 覆盖158表94187行及539文件，原529文件一致，旧行无删除；四技术mutex变化与8次授权及2次患者操作源码／数量吻合但未逐SQL追踪。[W4](phase-W4.md)
- W5 B 新独立 RO/RR 基线 `fb6474ef4bf31efe999f68329a40a083b3fa66c66e8dda1fda6d6e5edd64ca34`：158表94187行、539文件零缺失，与W4末 tables/files逐值相同。仅对所采表、非敏感字段和文件成立，不替代过去缺失的前像。

## 已知历史责任与旧原件边界

R1 W7 独立时点：文书509–514 pending；CBCT888、续诊895/900、续领897 pending；检查899、任务901/903及队列558–560仍待处理；复诊283 to_notify／activity215 active。退药757移入隔离未核查。停用增量产生处置45–55及事件5208–5218，旧槽1229–1238 suspended，原UID1541–1551 inactive；这些均不得自动完成或恢复。以上为R1时点，现场状态以本阶段B读回为准。

R2 新文书515–519、CBCT908、续诊913、药房余量916与退药769的实际未完成责任保留；不得因为停止服务或停用身份而清除。R1 740账单、收款、退款、多账单及处方31之4＋2与原库存移动不重放。

R1原件310–312及账单原件1当时已用真实网页请求与存档比对；旧店1的65份历史原件因当时无会员未实测下载／重印。W5 不为完成测试扩大读取权限；新申请仅限现有合法权限、原有快照，不能创建替代件或宣称物理出纸。合法读取/下载的本轮结果待 A/B。

厂商与人工外加工、真实外发及门户未获批准，保持 NOT_RUN；不因本阶段只读检查启用。财务、临床、税务、支付和P14也未获生产授权。

## 本轮合法读取原件310

B 读取前确认本轮医生1555对A店具有medical/write及患者关系，原件310来源clinical document509／patient1647／A541／version2，附件15956关联正确；原件声明及实际文件SHA均 `9b7c46b272187f7983a8f379bd8685786b946c9a1fddf632373cc36b4395c1ff`、48594字节，私有前像 `825b83cc0e043b2227afd5c68e1707c4b0a4530da1d0cd1b2697c2e92531dd2d`。A 以独立Context正常表单登录1555/A，真实download HTTP200，响应48594字节、SHA同原快照；只在内存计算，不输出PDF，Context/browser关闭；日志 `63d2a8b1e1d9fda27a6a9cf0bf72ee0f17b4cceae7cdc3f5ecbcacce5b0a7f23`。B独立核 accepted audit86495／actor1555／A／source509，原件、附件及权限关系保持，`1cea92d49ccda0deaf04ebe787ccdab5f6f012cc1da3305d310281322647d435`。这是该R1合成原件的合法下载及快照比对，不是旧店1的65份重印、实际出纸或全部原件的通过；随后 A 同身份正常网页单次 print_request HTTP200，响应同样48594字节、SHA与存档一致，日志 `7e795e1a063c556b90a3a4f13f8594db4c1a52ca172fa00b1cb57e695f1b2b06`；B独立核accepted audit86499、source509与元数据不变，paper_output unknown，`5b64546a89acb8f079c0a7e0d08d0572b3d283112d62855c908fb237e90173b6`。不代表物理出纸，其他原件尚未由此证明。

## W5 责任独立读回

B 在新 RO/RR 事务读回 `b0c34a8144e5a0a5d4b4c8bd69387f0a0269564af2f50e60bf9000bb1856ed23`：R1 文书509–514 pending／责任1544；888、895、897、900 pending，899、901、903 accepted、queue558–560 waiting；followup283 to_notify／activity215。R2 doc515–519 pending／editor空，908、913、916 pending；return757／769物理隔离 done 不代表核查完成。处置45–55 pending，通知 pending14／unknown1、mail exception13；旧11账号 inactive、10槽 suspended、R2八账号 active、active lease0。为指定来源的现场枚举，不冒全部责任完整普查；首次只读 SQL 因列名错误 SQLSTATE 42703／exit1、回滚，修正后成功，原失败保留。

B 另只读核311处方原件及文件 SHA `381c589dd355c0d5d1cb699393006a71793437a03856e0ed3c49cd403c20f4a2`／46711字节，312检查原件及文件 SHA `77a24503b1208406997fbcf8e75c1e8c1ec6447b113ecb23008278499f4cb55e`／38046字节；元数据、1555 medical／1557 exam 现有授权及关系回执 `7eae0966764b042ef601c9402050761ae0e7810d4355ec02afe4d462f03d805d`。随后 A 各用独立正常Context：1555/A 对311 download HTTP200、46711字节/SHA同存档，日志 `da90a4750841bdd44588add23a73d6233f393c6ce760188156df25409b151c83`；B核 accepted audit86503／order31，元数据不变 `673e2a85ebb22d306c439e7ca2280e950251022eac39e82603acdf58e84d03f0`。1557/A 对312 download HTTP200、38046字节/SHA同存档，日志 `d98c629f25e1a1161523387a0fdc3539f132a34cde2b7b3299826100cd9372d9`；B核accepted audit86507／exam.result30，元数据不变 `f334df90a066a11ef65d6f8e19ef066f4780fe5ce753a902e87a3abffc25d483`。均只内存计算、Context关闭，未生成新原件；311/312 本轮打印请求 NOT_RUN，R1当时验证保留原层，未证明物理出纸。B 另只读核旧店1有65份原件（账单6、病历10、摘要12、同意10、检查4、加工7、处方4、小票9、退款3），该店有active岗位，但未核对应来源权限及可用正常登录凭据，不能据此宣称已有合法读取；`b424acb6846810630b14b16dd747e3e0418e7facb32e0ddef19ce48009324633`。R2角色无旧店1会员，65份旧店件本轮合法读取／重印权限受阻；账单原件1当前R2无settlement权限，保持权限受阻／NOT_RUN，不临时扩权。

## 阶段末独立保护

B 在全部本轮请求后以新RO/RR读回158表94203行及539文件，缺失0；与W5起始比较仅新增16条正常认证、scope／切店及310下载／打印、311／312下载审计86492–86507，旧行无修改或删除，539文件逐值一致。回执 `ba63ed3f98fd41e8b1c1611b14062b4ac70ffb5d29a245ce00070cb3af1d6e4f`；事务rollback idle并关闭。该结论只覆盖所列158表的非敏感字段与文件，不外推全库，也不能填补历史缺失前像。阶段浏览器Context正常关闭；历史服务及R2账号的计划末收尾仍由主控进行。
