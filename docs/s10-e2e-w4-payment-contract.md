# S10-E2E-W4 安装态与两笔付款合同

授权：[#34 / 6185772190](https://github.com/Yredxin/YDental/issues/34#issuecomment-6185772190)；W3 独立复核：[#34 / 6185715797](https://github.com/Yredxin/YDental/issues/34#issuecomment-6185715797)。固定起点 `71a554667157cdd917c0062db5e4ddf1693f6410`。

| 阶段 | 执行动作 | 付款前硬门槛与 STOP |
| --- | --- | --- |
| 来源 | 只读 W3 OID2100285、152 个当前 filestore 文件和 164 个附件指针 | OID/cluster/config/marker、92 模块、38 张逐行经济/权限表、四费600/80/40/20、原生库存 done、posted740/residual740、付款/核销0、无业务连接；任一漂移 STOP |
| 克隆 | 唯一新库 `ydental_s10_test_20261015064000_d41e7b62`，端口18279；CREATE 一次 | 来源/目标全部业务行、模块、安装态视图、附件 SHA 相同；任一差异 STOP |
| 视图同步 | 原 venv Odoo20 仅 `-u ydental_settlement --stop-after-init --no-http` 一进程 | 除目标模块元数据和视图以外，38 张经济/权限表逐行哈希不变；源库不变、非目标模块元数据不变。安装态 token 的每个语言 arch 均须含 `output=html`，否则 STOP |
| 页面 GET | fresh 经理会话选原门店；GET `/ydental/settlement?patient_id=1` | 原 invoice1 posted740/residual740，真实已渲染 pay form 唯一选 invoice1；`output=html`、CSRF/key/revision、amount、cash、actual_utc、proof 和 HTML5 有效性全部成立；无写前拒绝则不发 POST |
| 首笔现金 | 原生 pay 表单提交500一次 | 付款前持久 intent；实际 form-urlencoded POST 的 output/pay/invoice1/500/cash 与 token 存在性落盘（不公开 token 值）。响应与只读账态先落盘，再要求 HTTP303、站内 Location 与一次性“操作已受理”反馈；原生 payment move posted500、一条partial500、S10 payment/receipt、S01 accepted、余额240 才进入第二笔 |
| 第二笔现金 | 重新 GET，原生 pay 表单提交240一次 | 同一合同；新增 posted240/partial240，余额0。两笔原生 payment、partial、S10 receipt/source、借贷平衡、全部原临床/费用/库存/权限表和 W3 源库保持真实不变量 |

不重做临床、检查、发药、出账、退款、日结。每笔 POST 最多一次；若响应丢失、状态异常或断言失败，先记录只读现态，再立即 STOP，绝不重发。私有日志/截图仅提交 SHA256 和脱敏 ID/金额/状态。脚本哈希在 GitHub 事前检查点固定，付款提交后不改脚本重跑。
