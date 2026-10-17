# D 准入阻塞：正常全局租约过期处理与旧临床保全冲突

状态：PRECONDITION_BLOCKED / D六TC NOT_RUN。未创建D患者/费用/账单/收退款，无金融派发intent，无新增经济提交。不是普通工具失败，不计修复循环。

新主目标独立RO1（6734行/316表）保留旧lease8、9、10：ydental_active=True，expires_at分别2026-10-17T04:53:57、04:58:10、05:01:15；关联execution8、9、10及entry8、9、10均serving。此处仅从已封存raw读取，不新增保护源或目标连接。

源码链：queue._operate和intake._queue_accept调用queue._expire；该过期处理范围是全库，按正常业务会把上述lease改为inactive/timeout、execution和entry改为verify，并追加root automation审计。更换新store或新actor不能隔离此变化。正常新费源经treatment._execute→_medical→_serving要求合法有效租约/执行；支持的上游创建入口必须经过该全局处理。直接内部_event/_new造费源只能是MODEL合成，不能冒充D所需真实合法上游链。

本包要求保全旧临床和已提交成果，未授权修改queue过期机制、手工清旧租约、重放旧治疗、第三库或scratch持久经济来源。故主控按已批硬边界冻结依赖D新来源的动作，不修旧记录、不patch过期逻辑、不造资金证据。

独立性：developer只读源码盘点；acceptance独立源码和新目标raw核实；tester唯一运行者接到冻结。clinical._operate和settlement._operate不触发该全局_expire，A/B/C/E及LOG/GPR验证可继续。E仍使用真实已有数据和A/B/C新事实执行S10-only升级；不得写成含本轮新D资金链的升级通过。

受影响TC：D-ADMIT、D-NORMAL-6、D-FAILED-2、D-RECOVER-2、D-LOST-REFUND-2、D-VERIFY-RETRY。推荐本轮交付具体阻塞及已完成独立范围；未来另行确认怎样合法处置旧临床过期事实及D来源，当前不扩大批准范围。Native根因UNKNOWN，S10阶段仍BLOCKED。
