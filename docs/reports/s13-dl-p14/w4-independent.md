# P14 W4 独立 scratch 与保护证据检查

2026-10-29，未参与产品实现的 W4 C 对既有 W2/W3 记录、两个本次 scratch 容器及最终源码工作树做只读检查。此报告不替代双浏览器最终验收，也不代替历史库独立前后快照。

## 独立 scratch

最终 scratch 的 `result.json` 记录新 PostgreSQL cluster `7701958915498270749`、数据库 OID `16384`，首次安装及合成 QWeb 渲染进程分别 exit 0；已加载页面的未付清 section 在只读事务渲染 normal、long、readonly、empty 四个合成分支，随后 rollback。四分支的权限布尔值、账单和 token 为内存数据，不代表普通岗位真实权限或真实经济记录。源码审阅发现该测试只解析前端资产路径，明确没有完整 bundle 编译或 HTTP 加载。

独立执行 `git -C .local/dl-p14/w3-final/source rev-parse HEAD` 得 `d70793d98c7cedbe7836900a811e517c8b9a47c8`，同目录 `git status --porcelain` 输出为空。`sha256sum` 独立匹配 QWeb 结果 `6487bc2314bec2db268a577eff53cc44ea1ea7166e4f6aa08bff95539569fb14`、渲染日志 `28c780449050447da03aac447896a4929c601fcaecc720e05ce0ea7e3f8e12ad`、安装日志 `23209a40c848670fd2517b9ed7f53f2a1ef659dc597a340643a0c605d12840fb`。渲染日志有针对测试 lambda 的 `Unsafe function access` 警告，末尾记录四分支成功，不将警告隐去。两个阶段的 `result.json` 均记录正常 stop exit 0；独立命令 `docker inspect --format '{{.Id}} Running={{.State.Running}} ExitCode={{.State.ExitCode}} Network={{.HostConfig.NetworkMode}}' fd07286b097c 62925da9886d` exit 0，两个实际容器均 Running=false、ExitCode=0、Network=none。第二个是最终候选的全新隔离库，前一个对应旧候选，证据不可混签。检查时 W4 浏览器团队仍在执行，因此此时不宣称本计划全部浏览器资源已停止。

## 失败、未知与保护范围

W2 静态夹具首轮外部溢出由缺失 Bootstrap border-box 的夹具配置造成，修正前事实保留；长单号造成金额列逐字换行在基线与首候选均能复现，最终候选修改后 WebKit 静态夹具定向复测通过。修复前 Chromium 的几何值部分仅采集、未断言；窄屏 200% 下焦点圈不能同时完整显示，滚轮未滚动的原因未知。以上不是最终候选完整真实页面通过证明。

新 scratch 的网络、独立路径、集群身份及执行代码支持其安装、渲染针对新目标的结论；本角色未发现对受保护历史库操作的证据，但没有进行本轮历史库物理独立前后比较，也未审计主机所有进程与所有潜在连接，因此**不能证明受保护历史库或全数据库零变化**。无经济 POST 的记录与只读渲染、源码检查均不能替代经济、库存、原件、附件、文书、审计与待办的独立前后读回。原 R3 等已提交对象和待办继续保护；此项当前为 UNKNOWN。共享 Odoo 服务及其他已有容器不属于本轮，不作停止或更改。

本次检查未启动或停止资源、未连接数据库、未执行业务动作、未修改产品文件。
