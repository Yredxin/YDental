# R3-W1 医疗正常完成动态验收

状态：**PARTIAL／R3-BUG-001 OPEN**。本阶段 A/B/C 为全新独立线程，主控统一协调目标和写入；线程共享主机，不构成 OS 隔离。用户计划要求真实普通岗位登录，区分治疗项目确认、文书确认、接诊段结束、任务终态，以及重复请求的费用、库存和后继任务影响。历史 R1/R2 对象和十九个停用账号不得重放或恢复。

## 契约与当前证据边界

#30 将主动交还定义为原段标记交还、产生或复用唯一后继，不能冒称治疗完成；#32 将文书确认、实际项目确认和本段结束分开，纯文书保存或补记不能计费扣库。W0 SOURCE 未见普通医疗完成入口，但还没有 A 的真实动态观察和 B 的独立复现，**尚无本阶段产品 BUG 结论**。现有责任转派仅接受 handover/interrupted；若实现医疗 completed，必须验证待完善文书的合法获取与移交。

W1 新独立 scratch 尚未实建或验证；当前产品的 demo 供给默认不可售，isolated_test 限既有合成目标，published 的正式政策不由本测试批准。环境选择、隔离和业务前置须按实际结果补充，不伪造 scope、身份或会话。

## 初始化预检

B 只读核六个 R3 登录名当前无冲突，历史合成目标的 policy 281／282 为 isolated_test 且其他连接为零。两次只读 SQL 因列名假设错误退出 1，核源码修正后成功；保留为工具前置错误，不计产品缺陷或业务提交。此为环境线索，不能以其推定新 scratch 可售供给或授权历史库升级。

A 准备在已核实的既有隔离合成库中创建本轮独立新身份和新对象，B 已限定 SOURCE 审查三新身份工具；新身份初始化使用原生 ORM，不冒产品 account.create 审计，真实岗位授权和网页登录须另验。实际身份、提交和副作用须以后续现场读回为准；历史目标仍不可升级。

三新身份经原生 ORM 创建后，B 独立物理只读核 UID1561–1563 active、邮箱空，仅1561具合成初始化集团管理组，其他无管理组；员工／会员尚为0，真实岗位授权和网页登录尚未验。旧十九账号 inactive、旧10槽 suspended、处置45–55及57 pending、原 exception 邮件保持（回执 `b9ea0ad3bc94fe7755413417e4396782c6d07b007a6ce488521e1dd8233d4ae1`）。B 以158表和539文件与W0对照，所采旧行无改删、旧文件一致；新增三用户／partner／公司关联、四组关系、15附件和六条新身份内部 notification 消息（快照 `15c7dd48113ba5e70eed47193e342b22811928c5890f0593060d8b4fcce2c04a`）。该结果仅限所采非敏感字段，不称全库零变化；消息不等于外发。

B 独核本轮专用服务 PID3315345 唯一监听 `127.0.0.1:18601`，目标 OID／cluster 吻合、允许限定测试策略、cron 0、SMTP 0、通知策略 disabled；目标库另有服务连接1。回执 `.local/s13-e2e-r3/b-w1/service-check.json` SHA-256 `fb8deb2bda3ba57daa3e81136ede86160ed16fa8d307a4ba308de805dd530ecc`。这是本进程及所查配置，不证明宿主全部出站隔离。

三新身份使用彼此独立浏览器 Context 正常表单登录；B 新物理连接核各一次真实登录记录及审计，回执 SHA-256 `c4c4998cd04a946856edbe312608fdb5c6f0f90767213437655f1feb9212ba9b`。这是身份登录，不证明门店岗位业务授权。

B 在只读 Odoo 事务实算21个 published slot 当时覆盖有效、未来 active assignment 0（日志 `de7b6fb075cbce16c587fed8bcc0e87b64370221b9451791c03b74a2a7ab7d65`）；授权前全库32 slot／6 assignment／12 disposition／212 event 的非敏感逐行摘要和供给 mutex 1615 固定于 `51e058f28f81f08b29aadd3b619afecadd64424022666a0fe3f41497e36d0df7`。这是时点前像，不证明后续授权无联动。

