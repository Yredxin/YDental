# S10-CLOSEOUT v1.1 R0检查点与R1待批准预算差异

状态：**R0取证器门禁失败已封存；R1仅离线准备，等待源尾审预算例外。**
本文件不是S10技术PASS、正式阶段交付或GitHub P0-25授权。
用户直接批准范围、完整计划及原确认见 s10-closeout-v1-plan.md 和
evidence/s10-closeout-v1/user-approval.json。

## 已实际执行

父7d52d9e；R0执行53665a184893e7056c20cb1d1241f4117a2be809，产品/core未改。
预检评论 https://github.com/Yredxin/YDental/issues/34#issuecomment-6231682329
已REST正文逐字读回，记录08:21:49.739220 UTC；GitHub同步成功独立列示，非业务PASS。
414项冻结含10份执行脚本。离线initial exit0，final因独占输出已存在exit1保留，
frozen完整进程exit0/12项；不能以中间文件exit0覆盖失败进程。

唯一新副本ydental_s10_test_20261017080710_2494c102，OID2144127，
cluster7694897083368259627，18325，独立config/data/真实filestore复制、无硬链接。
源P021 OID2122140复制前645表/schema及198文件核同有效尾审；复制初始完整核同。
第一次源RO关闭后才CREATE，维护/CREATE各1，没有第二库、其他旧库访问或旧经济重放。

native PID940956/backend1473875，exit1，无SIGSEGV，观测pool count1/max8。
A原责任人7的新合法scope已COMMIT并独立读回：只新增session107、audit1173/1174。
acquire确已在事务内调用，完整before/after/full-diff及拒绝先保存。
六行差异为四固定mutex各+1、doc1编辑字段和clinical.edit_acquire审计1175。
实际editor7/audit actor7，doc.write_uid1与严格write_uid7断言冲突，拒绝并整笔回滚。
没有acquire COMMIT、没有A成功marker。confirm/correct/release/心跳/B/C/D/E均0。
Firefox/业务HTTP/RPC/PDF生成/原件下载/升级均0。

最终独立新RO完整645表与复制初始相比，仅上述已提交scope的三行新增，其他全相同。
与acquire前快照的相关完整存储事实完全相同，证明本次失败动作已回滚。
doc1仍pending/v2/editorNULL；原账款/库存/原件/权限/附件不变。
源最后一次RO及198文件前后相同；源2/2已消耗并关闭。

实际RO5/28，均ROLLBACK/CLOSE：source-before、clone-initial、A-owner-scope-committed、
final-tail、source-final。维护1/1，CREATE1/1，Odoo1/6，COMMIT returned1且独立核验1；
资金库存业务提交0。现有P021财务/原件和全部旧裁定均未撤销或重判。

## 离线确定的修正

取证器在普通actor动作后先snapshot(root_uid1).flush_all。
固定core environments.py::flush_all→models.py::_flush→_write_multi，缺失dirty log字段时
用当前env.uid补write_uid；Many2one.write对相同值过滤不标dirty。
旧write_uid已7、普通actor仍7时，uid1 flush可以补1。
实际固定core函数前缀（SQL前）隔离执行给出uid1默认1、uid7默认7、已有dirty7不被覆盖。
结合完整真实差异和独立回滚证据，定位为取证器flush身份缺陷，不归因于产品权限或Native。

R1仅新脚本改为每个真实API/授权动作后先actor.env.flush_all，再uid1只读投影；
不手写write_uid，不接受write_uid1，不改产品/core、锁、作者、审计或经济断言。
新纯文件检查仍拒绝原真实writer1，合成writer7夹具可过；旧文件没有改字节。
R1只允许同一副本、核清当前状态后有限回归，无CREATE或旧资金操作。
C撤权/恢复使用同一合法经理的真实HTTP授权接口，以保持总Odoo≤6。

## 必须待批准的唯一预算例外

R0停止收口提前用完了原计划两条源RO；不能把该尾审冒充后续R1结束时的证明。
已向负责人请求：最多追加1条同一P021源的RO/RR，仅全包最终保全、ROLLBACK/CLOSE。
本请求不是自动生效；尚未生成批准凭据、尚未第三次连接源、尚未继续副本业务。
其他总RO28、Odoo6、唯一CREATE1、修复2及其他预算不扩大。
若不批准，则按当前实际BLOCKED范围封存、提交正式回执；不会换工具、身份或入口绕过。

## 当前证据入口

- R0-stop-facts.json：真实提交与未执行清单；R0-clone-initial-to-stop-diff-index.json：完整尾审差异。
- r0-prepare-all-acquire-1-diff-index.json和decision：原失败；私有before/after/full-diff保留。
- R1-offline-repair-check.json：隔离core前缀及独立回滚证明，零新数据库/Odoo操作。
- source-final-preserved.json：R0时点的源保全；不冒充未来R1终点。
- github-preflight-sync.json：真实评论及逐字读回；未发布R1执行预检或正式交付。
- repair-r1说明列出具体代码/预算差异。后续是否继续，等待用户对预算例外的明确选择。

S10退出五组仍未完成，旧v→6/无效JSON/Native风险继续UNKNOWN，不新增同类诊断批次。
本检查点不启S11、不改Issue/Project状态、不合并部署。最终固定证据提交及实际Git推送
会单列，不能以本机已提交冒称推送成功。
