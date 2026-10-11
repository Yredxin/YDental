# S01 修正交付与复核申请

仅按 [#25 最新 GPT-REVIEW](https://github.com/Yredxin/YDental/issues/25#issuecomment-6108433241) 修正 BLOCKER-1～4 和 COMPANY-SCOPE。沿用当前 S01 分支 `codex/s01-access-r1-20261011` 和同一会话，保留 e55f823 已通过能力、历史失败及补交证据。S01 仍待独立技术复核，#25 OPEN；S02 未启用，不生产发布。

固定产品修正 **`740c42bbf611baa8713758fba38c1411d6b966c9`**；固定产品+最终测试 **`f1ce22df7002e40391ce16fd59093d60c4522b2e`**。两者产品 tree 同为 `0bd0670ff54b6a0a75b03453204ea2f0c21a72a8`，差异只涉及两个测试文件。最终文档/证据提交在 #25 修正交付评论中固定；测试后没有更改产品、测试或运行工具。Git 根、版本树及核心保护见 [code-receipt.json](evidence/s01-rework/code-receipt.json)。

## 定向变更

|项|修正与证据|
|---|---|
|BLOCKER-1|去除客户端 care 字符串的授权效果；新增私有默认 FALSE 的 care 域钩子。合成模块仅用服务器固定标记和冻结 actor/session/revision/目标对象证明扩展。伪造 RPC、他店枚举、非目标记录、旧范围、跨店写和 settlement 负向测试通过；Firefox 实见目标历史而无无关历史。|
|BLOCKER-2|新登录范围首次真实消费默认门店建议，校验门店/任职/员工 active；非法建议留未选店。两个真实登录初始 B、独立手工切店、既有 session 不重复选店，用户全局 company/groups 不变。|
|BLOCKER-3|采用模型权限+审计方案。store/capability 普通 create/write 批量追加真实 actor/前后值事件；store 服务去重。公共字段直接写加入公司检查和 profile.change，原生权限仍有效；普通集团直接写拒绝，专门原生管理夹具直接写成功且一次审计。私有服务原有固定字段 sudo 路径在预先授权后单独记审计，不接受客户端抑制标记。|
|BLOCKER-4|原生 count/name_search/read_group/formatted_read_group/grouping_sets 返回受保护信息时一次 model/query 审计。target_id=0 明确表示查询；metadata 仅固定 operation，不保存 domain、正文、分组值、统计结果。普通 context 不能伪造内部去重 object；无业务读权聚合明确拒绝，查询日志只供同店原 actor 在仍有源读权时查看。|
|COMPANY-SCOPE|明确保留按 user.company_ids 限制集团动作。全账号 profile/depart 先核对目标允许/默认公司及全部 active/archived 员工和门店任职公司；有限 A 管理员不能改/停用另一公司或共享 A/C 账号；公共字段与原生 company_id/company_ids 同次写时也校验拟加入公司，不能靠自加公司扩大授权。人员日志按门店公司或全账号涉及公司保守过滤；模板 targets 同样校验门店公司。模型及真实 HTTP 负向验证均通过，目标账号与员工保持 active。|

完整补充契约见 [s01-rework-contracts.md](s01-rework-contracts.md)。生产 ACL、角色、许可证、依赖、原生 company 默认值未扩大；静态前端资产与原通过主路径保留。没有 OCA 引入、真实患者/病历模型或后续阶段空壳。调用签名依据实际锁定 fork 源码，使用 Odoo20 的 aggregates/grouping_sets API，不冒称核对同 SHA 官方上游。

## Project 和需求来源核对

实施前完整读取 Project #4 全部 **37 个条目（含 archived）、21 个字段、6 个视图、7 个 workflows 元数据**，并读取目标 Issue 当前正文和全部有效评论。只执行一次 mutation，将 #25 自定义“执行状态”从“待启用”设为 **返工**；立即完整读回、再次完整读回、交付前两次完整读回，语义比较均通过。原生 Status 保持 Todo，Issue 保持 OPEN，workflows 和其他字段/条目/视图均不变。见 [单字段核对](evidence/s01-rework/project/verification.json)、[交付核对](evidence/s01-rework/project/delivery-verification.json)、完整快照及操作日志。未将 Project 历史条目作为需求来源。

[#25 正文和最新复核评论未变](evidence/s01-rework/source-check.json)。未读撤销旧计划补需求，旧聊天和历史代码不授权新增业务。本次仅按用户明确授权例外更新该自定义字段，交付后仍为返工，等待 GPT 复核，不自行改为待复核或已验收。

## 最终运行与回归

最终全新隔离库 **`ydental_s01_test_20261011115257_85c44f56`**，loopback PostgreSQL 127.0.0.1:5432/odoo，cluster `7694897083368259627`；创建记录/OID/独立配置 SHA/data_dir/日志/精确 dbfilter/18090 端口均核对。cron=0、workers=0、SMTP 无外发；进程只允许本 PostgreSQL 和自身预览端口，浏览器只允许本预览源。核心仍 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，核心 Python 3.12.15；父目录未跟踪 AGENTS 原样保留。既有数据库、服务、核心和 odoo-12 未变。

|最终检查|结果|证据/口径|
|---|---|---|
|空库 install|PASS，退出0，0 failed / 0 errors / 29 tests|固定 f1ce22d；框架统计含安装阶段额外原生检查|
|同库 upgrade|PASS，退出0，0 / 0 / 27 tests|固定 f1ce22d；21 个模型方法 + 6 个真实 HTTP 方法|
|T01—T13|全部 PASS 当前/合成范围|原 13 TC 全部方法均实际启动；T13 改用受信任合成范围，旧客户端 care 用法不再作为合法证据|
|新增模型安全方法|5 项 PASS|care 信任及目标、首次默认店、直接主数据审计、单次最小查询审计、全账号公司边界|
|真实 HTTP|6 方法 PASS|原独立登录/旧页/RPC/原生 CSV/附件撤权/HTML 报告/模板路径；新增 forged care/aggregate 审计、默认会话/直接 master CRUD、有限公司 profile/depart/日志拒绝|
|隔离保护|5 项 PASS，退出0|[guards.json](evidence/s01-rework/guards.json)，无业务库连接或既有服务变更|
|Firefox 155|21 项 PASS；7 张最终截图已实际打开检查|[browser-final.json](evidence/s01-rework/browser-final.json)、[截图索引](evidence/s01-rework/browser-final.md)；默认安全控制，无覆盖设置|
|中文原生导出|198 词条无缺译/无缺引用|[translation-coverage.json](evidence/s01-rework/translation-coverage.json)|
|Codex 安全自审|定向修正及原有保护检查完毕|[review-sweep.json](evidence/s01-rework/review-sweep.json)，不替代独立 GPT 复核|

运行各次 commit、命令对应日志 SHA256、退出码、方法名和失败方法见 [runtime-redacted.json](evidence/s01-rework/runtime-redacted.json)。原始日志、凭据、SID/cookie、患者材料均不发布。执行命令：

```bash
../.venv/bin/python scripts/s01.py install --db ydental_s01_test_20261011115257_85c44f56 --port 18090
../.venv/bin/python scripts/s01.py upgrade --db ydental_s01_test_20261011115257_85c44f56 --port 18090
../.venv/bin/python -m unittest -v scripts.test_s01_guard
```

browser/seed 命令及隔离限制见截图索引。Firefox 最终验证和 install/upgrade 均固定 f1ce22d。原生只读 HTTP 在附加审计写时继续由框架重试到写 cursor；真实 HTTP 已确认成功且单次事件，没有关闭只读保护。没有只读副本可用性声明。

## 历史与失败链

[原 e55f823 证据](evidence/s01/) 和原报告/契约保持完全相同 Git tree，原 PASS 与失败材料不覆盖。本次五个库全部新建，不 drop、不 reset、不接管旧库。

|本次库后缀/测试提交|实际结果|处置|
|---|---|---|
|113145_8a6bfd16 / 45df40c|install：2 failed / 0 errors / 28，退出1|新增无读权聚合拒绝测试暴露空结果判断；固定显式 FALSE 后补交，失败保留|
|113326_ab887ef3 / a71d80e|install：1 failed / 1 error / 28，退出1|新增测试误认为原生自写规则可写应用公共字段；实际需要原生用户管理权限。修正为单独明确管理权限夹具，不扩大生产角色，失败保留|
|113553_19566503 / 9702b4e|install 28、upgrade 26，均0/0，Firefox21 PASS|保留该通过链；其后只补25行 HTTP 公司边界测试，产品不变|
|114045_4ea25b6c / af7f975|install29、upgrade27，均0/0，Firefox21 PASS|保留该通过链；其后在最终公司边界核对补拟加入公司预检查及26行模型/HTTP负向测试|
|115257_85c44f56 / f1ce22d|最终 install29、upgrade27，均0/0，Firefox21 PASS|最终完整交付链|

一次本轮失败诊断输出误带合成测试会话标识；两个失败运行进程结束后，已把其有效 sessions 目录移到本地私有保留位置，不记录值、不发布日志，见 [test-session-retirement.json](evidence/s01-rework/test-session-retirement.json)。仅按精确 PID/config 检查停止了本批中间新起的 18090 预览以换到后续新库，见 [preview-stop.json](evidence/s01-rework/preview-stop.json)；既有 18089 服务不停止或重配。

最终合成预览为 `http://127.0.0.1:18090/ydental/access`，私有测试凭据只在本机新库 run 的 0600 文件。浏览器创建/复用合成员工并撤销 operator 的 A 任职，B 登录读取保留。需要手工重复该前提时仅在本合成库通过集团受控动作重新关联/授权；不能复用为生产配置。

## 未执行边界与复核请求

真患者/病历/检查、S03 真实排班、S06 坐诊租约、正式邀请送达、真实 MFA/长期 idle、正式 PDF/实体打印、50 会话及持续备份恢复、S13 美化均保持 **NOT_RUN**。自然人复用只证明原生 login 或明确账号 ID 复用，不宣称强自然人唯一识别。正式生产参数和名单仍待对应责任阶段批准，未部署业务环境，不提供生产回滚验收声明。

申请 GPT 复核固定产品、固定测试及最终文档/证据版本，重点查看五项定向修正与负向回归。用户效果验收仍需独立记录。写入 #25 后完整读回并停止；不关闭任务、不改原生状态、不合并 PR、不启动 S02、不发布生产。
