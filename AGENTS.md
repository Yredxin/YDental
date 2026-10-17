# YDental 当前执行规则

规则版本：MAIN-A-DEV-AUTONOMY-1.0（2026-10-18）。

## 正式来源与任务

- 用户直接授权 `YD-S10-LC2-MAIN-A-20261018-02`；task `S10-LOG-AND-CLOSEOUT-v2`；scope `EXISTING_MAIN_TEST_CREDENTIAL_SETUP_AND_A_CLOSEOUT`。
- [开发测试自主权](https://github.com/Yredxin/YDental/issues/23#issuecomment-6243010403)、[MAIN-A范围](https://github.com/Yredxin/YDental/issues/34#issuecomment-6243026115)、#23/#34当前正文及有效增量是正式依据。
- 固定父 `41e6c7c2b906653c9e264e4f402f5e572765bb98`；分支 `codex/s10-settlement-finance-r1-20261013`；产品保持 `cf5d63fe510b52ea150d07495bf3062f4ce0961d`。工作目录 `/home/redxin/code/odoo/odoo-sd/code/sd-addons`。
- [上一轮MAIN-A](https://github.com/Yredxin/YDental/issues/34#issuecomment-6242930304)有限A-STATE（60表1034行/93模块）已采，A-EDITOR/A-ORIGINAL未运行，本轮目标为完成剩余A。
- 本轮实际已结束：用户7/5凭据准备及用户7正常HTTP登录完成；A-STATE终核保全通过；A-EDITOR因私有runner切店断言错误在acquire前退出，A-ORIGINAL因唯一Firefox启动失败未运行。Odoo4/RO8/Firefox1本轮额度已耗尽；另有原生设备日志session标识前缀缺陷。A组仍BLOCKED，详见现有报告，等待复核，不自动恢复运行。
- 150项历史纯测试及[六项原生框架](https://github.com/Yredxin/YDental/issues/34#issuecomment-6242631423)已接受，不无变更重跑/重判。S10/T12及生产仍BLOCKED。

## 唯一目标与允许动作

- 仅main `ydental_s10_test_20261017105432_810a7d9c` / OID2144129 / cluster7694897083368259627 / `127.0.0.1:18410`。沿用既有解释器/依赖/应用账号，workers=0、max_cron_threads=0、db_maxconn=4。
- 必要身份/状态刷新；核明确项目合成测试资源且无人使用后，通过获准Odoo管理/ORM为既有临床用户7及至多一个有原件读取/导出权的既有用户设置随机密码。同一人满足时不增第二人。认证准备计Odoo启动，不直接写密码哈希或改认证实现。
- 普通登录页面以实际业务身份登录；核资格/锁，经既有服务使用新会话和返回令牌合法acquire/release。已经release仅核实；有效他人锁/资格不足停止对应操作，不清字段、改时钟、负责人或权限。
- 真实工作台点击既有原件1下载，核27665B、application/pdf、SHA256 `05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4`，逐页查看。不以旧副本/直接HTTP替代，不调用动态PDF。
- 保留文书1 confirmed/v4、作者/负责人7及版本9→10。不save/confirm/correct/handover/transfer，不重演临床/药房/资金。业务后独立核编辑权/审计与正文/版本/作者/费库账款保全。认证、会话/缓存、互斥计数、编辑权及下载审计分别列实际差异。

## 凭据与自主修复

- 正常授权测试登录和密码准备属于任务，不逐次要求用户找回旧密码。密码仍是凭据，不改变字段类型、鉴权或工具控制。
- 不扫描个人目录，不读取浏览器cookie/密码哈希、破解或回读此前被拒账户材料。只用明确本项目provider；需新建时用 `.local/s10-lc2-main-a-20261018-02/credentials/`（0700），文件0600且Git忽略。本机生成，仅需登录的执行角色使用。
- 凭据值不进入命令参数、消息、Git/GitHub、日志、截图、DOM、HAR或密码摘要。开发/验收只接收别名/角色/脱敏结果。
- 不改用户ID、active、员工/公司/门店关系、业务groups或资格；无权限不能加权或用管理员代测。
- 普通凭据失效/配置/解析/集成/断言错误内部修复，保留首失败/补丁。实际工具拒绝、Native、未知提交/资金、身份/完整性漂移或有效他人锁停止对应动作，不换agent/账号/工具重放被拒请求。

## 资源、角色与交付

- 首次接收 `2026-10-17T23:31:10Z`，截止 `2026-10-18T03:31:10Z`。新增上限Odoo4（含ORM准备）、main独立RO8、HTTP200、Firefox1、旧原件GET3；单服务1200秒，新raw256MiB、包总1GiB。
- 累计起点Odoo2/12、RO11/48、HTTP1/600、Firefox0/3、GET0/12。复用现有profile最小接入；旧账本/STOP不改、不清零，旧窗口不恢复。
- 主控统一调度；真实developer/tester/acceptance先读本文件及正式范围，回报规则版本/职责/文件所有权。单文件单写者；同库唯一业务执行者为本轮tester。验收不签自己的实现；角色不代表OS隔离，能力不可用如实记录。
- 主控拥有入口/归档/GitHub/summary/defects/matrix；developer拥有分派工具；tester拥有运行脚本及私有运行证据；acceptance仅追加现有独立验收报告。交叉修改先交回所有权。
- 查重后#34 START及DELIVERY均API全文读回，固定product/test/evidence SHA、真实角色、资源及A三项实际层级。更新现有报告/矩阵，不新增P0或大型日志平台。
- 不进入scratch、来源/生产/外部账号、B/C、D、双E、S11；不建库/复制/恢复/升级或运维；不改core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`、odoo-12或长期服务；不改Issue/Project、不合并/强推/部署。

旧入口完整原字节及一次SHA校验见[历史原文](docs/history/AGENTS_before_20261018.md)和[校验](docs/history/AGENTS_before_20261018.sha256)。旧“当前”、事故窗口与STOP仅作历史，不重新授权。最新结果见 `docs/reports/s10-log-and-closeout-v2-r12/`。
