# S08-B定向返工脱敏证据索引

固定product `0a49fac432bcac0197eeddae9675b8cddb46e631`，固定test `f887d828da292d0da0513e667469b9df28ee4f05`。final完整SHA在#32本次交付评论。最终库为 `ydental_s08b_test_20261013015317_e72d1fca`；仅Codex作者自测，等待GPT独立技术复核。

- `final-tests.json`：固定提交、每条实际模型/HTTP测试、所有命令/exit/logSHA、并发、Firefox、翻译及NOT_RUN。
- `committed-business-projection.json`：只读原始SQL/绑定参数及真实持久事件、SKU、S05价格版本/币种、费用、native move/lot/quant、执行历史和A-only范围。
- `audit-after-business-upgrade.json`：35项SQL异常数均0。`business-upgrade-signatures.json`：24表相等；`pure-document-economic-signatures.json`：13经济表相等。
- `probe-attempts/`：A16+B25独立backend/barrier竞争和候选原始结果。最终以final-tests所指两份为准。
- `visual-review.json`：最终48张原PNG逐张实际打开核验记录与SHA；A/B/R结果JSON在对应 `*-browser-attempts/`，其中较早FAIL/候选PASS另存，不计入最终48图。
- `reproduction.json`：先加真实负向、原产品3FAIL+2ERROR。原“空白处方可开立”反证：原草稿即被默认required拒绝，不伪称复现。
- `attempt-history.json`：3个新库全部actions/logSHA/frames及所有浏览器尝试。原始私有日志、配置、口令、历史DB均在本机保留，未提交。
- `rework-candidate-browser-crash.json`：候选Firefox21项后page crash，根因UNKNOWN。
- `original-a-http-retry-exhaustion.json`：最终库首次A11项/2图FAIL，原生5次serialization重试耗尽HTTP500；同固定代码/参数完整重放PASS不代表根因修复。
- `browser-orchestration-interruption.json`：最终B24项/13图实际PASS后外层SIGTERM143，子进程exit UNKNOWN；精确PID/config已无进程，只移除失效自有marker后恢复R/升级。不得声称全程exit0。
- `environment-before.json`、`environment-preservation.json`：原114库OID/名称保全、本轮新增3合成库、容器/卷/核心/原服务不变，自有预览均已无进程。
- `project-initial/`、`project-final/`、`authority-and-project-final.json`：全部字段/条目/视图/公开workflow只读双快照和深比较，Project 0 mutation。
- `security-sweep.json`、`static-check.json`、`guard.json`、`translation-<最终库>.json`：逐模式自审、语法、guard5、实际POT/PO307。
- `diagnostic-sources/*.py.txt`：本轮本机只读SQL/导出、隔离预览编排、固定清单校验源代码归档。原运行脚本直接读受控本机config取得凭据，归档仅含字段名，不含凭据值；产品/测试正式代码仍在仓库模块及scripts/。
- `checksums.sha256`：本次AGENTS/四份文档及所有脱敏证据的完整SHA256，排除该校验文件自身。

所有合成药物、10/27/43/99/600演示价格及临床文本均不代表生产政策。S08-C/S09/S10未启用；历史S07 SIGSEGV、原B及本轮候选浏览器崩溃、原生竞争/运行器中断风险未宣称修复，生产部署BLOCKED。失败证据保留，后来的PASS不能抹去先前FAIL。
