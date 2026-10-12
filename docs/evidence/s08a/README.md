# S08-A 脱敏证据索引

固定 baseline `a5f53ac72d6d43901932adedc64c56cf6f97c675`；product `a69ac8bc431adb412341cd2fbff508d69ca0b84a`；test `be5f28ef336295633fd0d753c3e97051a2dc457d`。最终文档提交完整SHA固定于#32交付评论。全部为Codex自测；GPT复核/用户验收尚未发生。

- [最终测试与环境](final-tests.json)：新库/创建UTC/cluster/OID/config/端口/PID、命令、角色、数目及退出码。
- [实际执行历史](execution-history.json)：全部中间及最终action和私有原日志hash；不是公开原始日志。
- [失败与修正链](failure-chain.md)：失败从未删除或冒称最终PASS。
- [16项TC适用矩阵](tc-matrix.json)：A适用子范围与B/C/S09未做范围逐项区分。
- [逐项测试方法](test-methods.json)：21模型+7真实HTTP/RPC及前置/操作/断言实现引用。
- [Project保护](project-check.json)：唯一#32 mutation，两次开工全读回和两次交付全读回的深比较/完整快照hash。
- [GitHub需求再读](github-readback.json)：#23/#32正文和全部原有效评论再读、#31最新技术/状态未改变。
- [升级与经济签名](signature-comparison.json)：10组带业务升级前后相等；文书UI流程前后6组经济签名相等。
- [截图目视核验](visual-review.json)：最终Firefox全部11张的逐图观察和hash。
- `browser-attempts/`：每轮Firefox的检查、真实截图hash及PASS/FAIL；最终目录在final-tests.json固定。
- `probe-attempts/`：不同PostgreSQL backend PID/barrier、有界serialization retry的真实竞争；最终16/16。
- `audit-attempts/`：只读8类SQL不变量、10组行签名和临床审计计数；不导出病历全文或编辑秘密。
- `translation-*.json`：真实POT导出与源PO匹配；失败单独保留。

## 重现命令

使用核心 `../.venv/bin/python`，以下DB是本次已有证据对象，不能把install用于复用/重置它。独立复验必须生成另一个全新 `ydental_s08a_test_14位UTC时间_8位hex`，新建marker/OID/config由runner创建，专属空闲18000–18999端口。不要装业务库/历史库。

```bash
../.venv/bin/python scripts/s08a.py install --db NEW_UNIQUE_DB --port NEW_PORT
../.venv/bin/python scripts/s08a.py upgrade --db NEW_UNIQUE_DB --port NEW_PORT
../.venv/bin/python scripts/s08a.py probe --db NEW_UNIQUE_DB --port NEW_PORT
../.venv/bin/python scripts/s08a.py preview --db NEW_UNIQUE_DB --port NEW_PORT
../.venv/bin/python scripts/s08a.py audit --db NEW_UNIQUE_DB --port NEW_PORT
../.venv/bin/python scripts/s08a.py serve --db NEW_UNIQUE_DB --port NEW_PORT
../.venv/bin/python scripts/s08a_browser.py --db NEW_UNIQUE_DB --port NEW_PORT
# 独立终端按serve.pid和精确odoo.conf核对后，只SIGTERM本次预览。
../.venv/bin/python scripts/s08a.py audit --db NEW_UNIQUE_DB --port NEW_PORT
../.venv/bin/python scripts/s08a.py upgrade --db NEW_UNIQUE_DB --port NEW_PORT
../.venv/bin/python scripts/s08a.py audit --db NEW_UNIQUE_DB --port NEW_PORT
../.venv/bin/python scripts/s08a.py export --db NEW_UNIQUE_DB --port NEW_PORT
PYTHONPATH=.local/s00-b-deps/verify-lib ../.venv/bin/python scripts/s08a_translation.py --db NEW_UNIQUE_DB
../.venv/bin/python -m unittest scripts/test_s08a_guard.py
```

账号只记录角色，不提交凭据；随机密码/token/session cookie与私有config/原始日志留本机.local权限600。截图只有合成人员/患者且浏览器保存前扫描凭据。预置capacity演示与单例合成外检前提均明确测试限定，真实文书hook没有替身。

S08-B/C和S09—S13及生产NOT_RUN；历史S07 SIGSEGV根因未确定，生产部署BLOCKED。
