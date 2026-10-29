# R3 产品缺陷登记

## R3-BUG-001：医疗接诊缺少正常完成入口

**PRODUCT_DEFECT / OPEN；严重程度待主控评估。** 发现 W1：A 在新患者1652、医生1563、execution559实际持有租约并确认治疗 event367 后，通过真实浏览器检查 queue、clinical 和 treatment 页面，未发现正常结束入口。A 原始日志 `d4303485acb83e00ec517089bc93e608fdc61022caaf59c128294ae91f6428e2`；B 物理读回 event367 confirmed／唯一 fee362=600、旧记录保护 `0e5c7aafa4a14a255204864fb9eae379ef0f0161dd431dad4ded188724b53e7c`。项目已执行不等于文书确认或诊疗任务完成。

B 独立新 Session 通过正常现场核查取得新 execution560／lease565 后，真实持租约复现：queue 的 Renew／Exit／Save and hand over 可用，queue、clinical、treatment 均未见正常结束入口（`d2eb85be3db0b7a1ee8a2dde2f56f57547ee715f9cbde7ebda3c31b40bd49596`）。A 独立物理核原 execution559 interrupted、新560 serving、doc520责任与原event/费用保持，`dad8c5c9485105523ebfa041450e68cde316d83017c84b828f52cc486524a573`。B 分类 PRODUCT_DEFECT，主控裁定确认；不是操作错误，无需操作争议定向复验。源码当前医疗队列仅 reserve／restore／handover，`_exit` 在忙时拒绝；交还创建后继，不能冒正常完成。影响为合格医生已实际执行项目后无法在观察范围正常完成医疗任务，文书确认与结束仍须分离。

原 B Context 已关闭，但当时 lease565 仍 active，实际释放须另核。修复范围、独立开发者、固定代码、最终候选动态回归和剩余风险均待实施；不得自动签署文书、清理历史待办、重放事件367或将源码推断冒全部入口实测。

独立 D 在隔离 worktree 开发候选 `df4efc3`，涉及医疗正常结束、完成后待完善文书转派与相关 UI；静态编译／语法检查通过，模型、HTTP、浏览器及未实现者验收当时尚未运行。首次 `/tmp` worktree 因空间不足失败、翻译工具缺失均为环境／工具限制，不计产品 BUG；后续固定候选与独立实测须另记。

修复集成：独立 D 原候选 `df4efc3b8accd6d9bdce07ecda5063fec2531a58` 与 `34d3c29580aa64d760e0556fb7e22f8ad7035b62` 已由主控 cherry-pick 至 `e0a1a6434afc9eac78083aafb17f6afee84bcbba`／`c50688ba806c69a624c3bf9b171b10ea164bfeec`。B 独立 SOURCE 审查、D 四项 MODEL（含供给替身）及两项 HTTP（过期状态 mock）限定证据见 [W1](phase-W1.md)；最终候选真实浏览器及已提交影响面尚未实测，因此缺陷保持 OPEN，不由作者自签。

W3 新 A/B 对最终候选独立运行含供给替身的 MODEL／HTTP 回归，另对合成治疗、耗材后的完成／重发比较事件、费用、库存和任务；具体日志、环境初始化失败与独立归因见 [W3](phase-W3.md)。这些事务及替身证据不证明真实岗位浏览器完整正常完成、旧页重发或持久提交，**OPEN** 不变。

### 2026-10-29 限定验收增量

**R3-BUG-001：FIXED_VERIFIED（仅本次接续接诊、正常完成、防重及文书责任所测范围）**。固定产品候选 `f9c4778e584e0513bcaf46cee3a76fd6883b76af` 的真实隔离供给、普通医生浏览器、正常完成和新连接持久读回，以及同 key／旧版本受控重发与文书权限验证见 [1.2 定向验收](bug001-browser-verification.md)。原治疗属于超时后中断的旧执行段，正常完成发生于同一任务的现场接续段；不将两段事实混称同一执行。完成响应部分字段 UNKNOWN，持久状态已独核；无效编辑凭据的确认负例不能外推全部代签场景。上文各历史时点的 OPEN 与所有失败、UNKNOWN 保留；R3 整体仍 PARTIAL，#37 OPEN，P14 未授权。
