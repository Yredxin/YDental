# S09 原生崩溃诊断、F1 合同修正与完整交付复核｜YD-N1 R1

> 2026-10-13。以下是 Codex 在隔离开发环境的自测记录，不代表 GPT 独立运行或用户效果验收。原 S07、S08-C 和 S09 原生崩溃根因仍为 UNKNOWN，生产部署仍 BLOCKED。

## 1. 授权、版本、环境与数据保护

唯一续作授权是 [#33 GPT-REVIEW 6141720532](https://github.com/Yredxin/YDental/issues/33#issuecomment-6141720532)，上游 S08 最终技术 PASS 是 [#32 6140703673](https://github.com/Yredxin/YDental/issues/32#issuecomment-6140703673)。本批已重新读取 #23/#33 正文和全部有效评论，并发布且逐字读回 [第一阶段诊断 6141807213](https://github.com/Yredxin/YDental/issues/33#issuecomment-6141807213)。沿用 `codex/s09-exam-workbench-r1-20261013`，从旧 final `17cd02bf120fa9446af8d4e0effe9d0203570348` 线性追加；无强推、覆盖或删除旧库/日志/样张。产品最终 SHA `739a473948b014c7a31c2bda23c62f3b79e7336d`，测试最终 SHA `197d1942753fc5cb960af54b47f51dbd7959e4c7`；final SHA 见最终 #33 交付评论。

产品修正发生在测试补齐过程中：`08f9941` F1/跨日/模板/结果责任，`0b8c4d0` 中文 PDF 引擎，`4ac124f` PDF 错误翻译，`6d3e5ca`/`92a32bf` Odoo20 原生附件 raw，`739a473` 中文状态。测试提交 `b7c52cb`、`344570f`、`2de692d`、`197d194` 对应发现的缺口。所有失败候选与提交保留，最终资格仅取 `197d194` 之后的新隔离库。`739a473 → 197d194` 只改变测试文件。

Odoo Community 20.0 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`、项目 Python 3.12.15、PG 18.6 cluster `7694897083368259627`，既有 `odoo20-db` 卷、`odoo-12`、原服务和系统级依赖均未变。每座库均由 guard 新建，校验数据库 OID/cluster、配置 SHA、端口、data_dir、core SHA 和外发策略；不接受历史库或重置。最终库身份、端口和日志 SHA 见第 7 节。

## 2. 原生崩溃取证与有界诊断

旧 PID **1792405** 的原生日志 SHA `761e3cd6bfda2aef894fd7c413e532c28fcc853aa89b054452db4995b6132daf`，原生 exit `-11`。`PYTHONFAULTHANDLER=1` 最后 Python 栈为 GC → `contextlib.__exit__` → Odoo `registry.py:176`；17 个 native 扩展，core 软限 0，apport 记录信号但忽略非打包解释器，无 C/native 栈及 core；kernel journal 无匹配故障。Python Build-ID `7713d416ece8f53a2b37e61dd06defd7bf795954`、libpython `747f424108b209be95adc6bb8a826419eb7d6153`。旧 S08-C 在 `dict_dealloc`、S07 在 `_PyObject_Calloc` 的痕迹不能证明同一根因。结论始终 **UNKNOWN**。

第一阶段不启动 Odoo；仅在 [诊断回执](https://github.com/Yredxin/YDental/issues/33#issuecomment-6141807213) 写回后，按授权在新库 `ydental_s09_test_20261013084700_e6a4c2d1`／OID `1419240`／端口 `18191` 运行**恰好两次**旧固定源码定位调用：PID `1803641` install exit 0；PID `1804184` probe exit 1，为已知 F1 返回断言，均无新 native signal。没有用偶然无崩溃声称根因修复。诊断后才进入正式新代码和测试；之后任何新 SIGSEGV 的停止闸门始终有效。[脱敏诊断摘要](evidence/s09-rework/native-diagnosis.json)。

## 3. F1 四种状态、80 元原价与原生经济来源

旧 `_perform` 把 S08 事件返回的 `state` 用文书的 `pending` 覆写，故旧 F1 `actual['state']=='confirmed'` 必败；旧断言短路时不能推断费用。修正后返回保留原事件 `state`，并分列 `event_state`、`result_document_state`、`order_line_state`、`fee_source_state`。真实执行与文字确认分开：文字草稿不收费；一次实际执行调用既有 S08 event → S05 有效原价版本和快照 → 一份 fee；文字确认/更正/重传/PDF 下载不重记费。缺价事实保持 `pending`、无假 0 元费用，后价不能替代原价。

最终固定库 F1 以精确映射对应的 S05 演示价 80 元发布；真实全景 event、原价版本、快照、fee、库存耗用、CBCT 余项等数值见第 7 节及脱敏 F1 结果。空耗材列表不造 S07 库存事件；有耗材时复用既有 S07 原生 `stock.move`/`stock.quant` 和 S08 费库，不新建可改库存余额或财务账本。

## 4. 功能合同、权限与现场路径

检查工作台复用 S06 唯一患者号位、lease、执行与店/区域待办。S08 已冻结的检查医嘱行绑定 exact catalog/capability/任务；全景与 CBCT 不串叫，同能力多工位只有一个领取。检查资质绑定人员、门店、代码、起止期、撤销；模板需管理/医疗授权在**准确检查目录**显式绑定，不能凭目录名称猜测。

内嵌检查只在当前医疗段工位与人员同时具有准确能力时运行，不另建外派执行或关闭医疗段。外派检查按报到→叫号→开始→独立结果草稿/附件→真实执行→文字确认/更正→检查段结束；未做取消由医生附原因执行，已开始用中止/部分完成或完成事实，不删除已发生经济源。结果有独立作者、责任人、接管、编辑会话、不可覆盖版本和审核日志；上传附件不等于实际实施。Odoo20 附件改用 `ir.attachment.raw` 存取，下载返回真实 bytes，要求当前源读取及 export-write。

原医生保留时技师可独立编辑，`query_return` 只提示；真实 `restore` 才撤 CBCT 等候/叫号。交还后原作者保持，D2 新医生在原门诊能力方向的唯一后继取得已确认部分结果，未做 CBCT 保留。跨日清理不抹医嘱与既成检查，次日由当前医生在新医疗段重审剩余检查才允许重新报到。初版中文 PDF 强制中文模板及 UTF-8、本机已验证中文字体、禁外部资产和脚本、受控下载与 SHA 审计，醒目标为“演示草案／未审核签发”；不冒称 PACS、设备接通、正式签署、S12 原件或 S10 收退款。

权限仍沿 S01 门店/公司/患者关系；检查写、医疗写、导出写各自独立。服务端 `_operate` 使用已有 S01→S04→S03→S05→S06→S07→S08→S09 锁序、请求指纹和幂等 receipt；原生 RPC 不能直接 CRUD 改写结果，跨店、撤权、旧会话、伪造附件 ID 与报告 URL 受拒。S09 未安装时，S08-B 检查启动仍按原接口 `exam_integration_required` fail-closed。

## 5. S09-F1—F4 真实回放

| 流程 | 固定版检查点 | 结果与证据 |
| --- | --- | --- |
| F1 全景＋CBCT | 只报全景、CBCT 空闲不抢；全景真实执行／80 元费源／结果确认，CBCT 未做 | 固定库 probe PASS：医疗执行 343、检查执行 344、医嘱 95、全景行 143、CBCT 行 144、事件 99 `confirmed`、结果文书执行后 `pending`、行 `done`、费源 `recorded`；S05 版本 105／快照 85／费用 81 为 80 元，结果 27／版本 2，CBCT 仍未做；空耗材无库存事件。固定 ORM 测试、Firefox 及 PDF 均通过。 |
| F2 医生保留 | 全景执行时独立结果编辑；CBCT 已报到叫号；提示不撤号，确认恢复才撤；已执行时恢复拒绝 | 固定 ORM `test_f2_partial_result_return_restores_only_on_confirmation` PASS：提示后 CBCT 号位不变；真实恢复后号位 `void`、任务 `pending`、医嘱行仍 `issued`；无 CBCT 费用。T07 双 PG 竞争仅一方成功。 |
| F3 交还与部分返回 | 原医生下班，唯一根管方向续诊；新医生看已确认全景、CBCT 余项；原作者及 fee 不变 | 固定 ORM `test_f3_handover_to_new_doctor_sees_only_completed_result` PASS：新医疗执行 ID 与旧段不同，患者相同，续诊能力为原门诊方向；确认全景可读、CBCT `issued`，原医嘱作者、费用和唯一后继保持。 |
| F4 跨日余项 | 昨日全景完成；清昨日队列；今日医生再确认 CBCT，重新报到执行；全景不重做重费 | 固定 ORM `test_f4_next_day_requires_doctor_revalidation_and_preserves_done_line` PASS：受控 Odoo 时钟推进一天，昨日号位清理后任务 `pending`，全景仍 `done`；无新医生复核先拒绝，复核后新报到／真实 CBCT 事件 120 元；全景原 80 元费只一份。 |

## 6. S09-T01—T13 逐项矩阵

| 用例 | 固定版状态与实际依据 |
| --- | --- |
| T01 | PASS：`test_panorama_task_cannot_be_called_from_idle_cbct_station` 拒绝 CBCT 错叫；两组双 PG backend 首轮屏障分别争同一任务、同一已叫号位，各仅一成功。 |
| T02 | PASS：`test_inline_examination_keeps_medical_execution` 和 `test_draft_no_fee_and_template_measurement_rejection`；草稿无事件／费用，真实执行确认，原医疗执行仍 `serving`，无外派执行。 |
| T03 | PASS：F2 与 `test_result_takeover_requires_release_and_preserves_original_author_fee`；保留与技师独立编辑、释放后接管保持原作者及费用。 |
| T04 | PASS：F3 已确认部分结果与同原门诊方向唯一新医疗段；CBCT 留待执行。 |
| T05 | PASS：`test_unperformed_cancel_blocks_reporting_and_frozen_order_edit`、`test_started_inline_exam_cannot_be_cancelled_as_unperformed`；取消／实际执行双连接均先满足资格，竞争后取消成功、事件与费用均 0。 |
| T06 | PASS：已签发原单增删拒绝；有原因新增医嘱保留新 order ID 与原作者。 |
| T07 | PASS：恢复／检查开始双 PG backend 屏障各一成功一拒绝，最终仅一个有效执行；F2 提示不暗撤号。 |
| T08 | PASS：F4 受控跨日时钟推进、昨日号位清理、当日医生复核与重新报到。 |
| T09 | PASS：F1 同请求重放返回 `already_accepted` 且原事件 ID；独立结果确认／更正只增版本，费库仍唯一；缺价则原事件 pending、无伪费用且后价不得补入原价。 |
| T10 | PASS：模板未绑定拒绝；附件需当前编辑源与导出权限，伪附件 ID 拒绝；医生/只读角色 PDF 403，技师 Firefox 真实下载；中文 PDF 单页逐页查看可读。 |
| T11 | PASS：固定 test 安装 145、升级 143、带 F1 已提交业务再升级 143，均 0 fail/0 error；S08 A/B/C 同批集成测试运行；另见 S09 未安装 S08-B 原接口回归。 |
| T12 | PASS：F3 的 D2 新执行使用原门诊能力，不借用全景／CBCT 能力；原医生退出后新医生读取独立确认结果。 |
| T13 | PASS：模板测量类型、未知值验证，S05 原价／快照、结果查看／更正／下载审计，权限负向与 12 类 SQL 不变量为 0。 |

## 7. 固定版本运行、Firefox、PDF、翻译、SQL 与失败保全

固定库 `ydental_s09_test_20261013101000_0f5c8d2a`，OID `1501596`，端口 `18196`，cluster `7694897083368259627`，配置 SHA `eb36feec67e40fba2288516fef3f938764ca44136eebcb6a6f1b7a66ddae0a5d`。在同一固定 test `197d194` 上：install exit 0／PID 1853562／145 测试；upgrade exit 0／PID 1856226／143 测试；提交 F1 业务后 upgrade exit 0／PID 1858609／143 测试；三次均 0 fail／0 error。对应私有日志 SHA 依次为 `54f475f0aefc1640f2fe538f01678507f71bac7161c411821496746881c1810c`、`90d04fce884bf572ae562876e2ce207018ebb5fdd2c1ff0b5275c110cd0eed06`、`5f42f22bf8f8ae93be3cb23a7ec500080f56612000d2fc69946535d85d28e1f8`；命令明细及其他 exit/SHA 在[固定运行索引](evidence/s09-rework/final-tests.json)。

四组真实独立 PG backend 首轮屏障均一成功一拒绝，初始 PID 202151/202169，deadlock 0。[并发摘要](evidence/s09-rework/race-final.json)。真实 HTTP/RPC 负向包含 CSRF、未授权、旧版、跨店/角色及附件来源；Firefox 4 个角色 15 项、3 张合成图逐张目视、pageerror 0，技师原生下载 PDF，医生及只读导出 403、无权用户工作台 403。[Firefox 结果](evidence/s09-rework/browser/20261013T102400798830/result.json)。浏览器脚本首次要求 `f1-result.json` 而 probe 产出 `f1-result-99.json`；先因缺本地 fixture 退出，再以原 probe 字节创建不覆盖的同内容别名，才执行实际 Firefox PASS。未改固定产品、测试代码或业务库；此搭建缺口保留为遗留测试脚本局限。

另在 S09 未安装的新隔离库 `ydental_s08b_test_20261013102620_8b7e91ac`／OID `1518295`／端口 `18197`，以同一 Git test SHA 运行原生 S08-B install exit 0、PID 1863526、80 测试 0 fail／0 error；其中 `test_exam_actual_start_remains_fail_closed_until_s09` 实际执行且未跳过，验证原接口拒绝检查启动。日志 SHA `373ee42f471623cf6e62a6382204b574c2188e510bfc39ece24522f89f6b3c54`，独立库未覆盖历史库。

最终原生 QWeb/wkhtmltopdf 报告 26605 字节，1 页，PDF SHA `d886c72f5e95aba8183d2607e22210e550e3c6d1384344b38d2a3eb988de43c3`；Firefox 下载是同源另次渲染，SHA `981b146354bca9b6c6c966f1ade1fc858992e977d0b94ae5a5b4efe0d5ac8c63`，两次逐页文本与图像 SHA 相同，374 字且中文“已确认”可见；人工检查无遮挡、乱码或空页。[逐页检查](evidence/s09-rework/pdf-final/pdf-check.json)和[人工目视](evidence/s09-rework/pdf-final/visual-review.json)。中文导出 217/217 翻译，缺项/无效元数据/代码 0。[翻译审计](evidence/s09-rework/translation-ydental_s09_test_20261013101000_0f5c8d2a.json)。带业务再次升级前后 19 个业务表签名相等，12 类 SQL 不变量错误 0；竞争后再次审计亦 exit 0。[SQL 摘要](evidence/s09-rework/sql-upgrade.json)。

固定前候选库的通过结果不能代替最终版本。原旧库、2 次定位新库、全部候选新库、失败日志和乱码 PDF/PNG 均保留；不重置、不删除。首次附件负向暴露 Odoo20 `datas` 已移除、返回 `raw` 为惰性二进制对象；原失败 install/upgrade 与修正后的单测各自保留。初次中文报告出现 mojibake；旧失败样张与 UTF-8 修复样张各自保留，最终以新库样张为准。

## 8. Project 状态、剩余风险与复核边界

Project #4 本轮 0 mutation。实时两次只读快照相同；21 字段、15 当前条目和逐 ID 核对的 22 归档条目、6 视图可见字段 `9/9/5/3/7/3`、7 公开 workflow 与 S09 开工后快照一致。#33 仍 **S09／进行中／Todo／OPEN**，#32 为 **S08／待用户验收／Todo／OPEN**，#34—#37 待启用。[只读比较摘要](evidence/s09-rework/project-audit.json)。GitHub 当前项目列表仅返回 15 当前项，22 归档项按旧 ID 单独读取并比较，不能把 15 误报为完整 37 项。

本阶段医学模板和检查结论仅为演示结构，正式临床模板、设备/PACS 联机、审核签发、S10 结算/收退款、S12 长期原件生命周期和生产价策略尚未批准。S07/S08-C/S09 原生 SIGSEGV 根因均 UNKNOWN；生产部署维持 BLOCKED。完成交付评论并逐字读回后停止等待 GPT 独立复核；不关 Issue、不改 Project、不启 S10、不合并或部署。
