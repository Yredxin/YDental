# R3-W2 未完成文书责任接手

状态：**阶段记录完成，限定路径已验证；未测项及收尾留待 W3/W4**。本阶段 A/B/C 为新线程，使用同一主机；角色分工不等于 OS 隔离。原文书 515–519 仅只读核实，禁止修改旧作者、版本及临床事实。下列源码与历史证据不代替本轮真实操作。

## 业务合同与前置

#32 当前正文及有效增量要求：负责人离职或失权时由有权负责人安排合法接手；不得强抢仍有效的编辑占用；保留原作者与贡献版本，不代签无法核实事实；待完善入口不应占原牙椅或重复排队；纯补记不得重复计费或扣耗材。项目执行、文书确认及诊疗段结束分开。[S08-A 增量](https://github.com/Yredxin/YDental/issues/32#issuecomment-6122378640) 和既有模型回归不是本轮已停用身份后的真实浏览器证据。

W1 本轮新患者 1652 的文书 520 已为 pending/v1，原作者和当前责任人为新身份 1563，编辑占用为空；原执行 559 interrupted、续接 560 verify，任务 917 started；唯一治疗事件 367／费用 362 = 600，耗材 0。上述为 W1 当时读回，不得重放治疗或覆盖待现场核查责任；W2 是否采用此对象、任何动作前须新鲜确认。历史 515–519 均 pending，原负责人已 inactive，入口可用性 UNKNOWN。

当前代码的 `_transfer` 要求同店医疗写、原负责人或本店 manager、版本匹配及没有有效编辑占用；新负责人须 active、同公司有效员工和会员、有医疗写、原服务能力和适用资质。候选 `c50688b` 对来源 execution 为 completed 的 pending 文书增加转派路径，但历史服务仍运行原 R2 候选；不同候选的证据须分开。以上为 SOURCE，不代表负责人停用后的真实业务验收。

## 实际发现与独立复核

A/B 的实际环境、操作、前后状态及审计、原始失败和 UNKNOWN 由本阶段后续按实际结果追加；尚未登记新产品 BUG。

B 的初次独立只读核查发现 A 店当前没有 active 店长；原店长 UID1542 inactive，UID5 与 R3 初始化者1561均不是店长。现有 `group_with_replacement` 策略允许按真实授权模型任命新 R3 店长，但最后 active 店长的撤任需替代；该身份和收尾影响必须另审，不能恢复原19账号或以集团管理员冒充店长。前像回执 `preflight.json` SHA-256 `2ed02eb3297c925bfb903f25471e32dcad85609eaaa5e3c55ee03bb5c6afecd2`、`manager.json` `19245293ec13080c32694468c70649a46b588bb6d43cae3823732a5c5f32b9d3`。A 拟复用本轮新 doc520：其原 execution559 interrupted、责任1563、pending/v1、无编辑占用；execution560 verify、task917、已确认 event367／fee362 必须保留，不重复治疗。该方案仍待主控与 B 审核，尚非动态通过。

A 在已核合成目标单次 native ORM 创建本轮 D2 与 supervisor，记录 commit started／returned、进程 exit 0，初步 UID1564／1565，原日志 SHA `54b3b26445e22a11353d6d5f88ec2e894a399c29feeb720a630068183c98baa6`；B 的独立物理提交、权限与保护读回当时尚未完成。首次使用系统 Python 因缺 psycopg2 在 import 前退出，没有连接／写入，改项目 venv 后单次提交；该工具错误保留，不计产品缺陷。native create 不冒产品账号创建审计。

B 新物理事务对照创建前像：所采 158 表旧行无修改／删除、569 个旧附件文件哈希不变；新增用户及 partner 的内部 notification、各 5 个 partner SVG、各 1 条讨论成员均属两个新身份；旧讨论、处置、SMTP 和已有 mail 保持。对照回执 SHA `2263b043af5994393b8f5202c291b9f23ab86ccbc5e87fd39e162e7b5c8367a2`。该范围排除敏感字段及未列入表，不证明全库零变化；内部消息不等于外发。岗位授权及正常登录此时尚需实际验证。