三笔新 grant 后 B 核既有 slot／assignment／disposition／event 逐行不变，供给 mutex `1615→1618`（`583e9b807f4419ea7b145b508b8eaf051f259f5eccbd803f30ba18d109315bef`、`ea48ad020722611d05e30437bc21c48f0065c53c873982228fc09ae0459542d0`）。新 floor282 与旧 floor 分列，旧行保持（`ae08cfd4ee2023fdee37bf9f3780ec42ed08132d3035ec4afa9f4cc71deaa7ba`）；B 首次只读查询误把 varchar 当 JSON 导致 UndefinedFunction／exit 1，修正后成功，属只读工具错误。医生 profile 前，21 个已发布 slot 覆盖仍有效、未来 assignment 0（`7f87cb3989231381a61c3baf18ce49f7a4280d69d16b3ac6374406ca1d90e016`）。

A 原始操作：UID5 正常网页为新身份 join 并配置初始化者四类、前台和医生各单类 grant；新 floor 真实表单 runner exit 0，日志 `b3e4bec6d685da643f9d54aa72d903cc0cbcada29855d3060ee027c4f0e1af8b`，B 读回见上。医生 profile 单次请求 runner exit 0，日志 `83f0db7afd472991b8c90d780868c0fa962b49d8658ef5bf28933b3be4cf9232`；当时 B 读回尚进行，不能据 runner 退出认定岗位能力或供给保护通过。

B 随后物理读回新医生1563的能力559，既有32 slot／6 assignment／12 disposition／212 event 均与前像相同，mutex `1618→1621`（`aad2cc624a83107e04ee08a0c0ad620fab70d0f361a0d6a91a44762b143d5d0d`）；新 area1204 属 A541／floor282／care／reporting，W0 旧空间无改删（`c3031f3f3fec1c39ce42479171d57d3e27508bf99e9cdb0ee12b2df8701ed8b4`）。尚无患者、治疗、医疗结束动态结果。

B 新物理只读核新椅1345位于 floor282／area1204／A541，active、enabled、callable，能力559；W0旧 floor／area／station 非敏感投影不变（`539c705771a9906c178134e981e6cc9b514a53db6c0f682d7e143ce807ad934f`）。旧供给四表逐行不变，mutex `1621→1622`（`2619155ecd9bd4063291b4c030b06544811f107544ce293fd7704735420ed093`）。营业及 mapping 前像确认新区域两者均不存在，目录715 active、能力559、价347已发布且覆盖该时刻（`7348b23805ad9f10cd42d69cf1da60d69588c626333c0e9ca33dfa4cc331481c`）。B 独核时先后遇到 python 命令缺失和系统 Python 缺 psycopg2 两次启动错误，均未连接数据库，使用项目 venv 后只读成功；不归类产品失败。

B 独立读回新 mapping1278（A541／catalog715／报到与执行均area1204、active），旧 catalog／price／mapping／business 的W0投影不变（`4fd6a0657d54765329588452b909f7240b95aed0e11052c0ff06ae9155d1615b`）。新 business1232 为该新区域上海当地2026-10-29 open（`035aba15048984b1c813d321ab37cfbf0358ceed9ef79587047f5432e6df3a7b`）；旧 slot／assignment／disposition／event 逐行不变，新增 event5229，mutex `1622→1625`（`f58ec04209cd0c653ae9bcaf29b9cdeccfa36c4c02799204c9905bd340519bb7`）。

B 在已核合成目标及服务测试配置下只读 MODEL 实算：新工位选择 policy281／isolated_test、目标时间段无重叠，D1 1563 的能力559通过真实 `_coverage`；日志 `57748372bd79ea151f4ce426d33378f48efc09a200ed79f1da6427ce65a0b6f7`。首次只读 probe 缺服务专用标志而得到 access_denied，日志 `0067c2b1c9b4b92b5a5adf5da9da1a3d734c5c9a1df6b9414c96e51ac7601937`，属 probe 环境配置错误、无写入，不代表真实业务拒绝或权限通过。新合成患者名称预查无冲突（`5981b2f07ab31eb3545abfdab5e8efb321fdc074a5bf42b95e5ca00db5ea5b40`）。

