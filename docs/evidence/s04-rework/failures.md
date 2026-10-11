# S04 定向返工失败及补交链

原始交付`3b74b33987252d59033ae4b9d6757ad609818216`、[原失败链](../s04/failures.md)和`docs/evidence/s04`全部保留，不用本轮成功覆盖。以下只记录本轮实际运行，原始日志保持在私有`.local`；公开材料只含合成断言、退出码、固定提交及日志SHA。

## 首轮 install：2 failed / 3 errors / 38 tests

- 库：`ydental_s04_test_20261011232743_1a3ed3e0`。
- 提交：`6c7f30d0f2dffef258672cfc4866e2aa640a7029`。
- 产品缺口：native Dataset使用RPC context替换request context，模型读资格没有收到SID绑定；合法前台的partner读取被拒绝。`da6575d`补真实SID绑定，`887d0a9`保证无YDental应用组的普通Contacts不被controller过度封锁。
- 测试适配：当前fork的read_group签名为domain/groupby/aggregates，旧签名调用错误；_grant为局部更新，撤权测试必须显式frontdesk=none。`fbb1159`修正这两项，保持拒绝断言。
- 同一任务自建库的诊断upgrade在`fbb1159`通过0/0/36；随后另建全新库验证修正，没有接管业务库或历史S00—S03库。

## 首轮原生 Contacts UI 断言超时

- 库：`ydental_s04_test_20261011233210_ae64c6f0`；浏览器提交`07c705971013e3a82417b43304fe19658a31c851`。
- [原summary](browser-attempts/20261011T233459910936/summary.json)：25项已完成，TimeoutError，pageerror=0；原22项中除最后“无JS错误”汇总外的21个功能断言已完成，新增4项native Contacts RPC断言通过。不是完整Firefox PASS。
- 锁定客户端收到res.partner/web_read的AccessError后会退回可见列表；弹窗出现时序不宜作唯一断言，首轮私有诊断最终只见列表。测试错误等待弹窗。诊断确认错误类型odoo.exceptions.AccessError和权限拒绝消息，未改产品放宽规则。最终06b截图另可见中文AccessError弹窗。
- `f3dc3dc`改为检查真实web_read响应AccessError、退回列表无患者/监护人、无受保护表单；普通联系人表单必须打开。两个受保护表单各留截图，普通联系人另留截图。
- 本次超时目录中的5张已完成截图及summary保持原样；最终使用另一全新库重跑完整install/probe/upgrade/export/Firefox，不以部分断言冒充全量成功。

全部动作及SHA见[runtime-history.json](runtime-history.json)，最终结果见[报告](../../s04-rework-report.md)。未执行的真实S05/S06/S08/S09/S10/S12联调始终NOT_RUN。
