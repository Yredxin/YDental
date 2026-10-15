# S10-UI1 结算工作台回归：准备阶段 BLOCKED

**结论：BLOCKED。** 本批没有运行修改前的真实 HTTP/Firefox 表单提交，因此 HTML 导航到 JSON 的疑点仍为 `NOT_RUN`，不是已复现缺陷；产品文件修改为 0。S10 完整技术及生产继续 BLOCKED，旧 Native SIGSEGV 根因 UNKNOWN，S11 未启动。

## 授权、身份与先行检查

- 唯一执行授权：[#34 评论 6173692695](https://github.com/Yredxin/YDental/issues/34#issuecomment-6173692695)；后续 [交接 6181564664](https://github.com/Yredxin/YDental/issues/34#issuecomment-6181564664) 为 NO-NEW-AUTH。API GET 取得 #23/#29/#31/#34 当前正文及全部 3/7/8/110 条评论；#35 OPEN/0。授权后未发现 UI1 开工/交付或替代授权。
- 固定原分支、本地/远端起点 `d766b70b0a9c922c809248cdc87e76efa8d5bc23`，开工时工作树干净。Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；历史 S10 product/test 提交、现行 S10 service blob `d4d4363ab2dfdd982606f464e5b66c240744fac6` 与 S07 service SHA256 `df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b` 均匹配。
- 预检前离线 Python 编译、XML 解析和表单映射为 `SIMULATED PASS`：13 个普通 POST 表单覆盖 14 个操作，审批/驳回共用一表单。纯模板 OID2100080、92 模块、业务表空、0 活动连接。强制 [预检 6181951592](https://github.com/Yredxin/YDental/issues/34#issuecomment-6181951592)在 CREATE/Odoo/Firefox/产品修改前发表，API GET 逐字读回 SHA256 `cbd2d4faf51a83f59d48c5e3165064bdc5d53d2985d12accf0187bff40bbd377`。

## 本批实际动作与停止原因

仅一次 `CREATE DATABASE`，从模板克隆全新私有合成库 `ydental_s10_test_20261015011000_a91c4d70` / OID2100227 / 同 cluster `7694897083368259627` / HTTP 预定端口18269。模板 filestore 的124个文件逐项校验后复制到新库独立 data_dir；原模板未写。随后唯一 Odoo 进程1为 `odoo-bin shell -c <新库配置> --no-http`，PID3160616，exit1，signal11=false。尚未启动 HTTP 或 Firefox，未触发本批升级。

准备脚本在 Settings 管理员显式配置批准的全局原生组并创建合成场景时，走到首个预约容量调用。已安装 `ydental_settlement_test` 的合成适配器 `pre_init_hook` 对新库 marker 强制校验 `core` 字段；本批专属控制脚本写出的 marker 缺少该字段，于是抛出 `AccessError: S10 synthetic adapter database identity changed.`。这是**本批合成测试夹具身份标记缺陷**，不是已经证明 S10 产品失败，也不是 Native SIGSEGV。失败发生在 `fixture` 业务 COMMIT 前；Odoo shell 的未提交准备事务随进程结束回滚。原准备日志只保留在权限700私有目录，不上传原文。

预检已将命令/身份异常列为 STOP 条件，故没有修 marker 后重跑、没有使用第二座库或第二个 Odoo 进程。新失败库及私有目录保留。只读复核新库 `ydental_access_store`、`ydental_patient`、`ydental_treatment_fee`、settlement payment/refund/close/receipt、`account_move`、`account_payment`、`ydental_access_audit`、`mail_mail` 均为0。`bus_bus=6` 与纯模板的6相同；`mail_message=851` 与模板851相同，不能把继承的内部行数归因为本批业务副作用。新库无其他活动连接。

## 用量与验收状态

|项目|实际|判定|
|---|---:|---|
|新库 CREATE / 上限1|1 / OID2100227|完成，保全|
|Odoo 顺序进程 / 上限4|1；exit1，signal11=false|准备失败，停止|
|Firefox/Playwright 进程 / 上限1|0|NOT_RUN|
|明确业务 COMMIT / 上限12|0|NOT_RUN；准备事务已回滚|
|`-u ydental_settlement` / 上限1|0|NOT_RUN|
|修改前 HTML 表单真实点击与导航|0|NOT_RUN；JSON 疑点仍未复现|
|修改后工作台、连续收退款/日结、JSON API兼容|0|NOT_RUN；无产品 patch|
|权限/CSRF/revision/跨店/同 key Web 负向|0|NOT_RUN|
|大于50条 HTTP 分页|0|NOT_RUN|
|三类中文 PDF HTTP 下载与视觉、无权直链|0|NOT_RUN|
|静态 Python/XML/表单映射|完成|仅 SIMULATED PASS|

本批没有原生 posted invoice/payment/refund/close 增量、幂等 receipt 或 S01 业务审计；不能用旧 FC2 的财务 PASS 代替 UI1 Web 验收。旧事故 OID2056451、模板2100080、C1 2100125/2100126/2100176、FC1 2100197、FC2 2100212 在停止后均只读核实存在；全部历史库、filestore、日志、core、volume、备份及新失败库不清理。本批不使用 sudo，不开展基础设施专项，不改变 Project/Issue 状态、不合并/部署/启动 S11。

## 交付文件与后续边界

本提交只保存本批专属、**尚未执行到浏览器阶段**的控制/准备/浏览器脚本、本报告与[脱敏机器索引](evidence/s10-ui1-blocked/verification.json)。控制脚本保留当时实际失败的 marker 写法，供独立复核取证；**不得在当前授权下直接重试**。若 GPT 后续单独授权恢复，需要先离线修正 marker 的 `core` 字段并重新给出数据库/进程/COMMIT 预算与唯一新库身份；当前库不重建或复用以掩盖失败。