B 独核新 slot1240 published／v2，A541／新椅1345／area1204／policy281，UTC `2026-10-28 23:54` 至 `2026-10-29 02:59`，容量总3／预约1／现场2，coverage UID1563／能力559、审核者1561（`90637833c2d02a7835b076f45452a336b587d3d147657ce14e045c25869ebbcb`）。旧供给各表逐行不变，新 slot 和 events5230／5231 另列，mutex `1625→1627`，前后回执 `8f193e5b35d495581bf1b3d303befd1713dd3c3fff9c1183864147dffe792225`、`2de17f0323f41e6dbb118f2172ae4281ebb2307d7b0f7dd0608722d25aad14d4`。

B 新物理只读核新患者1652／partner3390／A541及关系1683；电话、邮件、出生、备注未填（`02c73944c74660390a5cc7aa14cea763f6c51bf45dc6d0bb5b8a10de161dfee3`）。W0旧患者／联系／关系／临床投影不变，新增患者及关系各一（`c8b2ebc97060dc5e46daefe6ecbdedf952719468b9448530c9db80174d36547a`）。

A 前台对新患者现场报到一次真实 HTTP303（日志 `67236a66e1d2aef013f6f606105df12d1bd6829c82eacbfcaa9c39d0429ae7e5`）；B 独立已提交读回 entitlement579 held／claim607、task917 accepted、唯一活动位置569及 actor1562 的 arrival1445。W0旧 entitlement／task／position／arrival投影保持（`78ff52eeaa74d8daddcd263ccaa10eac8f8ddce583c0b31e3c6dcb504f4d34dd`）。旧供给逐行不变，只有新slot1240变化、events5232／5233新增、mutex `1627→1629`（`f9e1973a5e0f1fe244b55eb885648cf2f3b120153725ece836a5169c2af03730`）。

## A 原始动态观察（OBSERVED，待B独立复核）

在产品树 `ca07961`（运行报告 HEAD `e06ae79` 产品文件相同）的历史隔离合成目标，医生1563正常登录并接诊新患者1652／execution559，建新草稿520。A 记录治疗 execute 单次浏览器 HTTP200，持久结果当时待 B 核；页面可见 Renew、禁用 Call、Exit、Save and hand over、Query return，文书页可见 Confirm text only、Save and hand back reception、Transfer pending document，未见普通医疗正常结束控件。原始 `.local/s13-e2e-r3/a-w1/history/doctor.log` SHA-256 `d4303485acb83e00ec517089bc93e608fdc61022caaf59c128294ae91f6428e2`。这是页面观察而非已经证明所有合法入口不存在；须 B 独立动态复现及主控裁定，不能只据源码登记 BUG。项目确认、文书确认、结束或交还仍须分别记录。

B 新物理连接独核 A 请求已提交：新治疗 event367 confirmed／execution559／document520／catalog715／数量1，唯一 fee362 为600，consumption 0；execution559 serving、task917 started、lease564 active。W0旧治疗 event／fee／consumption及execution／task投影不变，回执 `0e5c7aafa4a14a255204864fb9eae379ef0f0161dd431dad4ded188724b53e7c`。这是项目已执行，不代表文书确认、接诊段结束或任务终态。B 尚须独立正常登录复现入口观察；不得重放 event367。

