# S10 Native D1.7-L2：最小费库准备阻断

## 1. 授权与固定身份

唯一授权为 [#34 评论 6163322228](https://github.com/Yredxin/YDental/issues/34#issuecomment-6163322228)。原分支 `codex/s10-settlement-finance-r1-20261013` 从 `72234f43428fa6ac576c5d6e81c6484075ae06b0` 前进；固定 S10 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7` 和 Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` 未修改。执行前 API GET 已读取 #23、#34 正文及全部有效评论、最新授权与 #35；远端 HEAD、origin、干净工作树、venv、PG endpoint `127.0.0.1:5432` 和 cluster `7694897083368259627` 匹配。#35 仍 OPEN、0 评论。

本轮仅授权一次纯92模块克隆、最多一个 GDB/Odoo 准备目标和条件式两个只读 GDB/Odoo 目标。结算、会计出账、收退款、日结、完整业务回归、Firefox、安装/升级均不在授权范围。

## 2. D1.7-0 离线预检和强制检查点

原事故 OID2056451、纯92模板 OID2100080、L1 OID2100086 及其它历史 OID 不变。OID2100080 再次独立只读核查为 92 个精确 installed 模块、16 类业务表为0、70个系统附件/124个安装文件、0 活动模板连接；模块清单 SHA `c1bbaa9395bd01d9e11912d56b73155d2b6cd63d3fbf1f58de0404d58e66b8a0`，filestore 清单 SHA `e059eae26ea543e3f73111706466e4081df3c0478332f7761f7eaa6c646bc93b`。事故日志 SHA `f7795b360a80afc8fdfff8cd9c7e389da25064c36480bdb98bceccd9a2c0eef6`、事故 marker SHA `d1785e5f111f0c2358fce04895092b81f1c4455f3e0774f82b1646a447e48d78` 保持。

从 `scripts/s10_completion/concurrency_prepare.py`、`ydental_treatment_test/tests/common.py`、`treatment_common.py` 及实际 S01/S03/S05/S06/S07/S08 服务提取最小图：原生公司、一个合成门店、三位合成职员、一处工位/供给、一个患者、一项真实治疗和 100 元演示价、一次材料 receipt 与一次治疗 issue。准备脚本仅用既有 ORM 服务创建临床/库存/fee；未安装受独立 pre-init guard 保护的 `ydental_treatment_test`，未调用 settlement bill/pay/refund/close。预期两笔原生 `stock.move`，`account.move/payment/partial` 必须为0。Odoo20 该实例虽有 `stock_account` installed，却没有旧版本 `stock_valuation_layer` 表；事前真实 schema 查询识别这一差异，删除了错误的审计断言，未修改产品。

私有诊断工具在权限700目录 `.local/s10-native-20261014-6163322228-d17l2/`，文件600。`py_compile` exit0；AST/假连接/guard/PG白名单/GDB命令模拟 15 正例、26 负例 exit0，全部标 `SIMULATED`；原 `ydental_settlement_test.pre_init_hook` 的**实际未修改函数体**在隔离 stub 中正例1、负例12 exit0，源码 SHA `cb90e4a300486066049677d4b1cf0b98ac4fb3052e5d59a6646403d147d3cbcd`。GDB17.1 binary SHA `e5272927fc1b40345748dfa4133ec2a50caeb5f209a44099dd2c48679911c59c`；CPython Build ID `7713d416ece8f53a2b37e61dd06defd7bf795954`，glibc Build ID `066527e430a32768d82741e00b81eebb1a872294` 有匹配私有 debug 文件。CPython 完整 debug_info 和部分 native 扩展符号仍缺。

原 D0 native 扩展清单的47个 `.so` 于本轮重新逐SHA核对47/47匹配，原清单SHA `67c45d446e3a28348186d50f890e334d9de93adf49c2662c2396a5c1a4e34d13`；其中37个有、10个缺完整 debug_info（沿用 D1.6 的只读符号盘点）。哈希相同不能证明原事故瞬间的加载顺序或内存状态相同。

[检查点一 #34/6163799490](https://github.com/Yredxin/YDental/issues/34#issuecomment-6163799490)在 CREATE 和 Odoo 前发表，GET 逐字读回相同，评论体 SHA `0bc198e9b39d7a693c7cf364e5e473a3aa09594bd77667dd0bffc1320cb5a9b8`。检查点中预先列明了准确 CREATE、GDB/Odoo 命令、业务图、负向边界和配额。

## 3. D1.7-A 唯一 CREATE 与准备目标

唯一 CREATE 命令：

```text
cd /home/redxin/code/odoo/odoo-sd/code/sd-addons && ../.venv/bin/python .local/s10-native-20261014-6163322228-d17l2/l2_capture.py clone
```

exit0，一次 `CREATE DATABASE ... WITH TEMPLATE ...`；独立 postgres 管理连接在任何 SQL 前设置 autocommit，事务 IDLE，目标及模板都用 `psycopg2.sql.Identifier`。新库 `ydental_s10_test_20261014074928_875c1c23` / **OID2100087** / 原 cluster / 专属端口18254，配置 SHA `55776e99530ff459343db3cf0614b949323bc69c9fbaa665c9ad07ffb536350c`，marker SHA `86566fb5084998684e6d0638caa250f9af01ad009a6b075dd63935ee54eb26bd`，专属目录700、配置和 marker 600；124个安全模板安装文件逐SHA复制，严格 dbfilter、loopback Python guard、SMTP `127.0.0.1:1`、cron0。CREATE 后独立只读 OID/cluster/92模块/空业务核验 exit0；实际新 marker 上未修改 hook 函数体 stub 再验证 exit0。原模板及事故库 OID 和 SHA 未变。

唯一 A 命令：

```text
cd /home/redxin/code/odoo/odoo-sd/code/sd-addons && ../.venv/bin/python .local/s10-native-20261014-6163322228-d17l2/l2_capture.py prep
```

包装器 exit**2**；其 GDB 父 PID **2585093**、唯一 Odoo 目标 PID **2585100**。GDB `--batch --return-child-result` 实际 exit**1**，目标 `exited with code 01`，**signal11=0**；registry 从 `2026-10-14 08:04:56,199` 到 `08:04:56,897` UTC 加载92模块。A 日志 SHA `2961e7042afd54125f5c1839f411bf69dc3e60fd25a7c0de549bd10507a9e666`，结果 SHA `ab77c7dabe0ef47de01cddfcdaa305977bfaa29020ab3443f205180b50a5a886`。一次性准备 ledger 已写入，未复用、未重试。

真实失败链：`ydental.inventory.service._setup` 调用原生 `stock.warehouse.create`；Odoo20 `stock_warehouse.py` 的多仓库配置转入 `res.config.settings.execute`，再到 `product` 设置执行 `product.pricelist.action_archive()`；现有 `ydental_intake/models/native.py` 的受控价目表写入 guard 抛出 `AccessError: Native service data must use the controlled catalog or price action.` 这是**合法库存初始化与现有保护交互导致的诊断准备失败**，不是 SIGSEGV 根因。此前已经在同一未提交事务中创建一些 S01/供给/价格合成对象；异常使 ORM 事务回滚。没有修改产品或 guard，也没有重跑。

## 4. 停止后的独立只读保全核验

第一次独立核验命令是 `../.venv/bin/python - <<'PY'` 下的只读 psycopg2 聚合；因原断言要求克隆 filestore 完全不增加，实际发现6个新增文件而 exit**1**。保留该真实失败，不把它伪称 PASS。第二次仅调整**只读核验判据**，记录源/新库54张相关表记录数差异为 `{}`、92模块清单哈希相同、患者/治疗事件/confirmed fee/stock.move/quant、原生会计/支付/核销、结算四表及邮件队列仍为0；PG目标连接0。模板124个 filestore 文件 SHA 全相同，新库另有6个运行时文件，均未被新库 `ir_attachment.store_fname` 引用；**文件具体生成链 UNKNOWN**，原样留存，不清理。第二次只读核验 exit0，私有结果 SHA `8e238fabf51e44b12d441272a27383516556dc056e9147be19bad1b247a3d077`。同数量比较不等于每行字节级相等；但无目标 L2 业务事实被提交。旧模板重审 exit0、70附件/124文件与原 SHA 相同，所有固定历史OID及原崩溃日志/marker/config SHA 匹配。GDB/目标精确PID已经退出。

## 5. 配额、Native证据和裁定

| 项目 | 实际 | 上限 |
|---|---:|---:|
| CREATE | 1 | 1 |
| A准备 Odoo目标 | 1 | 1 |
| B双GDB只读 Odoo目标 | **0 / NOT_RUN** | 条件式2 |
| Odoo目标总数 | 1 | 3 |
| Firefox / 安装升级 / 财务业务actor | 0 | 0 |
| Project mutation / Issue状态修改 | 0 | 0 |

A 非正常退出，第二GitHub放行检查点**未发布**，B 窗口**未启动**；因此无双 PID/PG backend、registry 重叠、PG观察器真实样本、C backtrace或新 Native 信号。不能称 L2 未复现、不能称 Native 修复。旧 PID2383730 SIGSEGV 的 Native 根因仍 **UNKNOWN**。S10技术与生产继续 **BLOCKED**，#34 保持 OPEN，#35未启用，不启动S11。

下一次有信息增益的工作应先在独立授权下静态追踪上述原生多仓库设置与受控价目表写入的合法衔接，提出**不绕过保护**的最小夹具路径及负向验证；若不能合法构建 L2，即停止此假设。不得在本失败库补键/重试、重新克隆或自动进行L3。原始 GDB/配置/凭据/attempt ledger/孤立文件仅在私有 `.local/ydental_s10_test_20261014074928_875c1c23/` 和 `.local/s10-native-20261014-6163322228-d17l2/` 权限700/600保存。公开机器证据仅给出脱敏计数、SHA与状态。历史数据库、filestore、Docker volume、core、日志和备份未删除或覆盖；未改 S10 产品、固定runner、测试插件 hook、Odoo20 core、odoo-12或venv，未合并、强推或部署。

## 6. 真实命令与退出码索引

| 命令或调用 | 结果 |
|---|---|
| `gh api --method GET repos/Yredxin/YDental/issues/{23,34,35}`、`.../issues/34/comments --paginate`、授权评论 GET；`git ls-remote origin refs/heads/codex/s10-settlement-finance-r1-20261013` | 均 exit0；最新授权仍6163322228，HEAD一致 |
| `../.venv/bin/python .local/s10-native-20261014-6163322228-d17l2/audit_source.py` | CREATE前、A失败后各 exit0 |
| `../.venv/bin/python -m py_compile .local/s10-native-20261014-6163322228-d17l2/*.py` | exit0 |
| `../.venv/bin/python .local/s10-native-20261014-6163322228-d17l2/offline_tests.py` | exit0；仅SIMULATED |
| `../.venv/bin/python .local/s10-native-20261014-6163322228-d17l2/hook_verify.py offline` | exit0；实际hook函数体stub |
| `gh api --method POST repos/Yredxin/YDental/issues/34/comments --input <私有检查点请求JSON>`，随后 `gh api --method GET repos/Yredxin/YDental/issues/comments/6163799490` | 各exit0，正文逐字相同 |
| `../.venv/bin/python .local/s10-native-20261014-6163322228-d17l2/l2_capture.py clone` | exit0；唯一CREATE |
| `../.venv/bin/python .local/s10-native-20261014-6163322228-d17l2/hook_verify.py real-marker`；独立只读 `l2_capture.target()` | 均exit0 |
| `../.venv/bin/python .local/s10-native-20261014-6163322228-d17l2/l2_capture.py prep` | **exit2**，GDB exit1、Odoo code01、signal11=0 |
| 独立 `../.venv/bin/python - <<'PY'` psycopg2只读54表/filestore核验 | 首次错误断言exit1；记录6新文件后第二次exit0 |
| `readelf -n ../.venv/bin/python`、`sha256sum`、原47 `.so` 逐SHA读取 | exit0；无依赖修改 |

`l2_capture.py window`、第二检查点、Firefox、任何额外Odoo或CREATE命令均 **NOT_RUN**。
