# S09 工作台与待核对安全边界定向返工｜YD-N1 R1

2026-10-13。以下均为 Codex 在隔离合成数据上的自测，不是 GPT 独立复核或用户效果验收。S07／S08-C／S09 历史原生 SIGSEGV 根因仍 **UNKNOWN**，生产部署继续 **BLOCKED**。

## 1. 授权、固定版本和隔离边界

唯一最新返工指令是 [#33 GPT-REVIEW 6143776424](https://github.com/Yredxin/YDental/issues/33#issuecomment-6143776424)。重新读取 #23、#33 当前正文与全部有效评论；#33 原评论 7 条没有新增或改写。从旧 final `6f7087f49e2f7bbd9c00d8b94500b1ee003e6c2d` 在原分支线性追加：先以 `c77b997644f8144b06e8d6370a0ecca22b433e2c` 固定失败复现，再固定 rework product `f7f6b231f0768eef5de4c19d2f789c32e5684853`、rework test `9f91420a91ee51e667f46ad56a8e35cc6f936bbb`，final SHA 见 #33 最终评论。product→test 只改变测试模块与 runner；test→final 仅说明、AGENTS 和脱敏证据。

Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，PG cluster `7694897083368259627`，原服务、odoo-12、镜像、持久卷、系统依赖、旧库、旧提交和全部失败证据未改。新最终库 `ydental_s09_test_20261013112825_b6d907e2`／OID `1566298`／端口 `18200`，新反向 S08-B 库 `ydental_s08b_test_20261013114700_d10b5fa2`／端口 `18201`，均由 guard 新建且不提供 reset/drop。原生信号闸门仍有效；本轮没有新 SIGSEGV，不据此声称根因修复。

## 2. 缺口复现、修正和业务事实

| GPT 指出的问题 | 固定失败／保护 | 本次产品闭环 |
| --- | --- | --- |
| 已做检查但缺价／缺材料时无法离场 | 旧源码 `_finish` 强制 event confirmed；预修复新库 `.local/ydental_s09_test_20261013104800_a8c42d7e` 安装 exit1，2 fail／1 error，覆盖缺价结束、错模板、文字覆盖测量 | 已真实执行的 pending event 可附真实原因完成检查段，原 event、actor、时间、pending 原因与责任审计保留；S06 原 lease/工位释放。未实施项目不能借此完成。原事件核价、核料按既有服务恢复，不能重复实施或另造 0 元 fee。最终 SQL：event152 `pending/missing_price`、fee0；execution534 `completed`、lease inactive；审计 `exam.pending_departure` 1。 |
| 工作台测量、附件、耗材不可用 | 旧 JS 文字保存恒发 `{}`；本批旧版负向实测测量丢失 | 表单按模板结构化显示单位和 `known/unknown/not_applicable`；服务端稀疏更新保留未编辑值及 0；附件真实上传、受控下载；当前 lot、实际数量录入并调用 S07 原生库存。缺必需材料拒绝新实施，已做事实仍 pending；更正需原因且增加独立版本。Firefox 录入 12.5→文字/更正 13、下载附件精确字节；SQL event153 一份耗用 qty1、inventory event248→`stock.move`286 done。 |
| 全景与 CBCT 错模板 | 预修复负向能将 CBCT 模板绑全景 catalog | 目录必须有明确审核的 capability family，模板声明的 family 与之精确相同，服务端 create/write/bind/result 均拒错绑，不按名称猜。历史合法绑定不覆写；同能力多工位不误拒。双 PG 错绑竞争最终仅合法绑定。 |
| 当前医生／区域缺结果入口 | 旧版只有全店 exam 列表 | S09 在工作台对当前医疗执行和 S06 原区域共享待办做只读结果投影，沿原后继 ancestry 显示全景已完成、CBCT 未做或待核对；D1 保留与 D2 新医生可见，原作者不变，后继仍唯一。不另建患者队列或 continuation。 |

## 3. 实际 F1—F4 回放

- **F1**：原生 S06 全景报到→对应工位叫号、开始→测量／附件→S05 实际 80 元版本→事件 confirmed／文书独立确认；CBCT 仍未做。探针 event101、price version107／snapshot87／fee83 `80.00`；Firefox event153、fee125 `80.00`，耗材 1 份走真实 S07 native move；一次执行一次经济源。
- **F2**：医生保留、检查人员独立编辑；部分结果返回不撤另一检查号位，真实 restore 才撤。模型与 T07 双 PG 竞争验证；Firefox 实际点击返回并在区域看已做全景、未做 CBCT。
- **F3**：交还后新医生从原 S06 唯一 continuation 接诊，工作台当前医疗段直接看到全景结果及 CBCT 余项；Firefox 实际打开并保存自身临床文书，原结果作者与费用不变。
- **F4**：昨日未做 CBCT 先拒直接实施，由当前医生点击重新复核，次日重新报到、单独叫号、测量未知、真实执行并确认；全景不再实施或计费。Firefox CBCT event154、fee126 `120.00`。模型测试另用受控业务日推进，不以 UI 夹具的昨日日期冒充真实时钟推进。

## 4. S09-T01—T13 固定 test 验收矩阵

| 项 | 本轮证据与结果 |
| --- | --- |
| T01 | PASS：全景／CBCT 工位严格分开，7组中两组同号位／同任务不同真实 PG backend 初始屏障，均一成功一拒。 |
| T02 | PASS：内嵌检查保留原医疗段；外派检查走独立报到／叫号／执行，草稿无经济事件。 |
| T03 | PASS：医生保留与检查结果接管保留原作者、编辑权和经济源；Firefox 可实际操作。 |
| T04 | PASS：交还后 D2 唯一续诊看到已完成全景和未做 CBCT；区域 S06 共享待办有同源入口。 |
| T05 | PASS：未做取消、已开始中止与部分完成边界；取消／实施双 PG 竞争后没有虚假 event/fee。 |
| T06 | PASS：冻结医嘱不能原位改写；新增需另单及原因。 |
| T07 | PASS：restore／start 双 backend 竞争仅一条合法路径。 |
| T08 | PASS：跨日模型真实业务日推进，Firefox 当前医生复核昨日余项后继续，既成全景保护。 |
| T09 | PASS：重复请求不双实施、不双费；更正增版本。pending 缺价与缺料可离场、原 event 仍 pending。 |
| T10 | PASS：错模板、伪附件、撤权、旧页、跨店、未授权 PDF/附件等服务端拒绝；Firefox 只读与无权角色 403。 |
| T11 | PASS：同 test SHA 安装148、升级146、已提交 F1 业务再升级146，均 0 fail／0 error；S08 A/B/C 同批上游测试。另新 S08-B 无 S09 安装 80 项通过，原 `test_exam_actual_start_remains_fail_closed_until_s09` 确实执行。 |
| T12 | PASS：续诊用原门诊资格，不借检查能力；当前医生与区域 S06 任务投影不增加后继。 |
| T13 | PASS：模板 family、测量合法状态／0／稀疏保存、真实 S05 价快照、S07 native move、审计和 12 类 SQL 不变量 0。 |

## 5. 固定实测、HTTP／Firefox／PDF／翻译／SQL

同一固定 test `9f91420` 的三次原生 Odoo 命令退出码均 0，安装 PID1903510/148，升级 PID1906147/146，带已提交 F1 业务再次升级 PID1908350/146；原始日志 SHA 与所有命令见 [机器索引](evidence/s09-rework/rework-final-tests.json)。业务探针 exit0，7组真实双 PG 首轮 backend 不同、deadlock0，包含 pending 结束、错模板、测量同版本冲突。[并发原始摘要](evidence/s09-rework/race-rework-final.json)。最终 SQL 19 表签名及 12 类不变量错误全 0；[审计](evidence/s09-rework/sql-final-audit.json)与[原生来源核查](evidence/s09-rework/sql-final-business.json)列出 pending 事实、fee、实际耗材和已释放 lease。

Firefox 四角色先以旧读屏／PDF 脚本运行15项／3图，再用[真实按钮脚本](evidence/s09-rework/browser-actions/20261013T114152656340/result.json)运行44项／13图，pageerror0；13图均逐张目视，[核图](evidence/s09-rework/browser-actions/20261013T114152656340/visual-review.json)。动作含报到、叫号、测量保存及重载、附件上传下载、lot/quantity、实施、确认、更正、部分返回、新医生接诊、跨日复核、CBCT 独立完成及权限失败。检查报告有严格来源、患者/行权限及审计。中文 PO 导出 276/276，无缺项和无效元数据。

[F1 确认版 PDF](evidence/s09-rework/pdf-final-20261013/pdf-check.json) 1 页、375 字，中文标签及来源一致，逐页图人工查看无遮挡乱码。[Firefox 更正版 PDF](evidence/s09-rework/pdf-ui-final-20261013/corrected-pdf-check.json) 1 页、第3版，画面及提取文本确证测量 13 mm 和更正所见。通用校验器原断言只接受“已确认”而在合法“已更正”报告返回 exit1；原失败不抹去，针对更正状态补逐页核对且未改变产品/test SHA。演示报告明确未审核签发、无设备/PACS 接通或正式医疗原件效力。

## 6. 失败历史、原生风险和限制

旧 final `6f7087f` 的缺口、预复现新库安装 exit1 及本批候选库 `ydental_s09_test_20261013105632_cab4f92a` 中的多次 Firefox 页面／选择器／材料交互失败原始日志与库均保留；候选 PASS 没有拼接进最终验收。此前 PID1792405 SIGSEGV 无 native C 栈或 core，GC/contextlib/registry 的 Python 栈不足以定位根因；历史 S07/S08-C 亦 UNKNOWN。本批固定运行无新 SIGSEGV，生产稳定性和部署依然 BLOCKED。正式临床字段、设备/PACS、正式签署、S10 收退款、S12 归档及生产价税政策未获批准，不在本次演示系统内。

## 7. Project／Issue 状态与观察到的差异

本批 Project **0 mutation**。最后两次完整只读快照各 21 字段／15 项／6 视图／7 workflow，彼此深比较相同；#33 `S09／进行中／Todo／OPEN`、#32 `S08／待用户验收／Todo／OPEN`、#34—37 待启用，保留项目及字段值与启动快照相同。但 S09 启动快照当时返回 **37 项**，当前 API 仅返回 **#23—#37 共15项**；#1—#22 未返回，原因未知。本批没有任何 Project 写操作，也未擅自恢复这些条目，不能声称全部 Project 条目仍与启动时相同。[双读与差异摘要](evidence/s09-rework/project-rework-final.json)。

## 8. 交付与停止边界

正常推送当前分支后，在 #33 发布 `[CODEX] S09工作台/待核对安全边界定向修正交付与再次技术复核申请`，附固定 SHA、真实流程、失败与限制，并逐字读回即停止等待 GPT 独立复核。S09 不自动转待用户验收，不关闭 Issue，不改 Project、启 S10、合并主分支、强推或部署生产。