A 通过正常表单和服务端授权逐步为 UID1564／1565 在 A 店建立员工／会员及 medical/write，B 每步独立读回；最终专项回执 `e66ab85cc1a4bc7a835d1669c0d5633cbf63efaf154b6b0300273949cc14aeb5`：旧19账号、旧10槽、12处置、doc520、mail、供给及讨论成员保持，join 的原生消息和各步审计按实际新增。此时店长任命尚未执行，不以岗位 grant 代替店长授权或接手通过。

B 对新店长收尾路径执行正常 MODEL／ORM 事务回滚预演：任命后尝试正常撤任唯一店长，抛 `UserError`（原始正文未采；替代要求为源码支持的推断）；正常停用预演所见为新账号、对应 partner／讨论成员、原生 `mail_message` 及 supply mutex 变化，flush 后回滚。独立对比所采 158 表、589 附件和 107 讨论成员前后不变；3 个可见序列各推进 1，266 个不可见序列仍 UNKNOWN。这个预演不是浏览器权限或持久提交证据，不能用直接停用声称满足撤任替代政策；不得清除历史对象或责任以便收尾。

预演脚本 SHA `66efa6d90bde3429fd1205a1febaf402f76b2d75865162f28e2091ef46d24c29`，日志 `15e0c52c88f0645b1a854e779c93fce95b87a886db34082539851f13f6ac5a26`，结果 `3ca34c88e33f05a785d7963e6e9414724a4eab9c0e211aa1e318404d188057b9`，独立前后比较 `e407101616a76c0b199bcf43fb56d61f60f5f2a318ad9d08fc4246e602452d08`。

A 的 UID5 正常登录 hold-login 工具用于模型预演后，stdin 关闭导致未触发脚本 `CLOSED`；经 SIGINT 后进程退出码 130，Chromium 父进程已退出，但未证明 Context 正常关闭或 Session 失效。A 报告为工具操作问题，B 独立复核及归因待收；不能写为产品故障，也不能倒签正常关闭。

B 以独立无网络同构 Node stdin 程序复现：未分配 TTY 时向该 session 写入得到 `stdin is closed for this session; rerun exec_command with tty=true to keep stdin open`，SIGINT 后 exit 130。B 分类 **AGENT_OPERATION_ERROR**（错误预设 stdin 存活），不归产品；按计划主控独立定向复验待执行。原 Context 正常关闭和原 Session 失效仍为 UNKNOWN。

A 随后通过正常入口任命新 supervisor，B 独立读回 UID1565 在店541 `manager=true`、medical/write、账号与员工 active；旧19账号、旧10槽、12处置、doc520、供给和讨论成员保持，正常审计增量另列。回执 `38b9b7684cbb9fd6164f00ea16a2cb8ab86729ec6575fefc349c10a8be44763d`。最后店长撤任仍须遵守真实替代政策，不以 ORM 停用规避。此时尚未证明停用负责人后的转派或编辑。

主控针对 stdin 问题独立定向复验：首轮缺依赖引发 `TargetClosedError`，保留为工具环境失败；随后使用本机依赖并分配 TTY，在不操作业务的本地 probe 中报告 context／browser 已关闭、exit 0。B 核对脚本在 await close 后输出，SHA `1c23498ba84c8d8fbfc07ca5448d6ae9b6a3354e3ac3f0f69f5e7daedb7866bf`，且当前无 probe／hold 进程；原始交互结果由主控直接观察，B 未直接读取交互。此定向复验支持工具操作归因，不证明原 Context 正常关闭或原 Session 已失效，二者仍为 UNKNOWN。

UID1561 以新独立 Context 正常登录并切到店541，B 确认 scope4302 和紧邻基线；D2 能力559的正常服务 MODEL 事务仅作回滚预演，尚非实际表单提交。B 对照所采 158 表、589 附件、107 讨论成员不变；可见审计序列推进 1、266 个不可见序列 UNKNOWN；事务内供给时段及处置无变化，回执 SHA `6aa4d15ea3436a8956bd4281bb35075d0c4b563a2ef6ee117fb5470f85b8ee11`。能力关系表不在该 158 表中，实际提交后需专项读回。该 Context 显示正常 `CLOSED`；Node 因 TTY 保持而经 Ctrl-C exit 1，Session 失效未知。

