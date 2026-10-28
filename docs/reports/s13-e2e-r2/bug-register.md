# R2 产品缺陷登记

## E2E-R2-BUG-001：患者接口拒绝路径未记录预期 denial 审计

**状态 FIXED_VERIFIED（仅独立 scratch 所列范围）；历史目标未加载修复，最终影响面验收待 W6；严重程度中等（拒绝有效，限定患者动作拒绝审计缺失）。** 发现 W4：UID1560 在 B 店以当前 scope 对新合成 A 店背景2直接写，服务端真实 403 `access_denied`，B 核背景未变且无请求收据；拒绝本身有效。A 原日志 SHA `dbb3c9623252c7518d3b1fcb16e2688140cd74ac6fbce2b09ecf27fd9c1c8ab1`，B 读回 `603a6ff7beead6b36b305c3ab8dc4aa38bebbc1160dc6be9a5863333a44d052c`。

B 独立新 Context 重现403及无非法提交，查询该次审计只有登录、切店、读取，无对应 denied：`2f06ee13529109eaa562f5478fb39bcb16ba789c031bb27cb3ffeb78ab8d8b40`、`8ee9a0516fd814738ff2fcabc3865ced105ccb3162992bdadf2d0fb5e6aab688`。B 实际 MODEL 验证空 `ydental.patient.service` AbstractModel recordset 的 bool 为 false，日志 `94544ddbb11026a90e3f54639d3bf5bbb03e39ac487ae568531257336a0f0926`；结合 controller 异常路径 `if service:`，支持已实现的 denial 审计分支被跳过。主控确认登记产品缺陷；不将其称为本轮新引入或跨店写成功。

影响为所测患者 controller 拒绝路径的取证缺失；实际涉及其他分支和范围须进一步审查。修复和独立复验按下列固定证据限定；不能因未见 denial 而推定业务对象发生写入，亦不能让后续审计异常掩盖首异常。

修复 `794beea`，测试修正及最终测试候选 `ca07961da750dd5c58342cfe5759f45c1f806d5e`。B 独立 scratch 39 post-tests 0failed/0errors，日志 SHA `c98090781053cdd1745ee9be081ba7ce01e6b32dc7a48830f4f0607af56f293e`；前轮注入触发预派发HTTP500的测试失败保留，另有source.view只读cursor真实SQL ERROR及原生retry RW，非日志零ERROR。最终候选正常浏览器精确 B→A 直接写403并持久denied audit46，B `c3fc868ecbc09b3c2cade90644d6d8c7ec1b5bc6e38e7b10f64bdc077883a221`；撤权旧页403及audit55/56，B `a90bbd0c1ddcc272249ed8eaf9c2ab85e4a9452b793218ca60bdb20930da7fe0`。旧目标实际请求在旧候选上，未升级；不能以scratch结果补称旧目标已加载修复。详见 [W4](phase-W4.md)。
