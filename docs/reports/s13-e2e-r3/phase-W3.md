# R3-W3 最终候选影响面复验

状态：**限定实测完成；尚未签署最终候选通过**。本阶段 A、B、C 为新线程，主控负责运行及写入协调；共用主机不构成操作系统隔离。目标候选为 `c50688ba806c69a624c3bf9b171b10ea164bfeec`，从 R2 远端报告 HEAD `e06ae79efe6650e89deff7179cf16cf98daa59e5` 继承；与 `ca07961da750dd5c58342cfe5759f45c1f806d5e` 的历史运行服务证据分开。

相对 R2 报告 HEAD，候选修改 clinical 路由、服务、文书界面及模板、treatment 队列服务和终态标签，附加 MODEL／HTTP 测试。W1 A/B 在旧候选通过真实岗位页面与持有租约观察后登记 R3-BUG-001；独立 D 修复，不能由实现者自签通过。W2 的 interrupted 来源待完善文书在旧服务上真实转派、编辑和补记，不证明候选上 completed 来源的行为；详见 [W1](phase-W1.md)、[W2](phase-W2.md) 和 [缺陷登记](bug-register.md)。

## 验证准备

A 计划以独立 scratch、network none／Unix socket 在候选上验证完成、重放、文书确认状态、回滚和过期的 MODEL／HTTP 路径。该测试 addon 使用 demo 供给替身、部分过期结果由 mock 注入；不等同真实供给、完整真实浏览器接诊链或独立业务已提交。真实 isolated_test 供给策略受环境身份绑定，新 scratch 不得冒用受保护历史库身份；受保护历史库也不授权升级。后续以实际运行结果与 B 的独立复核为准。

B 独立 SOURCE 比较 `ca07961` 与候选：产品改动涉及 clinical／treatment，未修改 patient／access 模块及 R2 病患直接写拒绝审计修复路径；这是未受影响的源码比较，不冒充最终候选动态 403 回归。完成路径源码要求持有医疗租约、当前 serving execution、当前患者关联与 SaveIntent 校验，随后结束 execution／号位和 task、释放文书编辑占用，保留工位租约；未调用费用／耗材或创建后继。pending 文书可按规则转派，confirmed 不可转派。该段是源码判断，不代替实际网页、竞争和已提交状态的验证。

B 独立新 scratch cluster `7701887472848355358`／OID `16384`、network none／socket-only，在固定候选执行 9 项 MODEL post-tests，覆盖正常完成／重复／待完善文书转派、已确认文本保持、过期／异常回滚、交还／重复／回滚、D1／D2 责任及跨店／撤权模型；0 failed／0 errors，Odoo exit 0，容器 stop exit 0。日志 SHA-256 `0f1534bd71290386c1abe6da4f9ea4551ab65a4bd02a72a1441ebc803cc2ceec`。供给使用测试替身，过期和失败部分为注入，且为事务测试，不证明真实供给、真实浏览器或持久已提交；本组计数未覆盖治疗 event／fee，不能据此认定费用不重复。

A 在另一个独立最终候选 scratch cluster `7701887430466183198`／OID `16384`、network none／Unix socket 运行 6 项 post-tests，四项 MODEL 覆盖完成／重发／已确认文书／失败回滚／过期，两项 HTTP；0 failed／0 errors、Odoo exit 0，容器正常停止。日志 SHA `52ebd2cdad138b18f5236100cdb0f34dbc3f25f6eb5a5bd9f1a7e749267b8218`。同样含 demo 供给替身和过期／故障注入，不是浏览器、真实供给或独立已提交测试。`git diff --check ca07961 c50688b` 和相关 JS `node --check` 均 exit 0；源码未变化不能代替动态拒绝回归。

A 补充的费用／库存 MODEL 专项首轮 setup 因新 scratch 未启用库存多仓／库位而返回 `configuration_required`，0 tests／exit 1；容器已停止，日志 SHA `a3ba682d912745621b853d1625e3a6ed71fab9b42e8a9c1e5d31ca1f6fd04e69`。B 独立审查后，A 在另一全新 scratch 的测试事务内配置相关功能组继续，不能以首次失败或测试代码计划代替实际后续结果；没有改动历史库或共享配置。

第二 scratch cluster `7701888174067765278`／OID `16384` 在 `c50688b` 运行补充专项 1 post-test，0 failed／0 errors、exit 0，容器正常停止；日志 SHA `d21a5dbd6745af35bae08afbb7ff7f0b0d0852fdd38cfb35639f07666e233a25`。B 独立复核两轮日志与测试代码（测试文件 SHA `640168b1a2b6ed782f1fb8eb023a5611595cfd117e1619070f401cea43bdb131`）：首轮 `setUpClass` 0 post-tests、0 failures／1 error、exit 1，归 **TEST_ENVIRONMENT_ERROR**，不登记产品 BUG；第二轮确实执行新合成治疗及耗材，完成及重复后比较 event／fee 关键字段、quant 数量及预留、任务和库存数量保持。仍为使用 demo 供给替身的 MODEL 事务，不能冒称真实供给、浏览器或独立持久提交。

## 阶段结论及未完成项

固定候选的独立 MODEL／HTTP 回归及代码影响面检查成立于上述限定范围；A 的环境初始化失败与 B 的归因保留。没有在 W3 确认新的产品 BUG。R3-BUG-001 的真实普通岗位浏览器正常完成、重复与旧页重发及独立已提交状态仍缺证，保持 OPEN；已完成来源文书的最终候选真实转派、真实费用和耗材保护不能由 MODEL 冒称完成。W2 真实浏览器接手系旧服务版本，不能与最终候选混签；未测有医疗写权但无转派权的负例、Session 状态和全部最终保护仍留 W4。R2 拒绝审计路径源码未变，不代表本阶段新做了真实 HTTP 403 回归。

各项 scratch 容器已正常停止；本阶段未对受保护历史库做模块升级或重放 R1／R2 经济业务。历史目标新任务、未完成文书和待处理处置仍须最终独立保全核验，账号及历史服务须按正常授权与实际联动处置。
