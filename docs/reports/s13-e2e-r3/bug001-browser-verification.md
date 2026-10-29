# R3-BUG-001 最终候选浏览器定向验收

日期：2026-10-29。工作包 `YD-S13-E2E-R3-BUG001-VERIFY / 1.0`。R3 报告起点 `6cbc6e3618dc584dd775b893ab254e937c8d80b0`；产品候选 `c50688ba806c69a624c3bf9b171b10ea164bfeec`。

**结论：V0 BLOCKED；V1、V2 未进入。R3-BUG-001 保持 OPEN，R3 整体 PARTIAL。** 尚无最终候选的真实普通岗位浏览器完成、真实治疗及独立已提交状态证据，不能标记 FIXED_VERIFIED。未登记新的产品 BUG。#37 保持 OPEN，P14 未获授权。

## V0：供给前置与隔离探针

本轮在新 PostgreSQL 隔离探针中核实数据库身份：数据库 `yd_r3v_probe`，OID `16384`，cluster system identifier `7701894029317693484`，网络模式 `none`。B 使用新的独立数据库连接核对身份。主控提取候选源码中的纯身份判定函数，以该真实身份及门店 1、541、542 调用均返回 False（exit 0）；B 以另一连接只读查询身份，exit 0。这是数据库身份与 SOURCE/PURE 判定，不是 Odoo 动态请求，也不证明真实供给可以建立。

固定候选的 [供给服务源码](../../../ydental_supply/models/ydental_supply_service.py) 将 `isolated_test` 准入限制于特定历史数据库名、OID、cluster 和门店，另需进程标志；本轮新探针身份不满足该条件。该限制不能通过伪造身份、供给替身或修改产品守卫绕过。源码中 demo 供给默认不可售；`published` 需要正式批准，既有 R3 报告记录正式政策未获本测试批准。故没有建立合格真实供给，不能将准备状态判为通过。

本轮没有创建测试账号，没有执行医生浏览器登录、患者接诊、治疗确认、正常结束或防重重发；没有 completed 来源文书可供 V2 验证。没有以源码推断、探针、MODEL、mock 或截图代替实际浏览器和持久提交。未取得的治疗、费用、耗材、文书权限及审计结果均为未测，而非通过或失败。

## 保全和资源

未使用或改变历史受保护业务对象与身份；原 19 个测试账号及 UID1561–1563 未重新启用，UID1564 和 UID1565 的既有责任保留。未对历史合成库执行模块升级，未恢复旧执行窗口，未重放历史治疗、库存、费用或文书动作。本轮没有账号需要停用；本轮唯一新资源为 `yd-r3v-guard-probe` 临时容器，`docker stop` exit 0；随后 `docker ps -a` 按名称查询无匹配。未启动 Odoo 或浏览器服务，未创建账号；没有本轮 Session。

原 [R3 总结](summary.md)、[验收矩阵](acceptance-matrix.md)、[缺陷登记](bug-register.md)、[W1](phase-W1.md)、[W2](phase-W2.md)、[W3](phase-W3.md)、[W4](phase-W4.md) 和 [证据索引](evidence-index.md) 保留原有事实及限制。W2 转派响应正文、旧 Session 失效和缺失历史前像等既有 UNKNOWN 不因本轮核查改变；E2E-BUG-002 仍 OPEN。历史候选的浏览器证据不能与最终候选的 MODEL／HTTP 证据拼接为本轮通过。

本阶段 A、B、C 为新建独立线程，B 另开数据库连接只读核验；共享同一主机，不声称 OS 隔离。V0 未准出，因此未启动 V1／V2 或建立其团队，相关验收均 NOT_RUN。
