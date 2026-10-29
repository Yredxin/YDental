# P14-V2 T01—T12 验收矩阵

最终产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`。状态对应实际证据层级，PARTIAL/FAIL 不得写成整体通过。

| 编号 | 状态 | 实际结果及限制 |
| --- | --- | --- |
| T01 | PASS / SOURCE | 独立审查28项通过，目标区域外 XML C14N 一致，仅3个结算产品文件。 |
| T02 | PASS / SOURCE、限定 HTTP | 五列表头、卡片同源字段及分页保留；真实一笔账单，双账单和分页为已加载 QWeb 内存合成。 |
| T03 | PASS / 限定 HTTP | 真实可写、只读、导出只读及空态岗位；不外推所有角色。 |
| T04 | PASS / 限定 HTTP | 一笔真实账单唯一表单、真实令牌键名、FormData、校验属性与300字；未发送经济 POST。 |
| T05 | PASS / 限定浏览器 | 原生 details 的 Enter/Space 和取消导航、JS-on/off 代表场景；多账单同名组仅加载 QWeb 合成。 |
| T06 | PASS / SOURCE、HTTP | 局部 SCSS 编译、真实 frontend CSS HTTP 200，SHA256 `0ffcbe93ba588deca9e578b549bd6ae5f0257967bba52696df00845583923db4`。 |
| T07 | PARTIAL | 两引擎八主视口正常缩放布局和焦点诊断；指定缩放中 WebKit 根字号200%焦点失败，320物理宽原生200%探索未执行。 |
| T08 | PARTIAL | 真实一笔金额及双视图可读；两笔/分页为合成，未完整验证全部长内容、遮挡与屏读。 |
| T09 | FAIL | WebKit、320×800 CSS px、root 200%、真正 JS-off，Tab 到 amount/reason 轮廓底部 803.59375 > 800；退出2。完整轮廓不满足合同。 |
| T10 | PARTIAL | 目标外源码冻结、正常缩放布局有实测；未对全部相邻区域及缩放组合独立完成影响回归，P12 A04 原 FAIL 不改。 |
| T11 | PARTIAL | 独立升级前后受采34表、附件及引用文件/审计投影核查；HTTP 后技术资产与审计分类另记，不代表全库零变化。 |
| T12 | PARTIAL | 固定代码、独立源码与焦点审查、失败证据及资源处置见报告；T09 FAIL，不能 TECHNICALLY_COMPLETE。 |
