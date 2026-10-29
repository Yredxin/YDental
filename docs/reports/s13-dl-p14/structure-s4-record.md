# P14 结构性布局：S4 C 独立失败、保护与资源记录

2026-10-29，未参与产品实现的本角色仅审查现有文件并执行只读进程/容器检查，没有启动服务、连接数据库、提交业务或修改产品。固定候选 `34f7681797f4ad4aec0b3aa7201b9bf9d02761d8` 的本工作包结论为 **PARTIAL，焦点项 FAIL**。

## 失败与工具错误

- 独立读当前 `.local/p14-structure/s2-a/results.json`：静态变换旧 QWeb 的简化夹具，真实 Chromium 30组合中14组合至少有表内横向轮廓裁切；不是候选实际 loaded QWeb 或真实岗位。当前文件 SHA256 为 `e28e154ab47c53db8c1b32bc67d5d60d5950b848390058d48a87748bf58f5343`。此前 [S2 记录](structure-s2.md) 写同路径 SHA `534e962fb766697b9d80c42a46ecb58501d3aab27683de32c0c0fc75c7d9a970`；该报告记录及当前文件均保留，不覆盖。`check.cjs` 在每条 case 后及最终汇总时都会重写 `results.json`，当前文件 mtime 06:18:15、S2 报告 mtime 06:19:20（机器本地记录）；仅凭当前文件与这两个时间无法确定此前 SHA 的来源或内容是否不同，**哈希差异原因 UNKNOWN**。当前文件中的层级和14/30裁切可独立读到；不以旧 SHA 反签当前文件。
- 独立读取 `.local/p14-structure/s3-b/real-focus.json`：实际普通写岗位 Chromium、JS on、9组合有3个新办理锚点焦点裁切，文件 SHA256 `90af393e98d96f82ffe5e26a8a4c146e0776de103542319eb5b7234b09864112`；这是真实候选页面上的限定 FAIL。表外控件的独立记录 `.local/p14-structure/s3-b/real-focus-controls.json` SHA256 `5999436f8a1589b1431fe15fe4089d80fd8bf7a41fe9cbd7d42bb3ae3e8ffb29`。真实岗位 WebKit、JS off、PDF 及完整五视口矩阵不由这9例证明。
- S2 首次 Chromium 缩放因 fragment 留存发生工具错误，首轮28例未有效执行；修正后结果仍有几何失败。S2 WebKit 首次驱动 fill 抢走焦点，首轮中断；修正后静态夹具测试完成。不能把工具错误当产品 BUG，也不能把修正后简化夹具结果冒充真实页面。原 T09 与两类 CSS 探针失败不覆盖。

## 数据及角色

独立计算 A 保存的升级前和升级后 34 表快照 SHA，均为 `176da7a581e4fb3c05b30dfd92e8feab69f464a4550317f00330e56a3d81584d`。B 后续只读新连接证据确认相同目标及 source1→fee1/store1/patient2/invoice1、UID6 write/UID7 read；但升级前快照由 A 采集，B 未在升级前独立连接，不能说前像独立签署。账单1及已提交 event1/fee1 不得重放。HTTP 后 `ir_attachment` 摘要变化、行数109不变，缺逐行前像，具体差异 UNKNOWN；访问审计经 B 只读记录73→105，新32条 accepted。其他表、附件文件和历史库不在本次完整比较范围，不能写全库无变化。

读取 A 的 `identity-final.json`，记录 UID6 和 UID7 仍 active；B `verify-after.json` 记录两者在该 scratch 的 settlement write/read 权限。没有账号停用证据，不能宣称停用或 Session 失效；本角色未独立连接数据库再次读取。该隔离容器里的数据库角色是超级用户等属性，B 的连接是显式只读，不称角色本身受限。无经济 POST 的团队证据不等于服务端拒绝或全库无变化。

## 资源

本角色独立执行 `docker inspect --format '{{.Id}} Running={{.State.Running}} ExitCode={{.State.ExitCode}} Network={{.HostConfig.NetworkMode}}' 2007f4e0c139739dcf56f18403d177683b85319d7ee08f3d332155d14e4956f4`，exit 0，结果 Running=false、ExitCode=0、Network=none；`ss -ltn '( sport = :18631 )'` exit 0，无监听。此事实仅覆盖指定容器与端口，不代表审计了全部主机服务或 Session。浏览器关闭依据执行团队报告；本角色未独立枚举所有浏览器进程。
