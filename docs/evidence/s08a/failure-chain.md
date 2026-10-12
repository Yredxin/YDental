# 失败、修正与中间运行保留

所有数据库均为本批新建隔离合成库；没有接管历史库。完整 action/PID/SHA/退出码/测试数及私有原日志SHA256见 [execution-history.json](execution-history.json)。浏览器每轮独立目录保留 result.json 和已完成的合成截图；没有覆盖失败证据。

|阶段|实际失败/限制|处理与证据|
|---|---|---|
|b87575e初始安装|1 failed、18 errors、21 tests|S03合成demo容量前提未提供；HTTP夹具方法名与datetime冲突，负向参数先触发签名错误。05226d0修正测试前提/命名/参数，19方法通过；不是最终PASS|
|74c6678 preview|exit1|试图普通修改原生工位名称触发上游version保护；移除该非必要夹具改写，随后新preview成功|
|388f9c5首次Firefox|20 checks/9图/pageerror0后FAIL|测试期待“真实D2 serving”，页面当时只展示坐诊连接信息。产品补真实接诊段状态，测试改查稳定data-state。目录20261012T105343263272|
|059dab9第二次Firefox|22 checks/10图/pageerror0后FAIL|真实断网时浏览器原生英文NetworkError覆盖中文未同步提示；ca27708修正TypeError/offline中文反馈。目录20261012T110412225250|
|ca27708 / 9a4287e带演示价格数据升级|各0 failed/1 error/27 tests|S07真实库存回归夹具触发原生多仓库配置向导，归档已有受控S05价目而被安全guard拒绝。首个测试修正在错误group设置多库位，仍失败。1e9e1b9按核心实际源码改base.group_user测试前提；不改上游产品/核心，不绕过价目guard|
|7cf36df翻译|149词均有译文，但4个Python标记不完整|实际POT导出核查发现Present/Missing/Unknown/Not applicable的odoo-python metadata未同步。92e02ea复制真实POT标记/引用；translation-failure-7cf36df.json保留|
|1e9e1b9公司负向|upgrade28/install30各1 failed、0 error|旧编辑写被拒，但测试误把上游“选店”当法人范围校验；审查显示原生按membership选店。05ae407在本批文书动作及原生读取增加当前法人范围检查；05ab25a验证文书动作/读取，而不改S01选店语义|
|早期独立安装7cf36df/9a4287e|install29 PASS为中间检查|7cf36df运行期间工作树曾继续整理PO/测试夹具，不能声称该次是最终冻结源码完整验证。所有中间安装均不用于最终交付数目|
|1e9e1b9中间Firefox|26 checks/11图/pageerror0 PASS|目录20261012T111313589753；这是较早产品，最终产品再次全程跑Firefox，不移用该PASS|
|05ab25a前置检查|upgrade28、16双连接PASS|在08c90441库通过；最终库另做完整冻结提交验证。原14组probe也保留，不能代替最终16组|

所有上述失败均为应用断言/夹具/安全拒绝/展示问题，没有本批 SIGSEGV 或非预期进程信号。不能因此宣称历史S07根因已修复。生产部署仍BLOCKED。

第一次XML静态检查使用系统Python缺少lxml，随后改用规定核心.venv完成解析；没有安装系统依赖。此工具选择失败不算产品安装结果。

8056c2a额外封住离线恢复后点击重新编辑/移交可能将未提交本地文字误显示已保存的边界；971e559增加真实Firefox断线恢复再点击验证。旧05ab25a库install30/upgrade28/probe16虽通过，仍未移用为新固定提交最终验证。

a69ac8b自审发现并封住已确认文字用第二次confirm绕过原因的入口；50a1a6f新增模型相同请求幂等/新请求拒绝及真实HTTP409断言，upgrade28通过。此为代码审查修正，未冒称先跑了失败用例；旧971e559的install30/upgrade28/probe16仍只作中间证据。

50a1a6f审计首次FAIL：8类检查中其余7项均0，negative_quant为20。只读按库位usage核对全为原生演示库存调整外部inventory库位；误将外部对手数量当内部余额断言。后续只修audit的internal范围，不改任何库存行/产品。原FAIL的audit JSON/exit1/loghash保留；同SHA Firefox28/11图/pageerror0是中间完整验证，新固定test另在新库全跑。
