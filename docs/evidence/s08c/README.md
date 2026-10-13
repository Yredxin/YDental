# S08-C 证据索引（整体 BLOCKED）

固定 product 8794f1c6d6d7f4a8e76c64edddfb0c49c85e3fe2；test 87b2c8588ac3012abce7d9db5f26dc5682dc4e7d。final为本文件所在提交，完整SHA由#32交付评论固定。所有运行属于Codex自测，不是GPT亲测或用户验收。

- [八部分报告](../../s08c-report.md)、[最终固定状态](final-tests.json)、[C与S08矩阵](tc-matrix.json)、[方法索引](test-methods.json)。固定测试发生SIGSEGV，最终新库完整链没有运行。
- [新原生崩溃](native-crash.json)、[日志尾段](native-crash-log-excerpt.txt)、[全部managed动作/真实退出码/日志hash/入口命令](attempt-history.json)。entry_command由实际runner action记录与固定参数重建，原生子命令见固定scripts/s08c.py。完整原始日志本机保留，不公开凭据或敏感请求日志。
- [全部浏览器/并发结果索引](artifact-attempt-index.json)。诊断PASS仅该诊断完成，候选不同SHA不合并成固定验证；未保存的外层命令退出码明确UNKNOWN。
- [最后候选16PDF/来源版本/5真实PG屏障](probe-attempts/20261013T043822532357/result.json)及同目录实际PDF、抽取文本、61页PNG。**[人工逐页FAIL](candidate-page-visual-review.json)覆盖自动PASS验收结论**：RX-2最长处方空白/正文缺失；原自动结果不删。旧RX-1重叠、乱码/尾页等失败也保留。
- 三类例：[D1待完善病历](probe-attempts/20261013T043822532357/clinical-d1-pending.pdf)、[实际发4余2处方](probe-attempts/20261013T043822532357/prescription-four-dispensed-two-left.pdf)、[未签未审核同意书](probe-attempts/20261013T043822532357/consent-unsigned-unreviewed.pdf)。均合成演示患者，非正式签发/收据/原件归档。
- [Firefox43/真实下载/14图](print-browser-attempts/20261013T043328099034/result.json)、[14图实际目视核对](candidate-firefox-visual-review.json)。原生3打印对话框实测后取消，物理出纸UNKNOWN，处方为较早RX-1。
- [崩溃后只读41不变量/17签名保全](post-crash-readonly-audit.json)、[环境原117库/2新增/核心/容器/服务](environment-preservation.json)、[本地工具版本hash](local-tools-manifest.json)。只读保全PASS不等于升级/生产PASS。
- [授权/完整Project深比较](authority-and-project-final.json)及[全部开工/交付双读快照](authority-project)，21字段/15条目/6视图及字段/7公开workflow，0mutation。
- [固定产品树/严格diff契约](fixed-tree-contract.json)、[脱敏与原JSON保留hash](publication-redaction.json)、[只读取证及诊断源码](diagnostic-sources)。PDF/PNG字节未做编辑；本机原日志/config/access文件和原JSON副本保留，仓库不含这些敏感原件。

没有在SIGSEGV后修改产品/测试或重启Odoo；报告中的最终全量计数均为NOT_RUN目标。C不可技术PASS，生产继续BLOCKED。
