# R3-W4 独立验收与收尾

状态：**独立验收及许可范围内收尾完成；未决责任保留**。W4 A/B/C 为新线程，主控协调业务操作和最终准出；共享主机不构成 OS 隔离。最终产品候选 `c50688ba806c69a624c3bf9b171b10ea164bfeec`，其真实浏览器完成及持久提交缺证，R3-BUG-001 OPEN，不能判定 R3 限定技术完成。

B 独立新物理 RO/RR 基线：所采 158 表共95056行、589附件与 W2 最末快照一致，SHA-256 `60656954aa568985806e1b9a367ddb9cd800fba221cdd7f9c27ee1856ce18197`。采集范围不包含全部敏感字段与未覆盖对象，不能据此补齐历史 UNKNOWN。账号正常停用、原生 tracking、待处理责任及提交后保护读回须按实际追加。

新 UID1565 为当前店541唯一有效店长；正常撤任需遵守原生替代规则，不以直接数据库字段或正常撤任之外的停用规避。新 doc520 pending/v2 责任归 UID1564，task917、execution560 verify 和 disposition59 待处理，不能因收尾自动清理。原19账号、旧时段、旧未完成责任受保护。

Context、Session、服务、scratch 及新身份处置按下列实际证据记录；未决责任不冒称已收尾。

A 对本轮初始化者1561及前台1562分别执行 UID5 正常离职的 MODEL 事务预演，flush／precommit 后 rollback、runner exit0，UID5 浏览器 Context CLOSED／进程 exit0。事务内分别出现各2条原生 tracking 消息、各自新讨论成员1670／1671被移除，会员与权限停用，4个 mutex 变化；未观察到时段／处置变化。日志 SHA 分别 `fc94a845916b7e6ea07772fefbeb691a76baf99d04c4cd94f000d4fa8893648b`、`6ebb5539e0134c55346e93d46c89a9355906e06ee805c41ef655a7241b97eb5b`。这是回滚预演，实际提交及独立读回另见下文。

B 独立外部前后对照：所采158表仅 UID5 登录新增3条审计，589附件及110讨论成员不变；6个可见序列推进、266个不可读，SHA `a37d2ac0e56bfbe2c67ab87a02742efb7f112b22983d00b16b6c38f247f123d9`。预演事务内各2条 tracking、相应新讨论成员移除，用户／员工／授权／会员失效，供给与待处理处置未见变化。仍须实际提交后的独立读回，不能以预演代替。

UID1561 已正常停用，B 独立提交后读回：员工1516／成员2550 inactive，4 grant none，原生 tracking 11129／11130，移除本轮讨论成员1670；所采158表仅预期变化、登录审计及4个 mutex，589附件一致，旧19 inactive、处置45–55／57／59 pending，doc520责任1564，active 工位租约0。对照 SHA `96d3c27d9c774fc775d31bd3c08876d23bd306af56f7604145ac08196a61bd45`，专项 SHA `4057046bdea7d40c22542c2519b50ef439f8d943a20ac5e4ecbe6451c257352d`。Session 是否失效 UNKNOWN。

UID1562 已通过真实网页单次正常离职 HTTP200，Context关闭；B 独立提交后读回 UID／员工1517／成员2551 inactive、frontdesk grant none、tracking 11131／11132，仅移除本轮讨论成员1671。589附件一致，158表仅预期离职／登录及4个 mutex 变化；旧19 inactive、处置45–55／57／59 pending，doc520责任1564。对照 SHA `566b47ab95699110c540b8715bd8551436c3bd5844454cfd82a0a8845d600850`，专项 SHA `d884df4c67a68ed68f83fe5b673649120e247e4f82a0c672f066dad155a272f4`；Session 失效 UNKNOWN。1561、1562 两次实际网页输出日志 SHA 均为 `bd7e91a7f576673418087d913edf2a0ca421656e00287839cbfaa49f26107534`，分别来自不同目标配置，不混为一次动作。

A 对本轮历史合成目标服务 PID3315345 单次发送 TERM，命令 exit0；原启动父进程已退出，服务进程最终退出码 UNKNOWN。进程／监听／连接状态由 B 另行核实。

B 独立读回 PID3315345 不存在、18601无监听、历史库无连接，SHA `61cd379922cfe49f139ce1fcd9e1f1ac27298b123aaf3a32d7da1ae787d22a5f`。服务此前为孤儿，实际进程退出码 UNKNOWN；TERM 命令 exit0 不等于进程退出码。

A 的资源检查未见 R3 脚本或该项目 Chromium 运行进程；列出的 `ydental-s13-scratch` 容器均为 exited，其中包含历史容器，不把这些历史资源都归于 R3，也不推断其退出码均为0。W3 本轮各次 scratch 测试的实际容器 stop 结果见 [W3](phase-W3.md)。

本轮 UID1563 已在 W2 正常离职；1561、1562 如上实际停用并独核。UID1564 仍 active 并承担 doc520 pending 责任；UID1565 仍 active 且是该店唯一有效店长，其正常撤任受替代规则限制。两者的后续责任／店长安排须用户决定，不能为收尾强行停用、改原有规则、恢复旧身份或清除待办。原19账号及新产生的待处理责任保留。各次正常关闭 Context 不等于其 Session 失效；原 hold Context 是否正常关闭、所有旧 Session 失效继续 UNKNOWN。

服务停止后 B 独立最终快照：所采158表95078行、589附件、108讨论成员和可见序列与1562提交后快照一致；266序列不可读。比较 SHA `63d9fac0c26e2af062af8b291d91382daacece4233e32f9560c6c2044f68fd30`，完整快照 SHA `35ceed0db0b529fa15b870a23d23d067683f1999c52cdddebed62a75501fafc7`。旧19账号 inactive、处置45–55／57／59 pending、slot1229–1240 suspended、无 active 工位租约。新账号私有 provider 保留在本机，属主 redxin、权限 0600，不进入仓库。

## 独立验收与结论

固定候选的 W3 MODEL／HTTP 与源代码证据均已核；正常完成真实浏览器与独立持久提交、完成来源的真实文书接手、医疗写权非负责人负例未验。R3 限定验收 **PARTIAL**，R3-BUG-001 **OPEN**；不能用候选外 W2 浏览器证据填补最终候选缺口。历史 BUG-002 的历史库升级 NOT_RUN，R1／R2 与 P12 PARTIAL，#37 保持 OPEN，P14 未授权。
