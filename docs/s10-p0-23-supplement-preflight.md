# [CODEX] S10-P0-23 增量FILE_ONLY冻结：保留首次严格JSON失败，分层核对保存字节

沿唯一授权6230563750和已读回预检6230625715，不重复开工、不改旧文件/初始核验器、不放宽JSON有效性判据。首次核验器实际exit1：47项原字节均匹配旧manifest/冻结输入，随后严格解析报告JSONDecodeError Invalid control character，line1321326/column25/character40931612。按冻结循环，首个快照为`.local/s10-p0-22/r0-A-fresh-owner-scope-1-intent-before.json`；其sha=f38465a6f3aeba069cde55711bb4f4bafb230868628705a6f9221dcffcd9acb6。错误尚不能据此归因原文件、解码或解析过程。首次stdout/stderr/exit原字节私有保留，未重跑首次核验器，旧P022 FAIL不改。公开initial-run-result.json记录真实exit1及完整无秘密的调用栈。

本增量仅为完成已授权文件分层检查。固定提交`951348cbf430db69f5e813d09ee34f3c178d55cf`（正常线性推送）：新增scripts/s10_p0_23_diagnose.py，SHA256 **e426c4c649669b8381a313c8b9734cf94172badf700ab9c3bbe87fda5c012c90**；supplement-freeze.json SHA256 **e4d308f6d1b7ef0fe2c3deec96b6b3a9b0ffa09cd38b6a5f20522e8b7f6ce529**。原47输入清单SHA仍42f6033edb2a547db7980b0e47560266ec39fe56cbdabda93ce49c9d6122a3e4；初始核验器SHA仍5c89930fff75dc972f83b355c4c4befb5855d4d9f92ff7fa8e24a63c6a5dfbce。

新脚本先核以上冻结和输入SHA，再分别记录整文件严格JSON解析结果；从旧pretty-print的唯一tables/ir_ui_view边界定位原字节中的数组，独立严格解析该数组，核目标唯一/行和字段/原token。如果整数组严格失败，仅对词法分隔出的行片段逐项严格解析，记录每个失败，单独核严格有效的929行及原字节格式中的唯一id/key；明确此时不能宣称整文件/整数组有效，不能跳过坏行重算表签名，也不使用strict=False或修补原字节。若目标自身不能证明，保留BLOCKED，不捏造目标全文。

只对固定core模板完整字面/属性结构核同并确认异常仅一字符的目标值，才输出三份全文、UTF8 hex和各保存副本字段/整行比较。原始字节和整文件错误、数组错误、目标行有效性分别标明。新增两组独立纯文件进程，以已有`python3`和`../.venv/bin/python`各一次执行同一诊断器，分别写本批diagnostic-system/diagnostic-fixed目录，用于比较相同保存字节在不同现存解析入口的结果；不是数据库测量、环境专项或运行修复。不得因第二入口成功删除首次失败。

两组都可仅AST抽取初始P023核验器的小型纯文件helper和P022纯比较/保存helper，运行原预定11项合成正反例；不导入旧模块、capture/readonly/native或fixture main。额外结果仅本批新路径，原始全库/其他行不公开。逐次保存实际退出码、输出和最终交叉比较；发现错误如实列明，不修改冻结脚本后原路径重试。

本条REST GET逐字相等保存后依次运行：`PYTHONDONTWRITEBYTECODE=1 python3 scripts/s10_p0_23_diagnose.py diagnostic-system`；`PYTHONDONTWRITEBYTECODE=1 ../.venv/bin/python scripts/s10_p0_23_diagnose.py diagnostic-fixed`。两次都只读旧文件、只写新P023目录。数据库连接/SELECT/CREATE/DML/Odoo/业务HTTP-RPC/浏览器/PDF/scope/文书/收退款/日结/安装升级/权限变更/产品core修改/sudo/OS-PG-Docker-网络-硬件专项全部0。GitHub流程API和评论除外，Issue/Project状态0修改。

不把任何文件解析结果解释为数据库无损、根因已修或可恢复业务。A仍BLOCKED、B/C/D/E仍NOT_RUN、S10整体BLOCKED。本增量不是新运行授权；最终交付并REST逐字读回后STOP，不自动五组/P024/S11/合并部署。
