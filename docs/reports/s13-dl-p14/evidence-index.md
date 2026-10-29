# P14 证据索引

- 比较基线 `c663557eeb30b9bb43f07f3ff8130c8cd3bc4382`；产品基线 `f9c4778e584e0513bcaf46cee3a76fd6883b76af`；最终 `39038bd8b84ef00fe46dc37973e05a0e46d12796`，产品树等同实测 `d70793d98c7cedbe7836900a811e517c8b9a47c8`。
- [W0/W1](w1-record.md)、[W2 方法调查](w2-c-investigation.md)、[W3 独立源码复核](w3-review.md)、[W4 scratch 复核](w4-independent.md)、[最终独立复核](final-independent.md)。
- 私有原始证据 `.local/dl-p14/`：`b-contract/` 源合同；`w1-a/` 基线静态图片；`w2-a/`、`w2-b/` 初期浏览器；`w2-b-fix/` 金额定向复测；`w3-final/` 最终产品树的隔离 scratch/QWeb；`w4-a/`、`w4-b/` 最终产品树双浏览器；`w4-a-fix/`、`w4-b-fix/` 已撤回试验；`w4-d-probe/` CSS 探针。每批自身保留源、命令、结果、失败及截图，不将不同候选混签。
- scratch QWeb 合成结果 `.local/dl-p14/w3-final/qweb-components.json` SHA256 `6487bc2314bec2db268a577eff53cc44ea1ea7166e4f6aa08bff95539569fb14`。导出的 HTML、测试数据均为合成，不是真实授权数据。渲染日志含测试 lambda 的 Unsafe function access 警告。
- 私有只读包 `.local/dl-p14/viewing/P14-static-view-only.zip` SHA256 `7f6e132355cf34a15f3bd43632163cdd7037ec2713bfdb9666d8dbfe2435f1e2`，0400，13 成员；`package.sha256`、`files.sha256` 同目录。前后图并非同单号，且均为静态合成夹具。
- 工具失败保留：系统 Python 缺 lxml 后改项目 venv；静态首轮缺 border-box；Chromium 首轮误将 Home/End 当水平滚动键；WebKit 已撤回方案的额外滚动测试 exit 130；观看包首次在错误目录校验失败后于包目录通过。以上工具错误不冒称产品 BUG；实际 Tab 焦点裁切单列 FAIL。
