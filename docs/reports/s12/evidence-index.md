# S12 证据索引

原始材料只留本机忽略目录，不公开凭据、会话秘密、临床原件或签名。尚无最终独立验收。

|证据|层级/结论|私有路径|SHA-256|
|---|---|---|---|
|目标准入|真实目标RO/RR，rollback/idle/close；无业务写/服务启动|.local/s12/admission/target-readonly-confirmed.json|d35806698a60e9cfd65a967621fdf1ed05edf3c55bdd50305ea3891266466dbf|
|首轮探针错误|普通断言误查不存在callback_url；原回执保留，修正真实callback_secret后另采|.local/s12/admission/|见原回执|
|独立清单|SOURCE F1—F4/T01—T12，不冒动态PASS|.local/s12/acceptance/checklist.md|待固定|

最终16行矩阵须实际产品/文件/请求/独立提交及升级完成后填写；正式正文/真实税票/物理设备分别NOT_RUN。

|证据|层级/结论|私有路径|SHA-256|
|---|---|---|---|
|首chain最终原key恢复|NORMAL_HTTP＋不同物理连接提交读回|.local/s12/first-loop/first-normal-recover-font-20261024/result.json|1a18f99e715d2619b38f2635074fbd314bd10c0cc9b1a0e5c36deca4e4db1a1d|
|真实PDF前/后|2页A4，改新主档后原bytes相同|同目录original-before.pdf / original-after.pdf|ddb3962685c62ff531360c16edcf1e5ab9d9a829cd616ee81688e7b8a01ac8d1|
|首链独立总回执|原始19步HTTP、新RO快照/文件/17表逐值、逐页亲看；有旧排版跟进，不冒全S12|.local/s12/acceptance/first-loop-independent.json|3828129241eb8d68da59eaa278c28d340842f76dfb98e0f1a2bf544ec26a1976|
|首链独立RO|backend3899453/源/模板/render SHA/附件与两HTTP文件/审计/经济保护|.local/s12/acceptance/first-original-readback.json|2ea980e333ac92f13d380e4365f0a48d56ba15b582750355558e2c9d8beb0b5d|
|首语言失败|真实preview409，无原件无更名；正常管理后续行|.local/s12/first-loop/first-normal-20261024/result.json|2b1c99b12c103509b758fd539fd50421d18b4beeff9537961e01e618151b8c10|
|首字体失败|真实generate409，独立核原key无提交后同key恢复|.local/s12/first-loop/first-normal-resume-zhcn-20261024/result.json|d5de94a48080908601e2f3ccc19c95c34a52ac0cf56653adeeffd068b3a55e0d|
|初始升级独立|完整即时pre后限定4模块，0/ERROR0，旧事实/附件保持；非final|.local/s12/acceptance/initial-upgrade-independent.json|932e7ad196ffd12b5f42e56af1750488af2373270d45f5c74cf09c461e03d04c|

|W2限定升级独立|四模块更新+两个新模块安装0/ERROR0，99installed，非final|.local/s12/acceptance/first-w2-upgrade-independent.json|3dca2c580aecb09bfb2b087240c76a8ef98faf95c2618a216ea8672d18e3c67e|
|首suite原始FAIL|28post-tests，1failed20errors，child1/wrapper2，无Native|.local/s12/checks/first-suite-suite/result.json|da18d84602c7597c062cb5b0001ddb69df236491aa1cceffba62b77c7824a3c7|
|首suite独立首因|fixture actor env/原生placeholder预期；不冒产品通过|.local/s12/acceptance/first-suite-failure-independent.json|eebdbff7ee3e9ebd757382906054a52786c9e482c7bcbd3f8fa2f22d63de3928|
|首suite后独立保护|145业务/15附件等逐值一致，仅模块write_date；非suite PASS|.local/s12/acceptance/first-suite-protection-independent.json|4a7e28078247c4f04be25f41782c7418bf687b6ea22a8482fd65addaf98dd832|
