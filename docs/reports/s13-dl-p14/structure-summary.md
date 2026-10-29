# P14-STRUCTURE / 1.0：PARTIAL，T09 FAIL

2026-10-29。结构候选 `34f7681797f4ad4aec0b3aa7201b9bf9d02761d8` 将每笔原生免单表单移出横向滚动框，保留五列表格、原字段、权限及每账单唯一对应。真实页面复测中表外表单控件在所测组合横向可见，但表内新增办理锚点在 320 两种200% 和 768 正常缩放时焦点轮廓仍被裁切。故 T09 **FAIL**，P14 继续 **PARTIAL**。按计划不再追加 CSS 试验；候选保留在分支上，是否保留或回退由用户与 GPT 根据证据决定。

- **结构及合同：** [设计](structure-design.md)、[S1 源码复核](structure-s1.md)、[独立审查](structure-s4-review.md)。唯一表单、原生 details 组、表格字段、分页、PDF 条件、动态取消 href 和原表单序列经 SOURCE 核对；实际 loaded QWeb 的两笔账单合成分支中，行链接、summary、invoice_id、单号与余额一一对应。真实岗位仅一笔合成账单，不能代替真实多账单权限。
- **浏览器：** [S2](structure-s2.md)、[S4 独立浏览器复核](structure-s4-a.md)。简化合成夹具 Chromium 30 场景中新增锚点有12个水平裁切；WebKit 30 场景未记录水平裁切但部分超长 summary 高于物理视口，仍须正常滚动可达评价。真实 Chromium 正常写岗位9个组合中3个新增锚点裁切；该实际失败足以维持 T09 FAIL。真实岗位 WebKit、JS-off、PDF 和全矩阵未测，不以静态结果冒通过。
- **真实加载与保护：** [S3](structure-s3.md)、[S4 记录](structure-s4-record.md)。指定隔离 scratch 升级至候选后，真实写/只读岗位 GET、CSS HTTP 200、锚点跳转和内存 FormData 有证据。升级前后34张受检表摘要相同；升级前像由实施者采集，未在升级前独立读回。HTTP 后 `ir_attachment` 摘要变化而行数不变，因缺逐行前像具体差异 UNKNOWN；正常访问审计 73→105。未做经济 POST，原 event1/fee1/invoice1 不重放。此结果不证明全库或历史库无变化。
- **前后截图：** 私有 `.local/p14-structure/s3-a/evidence/real-before-bf60346.png`（SHA256 `0badaa3c061eb6d8c4eb0587fe2d018b84a698b4d48b6bc9d7d62280de7cdca9`）与 `real-write.png`（`91afdf896987eaedc609975705c1d11b7fecc241bfad6e26517b6e9fdd6409c1`）。均为真实岗位合成账单，但视口与展开状态不同，不是同条件像素对照。真实焦点截图和几何在 `.local/p14-structure/s3-b/`。
- **证据限制：** `.local/p14-structure/s2-a/results.json` 当前 SHA `e28e154ab47c53db8c1b32bc67d5d60d5950b848390058d48a87748bf58f5343` 与 [S2 原记录](structure-s2.md) SHA `534e962fb766697b9d80c42a46ecb58501d3aab27683de32c0c0fc75c7d9a970` 不符；原因及旧内容是否不同 UNKNOWN，保留原记录，不用旧 SHA 反签当前文件。真实岗位失败有独立结果支持。

Odoo 与独立容器已停止并独核，端口无监听；UID6/7 在该 scratch 的最终证据仍为 active，Session 失效未测。#37 保持 OPEN，原 P14/T09 失败与 P12 A04 历史结论不改；不启动 P15、不合并、不部署、不安排用户演示。