A 使用 UID1561 的真实 profile 表单在店541设置 D2 能力559，服务端返回 HTTP 303；B 独立读回 UID1564→559，D1 原能力不变，supervisor 无该能力；旧19账号／10槽／12处置、doc520、mail、供给全表与讨论成员均保持，回执 SHA `e214816d3486055f1c70ca5915e3ab91d2777962dc3e44a2d45ca980dd5a8e39`。能力配置不等于文书接手成功。

D1 离职 MODEL 回滚预演表明新 D1 的讨论成员1672受影响，本轮时段1240将 suspended，并生成新的 pending 处置和事件；这些责任不可自动清理。预演结果 SHA `9081b14bb8743592e34fa9fcf861b36dc1caff2d1f75ce7dc459c92d9645f9ca`。B 外部对照所采 158 表、589 附件、107 讨论成员回滚前后不变，SHA `d7ec3a67b67dc3ce7b54dcfa81c3aafe942b1eb5ffb8c7075b7de13ac31c1ee6`；5 个可见序列前进，266 个不可见序列 UNKNOWN。该模型预演不等于真实提交及提交后核验。

A 通过正常登录单次提交 D1 离职请求，返回 HTTP 200，报告 Context／browser closed；日志 SHA `bd7e91a7f576673418087d913edf2a0ca421656e00287839cbfaa49f26107534`。HTTP 200 不等于持久状态通过，B 提交后独立核实待完成。另 UID5 的预演 Context 显示 `CLOSED` 后 TTY 保持，经 Ctrl-C exit 1，其 Session 失效未知。

B 在独立事务读回 D1 离职的实际提交：UID1563／员工1518／成员2552 inactive、grant none；新 slot1240 suspended，新增 disposition59 pending，native tracking 11117／11118 分别对应员工1518／用户1563；移除讨论成员1672仅属本轮 D1。所采 158 表其余变化与预演及登录相符，589 附件和旧责任未变；doc520 仍 pending/v1，作者及负责人1563。回执 SHA `575b3c6321a2ee3448778d53bc0b28a93a09f6e392a95b0c9516222302d8b2ca`。处置59为真实新责任，须保留，不得自动完成或清除。

A 在 supervisor UID1565、店541、doc520 v1 场景单次发出转派请求，观察 HTTP 200，但读取响应体时出现 PlaywrightError、脚本最终 UNKNOWN／exit 2；Context 与 browser 已关闭。日志 SHA `513b568833c3702d9252bf2d1b4158a1fe646e70a6799b8be3c3e7e455f75521`。页面刷新仅为推测，不作为根因；未重试，提交状态待 B 独立核实。

B 的独立专项读回确认转派已持久提交：doc520 pending/v1、原作者1563、负责人1564、editor null；回执 SHA `4a0e8ac9ce6127d4d13b69fe451802cdc9cc79fb4ba9406adfa46e62df4f2707`。原 HTTP 响应体仍 UNKNOWN，不重试；全量保护对照尚待完成。该结果仅证明责任转派，不证明 D2 可编辑或确认。

B 的保护对照及审计87130显示 UID1565 店541的转派 accepted，doc520 负责人1563→1564；原作者、文书版本、执行、费用、库存、589 附件及全部旧讨论保持。supervisor 首次登录产生 channel45 两成员及消息，4 个技术 mutex revision 变化；对照 SHA `716ef9202f7683f09e1ac5f9b4ffe6e6575cf877b99894fe39ff5a0cba027d79`。不得重放该已提交转派；审计接受不消除原响应体 UNKNOWN。

