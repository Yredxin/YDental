# YDental 当前执行规则

规则版本：MAIN-A-ENGINEERING-1.0（2026-10-18）。

## 正式来源与任务

- 用户本会话直接批准 `YD-S10-LC2-MAIN-A-20261018-03`，task `S10-LOG-AND-CLOSEOUT-v2`，scope `MAIN_A_TEST_ENGINEERING_AND_CLOSEOUT`；用户提供的《16_CODEX_MAIN_A_ENGINEERING_CLOSEOUT_20261018.md》全文为本轮差异依据，仓内未找到同名附件，不伪称已读取附件原字节。
- 读取[实际上一轮交付6243358235](https://github.com/Yredxin/YDental/issues/34#issuecomment-6243358235)、[开发测试自主权6243010403](https://github.com/Yredxin/YDental/issues/23#issuecomment-6243010403)、[原MAIN-A范围6243026115](https://github.com/Yredxin/YDental/issues/34#issuecomment-6243026115)及#23/#34有效增量。GPT新的评论写入未成功，无新编号；不得代发、改述或补发该被拒评论。
- 固定父 `4554545e99375dd9b6c0552b0611cd550a717808`；分支 `codex/s10-settlement-finance-r1-20261013`；产品保持 `cf5d63fe510b52ea150d07495bf3062f4ce0961d`；core只读 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。目录 `/home/redxin/code/odoo/odoo-sd/code/sd-addons`。
- 上轮用户7/5凭据准备及用户7真实HTTP登录已完成；60表1034行/93模块保全已采。A-EDITOR因runner错误断言未执行，A-ORIGINAL因Firefox启动Error未执行；旧editor7/session109过期仍不等于release。旧窗口已结束，旧账本/STOP/原始证据保留。
- 六项原生框架及150项纯测试已采，不无变更重跑/重判。S10/T12及生产仍BLOCKED。

## 本包工程修正与实际收尾

- developer核实际access controller switch只返回revision，tester审实际调用点；将不含凭据的真实编排纳入固定可审测试源码。成功合法revision用于后续，真实正常会话核user/store；错误、过期revision或不匹配前提不acquire。相关回归依据真实controller/runner，不能复造错误mock断言。acceptance运行前交叉审实际runner。
- 保持3dc91ed就绪修正：真实run.start、socket、正确日志级别齐备才ready；纯解析错误先离线修，不为每字段重启Odoo。
- 先有限核旧owned浏览器进程清理状态；不得全局kill。核本项目既有Playwright版本、对应Firefox构建及选定可执行文件。最多2次无凭据诊断，每次90秒：不读取provider/会话、不访问业务站点、不配合Odoo，只起空白页并正常关闭，保存有界脱敏启动异常与可得PID/退出信息，旧UNKNOWN不回造。
- 仅无凭据独立诊断进程可局部 `DEBUG=pw:browser`，不得PWDEBUG、无限超时或把DEBUG带入登录进程，不改正常driver环境白名单。不开关sandbox、不安装依赖、不改系统权限/共享服务、不换浏览器规避拒绝。诊断依据[官方启动排错](https://playwright.dev/python/docs/ci#debugging-browser-launches)及[版本配对](https://playwright.dev/python/docs/browsers)，不预判根因。
- 核core res_device真实logger，仅在本任务本地日志配置精确抑制其敏感INFO（WARNING或最小filter）。不改core/认证/S01/设备记录，不关闭全体日志/异常栈。先合成敏感与普通错误验证，再正常登录时核实际logger配置及新日志脱敏marker计数。旧含session前缀日志继续0700/0600私有保全，不公开行/值/摘要，不声称密码外泄或被盗。
- 唯一业务目标main `ydental_s10_test_20261017105432_810a7d9c` / OID2144129 / cluster7694897083368259627 / `127.0.0.1:18410`。沿用既有解释器/依赖/应用账号，workers=0、max_cron_threads=0、db_maxconn=4；不在进程运行中改已加载源码，尽量共用同一固定候选服务。
- A-EDITOR：必要新鲜性核身份/资格/无冲突；用户7正常登录核user/store/revision，若已合法release只核实；否则既有服务acquire并用此次返回令牌release，token只RAM。提交可能发生后先核状态不盲重发；有效他人锁/资格不足停止，不清字段、改负责人或加权。浏览器受阻不阻止独立就绪的服务层编辑收尾，也不重做已完成动作。
- A-ORIGINAL：用户5正常Firefox登录实际结算工作台，点击既有原件1；关联页面/点击/下载，核27665B、application/pdf、SHA256 `05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4`及下载文件完整性/逐页查看。不以直接HTTP/旧副本替代、不调用新PDF渲染。
- 文书1 confirmed/v4、作者/负责人7及版本9→10、正文/费库账款/库存/原件保全。不save/confirm/correct/handover/transfer。只分别核认证/会话、四既有mutex、编辑权和下载审计实际允许差异，不放宽其他业务。

## 凭据、修复与资源

- 只沿用 `.local/s10-lc2-main-a-20261018-02/credentials/` 既有用户7/5 provider（0700/0600/Git忽略）。不重置密码、不新建替身、不要求用户找密码、不读哈希/cookie或旧被拒材料、不扫描私有目录。开发/验收不读值。
- 凭据值不进入命令参数、消息、Git/GitHub、日志、截图、DOM、HAR或密码摘要；不改输入类型/鉴权/工具控制，不广播秘密。
- 首次接收 `2026-10-18T00:03:25Z`，截止 `2026-10-18T04:03:25Z`。本轮新增上限Odoo4、main独立RO12、业务HTTP200、Firefox启动4（无凭据诊断≤2/UI≤2）、原件GET3。诊断90秒、每Odoo1200秒，新材料256MiB/总1GiB。
- 继承累计Odoo6/12、RO19/48、HTTP5/600、Firefox1；仅本次Firefox累计上限明确从3改为5；GET0/12，旧accidentRO2/maintenance1/CREATE2保留。新scope/profile一致接入、不清旧账目、不恢复旧窗口、不建新调度平台。
- 每重试必须新诊断/配置或代码补丁且前次owned进程已收敛，无信息不循环。普通脚本/配置/启动错误在范围内内部修复，保首失败及具体处置，不设通用ignore开关。真实工具安全拒绝、Native、未知提交/资金、身份/完整性异常停止受影响动作，不换agent/账号/入口重放。

## 真实角色与交付

- 继续原团队：主控 `/root`；developer `/root/developer_autonomy`；tester `/root/tester_autonomy` 唯一main DB/业务执行者；acceptance `/root/acceptance_autonomy` 独立审查。全部先读本文件/正式依据，回报版本/职责/所有权；不换会话，不虚构OS隔离，验收不签自己的实现。
- 主控拥有根规则/GitHub/summary/defects/matrix及新scope；developer拥有通用profile/launcher/HTTP/browser/日志接入；tester拥有本轮真实runner/相关契约回归/无凭据诊断脚本/私有观察证据，需交开发与验收审；acceptance仅追加已有acceptance-review.md。单文件单写者，交叉修改先交还。
- 只发布本轮真实新增CODEX START/DELIVERY，查重与API全文读回。若本轮写入安全拒绝，停止该写入，不改入口补发、不重做业务。不代发GPT未成功评论。
- 实际A操作与相关回归后更新现有summary/defects/matrix/验收，固定源码/测试/证据SHA、实际runner契约、浏览器首因已知未知、日志实际效果、允许提交差异、资源及独立结论；不以工具检查或数量冒A PASS。不新增P0或大型日志平台。
- 无scratch/历史来源连接，不建库/复制/恢复/升级，不动旧资金/库存/confirm/correct、B/C、D、双E、S11或生产；不装依赖、不改OS/PG/Docker/防火墙/core/odoo-12或长期服务。不改Issue/Project状态、不合并/强推/部署。

历史完整入口见[原字节归档](docs/history/AGENTS_before_20261018.md)和[校验](docs/history/AGENTS_before_20261018.sha256)；上轮规则保留于固定父Git历史。历史窗口/STOP不授权续跑。最新报告在 `docs/reports/s10-log-and-closeout-v2-r12/`。
