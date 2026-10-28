# R2 验收矩阵

| 条目 | 当前结论 | 实测层级与限制 |
|---|---|---|
| W0 身份及保护基线 | 限定准出 | RO/RR 真实目标；旧完整前像缺失 UNKNOWN。[W0](phase-W0.md) |
| BUG-002 升级 | PARTIAL／OPEN | 新独立 scratch `-u ydental_supply`，revision 3→3；W6最终候选再次实际升级同样3→3；历史库升级 NOT_RUN。[W1](phase-W1.md) |
| BUG-002 竞争及回滚 | 限定通过 | 最终候选新scratch MODEL，两物理事务锁等待、一提交一40001回滚，补试无重复出库；非HTTP或容量并发。[W1](phase-W1.md) |
| D1/D2、全景与CBCT | PARTIAL | 历史合成目标真实浏览器/独立读回；D2治疗event confirmed、handover终止当前执行段但未证明诊疗任务最终完成；文书pending，CBCT未执行保留。独立完成入口源码未见明确入口，A未实际尝试、B未动态复现，属优先复测线索而非已确认新BUG。[W2](phase-W2.md) |
| 耗材与缺货 | 限定通过 | 新lot真实耗用1；新来源真实409 insufficient_balance，无费库副作用；首409正文UNKNOWN。[W2](phase-W2.md) |
| 无药房权及受控发药 | 限定通过 | 真实HTTP403及独立无副作用；有pharmacy权无原生stock ACL真实派生费用和移动。[W3](phase-W3.md) |
| 幂等、超额及库存 | PARTIAL | 正确同key HTTP already_accepted、超额409；两个HTTP区间重叠一成功一不足，未证数据库锁等待；已完成事件浏览器重复点击NOT_RUN。[W3](phase-W3.md) |
| 退药及余量 | 限定通过 | 新退药入隔离，未恢复可领；续领916 pending。[W3](phase-W3.md) |
| 跨店及撤权 | 限定通过／最终影响面待验 | 旧服务历史目标直接403、旧页409、撤权403；最终候选scratch精确直写及撤权403、denial audit独立已提交。[W4](phase-W4.md) |
| 财务／附件／导出／日志 | 限定通过 | 指定真实403/404及HTTP200 JSON error分列；具体部分403正文未采，页面审计仅前100行。[W4](phase-W4.md) |
| 旧PDF及责任 | PARTIAL | 310下载/打印请求、311/312下载原快照一致；旧店65及账单1权限受阻；物理出纸未验。[W5](phase-W5.md) |
| W6 总验与收尾 | PARTIAL | 最终候选scratch升级及MODEL竞争复验；八账号停用和保护读回，服务精确停止，原退出码／Session失效UNKNOWN；最终影响面仍须分层。[W6](phase-W6.md) |

TECHNICALLY_COMPLETE 的必要项未全部成立；不能以不同候选证据拼成最终候选完整通过，也不改写 R1 PARTIAL。