D2 以独立 Context 正常网页登录，取得文书编辑权 HTTP 200，保存合成补记 HTTP 200／v2，随后正常 release HTTP 200、一次 heartbeat HTTP 200，报告 `CONTEXT_CLOSED`／`BROWSER_CLOSED`、exit 0。B 专项读回 v1 作者1563、v2 作者1564，仅 follow_up 追加指定测试标记；文书仍 pending、未签署，费用唯一362、无工位租约；专项 SHA `72a2dad85050666e422c2c24c6a631a69c9768640e7939aed7cae24f41cb173f`。全量保护复核尚待完成；补记不冒确认或任务终结。

B 全量对照 SHA `c28a6f9dfedeca147c1325e8d483a0ec9b628c2babe92f582058d29b376ec87d`：版本985/v1作者1563，986/v2作者1564；负责人1564，正常 release 后 editor null。所采 158 表与 589 附件中执行／任务／费用／库存／供给无变化；首登产生新 bot 讨论，技术 mutex 有变化；execution560 verify 与处置59 pending 保留。该合法补记后待完善责任仍由1564承担，不能称已确认。

A 以无医疗权限的前台 UID1562 正常登录店541，对 doc520 各发送一次 acquire 与 transfer 真实 HTTP 请求，均返回 403；Context／browser 正常关闭。B 已核 acquire 后文书和责任不变，服务日志记录 denied，但不能冒称持久业务审计；transfer 的独立核对待完成。该负例只覆盖无医疗权限角色，未覆盖有医疗写权但非负责人的角色，也不代表全部代签边界均已验证。

B 对两个 403 的最终独立对照：服务日志分别有 actor1562／clinical.action denied，并非持久数据库拒绝审计；所采 158 表、589 文件、110 讨论成员对比仅新增正常登录／切店审计，临床、费用、库存、任务及处置不变。对照 SHA `a744c7d02164cb8c79a4ba8d637d1c63e36aa10ffe415b51a8d5ce1e9efcf83e`。

## 分类及阶段结论

- **已证实，限定实际对象与原服务候选**：正常离职使新 D1 inactive 后，店长通过服务端转派原 pending 文书；D2 正常网页登录获得编辑权并保存一条合成补记，原作者和历史版本保留，责任转为 D2，既有执行、费用、库存及待处理责任未被重放。无医疗权前台对 acquire／transfer 的服务端真实 403 及无业务副作用经 B 独立读回。
- **AGENT_OPERATION_ERROR**：未分配 TTY 导致 hold-login stdin 关闭；B 同构复现，主控定向复验并记录首轮环境依赖错误。无产品 BUG 依据。转派响应体的 PlaywrightError 根因未证实，响应体 UNKNOWN，独立持久读回已确认该次提交，不得重试。
- **UNKNOWN／未测**：有医疗写权但非负责人的抢占及代签边界；已 completed execution 文书在最终候选上的实际转派；旧文书515–519的责任处理；原 hold-login Context 是否正常关闭及原 Session 失效；其余 Session 失效；266 个不可见序列；新唯一店长按替代政策的最终处置。不可把源码、MODEL 回滚或其他候选的证据代替真实动态验收。
- **后续责任**：doc520 pending/v2 由1564负责，execution560 verify、task917及 disposition59 pending 保留。slot1240 suspended 是新 D1 离职的实际联动；不能自动清除。最终账号收尾须单独检查原生 tracking 消息及待处理责任，提交后独立读回。

本阶段证明 interrupted 来源文书的有限接手路径，并未单独满足 R3 所有最终候选与权限验收；W3/W4 按影响范围独立复核。没有经 A/B 确认为真实产品缺陷的新 BUG；不将工具异常计入产品缺陷。

浏览器资源记录：A 报 join／grant／manager、profile、D1 离职及 supervisor 转派的访问日志均有 context_closed／browser_closed；D2 分步及前台负例的原始交互输出为 `CONTEXT_CLOSED`、`BROWSER_CLOSED`、exit 0，未另存单独脚本日志哈希。UID1561／UID5 两次 TTY 预演均在 await 关闭后输出 CLOSED，之后因 TTY 保持以 Ctrl-C 退出；最初 UID5 无 TTY 的 hold-login 未收到 CLOSED，原 Context 关闭状态和该 Session 失效仍 UNKNOWN。以上关闭记录不等于服务端 Session 已失效。
