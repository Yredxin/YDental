# S10 Native SIGSEGV D0/D1：建库命令异常，持续 BLOCKED

## 1. 授权与固定身份

本批唯一授权为 [#34 GPT-AUTHORIZE 6160027673](https://github.com/Yredxin/YDental/issues/34#issuecomment-6160027673)，承接[技术裁定 6159493421](https://github.com/Yredxin/YDental/issues/34#issuecomment-6159493421)。已完整读取 #23/#34 正文及各自全部 3/16 条有效评论、#35 正文与 0 评论；核对授权之后没有新的 GPT 裁定或 Codex 交付。#34、#35 均 OPEN，S11 没有启用。原分支 `codex/s10-settlement-finance-r1-20261013` 本地/远端 HEAD 均 `f24b0302569aefaa394391da6b696d915e3f0616`，D0 开始时工作树干净；product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` 未更改。

本批只进行 D0 只读取证和条件 D1 一次 Native 捕获准备。未授权 S10 D2 产品、业务、Firefox、Project 修改或生产部署。S10、生产均持续 BLOCKED。

## 2. D0 原事故和旧事故对照

原事故库 `ydental_s10_test_20261014020300_8b6c1d4e` 仍为 OID **2056451**、PG cluster `7694897083368259627`、config SHA256 `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`；原端口18247、专属dbfilter、data_dir/filestore保留。PID2383730 原日志 SHA256 `f7795b360a80afc8fdfff8cd9c7e389da25064c36480bdb98bceccd9a2c0eef6`、事故 marker SHA256 `d1785e5f111f0c2358fce04895092b81f1c4455f3e0774f82b1646a447e48d78` 均重新逐字节匹配。PID2383730 是 SIGSEGV/signal11/exit-11；PID2383729 是守卫 SIGINT/signal2/exit-2。92 模块和 registry 已加载，崩溃在本次并发 actor 的出账操作之前；`field_computed`/`res.users.context_get` 只是 Python faulthandler 最后可见栈，不是 Native C 根因。

| 旧事故 | 只读原始材料 | 已知差别/限制 |
|---|---|---|
| S07 PID1048392 | `serve.log` SHA `5fc113a2524a4e383b895d8487164e71f917c2189b88ebcb380c9c85867a9e41` 匹配 | 专属预览阶段；旧报告仅见 `_PyObject_Calloc` 附近，无完整 C 栈 |
| S08-C PID1670701 | `upgrade` 日志 SHA `07e23e987e415a50255789fbe9721b1d10e8931977d77fe4761ec7b1819f6909` 匹配 | post-tests 资产生成后；内核指令在 `dict_dealloc` 附近，非完整 C 栈 |
| S09 PID1792405 | `probe` 日志 SHA `761e3cd6bfda2aef894fd7c413e532c28fcc853aa89b054452db4995b6132daf` 匹配 | registry/GC→contextlib 的 Python 栈，无 Native 栈 |
| S10 旧 PID1965906 | `probe` 日志 SHA `9c62be35195a765bacf11f57629dd67c6d6156f5591c1d42dd2bc8a3e2cb47ef` 匹配 | registry/GC→contextlib 的 Python 栈，无 Native 栈 |
| S10 本次 PID2383730 | 原日志和 marker SHA 如上 | registry 后首次 shell 上下文，尚无并发业务动作，无 Native 栈 |

这些事故的可见阶段、指令、OS 记录不同；是否同根因 **UNKNOWN**。

## 3. D0 环境、ABI、GDB 与权限

Ubuntu26.04.1/kernel7.0.0-38-generic、x86_64 Ryzen 7 7730U/4 vCPU。D0 时内存7.2GiB/可用5.5GiB、swap4GiB/空2.2GiB、根盘空19GiB；原 postgres:18 容器 shm256MiB、用约126MiB，容器健康；这些只是当前快照，事故时资源峰值 UNKNOWN。原常驻 Odoo PID42433、odoo-12 与 Docker volumes 未动。当前 shell `ulimit -c=0`，`core_pattern` 为 Apport pipe，未见事故 PID core；当前事故时段 kernel journal 无可用 C 栈。原真实 venv CPython3.12.15 ELF Build ID `7713d416ece8f53a2b37e61dd06defd7bf795954`、SHA256 `0886fb76ceec8ff568d23079b5da6342bb41675e216e11525d4d6a9e65988d10`，有 `.symtab`，无完整 CPython `.debug_info`。47 个 native `.so` 均有 Build ID，`ldd` 没有缺库；完整原始路径与哈希只在私有目录。

系统原无 GDB 且无免密 sudo。仅向权限700的私有`.local/s10-native-20261014-6160027673/`下载并解包 GDB17.1、所需4个运行库和与现有 glibc2.43-2ubuntu2.4 匹配的 `libc6-dbg`；系统安装/升级 **0**。GDB binary SHA256 `e5272927fc1b40345748dfa4133ec2a50caeb5f209a44099dd2c48679911c59c`，私有命令脚本 SHA256 `5990f5cf11906ec2f185320b709b114e3abd777b6c4745a34b61640301420950`。离线 `/bin/cat` stdin/cwd/目标环境测试 exit0；非 Odoo SIGUSR1 测试确实输出 `info inferiors`、线程、完整栈、共享库及目标信号终止信息，GDB wrapper exit255。正式脚本只捕获真实 SIGSEGV，未人为制造 SIGSEGV。Python 源码行级 debug 信息不足，原生函数名/模块 Build ID 与匹配 glibc 调试符号可用；没有真正事故 C backtrace 前，不作归因。

D0 GitHub 检查点 [#34 评论 6160238952](https://github.com/Yredxin/YDental/issues/34#issuecomment-6160238952) 已在新 Odoo 进程之前发布，API 逐字读回相等，正文 SHA256 `ca6adbb77475c21d2096a6a57f5767c96c07eb9a77d1f6c4e6740c7345e0826c`。其中固定两进程预算、准确 GDB/Odoo 命令、guard/超时/私有证据边界。

## 4. D1 实际执行及立即停止

D1 计划新库名 `ydental_s10_test_20261014033000_6160a273`，端口18248。首次且唯一执行的 D1 命令：

```bash
../.venv/bin/python .local/s10-native-20261014-6160027673/native_capture.py create
```

该非 Odoo 命令 **exit1**，在 `CREATE DATABASE` 处收到 `psycopg2.errors.ActiveSqlTransaction: CREATE DATABASE cannot run inside a transaction block`。保护脚本 SHA256 `e3de7c8781887bf98fc42bb44620c62938c4ee376c40ad0e63c7d20ea9168c66`，失败记录私有副本 SHA256 `350882707346ef739ad6679dab928ba1266aa055cb53de68c19923f731af4e76`。这是新诊断脚本的建库事务处理缺陷，**不是旧 Odoo SIGSEGV 的根因**。

按“命令执行本身异常即停止”授权，未修改脚本重试。新数据库 **未创建、无 OID**，无 config/marker/GDB/Odoo 日志；只留下权限700的新私有目录、filestore空目录与一份权限600的网络guard副本，全部保留。只读 PG 再查原库仍 OID2056451、同 cluster，原 config/log SHA 不变。D1 实际 Odoo 子进程 **0/2**，GDB 目标进程0，Firefox0，真实 Native C 栈 **未捕获**。原 SIGSEGV 根因继续 UNKNOWN。

## 5. 数据保全、越权检查与可证伪下一步

旧 S00—S10 数据库、日志、filestore、备份、core、Docker volume 不删不覆；原 Odoo20 core、odoo-12、venv/system Python 与生产不变。#34 Issue 不关闭，Project mutation0，S11不启动。原始诊断脚本、GDB/包、ABI 清单、D0 评论草稿和 D1 失败副本均在权限700私有目录，文件600；[脱敏机器索引](evidence/s10-native-d0-d1-blocked/diagnostic.json)不含凭据、患者数据或 Native 私有栈。

建议下一次独立复核若允许恢复：先离线修正诊断脚本的 psycopg2 autocommit/上下文边界，并用新的受保护数据库验证建库 guard；确认 GitHub 检查点和进程预算后，再另行授权一次 GDB 父进程窗口。此为可证伪建议，**本次未执行**。不能把 D0 GDB 功能测试或旧财务子路径称为本次 Native 捕获成功。S10 技术与生产继续 BLOCKED，等待 GPT 独立复核。