B 独立新 Context 正常表单登录同一 D1 UID1563／A541：queue、clinical520、treatment 页面均 HTTP200，分别观察到 Renew／Call／Exit／Save and hand over／Query return、Confirm text only 与 hand back、Confirm actual treatment，未见普通正常结束入口。原始 `.local/s13-e2e-r3/b-w1/observe.log` SHA `724f0773b1ba7bdb240763b06fc3e6c5ceab4c65e1a94da81793af7fe91f4648`，执行源码 SHA `314b3ca5ba31190332cf1f931542219bfd28c1a5b65bf9a04f640275ee28914d`，Context关闭。**限制：** B 的新 Session 未持有 A 租约，queue动作控件 disabled；这是独立页面动态观察，不是 B 持有租约的完整业务复现。应与 A 持有租约的观察和 SOURCE 结合，不能仅以该页推断所有合法入口不存在。

为取得 B 持租约的独立动态证据，A 关闭原 Context 后 B 准备等待自然到期并通过真实 scheduler／现场接手，不复用 Session 或重放治疗。筹备时 execution559 serving、lease564 active（到期 UTC `00:15:16`）、doc520 draft／v1、event367及费用保持；全局无会受 timeout 影响的 active hold，唯一执行／租约且无 calling，前像 `27f2dc17280413e0940c3a7e497163f2e2eef9cfeb82cc20a7345e32242e5f34`。真实到期、调度及后续接手以实际结果另记，不将前置推断为复现。

B 为独立持租约复核，等待 A 原 Context 关闭后的真实到期，通过限定原生 scheduler 单次执行 timeout；B 日志 `67af51a8cd18578fee4d5d25cca3c4653bd0aaab46f7b1b078b6fb131dff8405`，A 独立读回 lease564 inactive／timeout（`22542586d60fe5ad3e7472142745d693a0e134b7392e9f68050477a071cc55f0`、`dea11b50c5a817ab4cc3ce0e69b6ff0483447922f958fbf9a859b4c3fca0a088`）。随后 B 新 Context 正常现场接手，A 新物理读回新 execution560 serving／lease565 active、原 execution559 interrupted，doc520 pending／v1、作者与责任保留、event367和600费用未重放（`dad8c5c9485105523ebfa041450e68cde316d83017c84b828f52cc486524a573`）。

B 同一新 Context 实际持有 lease565 时独立观察 queue、clinical、treatment 页面：Renew／Exit／Save and hand over 可用，但均未发现正常结束入口；记录 `d2eb85be3db0b7a1ee8a2dde2f56f57547ee715f9cbde7ebda3c31b40bd49596`。B 分类 **PRODUCT_DEFECT（当前候选医疗正常完成入口缺失）**，依据 A／B 各自真实持租约观察和 schema／handler SOURCE；主控裁定并登记为 `R3-BUG-001`；实际修复、固定代码与独立验收待后续记录。B Context 已关闭，当时 lease565 仍 active，不能因关闭浏览器冒称即时释放，后续须按真实状态收尾。

B 关闭 Context 后新只读核 lease565 仍 active、到期 UTC `00:26:25`，execution560 serving／559 interrupted、task917 started、doc520 pending／v1／责任1563且editor空；event367及唯一fee362=600保持、consumption0，旧治疗及任务／执行投影不变（`38d1a9bacc531d0e4944ec7a9e939d5feff017f674fd823e9446851ba707856a`、`f4a202b227463c32930953d3fcaaaf18c1500d1def77628b602f2900f6339dff`）。Context 关闭不等于租约即时释放或诊疗完成；须按真实 timeout 与独立读回保护责任。

## 修复候选（尚未动态验收）

独立 D 开发候选 `df4efc3`，位于本机忽略的隔离 worktree；新增医疗正常结束及完成后 pending 文书接手支持，调整相关 UI／通用终态标签，并新增模型用例覆盖重放、转派、编辑冲突、回滚及分支。D 实际执行 compileall、`git diff --check` 与 Node JS 语法检查通过；当时模型／HTTP／浏览器尚未执行，B 正独立 SOURCE 预审，不能以开发者静态检查冒验收。D 最初在 `/tmp` 创建 worktree 因空间不足失败，转用本项目忽略目录成功；独立 PO 工具检查因 `msgfmt` 和 `polib` 缺失未运行。原失败与未验证范围保留。

