# S10-CLOSEOUT v1.1 最后一轮定向修复 R2

R1真实执行a9afc6173c87740014ae45db3f3e24d137ce8674，native PID962172/backend1481921，
exit1/SIGSEGV=false。独立准入645表完全同R0尾审。scope108/audit1176/1177提交核回；
acquire存储write_uid1再次被原断言拒绝，完整差异/第一异常已保存，未执行confirm或后续。
R1最终RO已关闭，doc pending/v2/no editor，acquire审计1178及四mutex更新均回滚。

真实固定源码显示，R1修复只覆盖业务返回之后，仍遗漏服务内部savepoint退出的隐式flush：
clinical._operate:116→sql_db._FlushingSavepoint._close:178→Cursor.flush:301→
Transaction.flush:744，其default_env在environments.py:704选第一个有效uid（执行器root1）。
显式actor.flush发生在这之后，不能改回已写的writer1。真实actor/editor/audit均7，
无经济变化，独立尾审与acquire前完整事实相同，因此属于同一取证器环境缺陷的有限返工；
不将writer1接受为正确，不宣称R1通过或产品已修复。

采用core tests/common.py:686的正常测试身份绑定：每个真实actor调用前绑定
transaction.default_env=actor.env，让内部savepoint与显式flush同actor；全部调用改为延迟lambda，
不得先执行再换环境。成功清洁后恢复旧环境；异常有dirty时保留actor，绝不切uid1去flush。
bind创建scope也按actor；不改产品、core、write_uid字段、权限、文书锁或任何门禁。
实际core Transaction.flush与FlushingSavepoint._close离线执行：原default1→1，绑定7/5/6/41后
隐式及显式均对应actor；真实R1 writer1仍拒绝，R1回滚完整比较PASS。新反例/源码检查exit0。

原计划初次+最多2轮，本轮为最后一轮。唯一副本不变，不CREATE或重放旧经济。
从r1有效尾审做独立RO/RR准入。R2入口resume-r2，不调用R0创建或R1旧窗口。
经济、权限、版本及逐动作完整存储差异门禁原样保留。

RO已用8/28（源2/3），Odoo2/6。余额静态明确分配：准入1；
A四次提交核回4（新owner scope随acquire同一合法事务提交，不删除旧scope）；
B六项模型拒绝逐项完整差异，随后随C回滚夹具末端同一次提交独立核回1；
C准备1；D准入/新来源/failed/recover各1；A页面取回1；C真实授权/恢复各1；
D丢响应查证/同键重试核回各1；E前后2；新副本终审1；最终源保全1。
合计20条余量，累计28；无预算增加。Odoo余4=本native+preWeb+唯一升级+postWeb。
正常native单进程最长1200秒（含完整证据序列化），不增加进程或业务重试。
任何再失败不继续修复或另建库；先封存已得材料，按剩余预算保全并正式BLOCKED。

A+B→C+D→E、真实D日期身份/全部渠道日结、原件同SHA/0重渲染、网络层分列、
精确升级白名单及全部硬停止条件不变。源最后1条只在本包真正结束使用。
R0/R1 STOP及所有旧失败保留；R2许可只解除已经证明回滚的同一取证器缺陷，非放宽身份。
GitHub同步真实独立记录；交付完整五组结果/22行/固定提交/证据/push，随后STOP等GPT。
