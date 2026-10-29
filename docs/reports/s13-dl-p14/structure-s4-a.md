# P14 结构调整 S4 A：独立浏览器证据复核

2026-10-29，未参与产品实现的 S4 A 只读复核固定候选 `34f7681797f4ad4aec0b3aa7201b9bf9d02761d8` 的现有结果；未启动或连接服务、数据库，未发送任何请求。结论 **T09 FAIL，P14 仍 PARTIAL**。本复核检查原始证据，不将先前测试脚本退出码视为几何通过。

真实普通写岗位 Chromium GET 使用已提交的单笔合成账单、实际 Odoo 前端资产，JS on，三个视口各三种缩放；独立解析 `.local/p14-structure/s3-b/real-focus.json`，9 例中3例新增表格内免单链接的焦点轮廓在 Tab 后被横滚框裁切：

|视口和缩放|轮廓水平边界|滚动框水平边界|结论|
|---|---|---|---|
|320×800 native200|9.13–151.14px|24–136px|两侧裁切|
|320×800 root200|18.70–300.72px|24–296px|两侧裁切|
|768×1024 normal|637.14–779.16px|24–744px|右侧裁切|

剩余六例该锚点未测得水平裁切；每例 Enter 片段目标为 `waive-invoice-1` 的原生 summary，表单唯一且绑定 invoice_id=1。独立读取 `real-focus-controls.json`：相同9例的表外 amount、reason、提交和取消在所测横向轮廓内且无横向裁切祖先。该真实页面仅 Chromium、JS on、单账单、3视口；实际 WebKit、JS off、其余真实视口、真实 PDF 及完整多账单场景不能由其反签。原始 JSON SHA256 `90af393e98d96f82ffe5e26a8a4c146e0776de103542319eb5b7234b09864112`；测试中的 0 禁止经济请求/0 外部请求不代表服务端权限拒绝。

已升级 scratch 实际 loaded QWeb 的内存合成五分支结果 `.local/p14-structure/s3-a/evidence/loaded-qweb.json` SHA256 `1fdab3a76abc05f1a1152db0e57ba42274fdf5ef715bbb36cd5126378fb27bab`。本角色使用项目 venv 的 lxml 对结果独立解析：两个 write 分支均为两行、两链接、两个唯一 summary、两表单；链接目标和 summary id 分别与隐藏 invoice_id 逐笔一致。两个 read 分支各两行但没有免单链接、summary 或表单；empty 均为零。断言 exit 0。账单与权限是内存合成；这不是实际双账单岗位数据或持久财务验证。

S2 静态手工变换夹具的 Chromium 30 组合中，新增免单锚点12例、原 PDF 14例有水平焦点裁切；WebKit 同层级30例未记录水平裁切，超长 summary 的纵向可达性仍须单独验证。这些均使用简化外壳，不是实际加载的候选页面全矩阵。真实岗位的 3/9 失败本身已足以保留 T09 FAIL，不需要将不同层级结果混签。

真实前图 `.local/p14-structure/s3-a/evidence/real-before-bf60346.png` SHA256 `0badaa3c061eb6d8c4eb0587fe2d018b84a698b4d48b6bc9d7d62280de7cdca9`，图像 1280×720；真实后图 `real-write.png` SHA256 `91afdf896987eaedc609975705c1d11b7fecc241bfad6e26517b6e9fdd6409c1`，图像 768×2160。均是先前/本次真实岗位合成页面，版本、视口和展开条件不同，不能作相同条件的像素级前后对照；旧图不得覆盖。真实失败截图 `real-768-normal.png` 为768×1024。

S3 升级前快照由执行者采集，独立者在升级后对照，不冒称前像独立读回；HTTP 后 `ir_attachment` 摘要变化、逐行前像缺失，具体变化 UNKNOWN。历史库、全部数据库与真实多账单均不在本复核覆盖范围。有关容器、审计和受检表的限定记录见 [S3](structure-s3.md)；本角色没有自行核实停机或数据库状态。