D 在独立 PostgreSQL scratch 对候选 `df4efc3` 实际安装并运行4个 post-tests，exit 0，日志 SHA `ed1c71d72cfc40684b1745cb67d3562b839bf8083f617bbc63f7f9639ae3fd05`；cluster `7701878533844856862`／OID16384、network none／socket only，容器 stop exit 0。供给使用既有 guarded 测试 addon 的 demo 替身，故只属 MODEL 层，非真实供给、浏览器、独立已提交或未实现者验收。首次 scratch 使用 S07 库名前缀不符合 S08B guard，初始化 exit 255，日志 `2590e7e6b264032545950e8a2e457ddb07ac5a3153e6dda09ff27223cc29c39f`，容器正常停止；属测试环境前置错误，原始失败保留。
B 独立核该日志所记4 post-tests、0 fail／0 error与shutdown及独立 cluster 身份，确认 `_allow_demo_supply`、过期／故障分支带 patch；该核对不扩大为真实浏览器、实际资格、独立提交或真实并发。

B SOURCE 预审发现连接过期返回的遥测可能误记 accepted；D 隔离候选追加 `34d3c29`：将该结果映射为 HTTP409／JSON `connection_expired` 并按真实状态记录遥测，不修改既有异常拒绝审计。新 scratch 2 项 HTTP post-tests exit0，日志 `a7355c4a77317dc85b31c77024e51203add3da46bc6b5ed55e4c90cb808d4565`，容器 stop exit0。过期业务结果由 mock 注入，此证据仅属真实路由呈现，不证明真实过期竞态；后续固定候选和独立验证另记。

B 关闭 Context 后自然到期的第二次 scheduler 实际 exit0／COMMITTED expired565，日志 `cbda9b8f45aa3c57f059ad9952c43d63482423cb65e23cf448ed37b59d962144`。B 读回564／565 inactive timeout、559 interrupted、560／569 verify、task917 started、doc520 pending／v1／责任1563、无活动租约（`cbe684939943d32b686846711344dd520ddf7aeb69646f62e0636f66ab221576`、`a5464d049f58c1e3da85ecf2f139fe097e6ae5b520e01167e9dbb1e6ba9e8d31`）；旧 queue/task投影保持（`9fd9dae88c94a36b2281909d42e15ba0daa07aa05495ca1399ebc8d59fa4436e`）。C 应主控要求另开物理 RO/RR、回滚关闭，独立确认上述新状态、event367 confirmed及唯一fee362=600、旧queue558–560 waiting、处置45–55／57 pending、无active lease，以及 target lease565 的 timeout accepted audit87067（`.local/s13-e2e-r3/c-w1/timeout2-independent-extra.json` SHA `77bd0c02dbdc85f03b1bce760c53b97d5f28d657186a1ebfacf3bc9fd23a74f7`）。该专项不是全量保护快照；execution560／entry569 已进入现场核查，不应伪称正常完成或清除责任。

## 阶段收口

主控将独立 D 的修复与测试候选正常 cherry-pick 至 `e0a1a6434afc9eac78083aafb17f6afee84bcbba` 和 `c50688ba806c69a624c3bf9b171b10ea164bfeec`；D 原隔离提交分别为 `df4efc3b8accd6d9bdce07ecda5063fec2531a58`、`34d3c29580aa64d760e0556fb7e22f8ad7035b62`。B 做了独立 SOURCE 审查并核对 D 所运行的 MODEL／HTTP 日志，替身和首轮初始化失败如上保留。医疗正常结束、重复与旧页、文书接手在最终候选上的真实浏览器及独立已提交回归尚未完成，不以 cherry-pick 或作者测试称修复通过。后续 W2／W3 必须使用全新阶段团队并按最终候选另行验证。

本阶段结束时原动态测试 Context 均关闭，最后一条新执行560／队列569在自然timeout后为 verify，任务917 started，文书520 pending／责任1563，旧执行559 interrupted；event367及唯一fee362已提交，不可重放或清理。服务及本轮账号为后续计划继续使用，计划末须按真实影响收尾；旧19账号和责任继续保护。
