# S02修正交付与复核申请

依据 [GPT-REVIEW 6109759130](https://github.com/Yredxin/YDental/issues/26#issuecomment-6109759130) 与本会话用户授权，只修 BLOCKER-1～3 和停用 capability 新关联边界。沿用 `codex/s02-space-r1-20261011`，起点 `a4a6ae1277aa56c70d96542af60e9cbd45e0e3c6`；未从旧聊天、撤销计划补需求，未启动 S03。

已先将 Project 中 #26 的自定义“执行状态”从待启用单次改为返工，立即完整读回并二次同步。实际项目为 [Yredxin Project #4](https://github.com/users/Yredxin/projects/4) 的 Issue #26 条目；原生 Status 保持 Todo，Issue 保持 OPEN。事前读取全部条目字段、21个字段、6个视图及7个 workflow 的公开元数据，读回仅目标自定义字段改变。API 不暴露 workflow trigger/action 配置，未修改任何 workflow；可观察的身份/开关/时间戳前后完全一致。[Project 证据](evidence/s02-rework-20261011/project-readback.json)。本次单字段授权已经消耗，交付不再改 Project。

产品修正固定 **`de3cc85b2150ee3f9d42df6a947971607b51af74`**；最终测试/浏览器工具固定 **`637b74d2b49d19fc80a6246652bd4628e9f3b0a9`**。其间 `ae80d98` 仅修正原生 JSON 假值规范化测试，`637b74d` 仅修正浏览器对原生 SelectMenu 的选择方式；产品无后续变更。产品前序为 `c2ec75a` 四项修正及 `9a21b69` 模型/HTTP/角色工具补充；`de3cc85` 修正 native Many2many 对隐藏停用关系的实际清理行为。

原 S01 固定交付、S02 产品 `a128ff3`、测试 `0b87c1c`、文档 `a4a6ae1` 与原失败链全部保留；原 [S02报告](s02-report.md)、[旧证据](evidence/s02/runtime-history.json)、平面编辑/SVG/版本冲突接口均未重设计。差异仅后端六个文件及两条错误翻译、对应测试与验证工具、当前入口及新增修正文档/证据；没有修改 S01、static/、核心或第三方模块。本文配套 [定向修正契约](s02-rework-contracts.md) 仅替代原契约对应四项行为。

## 四项结果与实际流程

|复核项|完成情况/实现|直接模型、HTTP和实际路径|
|---|---|---|
|BLOCKER-1 公共/私有资源权限|完成；resource._resource_domain/create 拆分公共集团权和私有当前店业务权|独立 group_only 无 membership、无任何 space grant、无选店，可创建/修改/归档/恢复公共资源；浏览器真实原生表单创建/修改通过。普通 space=write 公共写拒绝，space=read 公共读通过；集团私有写及 context 默认他店私有 create 拒绝|
|BLOCKER-2 active 一致性|完成；station/item 约束触发加入 active，area 原有 active 约束保持|归档工位→归档子区域→action_unarchive/直接 write(active=True) 拒绝，原ID及item引用不变；按 floor→父区→子区→station 恢复通过。item 恢复检查有效 floor/resource；不物理删除历史，不新增 station 归档级联图形规则|
|BLOCKER-3 rect points|完成；area 服务端 rect 非空 points 拒绝，切换 rect 明确清空|超长/嵌套/字符串 direct create/write/layout RPC 拒绝；JSON假值由实际 ORM 安全规范化 False。polygon 3～100 有限坐标保持，101点/NaN/Inf拒绝；polygon→rect snapshot为空，rect→polygon缺点集拒绝|
|停用 capability 新关联|完成；geometry.capability_commands 按记录及命令序列比较原关系；version 写和审计读取完整存储历史|resource capabilities、station add/remove 三类关系均验证：新 LINK/SET inactive 拒绝；历史 inactive 显式 SET/无变化 LINK 可留；UNLINK/CLEAR/SET移除可清理，清理后再次关联拒绝；create 不允许 inactive；嵌套字典编辑仍拒绝|

各写路径保留 active 内部账号、真实 server-bound session、有效页面 revision、内容版本锁和公司范围规则。匿名、portal、伪造 Binding/旧 revision 不能维护公共资源；集团身份不能代替私有源资格。资源 export 仍需原 export=write 加源读取权，没有扩大导出。全部原子动作失败回滚，不把失败写进成功配置快照。

## 全新隔离运行与测试

核心固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，为本地声明20.0的 fork；不宣称已核对同 SHA 官方上游。Python 使用核心 `.venv/bin/python`。实际独立 Git 根和远端已核对，父根未跟踪 AGENTS.md 保留；没有修改核心、旧服务、历史/业务库、依赖或安全控制。

最终全新库 **`ydental_s02_test_20261011141857_3745e6ce`**，OID **199793**，端点127.0.0.1:5432/odoo，集群7694897083368259627；独立配置/data_dir/日志、精确 dbfilter、127.0.0.1:18103、cron=0、SMTP127.0.0.1:1及进程级外发限制，均由原 S02 runner 核验。创建时不存在，未重置或接管旧库。最终 install/upgrade/export/probe/browser 均固定到 `637b74d`。最终配置哈希和各动作退出码/日志哈希见 [runtime-history.json](evidence/s02-rework-20261011/runtime-history.json)。旧18102预览未停止或重配。

本次保留原13模型+2真实HTTP方法，新增4模型+4真实HTTP方法，共 **17模型+6HTTP=23项实质测试**。install 汇总25含2个原生 HOOT 入口（未匹配本模块单测资源而直接返回），不宣称完整原生JS套件运行；upgrade汇总23。浏览器在默认安全设置 Firefox155 执行原15项及新6项，共21项；截图、配置前后、角色断言、稳定ID/坐标、SVG摘要及并发结果见 [最终浏览器证据](evidence/s02-rework-20261011/final-run/browser-final.json)。

最终截图：[01平面](evidence/s02-rework-20261011/final-run/browser-attempts/20261011T142220309232/01-writer-floor.png)、[02保存](evidence/s02-rework-20261011/final-run/browser-attempts/20261011T142220309232/02-saved-floor.png)、[03画图拖放](evidence/s02-rework-20261011/final-run/browser-attempts/20261011T142220309232/03-drawing-and-drop.png)、[04安全上传](evidence/s02-rework-20261011/final-run/browser-attempts/20261011T142220309232/04-private-resource-upload.png)、[05只读](evidence/s02-rework-20261011/final-run/browser-attempts/20261011T142220309232/05-readonly-floor.png)、[06无选店/无space授权集团原生维护](evidence/s02-rework-20261011/final-run/browser-attempts/20261011T142220309232/06-group-only-common-resource.png)。已实际查看最终01与06，合成布局清楚，06顶部无当前门店且公共记录门店为空、修改后版本2；人工效果验收仍待用户复核。

|TC/回归|状态|实测范围与证据|
|---|---|---|
|T01|PASS|原树/稳定身份、多边形、真实矩形/多边形绘制和拖入资源；模型+浏览器|
|T02|PASS|工位更名、移动/尺寸、关联图形跟随，ID及引用保持；模型+浏览器前后读回|
|T03|PASS|资源并集加增减、区域发现不污染设备；新增停用关系保留/清理；模型+HTTP|
|T04|PASS|只读/异店/伪造范围、私有SVG403；新增独立集团无选店、portal/旧revision/私有默认值负向；模型+HTTP+浏览器|
|T05|PASS|原11类SVG攻击与上传负例、实际文件上传清洗；模型+HTTP+浏览器|
|T06|PASS|旧内容版本、非法批次整笔回滚、两个真实HTTP并发恰好1成功/1 version_conflict；模型+浏览器|
|T07|PASS|归档保引用、错店/归属拒绝、父级有效性恢复；新增四层恢复及resource停用反向；模型+HTTP|
|T08|PASS|全新 install 0 failed/0 errors/25；同库 upgrade 0/0/23；两个动作exit0|
|T09 空间及合成保护|PASS|最近报到祖先、合成in-use拒绝与参数前后审计；原模型保留|
|T09 真实排期/患者任务/队列/租约|NOT_RUN|未启用的 S03/S06 业务，不以合成钩子代替联调|
|T10|PASS|公共集团维护/普通拒绝、私有隔离、状态尚未接入、中文；原生导出135条词及来源引用匹配|
|隔离保护|PASS|原 scripts/test_s02_guard.py，5 tests/0 failure/0 error/exit0；无数据库写入|
|浏览器|PASS|21 checks/exit0，6张最终PNG，pageerrors为空；实际无授权集团原生入口通过|

实际命令（库已存在，runner拒绝再次install；不得重置）：

```bash
../.venv/bin/python scripts/s02.py install --db ydental_s02_test_20261011141857_3745e6ce --port 18103
../.venv/bin/python scripts/s02.py upgrade --db ydental_s02_test_20261011141857_3745e6ce --port 18103
../.venv/bin/python scripts/s02.py export --db ydental_s02_test_20261011141857_3745e6ce --port 18103
../.venv/bin/python scripts/test_s02_guard.py
../.venv/bin/python scripts/s02.py probe --db ydental_s02_test_20261011141857_3745e6ce --port 18103
../.venv/bin/python scripts/s02.py serve --db ydental_s02_test_20261011141857_3745e6ce --port 18103
PYTHONPATH="$PWD/.local/s00-b-deps/verify-lib" \
PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/s00-b-deps/browsers" \
LD_LIBRARY_PATH="$PWD/.local/s00-b-deps/browser-libs/usr/lib/x86_64-linux-gnu" \
../.venv/bin/python scripts/s02_browser.py --db ydental_s02_test_20261011141857_3745e6ce --port 18103 --evidence s02-rework-20261011/final-run
```

仅复用既有进程本地浏览器/字体，不安装依赖、不执行S00工具或接管其库。随机访问凭据仅本机0600文件，仓库/Issue不附凭据、session、患者资料、原始日志或备份。

## 保留失败链

本次第一库 `ydental_s02_test_20261011140720_44e1891a` 首次install（9a21b69）3失败/0错误/25：两个模型/HTTP测试暴露 native Many2many 自动保留 active_test 隐藏关联，导致 UNLINK 后重新 LINK 未被识别为新增；另一个测试错误预期 JSON 数字0应拒绝，实际原生 Json 会规范为空。前者在产品 de3cc85 窄化为显式能力写 active_test=False，后者 ae80d98修正预期并继续检查所有非空攻击。该库补交upgrade 0/0/23。

该库首次浏览器保留 FAIL：原15检查完成，新公共表单测试把 native SelectMenu 当成HTML select，选择器超时；637b74d改用实际原生菜单，补交21项PASS。没有为通过测试补授集团门店权限，也没有改产品UI或删除失败截图。第一库及所有动作/浏览器attempt保留；第二全新库完成最终重新install/upgrade/browser，最终证据单独写 `final-run/`，不覆盖第一库结果，更不覆盖原S02证据。

## 定向安全自查及限制

按已读取的 odoo-guidelines/odoo-security 自查修正差异：公共 domain 与 create 默认归属均服务端判定，受控session先于维护；私有未扩大；active-only写同约束；rect非空输入不进入成功快照；能力命令按完整旧关系逐条校验。active_test=False仅用于明确能力命令的底层 ORM 写及审计关系快照，不是sudo，不跳过ACL。原已有窄范围sudo字典存在性/反向引用/审计未扩成业务读写旁路。原SVG解析/路由、只读/公司范围、版本锁、安全上传全部保留并回归；静态前端文件未变。此为作者自查，不冒称独立复核。

没有业务数据迁移、级联物理删除、历史库清理或生产发布；旧库脏rect数据的批量清理不在本次运行授权内。图形有效不等价于station active/enabled，保留原历史关联语义。生产参数/人工用户效果验收/真实下游联调仍未完成，不宣称S02验收通过。

本次预览仅本机18103，四类合成角色可复查；若回滚预览，先核对本批配置和PID再停止本批进程，保留库与证据；不得用旧代码直接接管已升级库。没有生产回滚实测（NOT_RUN）。S03人员安排、S05预约、S06叫号继续按原接口文档后续接入，本次没有其模型、业务实现或启用动作。

申请对固定产品/测试提交及本次最终文档证据提交复核。#26保持OPEN、Project执行状态返工，不修改原生Status/workflows，不创建/合并PR、不启动S03。发布本申请后完整读回并停止。
