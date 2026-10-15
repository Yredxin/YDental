# S10-E2E-W3 真实 QWeb 选择器与动作合同

授权：[#34 / 6185309077](https://github.com/Yredxin/YDental/issues/34#issuecomment-6185309077)。固定起点 `a17cf61fadd983aa83ed53c791e79713b83f0b58`。这是 CREATE 前的源码合同；离线模拟不等于真实页面通过。

每个动作之前，浏览器以独立角色 session、当前 CSRF、门店 revision 和 queue connection/lease/token 操作。`form.checkValidity()`、唯一可见/可用选择器和 POST 响应类别必须成立；若失败即 STOP，不等待条件不成立的元素。每个动作之后另开只读 PostgreSQL 连接核对费用、库存、原生账款、结算来源与 S01 审计；每个 POST 单独落 `browser-actions.jsonl`，每步只读前后态、私有截图 SHA 与结果落 `browser-events.jsonl`。303 还须有“操作已受理”一次性页面反馈，不能把拒绝 303 视作成功。截图只保留私有目录。

| # | 步骤 / 角色 | 前置及真实元素来源 | 路由、请求与期望 | 持久态合同 |
|---:|---|---|---|---|
| 1 | 预约 / 前台 | 合成患者、已发布护理映射及分钟对齐容量；`#intake-create form:first` 的 `operation/patient_id/mapping_id/start/end` 均有效 | `/ydental/intake` → `/ydental/intake/action` HTML POST 303 | 新增本患者唯一 pending 护理 task；SQL 核店、患者、映射 |
| 2 | 到店 / 前台 | 同一患者；`#intake-create form:nth(1)` 的 `patient_id` | intake → intake/action HTML POST 303 | 合法到店记录，费库款不动 |
| 3 | 护理报到 / 前台 | SQL task pending；队列 `#continuation-reception [data-pending-task=ID] form[data-queue-form=report]` 的隐藏 `task_id/version` 与 SQL 一致 | `/ydental/queue` JS → `/ydental/intake/action` JSON POST 200 | task accepted，唯一排队；费库款不动 |
| 4 | 医生接诊 / 医生 | 合格护理工位空闲；`button[data-operation=enter][data-station=ID]`、持有后 `call`、本 task 行 `tr[data-task=ID] button[data-operation=start]` 仅 calling 出现 | queue/action 三次 JSON POST 200；进入 clinical | 唯一 serving 与持有 lease，任务 ID 与本患者一致 |
| 5 | 独立草稿 / 医生 | 当前 serving；`#open-document`、`textarea[name=chief_complaint]` 解锁后 `#save-document` | `/ydental/clinical` → `/ydental/clinical/action` JSON POST 200 | 文书版本 >0、无费用 |
| 6 | 治疗600 / 医生 | 当前文书和 lease；`form[data-operation=execute]` 中 catalog、quantity、tooth、tooth_state、lot、material_quantity、reason 必填/有效 | `/ydental/treatment` → treatment/action JSON POST 200 | 唯一 confirmed 治疗 event/fee600、快照600、原生物料 done 出库1 |
| 7 | 检查医嘱 / 医生 | 治疗后同一 serving；`form[data-operation=order]` 选择 exam、准确 mapping/quantity/purpose；新 `article[data-order-kind=exam] form[data-operation=issue]` 只在 draft 显示 | treatment/action 两次 JSON POST 200 | issued order 与 `tr[data-line]`；SQL `line.ydental_task_id` 精确映射同患者/同店/检查能力 pending task。检查行没有 `.task-id` |
| 8 | 处方签发 / 医生 | 同一 serving；order 表单选择 prescription、药品 SKU、方向、数量6、specification/usage/frequency/course；draft 卡片 issue | treatment/action 两次 JSON POST 200 | issued line 和首段 `segment`；SQL 用 line→order→首段 task，核同店/同患者/药房映射。首段前不依赖页面历史 segment 文本猜 ID |
| 9 | 治疗交还 / 医生 | 文书锁合法；`#open-document` 后 `#handover-document`，再 `button[data-operation=exit]` | clinical/action JSON POST 200；queue/action JSON POST 200 | 护理 serving 结束、lease 释放；检查可报到，治疗费库不动 |
| 10 | 检查报到 / 前台 | 检查行 SQL task pending，原 serving 已解决；队列同任务 data-pending-task 和 report 隐藏 ID/version | queue → intake/action JSON POST 200 | 检查 accepted；若患者仍 serving，服务拒绝必须 STOP |
| 11 | 检查接诊 / 检查员 | 检查站具精确能力；enter/call 后本 task 行 calling/start | queue/action 三次 JSON POST 200；进入 exam | 本检查 task 唯一 serving，正确操作者/工位 |
| 12 | 检查80 / 检查员 | `section[data-line=ID]` 与医嘱行相符；draft findings、perform reason、confirm reason、finish reason 依结果状态逐次出现 | `/ydental/exam` → exam/action 四次 JSON POST 200 | 唯一 confirmed exam event/fee80/快照80；结果 confirmed；finish 后工位释放；无额外耗材 |
| 13 | 药房报到 / 前台 | 首段 SQL task pending、检查 serving 已结束；队列隐藏 ID/version | queue → intake/action JSON POST 200 | 首段 accepted，无自动占队 |
| 14 | 药房接诊 / 药师 | 药房工位与资格；enter/call 后本 task 行 calling/start | queue/action 三次 JSON POST 200；进入 treatment | 首段 serving，原处方和患者一致 |
| 15 | 实发4 / 药师 | `article[data-order=ID] form[data-operation=dispense]` 仅 pharmacy/issued line；真实药品 lot、quantity4、reason | treatment/action JSON POST 200 | fee40/快照单价10、药品原生 done 出库4、处方余2 |
| 16 | 结束首段 / 药师 | 同 issued 处方 `form[data-operation=finish]`、必填 reason；当前费用 confirmed | treatment/action JSON POST 200 | 首段 done、工位释放；SQL 唯一第二段 pending task，line→order→segment 链相符 |
| 17 | 余量报到 / 前台 | 第二段 task pending，不复用首段 ID；队列隐藏 ID/version | queue → intake/action JSON POST 200 | 第二段 accepted，无新费用 |
| 18 | 再接诊 / 药师 | 药房工位已释放；enter/call 后第二段 task 行 calling/start | queue/action 三次 JSON POST 200 | 第二段 serving |
| 19 | 实发2 / 药师 | 同 issued line dispense 表单、相同合法 lot、quantity2、reason | treatment/action JSON POST 200 | fee20/单价10、原生 done 出库2、处方余0 |
| 20 | 结束最终段 / 药师 | finish 表单、reason；所有 event confirmed | treatment/action JSON POST 200 | 处方/行 done、lease 释放、无第三段 |
| 21 | 出账740 / 经理 | 患者过滤页仅4个 fee checkbox，其 value 与四条 confirmed SQL fee ID 完全一致；discount=0 | `/ydental/settlement?patient_id=ID` → settlement/action HTML POST 303 + accepted 反馈 | 一张 posted740、4条独立 source→原生 invoice line，余额740 |
| 22 | 线下收500 / 经理 | 唯一原生 invoice checkbox 与 SQL ID 一致；amount500、cash、原生必填 `actual_utc` 与 proof | settlement/action HTML POST 303 + accepted 反馈 | 本店 cash payment500、原生 move posted、partial500、余额240 |
| 23 | 补收240 / 经理 | 同一 invoice ID、余额240；amount240、同一 cash 渠道、actual_utc/proof 必填 | settlement/action HTML POST 303 + accepted 反馈 | 第二笔 payment240、原生 partial240、余额0 |

`exam_order` 和 `prescription` 的 draft+issue、`examination` 的 draft+perform+confirm+finish 是一个业务步骤内多个独立 POST。任一子动作成功后后续子动作失败，也必须保留已提交事实并停止，不重跑同库或换库。队列 JS 报到实际发送 `/ydental/intake/action`；其它队列动作发送 `/ydental/queue/action`。治疗/检查动作经 JS `preventDefault`、浏览器 confirm、当前 revision/CSRF/connection 发 JSON；结算为原生 HTML form，拒绝也可能303，所以核一次性反馈。

固定源码条件：`ydental_intake/views/intake.xml`、`ydental_queue/views/ydental_queue_templates.xml` 与 `static/src/workspace/workspace.js`、`ydental_clinical/static/src/document/document.js`、`ydental_treatment/views/ydental_treatment_templates.xml` 与 `static/src/workbench/workbench.js`、`ydental_exam/views/ydental_exam_templates.xml` 与 `static/src/workbench/workbench.js`、`ydental_settlement/views/ydental_settlement_templates.xml` 与 controller。药品 SKU 审核关联由固定 `price()` helper 在发布药品目录价格时建立，W3 预备 shell 只核唯一关联，不重复发布。
