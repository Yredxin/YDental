# S10-P0-01 历史退款与日结 Web 分页：预检阻断

状态：`BLOCKED_PREFLIGHT_INSTALLED_QWEB_DRIFT`。唯一授权为 [#34 评论 6190937428](https://github.com/Yredxin/YDental/issues/34#issuecomment-6190937428)；[预检回执 6191071835](https://github.com/Yredxin/YDental/issues/34#issuecomment-6191071835) 已通过 GitHub API 逐字读回。本批没有创建数据库、启动 Odoo HTTP 或 Firefox，也没有发出业务 POST。

## 固定身份与只读发现

原分支 `codex/s10-settlement-finance-r1-20261013` 从固定 `eb8d195580841a4c5d6b91b4e2c637b57898860f` 前进；开工时本地及远端相同、工作树干净。Odoo20 core 为 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。已读取 #23、#34 当前正文及其 3/173 条有效评论；#34 在本批前最后评论即正式授权。#35 为 OPEN、0 评论。

R3 唯一候选源库为 `ydental_s10_test_20261014020300_8b6c1d4e`，现场 OID **2056451**、PG cluster **7694897083368259627**，与原 marker 一致。原 config SHA256 为 `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`，marker SHA256 为 `96d261798a4b4370772d5700ba8516dd7677d2568f2b3fda80d3572b94a644e6`；filestore 有 184 文件，清单 SHA256 为 `b325817771a580474b632108ea11f373b319567626c5d434e72a047bc556b549`。`ydental_settlement` 和其测试模块均为 installed。

在无患者筛选、门店 1 的实际服务域下，退款共 **63** 条，按 `id desc` 分页 50 条，第 2 页含 requested 退款 **ID 14**，申请人用户 5，金额 1，原生退款付款和贷项字段均为空。日结共 **55** 条，第 2 页含 confirmed 日结 **ID 9**，且是该收费员/业务日/渠道的最新周期，原收/实退/在途快照均为 0。用户 6 在门店 1 具 `settlement=write`、`finance_approval=write`，与退款申请人不同；用户 10 无对应授权，用户 14 的本批相关授权在门店 3。以上仅为 `HISTORICAL_R3_MODEL_EVIDENCE`，不代表实际 Web 页面已渲染或旧对象已操作。

## 硬停止原因

R3 安装态 `ir.ui.view` 的 `ydental_settlement.ydental_settlement_tokens` SHA256 为 `7160c6c9d525cc4c7790079a944baa052a25bd488b23cbd77db90ad69b4cf0bc`；它包含 CSRF、revision 和 key，**缺少 `output=html`**。安装态主页面通过该模板生成驳回和解锁表单，并有第 2 页链接。当前源文件已有 `output=html`；当前控制器只有收到这个字段才以 303 跳转回工作台并显示结果，否则返回 JSON。代码差异来自 R3 之后的 UI1 R2 变更 `c2a26ee`；禁止的模块升级会是更新旧安装视图的通常途径。

只读预检脚本以安装态 token 构造 Fake DOM 表单字段，经当前控制器路由条件离线模拟，得到 `EXPECTED_FAIL_HTML_CONTRACT`：原生表单提交会走 JSON 响应分支。授权要求安装态 QWeb 与现行路由一致，且以真正 HTML 按钮完成可核验操作；该门槛未通过。没有通过手工补字段、安装升级或改产品绕开门槛。完整正例和其余负例因硬停止为 `NOT_RUN`，不能称 `SIMULATED_PASS`。

## 执行与证据边界

| 证据层级 | 结果 |
|---|---|
| `HISTORICAL_R3_MODEL_EVIDENCE` | 来源身份、安装态、门店内第 2 页候选与角色只读核对；详见 [脱敏预检 JSON](evidence/s10-p0-01/preflight.json) |
| `SIMULATED_PASS` | 无；离线合同模拟为预期失败 |
| `NEW_REAL_WEB_PAGE2` | `NOT_RUN` |
| `NEW_HTML_ACTION` | `NOT_RUN` |
| `NEW_NATIVE_READONLY_AUDIT` | 仅源库只读签名；新库未创建 |

复现命令：`/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python scripts/s10_p0_01_preflight.py`，退出码 0，输出阻断状态。脚本 SHA256 `b59b9d2933ebec7035d37607b305703096dbdb1d53e4b8e52c3dd5530b5a5270`；JSON SHA256 `8c8a5c4bc733e6802f75f6689c61fe8fc4630310f05b6a8646f86b4b40816bc9`。JSON 含来源业务表逐行摘要，不提交账号凭据、日志原件或患者数据。

预算实耗：CREATE **0/1**、Odoo HTTP **0/1**、Firefox **0/1**、Odoo shell **0**、退款驳回 **0/1**、日结解锁 **0/1**、无权请求 **0/2**，资金/库存/出账新动作 **0**。没有选择目标库名、端口或 HTTP/browser argv。原库及所有历史库、filestore、marker、事故日志保全。#34 保持 OPEN，#35 未启动，Project 零修改；S10 全阶段技术与生产继续 BLOCKED，等待 GPT 独立复核并另发新授权。
