# S10 原生事故 D0/D1 有界诊断及持续阻断

依据 [#34 GPT-REVIEW/AUTHORIZE 6146845983](https://github.com/Yredxin/YDental/issues/34#issuecomment-6146845983)，沿原分支及固定失败 final `87bad3b14a67a70ded6215cd9f3c324a30037936`。D0 回执 [6146948301](https://github.com/Yredxin/YDental/issues/34#issuecomment-6146948301)先发布并逐字读回，随后才进入 D1。原 product/test/final 提交及事故库、日志不改写。

## D0 只读取证

原事故库 `ydental_s10_test_20261013125916_2b3e556e` 的 OID 1598603 和 PG cluster 7694897083368259627 现场读回相同。原 PID1965906 已退出；原始探针日志 SHA256 `9c62be...cb47ef` 与源 SHA256 `eb4a22...22441766ac` 均匹配。13:20:11 的 Python faulthandler 显示 GC、`contextlib.__exit__` 和 `Registry.new`；业务脚本尚未执行。原 runner exit139/SIGSEGV。原 core soft limit 0、apport pipe；无可用 core/native 栈，根因 UNKNOWN。普通账户 `journalctl -k` 在事故窗口没有条目，`sudo -n` 不能访问内核日志；可读 syslog/kern.log 也没有 PID1965906 对应行，不能据此否定 signal11。

项目 CPython 3.12.15 ELF Build ID `7713d416ece8f53a2b37e61dd06defd7bf795954`，Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。原 faulthandler 列17个 native 扩展；已核对 venv 元数据与关键 `.so` 哈希，未将最后 Python 帧或旧 S07/S08-C/S09 事故误判为根因。当前 PG `/dev/shm` 256MiB、约163MiB可用，宿主内存 available 约5.9GB、盘约21GB；这是 D0 时点资源，不能证明事故时状态。原 132 座合成库保留。

## D1 两次额度和真实结果

先行创建新隔离合成库 `ydental_s10_test_20261013134700_d10a5e72`，OID1620922，原 cluster，专属端口18211，配置 SHA256 `123dd939503d37113ad85e83fe1d345b9d95400349a7f2a33853657ce08a2389`，独立 data_dir/dbfilter/filestore 和进程本地禁外发 guard。原库 OID 1598603 未变。首次外层创建脚本因 `CREATE DATABASE` 落在事务内 exit1，没有创建数据库；失败目录 `ydental_s10_test_20261013134500_d10a5e71` 保留，修正脚本后才创建上述唯一 D1 库。原始私有配置和日志留在 `.local/`，公开仅脱敏摘要。

| 次数 | PID | 命令目的 | 退出 | 结果 |
|---|---:|---|---:|---|
| 1 | 1980614 | 固定旧候选安装及上游/原生依赖，`PYTHONFAULTHANDLER=1` | 255 | `ydental_treatment_test` 的 pre-init guard 要求 S08-B 命名库，拒绝 S10 诊断库；未安装 S10。日志 SHA256 `94c23b42e7ef830eb75b121553f08a02c3635b6d7bf6021f16e03d5e1b4df53a`。 |
| 2 | 1982238 | `shell --no-http`，拟完成候选安装并读取上游事件 | 1 | registry 成功加载92模块，但诊断 stdin 首行 `from odoo import api, registry` 抛 ImportError；候选安装及业务入口没有执行。日志 SHA256 `aa06546e7744270a5ae3602cfb8ed93fc0056a8a5f34810975d5f30a79213287`。 |

两次无 signal11，仅表示**此有界窗口未复现**；两次均未完成计划的候选安装与 shell 业务入口，不能判定 D1 安全恢复。两次 Odoo 额度已耗尽，停止所有 Odoo/Firefox 调用，不再以换配置方式重试。D1 库只读 SQL：`account/sale/purchase/stock` installed，`ydental_settlement/ydental_treatment_test` uninstalled；治疗 event、原生 payment 和 partial reconcile 均0。当前合成库133座，两个诊断 PID 均退出，没有删库/卷。

## 后续边界

D2 **未启动**。没有新 rework product/test/final 三提交；F1—F6、T01—T16、真实740和270+200、退款100、跨法人T09、安装升级/带业务再升级、并发、Firefox、PDF、财务SQL均 NOT_RUN/BLOCKED。原候选的 pending 看板、退款撤销、跨法人交易硬缺口仍在。Project 0 mutation，#34保持 OPEN，生产继续 BLOCKED。需要 GPT 对本次诊断脚本的两个失败、额度耗尽和下一次安全诊断窗口作独立复核及新授权；不能凭未复现就继续 D2 或声称技术 PASS。

机器可读证据为 [diagnostic.json](evidence/s10-d1-blocked/diagnostic.json)。全部原始私有日志、配置和 guard marker 留在 `.local/ydental_s10_test_20261013134700_d10a5e72/`，原事故库及历史证据保留。
