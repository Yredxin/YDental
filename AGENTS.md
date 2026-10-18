# YDental 当前执行规则

规则版本：MAIN-A-ORIGINAL-UI-1.0（2026-10-18）。

## 正式依据与唯一当前任务

- 用户本会话直接批准 `YD-S10-LC2-MAIN-A-20261018-04`，task `S10-LOG-AND-CLOSEOUT-v2`，scope `MAIN_A_EXISTING_ORIGINAL_UI_ONLY`。用户提供《17_CODEX_MAIN_A_ORIGINAL_UI_CLOSEOUT_20261018.md》全文；仓内未找到同名附件，不冒称读取附件原字节。
- 完整依据：[正式复核6243885093](https://github.com/Yredxin/YDental/issues/34#issuecomment-6243885093)、[实际交付6243816035](https://github.com/Yredxin/YDental/issues/34#issuecomment-6243816035)、[开发测试自主权6243010403](https://github.com/Yredxin/YDental/issues/23#issuecomment-6243010403)及#23/#34当前正文/有效增量。GPT复核未新增额度；本轮额度只来自用户直接采用的新正文。
- 父 `980eda60f011b1dec5fbf16ee8f10cc8e7cfa414`；分支 `codex/s10-settlement-finance-r1-20261013`；目录 `/home/redxin/code/odoo/odoo-sd/code/sd-addons`；product保持 `cf5d63fe510b52ea150d07495bf3062f4ce0961d`，core只读 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。
- A-EDITOR已正式采纳：审计1191/1192/1193及独立提交终核，编辑字段已空，文书1 confirmed/v4、作者/负责人7、版本9→10。**本轮禁止用户7登录及任何acquire/release、save/confirm/correct/handover/transfer**，只能有限RO确认持续保全。150纯测试/六原生框架、指定device日志修复和Firefox启动配置均已采纳，不无变更重跑，不重置凭据。
- A-ORIGINAL尚未完成；旧UI失败确切URL缺失，不能将已确定的http_routing源码缺口倒填为历史实测根因。旧窗口/STOP/失败原文与Git历史保留，不恢复03任务。

## 本包实现及真实验收

- 仅main `ydental_s10_test_20261017105432_810a7d9c` / OID2144129 / cluster7694897083368259627 / `127.0.0.1:18410`。沿用既有解释器/依赖/应用账号，workers=0、max_cron_threads=0、db_maxconn=4。不在运行进程中热改源码；固定候选，复用owned服务，每次≤1200秒。
- 运行前共同核已安装模块对登录页/结算工作台的有效前端配置及正常资源，不只读web默认实现。http_routing的translationURL覆盖与默认回退、真实JS hash/lang producer均须经最终_request_allowed/实际调用点回归。两层规则优先共用小判定；仅同源必要只读初始化资源、真实query形状，未知/跨目标/业务写仍拒。不加第三层调度/代理/框架，不泛放/website/**或全部GET/RPC。
- 诊断只保静态已识别路径名称/动态模板、方法、查询键名、形状布尔、命中规则/阶段、实际派发及响应状态；不保完整query/fragment/POST正文、DOM/HAR、凭据或摘要。登录前读取允许非敏感初始化配置，核资源及表单存在/可见/可编辑布尔；本地拒绝须优先保存首因并结束等待，不只留下fill超时。不改DOM显示/密码类型、鉴权、cookie或前端初始化。
- 真实Firefox：用户5正常登录→正常选店1→真实结算工作台→点击invoice1的既存原件1链接→真实下载事件保存文件。说明现有上游转发/手动重定向层，不冒原生自动重定向兼容。原件1/附件161/invoice1/patient1/store1/company1，27665B、实际MIME application/pdf、SHA256 `05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4`，核完整性并逐页查看本次下载文件。
- 下载已发生则保留文件/审计，后处理错误只修后处理，不盲重点击。不得用直接HTTP/旧副本/新票据替代，不调用动态PDF/新建覆盖原件。前后必要有限RO核身份、无冲突、user5既有settlement/export资格、旧文书/版本/作者、费库账款/原件及已释放编辑字段保全；不反复转储60域、不重置业务基线。不新增编辑审计或mutex变化，正常认证/会话/缓存/下载审计分列，不称全库只读。

## 凭据、日志、资源与停止

- 只由需要登录的tester程序使用 `.local/s10-lc2-main-a-20261018-02/credentials/` 既有用户5 provider（0700/0600/Git忽略）；开发/验收不读值。缺口据实报告，不扫描个人目录/旧被拒材料，不读密码哈希/cookie、不重置密码/新建用户/改权限。
- 凭据值不进命令参数、消息、Git/GitHub、日志、截图、DOM/HAR或可离线猜测摘要。正常登录自主执行，不逐输入请求用户确认，不改变字段类型/鉴权/工具控制。
- 保持既有 `odoo.addons.base.models.res_device` WARNING30及actualPID/config证明，接入04，不另建日志机制、不关正常日志/设备记录/S01审计。新日志只作有界脱敏核验，旧敏感日志私有保全，不输出原行/标识/摘要。沿用已确认Firefox及子进程既有本地库配置，正常driver环境白名单不变，不重复空白页诊断、不安装依赖/关sandbox/改共享服务。
- 首次接收观测 `2026-10-18T00:53:07Z`，截止 `2026-10-18T04:53:07Z`。新上限Odoo2、main独立RO8、本地HTTP200、Firefox3、原件GET3；每服务1200秒，新材料256MiB/包总1GiB。所有实际尝试含失败计账，无免费诊断/浏览器/HTTP。
- 继承累计Odoo8/12、RO25/48、HTTP25/600、Firefox5（仅本任务上限明确调为8）、GET0/12；旧accidentRO2/maintenance1/CREATE2保留。新profile/日志证明/请求判定/预算调用者一致接入04，不清旧账目或STOP，不冒用旧窗口。
- 普通已确认资源/selector/脚本集成错误在包内自主修复、保首失败、定向回归/新候选，前次owned资源收敛后再运行；每次重试有新增证据/补丁/明确不同假设。未知请求不自动放行；真实工具拒绝、Native、未知提交/身份/完整性异常停止对应动作，不换工具/模型/账号/执行者重放。区分本地白名单误判与平台拒绝，无通用ignore开关。

## 团队与交付

- 继续 `/root` 主控、`/root/developer_autonomy` 开发、`/root/tester_autonomy` 唯一main执行者、`/root/acceptance_autonomy` 独立验收。各角色先读本文件及正式依据、回报版本/职责/所有权，不换会话，不虚构OS隔离，验收不签自身实现。
- 主控独占AGENTS/scope/GitHub/summary/defects/matrix；developer独占通用profile/HTTP/browser/launcher/日志最小适配；tester独占实际runner/相关契约回归/有限RO观察及私有运行证据；acceptance仅追加现有acceptance-review.md。单文件单写者，跨改先交回；运行前共同交叉审真实runner及有效前端配置。
- 查重后只发布本轮真实 `[CODEX-START / MAIN-A / ORIGINAL-UI]` 与 `[CODEX-DELIVERY / MAIN-A / ORIGINAL-UI / GPT-REVIEW-REQUEST]`，API全文读回。写入安全拒绝停止该写入，不代发旧被拒评论，不为同步重跑应用。正常线性提交推送，不合并/强推，不改Issue正文/状态或Project。
- 更新现有报告/矩阵，固定product/工具/实际执行/证据SHA、相关回归/页面诊断、用户5登录/点击/下载链、实际文件SHA/逐页结果、终核差异/资源及独立结论。未下载或未目视保持NOT_RUN，不只交未运行修正版；不新增P0/大资料包/框架。A完成仅交GPT整体复核，不扩大为S10/T12或后续通过。
- 不连接scratch/历史来源/生产/外部账号，不改密码/用户权限/编辑权，不出账收退款/库存/日结/动态PDF/新原件/建库复制恢复升级，不做OS/PG/Docker/防火墙或共享服务运维，不碰core/odoo-12或长期服务，不进B/C、D、双E、S11或生产。

历史完整入口见[归档](docs/history/AGENTS_before_20261018.md)及[校验](docs/history/AGENTS_before_20261018.sha256)；03规则与失败保留于固定父Git历史。当前报告 `docs/reports/s10-log-and-closeout-v2-r12/`。
